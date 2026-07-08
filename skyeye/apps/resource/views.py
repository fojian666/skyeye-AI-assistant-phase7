# _*_ coding: utf-8 _*_
# @Time : 2025/3/10 15:04 
# @Author : xxx 
# @Version：V 0.1
# @File : data_views.py
# @desc :
import configparser
import json
import os
import uuid
import subprocess
import threading
import time
from django.http import JsonResponse, HttpResponse, Http404, StreamingHttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import random
import re

import requests
from PIL import Image
from django.conf import settings
from django.db import transaction
from django.forms import model_to_dict

from apps.panorama.common import unzip_file
from apps.panorama.models import Grid, Batch, PointLocation, PanoramaImage, Clue, Resource, BufferFile
from apps.system.models import Nest
from apps.resource.models import MultivariateTask, MultivariateData
from django.core.paginator import Paginator
from django.db.models import Q
from utils_tools import common
from utils_tools.common import parse_jwt_token, warning, get_center, get_geoserver_center, get_arcgis_center, \
    login_request
from apps.panorama.change_detection.utils import batch_generate_geotiffs, get_exif_data, extract_exif_data_from_dict
from apps.panorama.views.supervision_views import link_vertical_view_to_polygons
from logger import Logger
from apps.system.models import Region, SysDictData

logger = Logger(logname='resource_views.log', loglevel=5, logger='resource').getlog()
config = configparser.ConfigParser()
config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')


def video_data(request):
    params = json.loads(request.body.decode('utf-8'))
    page = params.get("pageIndex", 1)
    limit = params.get("pageSize", 8)
    name = params.get("name", "")
    videoTaskList = [
        {
            'taskId': 'task_001',
            'name': '井盖检测',
            'status': 2,
            'frameInterval': 5,
            'shotTime': '2025-11-10',
            'clueCount': 12,
            'effectiveClueCount': 8,
            'modelSceneList': [
                {'id': 1, 'modelSceneName': '城市建设'},
            ],
            'coverUrl': '/static/images/jg.jpg',

            'videoUrl': '/static/video/03井盖检测.mp4'
        },
        {
            'taskId': 'task_002',
            'name': '森林火焰检测',
            'status': 2,
            'frameInterval': 3,
            'shotTime': '2025-09-12',
            'clueCount': 5,
            'effectiveClueCount': 3,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '智能安防'},
            ],
            'coverUrl': '/static/images/fire.jpg',
            'videoUrl': '/static/video/10火焰检测.mp4'
        },
        {
            'taskId': 'task_003',
            'name': '道路车牌识别',
            'status': 2,
            'frameInterval': 10,
            'shotTime': '2025-12-11',
            'clueCount': 6,
            'effectiveClueCount': 0,
            'modelSceneList': [
                {'id': 6, 'modelSceneName': '违章停车'},

            ],
            'coverUrl': '/static/images/cpjc.jpg',
            'videoUrl': '/static/video/16车牌检测与识别.mp4'
        },
        {
            'taskId': 'task_004',
            'name': '工地安防视频',
            'status': 2,
            'frameInterval': 2,
            'shotTime': '2025-10-08',
            'clueCount': 8,
            'effectiveClueCount': 0,
            'modelSceneList': [
                {'id': 1, 'modelSceneName': '人员检测'},
                {'id': 10, 'modelSceneName': '危险区域'}
            ],
            'coverUrl': '/static/images/aqm.jpg',
            'videoUrl': '/static/video/07安全帽检测.mp4'
        },
        {
            'taskId': 'task_005',
            'name': '道路渣土车检测',
            'status': 2,
            'frameInterval': 8,
            'shotTime': '2025-05-05',
            'clueCount': 18,
            'effectiveClueCount': 15,
            'modelSceneList': [
                {'id': 1, 'modelSceneName': '城市建设'},
            ],
            'coverUrl': '/static/images/ztc.jpg',
            'videoUrl': '/static/video/25渣土车识别.mp4'
        },
        {
            'taskId': 'task_006',
            'name': '道路占道经营检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-05-01',
            'clueCount': 23,
            'effectiveClueCount': 19,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '智慧城管'},

            ],
            'coverUrl': '/static/images/zdjy.jpg',
            'videoUrl': '/static/video/06占道经营（人行道与车道）.mp4'
        },
        {
            'taskId': '7',
            'name': '路面积水识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-05-03',
            'clueCount': 23,
            'effectiveClueCount': 19,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市建设'},

            ],
            'coverUrl': '/static/images/lmjs.jpg',
            'videoUrl': '/static/video/01路面积水.mp4'
        },
        {
            'taskId': '8',
            'name': '道路裂缝检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-06-03',
            'clueCount': 23,
            'effectiveClueCount': 19,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市建设'},

            ],
            'coverUrl': '/static/images/dllf.jpg',
            'videoUrl': '/static/video/02道路裂缝检测.mp4'
        },
        {
            'taskId': '9',
            'name': '垃圾识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-06-03',
            'clueCount': 23,
            'effectiveClueCount': 19,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市建设'},

            ],
            'coverUrl': '/static/images/pfw.jpg',
            'videoUrl': '/static/video/04垃圾识别.mp4'
        },
        {
            'taskId': '10',
            'name': '反光衣检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-06-03',
            'clueCount': 23,
            'effectiveClueCount': 19,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市建设'},

            ],
            'coverUrl': '/static/images/fgy.jpg',
            'videoUrl': '/static/video/08反光衣检测.mp4'
        },
        {
            'taskId': '11',
            'name': '违建识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-06-03',
            'clueCount': 23,
            'effectiveClueCount': 9,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市建设'},

            ],
            'coverUrl': '/static/images/wjj.jpg',
            'videoUrl': '/static/video/05违建识别.mp4'
        },
        {
            'taskId': '12',
            'name': '人员聚集识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '智能安防'},

            ],
            'coverUrl': '/static/images/ryjz.jpg',
            'videoUrl': '/static/video/09人员聚集识别.mp4'
        },
        {
            'taskId': '13',
            'name': '烟雾检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '智能安防'},

            ],
            'coverUrl': '/static/images/lc.jpg',
            'videoUrl': '/static/video/11烟雾检测.mp4'
        },
        {
            'taskId': '14',
            'name': '红外视角火焰检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '智能安防'},

            ],
            'coverUrl': '/static/images/fire.jpg',
            'videoUrl': '/static/video/12红外视角火焰检测.mp4'
        },
        {
            'taskId': '15',
            'name': '非机动车后排载人识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市治理'},

            ],
            'coverUrl': '/static/images/zr.jpg',
            'videoUrl': '/static/video/14非机动车后排载人识别.mp4'
        },
        {
            'taskId': '16',
            'name': '人脸检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '人脸识别'},

            ],
            'coverUrl': '/static/images/rlsb.jpg',
            'videoUrl': '/static/video/15人脸检测.mp4'
        },
        {
            'taskId': '17',
            'name': '路面障碍物检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '道路交通'},

            ],
            'coverUrl': '/static/images/zaw.jpg',
            'videoUrl': '/static/video/17路面障碍物检测.mp4'
        },
        {
            'taskId': '18',
            'name': '非机动车未戴头盔检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '道路交通'},

            ],
            'coverUrl': '/static/images/tk.jpg',
            'videoUrl': '/static/video/18非机动车未戴头盔检测.mp4'
        },
        {
            'taskId': '19',
            'name': '车辆拥堵检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '道路交通'},

            ],
            'coverUrl': '/static/images/yd.jpg',
            'videoUrl': '/static/video/19车辆拥堵检测.mp4'
        },
        {
            'taskId': '20',
            'name': '路面异常停车识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '道路交通'},

            ],
            'coverUrl': '/static/images/tc.jpg',
            'videoUrl': '/static/video/20路面异常停车识别.mp4'
        },
        {
            'taskId': '21',
            'name': '道路绿化带异常识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '道路交通'},

            ],
            'coverUrl': '/static/images/lhd.jpg',
            'videoUrl': '/static/video/21道路绿化带异常识别.mp4'
        },
        {
            'taskId': '22',
            'name': '路政工程车辆识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '道路交通'},

            ],
            'coverUrl': '/static/images/gcc.jpg',
            'videoUrl': '/static/video/22路政工程车辆识别.mp4'
        },
        {
            'taskId': '23',
            'name': '病枯树识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '城市园林'},

            ],
            'coverUrl': '/static/images/bks.jpg',
            'videoUrl': '/static/video/24病枯树识别.mp4'
        },
        {
            'taskId': '24',
            'name': '挖掘机识别',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '耕地保护'},

            ],
            'coverUrl': '/static/images/wjj.jpg',
            'videoUrl': '/static/video/26挖掘机识别.mp4'
        },
        {
            'taskId': '25',
            'name': '游泳人体检测',
            'status': 2,
            'frameInterval': 4,
            'shotTime': '2025-08-03',
            'clueCount': 13,
            'effectiveClueCount': 10,
            'modelSceneList': [
                {'id': 4, 'modelSceneName': '应急救援'},

            ],
            'coverUrl': '/static/images/yy.jpg',
            'videoUrl': '/static/video/27游泳人体检测.mp4'
        },
    ]
    # 4. 核心：根据name关键词进行模糊查询（不区分大小写）
    if name:
        # 过滤条件：任务名称包含关键词（转小写匹配，提升用户体验）
        filtered_list = [
            task for task in videoTaskList
            if name.lower() in task['name'].lower()
        ]
    else:
        # 无关键词时，返回全部列表
        filtered_list = videoTaskList
    paginator = Paginator(filtered_list, limit)
    results = paginator.page(page)
    data = []
    for i in results:
        record = {
            'taskId': i['taskId'],
            'name': i['name'],
            'status': i['status'],
            'frameInterval': i['frameInterval'],
            'shotTime': i['shotTime'],
            'clueCount': i['clueCount'],
            'effectiveClueCount': i['effectiveClueCount'],
            'modelSceneList': [
                {'id': 1, 'modelSceneName': i['modelSceneList'][0]['modelSceneName']},
            ],
            'coverUrl': i['coverUrl'],
            'videoUrl': i['videoUrl']
        }
        data.append(record)
    response_data = {
        'code': 0,
        "data": data,
        "msg": "数据获取成功！",
        "total": len(filtered_list),
    }
    return JsonResponse(response_data)


