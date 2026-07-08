import time
import uuid
import redis
import re

import json
import zipfile
from django.core.paginator import Paginator
from django.utils.encoding import escape_uri_path
from django.http import JsonResponse,StreamingHttpResponse

from utils_tools.common import  file_iterator, error, ok, warning
import apps.interpretation.ai_config as config
from apps.panorama.models import Resource
from apps.panorama.common import create_path,read_json_data,read_log,zip_folder
from apps.interpretation.ai_analysis.utils.custom_enumeration import DetectionType
from apps.interpretation.ai_analysis.utils.redis_operation import celeryrecord,delete_one_record
from apps.interpretation.ai_analysis.utils.dataVerification import data_verify
from apps.interpretation.ai_tasks import *
from apps.interpretation.models import InterpretationTaskResult,InterpretationTask


from logger import Logger

node_information = []
host = config.REDISIP
ai_db = config.AI_DB
redis_client = redis.Redis(host=host, port=6379, db=ai_db)

logger = Logger(logname='interpretation_views.log', loglevel=5, logger='interpretation').getlog()


def add_interpretation_task_result(request):
    """
    新建任务
    """
    params = json.loads(request.body.decode('utf-8'))
    name = params.get('name')
    task_type = params.get('taskType')
    data_path_id = params.get('dataPathId')
    username = params.get('username')
    # 根据成果服务id查找资源对应的坐标系代号
    data_cors = Resource.objects.get(id=data_path_id).coordinate_system
    # 若新增任务类别是地类变化
    if task_type == '地类变化':
        prev_id = params.get('prevId')
        next_id = params.get('nextId')
        # 前时影像坐标系
        prev_cors = Resource.objects.get(id=prev_id).coordinate_system
        # 后时影像坐标系
        next_cors = Resource.objects.get(id=next_id).coordinate_system
        # 判断地类变化前时影像、后时影像坐标系和成果服务坐标系三者是否相同，若相同
        if prev_cors == next_cors == data_cors:
            try:
                task_obj = InterpretationTaskResult.objects.create(
                    name=name,
                    task_type=task_type,
                    data_path_id=data_path_id,
                    prev_id=prev_id,
                    next_id=next_id,
                    create_person=username,
                )
            except Exception as e:
                return error('任务名称不能重复！')

            return ok('地类变化图斑获取成功！')
        else:
            return warning('前景影像、后景影像、检测成果坐标系不同，请重新输入！')
    else:
        # 新增地类分割或者目标检测任务
        path_id = params.get('path_id')
        path_cors = Resource.objects.filter(id=path_id).first().coordinate_system.name
        # 判断坐标系是否相同
        if path_cors != data_cors:
            logger.info("用户{}新增任务资源ID{}失败，原因是：影像图层、检测成果图层坐标系不同，请重新输入！".format(
                request.user.username, path_id))
            return warning('影像图层、检测成果图层坐标系不同，请重新输入！')
        InterpretationTaskResult.objects.create(
            name=name,
            task_type=task_type,
            data_path_id=data_path_id,
            path_id=path_id,
            create_person=username,
        )
        return ok('新建任务成功！')


def get_all_task_resources(request):
    """
    获取新建任务需要的资源数据
    """
    resp = {
        "code": 0,
        "msg": 'null',
        "data": {}
    }
    images_list = []  # 影像数据
    # 影像分割数据
    image_segmentation_list = []
    business_list = []
    county_list = list(
        Resource.objects.filter(source_type='影像服务').all().values_list('county', flat=True).distinct())
    for item in county_list:
        images_list1 = []
        images_dict = {'name': item}
        images_results = Resource.objects.filter(source_type='影像服务').filter(
            county=item).all().extra(
            select={'id': 'id', 'name': 'name'}).values_list('id', 'name')
        for i in list(images_results):
            result = {'id': i[0], 'name': i[1]}
            images_list1.append(result)
        images_dict['values'] = images_list1
        images_list.append(images_dict)

    county_list2 = list(
        Resource.objects.filter(source_type='业务矢量数据服务').all().values_list('county', flat=True).distinct())
    for item in county_list2:
        images_list2 = []
        images_dict2 = {'name': item}
        images_results2 = Resource.objects.filter(source_type='业务矢量数据服务').filter(
            county=item).all().extra(
            select={'id': 'id', 'name': 'name'}).values_list('id', 'name')
        for i in list(images_results2):
            result2 = {'id': i[0], 'name': i[1]}
            images_list2.append(result2)
        images_dict2['values'] = images_list2
        business_list.append(images_dict2)
    # 根据行政区统计影响分割数据
    image_segmentation_results = Resource.objects.filter(
        source_type='影像服务').all()
    for j in image_segmentation_results:
        result = {'id': j.id, 'name': j.name, 'county': j.county}
        image_segmentation_list.append(result)

    resp['data'] = {
        'imagesList': images_list,
        'imageSegmentationList': image_segmentation_list,
        'changeDetectionList': image_segmentation_list,
        'businessList': business_list,
    }
    # 数据返回至前端以echarts表格形式展示
    print(resp)
    return JsonResponse(resp, json_dumps_params={'ensure_ascii': False})
    # return JsonResponse(resp)


