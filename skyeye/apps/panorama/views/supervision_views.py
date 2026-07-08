# -*- coding: utf-8 -*-
import json
import os
import shutil
from datetime import datetime

import geopandas as gpd
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery, IntegerField, F, Case, When, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from shapely.geometry import Point, mapping, shape

from apps.panorama.common import unzip_file, find_nearest_point_id
from apps.panorama.models import (
    SupervisionProject,
    SupervisionProjectPolygon,
    SupervisionProjectRoute,
    SupervisionPolygonVertical,
    Route,
    PanoramaImage,
)
from apps.resource.models import MultivariateData
from utils_tools.common import find_shp_from_folder, parse_jwt_token
from logger import Logger
from apps.panorama.call_big_model import analyze_by_cate
logger = Logger(logname='supervision_views.log', loglevel=5, logger='supervision').getlog()


def _parse_body(request):
    if request.body:
        return json.loads(request.body.decode('utf-8'))
    return {}


def _get_user_info(request):
    try:
        user = parse_jwt_token(request)
        return user.username, user.county
    except Exception:
        return 'WXSAdmin', ''


def _load_polygon_gdf(upload_file):
    """从上传的 shp/zip 中读取面要素。"""
    temp_dir = os.path.join(settings.BASE_DIR, 'static', 'temp', 'supervision')
    os.makedirs(temp_dir, exist_ok=True)
    save_path = os.path.join(temp_dir, upload_file.name)
    if os.path.exists(save_path):
        os.remove(save_path)

    with open(save_path, 'wb+') as destination:
        for chunk in upload_file.chunks():
            destination.write(chunk)

    read_path = save_path
    if upload_file.name.lower().endswith('.zip'):
        unzip_dir = os.path.splitext(save_path)[0]
        if os.path.exists(unzip_dir):
            shutil.rmtree(unzip_dir)
        unzip_file(save_path, unzip_dir)
        shp_path = find_shp_from_folder(unzip_dir)
        if not shp_path:
            raise ValueError('压缩包中未找到 shp 文件')
        read_path = shp_path

    gdf = gpd.read_file(read_path)
    polygons_gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    if polygons_gdf.empty:
        raise ValueError('shp 中未找到面要素')
    return polygons_gdf


def _geometry_to_feature(geometry):
    return {
        'type': 'Feature',
        'geometry': mapping(geometry),
        'properties': {},
    }


def _fmt_dt(value):
    if not value:
        return ''
    return value.strftime('%Y-%m-%d %H:%M:%S')


def _fmt_date(value):
    if not value:
        return ''
    return value.strftime('%Y-%m-%d')


def _project_to_dict(obj, with_detail=False):
    data = {
        'id': obj.id,
        'dataType': obj.data_type,
        'count': obj.count,
        'createPerson': obj.create_person,
        'status': obj.status,
        'county': obj.county,
        'collectTime': _fmt_date(obj.collect_time),
        'createTime': _fmt_dt(obj.create_time),
    }
    if with_detail:
        data['polygons'] = [
            _polygon_to_dict(p) for p in SupervisionProjectPolygon.objects.filter(
                supervision_project_id=obj.id, is_del=0
            )
        ]
        data['routes'] = []
        for rel in SupervisionProjectRoute.objects.filter(supervision_project_id=obj.id):
            data['routes'].append(_route_to_dict(rel))
    return data


def _annotate_polygon_media_counts(qs):
    """按关联全景图数 + 俯视图数降序排序"""
    vertical_count_sq = SupervisionPolygonVertical.objects.filter(
        polygon_id=OuterRef('pk')
    ).values('polygon_id').annotate(cnt=Count('id')).values('cnt')[:1]

    panorama_count_sq = PanoramaImage.objects.filter(
        point_id=OuterRef('point_id')
    ).values('point_id').annotate(cnt=Count('image_id')).values('cnt')[:1]

    return qs.annotate(
        vertical_count=Coalesce(
            Subquery(vertical_count_sq, output_field=IntegerField()),
            Value(0),
        ),
        panorama_count=Case(
            When(point_id__isnull=True, then=Value(0)),
            When(point_id='', then=Value(0)),
            default=Coalesce(
                Subquery(panorama_count_sq, output_field=IntegerField()),
                Value(0),
            ),
            output_field=IntegerField(),
        ),
        media_count=F('panorama_count') + F('vertical_count'),
    ).order_by('-media_count', '-panorama_count', '-vertical_count', '-id')