def resourceLists(request):
    """
    资源列表
    @param request:
    @return:
    """

    try:
        current_user = parse_jwt_token(request)
        county = current_user.county
        params = json.loads(request.body.decode('utf-8'))
        page = params.get("pageIndex", 1)
        limit = params.get("pageSize", 8)
        order_by = params.get('orderField')  # 排序：创建时间or名称
        keyword = params.get('filter')
        data = []
        county_list = Resource.objects.filter(county=county).values_list('county', flat=True).distinct()
        if keyword is None:
            source_obj = Resource.objects.filter(county=county).all()
        else:
            keyword = eval(keyword)
            name = keyword.get("name")  # 资源名称
            create_time = keyword.get("create_time")  # 创建时间
            # 取出数据后剔除
            keyword.pop('name')
            keyword.pop('create_time')
            # 前端条件模糊查询
            if not name and not create_time:
                source_obj = Resource.objects.filter(**keyword).filter(county=county).all()
            elif name and not create_time:
                source_obj = Resource.objects.filter(**keyword).filter(name=name, county=county).all()
            elif not name and create_time:
                source_obj = Resource.objects.filter(create_time__year=create_time.split('-')[0],
                                                     create_time__month=create_time.split('-')[1],
                                                     create_time__day=create_time.split('-')[2], country=county).filter(
                    **keyword).all()
            else:
                source_obj = Resource.objects.filter(create_time__year=create_time.split('-')[0],
                                                     create_time__month=create_time.split('-')[1],
                                                     create_time__day=create_time.split('-')[2]).filter(
                    name=name, county=county).filter(
                    **keyword).all()
                # 获取最新的一条数据
        if source_obj:
            latest_source_id = source_obj[0].id
        else:
            latest_source_id = 0
            # 根据参数排序
        if order_by == 'time':
            source_obj = source_obj.order_by('-create_time')
        else:
            source_obj = source_obj.order_by('-name')
            # 分页
        paginator = Paginator(source_obj, limit)
        results = paginator.page(page)
        for i in results:
            records = {
                "id": i.id,
                "name": i.name,
                "url": i.url,
                "county": i.county,
                "owner": i.owner.username,
                "source_type": i.source_type,
                "center": i.center,
                "append_time": i.append_time,
                "gis_service_type": i.gis_service_type,
                "service_type": i.service_type,
                "create_time": i.create_time.strftime("%Y-%m-%d"),
            }
            data.append(records)
        response_data = {
            'code': 0,
            "data": data,
            "msg": "数据获取成功！",
            "total": len(source_obj),
            'latest_source_id': latest_source_id,
            'county_list': list(county_list)  # 行政区
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取资源列表失败: {e}')
        return JsonResponse({'code': 1, 'msg': '获取资源列表失败！'})


def resources(request):
    """
    新增资源
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        name = params.get('name')
        url = params.get('url')
        append_time = params.get('appendTime')
        source_type = params.get('sourceType')
        county = params.get('county')
        data_type = params.get('dataType')
        service_type = params.get('serviceType', '基础地理数据')
        datasets_name = params.get('datasetsName', '')
        datasource_name = params.get('datasourceName', '')
        polygon_color = params.get('polygonColor', '')
        polygon_weight = params.get('polygonWeight', '')
        polygon_opacity = params.get('polygonOpacity', '')
        is_show = params.get('isShow', 0)
        layer_name = params.get('layerName', '')
        is_show_on_panorama_image = params.get('isShowOnPanoramaImage', 0)
        gis_service_type = params.get('gisServiceType', 'wms')
        is_exists = Resource.objects.filter(name=name).exists()
        if is_exists:
            return JsonResponse({"code": 410, "msg": "资源名称已存在！"})
        # if source_type == '影像服务':
        #     is_exists = Resource.objects.filter(source_type='影像服务', county=county).first()
        #     if is_exists:
        #         logger.warning("当前行政区已存在影像服务，请勿重复上传！")
        #         return JsonResponse({"code": 410, "msg": "当前行政区已存在影像服务，请勿重复上传！"})
        source = Resource(name=name, url=url, append_time=append_time, service_type=service_type,
                          coordinate_system='4326', polygon_color=polygon_color, polygon_weight=polygon_weight,
                          polygon_opacity=polygon_opacity,
                          data_type=data_type, is_show_on_panorama=is_show_on_panorama_image, is_show=is_show,
                          source_type=source_type, county=county, owner_id=request.session['user_id'],
                          datasets_name=datasets_name, datasource_name=datasource_name,
                          gis_service_type=gis_service_type)

        if source_type == '影像服务':
            # 获取中心点坐标和坐标系
            if gis_service_type == '1':
                center, coordinate_system = get_center(url)
            elif gis_service_type == '2':
                pass
            elif gis_service_type == '3':
                pass
            else:
                center, coordinate_system = get_geoserver_center(url, datasource_name, datasets_name)
                source.datasets_name = layer_name
            # 判断坐标系是否错误
            if coordinate_system <= 0:
                logger.warning("影像坐标系错误或没有坐标系！")
                return warning("影像坐标系错误或没有坐标系！")
            source.center = center
            # 获取坐标系对象
            # coordinate_system_id = '4326'
            source.coordinate_system = coordinate_system
        elif source_type == '业务栅格数据服务':
            layer_name = params.get('layerName')
            source.datasets_name = layer_name
        source.save()
        return JsonResponse({'code': 0, 'msg': '资源新增成功！'})
    except Exception as e:
        logger.error(f"{e}")
        return JsonResponse({"msg": f'资源新增失败，{e}！', 'code': 500})


def resource_delete(request):
    """
    资源删除
    @param request:
    @return:
    """
    with  transaction.atomic():
        try:
            params = json.loads(request.body)
            resource_ids = params.get('resource_ids')
            for i in resource_ids:
                Resource.objects.filter(id=i).delete()
            return JsonResponse({'code': 0, 'msg': '资源删除成功！'})
        except Exception as e:
            logger.error(f"{e}")
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': '资源删除失败！'})


def resource_one(request):
    """
       资源目录查询单个资源详情
       """
    try:
        # 根据资源id查找对应资源，并将资源对应的信息返回
        source_id = request.GET.get('resource_id')
        source_obj = Resource.objects.filter(id=source_id).first()
        # 封装资源对象
        if source_obj:
            data = {
                'name': source_obj.name,  # 资源名称
                'url': source_obj.url,  # 资源地址
                'owner': source_obj.owner.username,  # 上传人
                'source_type': source_obj.source_type,  # 资源类型
                'coordinate_system': source_obj.coordinate_system,  # 坐标系
                'center': source_obj.center,  # 中心点坐标
                'data_type': source_obj.data_type,  # 数据类型
                'county': source_obj.county,  # 行政区编码
                'datasets_name': source_obj.datasets_name,  # 数据集名称
                'datasource_name': source_obj.datasource_name,  # 数据源名称
                'create_time': source_obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),  # 创建时间
                'append_time': source_obj.append_time,  # 资源创建时间
                'count': source_obj.count,  # 图斑数量
                'map_url': source_obj.map_url,  # 地图服务地址
                'status': True,
                'gis_service_type': source_obj.gis_service_type,  # GIS服务类型
            }
            response_data = {
                'msg': '资源数据获取成功！',
                'code': 0,
                'data': data
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'msg': '资源数据不存在！', 'code': 500})
    except Exception as e:
        logger.error(f"资源数据获取失败: {str(e)}")


def resource_modify(request):
    """
    资源修改
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        resource_id = params.get('resource_id')
        resource_name = params.get('resource_name')
        resource_url = params.get('resource_url')
        resource_map_url = params.get('resource_map_url')
        # 判断资源名称修改是否重复
        source_count = Resource.objects.filter(name=resource_name).exclude(id=resource_id).count()
        if source_count >= 1:
            return warning('资源名称重复，请修改后重新提交！')
        # 修改数据入库
        Resource.objects.filter(id=resource_id).update(
            name=resource_name,
            url=resource_url,
            map_url=resource_map_url
        )

        return JsonResponse({'msg': '资源修改成功！', 'code': 0})
    except Exception as e:
        logger.error(e)
        return JsonResponse({'msg': '资源修改失败，请查看后台日志！', 'code': 500})


def business_layer_data(request):
    current_user = parse_jwt_token(request)
    county = current_user.county
    current_resources = Resource.objects.filter(county=county, service_type='资源调查数据').values('id', 'name',
                                                                                             'data_type',
                                                                                             'url')
    resources_list = list(current_resources)

    return JsonResponse({'code': 0, 'data': resources_list, 'msg': '获取成功！'})


def get_resources_on_one_map(request):
    """
    一张图页面获取所有的资源
    @param request:
    @return:
    """
    # 获取所有资源并按 source_type 分组
    current_user = common.parse_jwt_token(request)
    county = current_user.county
    code = re.findall(r'\((\d+)\)', county)[0]
    print(code)
    t_region = Region.objects.filter(region_code=code).first()
    if t_region:
        longitude = t_region.longitude
        latitude = t_region.latitude
    else:
        longitude = ''
        latitude = ''
    resources = Resource.objects.filter(county=current_user.county).values('source_type', 'id', 'name', 'url',
                                                                           'data_type', 'center', 'county',
                                                                           'service_type', 'is_show',
                                                                           'is_show_on_panorama', 'gis_service_type',
                                                                           'datasource_name', 'datasets_name',
                                                                           'polygon_color', 'polygon_opacity', 'polygon_weight')

    # 创建一个空字典用于存储结果
    grouped_resources = {"低空业务数据": {"label": "低空业务数据", "children": []},
                         '基础地理数据': {'label': '基础地理数据', 'children': []},
                         '资源调查数据': {'label': '资源调查数据', 'children': []}}

    # 遍历资源并按 source_type 分组
    for resource in resources:
        service_type = resource['service_type']
        label = resource["name"]
        url = resource["url"]

        # 如果该类型不存在，则初始化
        if service_type not in grouped_resources:
            grouped_resources[service_type] = {"label": service_type, "children": []}

        # 将子项添加到对应类型的 children 列表中
        grouped_resources[service_type]["children"].append(
            {"label": label, "service": url, 'data_type': resource['data_type'], 'center': resource['center'],
             'county': resource['county'], 'datasource_name': resource['datasource_name'],
             'source_type': resource['source_type'], 'polygon_color': resource['polygon_color'],
             'polygon_opacity': resource['polygon_opacity'], 'polygon_weight': resource['polygon_weight'],
             'service_type': resource['service_type'], 'gis_service_type': resource['gis_service_type'],
             'datasets_name': resource['datasets_name'], 'isShowOnPanorama': resource['is_show_on_panorama'],
             "isShow": resource['is_show']})
    nest_list = Nest.objects.all()
    nest_data = []
    for i in nest_list:
        nest_data.append({
            'id': i.id,
            'name': i.name,
            'location': i.location,
            'status': i.status,
            'model': i.model,
            'longitude': i.longitude,
            'latitude': i.latitude,
            'plane_model': i.plane_model,
            'nest_sn': i.nest_sn,
            'plane_sn': i.plane_sn,
        })

    clue_list = Clue.objects.filter(status__in=[5]).all()
    clue_data = []
    for clue_obj in clue_list:
        records = {
            'clue_id': clue_obj.clue_id,
            'task_id': clue_obj.panorama_image_id,
            'clue_name': clue_obj.clue_name,
            'center_x': clue_obj.center_x,
            'center_y': clue_obj.center_y,
            'longitude': clue_obj.longitude,
            'latitude': clue_obj.latitude,
            'label': clue_obj.clue_name,
            'point_id': clue_obj.panorama_image.point_id,
            'position': clue_obj.position,
            'score': clue_obj.score,
            'yaw_degree': clue_obj.panorama_image.yaw_degree,
            'batch_id': clue_obj.batch_id,
            'panorama_image_lat': clue_obj.panorama_image.latitude,
            'panorama_image_lon': clue_obj.panorama_image.longitude,
            'address': clue_obj.address,
            'status': clue_obj.status,
            'create_time': clue_obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        clue_data.append(records)
    grouped_resources['低空业务数据']['children'].append(
        {'label': '机巢点位', 'service': '', 'data_type': 'nest_location', 'center': '', 'county': '栖霞区(320113)',
         'data': nest_data,
         'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append(
        {'label': '机巢覆盖范围', 'service': '', 'data_type': 'nest_coverage', 'center': '', 'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append(
        {'label': '全景点位', 'service': '', 'data_type': 'panorama', 'center': '', 'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append(
        {'label': '全景覆盖范围', 'service': '', 'data_type': 'panorama_coverage', 'center': '',
         'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append({
        "service": "",
        "center": "",
        "data_type": "top_view",
        "county": "320100",
        "orderIndex": 5,
        "datasource_name": "",
        "datasets_name": "",
        "label": "无人机俯视图"
    }, )
    grouped_resources['低空业务数据']['children'].append(
        {'label': '监测线索点', 'service': '', 'data_type': 'clue', 'center': '', 'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': '', 'data': clue_data})
    grouped_resources['longitude'] = longitude
    grouped_resources['latitude'] = latitude
    return JsonResponse({'data': grouped_resources, 'code': 0, "msg": '数据获取成功！'},
                        json_dumps_params={'ensure_ascii': False})


@login_request
def get_business_data(request):
    """
    获取所有的资源
    @param request:
    @return:
    """
    # 获取所有资源并按 source_type 分组
    current_user = common.parse_jwt_token(request)
    resources = Resource.objects.filter(county=current_user.county,
                                        service_type__in=['低空业务数据', '资源调查数据']).values(
        'source_type', 'id',
        'name', 'url',
        'data_type', 'center',
        'county',
        'service_type',
        'datasource_name',
        'datasets_name')

    # 创建一个空字典用于存储结果
    grouped_resources = {}

    # 遍历资源并按 source_type 分组
    for resource in resources:
        service_type = resource['service_type']
        label = resource["name"]
        url = resource["url"]

        # 如果该类型不存在，则初始化
        if service_type not in grouped_resources:
            grouped_resources[service_type] = {"label": service_type, "children": []}

        # 将子项添加到对应类型的 children 列表中
        grouped_resources[service_type]["children"].append(
            {"label": label, "service": url, 'data_type': resource['data_type'], 'center': resource['center'],
             'county': resource['county'], 'datasource_name': resource['datasource_name'],
             'source_type': resource['source_type'],
             'datasets_name': resource['datasets_name']})
    # grouped_resources['低空业务数据']['children'].append(
    #     {'label': '机巢点位', 'service': '', 'data_type': 'nest_location', 'center': '', 'county': '栖霞区(320113)',
    #      'datasource_name': '', 'datasets_name': ''})
    # grouped_resources['低空业务数据']['children'].append(
    #     {'label': '机巢覆盖范围', 'service': '', 'data_type': 'nest_coverage', 'center': '', 'county': '栖霞区(320113)',
    #      'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append(
        {'label': '全景点位', 'service': '', 'data_type': 'panorama', 'center': '', 'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append(
        {'label': '全景覆盖范围', 'service': '', 'data_type': 'panorama_coverage', 'center': '',
         'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': ''})
    grouped_resources['低空业务数据']['children'].append(
        {'label': '监测线索点', 'service': '', 'data_type': 'clue', 'center': '', 'county': '栖霞区(320113)',
         'datasource_name': '', 'datasets_name': ''})
    return JsonResponse({'data': list(grouped_resources.values()), 'code': 0})


def get_descendant_regions(root_region_id, max_depth=None):
    """
    从指定行政区按 parent_id 向下获取下级。
    :param max_depth: 最大层级深度；None 表示不限制。区县用户传 2 表示「两级到街道」。
    """
    collected = []
    current_level_ids = [root_region_id]
    depth = 0
    while current_level_ids:
        if max_depth is not None and depth >= max_depth:
            break
        children = list(Region.objects.filter(parent_id__in=current_level_ids))
        if not children:
            break
        collected.extend(children)
        current_level_ids = [c.region_id for c in children]
        depth += 1
    return collected


def is_city_level_region(region):
    """是否为地级市用户（如无锡市 320200）。"""
    code = (region.region_code or '').strip()
    if len(code) == 6:
        # 省级 XX0000；地级市 XXXX00（第3-4位不为00）
        if code[2:] == '0000':
            return False
        if code[4:] == '00':
            return True
    name = region.region_name or ''
    return name.endswith('市') and '区' not in name and '县' not in name


def resolve_user_region(county_raw):
    """
    根据用户 county 字段解析所属行政区。
    优先用括号内行政区代码（如 无锡市(320200)），避免同名区划匹配错误。
    """
    if not county_raw:
        return None
    if '(' in county_raw and ')' in county_raw:
        region_code = county_raw.split('(')[1].rstrip(')')
        region = Region.objects.filter(region_code=region_code).first()
        if region:
            return region
    region_name = county_raw.split('(')[0]
    return Region.objects.filter(region_name=region_name).first()


def build_tree(divisions, parent_id=1):
    """
    递归查询省市区县街道（已去掉网格查询，只到街道）
    @param divisions:
    @param parent_id:
    @return:
    """
    tree = []
    for division in divisions:
        if division.parent_id == parent_id:
            # 递归构建子级区域（省→市→区→街道）
            children = build_tree(divisions, division.region_id)
            if len(children) == 0:

                tree.append({
                    'id': division.region_id,
                    'label': division.region_name,
                    'value': division.region_code,
                    'longitude': division.longitude,
                    'latitude': division.latitude,
                    # 统计点位数量（按街道名称统计）
                    'count': PointLocation.objects.filter(grid__street=division.region_name).count()
                })
            else:
                tree.append({
                    'id': division.region_id,
                    'label': division.region_name,
                    'value': division.region_code,
                    'longitude': division.longitude,
                    'latitude': division.latitude,
                    'children': children,
                    # 统计点位数量（按街道名称统计）
                    'count': PointLocation.objects.filter(grid__street=division.region_name).count()
                })
    return tree


def build_tree1(divisions, parent_id=1):
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
                            'label': k.grid_name,
                            'count': PointLocation.objects.filter(grid_id=k.grid_id).count()
                        }
                        grand_children_region_list.append(grand_children_records)
                    division.children = grand_children_region_list
                    children = grand_children_region_list
                tree.append({
                    'id': division.region_id,
                    'label': division.region_name,
                    'value': division.region_code,
                    'longitude': division.longitude,
                    'latitude': division.latitude,
                    'children': children,
                    'count': PointLocation.objects.filter(grid__street=division.region_name).count()
                })
        return tree
    except Exception as e:

        return JsonResponse({'code': 500, 'msg': '数据获取失败！', 'data': str(e)})


def compress_picture(inputImage):
    """
    Pillow压缩图斑图片
    @param inputImage:输入图片路径
    @return:None
    """
    try:
        # Pillow读取img文件
        im = Image.open(inputImage)
        # 读取图片尺寸大小（像素宽高）
        (x, y) = im.size
        # 定义缩小后的标准宽度
        new_width = 400
        # 计算缩小后的高度
        new_height = int(y * new_width / x)
        # 改变尺寸，保持图片高品质
        out = im.resize((new_width, new_height))
        # 保存图片，替换原图
        out.save(inputImage)
    except Exception as e:
        print(f"压缩图片报错，报错内容：{str(e)}")


def import_regions(data, parent=None):
    """
    递归导入行政区划数据
    :param data: 当前层级的行政区划列表
    :param parent: 父级行政区划对象
    """
    for item in data:
        # 创建当前行政区划
        region = Region(
            region_name=item['label'],
            region_code=item['value'],
            region_level=1 if parent is None else parent.region_level + 1,
            parent_id=parent.region_id if parent else 0,
            parent_name=parent.region_name if parent else '',
            parent_code=parent.region_code if parent else '',
            longitude=0,
            latitude=0
        )
        region.save()

        # 递归处理子节点
        if 'children' in item:
            import_regions(item['children'], parent=region)


@login_request
def region_data(request):
    """
    获取当前登录用户所属的行政区树（最底层均为街道）。
    - 地级市用户（如无锡市）：返回市下完整层级（区县→…→街道）
    - 区县用户（如梁溪区）：仅返回两级到街道（兼容区→街道、区→镇→街道）
    """
    try:
        current_user = parse_jwt_token(request)
        current_region = resolve_user_region(current_user.county)
        if not current_region:
            return JsonResponse({'code': 500, 'msg': '未找到用户所属行政区', 'data': []})

        if is_city_level_region(current_region):
            region_objs = get_descendant_regions(current_region.region_id)
        else:
            region_objs = get_descendant_regions(current_region.region_id, max_depth=2)
        root_divisions = build_tree(region_objs, current_region.region_id)
        root_divisions1 = build_tree1(region_objs, current_region.region_id)
        return JsonResponse({'code': 0, 'msg': '数据已接收！', 'data': root_divisions, 'data1': root_divisions1})
    except Exception as e:
        print(e)
        return JsonResponse({'code': 500, 'msg': f'数据获取失败:{e}', 'data': []})


@login_request
def query_data_by_grid_id(request):
    """
    根据网格id获取所有的全景图
    @param request:
    @return:
    """
    params = json.loads(request.body.decode('utf-8'))
    keyword = params.get('keyword')
    limit = params.get('limit', 10)
    page = params.get('page', 1)
    current_user = common.parse_jwt_token(request)
    county = current_user.county
    batch_list = Batch.objects.filter(grid__county=county).exclude(status=0).all().order_by('-start_date')
    if len(batch_list) > 0:
        last_batch = batch_list[0]
    else:
        response_data = {
            'code': 0,
            'msg': '数据获取成功！',
            'data': [],
            'count': 0
        }
        return JsonResponse(response_data)
    if keyword:
        panorama_list = PanoramaImage.objects.filter(image_name__contains=keyword, batch=last_batch).all()
    else:
        panorama_list = PanoramaImage.objects.filter(batch=last_batch).all()
    if len(panorama_list) > 0:
        paginator = Paginator(panorama_list, limit)
        results = paginator.page(page)
    else:
        results = []
    data = []
    if results:
        for i in results:
            # compress_picture(i.image_path)
            value = PanoramaImage.objects.filter(point_id=i.point_id).exclude(image_id=i.image_id).count()
            record = {
                'image_id': i.image_id,
                'image_name': i.image_name,
                'longitude': i.longitude,
                'image_path': i.image_path.split('gtus')[1],
                'latitude': i.latitude,
                'point_id': i.point.point_id,
                'count': value,
                'yaw_degree': i.yaw_degree,
                'point_name': i.point.point_name,
                'street': i.point.grid.street if i.point.grid else '-',
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)
    response_data = {
        'code': 0,
        'msg': '数据获取成功！',
        'data': data,
        'count': len(panorama_list)
    }
    return JsonResponse(response_data)


@login_request
def get_time_axis(request):
    response_data = {
        "code": 0,
        "msg": '',
        "data": {
            "rawTimelineItems": [
                {
                    "year": "2024",
                    "month_list": [
                        "08",
                        "12"
                    ]
                },
                {
                    "year": "2025",
                    "month_list": [
                        "02",
                        "04",
                        "05",
                        "05",
                        "06",
                        "06",
                        "06",
                        "06",
                        "07",
                        "07",
                        "07",
                        "07"
                    ]
                }
            ]
        }
    }
    return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})


@login_request
def top_view_task(request):
    # p = PanoramaImage.objects.all()
    # for i in p:
    #     crop_save_folder = os.path.join(settings.BASE_DIR, 'static', 'layers',
    #                                     i.batch_id, i.image_id)
    #     start_cut_image(i.image_path, crop_save_folder, 2)
    response_data = {
        "code": 0,
        "msg": "null",
        "data": [
            {
                "latitude": 31.3886000000,
                "longitude": 118.9971000000,
                "bounds": "[[31.388333874682242,118.99666485387775],[31.38892212531776,118.99757914612228]]",
                "id": "126a34f75eb74a79a52d5035d17c5988",
                "file_id": "t_05_82cf404978954155b48487fc7a128f16",
                "data_name": "DJI_20250513115848_0003_V",
                "path": "/static/vertical_view/DJI_20250513115848_0003_V.jpeg",
                "collect_time": "2025-05-13 11:58:48",
                "task_id": "e2e8c71b079a4f9bbb3c8c827c2e4a76"
            },
            {
                "latitude": 31.3842000000,
                "longitude": 118.9943000000,
                "bounds": "[[31.383902524370644,118.99385880947175],[31.384491475629357,118.99477519052823]]",
                "id": "64dcc380fad94a9b8f896ae796e94399",
                "file_id": "t_05_bf944529c4ed49369930a5d092418233",
                "data_name": "DJI_20250513115802_0001_V",
                "path": "/static/vertical_view/DJI_20250513115802_0001_V.jpeg",
                "collect_time": "2025-05-13 11:58:02",
                "task_id": "e2e8c71b079a4f9bbb3c8c827c2e4a76"
            }
        ]
    }
    return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})