def get_all_task(request):
    """
    获取任务数据
    """
    keyword = request.GET.get('filter')  # 条件查询
    page = request.GET.get("pageIndex", 1)  # 分页
    limit = request.GET.get("pageSize", 8)
    order_by = request.GET.get('orderField', '')  # 排序字段
    print("keyword:", keyword)
    data = []
    latest_task_id = InterpretationTaskResult.objects.all().order_by('-id')[0].id
    # 如果没有搜索，返回全部数据，按照创建时间排序
    if keyword is None:
        task_obj = InterpretationTaskResult.objects.all().order_by('-id')
    else:
        keyword = eval(keyword)
        name = keyword.get("name")
        create_time = keyword.get("create_time")
        if "name" in keyword:
            keyword.pop('name')
        if "create_time" in keyword:
            keyword.pop('create_time')
        county = keyword.get("county")
        if "county" in keyword:
            keyword.pop("county")
        if len(name) == 0 and len(create_time) == 0:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).all()
        elif len(name) != 0 and len(create_time) == 0:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).filter(name__contains=name).all()
        elif len(name) == 0 and len(create_time) != 0:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).filter(
                create_time__year=create_time.split('-')[0]). \
                filter(create_time__month=create_time.split('-')[1]) \
                .filter(create_time__day=create_time.split('-')[2]).all()
        else:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).filter(
                create_time__year=create_time.split('-')[0]). \
                filter(create_time__month=create_time.split('-')[1]) \
                .filter(create_time__day=create_time.split('-')[2]).filter(name__contains=name).all()

        if county:
            task_obj = task_obj.filter(county=county).all()

    # 按照时间排序
    if order_by == 'name':
        task_obj = task_obj.order_by('-name')
    else:  # 按照名称排序
        task_obj = task_obj.order_by('-create_time')
    paginator = Paginator(task_obj, limit)
    results = paginator.page(page)
    total_polygon = 0  # 记录总的图斑数量

    for result in results:
        # 如果是地类变化，记录前时影像和后时影像信息
        if result.prev_id:
            prev_image = Resource.objects.get(id=result.prev_id)
            next_image = Resource.objects.get(id=result.next_id)
            prev_image1 = {'name': prev_image.name, 'appendTime': prev_image.append_time,
                           'url': prev_image.url, 'serviceType': prev_image.service_type}
            next_image1 = {'name': next_image.name, 'appendTime': next_image.append_time,
                           'url': next_image.url, 'serviceType': next_image.service_type}
            path = {}
        else:
            prev_image1 = {}
            next_image1 = {}
            path_image = Resource.objects.get(id=result.path_id)
            path = {'name': path_image.name, 'appendTime': path_image.append_time, 'url': path_image.url,
                    'dataType': path_image.data_type, 'serviceType': path_image.service_type}
        data_path_resource = Resource.objects.get(id=result.data_path_id)
        record = {
            "id": result.id,
            "name": result.name,
            "path": path,
            "prevImage": prev_image1,
            "nextImage": next_image1,
            'createTime': result.create_time.strftime('%Y-%m-%d'),
            "data_path": data_path_resource.url,
            "data_path_service_type": data_path_resource.service_type,
            "county": data_path_resource.county,
            "datasets_name": data_path_resource.datasets_name,
            "createPerson": result.create_person,
            "polygon_count": data_path_resource.count,
            "taskType": result.task_type,
            "appendTime": data_path_resource.append_time,
        }
        total_polygon += data_path_resource.count
        data.append(record)
    county_list = set()
    for i in Resource.objects.all():
        county_list.add(i.county)
    response_data = {
        'total': len(task_obj),
        'data': data,
        'total_polygon': total_polygon,
        'county_list': list(county_list),
        'latestID': latest_task_id,
        'code': 0
    }

    return JsonResponse(response_data)


