# _*_ coding: utf-8 _*_
# @Time : 2024/12/18 13:57
# @Author : xxx
# @Version：V 0.1
# @File : experience_views.py
# @desc :
import json
import os
import shutil
import uuid
import cv2
import numpy as np
import requests
from PIL import Image
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.http import JsonResponse
from django.db import transaction
from apps.panorama.models import Project, Task, Alarms,PanoramaImage, Clue, Picture
from apps.panorama.common import get_yaw_degree, get_coordinates, image_to_latlon
from apps.panorama.generate import start_progress
from apps.panorama.uav_monitoring_service_dev import od,main
from apps.system.models import User
from apps.panorama.tasks import task_processing
from utils_tools.common import warning, login_request
from logger import Logger

logger = Logger(logname='experience_views.log', loglevel=5, logger='experience').getlog()


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


def panorama_image_list(request):
    """
    获取全景图列表
    @param request:
    @return:
    """
    try:
        logger.info("获取全景图列表")
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('name')
        page = params.get('page', 1)
        limit = params.get('limit', 4)
        project_id = params.get('project_id', 1)

        response_data = {'code': 0, 'msg': '', 'data': []}
        if keyword is None:
            tasks_obj = Task.objects.filter(project_id=project_id).all().order_by('-id')
        else:
            tasks_obj = Task.objects.filter(name__contains=keyword, project_id=project_id).all().order_by('-id')
        paginator = Paginator(tasks_obj, limit)
        results = paginator.page(page)
        task_list = []
        for task in results:
            task_data = {
                'task_id': task.id,
                'task_name': task.name,
                'task_path': task.path,
                'longitude': task.longitude,
                'latitude': task.latitude,
                'project_id': project_id,
                'count': Alarms.objects.filter(task_id=task.id).count(),
                'task_create_time': task.create_time.strftime('%Y-%m-%d %H:%m:%S'),
            }
            task_list.append(task_data)
        response_data['data'] = task_list
        response_data['count'] = len(tasks_obj)
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取全景图列表失败: {e}')
        return JsonResponse({'code': 500, 'msg': f'{e}', 'data': []})


def project(request):
    """
    获取项目列表
    @param request:
    @return:
    """
    # try:
    if 1 == 1:
        logger.info('获取项目列表')
        params = json.loads(request.body.decode('utf-8'))
        page = params.get('page', 1)
        limit = params.get('limit', 4)
        project_source = params.get('project_source')
        project_name = params.get('project_name')
        response_data = {'code': 0, 'msg': '', 'data': []}
        if project_name is None:
            project_objs = Project.objects.filter(project_source=project_source).all().order_by('-id')
        else:
            project_objs = Project.objects.filter(name__contains=project_name,
                                                  project_source=project_source).all().order_by('-id')
        paginator = Paginator(project_objs, limit)
        results = paginator.page(page)
        data = []
        if results:
            for project_obj in results:
                dict_value = {
                    'id': project_obj.id,
                    'name': project_obj.name,
                    'count': project_obj.count,
                    'remark': project_obj.remark,
                    'project_source': project_obj.project_source,
                    'create_time': project_obj.create_time.strftime('%Y-%m-%d %H:%m:%S'),
                }
                data.append(dict_value)
        response_data['data'] = data
        response_data['count'] = len(project_objs)

        # batch_id = '32011300500220240812'
        # save_panorama_dir = os.path.join(settings.BASE_DIR, 'static', 'layers',batch_id)  # 保存三个图层的文件夹
        # os.makedirs(save_panorama_dir, exist_ok=True)
        # folder_path = r'E:\supermap_gitlab\gtus\static\temp\龙潭全景'
        # filelist = os.listdir(folder_path)
        # for i in filelist:
        #     path = os.path.join(folder_path,i)
        #     print(path)
        #     p = PanoramaImage.objects.filter(batch_id=batch_id,image_name=i).first()
        #     output_path = os.path.join(save_panorama_dir, p.image_id)
        #     print(output_path)
        #     os.makedirs(output_path, exist_ok=True)
        #     start_progress(path, output_path)
        return JsonResponse(response_data)
    # except Exception as e:
    #     logger.error(f'获取项目列表失败: {e}')
    #     return JsonResponse({'code': 500, 'msg': f'{e}', 'data': []})