@login_request
def flight_view_task(request):
    response_data = {
        "code": 0,
        "msg": "null",
        "data": [
            {
                "id": "f263dd582deb48efbd85a97c80bf4a12",
                "timeAxis": "2025-07",
                "timeAxisYear": "2025",
                "tiffServiceCollection": "imagetestdk",
                "timeName": "Feihuacun.tif",
                "tiffCenter": "32.1974547315,119.18851237575001",
                "tiffServiceUrl": "http://192.168.60.42:8090/iserver/services/imageservice-njimagetest/restjsr/",
                "tiffId": "1"
            }
        ]
    }
    return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})


@login_request
def query_point_location(request):
    """
    获取所有的全景点信息
    """
    current_user = parse_jwt_token(request)
    county = current_user.county
    point_location_list = PointLocation.objects.filter(grid__county=county).all()
    results = []
    for point_location in point_location_list:
        records = {
            "pointId": point_location.point_id,
            "pointName": point_location.point_name,
            "latitude": point_location.latitude,
            "longitude": point_location.longitude,
            "gridName": point_location.grid.grid_name,
            "gridOperator": point_location.grid.grid_operator.username if point_location.grid.grid_operator else '-',
            "latestTime": point_location.create_time.strftime('%Y-%m-%d %H:%M:S'),
            "panoramaImageCount": PanoramaImage.objects.filter(point=point_location).count(),
            "pointType": point_location.point_type,
        }
        results.append(records)
    response_data = {
        "code": 0,
        "msg": "获取成功！",
        "data": results,
        "total": len(results)
    }

    return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})