def get_interpretation_task_result_by_id(request, task_id):
    """
    根据ID获取单个任务
    """
    data_obj = InterpretationTaskResult.objects.get(id=task_id)
    task_type = data_obj.task_type
    if task_type == '地类变化':
        prev_image = Resource.objects.get(id=data_obj.prev_id)
        next_image = Resource.objects.get(id=data_obj.next_id)
        prev_image1 = {'name': prev_image.name, 'appendTime': prev_image.append_time,
                       'coordinateSystem': prev_image.coordinate_system,
                       'url': prev_image.url, 'serviceType': prev_image.service_type}
        next_image1 = {'name': next_image.name, 'appendTime': next_image.append_time,
                       'coordinateSystem': next_image.coordinate_system,
                       'url': next_image.url, 'serviceType': next_image.service_type}
        path_image = {}
    else:
        prev_image1 = {}
        next_image1 = {}
        path_image = Resource.objects.get(id=data_obj.path_id)
        path_image = {'name': path_image.name, 'appendTime': path_image.append_time, 'url': path_image.url,
                      'coordinateSystem': path_image.coordinate_system,
                      'dataType': path_image.data_type, 'serviceType': path_image.service_type}
    data_path_image = Resource.objects.get(id=data_obj.data_path_id)
    response_data = {
        "code": 0,
        "msg": 'null',
        "data": {
            "id": data_obj.id,
            "name": data_obj.name,
            "path": path_image,
            "prevImage": prev_image1,
            "nextImage": next_image1,
            "createTime": data_obj.create_time.strftime('%Y-%m-%d %H%M%S'),
            "dataPath": data_path_image.url,
            "dataPathServiceType": "iServer",
            "county": data_path_image.county,
            "datasetsName": data_path_image.datasets_name,
            "owner": data_obj.create_person,
            "polygonCount": 11,
            "taskType": "地类变化",
            "taskTypeTag": "地类变化",
            "appendTime": "2025-06",
            "datasourceName": data_path_image.datasource_name,
            "count": data_path_image.count,
            "sourceCountyData": [],
            "changePolygonCount": [],
            "center": 'null',
            "dataTypeList": 'null',
            "countyData": 'null',
            "dataType": 'null',
            "desc": 'null',
            "status": 'null'
        }
    }
    return JsonResponse(response_data)


