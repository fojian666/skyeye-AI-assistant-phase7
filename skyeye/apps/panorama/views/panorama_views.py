# _*_ coding: utf-8 _*_
# @Time : 2024/12/18 13:55 
# @Author : xxx 
# @Version：V 0.1
# @File : panorama_views.py
# @desc :
import ast
import datetime
import math
import os
import json
import random
import re
import shutil
import time
import uuid
import configparser
import zipfile
import cv2
import numpy as np
import pandas as pd
import requests
from PIL import Image
from django.conf import settings
from django.contrib.admin.utils import quote
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.encoding import escape_uri_path
from django.db import transaction
import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Polygon as shapely_polygon, Point

from apps.system.models import User, SysDictData
from utils_tools.common import create_log, login_request, read_json, file_iterator, find_shp_from_folder, \
    parse_jwt_token

from apps.panorama.models import Batch, Grid, PanoramaImage, Clue, UploadBatch, PointLocation, Scene, BufferFile, \
    FrameArea, Notify, BatchResource, Resource, PlotRecord, FlyOrder
from apps.panorama.tasks import panorama_detection, submit_panorama_detection
from apps.panorama.common import get_coordinates, unzip_file, read_grid_shp, read_point_shp, calculate_date_ranges, \
    image_to_latlon, shp_to_kml, get_yaw_degree, calculate_distances, get_recent_seven_day, \
    find_village_by_point, safe_unzip, compute_yaw_pitch, get_point_buffer_gd, get_point_buffer_gd_geoserver, \
    calculate_distances2

from logger import Logger

logger = Logger(logname='panorama_views.log', loglevel=5, logger='panorama').getlog()

config = configparser.ConfigParser()
# 假设config.ini位于脚本同级目录下
config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
common_config = config['common']


def delete_backups_files(temp_files_list):
    """
    代码运行时，产生的输出文件，但因执行报错，进入except中，需要删除中间的生成文件，用此函数
    @temp_files_list：文件路径存储列表
    :return:
    """
    for i in temp_files_list:
        if os.path.exists(i):
            if os.path.isdir(i):
                shutil.rmtree(i)
            elif os.path.isfile(i):
                os.remove(i)


def restore_files_to_original_path(temp_file_list):
    """
    任务执行时，接收到删除任务的请求，在此过程中进行了文件备份，当删除某文件，但并未完全成功执行任务时，需要将备份文件进行恢复，不进行删除，用此函数
    @temp_file_list:任务删除列表，里面包含若干个字典，每个字典存在src和copy_path路径
    :return:
    """
    for i in temp_file_list:
        src_path = i['src']
        copy_path = i['copy_path']
        if os.path.exists(copy_path):
            shutil.copy(copy_path, src_path)


def delete_copy_path(temp_file_list):
    for i in temp_file_list:
        copy_path = i['copy_path']
        if os.path.exists(copy_path):
            if os.path.isdir(copy_path):
                shutil.rmtree(copy_path)
            elif os.path.isfile(copy_path):
                os.remove(copy_path)


def filter_clues(status=None, clue_name=None, grid_name=None, start_date=None, end_date=None, county=None):
    """
    根据提供的查询条件过滤线索。

    参数:
    - status (str): 状态
    - clue_name (str): 线索名称
    - grid_name (str): 网格名称
    - start_date (datetime): 开始日期
    - end_date (datetime): 结束日期

    返回:
    - QuerySet: 过滤后的线索查询集
    """
    try:
        # 构建查询条件
        filters = Q()
        if status:
            filters &= Q(status__in=status)
        if clue_name:
            filters &= Q(clue_name__contains=clue_name)
        if grid_name:
            filters &= Q(batch__grid_id=grid_name)
        if start_date:
            filters &= Q(create_time__gte=start_date)
        if end_date:
            filters &= Q(create_time__lte=end_date)
        if county:
            filters &= Q(batch__grid__county=county)
        # 应用过滤条件
        clues = Clue.objects.filter(filters).order_by('-clue_id')
        return clues
    except Exception as e:
        logger.error(f"根据提供的查询条件过滤线索失败: {e}")


def map_view_clue_list(request):
    """
    地图总览获取线索数据
    @param request:
    @return:
    """

    response_data = {'code': 0, 'msg': '', 'data': []}
    try:
        params = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        params = {}
    status = params.get('status')
    if status == '' or status is None:
        status = [0, 2, 3, 5]
    else:
        if status == 2:
            status = [2, 3]
        else:
            status = [status]
    current_user = parse_jwt_token(request)
    if not current_user:
        return JsonResponse({'code': 405, 'msg': '登录失效，请重新登录', 'data': []})
    county = current_user.county
    keyword = params.get('keyword')
    grid_name = params.get('grid_name')
    start_date = params.get('start_date')
    end_date = params.get('end_date')
    limit = params.get('limit', 10)
    page = params.get('page', 1)
    # 将日期字符串转换为 datetime 对象
    start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
    end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
    clue_objs = filter_clues(status, keyword, grid_name, start_date, end_date, county)
    if len(clue_objs) > 0:
        paginator = Paginator(clue_objs, limit)
        results = paginator.page(page)
    else:
        results = []
    data = []
    for clue_obj in results:
        panorama_image_obj = clue_obj.panorama_image
        record = {
            'clue_id': clue_obj.clue_id,
            'clue_name': clue_obj.clue_name,
            'region': clue_obj.batch.region,
            'clue_status': clue_obj.status,
            'batch_id': clue_obj.batch_id,
            'longitude': clue_obj.longitude,
            'latitude': clue_obj.latitude,
            'panorama_image_name': panorama_image_obj.image_name if panorama_image_obj else '-',
            'point_id': panorama_image_obj.point_id if panorama_image_obj else '-',
            'create_time': clue_obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': clue_obj.last_modify_time,
            'image_path': clue_obj.file_path,
        }
        data.append(record)
    response_data['data'] = data
    response_data['count'] = len(clue_objs)
    return JsonResponse(response_data)


def map_view_info(request):
    """
    地图总览信息获取
    @param request:
    @return:
    """
    try:

        current_user = parse_jwt_token(request)
        if not current_user:
            return JsonResponse({'code': 405, 'msg': '登录失效，请重新登录', 'data': {}})
        country = current_user.county
        panorama_count = PanoramaImage.objects.filter(batch__grid__county=country).count()
        clue_confirm_count = Clue.objects.filter(status__in=[2, 3],
                                                 batch__grid__county=country).count()
        clue_effective = Clue.objects.filter(status=5, batch__grid__county=country).count()
        clue_review_count = Clue.objects.filter(status=0, batch__grid__county=country).count()
        grid_names = (Batch.objects.values('grid__grid_name').annotate(count=Count('batch_id')).order_by())
        grid_name_list = [
            {
                'name': grid['grid__grid_name'],
                'value': Grid.objects.filter(grid_name=grid['grid__grid_name']).first().grid_id
                if Grid.objects.filter(grid_name=grid['grid__grid_name']).first() else None
            }
            for grid in grid_names
        ]
        business_status = [{'name': '待审核', 'value': 0}, {'name': '疑似', 'value': 2}, {'name': '有效', 'value': 5}]

        response_data = {
            "code": 0,
            'msg': '数据获取成功',
            "data": {
                'panorama_count': panorama_count,
                'clue_effective': clue_effective,
                'clue_confirm_count': clue_confirm_count,
                'clue_review_count': clue_review_count,
                'grid_name_list': grid_name_list,
                'business_status': business_status,

            }
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'地图总览信息获取失败{e}')
        return JsonResponse({'code': 500, 'msg': f'{e}', 'data': {}})


def _location_str(name, lat, lon):
    if lat is not None and lon is not None:
        return f"全景点【{name}】:{lat},{lon}"
    return ""


def _detection_log_detail(remark, point_locations):
    buffer = []
    if remark:
        try:
            result = json.loads(remark)
        except (json.JSONDecodeError, TypeError):
            result = {}
        repeat_list = result.get("repeatImageList") or []
        if repeat_list:
            buffer.append("重复图片信息:")
            for item in repeat_list:
                loc = _location_str(item.get("pointName"), item.get("lat"), item.get("lon"))
                buffer.append(
                    f"    本次提交图片名称：{item.get('imageName', '')}"
                    f",重复图片名称：{item.get('repetitiveImageName', '')}"
                    f",{loc}"
                )
        non_related = result.get("nonRelatedPointImageList") or []
        if non_related:
            buffer.append("未关联到全景点图片信息:")
            for name in non_related:
                buffer.append(f"    本次提交图片名称：{name}")
        non_panorama = result.get("nonPanoramaImageList") or []
        if non_panorama:
            buffer.append("非全景图片信息:")
            for name in non_panorama:
                buffer.append(f"    本次提交图片名称：{name}")
    if point_locations:
        buffer.append("仍未上传全景图片的全景点信息:")
        for loc in point_locations:
            line = _location_str(loc.point_name, loc.latitude, loc.longitude)
            if line:
                buffer.append(f"    {line}")
    return "\r\n".join(buffer) + ("\r\n" if buffer else "")


def down_detection_log(request, upload_batch_id):
    """
    下载全景检测提交日志，对应 Java GET /panorama_view/down_detection_log/{id}
    """
    upload_batch_id = (upload_batch_id or "").strip()
    upload_batch = UploadBatch.objects.filter(id=upload_batch_id).first()

    filename = None
    error = ""
    if not upload_batch:
        error = f"提交批次【{upload_batch_id}】未找到"
        filename = "error"
    else:
        batch = Batch.objects.filter(batch_id=upload_batch.batch_id).first()
        if not batch:
            error = f"提交批次【{upload_batch_id}】对应飞行批次未找到"
            filename = upload_batch.id
        else:
            create_date = upload_batch.create_time or timezone.now()
            filename = f"{batch.batch_name}-{create_date.strftime('%Y%m%d%H%M%S')}提交日志"

    if error:
        content = error
    else:
        point_ids = set(
            PanoramaImage.objects.filter(batch_id=upload_batch.batch_id)
                .values_list("point_id", flat=True)
        )
        point_locations = []
        if upload_batch.batch_type == 0 and upload_batch.batch.grid_id:
            point_locations = [
                p for p in PointLocation.objects.filter(grid_id=upload_batch.batch.grid_id).order_by("point_id")
                if p.point_id not in point_ids
            ]
        content = _detection_log_detail("", point_locations)

    response = HttpResponse(content.encode("utf-8"), content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{quote(filename)}.txt"'
    return response


def main_detection(request):
    """
    全景检测
    @param request:
    @return:
    """
    if request.method == 'GET':
        try:
            data = []
            grid_objs = Grid.objects.all()
            for grid in grid_objs:
                kml_path = grid.kml_path
                street = grid.street
                # batch_objs = Batch.objects.filter(grid=grid).filter(Q(end_date__gte=today)).all()
                batch_objs = Batch.objects.filter(grid=grid).filter(status__in=[0, 1]).all()
                batch_id_list = []
                for batch in batch_objs:
                    records = {
                        'batch_id': batch.batch_id,
                        'batch_name': batch.batch_name,
                        'count': batch.count - PanoramaImage.objects.filter(batch=batch).count(),
                    }
                    batch_id_list.append(records)
                records = {
                    'kml_path': kml_path,
                    'street': street,
                    'grid_name': grid.grid_name,
                    'batch_list': batch_id_list
                }
                data.append(records)
            response_data = {
                'code': 0,
                'msg': '',
                'data': data,

            }
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'网格查询失败{e}')
            return JsonResponse({'code': 500, 'msg': f'网格查询失败{e}'})
    elif request.method == 'POST':
        logger.info('开始上传全景图')
        try:
            params = json.loads(request.body.decode('utf-8'))
            file_name = params.get('fileName')
            batch_id = params.get('batchId')
            street = params.get('street')
            operator = params.get('operator')
            file_folder = os.path.join(settings.BASE_DIR, 'static', 'temp', file_name)
            file_list = os.listdir(file_folder)
            batch_obj = Batch.objects.get(batch_id=batch_id)
            upload_batch = UploadBatch.objects.create(
                batch_id=batch_id,
                grid_operator=operator,
                file_path=file_folder,
            )
            file_id = 1
            r = []
            for i in file_list:
                print(f"正在开始第{file_id}/{len(file_list)}, {i}")
                file_path = os.path.join(file_folder, i)
                image_id = str(uuid.uuid1()).replace('-', '')
                img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                lat, lon, gps_height = get_coordinates(file_path)
                all_points = PointLocation.objects.filter(grid_id=upload_batch.batch.grid_id).all()
                all_lonlat = []
                for j in all_points:
                    all_lonlat.append({"point_id": j.point_id, 'point': (j.latitude, j.longitude)})
                closest_point, distance = calculate_distances((lat, lon), all_lonlat)
                # 如果没有关联全景点，就下一个
                if not closest_point:
                    continue
                print(closest_point, distance)
                r.append({closest_point: distance})
                yaw_degree, relativeAltitude = get_yaw_degree(file_path)
                image_height, image_width, _ = img.shape
                current_point_exists = PanoramaImage.objects.filter(batch_id=batch_id, point_id=closest_point).first()
                if current_point_exists:
                    continue
                is_exists = PanoramaImage.objects.filter(batch_id=batch_id, latitude=lat, longitude=lon).exists()
                if not is_exists:
                    with transaction.atomic():
                        panorama_image = PanoramaImage.objects.create(
                            image_id=image_id,
                            image_name=i,
                            image_path=file_path,
                            longitude=lon,
                            point_id=closest_point,
                            latitude=lat,
                            batch_id=batch_id,
                            image_height=image_height,
                            image_width=image_width,
                            height=relativeAltitude,
                            yaw_degree=yaw_degree,
                            upload_batch=upload_batch,
                        )
                        p_obj = {
                            'image_id': image_id,
                            'image_name': i,
                            'image_path': file_path,
                            'longitude': lon,
                            'point_id': closest_point,
                            'latitude': lat,
                            'batch_id': batch_id,
                            'image_height': image_height,
                            'image_width': image_width,
                            'height': float(relativeAltitude),
                            'yaw_degree': yaw_degree,
                            'is_change_detection': batch_obj.change_detection,
                        }
                        transaction.on_commit(lambda: panorama_detection.apply_async(
                            args=[image_id, p_obj],
                            task_id=str(image_id)
                        ))
                    print(f"第{file_id}张图片{panorama_image.image_name}保存成功！")
                    file_id += 1
                    # panorama_detection.apply_async(args=[image_id, closest_point], task_id=str(image_id))
            upload_batch.count = file_id - 1
            upload_batch.save()
            current_batch = Batch.objects.get(batch_id=batch_id)
            current_batch.status = 1
            current_batch.save()
            # write_doc(task, res, target_directory)
            surplus_count = current_batch.count - file_id - 1
            return JsonResponse({'code': 0,
                                 'msg': f'提交识别任务成功,已上传全景图一共{file_id - 1}张，当前批次还剩{surplus_count}张待上传'})
        except Exception as e:
            logger.error(f'提交识别任务失败，{e}')
            return JsonResponse({'code': 500, 'msg': f'提交识别任务失败，{e}'})