def _polygon_to_dict(obj, use_fly_status=False):
    polygon_data = obj.polygon
    try:
        polygon_data = json.loads(obj.polygon) if obj.polygon else ''
    except (TypeError, json.JSONDecodeError):
        pass
    polygon_type_number = str(obj.polygon_type)
    if polygon_type_number == '1':
        polygon_type = '临时用地恢复'
    elif polygon_type_number == '2':
        polygon_type = '山水工程'
    else:
        polygon_type = '建设项目'
    t = getattr(obj, 'vertical_count', None)
    if t is None:
        t = SupervisionPolygonVertical.objects.filter(polygon_id=obj.id).count()
    panorama_count = getattr(obj, 'panorama_count', None)
    if panorama_count is None:
        panorama_count = (
            PanoramaImage.objects.filter(point_id=obj.point_id).count()
            if obj.point_id else 0
        )
    # status: 0-未飞过  1-已飞过（有关联全景图或俯视图）
    fly_status = 1 if (panorama_count > 0 or t > 0) else 0
    return {
        'id': obj.id,
        'supervisionProjectId': obj.supervision_project_id,
        'polygon': polygon_data,
        'latitude': obj.latitude,
        'longitude': obj.longitude,
        'polygonType': polygon_type,
        'constructionDesc': obj.construction_desc,
        'colorDesc': obj.color_desc,
        'pointId': obj.point_id,
        'status': fly_status if use_fly_status else obj.status,
        'createPerson': obj.create_person,
        'createTime': _fmt_dt(obj.create_time),
        'updateTime': _fmt_dt(obj.update_time),
        'verticalCount': t,
        'panoramaCount': panorama_count,
        'mediaCount': panorama_count + t,
    }


def _route_to_dict(obj):
    route = Route.objects.filter(id=obj.route_id).first()
    return {
        'id': obj.id,
        'supervisionProjectId': obj.supervision_project_id,
        'routeId': obj.route_id,
        'routeName': route.name if route else '',
        'createTime': _fmt_dt(obj.create_time),
    }


def _parse_bounds(bounds_raw):
    if not bounds_raw:
        return []
    if isinstance(bounds_raw, list):
        return bounds_raw
    try:
        return json.loads(bounds_raw)
    except (TypeError, json.JSONDecodeError):
        return bounds_raw


def _vertical_view_to_dict(obj):
    return {
        'id': obj.id,
        'dataName': obj.data_name,
        'fileId': obj.file_id,
        'path': obj.path,
        'latitude': obj.latitude,
        'longitude': obj.longitude,
        'bounds': _parse_bounds(obj.bounds),
        'county': obj.county,
        'fileSize': obj.file_size,
        'collectTime': _fmt_dt(obj.collect_time),
        'createTime': _fmt_dt(obj.create_time),
    }


def _get_polygon_vertical_views(polygon_id):
    rels = SupervisionPolygonVertical.objects.filter(polygon_id=polygon_id).order_by('-create_time')
    vertical_views = []
    for rel in rels:
        vertical_obj = MultivariateData.objects.filter(id=rel.vertical_view_id).first()
        if not vertical_obj:
            continue
        item = _vertical_view_to_dict(vertical_obj)
        item['relationId'] = rel.id
        vertical_views.append(item)
    return vertical_views


def link_vertical_view_to_polygons(vertical_view_id, longitude, latitude, image_path):
    """
    根据俯视图经纬度与监测图斑做空间关联：俯视图 GPS 落在图斑面内则关联。
    """
    if not longitude or not latitude:
        return []

    point = Point(float(longitude), float(latitude))
    linked_polygon_ids = []
    polygon_objs = SupervisionProjectPolygon.objects.filter(is_del=0)

    for polygon_obj in polygon_objs:
        if not polygon_obj.polygon:
            continue
        try:
            geo = json.loads(polygon_obj.polygon)
            geom_data = geo.get('geometry') if geo.get('type') == 'Feature' else geo
            polygon_geom = shape(geom_data)
            if polygon_geom.covers(point):
                SupervisionPolygonVertical.objects.get_or_create(
                    polygon_id=polygon_obj.id,
                    vertical_view_id=vertical_view_id,
                )
                linked_polygon_ids.append(polygon_obj.id)
                desc = analyze_by_cate(image_path, polygon_obj.polygon_type)
                polygon_obj.construction_desc = desc
                polygon_obj.save()
        except Exception as e:
            logger.warning(f'图斑关联俯视图失败 polygon_id={polygon_obj.id}: {e}')
    return linked_polygon_ids