def fetch_interpretation_task_result_fronted(request):
    """
    高清航片解译/地类变化 获取所有数据
    """
    """
       获取任务数据
       """
    keyword = request.GET.get('filter')  # 条件查询
    page = request.GET.get("pageIndex", 1)  # 分页
    limit = request.GET.get("pageSize", 8)
    order_by = request.GET.get('orderField', '')  # 排序字段
    print("keyword:", keyword)
    data = {"taskResultData": [], "latestID": ''}
    latest_task_id = InterpretationTaskResult.objects.all().order_by('-id')[0].id
    # 如果没有搜索，返回全部数据，按照创建时间排序
    if keyword is None:
        task_obj = InterpretationTaskResult.objects.all().order_by('-id')
    else:
        keyword = eval(keyword)
        name = keyword.get("name")
        create_time = keyword.get("create_time")
        if "name" in keyword:
            keyword.pop('name')
        if "create_time" in keyword:
            keyword.pop('create_time')
        county = keyword.get("county")
        if "county" in keyword:
            keyword.pop("county")
        if len(name) == 0 and len(create_time) == 0:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).all()
        elif len(name) != 0 and len(create_time) == 0:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).filter(name__contains=name).all()
        elif len(name) == 0 and len(create_time) != 0:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).filter(
                create_time__year=create_time.split('-')[0]). \
                filter(create_time__month=create_time.split('-')[1]) \
                .filter(create_time__day=create_time.split('-')[2]).all()
        else:
            task_obj = InterpretationTaskResult.objects.filter(**keyword).filter(
                create_time__year=create_time.split('-')[0]). \
                filter(create_time__month=create_time.split('-')[1]) \
                .filter(create_time__day=create_time.split('-')[2]).filter(name__contains=name).all()

        if county:
            task_obj = task_obj.filter(county=county).all()

    # 按照时间排序
    if order_by == 'name':
        task_obj = task_obj.order_by('-name')
    else:  # 按照名称排序
        task_obj = task_obj.order_by('-create_time')
    paginator = Paginator(task_obj, limit)
    results = paginator.page(page)
    total_polygon = 0  # 记录总的图斑数量

    for result in results:
        # 如果是地类变化，记录前时影像和后时影像信息
        if result.prev_id:
            prev_image = Resource.objects.get(id=result.prev_id)
            next_image = Resource.objects.get(id=result.next_id)
            prev_image1 = {'name': prev_image.name, 'appendTime': prev_image.append_time,
                           'url': prev_image.url, 'serviceType': prev_image.service_type}
            next_image1 = {'name': next_image.name, 'appendTime': next_image.append_time,
                           'url': next_image.url, 'serviceType': next_image.service_type}
            path = {}
        else:
            prev_image1 = {}
            next_image1 = {}
            path_image = Resource.objects.get(id=result.path_id)
            path = {'name': path_image.name, 'appendTime': path_image.append_time, 'url': path_image.url,
                    'dataType': path_image.data_type, 'serviceType': path_image.service_type}
        data_path_resource = Resource.objects.get(id=result.data_path_id)
        record = {
            "id": result.id,
            "name": result.name,
            "path": path,
            "prevImage": prev_image1,
            "nextImage": next_image1,
            'createTime': result.create_time.strftime('%Y-%m-%d'),
            "data_path": data_path_resource.url,
            "data_path_service_type": data_path_resource.service_type,
            "county": data_path_resource.county,
            "datasets_name": data_path_resource.datasets_name,
            "createPerson": result.create_person,
            "polygon_count": data_path_resource.count,
            "taskType": result.task_type,
            "appendTime": data_path_resource.append_time,
        }
        total_polygon += data_path_resource.count
        data['taskResultData'].append(record)
    data['latestID'] = latest_task_id
    county_list = set()
    for i in Resource.objects.all():
        county_list.add(i.county)
    response_data = {
        'total': len(task_obj),
        'data': [data],
        'county_list': list(county_list),
        'latestID': latest_task_id,
        'code': 0
    }

    return JsonResponse(response_data)


def get_stat_info(request):
    resp = {
        "code": 0,
        "msg": 'null',
        "data": {
            "chartData": {
                "changeSpotByArea": {
                    "series": [
                        6,
                        11
                    ],
                    "xaxis": [
                        "高淳县(320125)",
                        "栖霞区(320113)"
                    ]
                },
                "changeSpotByTime": {
                    "series": [
                        17
                    ],
                    "xaxis": [
                        "2025"
                    ]
                },
                "segSpotByArea": {
                    "series": [
                        444
                    ],
                    "xaxis": [
                        "高淳县(320125)"
                    ]
                },
                "segSpotByTime": {
                    "series": [
                        444
                    ],
                    "xaxis": [
                        "2025"
                    ]
                }
            },
            "totalChangePolygon": 17,
            "totalSegPolygon": 444
        }
    }
    return JsonResponse(resp)


def get_detail_result(request,task_id):
    """
    获取任务结果详情
    """

    """
       根据ID获取单个任务
       """
    data_obj = InterpretationTaskResult.objects.get(id=task_id)
    task_type = data_obj.task_type
    if task_type == '地类变化':
        prev_image = Resource.objects.get(id=data_obj.prev_id)
        next_image = Resource.objects.get(id=data_obj.next_id)
        prev_image1 = {'name': prev_image.name, 'appendTime': prev_image.append_time,
                       'coordinateSystem': prev_image.coordinate_system,'center':prev_image.center,
                       'url': prev_image.url, 'serviceType': prev_image.service_type}
        next_image1 = {'name': next_image.name, 'appendTime': next_image.append_time,
                       'coordinateSystem': next_image.coordinate_system,'center':next_image.center,
                       'url': next_image.url, 'serviceType': next_image.service_type}
        path_image = {}
    else:
        prev_image1 = {}
        next_image1 = {}
        path_image = Resource.objects.get(id=data_obj.path_id)
        path_image = {'name': path_image.name, 'appendTime': path_image.append_time, 'url': path_image.url,
                      'coordinateSystem': path_image.coordinate_system,'center':path_image.center,
                      'dataType': path_image.data_type, 'serviceType': path_image.service_type}
    data_path_image = Resource.objects.get(id=data_obj.data_path_id)
    response_data = {
        "code": 0,
        "msg": 'null',
        "data": {
            "id": data_obj.id,
            "name": data_obj.name,
            "path": path_image,
            "prevImage": prev_image1,
            "nextImage": next_image1,
            "createTime": data_obj.create_time.strftime('%Y-%m-%d %H%M%S'),
            "dataPath": data_path_image.url,
            "dataPathServiceType": "iServer",
            "county": data_path_image.county,
            "datasetsName": data_path_image.datasets_name,
            "owner": data_obj.create_person,
            "polygonCount": 11,
            "taskType": "地类变化",
            "taskTypeTag": "地类变化",
            "appendTime": "2025-06",
            "datasourceName": data_path_image.datasource_name,
            "count": data_path_image.count,
            "sourceCountyData": [],
            "changePolygonCount": [],
            "center": 'null',
            "dataTypeList": 'null',
            "countyData": 'null',
            "dataType": 'null',
            "desc": 'null',
            "status": 'null'
        }
    }
    return JsonResponse(response_data)