@login_request
def get_machine_nest(request):
    """
    获取机巢信息接口
    """
    all_nests = Nest.objects.all()
    data = []
    for nest in all_nests:
        records = {
            'name': nest.name,
            'value': nest.id
        }
        data.append(records)
    return JsonResponse({'data': data, 'code': 0, 'msg': ''})


@login_request
def get_buffer_list(request):
    """
    获取分析时需要叠加的数据
    """
    current_user = parse_jwt_token(request)
    county = current_user.county
    all_resources = Resource.objects.filter(source_type='业务矢量数据服务', service_type='资源调查数据', is_show_on_panorama=1,
                                            county=county).all()
    data = []
    for i in all_resources:
        records = {
            "name": i.name,
            "url": i.url,
            "sourceType": i.source_type,
            "serviceType": i.service_type,
            "data_type": i.data_type,
            "datasource_name": i.datasource_name,
            "datasets_name": i.datasets_name,
            "id": i.id,
            'isShow': i.is_show,
            'isShowOnPanoramaImage': i.is_show_on_panorama,

        }
        data.append(records)
    response_data = {
        "code": 0,
        "msg": "获取服务列表成功",
        "data": data
    }
    return JsonResponse(response_data)


@login_request
def get_uav_info(request):
    """
    获取无人机信息接口
    """
    response_data = {"code": 0, "msg": 'null', "data": [{"label": "大疆 Mavic 3 系列，焦距 24mm", "value": "24"}, {
        "label": "佳能 EOS R5, 焦距 24-105mm",
        "value": "24-105"
    }, {
                                                            "label": "索尼 A7 IV, 焦距 28-70mm",
                                                            "value": "28-70"
                                                        }, {
                                                            "label": "尼康 Z7 II, 焦距 24-70mm",
                                                            "value": "24-70"
                                                        }, {
                                                            "label": "GoPro Hero 11 Black, 焦距 16mm",
                                                            "value": "16"
                                                        }, {
                                                            "label": "富士 X-T4, 焦距 18-55mm",
                                                            "value": "18-55"
                                                        }]}
    return JsonResponse(response_data)