def _parse_polygon_fields(params, username):
    polygon_val = params.get('polygon', '')
    if isinstance(polygon_val, (dict, list)):
        polygon_val = json.dumps(polygon_val, ensure_ascii=False)
    latitude = float(params.get('latitude', 0) or 0)
    longitude = float(params.get('longitude', 0) or 0)
    if polygon_val and (not latitude or not longitude):
        try:
            geo = json.loads(polygon_val)
            geom = geo.get('geometry') if geo.get('type') == 'Feature' else geo
            centroid = shape(geom).centroid
            longitude, latitude = centroid.x, centroid.y
        except Exception:
            pass
    return {
        'supervision_project_id': int(params.get('supervisionProjectId') or 0),
        'polygon': polygon_val,
        'latitude': latitude,
        'longitude': longitude,
        'polygon_type': params.get('polygonType', '建设项目'),
        'construction_desc': params.get('constructionDesc', ''),
        'color_desc': params.get('colorDesc', ''),
        'point_id': params.get('pointId', ''),
        'status': int(params.get('status', 0) or 0),
        'create_person': params.get('createPerson') or username,
    }


# ==================== 监管任务 ====================

def project_list(request):
    try:
        params = _parse_body(request)
        page = int(params.get('pageIndex', 1))
        limit = int(params.get('pageSize', 10))
        detail_id = params.get('id')

        qs = SupervisionProject.objects.all()
        if params.get('dataType'):
            qs = qs.filter(data_type=params.get('dataType'))
        if params.get('county'):
            qs = qs.filter(county__contains=params.get('county'))
        if params.get('status') not in (None, ''):
            qs = qs.filter(status=params.get('status'))

        if detail_id:
            obj = qs.filter(id=detail_id).first()
            data = [_project_to_dict(obj, with_detail=True)] if obj else []
            return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data, 'total': len(data)})

        total = qs.count()
        results = Paginator(qs, limit).page(page)
        data = [_project_to_dict(i) for i in results]
        count1 = SupervisionProject.objects.filter(data_type=1).count()
        count2 = SupervisionProject.objects.filter(data_type=2).count()
        count3 = SupervisionProject.objects.filter(data_type=3).count()
        return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data, 'total': total,'count1': count1, 'count2': count2, 'count3': count3})
    except Exception as e:
        logger.error(f'监管任务列表查询失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': []})


def project_add(request):
    """
    新增监管项目（山水工程等）。
    上传 shp/zip，每个面要素单独创建一个监管项目（1 图斑 = 1 项目）。
    FormData: file(必填), dataType, county, collectTime, status, polygonType
    """
    with transaction.atomic():
        try:
            upload_file = request.FILES.get('file')
            if not upload_file:
                return JsonResponse({'code': 1, 'msg': '请上传 shp 或 zip 文件', 'data': {}})

            username, user_county = _get_user_info(request)
            data_type = request.POST.get('dataType') or request.POST.get('data_type') or 3
            county = request.POST.get('county') or user_county or '无锡市(320200)'
            status = int(request.POST.get('status', 0) or 0)
            collect_time = request.POST.get('collectTime') or request.POST.get('collect_time')

            polygons_gdf = _load_polygon_gdf(upload_file)
            project_ids = []
            polygon_ids = []
            polygon_point_map = []
            for _, row in polygons_gdf.iterrows():
                geometry = row.geometry
                if geometry is None or geometry.is_empty:
                    continue

                project_fields = {
                    'data_type': data_type,
                    'count': 1,
                    'create_person': username,
                    'status': status,
                    'county': county,
                }
                if collect_time:
                    project_fields['collect_time'] = datetime.strptime(
                        str(collect_time)[:10], '%Y-%m-%d'
                    ).date()

                project_obj = SupervisionProject.objects.create(**project_fields)
                project_ids.append(project_obj.id)

                feature = _geometry_to_feature(geometry)
                centroid = geometry.centroid
                nearest_point_id, nearest_distance = find_nearest_point_id(
                    centroid.y, centroid.x, county
                )
                polygon_obj = SupervisionProjectPolygon.objects.create(
                    supervision_project_id=project_obj.id,
                    polygon=json.dumps(feature, ensure_ascii=False),
                    latitude=centroid.y,
                    longitude=centroid.x,
                    polygon_type=data_type,
                    construction_desc='',
                    color_desc='',
                    point_id=nearest_point_id or '',
                    create_person=username,
                    status=0,
                )
                polygon_ids.append(polygon_obj.id)
                polygon_point_map.append({
                    'projectId': project_obj.id,
                    'polygonId': polygon_obj.id,
                    'pointId': nearest_point_id,
                    'pointDistance': round(nearest_distance, 2) if nearest_distance is not None else None,
                })

            project_count = len(project_ids)
            if project_count == 0:
                raise ValueError('shp 中未找到有效面要素')

            return JsonResponse({
                'code': 0,
                'msg': f'新增成功，共创建 {project_count} 个项目',
                'data': {
                    'id': project_ids[0] if project_ids else None,
                    'projectIds': project_ids,
                    'projectCount': project_count,
                    'polygonCount': project_count,
                    'polygonIds': polygon_ids,
                    'polygonPointMap': polygon_point_map,
                }
            })
        except ValueError as e:
            return JsonResponse({'code': 1, 'msg': str(e), 'data': {}})
        except Exception as e:
            logger.error(f'监管项目新增失败: {e}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': f'新增失败: {e}', 'data': {}})