def ai_detection_one_step(request):
    """
    影像分割、变化检测、影像分割擦除批量一键通
    @return:请求成功或失败信息
    """
    global node_information
    print("---------------------------------接收到请求------------------------------")
    data = json.loads(request.body.decode('utf-8'))
    seg_path = data.get('segPath','')  # 输入文件路径
    pre_path = data.get('prePath','')  # 输入文件路径
    next_path = data.get('nextPath','')  # 输入文件路径
    outputpath = data.get('output_path') # 输出文件路径
    fragment = data.get('fragment', '50') # 碎斑阈值
    detection_type = data.get('detection_type') # 检测类型
    print("检测类型：",detection_type)
    model_name = data.get('model_name') # 模型名称
    print("模型名称：",model_name)
    building_regular = data.get('building_regular', '0') # 是否规则化
    model_path = data.get('model_path') # 模型路径
    model_network = data.get('model_network') # 模型网络
    config_path = data.get('config_path','') # 配置文件路径
    project_id = data.get('project_id') # 项目id
    output_path = os.path.join(settings.SHARED_PATH,'result',outputpath)
    create_path(output_path)
    task_ids = []
    print("项目id:",project_id)
    if detection_type == DetectionType.IMAGESEGMENTATION.value or detection_type == DetectionType.PREDICTIONBASEDONCD.value or detection_type == DetectionType.ERASEBASEDONIS.value:
        pass
    else:
        return JsonResponse({'code': 400, 'message': '检测类型错误', 'data': {}})

    try:
        if detection_type == DetectionType.IMAGESEGMENTATION.value:
            if seg_path.endswith(".tif") or seg_path.endswith('.tiff'):
                task_id = str(uuid.uuid1()).replace('-', '')
                # 序列化任务信息
                image_segmentation_predict.apply_async(
                    args=[task_id,project_id,seg_path,output_path, fragment, building_regular,
                       model_path, model_name, config_path, model_network],
                    task_id=task_id,
                    options=project_id)

                task_ids.append({"file_name": os.path.basename(seg_path), "task_id": task_id})
            else:
                print({"code": 500, "msg": "请上传tif格式的图片"})
                return JsonResponse({"code": 500, "msg": "请上传tif格式的图片"})
        else:
            if not pre_path.endswith(".tif") and not next_path.endswith('.tiff'):
                print({"code": 500, "msg": "数据有问题,请上传tif格式的图片"})
                return JsonResponse({"code": 500, "msg": "数据有问题,请上传tif格式的图片"})
            else:
                prev_path = pre_path
                next_path = next_path
                folder_name = os.path.basename(prev_path).split('.')[0]
                task_id = str(str(uuid.uuid1())).replace('-', '')
                if detection_type == DetectionType.PREDICTIONBASEDONCD.value:
                    change_detection_one_step.apply_async(
                        args=[task_id,project_id,output_path,folder_name,prev_path,next_path,model_path,fragment,model_network,building_regular],
                        task_id=task_id ,
                        options=project_id)
                elif detection_type == DetectionType.ERASEBASEDONIS.value:
                    image_seg_er_predict.apply_async(
                        args=[task_id,project_id,prev_path, next_path, model_path, model_network, fragment, building_regular,output_path,config_path],
                        task_id=task_id,
                        options=project_id)

                task_ids.append({"file_name": folder_name, "task_id": task_id})
        print({
            'message': '数据已接收，后台运行中',
            'error': 0,
            'task_id': task_ids,
            'project_id': project_id,
            'node_information': node_information,
        })
        return JsonResponse({
            'message': '数据已接收，后台运行中',
            'error': 0,
            'task_id': task_ids,
            'project_id': project_id,
            'node_information': node_information,
        })
    except Exception as e:
        print(e)
        return JsonResponse({'message': str(e), 'error': 403})