# Define a function
def files_upload(request):
    with transaction.atomic():
        try:
            current_user = parse_jwt_token(request)
            county = current_user.county
            myFile = request.FILES.get("file", None)
            if myFile:
                save_path = os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name)
                destination = open(save_path, 'wb+')
                for chunk in myFile.chunks():
                    destination.write(chunk)
                destination.close()
                if myFile.name.endswith('.zip'):
                    unzip_path = os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name.split('.')[0])
                    unzip_file(save_path, unzip_path)

            return JsonResponse({'code': 0, 'msg': '上传成功', 'data': len(os.listdir(unzip_path))})
        except Exception as e:
            logger.error(f'上传失败: {str(e)}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': '上传失败', 'error': str(e)})


@login_request
def add_multivariate_data(request):
    """
    新增多元数据接口
    """
    current_user = parse_jwt_token(request)
    params = json.loads(request.body.decode('utf-8'))
    task_name = params.get('taskName')
    task_type = params.get('taskType')
    flight = params.get('flight')
    nest = params.get('nest')
    organization = params.get('organization')
    collect_type = params.get('collectType')
    file_name = params.get('fileName')
    collect_time = params.get('collectTime')
    tiffName = params.get('tiffName', '')
    tiffServiceCollection = params.get('tiffServiceCollection')
    tiffCenter = params.get('tiffCenter')
    tiffId = params.get('tiffId')
    county = params.get('county')
    tiffServiceUrl = params.get('tiffServiceUrl')
    current_task = MultivariateTask.objects.create(
        task_name=task_name,
        task_type=task_type,
        flight=flight,
        nest_id=nest,
        organization=organization,
        collect_type=collect_type,
        collect_time=collect_time,
        tiff_name=tiffName,
        create_person=current_user.username
    )

    sensor_width = 17.3
    sensor_height = 13
    # 获取配置文件中的公共配置
    config_common = config['common']
    # 获取主机地址
    HOST = config_common['host']
    # 获取端口号
    PORT = config_common['port']
    file_folder = os.path.join(settings.BASE_DIR, 'static', 'temp', file_name.split('.')[0])
    for i in os.listdir(file_folder):
        file_path = os.path.join(file_folder, i)
        while True:
            file_id = f"62{random.randint(10000000000000, 99999999999999)}"
            is_exist = BufferFile.objects.filter(file_id=file_id)
            if not is_exist:
                break
        filename, extension = os.path.splitext(i)
        BufferFile.objects.create(
            file_id=file_id,
            file_name=i,
            file_extension=extension,
            file_path=file_path,
            owner=current_user.username,
            file_type='zip',
            file_size=os.path.getsize(file_path)
        )
        if collect_type == '1':
            # 俯视图：生成正射影像并关联监测图斑
            vertical_view_path = os.path.join(settings.BASE_DIR, 'static', 'vertical_view')
            os.makedirs(vertical_view_path, exist_ok=True)
            save_path = os.path.join(vertical_view_path, i)
            exif_data = extract_exif_data_from_dict(get_exif_data(file_path))
            latitude = float(exif_data['GpsLatitude'])
            longitude = float(exif_data['GpsLongitude'])
            left_bottom, right_top = batch_generate_geotiffs(
                file_path, save_path, [sensor_width, sensor_height]
            )
            data_obj = MultivariateData.objects.create(
                task=current_task,
                file_id=file_id,
                file_size=os.path.getsize(file_path),
                county=county,
                data_name=i,
                path=f"http://{HOST}:{PORT}/static/vertical_view/{i}",
                bounds=json.dumps([left_bottom, right_top], ensure_ascii=False),
                latitude=latitude,
                longitude=longitude,
                create_person=current_user.username,
            )
            link_vertical_view_to_polygons(data_obj.id, longitude, latitude, file_path)
        else:
            MultivariateData.objects.create(
                task=current_task,
                file_id=file_id,
                file_size=os.path.getsize(file_path),
                county=county,
                data_name=i,
                path=f"http://{HOST}:{PORT}/static/vertical_view/{i}",
                bounds=[],

            )
    return JsonResponse({"code": 0, "msg": "", "data": []})