def interpretation_progress(request):
    """
    根据批次编号查询全景图检测的进度
    @param request:
    @param batch_id:
    @return:
    """
    try:
        upload_batch_objs = UploadBatch.objects.all()
        data = []
        for i in upload_batch_objs:
            done_count = PanoramaImage.objects.filter(upload_batch=i).exclude(status=0).count()
            total_count = PanoramaImage.objects.filter(upload_batch=i).count()
            if total_count == 0:
                percent = 0
            else:
                percent = done_count / total_count
            current_batch_obj = Batch.objects.get(batch_id=i.batch_id)
            if done_count == current_batch_obj.count and current_batch_obj.status == 1:
                current_batch_obj.status = 3
                current_batch_obj.save()
            records = {
                'upload_batch_id': i.id,
                'done_count': done_count,
                'total_count': total_count,
                'percent': percent,
            }
            data.append(records)
        return JsonResponse({"code": 0, 'data': data, 'msg': ''})
    except Exception as e:
        logger.error(f'查询全景图检测的进度请求失败，错误信息：{str(e)}')
        return JsonResponse({"code": 500, 'data': [], 'msg': str(e)})


# 自定义排序函数
def extract_number(name):
    # 提取字符串中的数字部分
    match = re.search(r'\d+', name)
    return int(match.group()) if match else 0


def panorama_image_by_params(request):
    """
    根据批次ID获取所有全景图片
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        batch_id = params.get('batchId')
        had_clue = params.get('hadClue', -1)
        point_name = params.get('pointName')
        page = params.get('pageIndex')
        limit = params.get('pageSize')
        panorama_list1 = PanoramaImage.objects.filter(point__point_name__contains=point_name, batch_id=batch_id).all()
        panorama_list = sorted(
            panorama_list1,
            key=lambda img: int(re.search(r'\d+', img.point.point_name).group())
        )
        if len(panorama_list) > 0:
            paginator = Paginator(panorama_list, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []

        for i in results:

            year_month = i.create_time.strftime('%Y%m')
            record = {
                'imageId': i.image_id,
                'imageName': i.image_name,
                'longitude': i.longitude,
                'latitude': i.latitude,
                'count': Clue.objects.filter(status=0, panorama_image=i).count(),
                'yawDegree': i.yaw_degree,
                'imageWidth': i.image_width,
                'imageHeight': i.image_height,
                'imagePath': i.image_path,
                'pointId': i.point.point_id,
                'pointName': i.point.point_name,
                'height': i.height,
                'desc':i.desc,
                'street': i.point.grid.street if i.point.grid else '-',
                'createTime': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'tileResolution': i.tile_resolution,
                'maxLevel': i.max_level,
                'cubeResolution': i.cube_resolution,
                'yearMonth': year_month,
                'status': i.status,
                'todoCount': Clue.objects.filter(panorama_image=i, status=0).count(),
                'doneCount': Clue.objects.filter(panorama_image=i, status__in=[2, 3, 5]).count(),
            }
            count = Clue.objects.filter(panorama_image=i).count()
            if had_clue == 1:
                if count > 0:
                    data.append(record)
            elif had_clue == 0:
                if count == 0:
                    data.append(record)
            else:
                data.append(record)
        total_todo__clue_count = Clue.objects.filter(batch_id=batch_id, status=0).count()
        response_data = {
            'code': 0,
            'msg': '数据获取成功！',
            'data': {
                'cards': data,
                'total_todo_count': total_todo__clue_count
            },
            'total': len(panorama_list),

        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error('根据批次ID获取所有全景图片异常：{}'.format(e))
        return JsonResponse({'code': 500, 'msg': '根据批次ID获取所有全景图片异常：{}'.format(e)})


def panorama_image_by_batch_id(request):
    """
    根据批次ID获取所有全景图片
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        batch_id = params.get('batchId')
        panorama_list1 = PanoramaImage.objects.filter(batch_id=batch_id).all()
        panorama_list = sorted(
            panorama_list1,
            key=lambda img: int(re.search(r'\d+', img.point.point_name).group())
        )
        data = []

        for i in panorama_list:
            year_month = i.create_time.strftime('%Y%m')
            record = {
                'imageId': i.image_id,
                'imageName': i.image_name,
                'longitude': i.longitude,
                'latitude': i.latitude,
                'count': Clue.objects.filter(status=0, panorama_image=i).count(),
                'yawDegree': i.yaw_degree,
                'imageWidth': i.image_width,
                'imageHeight': i.image_height,
                'imagePath': i.image_path,
                'pointId': i.point.point_id,
                'height': i.height,
                'pointName': i.point.point_name,
                'street': i.point.grid.street if i.point.grid else '-',
                'createTime': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'tileResolution': i.tile_resolution,
                'maxLevel': i.max_level,
                'cubeResolution': i.cube_resolution,
                'yearMonth': year_month,
                'status': i.status,
                'todoCount': Clue.objects.filter(panorama_image=i, status=0).count(),
                'doneCount': Clue.objects.filter(panorama_image=i, status__in=[2, 3, 5]).count(),
            }
            data.append(record)
        response_data = {
            'code': 0,
            'msg': '数据获取成功！',
            'data': {
                'total_todo_count': 0,
                'cards': data
            },
            'total': len(panorama_list)
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error('根据批次ID获取所有全景图片异常：{}'.format(e))
        return JsonResponse({'code': 500, 'msg': '根据批次ID获取所有全景图片异常：{}'.format(e)})


def panorama_image_by_point_id(request):
    """
    根据点位ID获取全景图片
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        point_id = params.get('pointId')
        panorama_list = PanoramaImage.objects.filter(point_id=point_id).all().order_by('-batch_id')
        data = []
        for i in panorama_list:
            record = {
                'imageId': i.image_id,
                'imageName': i.image_name,
                'batchId': i.batch.batch_id,
                'batchName': i.batch.batch_name,
                'longitude': i.longitude,
                'imageWidth': i.image_width,
                'imageHeight': i.image_height,
                'imagePath': i.image_path,
                'pointName': i.point.point_name,
                'latitude': i.latitude,
                'yawDegree': i.yaw_degree,
                'tileResolution': i.tile_resolution,
                'maxLevel': i.max_level,
                'cubeResolution': i.cube_resolution,
                'pointId': i.point.point_id,
            }
            data.append(record)
        response_data = {
            'code': 0,
            'msg': '数据获取成功！',
            'data': data,
            'count': len(panorama_list)
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error('根据点位ID获取全景图片异常：{}'.format(e))
        return JsonResponse({'code': 500, 'msg': '根据点位ID获取全景图片异常：{}'.format(e)})


def panorama_image_one(request):
    """
    根据批次ID获取全景图
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        batch_id = params.get('batch_id')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        panorama_list1 = PanoramaImage.objects.filter(batch_id=batch_id).all()
        panorama_list = sorted(
            panorama_list1,
            key=lambda img: int(re.search(r'\d+', img.point.point_name).group())
        )
        paginator = Paginator(panorama_list, limit)
        try:
            results = paginator.page(page)
        except Exception as e:
            results = paginator.page(page - 1)
        data = []
        for i in results:
            if i.point.grid:
                street = i.point.grid.street
            else:
                street = '-'
            record = {
                'imageId': i.image_id,
                'imageName': i.image_name,
                'longitude': i.longitude,
                'latitude': i.latitude,
                'todoCount': Clue.objects.filter(panorama_image=i, status=0).count(),
                'doneCount': Clue.objects.filter(panorama_image=i, status__in=[2, 3, 5]).count(),
                'yawDegree': i.yaw_degree,
                'status': i.status,
                'imageWidth': i.image_width,
                'imageHeight': i.image_height,
                'imagePath': i.image_path,
                'pointName': i.point.point_name,
                'street': street,
                'createTime': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'tileResolution': i.tile_resolution,
                'maxLevel': i.max_level,
                'cubeResolution': i.cube_resolution,
            }
            data.append(record)
        response_data = {
            'code': 0,
            'msg': '数据获取成功！',
            'data': data,
            'total_todo_count': Clue.objects.filter(batch_id=batch_id, status=0).count(),
            'count': len(panorama_list)
        }

        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'根据批次ID获取全景图异常：{e}')
        return JsonResponse({'code': 500, 'msg': f'根据批次ID获取全景图异常：{e}'})


def get_clue_by_panorama_image_id(request):
    """
    根据全景图片查询线索
    @param request:
    @return:
    """
    try:
        panorama_image_id = request.GET.get('panorama_image_id')
        panorama_image_obj = PanoramaImage.objects.get(image_id=panorama_image_id)
        if not panorama_image_obj:
            return JsonResponse({"code": 404, "msg": "全景图片不存在！"})
        results = Clue.objects.filter(panorama_image_id=panorama_image_id).all().order_by('-clue_id')
        data = []
        for result in results:
            position = result.position
            points = []
            if position:
                position_list = ast.literal_eval(position)
                # 将像素坐标转换为弧度
                yaw_rad = (position_list[0] / panorama_image_obj.image_width) * 2 * math.pi - math.pi
                pitch_rad = math.pi / 2 - (position_list[1] / panorama_image_obj.image_height) * math.pi
                # 将弧度转换为角度
                x = yaw_rad * 180 / math.pi
                y = pitch_rad * 180 / math.pi
                points.append([y, x])
            dict_value = {
                'clue_id': result.clue_id,
                'label': result.clue_name,
                'center_x': result.center_x,
                'center_y': result.center_y,
                'latitude': result.latitude,
                'longitude': result.longitude,
                'position': points,
                'clue_source': result.clue_source,
                'status': result.status,
                'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),

            }
            data.append(dict_value)
        response_data = {'code': 0, 'msg': '', 'data': {
            'image_width': panorama_image_obj.image_width,
            'image_height': panorama_image_obj.image_height,
            'clue_list': data,
            'point_id': panorama_image_obj.point_id
        }}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'根据全景图片查询线索异常{e}')
        return JsonResponse({'code': 55, 'msg': f'根据全景图片查询线索异常{e}'})


def panorama_image_sibling(request):
    """
    获取相同全景点位的全景图
    @param request:
    @return:
    """
    try:
        panorama_image_id = request.GET.get('panorama_image_id')
        panorama_image_obj = PanoramaImage.objects.get(image_id=panorama_image_id)
        point_id = panorama_image_obj.point_id
        relate_image_list = PanoramaImage.objects.filter(point_id=point_id).all().order_by('-create_time')
        data = []

        for i in relate_image_list:
            record = {
                'title': i.point.point_name,
                'imageName': i.image_name,
                'uploader': i.batch.operator,
                'street': i.batch.region,
                'createTime': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'imageId': i.image_id,
                'longitude': i.longitude,
                'latitude': i.latitude,
                'yawDegree': i.yaw_degree,
                'batchId': i.batch_id,
                'imageWeight': i.image_height,
                'imagePath': i.image_path,
                'batchName': i.batch.batch_name,
                'count': i.count,
                'tileResolution': i.tile_resolution,
                'maxLevel': i.max_level,
                'status': i.status,
                'cubeResolution': i.cube_resolution,
                'pointId': i.point.point_id,
                'pointName': i.point.point_name,
            }
            data.append(record)
        response_data = {'code': 0, 'msg': '', 'data': data}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取相同全景点位的全景图异常{e}')
        return JsonResponse({'code': 500, 'msg': f'获取相同全景点位的全景图异常{e}'})