def server_paths(request):
    """
    获取服务器路径
    @param request:
    @return:
    """
    target_dir = os.path.join(settings.SHARED_PATH, 'remote_images')
    # 获取目录下的所有文件夹
    paths = [os.path.join(target_dir, d) for d in os.listdir(target_dir)]
    filter_paths = [path for path in paths if path.endswith('.tif') or path.endswith('.tiff')]
    result_path = os.path.join(settings.SHARED_PATH, 'result')
    result_dirs = [dir_name for dir_name in os.listdir(result_path)]
    filter_paths.sort(key=lambda x: os.path.getctime(os.path.join(target_dir, x)), reverse=True)
    return JsonResponse({'paths': filter_paths, 'result_path': result_dirs})

def get_models_list(request):
    """
    获取模型列表
    """
    seg_models_dic = config.IMAGE_SEGMENTATION_MODEL
    data = []
    for i in config.IMAGE_SEGMENTATION_MODEL:
        network = os.path.basename(seg_models_dic[i]).split('_')[0]
        config_path = config.MMSEG_CONFIGPY[i] if (i in config.MMSEG_CONFIGPY and config.MMSEG_CONFIGPY[i]) else ''
        data.append({'model_type_name': i, 'model_path': seg_models_dic[i],'network':network,'model_type': '地类分割','config_path':config_path})
    change_detection_models_dic = config.CHANGE_DETECTION_MODEL
    for i in change_detection_models_dic:
        network = os.path.basename(change_detection_models_dic[i]).split('_')[0]
        data.append({'model_type_name': i, 'model_path': change_detection_models_dic[i],'network':network,'model_type': '地类变化','config_path':''})
    return JsonResponse({'code':0,'models': data,'msg':'success'})

def get_process_status_node(request):
    """
    获取当前各个机器进展情况
    Returns:
    """
    try:
        paras = json.loads(request.body.decode('utf-8'))
        detection_type = paras.get('detection_type')
        task_name = paras.get('task_name')
        if not detection_type or not task_name:
            return JsonResponse({'code': 500, 'msg': '参数缺失，参数均不能为空值'})

        node_information = config.node_information_all.get(detection_type, [])    # 当前节点状态变量
        node_information_all, node_information_all_step = [], 0
        if len(node_information) == 0:
            return JsonResponse({'code': 0, 'msg': '检测类型未找到', 'data': []})
        data = []
        log_file_path = os.path.join(config.logger_path, 'ai_interpretation.log')
        penultimate_line, current_process = read_log(log_file_path)
        is_error = False
        # 更新节点信息：若未检测到报错信息，则正常检测节点信息位置进行状态更新；反之，以上一节点为准，状态值为0：未完成，1：已完成,3进行中，2报错
        if "ERROR" not in current_process:
            verification_tag = ("".join(current_process.split('-')[1:])).split(':')[0]
            if verification_tag not in node_information:
                time.sleep(2)
                penultimate_line, current_process = read_log(log_file_path)
            try:
                tag_index = node_information.index(verification_tag)
            except ValueError:
                tag_index = 0

            # 更新节点状态
            for i, step in enumerate(node_information):
                if i < tag_index:
                    status = 1  # 已完成
                    node_information_all_step += 1
                elif i == tag_index:
                    status = 3  # 进行中
                else:
                    status = 0  # 未开始
                node_information_all.append({'node_name': step, 'status': status})
        else:
            is_error = True
            error_verification_tag = ("".join(current_process.split('-')[1:])).split(':')[0]
            try:
                tag_index = node_information.index(error_verification_tag)
            except ValueError:
                tag_index = 0

            for i, step in enumerate(node_information):
                if i < tag_index:
                    status = 1  # 已完成
                    node_information_all_step += 1
                elif i == tag_index:
                    status = 2  # 报错
                else:
                    status = 0  # 未开始
                node_information_all.append({'node_name': step, 'status': status})

        # 先查节点Gpu信息
        ip_computer = config.IP_ADDRESS
        json_file_path = os.path.join(config.logger_path, 'system_info', '{}.json'.format(ip_computer.replace('.','-')))
        ip_message = read_json_data(json_file_path)
        ip_message['node_message'] = '主节点'
        ip_message['ip_computer'] = ip_computer.replace("-", ".")
        data.insert(0, {
            'ip_message': ip_message,
            'current_process': current_process,
            'node_image': task_name,
            'node_information': node_information_all,
            'node_information_all_step': node_information_all_step,
        })

        # 计算已完成节点的数量
        completed_steps = sum(1 for node in node_information_all if node['status'] == 1 or node['status'] == 2 or node['status'] == 3)
        total_steps = len(node_information)
        progress_percentage = round((completed_steps / total_steps),3) * 100 if total_steps > 0 else 0
        count, task_id_list = celeryrecord()
        error_count = 0
        success_count = 0
        if int(progress_percentage) == 100:
            if is_error:
                error_count = 1
            else:
                success_count = 1
        print({'data': data, 'current_status': progress_percentage, "error": 0,"msg": 'get the status information succeeded!', 'redis_queue': count,
               "error_count":error_count, "success_count":success_count})
        return JsonResponse({
            'data': data,
            'current_status': progress_percentage,
            "error": 0,
            "msg": 'get the status information succeeded!',
            'redis_queue': count,
            'error_count':error_count,
            'success_count':success_count
        })
    except Exception as e:
        return JsonResponse({
            'data': [],
            'current_status': 0,
            'msg': 'get txt file failed',
            'error': e
        })