def filter_multivariate_data(task_name=None, task_type=None, start_date=None, end_date=None, flight=None, nest=None,
                             organization=None):
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
    if task_name:
        filters &= Q(task_name__contains=task_name)
    if task_type:
        filters &= Q(task_type=task_type)
    if start_date:
        filters &= Q(record_time__gte=start_date)
    if end_date:
        filters &= Q(record_time__lte=end_date)
    if flight:
        filters &= Q(flight=flight)
    if nest:
        filters &= Q(nest_id=nest)
    if organization:
        filters &= Q(organization__contains=organization)
    return filters


@login_request
def query_multivariate_data(request):
    """
    获取多元数据接口
    """
    params = json.loads(request.body.decode('utf-8'))
    task_name = params.get('taskName')
    task_type = params.get('taskType')
    flight = params.get('flight')
    nest = params.get('nest')
    organization = params.get('organization')
    page = params.get('pageIndex')
    limit = params.get('pageSize')
    collectTimeStart = params.get('collectTimeStart')
    collectTimeEnd = params.get('collectTimeEnd')
    filters = filter_multivariate_data(task_name, task_type, collectTimeStart, collectTimeEnd, flight, nest,
                                       organization)
    try:
        data_obj = MultivariateTask.objects.filter(filters).all().order_by('-id')
        if len(data_obj) > 0:
            paginator = Paginator(data_obj, limit)
            data = paginator.page(page)
        else:
            data = []
        results = []
        for i in data:
            collect_type = SysDictData.objects.filter(dict_type='collectType', value=i.collect_type).first()
            task_type = SysDictData.objects.filter(dict_type='multivariateType', value=i.task_type).first()
            records = {
                "id": i.id,
                "taskName": i.task_name,
                "taskType": task_type.name if task_type else '-',
                "flight": i.flight,
                "nest": Nest.objects.get(id=i.nest_id).name,
                "organization": i.organization,
                "collectType": collect_type.name if collect_type else '-',
                "collectTime": i.collect_time,
                "operatorName": i.create_person,
                "count": MultivariateData.objects.filter(task=i).count(),
            }
            results.append(records)
        return JsonResponse({"msg": '', 'data': results, 'code': 0, 'total': len(data)})
    except Exception as e:
        logger.error(f"多元数据获取失败，报错内容:{e}")
        return JsonResponse({"msg": '获取多元数据失败！', "code": 500, "data": []})


@login_request
def delete_multivariate_data(request):
    """
    删除多元数据接口
    """
    params = json.loads(request.body.decode('utf-8'))
    task_id_list = params.get('taskIdList')
    try:
        for task_id in task_id_list:
            data_list = MultivariateData.objects.filter(task_id=task_id).all()
            for i in data_list:
                file_path = i.path
                file_id = i.file_id
                BufferFile.objects.get(file_id=file_id).delete()
                if os.path.exists(file_path):
                    os.remove(file_path)
                i.delete()
            MultivariateTask.objects.get(id=task_id).delete()
        logger.info(f"多元数据ID为{task_id_list}删除成功！")
        return JsonResponse({"msg": '删除成功', "code": 0, "data": []})
    except Exception as e:
        logger.error(f"删除{task_id_list}失败，报错内容:{e}")
        return JsonResponse({"msg": '删除多元数据失败！', "code": 500, "data": []})


def get_three_source_list(request):
    """
    获取多元数据接口
    """
    # 假数据（真实环境替换成你的服务器 tileset.json 地址）
    data = {
        "code": 0,
        "msg": "获取三维数据成功",
        "data": [{
            # 核心：只需要返回这个 URL！
            "url": "http://192.168.1.4:8009/static/3dtiles/test1/tileset.json",
            # 可选：位置、高度、名称等配置
            "name": "厂区三维模型",
            "longitude": 116.403874,  # 中心点经度
            "latitude": 39.914885,  # 中心点纬度
            "height": 0,  # 高度偏移
            "maximumScreenSpaceError": 16  # 3D瓦片精度
        }]
    }
    return JsonResponse(data)


