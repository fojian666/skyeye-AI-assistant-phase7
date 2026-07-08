# _*_ coding: utf-8 _*_
# @Time : 2024/12/18 14:58 
# @Author : xxx 
# @Version：V 0.1
# @File : verify_views.py
# @desc :
import ast
import datetime
import json
import os
import random
from math import radians, sin, acos, cos

import openpyxl
import requests
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.db import transaction
from apps.panorama.models import VerifyTask, VerifyClue, PolygonData, PolygonTask, BufferFile, PanoramaImage, \
    PointLocation, Clue
import geopandas as gpd
from apps.panorama.common import unzip_file, compute_yaw_pitch
from apps.panorama.generate_file import zip_folder
from shapely import Polygon, MultiPolygon
from shapely.geometry import Polygon as shapely_polygon
from utils_tools.common import transform_xy, parse_jwt_token
from logger import Logger
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from .panorama_views import file_iterator
from django.utils.encoding import escape_uri_path

logger = Logger(logname='verify_views.log', loglevel=5, logger='verify').getlog()


def files(request):
    """
    上传文件接口
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            myFile = request.FILES.get("file", None)
            if myFile:
                save_path = os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name)
                destination = open(save_path, 'wb+')
                for chunk in myFile.chunks():
                    destination.write(chunk)
                destination.close()
                if myFile.name.endswith('.zip'):
                    unzip_file(save_path, os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name.split('.')[0]))
                elif myFile.name.endswith('xlsx') or myFile.name.endswith('xls'):
                    verify_task_obj = VerifyTask.objects.create(
                        task_name=myFile.name,
                        file_path=save_path,
                        file_size=os.path.getsize(save_path),
                        status='未推送'
                    )
                    # 打开 Excel 文件
                    workbook = openpyxl.load_workbook(save_path)
                    sheet = workbook.active  # 选择第一个工作表
                    # 读取单元格数据
                    for row_value in sheet.iter_rows(values_only=True):
                        longitude, latitude = transform_xy(row_value[2], row_value[3])
                        VerifyClue.objects.create(
                            longitude=longitude,
                            latitude=latitude,
                            task=verify_task_obj,
                            division_code=row_value[4],
                            address=row_value[5],
                            level=row_value[6],
                            status='待核实',
                        )

            return JsonResponse({'code': 0, 'msg': '上传成功'})
        except Exception as e:
            logger.error(f'上传失败: {str(e)}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': '上传失败', 'error': str(e)})


def filter_verify_clue(status=None, division_code=None, start_date=None, end_date=None, verify_task=None):
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
    try:
        # 构建查询条件
        filters = Q()
        if status:
            filters &= Q(status=status)
        if division_code:
            filters &= Q(division_code=division_code)
        if start_date:
            filters &= Q(record_time__gte=start_date)
        if end_date:
            filters &= Q(record_time__lte=end_date)
        if verify_task:
            if verify_task != '':
                filters &= Q(task_id=int(verify_task))
        # 应用过滤条件
        verify_clue_list = VerifyClue.objects.filter(filters).order_by('-clue_id')
        return verify_clue_list
    except Exception as e:
        logger.error(f'过滤线索时发生错误: {str(e)}')
        return None


def verify_clue(request):
    """
    获取核实线索
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        status = params.get('status', '')
        start_date = params.get('start_date', '')
        end_date = params.get('end_date', '')
        division_code = params.get('division_code', '')
        verify_task_id = params.get('verify_task_id', '')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        verify_clue_list = filter_verify_clue(status, division_code, start_date, end_date, verify_task_id)
        if len(verify_clue_list) > 0:
            paginator = Paginator(verify_clue_list, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        for i in results:
            record = {
                'clue_id': i.clue_id,
                'status': i.status,
                'division_code': i.division_code,
                'address': i.address,
                'level': i.level,
                "longitude": i.longitude,
                'latitude': i.latitude,
                'verify_task': i.task.task_id,
                'record_time': i.record_time.strftime('%Y-%m-%d %H:%M:%S'),
                'video_path': ''
            }
            data.append(record)
        response_data = {'code': 0, 'msg': '', 'data': data, 'count': len(verify_clue_list)}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取核实线索异常{e}')
        return JsonResponse({'code': 500, 'msg': str(e)})


def verify_clue_list(request):
    """
    根据任务id查询核实线索
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        task_id = params.get('task_id', '')
        if task_id:
            verify_clue_list = VerifyClue.objects.filter(task_id=task_id).all()
        else:
            verify_clue_list = VerifyClue.objects.all()
        data = []
        for i in verify_clue_list:
            record = {
                'clue_id': i.clue_id,
                'status': i.status,
                'division_code': i.division_code,
                'address': i.address,
                'level': i.level,
                "longitude": i.longitude,
                'latitude': i.latitude,
                'verify_task': i.task.task_id,
                'record_time': i.record_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)
        response_data = {'code': 0, 'msg': '核实成功', 'data': data, 'count': len(verify_clue_list)}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取核实线索失败: {e}')
        return JsonResponse({'code': 500, 'msg': '获取核实线索失败', 'data': []})


def verify_task_params(request):
    try:
        verify_task_name_list = []
        results = VerifyTask.objects.all()
        for result in results:
            verify_task_name_list.append({
                'task_id': result.task_id,
                'task_name': result.task_name
            })
        verify_clue_status = [{'value': '待核实', 'name': '待核实'}, {'value': '已核实', 'name': '已核实'}]
        # 获取所有唯一的行政区
        division_code_list = VerifyClue.objects.values_list('division_code', flat=True).distinct()
        total_count = VerifyClue.objects.count()
        total_todo_count = VerifyClue.objects.filter(status='待核实').count()
        total_done_count = VerifyClue.objects.filter(status='已核实').count()
        # 将结果转换为列表
        division_code_list = list(division_code_list)
        data = {
            'verify_task_name_list': verify_task_name_list,
            'verify_clue_status': verify_clue_status,
            'division_code_list': division_code_list,
            'total_count': total_count,
            'total_todo_count': total_todo_count,
            'total_done_count': total_done_count
        }
        return JsonResponse({'code': 0, 'msg': '', 'data': data, 'count': 0})
    except Exception as e:
        logger.error(f'获取核实任务参数异常{e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': [], 'count': 0})


def verify_task(request):
    """

    @param request:
    @return:
    """
    try:
        params = json.loads(request.body)
        task_name = params.get('task_name', '')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        verify_task_list = VerifyTask.objects.filter(task_name__contains=task_name).all()
        if len(verify_task_list) > 0:
            paginator = Paginator(verify_task_list, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        for i in results:
            record = {
                'task_id': i.task_id,
                'status': i.status,
                'task_name': i.task_name,
                'file_path': i.file_path,
                'file_size': i.file_size,
                'count': VerifyClue.objects.filter(task=i, status='待核实').count(),
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)
        response_data = {'code': 0, 'msg': '', 'data': data, 'count': len(verify_task_list)}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取任务核实表失败{e}')
        return JsonResponse({'code': 1, 'msg': str(e)})


def verify_clue_add(request):
    """
    新增线索点
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        task_id = params.get('task_id')
        longitude = params.get('longitude')
        latitude = params.get('latitude')
        division_code = params.get('division_code')
        # shapefile_path = os.path.join(settings.BASE_DIR, r'static/shp/ltcj/龙潭村界shp.shp')  # 村界 Shapefile 文件的路径
        # address = find_village_by_point(shapefile_path, latitude, longitude)
        address = params.get('address')
        VerifyClue.objects.create(
            longitude=longitude,
            latitude=latitude,
            address=address,
            status='待核实',
            task_id=task_id,
            division_code=division_code,
            level=''
        )
        return JsonResponse({"code": 0, 'msg': '线索打点成功'})
    except Exception as e:
        logger.error(f'新增线索点失败{e}')
        return JsonResponse({'code': 500, 'msg': f'新增线索点失败{e}'})


def verify_clue_delete(request):
    """
    删除线索点
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            verify_clue_id = params.get('verify_clue_id')
            is_exist = VerifyClue.objects.get(clue_id=verify_clue_id)
            if is_exist:
                is_exist.delete()
                return JsonResponse({"code": 0, 'msg': '线索删除成功'})
            else:
                logger.warning('线索不存在')
                return JsonResponse({"code": 1, 'msg': '线索不存在'})
        except Exception as e:
            logger.error(f'删除线索点失败{e}')
            return JsonResponse({'code': 500, 'msg': f'删除线索点失败{e}'})


def information_push(request):
    """
    异常点推送
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            verify_task_id = int(params.get('task_id'))
            url = "http://221.230.150.241:8889/prod-api/ctuav/policeInfo/add"
            current_verify_task = VerifyTask.objects.filter(task_id=verify_task_id).first()
            # if current_verify_task and current_verify_task.status == "待推送":
            if current_verify_task:
                if current_verify_task.status == "未推送":
                    # data_list = VerifyClue.objects.filter(task_id=verify_task_id, status='已核实').all()
                    data_list = VerifyClue.objects.filter(task_id=verify_task_id).all()
                    for i in data_list:
                        records = {
                            'alarm_id': i.clue_id,
                            "record_time": i.record_time.strftime('%Y-%m-%d %H:%M:%S'),
                            "division_code": i.division_code,
                            "address": i.address,
                            "latitude": i.latitude,
                            "longitude": i.longitude,
                            "level": i.level
                        }
                        response = requests.post('http://221.230.150.241:8889/prod-api/auth/ticketLogin',
                                                 json={'ticket': '7ZiCCyDn+XmW2eJJ9sVcuKmBitMJLVNhboJvJJ0YBuU='})
                        tokena = json.loads(response.text)['token']
                        response = requests.post(url, json=records,
                                                 headers={'Authorization': 'Bearer {}'.format(tokena)})
                    current_verify_task.status = '待拍摄'
                    current_verify_task.save()
                return JsonResponse({"code": 0, 'msg': '推送成功'})
            else:
                return JsonResponse({"code": 500, 'msg': '未找到任务，推送失败'})
        except Exception as e:
            logger.error(f'推送失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, 'msg': '推送失败'})


def geometry_to_coords_array(geometry):
    """
     定义函数：将几何对象转换为嵌套数组
    @param geometry:
    @return:
    """
    coords_array = []
    if isinstance(geometry, Polygon):  # 如果是单个 Polygon
        coords = geometry.exterior.coords  # 获取外环坐标
        coords_array = [[y, x] for x, y in coords]
    elif isinstance(geometry, MultiPolygon):  # 如果是 MultiPolygon
        coords_array = [
            [[y, x] for x, y in polygon.exterior.coords]  # 每个子多边形的外环坐标
            for polygon in geometry.geoms
        ]
    return coords_array


def polygon_task_add(request):
    """
    上传文件接口
    @param request:
    @return:
    """
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
                    unzip_file(save_path, os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name.split('.')[0]))
                    while True:
                        file_id = f"62{random.randint(10000000000000, 99999999999999)}"
                        is_exist = BufferFile.objects.filter(file_id=file_id)
                        if not is_exist:
                            break
                    BufferFile.objects.create(
                        file_id=file_id,
                        file_name=myFile.name,
                        file_extension='.kml',
                        file_path=save_path,
                        owner=current_user.username,
                        file_type='kml',
                        file_size=os.path.getsize(save_path)
                    )
                    # 1. 读取 Shapefile 文件

                    gdf = gpd.read_file(save_path)
                    # 2. 过滤几何类型为面的数据
                    polygons_gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
                    # 4. 转换几何对象为坐标串
                    polygons_gdf['coords'] = polygons_gdf['geometry'].apply(geometry_to_coords_array)
                    # 3. 提取指定字段
                    # 检查是否包含所需字段
                    required_fields = ['BSM', 'DLMC', 'QSDWMC', 'coords']
                    # 提取指定字段的数据
                    filtered_data = polygons_gdf[
                        ['geometry'] + [field for field in required_fields if field in polygons_gdf.columns]]

                    # 4. 输出结果
                    # 转换为字典列表格式
                    data_list = []
                    verify_task_obj = PolygonTask.objects.create(
                        task_id='',
                        file_id=file_id,
                        status=0,
                        task_type=0,
                        street=county
                    )
                    need_verify = 0
                    task_id = ''
                    for idx, row in filtered_data.iterrows():
                        data_list.append({
                            "geometry": row['geometry'].wkt,  # 将几何对象转换为 WKT 格式
                            "BSM": row.get('BSM', None),
                            "DLMC": row.get('DLMC', None),
                            "QSDWMC": row.get('QSDWMC', None)
                        })
                        PolygonData.objects.create(
                            bsm=row.get('BSM', None),
                            name=row.get('DLMC', None),
                            unit_name=row.get('QSDWMC', None),
                            status=0,
                            polygon_task=verify_task_obj,
                            polygon=row['coords']
                        )
                        task_id = row.get('BSM', None)[0:9]
                        need_verify += 1
                    verify_task_obj.task_id = str(task_id) + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    verify_task_obj.need_verify = need_verify
                    verify_task_obj.save()

            return JsonResponse({'code': 0, 'msg': '上传成功'})
        except Exception as e:
            logger.error(f'上传失败: {str(e)}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': '上传失败', 'error': str(e)})