def search_redis_count(request):
    """
        查询redis中任务数量
        Args:
            request:
        Returns:
    """
    try:
        count,taskid_list = celeryrecord()
        return JsonResponse({
            'count': count,
            'taskIdList': taskid_list,
            'code': 200,
            'msg': '查询任务数量成功!!'
        })
    except Exception as e:
        return JsonResponse({
        'count':0,
        'taskIdList':[],
        'code': 500,
        'msg': '查询任务数量失败!!'
    })

def get_redis_count(request):
    """
    请求获取还有多少个任务为未完成，查询数据库
    查询数据库
    Returns:
    """
    #改为直接从redis获取 我们的项目是直接存储celery队列中
    queue_name = 'celery'
    # 使用 LRANGE 命令查看队列中的全部任务
    tasks = redis_client.lrange(queue_name, 0, -1)
    count = len(tasks)
    return JsonResponse({'count': count, 'error': 0, "msg": '运行中的任务数量获取成功!!!'})

def get_gpu_free_memory(request):
    """
    获取当前各个机器显存剩余,返回不足5GB的ip地址和容量
    Returns:
    """
    data = []
    # 系统日志目录
    log_sys_path = os.path.join(config.logger_path, 'system_info')
    try:
        for log_file in os.listdir(log_sys_path):
            json_file_path = os.path.join(log_sys_path, log_file)
            ip_message = read_json_data(json_file_path)
            gpu_free_memory, available_memory, used_cpu = ip_message['gpu_free_memory'], ip_message['available_memory'], \
            ip_message['used_cpu']
            gpu_free_memory_num = float(re.search(r'(\d+(?:\.\d+)?)', ip_message['gpu_free_memory']).group())
            available_memory_num = float(re.search(r'(\d+(?:\.\d+)?)', ip_message['available_memory']).group())
            used_cpu_num = float(ip_message['used_cpu'].rstrip('%'))
            ip_computer = ip_message.get('ip_address').replace('-', '.')
            if gpu_free_memory_num / 1024 < 5 or available_memory_num < 20 or used_cpu_num > 50:
                data.append({'ip_address': ip_computer, 'gpu_free_memory': gpu_free_memory,
                             'available_memory': available_memory, 'used_cpu': used_cpu})
        return JsonResponse({
            'data': data,
            "error": 0,
            "msg": 'get succeeded!',
        })
    except Exception as e:
        return JsonResponse({
            "error": 1,
            "msg": str(e),
        })