def panorama(request):
    """
    全景融合
    """

    if request.method == 'POST':
        if request.FILES:
            folder_path = request.POST.get('folderPath')
            project_name = request.POST.get('project_name')
            target_directory = os.path.join(settings.BASE_DIR, 'static', 'temp', folder_path)
            os.makedirs(target_directory, exist_ok=True)
            for i, myFile in enumerate(request.FILES.values()):
                with open(os.path.join(target_directory, myFile.name), 'wb+') as destination:
                    for chunk in myFile.chunks():
                        destination.write(chunk)
            save_panorama_dir = os.path.join(settings.BASE_DIR, 'static', 'layers')  # 保存三个图层的文件夹
            os.makedirs(save_panorama_dir, exist_ok=True)
            file_list = os.listdir(target_directory)
            project_obj = Project.objects.create(
                name=project_name,
                count=len(file_list),
                project_source='全景融合'
            )

            for i in file_list:
                logger.info(f'开始处理图片{i},{project_obj.id}')
                task_path = str(uuid.uuid1()).replace('-', '')
                path = os.path.join(target_directory, i)
                print(path)
                output_path = os.path.join(save_panorama_dir, task_path)

                os.makedirs(output_path,exist_ok=True)
                img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
                lat, lon, gps_height = get_coordinates(path)
                yaw_degree,real_height = get_yaw_degree(path)
                with Image.open(path) as cimg:
                    image_width, image_height = cimg.size
                res_image, res = od.panorama_img_detection_v2(img, settings.OD_URL)
                task, created = Task.objects.get_or_create(
                    name=i,
                    owner_id=request.session['user_id'],
                    longitude=lon,
                    latitude=lat,
                    image_height=image_height,
                    image_width=image_width,
                    height=real_height,
                    yaw_degree=yaw_degree,
                    project=project_obj,
                    task_type='全景检测',
                    defaults={
                        'path': task_path,
                        'note': '',
                    }
                )
                for j in res:
                    position = j['position']
                    center_x = (position[0] + position[2]) // 2
                    center_y = (position[1] + position[3]) // 2
                    # 计算 yaw 和 pitch
                    yaw = (center_x / image_width) * 360 - 180
                    pitch = 90 - (center_y / image_height) * 180
                    print(lat, lon, real_height, yaw, pitch, yaw_degree)
                    alarm_lat, alarm_lon = image_to_latlon(lat, lon, real_height, yaw, pitch, yaw_degree)
                    Alarms.objects.create(
                        label=j['className'],
                        alarms=j['position'],
                        task=task,
                        longitude=alarm_lon,
                        latitude=alarm_lat,
                        center_x=center_x,
                        center_y=center_y
                    )
                start_progress(path, output_path)
                task.panoramic_image = target_directory
                task.save()
                os.remove(path)
            return JsonResponse({'msg': '全景图识别成功！', 'code': 0, 'data': {}})
    return JsonResponse({'msg': '无效的请求类型', 'code': 400})