def upload_batch_list(request):
    """
    全景上传管理
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        batch_id = params.get('batchId')
        grid_id = params.get('gridId')
        limit = params.get('pageSize', 10)
        page = params.get('pageIndex', 1)
        batch_type = params.get('batchType', 0)
        filters = Q()
        if grid_id:
            filters &= Q(batch__grid_id=grid_id)
        if batch_id:
            filters &= Q(batch_id=batch_id)
        if request.session['role'] != 1:
            filters &= Q(grid_operator=request.session['username'])
        up_data_list = UploadBatch.objects.filter(filters).filter(batch_type=batch_type).all()
        if len(up_data_list) > 0:
            paginator = Paginator(up_data_list, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        for i in results:
            clue_count = Clue.objects.filter(panorama_image__upload_batch=i).count()
            record = {
                'id': i.id,
                'batch_id': i.batch_id,
                'grid_operator': i.grid_operator,
                'count': i.count,
                'clue_count': clue_count,
                "grid_id": i.batch.grid_id,
                'percent': 0,
                'status': i.status,
                "batch_name": i.batch.batch_name,
                "street": i.batch.street,
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)
        response_data = {'code': 0, 'msg': '', 'data': data, 'count': len(up_data_list)}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取相同全景点位的全景图异常{e}')
        return JsonResponse({'code': 500, 'msg': f'获取相同全景点位的全景图异常{e}'})


def export_clue_data(request):
    """
    导出线索数据
    """
    params = json.loads(request.body.decode('utf-8'))
    clue_type = params.get('clueType')
    clue_status = params.get('clueStatus')
    filters = Q()
    if clue_status:
        filters &= Q(status=clue_status)
    if clue_type:
        filters &= Q(clue_name=clue_type)
    clue_list_data = Clue.objects.filter(filters).all()
    # 准备数据列表
    features = []
    image_files = []
    # 创建临时工作目录
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    export_dir_name = f'clue_{timestamp}'
    export_dir = os.path.join(settings.BASE_DIR, 'static/exports', export_dir_name)
    # 创建导出目录结构
    os.makedirs(export_dir, exist_ok=True)
    image_dir = os.path.join(export_dir, 'images')
    data_dir = os.path.join(export_dir, 'data')
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    for clue in clue_list_data:
        file_path = os.path.join(settings.BASE_DIR, 'static/resultImg', clue.batch_id, clue.panorama_image_id,
                                 f"{clue.batch_id}-{clue.clue_id}-{clue.longitude}-{clue.latitude}.jpg")
        # 检查图片是否存在
        if os.path.exists(file_path):
            # 目标图片路径
            dest_image_name = f"{clue.clue_id}_{clue.clue_name}.jpg"
            dest_image_path = os.path.join(image_dir, dest_image_name)

            # 复制图片
            shutil.copy2(file_path, dest_image_path)
            image_files.append(dest_image_name)

        # 收集点位和属性信息
        features.append({
            'id': clue.clue_id,
            'clue_name': clue.clue_name,
            'status': clue.status,
            'batch_id': clue.batch_id,
            'panorama_image_id': clue.panorama_image_id,
            'longitude': float(clue.longitude) if clue.longitude else 0.0,
            'latitude': float(clue.latitude) if clue.latitude else 0.0,
        })
    # 创建 GeoDataFrame
    if features:
        # 提取坐标创建几何
        geometries = [
            Point(feature['longitude'], feature['latitude'])
            for feature in features
        ]

        # 创建属性DataFrame
        attributes_df = pd.DataFrame([{
            k: v for k, v in feature.items()
            if k not in ['longitude', 'latitude']
        } for feature in features])

        # 创建 GeoDataFrame
        gdf = gpd.GeoDataFrame(
            attributes_df,
            geometry=geometries,
            crs='EPSG:4326'  # WGS84坐标系
        )

        # 保存为多种格式
        shp_path = os.path.join(data_dir, 'clue_points.shp')
        gdf.to_file(shp_path, driver='ESRI Shapefile', encoding='utf-8')
    zip_filename = f'clue_{timestamp}.zip'
    zip_path = os.path.join(settings.MEDIA_ROOT, 'exports', zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:

        # 添加图片文件
        for root, dirs, files in os.walk(image_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, export_dir)
                zipf.write(file_path, arcname)

        # 添加数据文件
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, export_dir)
                zipf.write(file_path, arcname)

    # 准备HTTP响应
    with open(zip_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        response['Content-Length'] = os.path.getsize(zip_path)
    return response


def clue_list(request):
    """
    获取线索列表
    @param request:
    @return:
    """
    try:
        # c = Clue.objects.all()
        # for i in c:
        #     i.file_path = i.file_path.replace('pcw.windofmay.top', 'skyeye.isitai.cn')
        #     i.save()
        current_user = parse_jwt_token(request)
        county = current_user.county
        params = json.loads(request.body.decode('utf-8'))
        clue_type = params.get('keyword', '')
        status = params.get('status', '')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        if status:
            clues = Clue.objects.filter(clue_name__contains=clue_type, status=status,
                                        batch__grid__county=county).all().order_by('-clue_id')
        else:
            clues = Clue.objects.filter(clue_name__contains=clue_type, batch__grid__county=county).all().order_by(
                '-clue_id')
        data_list = []
        if len(clues) > 0:
            paginator = Paginator(clues, limit)
            results = paginator.page(page)
        else:
            results = []
        for clue_obj in results:
            records = {
                'clue_id': clue_obj.clue_id,
                'task_id': clue_obj.panorama_image_id,
                'center_x': clue_obj.center_x,
                'center_y': clue_obj.center_y,
                'longitude': clue_obj.longitude,
                'latitude': clue_obj.latitude,
                'label': clue_obj.clue_name,
                'position': clue_obj.position,
                'score': clue_obj.score,
                'yaw_degree': clue_obj.panorama_image.yaw_degree,
                'batch_id': clue_obj.batch_id,
                'panorama_image_lat': clue_obj.panorama_image.latitude,
                'panorama_image_lon': clue_obj.panorama_image.longitude,
                'address': clue_obj.address,
                'status': clue_obj.status,
                'image_path': clue_obj.file_path,
                'create_time': clue_obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data_list.append(records)
        response_data = {
            'code': 0,
            'msg': '',
            'data': data_list,
            'count': len(clues)
        }
        return JsonResponse(response_data)
    except Exception as e:
        print(f"查询线索详情失败，报错内容{e}")
        return JsonResponse({'code': 1, 'msg': str(e)})


def clue_view(request, clue_id):
    """
    线索图片查看
    @param request:
    @param clue_id:
    @return:
    """
    try:
        clue_obj = Clue.objects.get(clue_id=clue_id)
        path = clue_obj.file_path
        if not os.path.exists(path):
            path = os.path.join(settings.BASE_DIR, 'static/images', 'nophoto.png')
        with open(path, 'rb') as f:
            image_byte_array = f.read()

        # 创建 HttpResponse 对象，并设置 Content-Type 为 image/jpeg
        response = HttpResponse(content=image_byte_array, content_type='image/jpg')
        # 返回 HttpResponse 对象
        return response
    except Exception as e:
        logger.error(f'查看线索图片异常{e}')


def upload_batch_delete(request):
    """
    批量删除上传批次
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        ids = params.get('ids')
        try:
            for i in ids:
                panorama_image_obj_list = PanoramaImage.objects.filter(upload_batch_id=i).all()
                for panorama_image_obj in panorama_image_obj_list:
                    if panorama_image_obj:
                        # 先删除对应的线索
                        clue_objs = Clue.objects.filter(panorama_image=panorama_image_obj).all()
                        for clue_obj in clue_objs:
                            path = clue_obj.file_path
                            if os.path.exists(path):
                                os.remove(path)
                            clue_obj.delete()
                        panorama_image_path = panorama_image_obj.image_path
                        if os.path.exists(panorama_image_path):
                            os.remove(panorama_image_path)
                        layer_dir = os.path.join(settings.BASE_DIR, 'static/layers', str(panorama_image_obj.batch_id),
                                                 str(panorama_image_obj.image_id))
                        if os.path.exists(layer_dir):
                            shutil.rmtree(layer_dir)
                        result_dir = os.path.join(settings.BASE_DIR, 'static/resultImg',
                                                  str(panorama_image_obj.batch_id),
                                                  str(panorama_image_obj.image_id))
                        if os.path.exists(result_dir):
                            shutil.rmtree(result_dir)
                        panorama_image_obj.delete()
                upload_batch_obj = UploadBatch.objects.get(id=i)
                upload_batch_obj.delete()
            return JsonResponse({'code': 0, 'msg': f'删除成功!已删除{len(ids)}个上传记录'})
        except Exception as e:
            print(e)
            return JsonResponse({'code': 500, 'msg': f'删除失败!报错内容{str(e)}'})
    except Exception as e:
        logger.error(f"删除失败!报错内容{str(e)}")
        transaction.set_rollback(True)
        return JsonResponse({'code': 500, 'msg': f'删除失败!报错内容{str(e)}'})


def get_clue_data_by_id(request):
    """
    根据id查询线索
    @param request:
    @return:
    """
    try:
        clue_id = request.GET.get('clue_id')
        if clue_id == "-1":
            logger.error('数据获取失败！,clue_id == "-1"')
            return JsonResponse({'code': 400, 'msg': '数据获取失败！', 'data': {}})
        clue_obj = Clue.objects.filter(clue_id=clue_id).first()
        if clue_obj:
            panorama_image_obj = clue_obj.panorama_image
            response_data = {
                'code': 0,
                'msg': '',
                'data': {
                    'clue_id': clue_obj.clue_id,
                    'task_id': clue_obj.panorama_image_id,
                    'center_x': clue_obj.center_x,
                    'center_y': clue_obj.center_y,
                    'longitude': clue_obj.longitude,
                    'latitude': clue_obj.latitude,
                    'label': clue_obj.clue_name,
                    'position': clue_obj.position,
                    'score': clue_obj.score,
                    'status': clue_obj.status,
                    'yaw_degree': panorama_image_obj.yaw_degree,
                    'batch_id': clue_obj.batch_id,
                    'panorama_image_lat': panorama_image_obj.latitude,
                    'panorama_image_lon': panorama_image_obj.longitude,
                }
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'code': 400, 'msg': '数据获取失败！', 'data': {}})
    except Exception as e:
        logger.error(f'获取数据失败{e}')
        return JsonResponse({'code': 400, 'msg': f'获取数据失败{e}', 'data': {}})


def panorama_list_by_upload(request):
    return