def project_edit(request):
    try:
        params = _parse_body(request)
        record_id = params.get('id')
        if not record_id:
            return JsonResponse({'code': 1, 'msg': '缺少ID', 'data': {}})
        fields = {
            'data_type': params.get('dataType', ''),
            'count': int(params.get('count', 0) or 0),
            'status': int(params.get('status', 0) or 0),
            'county': params.get('county', ''),
        }
        collect_time = params.get('collectTime')
        if collect_time:
            fields['collect_time'] = datetime.strptime(str(collect_time)[:10], '%Y-%m-%d').date()
        SupervisionProject.objects.filter(id=record_id).update(**fields)
        return JsonResponse({'code': 0, 'msg': '修改成功', 'data': {'id': record_id}})
    except Exception as e:
        logger.error(f'监管任务修改失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def project_delete(request):
    try:
        params = _parse_body(request)
        ids = params.get('ids') or ([params.get('id')] if params.get('id') else [])
        if not ids:
            return JsonResponse({'code': 1, 'msg': '缺少删除ID', 'data': {}})
        deleted = 0
        for record_id in ids:
            SupervisionProjectPolygon.objects.filter(supervision_project_id=record_id).update(is_del=1)
            SupervisionProjectRoute.objects.filter(supervision_project_id=record_id).delete()
            deleted += SupervisionProject.objects.filter(id=record_id).delete()[0]
        return JsonResponse({'code': 0, 'msg': '删除成功', 'data': {'deleted': deleted}})
    except Exception as e:
        logger.error(f'监管任务删除失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


# ==================== 监管图斑 ====================

def polygon_list(request):
    try:
        params = _parse_body(request)
        page = int(params.get('pageIndex', 1))
        limit = int(params.get('pageSize', 10))
        detail_id = params.get('id')

        qs = SupervisionProjectPolygon.objects.filter(is_del=0)
        if params.get('supervisionProjectId'):
            qs = qs.filter(supervision_project_id=params.get('supervisionProjectId'))
        if params.get('polygonType'):
            qs = qs.filter(polygon_type=params.get('polygonType'))

        qs = _annotate_polygon_media_counts(qs)

        # 按是否飞过筛选：1-已飞过  0-未飞过
        fly_status = params.get('status')
        if fly_status not in (None, ''):
            fly_status = int(fly_status)
            if fly_status == 1:
                qs = qs.filter(media_count__gt=0)
            elif fly_status == 0:
                qs = qs.filter(media_count=0)

        if detail_id:
            obj = qs.filter(id=detail_id).first()
            data = [_polygon_to_dict(obj, use_fly_status=True)] if obj else []
            return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data, 'total': len(data)})

        total = qs.count()
        results = Paginator(qs, limit).page(page)
        data = [_polygon_to_dict(i, use_fly_status=True) for i in results]
        return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data, 'total': total})
    except Exception as e:
        logger.error(f'监管图斑列表查询失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': []})