def project_delete(request):
    """
    删除项目
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            project_id = params.get('project_id')
            project_obj = Project.objects.filter(id=project_id).first()
            if project_obj:
                task_list = Task.objects.filter(project_id=project_id).all()
                for j in task_list:
                    task_path = os.path.join(settings.BASE_DIR, 'static/layers', str(j.path))
                    if os.path.exists(task_path):
                        shutil.rmtree(task_path)
                    j.delete()
                project_obj.delete()
            return JsonResponse({'code': 0, 'msg': '删除成功'})
        except Exception as e:
            logger.error(f"删除项目失败{e}")
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': "{}".format(e)})


def experience_data(request):
    """
    获取体验中心数据
    @param request:
    @return:
    """
    try:
        logger.info("接收获取体验中心数据请求")
        is_datas = [{
            'name': '水系',
            'icon': 'icon-geoai-river',
            'datasets_name': 'WATER@JJFA'
        }, {
            'name': '林地',
            'icon': 'icon-geoai-woodland',
            'datasets_name': 'LD@JJFA'
        }, {
            'name': '道路',
            'icon': 'icon-geoai-road',
            'datasets_name': 'ROAD@JJFA'
        }, {
            'name': '耕地',
            'icon': 'icon-geoai-crops',
            'datasets_name': 'GD@JJFA'
        }, {
            'name': '建设用地',
            'icon': 'icon-geoai-construction',
            'datasets_name': 'JSYD@JJFA'
        }]

        dict_data = {
            'name': '泰州',
            'is_map_url': 'http://192.168.60.51:8090/iserver/services/map-ugcv5-HQ2018HQ2018/rest/maps/HQ2018%40HQ2018',
            'prev_url': 'http://192.168.60.51:8090/iserver/services/map-ugcv5-HQ2021HQ2021/rest/maps/HQ2021%40HQ2021',
            'next_url': 'http://192.168.60.51:8090/iserver/services/map-ugcv5-HQ2022HQ2022/rest/maps/HQ2022%40HQ2022',
            'is_center': [32.275163, 120.187654],
            'cd_center': [32.275163, 120.187654],
            'cd_datasets_name': 'BHJC@JJFA',
            'spatial_analysis_url': 'http://192.168.60.51:8090/iserver/services/spatialAnalysis-JJFA/restjsr/spatialanalyst',
            'models': is_datas,
            'code': 0
        }
        response_data = {
            "code": 0,
            "data": dict_data,
            "msg": '获取数据成功'
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"获取体验中心数据{e}")


def get_shape(request):
    """
    获取图片宽和高
    @param request:
    @return:
    """
    try:
        logger.error("接收获取图片宽和高请求")
        task_id = request.GET.get('task_id')
        task_obj = Task.objects.get(id=task_id)
        panorama_path = os.path.join(settings.BASE_DIR, 'static/layers', task_obj.path, 'origin_panorama.png')
        if os.path.exists(panorama_path):
            imgs = cv2.imread(panorama_path)
            height, width, _ = imgs.shape
        else:
            width, height = 14400, 7200
        response_data = {'code': 0, 'msg': '', 'data': {'width': width, 'height': height}}
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"获取图片宽和高失败{e}")
        response_data = {'code': 500, 'msg': f"获取图片宽和高失败{e}", 'data': {}}


def get_alarms_list(request):
    """
    获取目标检测结果列表
    @param request:
    @return:
    """
    try:
        logger.error("接收获取目标检测结果列表请求")
        task_id = request.GET.get('task_id')
        results = Alarms.objects.filter(task_id=task_id).all()
        data = []
        response_data = {'code': 0, 'msg': '', 'data': []}
        for result in results:
            dict_value = {
                'id': result.id,
                'label': result.label,
                'center_x': result.center_x,
                'center_y': result.center_y,
                'latitude': result.latitude,
                'longitude': result.longitude,
                'is_delete': result.is_delete,
                'inspector': result.inspector,
                'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),

            }
            data.append(dict_value)
        response_data['data'] = data
        response_data['count'] = len(results)
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"获取目标检测结果列表失败{e}")
        return JsonResponse({'code': '500', 'msg': "{}".format(e), 'data': []})


def label_data(request):
    """
    保存目标信息
    @param request:
    @return:
    """
    logger.info("接受保存目标信息请求")
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            pixel_x = int(params.get('pixel_x', 1))
            pixel_y = int(params.get('pixel_y', 1))
            class_name = params.get('class')
            image_id = params.get('task_id')
            yaw = params.get('yaw')
            pitch = params.get('pitch')
            panorama_obj = Task.objects.get(id=image_id)
            # lat, lon = image_to_latlon(panorama_obj.latitude, panorama_obj.longitude, panorama_obj.height, yaw, pitch,
            #                            panorama_obj.yaw_degree)
            lat ,lon = 32.2293,119.033
            #crop_save_folder = os.path.join(settings.BASE_DIR, 'static', 'resultImg', panorama_obj.batch_id, image_id)
            # 绘制图
            #origin_img = Image.open(os.path.join(crop_save_folder, panorama_obj.image_name))
            # 裁剪图片
            #cropped_img = origin_img.crop((pixel_x - 400, pixel_y - 400, pixel_x + 400, pixel_y + 400))
            clue_obj = Alarms.objects.create(
                center_x=pixel_x,
                center_y=pixel_y,
                label=class_name,

                latitude=lat,
                longitude=lon,
                task_id=image_id,
            )
            #output_path = os.path.join(crop_save_folder, str(clue_obj.clue_id) + '.jpg')
            # 保存裁剪后的图片
            # 打开前景图片
            #foreground = Image.open(os.path.join(settings.BASE_DIR, 'static/images/red.png'))
            #w, h = cropped_img.size
            # 粘贴前景图片到背景图片上
            #cropped_img.paste(foreground, (int(w / 2), int(h / 2)), foreground)
            #cropped_img.save(output_path)
            #clue_obj.file_path = output_path
            clue_obj.save()
            response_data = {'code': 0, 'msg': '保存成功！'}
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'保存目标信息失败{e}')
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': str(e)})


def files1(request):
    """
    目标检测功能
    """
    if request.method == 'POST':
        if request.FILES:
            folder_path = request.POST.get('folderPath')
            task_name = request.POST.get('filePath','测试')
            task_type = request.POST.get('task_type','')
            user = User.objects.first()
            task, created = Task.objects.get_or_create(
                name=task_name,
                owner=user,
                task_type='图片检测',
                defaults={
                    'path': '',
                    'note': 'Task created during file upload',
                }
            )
            target_directory = os.path.join(settings.BASE_DIR, 'static', 'upload')
            os.makedirs(target_directory, exist_ok=True)
            save_path = os.path.join(settings.BASE_DIR, 'static', 'resultImg')
            os.makedirs(save_path, exist_ok=True)
            myFile = request.FILES.get('files')
            if myFile:
                with open(os.path.join(target_directory, myFile.name), 'wb+') as destination:
                    for chunk in myFile.chunks():
                        destination.write(chunk)
            url = settings.OD_URL

            path = os.path.join(target_directory, myFile.name)
            data = {
                "filename": myFile.name,
                "camera_id": "32040123082409010301010000323251",
                "file_path": path}
            headers = {'Connection': 'close'}
            # 返回的结果信息
            images_info = {"image": open(path, 'rb')}
            res = requests.post(url=url, headers=headers, data=data,files=images_info).json()
            if len(res['alarms']) > 0:
                result, labels = res['alarms'], res['labels']
                #final_list = main.single_img_location(path, result)
                if len(result) > 0:
                    Picture.objects.create(
                        name=myFile.name,
                        file_path='static/uploadImg/' + myFile.name,
                        task=task,
                        labels=labels,
                        alarms=result,
                        result_path='static/resultImg/'+myFile.name
                    )
            return JsonResponse({'msg': '上传成功！', 'statusCode': '200'})
    return JsonResponse({'msg': 'Invalid request method', 'statusCode': '200'})


def get_alarms_by_id(request):
    try:
        logger.info("接收获取线索点请求")
        alarm_id = request.GET.get('id')
        alarm_obj = Alarms.objects.get(id=alarm_id)
        response_data = {
            'code': 0,
            'msg': '',
            'data': {
                'id': alarm_obj.id,
                'task_id': alarm_obj.task_id,
                'center_x': alarm_obj.center_x,
                'center_y': alarm_obj.center_y,
                'longitude': alarm_obj.longitude,
                'latitude': alarm_obj.latitude,
                'label': alarm_obj.label
            }
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error("获取线索点失败：" + str(e))
        return JsonResponse({'code': 500, 'msg': str(e)})


def video_task(request):
    """
    批量处理视频目标检测任务
    @param task_id:
    @return:
    """
    print("========================开始处理视频目标检测任务========================")
    folder_path = request.POST.get('folderPath')
    view_angle = request.POST.get('view_angle')
    file_type = request.POST.get('file_type')
    frame_interval = 10
    target_directory = os.path.join(settings.BASE_DIR, 'static', 'upload', folder_path)
    os.makedirs(target_directory, exist_ok=True)
    for i, myFile in enumerate(request.FILES.values()):
        with open(os.path.join(target_directory, myFile.name), 'wb+') as destination:
            for chunk in myFile.chunks():
                destination.write(chunk)
    video_list = os.listdir(target_directory)
    save_panorama_dir = os.path.join(settings.BASE_DIR, 'static', 'layers')  # 保存三个图层的文件夹
    os.makedirs(save_panorama_dir, exist_ok=True)

    for i in video_list:
        video_path = os.path.join(target_directory, i)
        task = Task.objects.create(
            name=i,
            owner_id=request.session['user_id'],
            longitude=119.92,
            latitude=32.57,
            path=video_path,
            task_type='视频检测',
            note='',
        )
        task_id = str(uuid.uuid1())
        task_processing.apply_async(args=[task.id], task_id=str(task.id))
    return JsonResponse({'code': 0, 'msg': '开始检测成功！'})


def alarms_delete(request):
    """
    根据ID删除目标
    @param request:
    @return:
    """
    logger.info("接收根据ID删除目标请求")
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode("utf-8"))
            alarms_id = params.get('id')
            alarms_obj = Alarms.objects.filter(id=alarms_id).first()
            if alarms_obj:
                alarms_obj.delete()
                return JsonResponse({'code': 0, 'msg': '删除成功'})
            else:
                return JsonResponse({'code': 404, 'msg': '删除失败，标签不存在'})
        except Exception as e:
            logger.error(f"删除失败，服务器错误{e}")
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': f'删除失败，服务器错误{e}'})


def task_data(request):
    """
    获取全景图列表
    @param request:
    @return:
    """
    logger.info("接收获取全景图列表请求")
    try:
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('keyword')
        page = params.get('page', 1)
        limit = params.get('limit', 4)
        project_id = params.get('project_id')
        task_type = params.get('task_type', '全景检测')
        response_data = {'code': 0, 'msg': '', 'data': []}
        if keyword is None:
            tasks_obj = Task.objects.filter(task_type=task_type, project_id=project_id).all().order_by('-id')
        else:
            tasks_obj = Task.objects.filter(task_type=task_type, name__contains=keyword,
                                            project_id=project_id).all().order_by('-id')
        paginator = Paginator(tasks_obj, limit)
        try:
            # 尝试获取当前页的数据
            results = paginator.page(page)
        except EmptyPage:
            # 如果当前页为空，则获取前一页的数据
            if page > 1:
                page = page - 1
                results = paginator.page(page)
            else:
                # 如果已经是第一页，返回空列表
                results = []
        task_list = []
        for task in results:
            pictures = Picture.objects.filter(task=task).all()
            record = {
                'task_id': task.id,
                'task_name': task.name,
                'task_path': task.path,
                'longitude': task.longitude,
                'latitude': task.latitude,
                'project_id': task.project_id,
                'image_width': task.image_width,
                'image_height': task.image_height,
                'height': task.height,
                "yaw_degree": float(task.yaw_degree) if task.yaw_degree else 0,
                'count': Alarms.objects.filter(task_id=task.id).count(),
                'task_create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'pictures': [{
                    'name': picture.name,
                    'file_path': picture.file_path,
                    'result_path': picture.result_path,
                    'alarms': eval(picture.alarms),
                    'labels': picture.labels,
                    'create_time': picture.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                } for picture in pictures]
            }
            task_list.append(record)
        response_data['data'] = task_list
        response_data['count'] = len(tasks_obj)
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"查询任务失败，错误信息：{e}")
        return JsonResponse({'code': 500, 'msg': f'{e}', 'data': []})


def panorama_task_delete(request):
    """
    删除全景图任务及其关联的图片
    """
    logger.info("接收删除全景图任务及其关联的图片请求")
    temp_files_list = []
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            task_id = params.get('task_id')
            # 查询任务对象
            task = Task.objects.filter(id=task_id).first()
            if task:
                upload_path = os.path.join(settings.BASE_DIR, 'static', 'upload', task.path)
                if os.path.exists(upload_path):
                    # 为了便于任务失败回退，需要删除的东西，需要先行备份
                    copy_path = os.path.join(os.path.dirname(upload_path), 'temp_{}'.format(str(task.path)))
                    shutil.rmtree(upload_path)
                task.delete()
                delete_copy_path(temp_files_list)
                return JsonResponse({'msg': "任务删除成功", 'code': 0, 'data': {}})
            else:
                logger.error("任务删除失败，找不到ID为{}的任务".format(task_id))
                return JsonResponse({'msg': "任务删除失败，找不到ID为{}的任务".format(task_id), 'code': 401, 'data': {}})
        except Task.DoesNotExist:
            logger.error("任务删除失败，找不到任务，Task.DoesNotExist")
            restore_files_to_original_path(temp_files_list)
            transaction.set_rollback(True)
            return JsonResponse({'msg': "任务删除失败", 'code': 401, 'data': {}})


@login_request
def task_lists(request):
    """
    运维中心任务列表
    @param request:
    @return:
    """
    logger.info("接收运维中心任务列表请求")
    try:
        params = json.loads(request.body.decode('utf-8'))
        task_type = params.get('task_type')
        keyword = params.get('filter')  # 条件查询
        page = params.get("page", 1)  # 分页
        limit = params.get("limit", 8)
        order_by = params.get('order_by', '')  # 排序字段
        response_data = {}
        data = []
        latest_task_id =None
        latest_task_obj = Task.objects.all().order_by('-create_time')
        if latest_task_obj:
            latest_task_id = latest_task_obj[0].id
        # 如果没有搜索，返回全部数据，按照创建时间排序
        if task_type == '图片检测':
            if keyword is None:
                task_obj = Task.objects.all().order_by('-create_time')
            else:
                keyword = eval(keyword)
                name = keyword.get("name")
                create_time = keyword.get("create_time")
                if "name" in keyword:
                    keyword.pop('name')
                if "create_time" in keyword:
                    keyword.pop('create_time')
                if "county" in keyword:
                    keyword.pop("county")
                if len(name) == 0 and len(create_time) == 0:
                    task_obj = Task.objects.filter(**keyword).all()
                elif len(name) != 0 and len(create_time) == 0:
                    task_obj = Task.objects.filter(**keyword).filter(name__contains=name).all()
                elif len(name) == 0 and len(create_time) != 0:
                    task_obj = Task.objects.filter(**keyword).filter(
                        create_time__year=create_time.split('-')[0]). \
                        filter(create_time__month=create_time.split('-')[1]) \
                        .filter(create_time__day=create_time.split('-')[2]).all()
                else:
                    task_obj = Task.objects.filter(**keyword).filter(
                        create_time__year=create_time.split('-')[0]). \
                        filter(create_time__month=create_time.split('-')[1]) \
                        .filter(create_time__day=create_time.split('-')[2]).filter(name__contains=name).all()
        else:
            if keyword is None:
                task_obj = Task.objects.all().order_by('-create_time')
            else:
                keyword = eval(keyword)
                name = keyword.get("name")
                create_time = keyword.get("create_time")
                if "name" in keyword:
                    keyword.pop('name')
                if "create_time" in keyword:
                    keyword.pop('create_time')
                if "county" in keyword:
                    keyword.pop("county")
                if len(name) == 0 and len(create_time) == 0:
                    task_obj = Task.objects.filter(**keyword).all()
                elif len(name) != 0 and len(create_time) == 0:
                    task_obj = Task.objects.filter(**keyword).filter(name__contains=name).all()
                elif len(name) == 0 and len(create_time) != 0:
                    task_obj = Task.objects.filter(**keyword).filter(
                        create_time__year=create_time.split('-')[0]). \
                        filter(create_time__month=create_time.split('-')[1]) \
                        .filter(create_time__day=create_time.split('-')[2]).all()
                else:
                    task_obj = Task.objects.filter(**keyword).filter(
                        create_time__year=create_time.split('-')[0]). \
                        filter(create_time__month=create_time.split('-')[1]) \
                        .filter(create_time__day=create_time.split('-')[2]).filter(name__contains=name).all()
        # 按照时间排序
        if order_by == 'name':
            task_obj = task_obj.order_by('-name')
        else:  # 按照名称排序
            task_obj = task_obj.order_by('-create_time')

        task_id_list = []
        for item in task_obj:
            task_id_list.append(item.id)
        paginator = Paginator(task_obj, limit)
        results = paginator.page(page)
        task_annotate_list = []
        if results:
            for task in results:
                record = {
                    'task_id': task.id,
                    'task_name': task.name,
                    'task_path': task.path,
                    'longitude': task.longitude,
                    'owner': task.owner.username,
                    'latitude': task.latitude,
                    'task_create_time': task.create_time.strftime('%Y-%m-%d'),
                }
                data.append(record)
            response_data = {
                'count': len(task_obj),
                'data': data,
                'task_annotate_list': task_annotate_list,
                'latest_task_id': latest_task_id,
                'code': 0
            }

            return JsonResponse(response_data)
        else:
            logger.warning('没有任务数据！')
            return warning('没有任务数据！')
    except Exception as e:
        logger.error(f'获取任务数据失败:{e}')
        return warning('获取任务数据失败！')


@login_request
def od_image_list(request):
    """
    目标检测任务获取接口
    @param request:
    @return:
    """
    logger.info('接收目标检测任务获取请求')
    try:
        params = json.loads(request.body)
        keyword = params.get('name')
        page = params.get("page", 1)  # 分页
        limit = params.get("limit", 4)
        response_data = {'code': 0, 'msg': '', 'data': []}
        if keyword is None:
            tasks_obj = Task.objects.filter.all().order_by('-id')
        else:
            tasks_obj = Task.objects.filter(name__contains=keyword).all().order_by('-id')
        paginator = Paginator(tasks_obj, limit)
        results = paginator.page(page)
        if results:
            for task in results:
                pictures = Picture.objects.filter(task=task).all()
                record = {
                    'task_id': task.id,
                    'task_name': task.name,
                    'task_path': task.path,
                    'longitude': task.longitude,
                    'latitude': task.latitude,
                    'task_create_time': task.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'pictures': [{
                        'name': picture.name,
                        'file_path': picture.file_path,
                        'result_path': picture.result_path,
                        'alarms': eval(picture.alarms),
                        'labels': picture.labels,
                        'create_time': picture.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    } for picture in pictures]
                }
                response_data['data'].append(record)
        response_data['count'] = len(tasks_obj)
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"目标检测任务获取失败：{e}")
        return JsonResponse({'code': 500, 'msg': f'{e}', 'data': []})