def scene(request):
    """
    获取场景信息
    @param request:
    @return:
    """
    try:
        current_user = parse_jwt_token(request)
        county = current_user.county
        params = json.loads(request.body.decode('utf-8'))
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        keyword = params.get('keyword')
        if current_user.role == 1:
            scene_objs = Scene.objects.filter(scene_name__contains=keyword).all().order_by('-scene_id')
        else:
            scene_objs = Scene.objects.filter(scene_name__contains=keyword, operator__county=county).all().order_by(
                '-scene_id')
        if len(scene_objs) > 0:
            paginator = Paginator(scene_objs, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        for i in results:
            record = {
                'sceneId': i.scene_id,
                'sceneName': i.scene_name,
                'labels': i.labels,
                'operator': i.operator.username,
                'createTime': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)
        labels = ['堆土', '施工人员', '堆砖', '在建砖房', '塔吊', '物料提升机', '搅拌车', '板房棚房', '脚手架', '钢筋',
                  '挖掘机', '小轿车', '水泥管', '起重机',
                  '大巴',
                  '围挡', '翻斗车', '防尘网', '运输车', '搅拌机', '打桩机', '推土车', '压路车', '烟雾', '树', '翻土机',
                  "工程管", '水泥地面', '火焰', '工程车辆',
                  '撂荒地', '垃圾堆', '黑臭水体']
        response_data = {'code': 0, 'msg': '', 'data': data, 'count': len(scene_objs), 'labels': labels}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取场景信息失败{e}')
        return JsonResponse({'code': 500, 'msg': f'获取场景信息失败{e}'})


def scene_insert(request):
    """
    新增场景
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        scene_name = params.get('sceneName')
        labels = params.get('labels')
        Scene.objects.create(
            scene_name=scene_name,
            labels=labels,
            operator_id=request.session.get('user_id')
        )
        return JsonResponse({'code': 0, 'msg': f'场景{scene_name}新增成功'})
    except Exception as e:
        logger.error(f'新增场景失败{e}')
        return JsonResponse({'code': 500, 'msg': f'新增场景失败{e}'})


def scene_modify(request):
    """
    场景修改
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        scene_id = params.get('scene_id')
        scene_name = params.get('scene_name')
        labels = params.get('labels')
        Scene.objects.filter(scene_id=scene_id).update(
            scene_name=scene_name,
            labels=labels
        )
        return JsonResponse({'code': 0, 'msg': f'场景{scene_name}修改成功'})
    except Exception as e:
        logger.error(f'修改场景失败{e}')
        return JsonResponse({'code': 500, 'msg': f'修改场景失败{e}'})


def scene_delete(request):
    """
    删除场景
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            ids = params.get('ids')
            for i in ids:
                scene_obj = Scene.objects.get(scene_id=i)
                if scene_obj:
                    scene_obj.delete()
            return JsonResponse({'code': 0, 'msg': f'场景删除成功'})
        except Exception as e:
            logger.error(f'场景删除失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': f'场景删除失败{e}'})


def panorama_image_review(request):
    """
    全景图片线索复核提交
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            image_id = params.get('panoramaImageId')
            panorama_image_obj = PanoramaImage.objects.get(image_id=image_id)
            unchecked_count = Clue.objects.filter(status=0, panorama_image=panorama_image_obj).count()
            if unchecked_count == 0:
                panorama_image_obj.status = 2
                panorama_image_obj.save()
                p_count = PanoramaImage.objects.filter(batch=panorama_image_obj.batch, status=2).count()
                batch_obj = Batch.objects.get(batch_id=panorama_image_obj.batch_id)
                # 如果已判读的全景图等于批次的全景图数量，则批次完成
                print("已完成的数量", p_count, batch_obj.count, p_count == batch_obj.count)
                if p_count == batch_obj.count:
                    batch_obj.status = 4
                    batch_obj.save()
                return JsonResponse({"code": 0, 'msg': '复核成功'})
            return JsonResponse({"code": 400, 'msg': '尚有线索未判读，请判读后提交'})
        except Exception as e:
            logger.error(f'全景图片线索复核失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, 'msg': str(e)})


def clue_status(request):
    """
    线索判读
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            clue_id = params.get('id')
            status = params.get('status')
            clue_obj = Clue.objects.get(clue_id=clue_id)
            if clue_obj:
                clue_obj.status = status
                clue_obj.inspector_id = request.session.get('user_id')
                clue_obj.save()
                interpretation_count = Clue.objects.filter(batch_id=clue_obj.batch_id, status=0).count()
                return JsonResponse(
                    {"code": 0, 'msg': '判读成功', 'status': 0, 'interpretation_count': interpretation_count})
            else:
                logger.error("当前线索已删除或不存在，请刷新后重试！")
                return JsonResponse({"code": 404, 'msg': "当前线索已删除或不存在，请刷新后重试！"})
        except Exception as e:
            logger.error(f'线索判读失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, 'msg': f'线索判读失败{e}'})


@login_request
def grid_add(request):
    """
    新增网格 | POST
    @param request:
    @return:
    """
    temp_files_list = []
    current_user = parse_jwt_token(request)
    try:
        grid_shp = request.FILES.get('grid_shp')
        panorama_shp = request.FILES.get('panorama_shp')
        county = request.POST.get('county')
        shp_path = os.path.join(settings.BASE_DIR, 'static/shp')
        os.makedirs(shp_path, exist_ok=True)
        grid_zip_path = os.path.join(shp_path, grid_shp.name)
        panorama_zip_path = os.path.join(shp_path, panorama_shp.name)
        kml_folder = os.path.join(settings.BASE_DIR, 'static/kml', panorama_shp.name.split('.')[0])
        os.makedirs(kml_folder, exist_ok=True)
        if os.path.exists(grid_zip_path):
            os.remove(grid_zip_path)
        # 保存网格数据zip
        with open(grid_zip_path, 'wb+') as destination:
            for chunk in grid_shp.chunks():
                destination.write(chunk)
        temp_files_list.append(grid_zip_path)
        # 解压shp文件夹
        unzip_path = os.path.splitext(grid_zip_path)[0]
        unzip_file(grid_zip_path, unzip_path)
        temp_files_list.append(unzip_path)
        if os.path.exists(panorama_zip_path):
            os.remove(panorama_zip_path)
        # 保存全景点数据zip
        with open(panorama_zip_path, 'wb+') as destination:
            for chunk in panorama_shp.chunks():
                destination.write(chunk)
        temp_files_list.append(panorama_zip_path)
        # 解压shp文件夹
        unzip_path1 = os.path.splitext(panorama_zip_path)[0]
        unzip_file(panorama_zip_path, unzip_path1)
        temp_files_list.append(unzip_path1)
        grid_shp_path = find_shp_from_folder(unzip_path)
        grid_data = read_grid_shp(grid_shp_path)
        panorama_point_shp_path = find_shp_from_folder(unzip_path1)
        point_data = read_point_shp(panorama_point_shp_path)
        last_grid = Grid.objects.order_by('-order')
        kml_name = shp_to_kml(panorama_point_shp_path, kml_folder)
        temp_files_list.append(kml_folder)
        if last_grid:
            count = last_grid[0].order + 1
        else:
            count = 1

        for i in grid_data:
            is_exist = Grid.objects.filter(grid_name=i['grid_name'], street=i['street']).first()
            wgy = User.objects.filter(username=i['grid_operator']).first()
            if not is_exist:
                kml_path = os.path.join(kml_folder, kml_name + '.kml')
                while True:
                    file_id = f"62{random.randint(10000000000000, 99999999999999)}"
                    is_exist = BufferFile.objects.filter(file_id=file_id)
                    if not is_exist:
                        break
                BufferFile.objects.create(
                    file_id=file_id,
                    file_name=i['grid_name'] + '.kml',
                    file_extension='.kml',
                    file_path=kml_path,
                    owner=current_user.username,
                    file_type='kml',
                    file_size=os.path.getsize(kml_path)
                )
                Grid.objects.create(
                    grid_id=str(i['street_id']),
                    grid_name=i['grid_name'],
                    kml_path=file_id,
                    street=i['street'],
                    county=county,
                    center_x=i['center_x'],
                    center_y=i['center_y'],
                    count=0,
                    grid_operator=wgy,
                    uploader_id=current_user.id
                )
                count += 1
                create_log(request, current_user.username, current_user.username, "add",
                           "新增了网格《" + i['grid_name'] + "》")
            else:
                continue
        count1 = 1
        for j in point_data:
            is_exists = PointLocation.objects.filter(longitude=j['center_x'], latitude=j['center_y']).first()
            current_grid = Grid.objects.filter(grid_name=j['grid_name']).first()
            if not is_exists:
                PointLocation.objects.create(
                    point_id=current_grid.grid_id + f"{count1:03d}",
                    point_name=f'全景点位{count1}',
                    grid=current_grid,
                    longitude=j['center_x'],
                    latitude=j['center_y'],
                )
                current_grid.count += 1
                current_grid.save()
                count1 += 1
            else:
                is_exists.grid = current_grid
                is_exists.point_name = f'全景点位{count1}'
                is_exists.point_id = current_grid.grid_id + f"{count1:03d}"
                current_grid.count += 1
                is_exists.save()
        response_data = {'code': 0, 'msg': '新增成功！', 'data': []}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'新增失败{e}')
        return JsonResponse({'code': 500, 'msg': '新增失败！', 'data': []})


@login_request
def grid_list(request):
    """
    根据参数获取网格信息 | POST
    @param request:
    @return:
    """
    try:

        response_data = {'code': 0, 'msg': '', 'data': []}
        params = json.loads(request.body.decode('utf-8'))
        street = params.get('street', '')
        keyword = params.get('keyword', '')
        limit = params.get('pageSize', 10)
        page = params.get('pageIndex', 1)
        current_user = parse_jwt_token(request)
        county = current_user.county
        if current_user.role == 1:
            if street:
                grid_objs = Grid.objects.filter(grid_name__contains=keyword, street=street, county=county).all()
            else:
                grid_objs = Grid.objects.all()

        else:
            if street:
                grid_objs = Grid.objects.filter(grid_name__contains=keyword, street=street, county=county).all()
            else:
                grid_objs = Grid.objects.filter(grid_name__contains=keyword, county__contains=county[0:4]).all()
        if len(grid_objs) > 0:
            paginator = Paginator(grid_objs, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        if results:
            for result in results:
                dict_value = {
                    'grid_id': result.grid_id,
                    'grid_name': result.grid_name,
                    'kml_path': result.kml_path,
                    'count': result.count,
                    'street': result.street,
                    'county': result.county,
                    'grid_operator': result.grid_operator.username if result.grid_operator else '-',
                    'uploader': result.uploader.username,
                    'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                data.append(dict_value)
        response_data['data'] = data
        response_data['total'] = len(grid_objs)

        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'根据参数获取网格信息失败{e}')
        return JsonResponse({'code': 500, 'msg': f'根据参数获取网格信息失败{e}', 'data': []})


@login_request
def grid_delete(request):
    """
    删除网格
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            response_data = {'code': 0, 'msg': '删除成功！', 'data': []}
            params = json.loads(request.body.decode('utf-8'))
            username = request.session['username']
            grid_ids = params.get('grid_ids')
            for grid_id in grid_ids:
                grid_obj = Grid.objects.filter(grid_id=grid_id).first()
                PointLocation.objects.filter(grid_id=grid_id).delete()
                grid_obj.delete()
            create_log(request, username, username, "delete",
                       f"删除了网格《{grid_ids}》")
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'删除网格失败{e}')
            transaction.set_rollback(True)
            create_log(request, username, username, "delete",
                       f"删除了网格《{grid_ids}》", 0, str(e)[0:254])
            return JsonResponse({'code': 500, 'msg': f'删除失败！{str(e)}', 'data': []})


@login_request
def point_location(request):
    """
    获取全景点位信息
    @param request:
    @return:
    """
    try:
        current_county = request.session.get('county')
        grid_obj = Grid.objects.filter(county=current_county).all()
        response_data = {'code': 0, 'msg': '获取成功！', 'data': []}
        data = []
        for i in grid_obj:
            results = PointLocation.objects.filter(grid=i).all()
            for result in results:
                latest_time = ''
                panorama_image_list = PanoramaImage.objects.filter(point_id=result.point_id).all().values('image_id',
                                                                                                          'image_name',
                                                                                                          'longitude',
                                                                                                          'latitude',
                                                                                                          'point_id',
                                                                                                          'create_time')
                sorted_query_set = sorted(panorama_image_list, key=lambda x: x['create_time'], reverse=True)

                if len(sorted_query_set) > 0:
                    latest_obj = sorted_query_set[0]
                    latest_time = latest_obj['create_time'].strftime('%Y-%m-%d %H:%M:%S')
                record = {
                    "point_id": result.point_id,
                    "point_name": result.point_name,
                    "longitude": result.longitude,
                    "latitude": result.latitude,
                    "grid_name": result.grid.grid_name,
                    "panorama_image_list": list(panorama_image_list),
                    "grid_operator": result.grid.grid_operator.username if result.result.grid_operator else '-',
                    'latest_time': latest_time
                }
                data.append(record)
        response_data['data'] = data
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取全景点位信息失败{e}')
        return JsonResponse({'code': 500, 'msg': f'获取失败！{str(e)}', 'data': []})


def build_tree(divisions, parent_id=0):
    """
    递归查询省市区县街道
    @param divisions:
    @param parent_id:
    @return:
    """
    try:
        tree = []
        for division in divisions:
            if division.parent_id == parent_id:
                children = build_tree(divisions, division.region_id)
                if children:
                    division.children = children
                else:
                    grand_children_regions = Grid.objects.filter(street=division.region_name).all()
                    grand_children_region_list = []
                    for k in grand_children_regions:
                        grand_children_records = {
                            'value': k.grid_id,
                            'label': k.grid_name
                        }
                        grand_children_region_list.append(grand_children_records)
                    division.children = grand_children_region_list
                    children = grand_children_region_list
                tree.append({
                    'id': division.region_id,
                    'label': division.region_name,
                    'value': division.region_code,
                    'children': children
                })
        return tree
    except Exception as e:
        logger.error(f'数据获取失败{e}')
        return JsonResponse({'code': 500, 'msg': '数据获取失败！', 'data': str(e)})


def batch_status(request):
    """
    获取批次状态
    @param request:
    @return:
    """
    try:
        dict_data = SysDictData.objects.filter(dict_type='Batch_Status').all()
        data = []
        for i in dict_data:
            data.append({'value': i.value, 'name': i.name})
        return JsonResponse({'code': 0, 'msg': '数据获取成功！', 'data': data})
    except Exception as e:
        logger.error(f'数据获取失败:{e}')
        return JsonResponse({'code': 500, 'msg': f'数据获取失败:{e}', 'data': []})


def change_status(request):
    """
    结束批次状态
    Args:
        request:

    Returns:

    """
    params = json.loads(request.body.decode('utf-8'))
    batch_id = params.get('batchId')
    batch_obj = Batch.objects.filter(batch_id=batch_id).first()
    if batch_obj:
        panorama_image_undo_count = PanoramaImage.objects.filter(batch=batch_obj, status=1).count()
        if panorama_image_undo_count > 0:
            return JsonResponse({'code': 500, 'msg': '该批次下有未判读的图片，请判读完成后再结束批次！', 'data': []})
        batch_obj.status = 4
        batch_obj.save()
    return JsonResponse({'code': 0, 'msg': '批次结束判读成功！', 'data': []})


@login_request
def batch_add(request):
    """
    新建批次
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            start_date = params.get('startDate')
            end_date = params.get('endDate')
            interval_days = int(params.get('intervalDays'))
            grid_obj = params.get('region')  # 区-街道-网格
            grid_obj_list = grid_obj.split('/')
            region_zw = params.get('regionZw')  # 区域网格的中文标签
            regionZw_list = region_zw.split('/')
            ids = params.get('resourceIdList')
            changeDetect = params.get('changeDetect')
            grid_id = grid_obj_list[-1]
            region_name = regionZw_list[-1]
            # 计算时间的交集
            # 将字符串日期转换为datetime对象
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            query_objs = Batch.objects.filter(grid_id=grid_id)
            for obj in query_objs:
                obj_startdate = datetime.datetime.strptime(str(obj.start_date), '%Y-%m-%d')  # 示例数据开始日期
                obj_enddate = datetime.datetime.strptime(str(obj.end_date), '%Y-%m-%d')  # 示例数据结束日期
                if max(start_date, obj_startdate) <= min(end_date, obj_enddate):
                    print({"code": 500, "msg": "新建任务失败,该区域已存在批次，请重新选择!!", "data": []})
                    logger.error("新建任务失败,该区域已存在批次，请重新选择!!")
                    return JsonResponse({"code": 500, "msg": "新建任务失败,该区域已存在批次，请重新选择!!", "data": []})

            data_list = calculate_date_ranges(start_date, end_date, interval_days)
            count = 1
            for i in data_list:
                year, month = i['start_date'].split('-')[0], i['start_date'].split('-')[1]
                is_exists = Batch.objects.filter(year=year, month=month, grid_id=grid_id).all().order_by('-order')
                if is_exists:
                    order = is_exists[0].order + 1
                else:
                    order = count
                batch_name = f"{year}年{month}月第{order}批次"
                grid_obj = Grid.objects.filter(grid_id=grid_id).first()
                if not grid_obj:
                    grid_obj = Grid.objects.filter(Q(grid_name=region_name) | Q(street=region_name)).first()
                current_batch = Batch.objects.create(
                    batch_id=grid_id + str(i['start_date'].replace('-', '')),
                    batch_name=batch_name,
                    start_date=i['start_date'],
                    end_date=i['end_date'],
                    grid_id=grid_id,
                    year=year,
                    month=month,
                    street=grid_obj.street,
                    count=PointLocation.objects.filter(grid_id=grid_id).count(),
                    region=region_name,
                    operator=params.get('username'),
                    order=order,
                    change_detection=changeDetect,
                )
                count += 1
                for i in ids:
                    BatchResource.objects.create(
                        batch=current_batch,
                        resource_id=i
                    )
            return JsonResponse({"code": 0, "msg": "新建任务成功！", "data": []})
        except Exception as e:
            logger.error(f'新建批次失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, "msg": str(e), "data": []})


def filter_batchs(status=None, batch_name=None, grid_name=None, start_date=None, end_date=None, county=None,
                  batch_type=None, ):
    """
    根据提供的查询条件过滤线索。

    参数:
    - status (str): 状态
    - batch_name (str): 线索名称
    - grid_name (str): 网格名称
    - start_date (datetime): 开始日期
    - end_date (datetime): 结束日期

    返回:
    - QuerySet: 过滤后的线索查询集
    """
    # 构建查询条件
    filters = Q()
    if status:
        filters &= Q(status=status)
    if batch_name:
        filters &= Q(batch_name__contains=batch_name)
    if grid_name:
        filters &= Q(grid_id=grid_name)
    if start_date:
        filters &= Q(start_date__gte=start_date)
    if end_date:
        filters &= Q(end_date__lte=end_date)
    if county:
        filters &= Q(grid__county=county) | Q(grid__county__isnull=True) | Q(street="-")
    if batch_type:
        filters &= Q(batch_type=batch_type)
    # 应用过滤条件
    batches = Batch.objects.filter(filters).order_by('-batch_id')
    return batches



@login_request
def batch_list(request):
    """
    根据参数获取批次信息 | POST
    @param request:
    @return:
    """
    try:
        response_data = {'code': 0, 'msg': '', 'data': []}
        params = json.loads(request.body.decode('utf-8'))
        status = params.get('status')
        keyword = params.get('keyword')
        start_date = params.get('startDate')
        end_date = params.get('endDate')
        grid_name = params.get('grid_name')
        batch_id = params.get('batchId')
        batch_type = params.get('batchType')
        limit = params.get('pageSize', 10)
        page = params.get('pageIndex', 1)
        # 将日期字符串转换为 datetime 对象
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        current_user = parse_jwt_token(request)
        county = current_user.county
        batch_objs = filter_batchs(status, keyword, grid_name, start_date, end_date, county, batch_type)
        if len(batch_objs) > 0:
            paginator = Paginator(batch_objs, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        if results:
            for result in results:
                dict_value = {
                    'grid_id': result.grid.grid_id if result.grid else '-',
                    'batch_name': result.batch_name,
                    'grid_operator_name': result.grid.grid_operator.username if result.grid else '-',
                    'batch_id': result.batch_id,
                    'total_count': result.count,
                    'done_count': str(PanoramaImage.objects.filter(batch=result).count()) + '/' + str(
                        result.count),
                    'suspected_clue_count': Clue.objects.filter(status=0, batch=result).count(),
                    'pending_clue_count': Clue.objects.filter(status__in=[2, 3], batch=result).count(),
                    'confirmed_clue_count': Clue.objects.filter(status=5, batch=result).count(),
                    'fcw': Clue.objects.filter(batch=result, clue_name='防尘网').count(),
                    'wd': Clue.objects.filter(batch=result, clue_name='围挡').count(),
                    'jj': Clue.objects.filter(batch=result,
                                              clue_name__in=['挖掘机', '搅拌车', '塔吊', '起重机', '搅拌机', '打桩机', '翻土机']).count(),
                    'batch_type': result.batch_type,
                    'start_date': result.start_date,
                    'end_date': result.end_date,
                    'pointType': result.batch_type,
                    'status': "●" + SysDictData.objects.filter(value=result.status,
                                                               dict_type='Batch_Status').first().name,
                    'region': result.region,
                    'orginalStatus': result.status,
                    'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                data.append(dict_value)
        response_data['data'] = data
        response_data['total'] = len(batch_objs)
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'根据参数获取批次信息失败：{e}')
        return JsonResponse({'code': 500, 'msg': str(e)})


def temp_detection_batch_data(request):
    """
    获取临时检测批次数据
    """
    try:
        current_user = parse_jwt_token(request)
        now = datetime.datetime.now()
        county = current_user.county

        # 正则提取 6 位数字行政编码
        result = re.search(r'(\d{6})', county)

        # 拿到编码
        county = result.group(1) if result else ""
        grid = f"{county}001"
        date_time = now.strftime("%Y%m%d")
        year = str(now.year)
        month = str(now.month)

        order = (
                Batch.objects.filter(grid_id=grid, year=year, month=month, batch_type=1)
                .count()
                + 1
        )
        BATCH_NAME_TEMPLATE = '%s%s%s年%s月第%d批次'
        batch_name = f"临时批次{BATCH_NAME_TEMPLATE % ('', '', year, month, order)}"
        batch_id = f"LS{grid}{date_time}"

        batch = Batch.objects.filter(batch_id=batch_id).first()
        if batch:
            batch_id = batch.batch_id
            batch_name = batch.batch_name or batch_name

        return JsonResponse({'code': 0, 'data': {"batchId": batch_id, "batchName": batch_name}, 'msg': '查询成功！'})
    except Exception as e:
        logger.exception("临时全景点上传批次信息初始化失败")
        return JsonResponse({'code': 1, 'data': {}, 'msg': f'查询失败！{e}'})


def get_batch_by_id(request):
    """
    根据批次id获取批次信息
    """
    batch_id = request.GET.get('batch_id')
    obj = Batch.objects.filter(batch_id=batch_id).first()
    if not obj:
        return JsonResponse({'code': 1, 'msg': "批次未找到"})
    t_upload_batch_list = UploadBatch.objects.filter(batch_id=batch_id).all()
    remaining_count = obj.count
    for i in t_upload_batch_list:
        remaining_count -= i.count
    obj.remaining_count = remaining_count
    data = {
        "pk_id": obj.batch_id,
        "count": obj.count,
        "status": obj.status,
        "region": obj.region,
        "grid_id": obj.grid_id,
        "street": obj.street,
        "batch_name": obj.batch_name,
        "year": obj.year,
        "month": obj.month,
        "remaining_count": obj.remaining_count,
    }
    return JsonResponse({'code': 0, 'data': data})


@login_request
def batch_delete(request):
    """
    删除批次
    """
    params = json.loads(request.body.decode('utf-8'))
    batch_ids = params.get('batchIds')
    try:
        for i in batch_ids:
            # 查询批次对象
            batch = Batch.objects.get(batch_id=i)
            if batch:
                panorama_objs = PanoramaImage.objects.filter(batch=batch).all()
                for panorama_obj in panorama_objs:
                    panorama_path = panorama_obj.image_path
                    if os.path.exists(panorama_path):
                        os.remove(panorama_path)
                    Clue.objects.filter(panorama_image=panorama_obj).delete()
                    panorama_obj.delete()
                UploadBatch.objects.filter(batch_id=i).delete()
                layer_dir = os.path.join(settings.BASE_DIR, 'static/layers', str(i))
                if os.path.exists(layer_dir):
                    shutil.rmtree(layer_dir)
                result_dir = os.path.join(settings.BASE_DIR, 'static/resultImg', str(i))
                if os.path.exists(result_dir):
                    shutil.rmtree(result_dir)
                batch.delete()
        return JsonResponse({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        logger.error(f'删除失败,报错内容：{str(e)}')
        return JsonResponse({'code': 500, 'msg': f'删除失败,报错内容：{str(e)}'})


def files_upload(request):
    """
    上传文件接口
    @param request:
    @return:
    """
    try:
        myFile = request.FILES.get("file", None)
        if myFile:
            current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            save_path = os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name)
            destination = open(save_path, 'wb+')
            for chunk in myFile.chunks():
                destination.write(chunk)
            destination.close()
            if myFile.name.endswith('.zip'):
                unzip_path = os.path.join(settings.BASE_DIR, 'static', 'temp', current_time)
                safe_unzip(save_path, unzip_path)
                return JsonResponse({'code': 0, 'msg': '上传成功', 'unzip_path': current_time})
            else:
                return JsonResponse({'code': 500, 'msg': '上传失败，请上传zip格式文件！'})
        else:
            return JsonResponse({'code': 500, 'msg': '上传失败，文件为空，请选择文件！'})
    except Exception as e:
        logger.error(f'上传失败: {str(e)}')
        return JsonResponse({'code': 500, 'msg': '上传失败', 'error': str(e)})


def add_label(request):
    """
    保存目标信息
    @param request:
    @return:
    """
    logger.info("接受保存目标信息请求")
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            pixel_x = int(params.get('pixelX', 1))
            pixel_y = int(params.get('pixelY', 1))
            class_name = params.get('className')
            pixel = params.get('pixel', '')
            image_id = params.get('panoramaImageId')
            yaw = params.get('yaw', '')
            pitch = params.get('pitch', '')
            panorama_obj = PanoramaImage.objects.get(image_id=image_id)
            lat, lon = image_to_latlon(panorama_obj.latitude, panorama_obj.longitude, panorama_obj.height, yaw, pitch,
                                       panorama_obj.yaw_degree)
            crop_save_folder = panorama_obj.image_path
            # 绘制图
            origin_img = Image.open(crop_save_folder)
            # 裁剪图片
            cropped_img = origin_img.crop((pixel_x - 400, pixel_y - 400, pixel_x + 400, pixel_y + 400))
            clue_obj = Clue.objects.create(
                center_x=pixel_x,
                center_y=pixel_y,
                clue_name=class_name,
                latitude=lat,
                longitude=lon,
                position=pixel,
                status=2,
                panorama_image_id=image_id,
                batch_id=panorama_obj.batch_id,
                clue_source='人工'
            )
            p_path = os.path.join(settings.BASE_DIR, 'static/resultImg', panorama_obj.batch_id,
                                       panorama_obj.image_id)
            os.makedirs(p_path, exist_ok=True)
            output_path = os.path.join(p_path, str(clue_obj.clue_id) + '.jpg')
            # 保存裁剪后的图片
            # 打开前景图片
            foreground = Image.open(os.path.join(settings.BASE_DIR, 'static/images/red.png'))
            w, h = cropped_img.size
            # 粘贴前景图片到背景图片上
            cropped_img.paste(foreground, (int(w / 2), int(h / 2)), foreground)
            cropped_img.save(output_path)

            clue_obj.file_path = f"http://{common_config['host']}:{common_config['port']}/static/resultImg/{panorama_obj.batch_id}/{panorama_obj.image_id}/{str(clue_obj.clue_id)}.jpg"
            clue_obj.save()
            response_data = {'code': 0, 'msg': '保存成功！', 'data': {'clue_id': clue_obj.clue_id}}
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'保存目标信息失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': str(e)})


def point_list_by_batch(request):
    """
    根据批次查询已上传的点位
    @param request:
    @return:
    """
    try:
        batch_id = request.GET.get('batch_id')
        batch_obj = Batch.objects.get(batch_id=batch_id)
        point_objs = PointLocation.objects.filter(grid_id=batch_obj.grid_id).all()
        data = []
        for i in point_objs:
            p = PanoramaImage.objects.filter(batch_id=batch_id, point=i).first()
            records = {
                'point_id': i.point_id,
                'longitude': i.longitude,
                'latitude': i.latitude,
                'point_name': i.point_name,
                'status': 0
            }
            if p:
                records['status'] = 1
            data.append(records)
        return JsonResponse({"code": 0, 'data': data, 'msg': '数据获取成功'})
    except Exception as e:
        logger.error(f'数据获取失败{e}')
        return JsonResponse({"code": 500, 'data': [], 'msg': f'数据获取失败{e}'})


def clue_location(request):
    """
    线索打点
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            clue_id = params.get('clue_id')
            longitude = params.get('longitude')
            latitude = params.get('latitude')
            clue_obj = Clue.objects.filter(clue_id=clue_id).first()
            if clue_obj:
                address = find_village_by_point(settings.SHP_FILE_PATH, latitude, longitude)
                clue_obj.longitude = longitude
                clue_obj.latitude = latitude
                clue_obj.address = address
                clue_obj.save()
                return JsonResponse({"code": 0, 'msg': '线索打点成功'})
            else:
                logger.error(f'线索打点失败: 线索不存在')
                return JsonResponse({"code": 404, 'msg': '线索不存在'})
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f'线索打点失败: {str(e)}')
            return JsonResponse({"code": 500, 'msg': '线索打点失败'})