def live_stream(request):
    """
    获取拉流地址
    """
    uav_list = [
        {"name": "无锡滨湖-蠡湖未来城",
         "tenantId": 362711,  # 租户ID
         "projectId": "2054085558198116352",  # 组织ID
         "id": "8UUXNBH00A0TQC",  # 机库ID：
         "uav_id": "1581F8HGX253U00A0645"  # 无人机ID
         },
        {"name": "无锡 - 01机库",
         "tenantId": 362711,  # 租户ID
         "projectId": "2054085558198116352",  # 组织ID
         "id": "8UUXN4200A04G7",  # 机库ID：
         "uav_id": "1581F8HGX253X00A06NM"  # 无人机ID
         },
        {"name": "蠡开01 - 瑞庭西郊",
         "tenantId": 362711,  # 租户ID
         "projectId": "2054085558198116352",  # 组织ID
         "id": "8UUXNAX00A0RQZ",  # 机库ID：
         "uav_id": "1581F8HGX258600A0RYQ"  # 无人机ID
         },
    ]
    try:
        params = json.loads(request.body.decode('utf-8'))
        print(params)
        device_id = params.get('deviceSn')
        result = None
        for item in uav_list:
            if item.get('id') == device_id:
                result = item
                break

        url = 'http://2.20.41.1:6080/wrjapi?apiName=/v1/live/pull-url&method=post'
        data = {
            "deviceSn": device_id,
            "projectId": result['projectId'],
        }
        # 方式2：手动转json字符串 + 手动指定header
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url=url, data=json.dumps(data), headers=headers).json()
        resp = json.loads(resp)
        webrtc_url = None
        print(resp)
        if resp['code'] == 0:
            webrtc_url = resp['data']['liveStreamUrl']
        response_data = {
            "code": 0,
            "data": {
                "webrtcUrl": webrtc_url,
                'deviceName': result['name'],
                'deviceSn': device_id,
                'latitude': 31.5279,
                'longitude': 120.241
            }
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({"code": 1, "message": str(e)})


# ============================================================
# GDAL 路径配置
# ============================================================
GDAL_DIR = r'E:\02prjs\gtus\utils_tools\GDAL'
GDAL_BIN = os.path.join(GDAL_DIR, 'bin')
GDALWARP = os.path.join(GDAL_BIN, 'gdalwarp.exe')                # 重投影工具
GDAL_TRANSLATE = os.path.join(GDAL_BIN, 'gdal_translate.exe')    # COG 转换工具
GDAL_DATA = os.path.join(GDAL_DIR, 'share', 'gdal')              # GDAL 数据文件
PROJ_LIB = os.path.join(GDAL_DIR, 'share', 'proj')               # PROJ 投影库

# 上传文件暂存目录
UPLOAD_DIR = r'E:\02prjs\gtus\static\tif_upload'
# COG 转换输出根目录
COG_OUTPUT_BASE = r'E:\02prjs\gtus\static\tif_output'
COG_RANGE_CHUNK_SIZE = 64 * 1024
COG_MAX_RANGE_BYTES = 16 * 1024 * 1024
GDALWARP_TIMEOUT = 300          # gdalwarp 超时（秒）
GDAL_TRANSLATE_TIMEOUT = 3600   # gdal_translate 超时（秒）

# ============================================================
# 内存任务存储（task_id → {status, progress, message, outputFile}）
# 生产环境可替换为 Redis/数据库
# ============================================================
_cog_tasks = {}


# ============================================================
# 接口 1：上传 TIF 文件
# POST /api/resource/cog/upload
# ============================================================
@csrf_exempt
def cog_upload(request):
    """接收前端上传的 TIF 文件，保存到暂存目录，返回文件路径"""
    if request.method != 'POST':
        return JsonResponse({'code': 1, 'msg': '仅支持 POST 请求'}, status=405)

    # 从 multipart/form-data 中获取文件
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'code': 1, 'msg': '未接收到文件'}, status=400)

    # 校验文件扩展名
    file_name = uploaded_file.name
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ('.tif', '.tiff'):
        return JsonResponse({'code': 1, 'msg': '仅支持 .tif / .tiff 格式文件'}, status=400)

    # 确保上传目录存在
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 保存文件（文件名加时间戳避免覆盖）
    base, ext_part = os.path.splitext(file_name)
    saved_name = f'{base}_{uuid.uuid4().hex[:8]}{ext_part}'
    saved_path = os.path.join(UPLOAD_DIR, saved_name)

    with open(saved_path, 'wb+') as dest:
        for chunk in uploaded_file.chunks():
            dest.write(chunk)

    return JsonResponse({
        'code': 0,
        'msg': '文件上传成功',
        'fileName': file_name,
        'filePath': saved_path,
        'fileSize': uploaded_file.size,
    })