def polygon_detail(request):
    """根据图斑ID获取监测图斑详情。"""
    try:
        params = _parse_body(request)
        polygon_id = params.get('polygonId') or params.get('polygon_id') or params.get('id')
        if not polygon_id:
            return JsonResponse({'code': 1, 'msg': '缺少图斑ID', 'data': {}})

        obj = SupervisionProjectPolygon.objects.filter(id=polygon_id, is_del=0).first()
        if not obj:
            return JsonResponse({'code': 1, 'msg': '图斑不存在', 'data': {}})

        data = _polygon_to_dict(obj)
        project = SupervisionProject.objects.filter(id=obj.supervision_project_id).first()
        if project:
            data['project'] = {
                'id': project.id,
                'dataType': project.data_type,
                'count': project.count,
                'county': project.county,
                'status': project.status,
                'createPerson': project.create_person,
                'collectTime': _fmt_date(project.collect_time),
                'createTime': _fmt_dt(project.create_time),
            }
        data['verticalViews'] = _get_polygon_vertical_views(obj.id)
        data["fcw"] = 5
        data["jj"] = 2
        data["wd"] = 8
        return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data})
    except Exception as e:
        logger.error(f'监管图斑详情查询失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def polygon_add(request):
    try:
        params = _parse_body(request)
        fields = _parse_polygon_fields(params, _get_user_info(request)[0])
        if not fields['supervision_project_id']:
            return JsonResponse({'code': 1, 'msg': '缺少监管任务ID', 'data': {}})
        obj = SupervisionProjectPolygon.objects.create(**fields)
        return JsonResponse({'code': 0, 'msg': '新增成功', 'data': {'id': obj.id}})
    except Exception as e:
        logger.error(f'监管图斑新增失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def polygon_edit(request):
    try:
        params = _parse_body(request)
        record_id = params.get('id')
        if not record_id:
            return JsonResponse({'code': 1, 'msg': '缺少ID', 'data': {}})
        fields = _parse_polygon_fields(params, _get_user_info(request)[0])
        if not fields['supervision_project_id']:
            return JsonResponse({'code': 1, 'msg': '缺少监管任务ID', 'data': {}})
        SupervisionProjectPolygon.objects.filter(id=record_id).update(**fields)
        return JsonResponse({'code': 0, 'msg': '修改成功', 'data': {'id': record_id}})
    except Exception as e:
        logger.error(f'监管图斑修改失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def polygon_delete(request):
    try:
        params = _parse_body(request)
        ids = params.get('ids') or ([params.get('id')] if params.get('id') else [])
        if not ids:
            return JsonResponse({'code': 1, 'msg': '缺少删除ID', 'data': {}})
        deleted = SupervisionProjectPolygon.objects.filter(id__in=ids).update(is_del=1)
        return JsonResponse({'code': 0, 'msg': '删除成功', 'data': {'deleted': deleted}})
    except Exception as e:
        logger.error(f'监管图斑删除失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


# ==================== 监管航线关联 ====================

def route_list(request):
    try:
        params = _parse_body(request)
        page = int(params.get('pageIndex', 1))
        limit = int(params.get('pageSize', 10))
        detail_id = params.get('id')

        qs = SupervisionProjectRoute.objects.all()
        if params.get('supervisionProjectId'):
            qs = qs.filter(supervision_project_id=params.get('supervisionProjectId'))

        if detail_id:
            obj = qs.filter(id=detail_id).first()
            data = [_route_to_dict(obj)] if obj else []
            return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data, 'total': len(data)})

        total = qs.count()
        results = Paginator(qs, limit).page(page)
        data = [_route_to_dict(i) for i in results]
        return JsonResponse({'code': 0, 'msg': '查询成功', 'data': data, 'total': total})
    except Exception as e:
        logger.error(f'监管航线关联查询失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': []})


def route_add(request):
    try:
        params = _parse_body(request)
        supervision_project_id = int(params.get('supervisionProjectId') or 0)
        route_id = int(params.get('routeId') or 0)
        if not supervision_project_id or not route_id:
            return JsonResponse({'code': 1, 'msg': '缺少监管任务ID或航线ID', 'data': {}})
        obj = SupervisionProjectRoute.objects.create(
            supervision_project_id=supervision_project_id,
            route_id=route_id,
        )
        return JsonResponse({'code': 0, 'msg': '新增成功', 'data': {'id': obj.id}})
    except Exception as e:
        logger.error(f'监管航线关联新增失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def route_edit(request):
    try:
        params = _parse_body(request)
        record_id = params.get('id')
        supervision_project_id = int(params.get('supervisionProjectId') or 0)
        route_id = int(params.get('routeId') or 0)
        if not record_id:
            return JsonResponse({'code': 1, 'msg': '缺少ID', 'data': {}})
        if not supervision_project_id or not route_id:
            return JsonResponse({'code': 1, 'msg': '缺少监管任务ID或航线ID', 'data': {}})
        SupervisionProjectRoute.objects.filter(id=record_id).update(
            supervision_project_id=supervision_project_id,
            route_id=route_id,
        )
        return JsonResponse({'code': 0, 'msg': '修改成功', 'data': {'id': record_id}})
    except Exception as e:
        logger.error(f'监管航线关联修改失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def route_delete(request):
    try:
        params = _parse_body(request)
        ids = params.get('ids') or ([params.get('id')] if params.get('id') else [])
        if not ids:
            return JsonResponse({'code': 1, 'msg': '缺少删除ID', 'data': {}})
        deleted = SupervisionProjectRoute.objects.filter(id__in=ids).delete()[0]
        return JsonResponse({'code': 0, 'msg': '删除成功', 'data': {'deleted': deleted}})
    except Exception as e:
        logger.error(f'监管航线关联删除失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})