def frame_area(request):
    """
    新增不检测区域
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body)
            polygon = params.get('polygon')
            pixel = params.get('pixel')
            area_type = params.get('area_type', 0)
            some_poly = shapely_polygon(pixel)
            x, y = some_poly.centroid.coords.xy
            x, y = x.tolist()[0], y.tolist()[0]
            FrameArea.objects.create(
                name=params.get('name'),
                polygon=polygon,
                area_type=area_type,
                center_x=x,
                center_y=y,
                point_id=params.get('point_id'),
                pixel=pixel
            )
            return JsonResponse({"msg": '新增成功', 'code': 0})
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f'新增不检测区域失败: {str(e)}')
            return JsonResponse({"code": 500, 'msg': '新增不检测区域失败'})


def frame_area_list(request):
    """
    获取多边形区域列表
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('keyword')
        point_id = params.get('pointId')
        panorama_image_id = params.get('imageId')
        response_data = {'code': 0, 'msg': '', 'data': []}
        if keyword is None:
            data_obj = FrameArea.objects.filter(point_id=point_id).all().order_by('-id')
        else:
            data_obj = FrameArea.objects.filter(name__contains=keyword, point_id=point_id).all().order_by('-id')
        panorama_obj = PanoramaImage.objects.get(image_id=panorama_image_id)
        no_detection_area_list = []
        polygon_list = []

        for i in data_obj:
            xy_list = []
            polygons = ast.literal_eval(i.polygon)
            for j in polygons:
                # [[-39.705659009002574, 91.06303224538604], [-55.629766898950045, 22.529056448187887], [-74.8571602634237, -1.4616145294985898], [-47.91825175296964, 128.56593117885507]]
                lat, lon = image_to_latlon(panorama_obj.latitude, panorama_obj.longitude, panorama_obj.height, j[1],
                                           j[0],
                                           panorama_obj.yaw_degree)
                xy_list.append([lat, lon])
            record = {
                'id': i.id,
                'name': i.name,
                'center_x': i.center_x,
                'center_y': i.center_y,
                'point_id': i.point_id,
                'polygon': i.polygon,
                'pixel': i.pixel,
                'xy': xy_list,
                'status': i.status,
                'area': i.area,
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            if i.area_type == 0:
                no_detection_area_list.append(record)
            else:
                polygon_list.append(record)
        response_data['data'] = {
            'no_detection_area_list': no_detection_area_list,
            'polygon_list': polygon_list
        }
        response_data['count'] = len(data_obj)
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取不检测区域列表失败：{e}')
        return JsonResponse({'code': 500, 'msg': f'获取不检测区域列表失败：{e}', 'data': []})


def get_target_area_list(request):
    try:
        params = json.loads(request.body.decode('utf-8'))
        panorama_image_id = params.get('image_id')
        data = []
        result_objs = Clue.objects.filter(panorama_image_id=panorama_image_id, clue_source='人工').all()
        for j in result_objs:
            panorama_image_obj = PanoramaImage.objects.get(image_id=j.panorama_image_id)
            position_list = ast.literal_eval(j.position)
            polygons = []
            for i in position_list:
                # 将像素坐标转换为弧度
                yaw_rad = (i[0] / panorama_image_obj.image_width) * 2 * math.pi - math.pi
                pitch_rad = math.pi / 2 - (i[1] / panorama_image_obj.image_height) * math.pi
                # 将弧度转换为角度
                x = yaw_rad * 180 / math.pi
                y = pitch_rad * 180 / math.pi
                polygons.append([y, x])
            record = {
                'id': j.clue_id,
                'name': j.clue_name,
                'polygon': polygons,
            }
            data.append(record)
        return JsonResponse({'code': 0, 'msg': '获取目标区域列表成功', 'data': data})

    except Exception as e:
        logger.error(f'获取目标区域列表失败：{e}')
        return JsonResponse({'code': 500, 'msg': f'获取目标区域列表失败：{e}', 'data': []})


def frame_area_delete(request):
    """
    删除不检测区域
    @param request:
    @return:
    """
    logger.info(f'删除不检测区域请求参数')
    try:
        response_data = {'code': 0, 'msg': 'success', 'data': {}}
        if request.method == 'POST':
            params = json.loads(request.body)
            frame_area_id = params.get('frame_area_id')
            is_exists = FrameArea.objects.filter(id=frame_area_id)
            if is_exists:
                is_exists.delete()
                return JsonResponse(response_data)
            else:
                return JsonResponse({'code': 1, 'msg': '删除失败，该区域不存在', 'data': {}})
    except Exception as e:
        logger.error(f'删除不检测区域失败：{e}')
        return JsonResponse({'code': 500, 'msg': f'删除不检测区域失败：{e}', 'data': {}})


def get_upload_areas(request):
    """
    根据全景点ID获取不检测区域
    """
    params = json.loads(request.body.decode('utf-8'))
    response_data = {'code': 0, 'data': [], 'msg': ''}
    return JsonResponse(response_data)


def target_area_clue_delete(request):
    """
    删除新增目标区域线索
    Args:
        request:

    Returns:

    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        clue_id = params.get('clue_id')
        result_obj = Clue.objects.filter(clue_id=clue_id).first()
        if result_obj:
            result_obj.delete()
            return JsonResponse({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': f'删除失败：{e}', 'data': []})


@login_request
def info(request):
    """
    首页信息统计
    @param request:
    @return:
    """
    try:
        # 线索类型分布
        user_id = request.session.get('user_id')
        clue_objs = Clue.objects.filter(batch__grid__grid_operator_id=user_id).values('clue_name').annotate(
            count=Count('clue_name'))
        clue_type_count_list = []
        for i in clue_objs:
            clue_type_count_list.append({
                'name': i['clue_name'],
                'value': i['count']
            })
        # 线索区域分布
        batch_objs = Batch.objects.filter(grid__grid_operator_id=request.session.get('user_id')).all()
        clue_area_count_list = []
        for i in batch_objs:
            clue_area_count_list.append({
                'name': i.batch_name,
                'value': i.count - PanoramaImage.objects.filter(batch_id=i.batch_id).count()
            })
        # 已处理的批次数量
        done_batch_count = Batch.objects.filter(status=2, grid__grid_operator_id=user_id).count()
        c = Batch.objects.filter(status__in=[0, 1], grid__grid_operator_id=user_id).all()
        todo_list = []
        for i in c:
            surplus_count = i.count - PanoramaImage.objects.filter(batch=i).count()
            todo_list.append({
                'text': f"【{i.start_date}】{i.batch_name}尚有{surplus_count}张全景图待上传",
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'batch_id': i.batch_id,
            })
        c = UploadBatch.objects.filter(grid_operator=request.session['username']).all()
        done_list = []
        for i in c:
            done_list.append({
                'text': f"【{i.create_time.strftime('%Y-%m-%d')}】{i.batch.batch_name}上传了{i.count}张全景图",
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
            # 查询所有记录，并按月份分组统计数量
        monthly_counts = (
            Clue.objects
                .annotate(month=ExtractMonth('create_time'))
                .values('month')
                .annotate(total=Count('clue_id'))
                .order_by('month')
        )

        # 创建一个字典来存储查询结果
        counts_dict = {item['month']: item['total'] for item in monthly_counts}

        # 创建一个包含所有月份的列表
        all_months = range(1, 13)

        # 使用列表推导式填充完整的结果集
        full_monthly_counts = [{'month': month, 'total': counts_dict.get(month, 0)} for month in all_months]

        month_list = []
        count_list = []
        for entry in full_monthly_counts:
            month_list.append(entry['month'])
            count_list.append(entry['total'])
        recent_seven_days_count = []
        seven_days = get_recent_seven_day()

        for i in seven_days:
            p_count = PanoramaImage.objects.filter(upload_batch__grid_operator=request.session['username']).filter(
                create_time__year=i.split('-')[0], create_time__month=i.split('-')[1],
                create_time__day=i.split('-')[2]).count()
            recent_seven_days_count.append(p_count)

        response_data = {
            'code': 0,
            'msg': '',
            'data': {
                'clue_type_count_list': clue_type_count_list,
                'clue_area_count_list': clue_area_count_list,
                'done_batch_count': done_batch_count,
                'todo_list': todo_list,
                'done_list': done_list,
                'month_list': month_list,
                'count_list': count_list,
                'recent_seven_days_data': seven_days,
                'recent_seven_days_count': recent_seven_days_count
            }
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取首页信息失败{e}')
        return JsonResponse({'code': 500, 'msg': f'获取首页信息失败{e}'})


def data_info(request):
    """
    大屏统计
    @param request:
    @return:
    """
    try:
        current_user = parse_jwt_token(request)
        county = current_user.county
        grid_operator_count = User.objects.filter(role=2,county=county).count()
        clue_count = Clue.objects.filter(batch__grid__county=county).count()
        grid_count = Grid.objects.filter(county=county).count()
        point_count = PointLocation.objects.filter(grid__county=county).count()
        batch_count = Batch.objects.filter(grid__county=county).count()
        upload_batch_count = UploadBatch.objects.filter(batch__grid__county=county).count()
        clue_effective_count = Clue.objects.filter(status=2,batch__grid__county=county).count()
        clue_invalid_count = Clue.objects.filter(status=1,batch__grid__county=county).count()
        response_data = {
            'code': 0,
            "data": {
                "grid_operator_count": grid_operator_count,
                "clue_count": clue_count,
                "grid_count": grid_count,
                "point_count": point_count,
                "batch_count": batch_count,
                "upload_batch_count": upload_batch_count,
                "clue_effective_count": clue_effective_count,
                "clue_invalid_count": clue_invalid_count,
            },
            "msg": "数据获取成功！"
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"获取大屏统计信息：{str(e)}")
        return JsonResponse({'code': 500, 'msg': '获取大屏统计信息失败！'})


def download(request, file_id):
    """
    通用文件下载接口
    :param file_id: 文件ID
    :param request: 请求对象
    :return: 文件流
    """
    try:
        file_obj = BufferFile.objects.filter(file_id=file_id).first()
        file_name = file_obj.file_name
        file_path = file_obj.file_path
        # 设置响应头
        # StreamingHttpResponse将文件内容进行流式传输，数据量大可以用这个方法
        if not os.path.exists(file_path):
            logger.error(f"文件ID为{file_id}，文件路径为{file_path}的文件未找到！")
            return JsonResponse({"error": "文件未找到"}, status=404)
        response = StreamingHttpResponse(file_iterator(file_path))
        # 以流的形式下载文件,这样可以实现任意格式的文件下载
        response['Content-Type'] = 'application/octet-stream'
        # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(escape_uri_path(file_name))
        logger.info(f"文件ID为{file_id}，文件名为{file_name}的文件已下载成功！")
        return response
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return JsonResponse({"error": "文件未找到"}, status=404)


def message_notify(request):
    """
    {
    "notify_type": "file_uploaded",
    "notify_time": "2023-11-07T12:00:00.582627+00:00",
    "data": {
        "organization_id": "Organization ID",
        "workspace_id": "Project ID",
        "file": {
            "id": "File ID",
            "name": "File Name",
            "object_key": "Object Storage Key",
            "type": 5 // 5-Flight route files，7-3D mapping files
            }
        }
    }
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = request.body
            params = json.loads(params)
            file_id = params['data']['file']['id']
            url = f'https://es-flight-api-cn.djigate.com/storage/api/v1.0/files/{file_id}'
            payload = {}
            headers = {
                'X-Organization-Key': 'cce120da42440bc52ae693b5356f64fb4fb71ea421f6587201d07e13f16bdb02',
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
            }

            resp = requests.get(url=url, payload=payload, headers=headers).json()
            download_url = resp['data']['url']
            save_path = os.path.join(settings.BASE_DIR,
                                     'static/temp/dikong/' + str(uuid.uuid1()).replace('-', '') + '.jpg')
            print(f"获取到的图片下载地址为{download_url}")
            try:
                # 发起 GET 请求获取图片数据
                response = requests.get(save_path, stream=True)
                # 检查响应状态码是否为 200（成功）
                if response.status_code == 200:
                    # 以二进制写模式打开文件
                    with open(save_path, 'wb') as file:
                        # 写入图片数据
                        file.write(response.content)
                    Notify.objects.create(
                        file_id=file_id,
                        save_path=save_path,
                        url=download_url,
                        notify_type=params['notify_type']
                    )
                    print(f"全景图已保存到{save_path}")
                else:
                    print(f"全景图保存失败: {response.status_code}")
                    logger.error(f"全景图保存失败: {response.status_code}")
            except Exception as e:
                print(f"An error occurred: {e}")
                logger.error(f'message_notify接口失败：{e}')
            return JsonResponse({'code': 0, 'msg': '数据已接收！'})
        except Exception as e:
            logger.error(f'message_notify接口失败：{e}')


def clue_entry(request):
    """
    线索录入
    @param request:
    @return:
    """
    params = json.loads(request.body.decode('utf-8'))
    status = params.get('status')
    verification_conclusion = params.get('verification_conclusion')
    clue_id = params.get('clue_id')
    if clue_id:
        clue_obj = Clue.objects.get(clue_id=clue_id)
        clue_obj.status = status
        clue_obj.verification_conclusion = verification_conclusion
        clue_obj.save()
        return JsonResponse({"msg": "线索录入成功", 'code': 0})
    return JsonResponse({"msg": "线索录入失败，线索不存在", 'code': 1})


def auto_start_detection(request):
    """
    大疆司空2 获取数据自动开始检测
    @param request:
    @return:
    """
    current_user = parse_jwt_token(request)
    county = current_user.county
    grid = Grid.objects.filter(county=county).first()
    start_date = datetime.datetime.now().strftime('%Y-%m-%d')
    start_name = datetime.datetime.now().strftime('%Y%m%d')
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    if month < 10:
        month = '0' + str(month)
    is_exists = Batch.objects.filter(grid=grid, year=year, month=month).order_by('-order')
    if is_exists:
        order = is_exists[0].order + 1
    else:
        order = 1
    batch_name = f"{year}年{month}月第{order}批次"
    batch = Batch.objects.create(
        batch_id=grid.grid_id + start_name,
        batch_name=batch_name,
        start_date=start_date,
        end_date=start_date,
        grid=grid,
        year=datetime.datetime.now().year,
        month=datetime.datetime.now().month,
        street=grid.street,
        count=PointLocation.objects.filter(grid=grid).count(),
        region='',
        operator_id=current_user.id
    )
    file_folder = os.path.join(settings.BASE_DIR, 'static', 'temp', start_name)
    os.makedirs(file_folder, exist_ok=True)
    from utils_tools.oss_module import main
    main(file_folder)
    file_list = os.listdir(file_folder)
    save_panorama_dir = os.path.join(settings.BASE_DIR, 'static', 'layers')  # 保存三个图层的文件夹
    upload_batch = UploadBatch.objects.create(
        batch_id=batch.batch_id,
        grid_operator=current_user.username,
        file_path=file_folder,
    )
    file_id = 1
    for i in file_list:
        print(f"正在开始第{file_id}/{len(file_list)}, {i}")
        file_path = os.path.join(file_folder, i)
        image_id = str(uuid.uuid1()).replace('-', '')
        img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        image_height, image_width, _ = img.shape
        resize_path = file_path
        # if image_width != 14400:
        #     img = cv2.resize(img, (14400, 7200))
        #     resize_path = os.path.join(settings.BASE_DIR, 'static/temp/resize', i)
        #     cv2.imwrite(resize_path, img)
        lat, lon, gps_height = get_coordinates(file_path)
        all_points = PointLocation.objects.filter(grid_id=upload_batch.batch.grid_id).all()
        all_lonlat = []
        for j in all_points:
            all_lonlat.append({"point_id": j.point_id, 'point': (j.latitude, j.longitude)})
        closest_point, distance = calculate_distances((lat, lon), all_lonlat)
        yaw_degree, relativeAltitude = get_yaw_degree(file_path)

        is_exists = PanoramaImage.objects.filter(batch_id=batch.batch_id, latitude=lat, longitude=lon).exists()
        if not is_exists:
            with transaction.atomic():
                panorama_image = PanoramaImage.objects.create(
                    image_id=image_id,
                    image_name=i,
                    image_path=file_path,
                    longitude=lon,
                    point_id=closest_point,
                    latitude=lat,
                    batch_id=batch.batch_id,
                    image_height=image_height,
                    image_width=image_width,
                    height=relativeAltitude,
                    yaw_degree=yaw_degree,
                    upload_batch=upload_batch,
                )
                p_obj = {
                    'image_id': image_id,
                    'image_name': i,
                    'image_path': resize_path,
                    'longitude': lon,
                    'point_id': closest_point,
                    'latitude': lat,
                    'batch_id': batch.batch_id,
                    'image_height': image_height,
                    'image_width': image_width,
                    'height': relativeAltitude,
                    'yaw_degree': yaw_degree,
                }
                transaction.on_commit(lambda: panorama_detection.apply_async(
                    args=[image_id, closest_point, p_obj],
                    task_id=str(image_id)
                ))
            print(f"第{file_id}张图片{panorama_image.image_name}保存成功！")
            file_id += 1
            # panorama_detection.apply_async(args=[image_id, closest_point], task_id=str(image_id))
    upload_batch.count = file_id - 1
    upload_batch.save()
    current_batch = Batch.objects.get(batch_id=batch.batch_id)
    current_batch.status = 1
    current_batch.save()
    # write_doc(task, res, target_directory)
    surplus_count = current_batch.count - file_id - 1
    return JsonResponse(
        {'code': 0, 'msg': f'提交识别任务成功,已上传全景图一共{file_id - 1}张，当前批次还剩{surplus_count}张待上传'})


def get_temp_data(request):
    """
    临时上传全景点获取生成批次名称和批次编号
    @param request:
    @return:
    """
    current_user = parse_jwt_token(request)
    county = current_user.county
    grid = Grid.objects.filter(county=county).first()

    start_name = datetime.datetime.now().strftime('%Y%m%d')
    batch_id = grid.grid_id + start_name
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    is_today_batch_exists = Batch.objects.filter(batch_id=batch_id).first()
    if is_today_batch_exists:
        response_data = {
            "code": 0,
            "data": {
                "batch_id": batch_id,
                "batch_name": is_today_batch_exists.batch_name,
            }
        }
        return JsonResponse(response_data)
    if month < 10:
        month = '0' + str(month)

    # 获取编号
    is_exists = Batch.objects.filter(grid=grid, year=year, month=month).order_by('-order')
    if is_exists:
        order = is_exists[0].order + 1
    else:
        order = 1
    batch_name = f"{year}年{month}月第{order}批次"

    response_data = {
        "code": 0,
        "data": {
            "batch_id": batch_id,
            "batch_name": batch_name,
        }
    }
    return JsonResponse(response_data)


def temp_main_detection(request):
    """
    临时上传全景图功能（临时批次默认不做变化检测）
    """
    logger.info('开始临时上传全景图')
    try:
        current_user = parse_jwt_token(request)
        county = current_user.county
        params = json.loads(request.body.decode('utf-8'))
        batch_name = params.get('batch_name') or params.get('batchName')
        batch_id = params.get('batch_id') or params.get('batchId')
        unzip_path = params.get('unzip_path') or params.get('unzipPath')
        operator = params.get('operator')

        if not batch_id or not batch_name:
            return JsonResponse({'code': 1, 'msg': '缺少批次信息 batchId / batchName'})
        if not unzip_path:
            return JsonResponse({'code': 1, 'msg': '缺少解压路径 unzipPath，请先上传 zip 文件'})

        year = datetime.datetime.now().year
        month = datetime.datetime.now().month
        if month < 10:
            month = '0' + str(month)
        start_date = datetime.datetime.now().strftime('%Y-%m-%d')
        grid = Grid.objects.filter(county=county).first()
        street = grid.street if grid else '-'

        batch_obj = Batch.objects.filter(batch_id=batch_id).first()
        if not batch_obj:
            batch_obj = Batch.objects.create(
                batch_id=batch_id,
                batch_name=batch_name,
                start_date=start_date,
                end_date=start_date,
                grid=grid,
                year=year,
                month=month,
                street=street,
                count=PointLocation.objects.filter(grid=grid).count() if grid else 0,
                region='',
                operator=current_user.username,
                batch_type=1,
                change_detection=0,
            )

        file_folder = os.path.join(settings.BASE_DIR, 'static', 'temp', unzip_path)
        if not os.path.isdir(file_folder):
            return JsonResponse({'code': 1, 'msg': f'解压目录不存在: {unzip_path}'})

        file_list = [
            f for f in os.listdir(file_folder)
            if os.path.isfile(os.path.join(file_folder, f))
            and f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
        if not file_list:
            return JsonResponse({'code': 1, 'msg': '解压目录中没有可用的图片文件'})

        upload_batch = UploadBatch.objects.create(
            batch_id=batch_id,
            grid_operator=operator,
            file_path=file_folder,
            batch_type=1,
        )

        uploaded_count = 0
        submitted_image_ids = []
        for i in file_list:
            file_path = os.path.join(file_folder, i)
            img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                logger.warning(f'跳过无法解析的图片: {file_path}')
                continue

            lat, lon, gps_height = get_coordinates(file_path)
            if lat is None or lon is None:
                logger.warning(f'跳过无 GPS 信息的图片: {file_path}')
                continue

            point_exists = PointLocation.objects.filter(latitude=lat, longitude=lon).first()
            if not point_exists:
                point_exists = PointLocation.objects.create(
                    point_id=f't{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}{uploaded_count + 1}',
                    point_name=i.split('.')[0],
                    point_type=0,
                    grid=grid,
                    latitude=lat,
                    longitude=lon,
                )
            yaw_degree, relativeAltitude = get_yaw_degree(file_path)
            image_height, image_width, _ = img.shape
            image_id = str(uuid.uuid1()).replace('-', '')

            with transaction.atomic():
                panorama_image = PanoramaImage.objects.create(
                    image_id=image_id,
                    image_name=i,
                    image_path=file_path,
                    longitude=lon,
                    point_id=point_exists.point_id,
                    latitude=lat,
                    batch_id=batch_id,
                    image_height=image_height,
                    image_width=image_width,
                    height=relativeAltitude,
                    yaw_degree=yaw_degree,
                    upload_batch=upload_batch,
                )
                p_obj = {
                    'image_id': image_id,
                    'image_name': i,
                    'image_path': file_path,
                    'longitude': lon,
                    'point_id': point_exists.point_id,
                    'latitude': lat,
                    'batch_id': batch_id,
                    'image_height': image_height,
                    'image_width': image_width,
                    'height': float(relativeAltitude),
                    'yaw_degree': yaw_degree,
                    'is_change_detection': 0,
                }
                transaction.on_commit(
                    lambda img_id=image_id, obj=p_obj: submit_panorama_detection(img_id, obj)
                )
            logger.info(f'临时检测图片 {panorama_image.image_name} 已提交识别任务')
            uploaded_count += 1
            submitted_image_ids.append(image_id)

        upload_batch.count = uploaded_count
        upload_batch.save()
        batch_obj.status = 1
        batch_obj.save(update_fields=['status'])

        if uploaded_count == 0:
            return JsonResponse({
                'code': 1,
                'msg': '未提交任何检测任务，请检查图片是否含 GPS、是否为重复上传',
                'data': {'uploadedCount': 0, 'imageIds': []},
            })

        return JsonResponse({
            'code': 0,
            'msg': f'提交识别任务成功，本次共提交 {uploaded_count} 张全景图',
            'data': {'uploadedCount': uploaded_count, 'imageIds': submitted_image_ids},
        })
    except Exception as e:
        logger.exception('临时检测提交失败')
        return JsonResponse({'code': 500, 'msg': f'提交识别任务失败: {e}'})


def get_buffer_gd(request):
    """
    获取点700米缓冲区内的耕地范围
    :param request:
    :return:
    """
    try:
        panorama_image_id = request.GET.get('panorama_image_id')
        resource_id = request.GET.get('resource_id')
        panorama_image_obj = PanoramaImage.objects.get(image_id=panorama_image_id)
        if panorama_image_obj:
            point_obj = PointLocation.objects.get(point_id=panorama_image_obj.point_id)
            resource_obj = Resource.objects.get(id=resource_id)
            if point_obj:
                point_lon = point_obj.longitude
                point_lat = point_obj.latitude
                if resource_obj.gis_service_type == '1':
                    polygons_list = get_point_buffer_gd([point_lon, point_lat], resource_obj.url,
                                                        resource_obj.datasource_name, resource_obj.datasets_name)
                elif resource_obj.gis_service_type == '4':
                    polygons_list = get_point_buffer_gd_geoserver([point_lon, point_lat], resource_obj.url,
                                                                  resource_obj.datasource_name,
                                                                  resource_obj.datasets_name)
                data_list = []
                if isinstance(polygons_list, list):
                    for i_points in polygons_list:
                        new_points = []
                        for j in i_points:
                            yaw, pitch = compute_yaw_pitch(j[1], j[0], panorama_image_obj.latitude,
                                                           panorama_image_obj.longitude, panorama_image_obj.height,
                                                           panorama_image_obj.yaw_degree)
                            new_points.append([pitch, yaw])
                        data_list.append(new_points)
                    return JsonResponse({'code': 0, 'msg': '获取缓冲区范围内耕地成功', 'data': data_list})

                else:
                    return JsonResponse({'code': 1, 'msg': '获取缓冲区范围内耕地失败,{}'.format(polygons_list)})
    except Exception as e:
        print(e)
        return JsonResponse({'code': 1, 'msg': '获取缓冲区范围内耕地失败{}'.format(e)})


def add_plot(request):
    """
    新增图斑面
    """
    params = json.loads(request.body.decode('utf-8'))
    clue_id = params.get('clueId')
    clue_name = params.get('clueName')
    color = params.get('color')
    transparent = params.get('transparent')
    line_color = params.get('lineColor')
    line_width = params.get('lineWidth')
    plot_name = params.get('plotName')
    plot_type = params.get('plotType')
    plot_desc = params.get('plotDesc')
    image_id = params.get('imageId')
    point_id = params.get('pointId')
    point_name = params.get('pointName')
    geometry = params.get('geometry')
    plot_area = params.get('plotArea')
    PlotRecord.objects.create(clue_id=clue_id, clue_name=clue_name, color=color, transparent=transparent,
                              line_color=line_color, line_width=line_width, plot_name=plot_name, plot_type=plot_type,
                              plot_status=0, plot_desc=plot_desc, image_id=image_id, point_id=point_id,
                              point_name=point_name, geometry=geometry, plot_area=plot_area,
                              create_person=request.user.username)
    return JsonResponse({'code': 0, 'msg': '新增图斑面成功',
                         'data': {'pointName': point_name, 'geometry': geometry, 'plotArea': plot_area,
                                  'lineColor': line_color, 'line_width': line_width,
                                  'clueId': clue_id, 'clueName': clue_name, 'plotName': plot_name,
                                  'plotType': plot_type, 'plotDesc': plot_desc}})


def get_plot_by_panorama_image_id(request):
    image_id = request.GET.get('id')
    results = PlotRecord.objects.filter(image_id=image_id).all()
    data = []
    for i in results:
        record = {
            "id": i.id,
            "currentStatus": 0,
            "createPerson": i.create_person,
            "orderIndex": 1,
            "createDate": i.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "isDel": 1,
            "county": "龙袍街道(320116011)",
            "color": i.color,
            "transparent": i.transparent,
            "lineColor": i.line_color,
            "lineWidth": i.line_width,
            "plotName": i.plot_name,
            "plotType": i.plot_type,
            "plotStatus": i.plot_status,
            "plotDesc": i.plot_desc,
            "clueId": i.clue_id,
            "clueName": i.clue_name,
            "imageId": i.image_id,
            "pointName": i.point_name,
            "pointId": i.point_id,
            "geometry": i.geometry,
            "plotArea": i.plot_area

        }
        data.append(record)
    response_data = {'code': 0, 'msg': '', 'data': data}
    return JsonResponse(response_data)


def get_plot_by_id(request):
    return


def delete_plot(request):
    """
    删除标绘图斑面
    """
    params = json.loads(request.body)
    plot_id = params.get('plot_id')
    plot_record_obj = PlotRecord.objects.filter(id=plot_id).first()
    if plot_record_obj:
        plot_record_obj.delete()
        return JsonResponse({'code': 0, 'msg': '删除图斑面成功'})
    else:
        return JsonResponse({'code': 404, 'msg': '删除图斑面失败,图斑面不存在！'})


def update_plot(request):
    """
    修改标绘面信息
    """
    params = json.loads(request.body.decode('utf-8'))
    plot_id = params.get('id')
    clue_id = params.get('clueId')
    clue_name = params.get('clueName')
    plot_desc = params.get('plotDesc')
    PlotRecord.objects.filter(id=plot_id).update(
        clue_id=clue_id,
        clue_name=clue_name,
        plot_desc=plot_desc
    )
    logger.info(f"修改绘制图斑{plot_id}成功")
    return JsonResponse({'code': 0, 'msg': '修改图斑面成功', 'data': []})


def export_shp(request):
    """
    导出绘制的图斑面
    """
    current_user = parse_jwt_token(request)
    params = json.loads(request.body.decode('utf-8'))
    batch_id = params.get('batchId')
    batch_obj = Batch.objects.filter(batch_id=batch_id).first()
    panorama_objs = PanoramaImage.objects.filter(batch=batch_obj).all().values('image_id')
    # 转换为只包含 image_id 值的列表
    image_id_list = [item['image_id'] for item in panorama_objs]
    all_plot = PlotRecord.objects.filter(image_id__in=image_id_list).all()
    plots_list = []
    clue_name_list = []
    plot_name_list = []
    plot_desc_list = []
    for i in all_plot:
        original_points = ast.literal_eval(i.geometry)
        # 2. 交换每个点的经纬度顺序：[lat, lon] → [lon, lat]
        swapped_points = [[point[1], point[0]] for point in original_points]
        # 3. 注意：如果是多边形，需确保最后一个点与第一个点一致（闭合），避免shp导出警告
        if swapped_points and swapped_points[0] != swapped_points[-1]:
            swapped_points.append(swapped_points[0])
        if len(swapped_points) > 3:
            plots_list.append(shapely_polygon(swapped_points))
            clue_name_list.append(i.clue_name)
            plot_name_list.append(i.plot_name)
            plot_desc_list.append(i.plot_desc)
    gdf = gpd.GeoDataFrame()
    gdf['geometry'] = plots_list
    gdf['prev_type'] = ''
    gdf['next_type'] = ''
    # 设置 CRS
    crs = CRS.from_epsg(4326)
    gdf.crs = crs  # 使用WGS84坐标系
    for index, row in gdf.iterrows():
        gdf.at[index, 'clue_name'] = clue_name_list[index]
        gdf.at[index, 'plot_name'] = plot_name_list[index]
        gdf.at[index, 'plot_desc'] = plot_desc_list[index]
    # 将数据保存为shp格式文件
    save_path = os.path.join(settings.BASE_DIR, 'static', 'plot', batch_id)
    os.makedirs(save_path, exist_ok=True)
    shp_path = os.path.join(save_path, f'{batch_id}.shp')
    gdf.to_file(shp_path, encoding='utf-8')
    zip_path = os.path.join(settings.BASE_DIR, 'static', 'plot', f'{batch_id}.zip')
    # 打包文件
    file_name = f'{batch_id}.zip'
    zf = zipfile.ZipFile(zip_path, 'w')
    for root, dirs, files in os.walk(save_path):
        for f in files:
            zf.write(os.path.join(root, f), f)
    zf.close()
    while True:
        file_id = f"62{random.randint(10000000000000, 99999999999999)}"
        is_exist = BufferFile.objects.filter(file_id=file_id)
        if not is_exist:
            break
    BufferFile.objects.create(
        file_id=file_id,
        file_name=file_name,
        file_extension='.zip',
        file_path=zip_path,
        owner=current_user.username,
        file_type='zip',
        file_size=os.path.getsize(zip_path)
    )
    return JsonResponse({'code': 0, 'msg': '导出图斑面成功', 'data': {'file_id': file_id, 'file_name': file_name}})


def order_list(request):
    """
    订单列表数据
    """
    try:

        response_data = {'code': 0, 'msg': '', 'data': []}
        params = json.loads(request.body.decode('utf-8'))
        order_name = params.get('orderName', '')
        data_type = params.get('dataType')
        organization = params.get('organization')
        collect_type = params.get('collectType')
        limit = params.get('pageSize', 10)
        page = params.get('pageIndex', 1)
        current_user = parse_jwt_token(request)
        county = current_user.county
        # 构建查询条件
        filters = Q()
        if order_name:
            filters &= Q(order_name__contains=order_name)
        if data_type:
            filters &= Q(data_type=data_type)
        if organization:
            filters &= Q(organization__contains=organization)
        if collect_type:
            filters &= Q(collect_type=collect_type)

        order_objs = FlyOrder.objects.filter(filters).all()

        if len(order_objs) > 0:
            paginator = Paginator(order_objs, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        if results:
            for result in results:
                dict_value = {
                    'orderName': result.order_name,
                    'id': result.id,
                    'dataType': SysDictData.objects.filter(dict_type='multivariateType',
                                                           value=result.data_type).first().name,
                    'organization': result.organization,
                    'collectType': SysDictData.objects.filter(dict_type='collectType',
                                                              value=result.collect_type).first().name,
                    'createPerson': result.create_person,
                    'status': result.status,
                    'county': result.county,
                    'route': result.route.name,
                    'collectTime': result.collect_time.strftime("%Y-%m-%d"),
                    'createTime': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                data.append(dict_value)
        response_data['data'] = data
        response_data['total'] = len(order_objs)

        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'根据参数获取订单信息失败{e}')
        return JsonResponse({'code': 500, 'msg': f'根据参数获取订单信息失败{e}', 'data': []})


def order_add(request):
    """
    新增订单
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        order_name = params.get('orderName')
        data_type = params.get('dataType')
        organization = params.get('organization')
        collect_type = params.get('collectType')
        county = params.get('county')
        route = params.get('route')
        current_user = parse_jwt_token(request)
        collect_time = params.get('collectTime')
        collect_time = datetime.datetime.strptime(collect_time, "%Y-%m-%d")
        order_obj = FlyOrder.objects.create(
            order_name=order_name,
            data_type=data_type,
            organization=organization,
            collect_type=collect_type,
            county=county,
            route_id=route,
            create_person=current_user.username,
            collect_time=collect_time
        )
        return JsonResponse({"code": 0, 'msg': "订单创建成功!", 'data': {'id': order_obj.id}})
    except Exception as e:
        logger.error(f"创建订单失败，报错内容{e}")
        return JsonResponse({"code": 500, 'msg': str(e), 'data': {}})


def order_delete(request):
    """
    删除订单
    """
    params = json.loads(request.body.decode('utf-8'))
    order_ids = params.get('ids')
    success_count = 0
    error_count = 0
    for i in order_ids:
        order_obj = FlyOrder.objects.filter(id=i).first()
        if order_obj:
            order_obj.delete()
            success_count += 1
        else:
            error_count += 1

    return JsonResponse({"code": 0, 'msg': f"删除操作已完成，成果{success_count}个,失败{error_count}个"})


def change_detection(request):
    """
    全景检测API
    """
    from draw_panorama import main_draw_panorama_with_bboxes
    from cut_image import main_cut_image
    from ai_detection.predict import main_detection
    is_default_img = request.form.get('isDefaultImg')
    if is_default_img == '1':
        file1_path = os.path.join(settings.BASE_DIR, 'static/1.JPG')
        file2_path = os.path.join(settings.BASE_DIR, 'static/2.JPG')
    else:
        # 1. 接收前端FormData中的文件
        if 'panorama1' not in request.files or 'panorama2' not in request.files:
            return JsonResponse({
                'code': 400,
                'msg': '缺少全景图文件（panorama1或panorama2）'
            }), 400

        file1 = request.files['panorama1']  # 对应前端formData.append('panorama1', ...)
        file2 = request.files['panorama2']  # 对应前端formData.append('panorama2', ...)
        timestamp = int(time.time())  # 时间戳避免文件名冲突
        file1_path = os.path.join(settings.BASE_DIR, 'static', 'temp', file1.filename)
        file2_path = os.path.join(settings.BASE_DIR, 'static', 'temp', file2.filename)
        file1.save(file1_path)
        file2.save(file2_path)
    output_dir = os.path.join(settings.BASE_DIR, 'static', 'output')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    main_cut_image(file1_path, file2_path, output_dir)
    save_path = os.path.join(settings.BASE_DIR, 'static', 'resultImg')

    save_path2 = os.path.join(output_dir, 'C')
    os.makedirs(save_path2, exist_ok=True)
    main_detection(output_dir, save_path, save_path2)
    pic_save_path = os.path.join(settings.BASE_DIR, 'static', 'finalImg')
    if os.path.exists(pic_save_path):
        shutil.rmtree(pic_save_path)
    os.makedirs(pic_save_path, exist_ok=True)
    # main_draw_panorama(file1_path,save_path,os.path.join(pic_save_path,os.path.basename(file1_path)))
    main_draw_panorama_with_bboxes(file1_path, save_path, os.path.join(pic_save_path, os.path.basename(file1_path)))
    data = []
    for fl1, resultImg in zip(os.listdir(os.path.join(output_dir, 'A')), os.listdir(save_path)):
        records = {
            'file1': f'/static/output/A/{fl1}',
            'file2': f'/static/output/B/{fl1}',
            'file3': f'/static/output/C/{fl1}',
            'resultImg': f'/static/resultImg/{resultImg}'

        }
        data.append(records)
    if os.path.exists(file1_path) and is_default_img != '1':
        os.remove(file1_path)
    if os.path.exists(file2_path) and is_default_img != '1':
        os.remove(file2_path)
    return JsonResponse(
        {"code": 0, 'msg': '检测完成', 'data': data, 'finalImg': f'/static/finalImg/{os.path.basename(file1_path)}',
         'next_path': f'/static/temp/{os.path.basename(file2_path)}'})


def panorama_point_nearest(request):
    """
    根据经纬度获取最近的全景点信息
    """
    params = json.loads(request.body.decode('utf-8'))
    longitude = params.get('longitude')
    latitude = params.get('latitude')
    all_points = PointLocation.objects.all()
    all_lonlat = []
    for j in all_points:
        all_lonlat.append({"point_id": j.point_id, 'point': (j.latitude, j.longitude)})
    closest_point, distance = calculate_distances2((latitude, longitude), all_lonlat)
    point_obj = PointLocation.objects.filter(point_id=closest_point).first()
    if point_obj:
        point_name = point_obj.point_name
    else:
        point_name = ''
    panorama_obj = PanoramaImage.objects.filter(point_id=closest_point).all().order_by('-create_time').first()
    if panorama_obj:
        batch_id = panorama_obj.batch_id
    else:
        batch_id = ''
    response_data = {
        "code": 0,
        "msg": "success",
        "data": {
            "pointId": closest_point,
            "point_id": closest_point,
            "pointName": point_name,
            "longitude": 119.7123,
            "latitude": 31.1825,
            "batchId": batch_id,
            "batchNumber": batch_id
        }
    }
    return JsonResponse(response_data)