# ============================================================
# 接口 2：提交 COG 转换任务
# POST /api/resource/cog/convert
# ============================================================
@csrf_exempt
def cog_convert(request):
    """接收 filePath 和 serviceName，启动后台 COG 转换，返回任务 ID"""
    if request.method != 'POST':
        return JsonResponse({'code': 1, 'msg': '仅支持 POST 请求'}, status=405)

    # 解析请求参数
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'code': 1, 'msg': '请求体格式错误，需要 JSON'}, status=400)

    file_path = (data.get('filePath') or '').strip()
    service_name = (data.get('serviceName') or '').strip()
    output_folder_name = (data.get('outputFolderName') or '').strip()

    # 校验输入文件
    if not file_path:
        return JsonResponse({'code': 1, 'msg': '缺少 filePath 参数'}, status=400)
    if not os.path.isfile(file_path):
        return JsonResponse({'code': 1, 'msg': f'文件不存在: {file_path}'}, status=400)

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ('.tif', '.tiff'):
        return JsonResponse({'code': 1, 'msg': '仅支持 .tif / .tiff 格式'}, status=400)

    # 服务名称为空时用文件名
    if not service_name:
        service_name = os.path.splitext(os.path.basename(file_path))[0]

    # 创建输出目录：{base}/{outputFolderName}/
    folder_name = output_folder_name or service_name
    output_dir = os.path.join(COG_OUTPUT_BASE, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # 输出文件：保持原文件名
    output_file = os.path.join(output_dir, os.path.basename(file_path))
    # 确保输出文件以 .tif 结尾
    if not output_file.lower().endswith('.tif'):
        output_file += '.tif'

    # 生成任务 ID
    task_id = uuid.uuid4().hex[:12]

    # 初始化任务状态
    _cog_tasks[task_id] = {
        'status': 'queued',
        'progress': 0,
        'message': '任务已创建，等待处理...',
        'outputFile': output_file,
        'serviceName': service_name,
    }

    # 启动后台线程执行转换
    thread = threading.Thread(
        target=_run_cog_conversion,
        args=(task_id, file_path, output_file),
        daemon=True,
        name=f'cog-{task_id}',
    )
    thread.start()

    return JsonResponse({
        'code': 0,
        'msg': 'COG 转换任务已创建',
        'taskId': task_id,
    })


# ============================================================
# 接口 3：查询转换进度
# GET /api/resource/cog/status/<task_id>
# ============================================================
def cog_status(request, task_id):
    """查询指定任务的转换进度"""
    task = _cog_tasks.get(task_id)
    if not task:
        return JsonResponse({'code': 1, 'msg': '任务不存在'}, status=404)

    return JsonResponse({
        'code': 0,
        'taskId': task_id,
        'status': task['status'],          # queued | running | completed | failed
        'progress': task['progress'],      # 0-100
        'message': task['message'],        # 当前步骤描述
        'outputFile': task.get('outputFile', ''),
    })


# ============================================================
# 后台转换函数（在线程中执行）
# ============================================================
def _run_cog_conversion(task_id, input_file, output_file):
    """
    执行 COG 转换：gdalwarp 重投影 → gdal_translate 转 COG
    - 步骤 1：gdalwarp 将源文件重投影到 EPSG:4326，输出为 VRT（虚拟栅格，瞬时完成）
    - 步骤 2：gdal_translate 将 VRT 转换为 COG 格式（带压缩、金字塔、分块）
    """
    task = _cog_tasks.get(task_id)
    if not task:
        return

    # ---------- 校验 GDAL 工具 ----------
    if not os.path.isfile(GDALWARP):
        task['status'] = 'failed'
        task['progress'] = 0
        task['message'] = f'gdalwarp.exe 未找到: {GDALWARP}'
        return

    if not os.path.isfile(GDAL_TRANSLATE):
        task['status'] = 'failed'
        task['progress'] = 0
        task['message'] = f'gdal_translate.exe 未找到: {GDAL_TRANSLATE}'
        return

    if not os.path.isfile(input_file):
        task['status'] = 'failed'
        task['progress'] = 0
        task['message'] = f'输入文件不存在: {input_file}'
        return

    # ---------- 环境变量配置 ----------
    env = os.environ.copy()
    # 将 GDAL bin 目录加入 PATH，确保 DLL 可加载
    env['PATH'] = GDAL_BIN + os.pathsep + env.get('PATH', '')
    env['GDAL_DATA'] = GDAL_DATA
    env['PROJ_LIB'] = PROJ_LIB

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # VRT 临时文件路径
    vrt_path = os.path.join(
        os.path.dirname(output_file),
        f'_cog_{task_id}.vrt',
    )

    try:
        # ========== 步骤 1：gdalwarp 重投影为 VRT ==========
        task['status'] = 'running'
        task['progress'] = 2
        task['message'] = '【步骤 1/2】正在重投影到 EPSG:4326，生成虚拟栅格...'

        ret = subprocess.run(
            [
                GDALWARP,
                '-t_srs', 'EPSG:4326',   # 目标坐标系
                '-of', 'VRT',            # 输出为虚拟栅格格式
                input_file,
                vrt_path,
            ],
            capture_output=True,
            env=env,
            timeout=GDALWARP_TIMEOUT,
        )

        if ret.returncode != 0:
            err_msg = ret.stderr.decode('utf-8', errors='replace').strip() or '未知错误'
            task['status'] = 'failed'
            task['progress'] = 0
            task['message'] = f'gdalwarp 重投影失败 (code {ret.returncode}): {err_msg[:200]}'
            return

        if not os.path.isfile(vrt_path):
            task['status'] = 'failed'
            task['progress'] = 0
            task['message'] = 'VRT 虚拟栅格文件未生成'
            return

        # ========== 步骤 2：gdal_translate 转 COG ==========
        task['progress'] = 5
        task['message'] = '【步骤 2/2】正在转换为 COG 格式（压缩 + 金字塔 + 分块）...'

        # 启动 gdal_translate 子进程，实时读取 stdout 解析进度
        proc = subprocess.Popen(
            [
                GDAL_TRANSLATE,
                '-of', 'COG',                    # 输出格式：Cloud Optimized GeoTIFF
                '-co', 'COMPRESS=DEFLATE',       # 压缩算法
                '-co', 'RESAMPLING=AVERAGE',     # 金字塔重采样方式
                '-co', 'OVERVIEWS=AUTO',         # 自动生成金字塔层级
                '-co', 'BIGTIFF=YES',            # 支持大于 4GB 的文件
                '-co', 'NUM_THREADS=2',           # 使用 2 个线程
                '--config', 'GDAL_CACHEMAX', '1024',  # 缓存大小 1GB
                vrt_path,
                output_file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
        )

        returncode = _wait_gdal_translate_with_progress(
            proc, task, timeout=GDAL_TRANSLATE_TIMEOUT,
        )

    except subprocess.TimeoutExpired as e:
        cmd = e.cmd
        if isinstance(cmd, (list, tuple)) and cmd:
            cmd_name = os.path.basename(cmd[0])
        else:
            cmd_name = 'GDAL'
        task['status'] = 'failed'
        task['progress'] = 0
        task['message'] = f'{cmd_name} 执行超时（超过 {e.timeout} 秒）'
        return
    except Exception as e:
        task['status'] = 'failed'
        task['progress'] = 0
        task['message'] = f'转换异常: {str(e)}'
        return
    finally:
        _cleanup_vrt(vrt_path)

    # ---------- 结果处理 ----------
    if returncode == 0 and os.path.isfile(output_file):
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        task['status'] = 'completed'
        task['progress'] = 100
        task['message'] = f'COG 转换完成！文件: {os.path.basename(output_file)} ({file_size_mb:.1f} MB)'
    else:
        task['status'] = 'failed'
        task['progress'] = 0
        task['message'] = f'gdal_translate 退出码 {returncode}，COG 文件未生成'


def _wait_gdal_translate_with_progress(proc, task, timeout):
    """读取 gdal_translate 输出并解析进度，超时则终止子进程。"""
    deadline = time.monotonic() + timeout
    line_count = 0

    while True:
        if time.monotonic() > deadline:
            proc.kill()
            proc.wait()
            raise subprocess.TimeoutExpired(GDAL_TRANSLATE, timeout)

        if proc.poll() is not None:
            for raw_line in proc.stdout:
                _update_cog_progress_from_line(task, raw_line, line_count)
                line_count += 1
            return proc.returncode

        raw_line = proc.stdout.readline()
        if not raw_line:
            time.sleep(0.2)
            continue

        line_count += 1
        _update_cog_progress_from_line(task, raw_line, line_count)


def _update_cog_progress_from_line(task, raw_line, line_count):
    text = raw_line.decode('utf-8', errors='replace').strip()
    if not text:
        return

    pct = _extract_progress(text)
    if pct > 0:
        task['progress'] = max(5, min(99, int(pct)))
    elif line_count <= 10:
        task['progress'] = min(5 + line_count * 2, 15)
    else:
        task['progress'] = min(15 + (line_count - 10), 90)

    task['message'] = text[:200]


def _extract_progress(text):
    """从 GDAL 输出文本中提取百分比数字"""
    import re
    # 匹配 "25.5" "50%" "progress=75" 等模式
    patterns = [
        r'\.\.\.(\d{1,3}(?:\.\d+)?)',
        r'(\d{1,3}(?:\.\d+)?)\s*%',
        r'progress[=:\s]*(\d{1,3}(?:\.\d+)?)',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            try:
                val = float(m.group(1))
                if 0 <= val <= 100:
                    return val
            except ValueError:
                pass
    return 0


def _cleanup_vrt(vrt_path):
    """删除临时 VRT 文件"""
    try:
        if os.path.isfile(vrt_path):
            os.remove(vrt_path)
    except Exception:
        pass

def _cog_file_cors_headers(response):
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Range'
    response['Access-Control-Expose-Headers'] = 'Content-Range, Accept-Ranges, Content-Length'
    response['Accept-Ranges'] = 'bytes'
    return response

def _cog_range_stream(file_path, start, length, chunk_size=COG_RANGE_CHUNK_SIZE):
    """按块流式读取，避免大 Range 一次性载入内存"""
    with open(file_path, 'rb') as fp:
        fp.seek(start)
        remaining = length
        while remaining > 0:
            data = fp.read(min(chunk_size, remaining))
            if not data:
                break
            remaining -= len(data)
            yield data


def _parse_cog_range_header(range_header, file_size):
    """解析单段 Range 头，忽略多段请求中的后续段"""
    match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else file_size - 1
    end = min(end, file_size - 1)
    if start > end or start >= file_size:
        return 'invalid'
    length = end - start + 1
    if length > COG_MAX_RANGE_BYTES:
        logger.warning(
            'COG range too large: %s bytes (max %s), file_size=%s',
            length, COG_MAX_RANGE_BYTES, file_size
        )
    return start, end, length

# ============================================================
# 接口 4：COG 文件下载（支持 HTTP Range）
# GET /api/resource/cog/file/<folder>/<filename>
# ============================================================
@csrf_exempt
def cog_serve_file(request, folder, filename):
    """从 COG_OUTPUT_BASE 读取 TIF，支持 Range 分段响应"""
    range_header = request.META.get('HTTP_RANGE', '').strip()
    try:
        if request.method == 'OPTIONS':
            return _cog_file_cors_headers(HttpResponse(status=204))

        if request.method != 'GET':
            return JsonResponse({'code': 1, 'msg': '仅支持 GET 请求'}, status=405)

        if '..' in folder or '..' in filename or '/' in filename or '\\' in filename:
            raise Http404

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ('.tif', '.tiff'):
            raise Http404

        file_path = os.path.join(COG_OUTPUT_BASE, folder, filename)
        if not os.path.isfile(file_path):
            raise Http404

        file_size = os.path.getsize(file_path)

        if range_header:
            parsed = _parse_cog_range_header(range_header, file_size)
            if parsed == 'invalid':
                resp = HttpResponse(status=416)
                resp['Content-Range'] = f'bytes */{file_size}'
                return _cog_file_cors_headers(resp)
            if parsed:
                start, end, length = parsed
                resp = StreamingHttpResponse(
                    _cog_range_stream(file_path, start, length),
                    status=206,
                    content_type='image/tiff',
                )
                resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                resp['Content-Length'] = str(length)
                return _cog_file_cors_headers(resp)

        resp = FileResponse(open(file_path, 'rb'), content_type='image/tiff')
        resp['Content-Length'] = str(file_size)
        return _cog_file_cors_headers(resp)
    except Http404:
        raise
    except Exception as e:
        logger.error(
            'cog_serve_file failed folder=%s filename=%s range=%s error=%s',
            folder, filename, range_header, e,
            exc_info=True,
        )
        return JsonResponse({'code': 500, 'msg': 'COG 文件读取失败'}, status=500)