def data_verify_main(request):
    """
    数据校验
    """
    data = json.loads(request.body.decode('utf-8'))
    inputpath = data.get('input_path','')
    pre_path = data.get('input_path_prev','')
    nex_path = data.get('input_path_next','')
    data_obj = []
    largedataCount = 0
    error_corsCount = 0
    data_size = config.dataSize
    try:
        if inputpath.endswith('.tif') or inputpath.endswith('.tiff'):
            tifinfo = data_verify(inputpath)
            largedataCount += tifinfo['is_largedata']
            error_corsCount += tifinfo['is_errorEpsg']
            data_obj.append(tifinfo)
        elif pre_path and nex_path:
            if pre_path.endswith('.tif') or pre_path.endswith('.tiff') and (nex_path.endswith('.tif') or nex_path.endswith('.tiff')):
                tifinfo = data_verify(pre_path)
                largedataCount += tifinfo['is_largedata']
                error_corsCount += tifinfo['is_errorEpsg']
                data_obj.append(tifinfo)
                tifinfo = data_verify(nex_path)
                largedataCount += tifinfo['is_largedata']
                error_corsCount += tifinfo['is_errorEpsg']
                data_obj.append(tifinfo)
        print({"datainfo":data_obj,"largedataCount":largedataCount, "errorEpsgcount":error_corsCount,"status":"success"})
        return JsonResponse({"datainfo":data_obj,"largedataCount":largedataCount, "errorEpsgcount":error_corsCount,"status":"success","dataSize":data_size})
    except Exception as e:
        return JsonResponse({"msg:":e,"status":"error"})

def emptyRedis(request):
    """
        清除redis缓存
        Args:
            request:
        Returns:
    """
    # 前端响应数据
    response_data = {
        'msg': '清除redis成功！',
        'statusCode': 200,
    }
    try:

        # 获取所有任务键
        task_keys = redis_client.keys('*')
        print(len(task_keys))
        if len(task_keys) > 0:
            print("Redis中还有任务存在。")
        else:
            print("Redis中没有任务。")
        redis_client.flushall()
        print("redis数据库已清空")
    except Exception as e:
        response_data = {
            'msg': '清除redis失败！',
            'statusCode': 403,
        }
    return JsonResponse(response_data)

def task_terminatemain(request):
    """
    删除指定任务
    """
    print("---------------------------------接收到请求------------------------------")
    data = json.loads(request.body.decode('utf-8'))
    project_id = data.get('project_id')
    print(project_id)
    try:
        #删除redis的任务
        tag,msg = delete_one_record(project_id)
        print(tag,msg)
        if not tag:
            msg = '该任务已在被celery预领取，已不可终止，请重新刷新页面即可查看任务状态!!!'
        else:
            InterpretationTask.objects.filter(id=project_id).update(status=4)
        return JsonResponse({'message': msg,'code':0,'tag':tag})
    except Exception as e:
        return JsonResponse({'error': str(e),'code':0})

def download_task_result(request):
    """
    下载任务结果
    """
    try:
        print("---------------------------------接收到请求------------------------------")
        data = json.loads(request.body.decode('utf-8'))
        task_name = data.get('task_name')
        outpath_name = data.get('output_path')
        detection_type = data.get('detection_type')
        shp_path = ''
        outpath = os.path.join(settings.SHARED_PATH,'result',outpath_name)
        zip_path = os.path.join(settings.SHARED_PATH, 'result', f'{task_name}.zip')
        if detection_type == DetectionType.ERASEBASEDONIS.value:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i in os.listdir(outpath):
                    if "change_detection_result" in i:
                        file_path = os.path.join(outpath, i)
                        # 在ZIP中保持相对路径结构
                        arcname = os.path.relpath(file_path, os.path.dirname(outpath))
                        zipf.write(file_path, arcname)
        else:
            for root, dirs, files in os.walk(outpath):
                if detection_type == DetectionType.IMAGESEGMENTATION.value or detection_type == DetectionType.PREDICTIONBASEDONCD.value:
                    if 'shp' in dirs:
                        shp_path = os.path.join(root, 'shp')
                        zip_folder(shp_path, zip_path)
                        continue

        # StreamingHttpResponse将文件内容进行流式传输，数据量大可以用这个方法
        if not os.path.exists(zip_path):
            return JsonResponse({"error": "压缩文件未找到"}, status=404)
        response = StreamingHttpResponse(file_iterator(zip_path))
        # 以流的形式下载文件,这样可以实现任意格式的文件下载
        response['Content-Type'] = 'application/octet-stream'
        # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(escape_uri_path(task_name))
        return response
    except Exception as e:
        print(e)
        return JsonResponse({"error": "文件未找到"}, status=404)