def frame_area_upload(request):
    """
    上传文件接口
    @param request:
    @return:
    """
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
                    unzip_file(save_path, os.path.join(settings.BASE_DIR, 'static', 'temp', myFile.name.split('.')[0]))
                    while True:
                        file_id = f"62{random.randint(10000000000000, 99999999999999)}"
                        is_exist = BufferFile.objects.filter(file_id=file_id)
                        if not is_exist:
                            break
                    BufferFile.objects.create(
                        file_id=file_id,
                        file_name=myFile.name,
                        file_extension='.kml',
                        file_path=save_path,
                        owner=current_user.username,
                        file_type='kml',
                        file_size=os.path.getsize(save_path)
                    )
                    # 1. 读取 Shapefile 文件

                    gdf = gpd.read_file(save_path)
                    # 2. 过滤几何类型为面的数据
                    polygons_gdf = gdf[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
                    # 4. 转换几何对象为坐标串
                    polygons_gdf['coords'] = polygons_gdf['geometry'].apply(geometry_to_coords_array)
                    # 3. 提取指定字段
                    # 检查是否包含所需字段
                    required_fields = ['PCMC', 'PWH', 'coords']
                    # 提取指定字段的数据
                    filtered_data = polygons_gdf[
                        ['geometry'] + [field for field in required_fields if field in polygons_gdf.columns]]
                    # 4. 输出结果
                    verify_task_obj = PolygonTask.objects.create(
                        task_id='',
                        file_id=file_id,
                        status=0,
                        task_type=1,
                        street=county
                    )
                    need_verify = 0
                    for idx, row in filtered_data.iterrows():
                        PolygonData.objects.create(
                            bsm='',
                            name=row.get('PCMC', ''),
                            unit_name=row.get('PWH', ''),
                            status=1,
                            polygon_task=verify_task_obj,
                            polygon=row['coords']
                        )
                        need_verify += 1
                    verify_task_obj.task_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                    verify_task_obj.need_verify = need_verify
                    verify_task_obj.save()

            return JsonResponse({'code': 0, 'msg': '上传成功'})
        except Exception as e:
            logger.error(f'上传失败: {str(e)}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': '上传失败', 'error': str(e)})


def polygon_task(request):
    """
    获取图斑任务列表
    @param request:
    @return:
    """
    try:
        current_user = parse_jwt_token(request)
        county = current_user.county
        params = json.loads(request.body)
        task_id = params.get('taskId', '')
        task_type = params.get('taskType')
        limit = params.get('pageSize', 10)
        page = params.get('pageIndex', 1)
        verify_task_list = PolygonTask.objects.filter(task_id__contains=task_id, task_type=task_type,
                                                      street=county).all().order_by('-id')
        if len(verify_task_list) > 0:
            paginator = Paginator(verify_task_list, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        for i in results:
            record = {
                'id': i.id,
                'task_id': i.task_id,
                'status': i.status,
                'street': i.street,
                'total_count': PolygonData.objects.filter(polygon_task_id=i.id).count(),
                'todo_count': PolygonData.objects.filter(polygon_task_id=i.id, status=0).count(),
                'no_occupied': PolygonData.objects.filter(polygon_task_id=i.id, status=1).count(),
                'occupy': PolygonData.objects.filter(polygon_task_id=i.id, status=2).count(),
                'verifier': i.verifier.username if i.verifier else '-',
                'create_person': i.create_person,
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)
        response_data = {'code': 0, 'msg': '', 'data': data, 'total': len(verify_task_list)}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取任务核实表失败{e}')
        return JsonResponse({'code': 1, 'msg': str(e)})


def polygon_task_delete(request):
    """
    图斑核实任务删除
    @param request:
    @return:
    """
    params = json.loads(request.body)
    task_id_list = params.get('task_id_list', [])
    try:
        for i in task_id_list:
            PolygonData.objects.filter(polygon_task_id=i).delete()
            PolygonTask.objects.filter(id=i).delete()
        return JsonResponse({"code": 0, 'msg': '删除成功！'})
    except Exception as e:
        print(e)
        return JsonResponse({"code": 500, 'msg': '删除失败！'})


# Haversine公式计算两点间距离（单位：公里）
def calculate_distance(slat, slon, elat, elon):
    slat, slon, elat, elon = map(radians, [slat, slon, elat, elon])

    dist = 6371.01 * acos(sin(slat) * sin(elat) + cos(slat) * cos(elat) * cos(slon - elon))
    return dist


def polygon_data(request):
    """
    根据任务ID获取图斑数量
    @param request:
    @return:
    """
    params = json.loads(request.body)
    task_id = params.get('taskId', '')
    limit = params.get('limit', 10)
    page = params.get('page', 1)
    polygon_data_list = PolygonData.objects.filter(polygon_task_id=task_id).all().order_by('id')
    current_tasks = PolygonTask.objects.get(id=task_id)
    if current_tasks.status == 0:
        current_tasks.status = 1
        current_tasks.save()
    if len(polygon_data_list) > 0:
        paginator = Paginator(polygon_data_list, limit)
        results = paginator.page(page)
    else:
        results = []

    data = []
    pl = PointLocation.objects.all()
    # 初始化最小距离为无穷大，以及最近点的id为None
    for i in results:
        min_distance = float('inf')
        nearest_point_id = None
        # 遍历所有点，寻找最近的点
        for j in pl:
            point_location = ast.literal_eval(i.polygon)
            distance = calculate_distance(point_location[0][0], point_location[0][1], j.latitude, j.longitude)
            if distance < min_distance:
                min_distance = distance
                nearest_point_id = j.point_id
        record = {
            'polygon_task_id': i.polygon_task_id,
            'id': i.id,
            'bsm': i.bsm,
            'unit_name': i.unit_name,
            'status': i.status,
            'name': i.name,
            'point_location_id': nearest_point_id,
            "verify_conclusion": i.verify_conclusion,
            'polygon': ast.literal_eval(i.polygon),
        }
        data.append(record)
    return JsonResponse({'code': 0, 'msg': '', 'data': data, 'count': len(polygon_data_list)})


def point_panorama_image(request):
    """
    根据点ID获取全景图
    @param request:
    @return:
    """
    params = json.loads(request.body)
    point_id = params.get('point_id')
    panorama_image_list = PanoramaImage.objects.filter(point_id=point_id).all().values('image_id',
                                                                                       'batch_id',
                                                                                       'image_name',
                                                                                       'longitude',
                                                                                       'latitude',
                                                                                       'point_id',
                                                                                       'create_time')
    response_data = {
        'code': 0,
        'data': list(panorama_image_list),
        'msg': "数据获取成功"
    }
    return JsonResponse(response_data)


def polygon_data_status(request):
    """
    修改核查图斑状态-是否占用耕地
    @param request:
    @return:
    """
    current_user = parse_jwt_token(request)
    params = json.loads(request.body)
    polygon_data_id = params.get('polygon_data_id', '')
    status = params.get('status', 0)
    if polygon_data_id:
        polygon_data_obj = PolygonData.objects.get(id=polygon_data_id)
        if polygon_data_obj:
            polygon_data_obj.status = status
            polygon_data_obj.save()
            undo_count = PolygonData.objects.filter(polygon_task_id=polygon_data_obj.polygon_task_id, status=0).count()
            if undo_count == 0:
                PolygonTask.objects.filter(id=polygon_data_obj.polygon_task_id).update(
                    status=2
                )
            else:
                PolygonTask.objects.filter(id=polygon_data_obj.polygon_task_id).update(
                    status=1,
                    verifier=current_user
                )
            return JsonResponse({'code': 0, 'msg': '修改成功'})
    return JsonResponse({'code': 1, 'msg': '修改失败'})


def polygon_data_conclusion(request):
    """
    修改核查图斑状态-核查结论
    @param request:
    @return:
    """
    params = json.loads(request.body)
    polygon_data_id = params.get('polygon_data_id', '')
    verify_conclusion = params.get('verify_conclusion', 0)
    if polygon_data_id:
        polygon_data_obj = PolygonData.objects.get(id=polygon_data_id)
        if polygon_data_obj:
            polygon_data_obj.verify_conclusion = verify_conclusion
            polygon_data_obj.save()
            return JsonResponse({'code': 0, 'msg': '修改成功'})
    return JsonResponse({'code': 1, 'msg': '修改失败'})


def delete_clue_task(request):
    """删除线索核实任务"""
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            verify_task_id = params.get('task_id_list')
            for i in verify_task_id:
                task_id = int(i)
                verifyclue_objs = VerifyClue.objects.filter(task_id=task_id).all()
                for j in verifyclue_objs:
                    j.delete()
                verify_task = VerifyTask.objects.filter(task_id=task_id).first()
                if verify_task:
                    if os.path.exists(verify_task.file_path):
                        os.remove(verify_task.file_path)
                    verify_task.delete()
            return JsonResponse({"code": 0, 'msg': '删除完成'})
        except Exception as e:
            logger.error(f'推送失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, 'msg': '推送失败'})


def calculate_panorama(request):
    """
    根据经纬度计算全景图中yaw，pitch
    @param request:
    @return:
    """
    params = json.loads(request.body.decode('utf-8'))
    polygon_data_id = params.get('polygonDataId')
    image_id = params.get('imageId')
    panorama_image = PanoramaImage.objects.filter(image_id=image_id).first()
    if not panorama_image:
        return JsonResponse({"code": 404, "msg": "全景图片不存在！"})

    polygon_data_obj = PolygonData.objects.filter(id=polygon_data_id).first()
    if not polygon_data_obj:
        return JsonResponse({"code": 500, 'msg': '未找到对应数据'})
    polygon = ast.literal_eval(polygon_data_obj.polygon)
    some_poly = shapely_polygon(polygon)
    x, y = some_poly.centroid.coords.xy
    x, y = x.tolist()[0], y.tolist()[0]
    if panorama_image:
        points = []
        for i in polygon:
            yaw, pitch = compute_yaw_pitch(i[0], i[1], panorama_image.latitude, panorama_image.longitude,
                                           panorama_image.height,
                                           panorama_image.yaw_degree)
            points.append([pitch, yaw])
        yaw, pitch = compute_yaw_pitch(x, y, panorama_image.latitude, panorama_image.longitude, panorama_image.height,
                                       panorama_image.yaw_degree)
        return JsonResponse({"code": 0, 'msg': '计算完成', 'data': {'points': points, 'yaw': yaw, 'pitch': pitch}})
    return JsonResponse({"code": 500, 'msg': '全景图不存在'})


def judge_clue(request):
    """
    判断是否存在未核实的图斑
    @param request:
    @param task_id:
    @return:
    """
    task_id = request.GET.get('taskId')
    unverified = PolygonData.objects.filter(polygon_task_id=task_id, status=0).exists()
    if unverified:
        return JsonResponse({"error": "1存在未核实的图斑，请完成核实后再导出", 'code': 400})
    return JsonResponse({"error": "0", 'code': 0})


def pattern_report_export(request, task_id):
    try:
        task_obj = PolygonTask.objects.filter(task_id=task_id).first()
        if task_obj:
            file_id = task_obj.file_id
            file_obj = BufferFile.objects.filter(file_id=file_id).first()
            if file_obj:
                file_name = file_obj.file_name
                task_id = task_obj.task_id
                # 2. 验证所有图斑是否已核实
                unverified = PolygonData.objects.filter(polygon_task_id=task_id, status=0).exists()
                if unverified:
                    return JsonResponse({"error": "存在未核实的图斑，请完成核实后再导出", 'code': 400})
                file_zip_path = file_obj.file_path
                if file_zip_path.endswith('.zip'):
                    unzip_dir_path = file_zip_path.replace('.zip', '')
                    unzip_file(file_zip_path, unzip_dir_path)
                    shp_list = [os.path.join(unzip_dir_path, i) for i in os.listdir(unzip_dir_path) if
                                i.endswith('.shp')]
                    if len(shp_list) < 1:
                        return JsonResponse({"error": "2未找到shp文件"}, status=404)
                    shp_gdf = gpd.read_file(shp_list[0])
                    # 确保有bsm字段
                    if 'BSM' not in shp_gdf.columns:
                        return JsonResponse({"error": "3SHP文件中缺少bsm字段"}, status=404)
                    patterns = PolygonData.objects.filter(polygon_task_id=task_obj.id).all()
                    for pattern in patterns:
                        mask = shp_gdf['BSM'] == pattern.bsm
                        if mask.any():
                            shp_gdf.loc[mask, 'verify_conclusion'] = pattern.verify_conclusion
                            if pattern.status == 1:
                                shp_gdf.loc[mask, 'is_occupy'] = '未占用'
                            elif pattern.status == 2:
                                shp_gdf.loc[mask, 'is_occupy'] = '占用'
                            else:
                                shp_gdf.loc[mask, 'is_occupy'] = '未知'

                    output_dir = os.path.join(settings.BASE_DIR, 'static/report', file_name.split('.')[0])
                    os.makedirs(output_dir, exist_ok=True)
                    output_shp = os.path.join(output_dir, 'result.shp')
                    shp_gdf.to_file(output_shp, encoding='utf-8')
                    zip_path = output_dir + '.zip'
                    zip_folder(output_dir, zip_path)
                    response = StreamingHttpResponse(file_iterator(zip_path))
                    # 以流的形式下载文件,这样可以实现任意格式的文件下载
                    response['Content-Type'] = 'application/octet-stream'
                    # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
                    response['Content-Disposition'] = 'attachment;filename="{}"'.format(escape_uri_path(file_name))
                    return response
            else:
                return JsonResponse({"error": "未找到文件"}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"error": "服务器错误"}, status=500)
