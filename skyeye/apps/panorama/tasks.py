# _*_ coding: utf-8 _*_
# @Time : 2024/8/13 18:59 
# @Author : xxx 
# @Version：V 0.1
# @File : tasks.py
# @desc :
import datetime
import json
import math
import os, sys
import time

import cv2
import numpy as np
import django
from PIL import Image
from shapely.geometry import Polygon, Point, box
import configparser
from multiprocessing import Process

from apps.panorama.spatial_analysis_geoserver import GeoServerPointInPolygonChecker

work_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, work_dir)
from gtus.celery_config import celery_app
from celery import Task as CeleryTask

django.setup()
from django.conf import settings
from utils_tools.common import read_json
from logger import Logger
from apps.panorama.uav_monitoring_service_dev import od
from apps.panorama.common import image_to_latlon, find_village_by_point
from apps.panorama.generate import start_progress
from apps.panorama.change_detection.registration_panorama_task import panorama_image_registration_by_cube_image
from apps.panorama.models import PanoramaImage, Clue, FrameArea, Resource, PointLocation, BatchResource
from apps.panorama.generate_python import start_cut_image

logger = Logger(logname='task.log', loglevel=5, logger='task').getlog()


class CallbackTask(CeleryTask):
    abstract = True

    def __init__(self):
        self.config = configparser.ConfigParser()
        # 假设config.ini位于脚本同级目录下
        self.config.read(os.path.join(work_dir, 'config.ini'), encoding='utf-8')

    def on_success(self, retval, image_id, args, kwargs):
        logger.info("ID为%s的任务已经完成!!!" % image_id)
        # 获取检测结果中的 alarms
        alarms_data = retval.get('alarms', [])
        point_id = retval.get('point_id', '')
        tile_output_path = retval.get('tile_output_path', '')
        image_path = retval.get('image_path', '')
        json_path = os.path.join(tile_output_path, 'config.json')
        # 如果配置文件存在，获取参数信息
        if os.path.exists(json_path):
            last_three_items = read_json(json_path)
            tileResolution = last_three_items['tileResolution']
            maxLevel = last_three_items['maxLevel']
            cubeResolution = last_three_items['cubeResolution']
        else:
            if image_path:
                origWidth, origHeight = Image.open(image_path).size
                haov = -1
                if haov == -1:
                    haov = 360.0
                cubeResolution = 0
                if cubeResolution != 0:
                    cubeResolution = 0
                else:
                    cubeResolution = 8 * math.ceil((360 / haov) * origWidth / math.pi / 8)
                tileResolution = min(512, cubeResolution)
                maxLevel = int(math.ceil(math.log(float(cubeResolution) / tileResolution, 2))) + 1
                if int(cubeResolution / 2 ** (maxLevel - 2)) == tileResolution:
                    maxLevel -= 1  # Handle edge case
            else:
                tileResolution = 512
                maxLevel = 5
                cubeResolution = 4576
        logger.info(f"tileResolution: {tileResolution}, maxLevel: {maxLevel}, cubeResolution: {cubeResolution}")
        logger.info(f"image_id为{image_id}的检测结果: {alarms_data}，对应的全景点是{point_id}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # 获取异常对象
        exception_message = str(exc) if exc else "Unknown error"

        # 记录详细错误日志
        logger.error(
            f"❌❌❌   image_id为【{task_id}】的全景图检测失败！错误: {exception_message}"
        )


@celery_app.task(base=CallbackTask)
def panorama_detection(image_id, panorama_image_obj):
    """
    全景图片检测处理
    """
    start_time = time.time()
    config = configparser.ConfigParser()
    # 假设config.ini位于脚本同级目录下
    config.read(os.path.join(work_dir, 'config.ini'), encoding='utf-8')
    common_config = config['common']
    object_detection_config = config['object_detection']
    file_path = panorama_image_obj['image_path']
    file_name = os.path.basename(file_path)
    is_change_detection = panorama_image_obj['is_change_detection']
    point_id = panorama_image_obj['point_id']
    logger.info(f"图片ID：{panorama_image_obj['image_id']}开始全景检测，图片路径为{file_path}")
    img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    res_image, res = od.panorama_img_detection_v2(img, object_detection_config['od_url'],
                                                  panorama_image_obj['batch_id'], image_id)
    current_year_month = datetime.datetime.now().strftime("%Y%m")
    tile_output_path = os.path.join(settings.BASE_DIR, 'static', 'layers',
                                    panorama_image_obj['batch_id'],
                                    image_id)  # 保存三个图层的文件夹
    os.makedirs(tile_output_path, exist_ok=True)
    crop_save_folder = os.path.join(settings.BASE_DIR, 'static', 'resultImg',
                                    panorama_image_obj['batch_id'], image_id)
    os.makedirs(crop_save_folder, exist_ok=True)
    # 绘制图
    # draw_picture(file_path, res, os.path.join(crop_save_folder, file_name))
    # origin_img = Image.open(os.path.join(crop_save_folder, file_name))
    count = 1
    alarms = []
    all_resource = Resource.objects.filter(
        id__in=BatchResource.objects.filter(
            batch_id=panorama_image_obj['batch_id'],
        ).values_list('resource_id', flat=True)
    ).values()
    # 不检测区域
    all_area = FrameArea.objects.all().values()
    for j in res:
        position = j['position']
        center_x = (position[0] + position[2]) // 2
        center_y = (position[1] + position[3]) // 2
        bottom_center_x = (position[0] + position[2]) // 2
        bottom_center_y = position[3]
        left, top, right, bottom = position[0], position[1], position[2], position[3]
        # 计算 yaw 和 pitch
        yaw = (bottom_center_x / panorama_image_obj['image_width']) * 360 - 180
        pitch = 90 - (bottom_center_y / panorama_image_obj['image_height']) * 180

        alarm_lat, alarm_lon = image_to_latlon(panorama_image_obj['latitude'], panorama_image_obj['longitude'],
                                               panorama_image_obj['height'], yaw, pitch,
                                               panorama_image_obj['yaw_degree'])
        in_not_detection_area = 0
        for m in all_area:
            p = json.loads(m['pixel'])
            # 如果polygon_task_id不为空，则使用经纬度polygon比较
            if m['polygon_task_id']:
                reverse_polygon = [[point[1], point[0]] for point in p]

                polygon = Polygon(reverse_polygon)
                # 测试点（经度, 纬度）
                test_point = Point(alarm_lon, alarm_lat)  # 示例点，修改为实际坐标
                # 判断点是否在多边形内
                if polygon.contains(test_point):
                    in_not_detection_area = 1
                    break
            else:
                polygon = Polygon(p)
                rectangle = box(left, top, right, bottom)
                if polygon.intersects(rectangle):
                    in_not_detection_area = 1
                    break
        # 将像素坐标转换为弧度
        pitch_rad = math.pi / 2 - (center_y / panorama_image_obj['image_height']) * math.pi
        # 将弧度转换为角度
        pitch1 = pitch_rad * 180 / math.pi
        if pitch1 < -9.0902:
            address = find_village_by_point(settings.SHP_FILE_PATH, alarm_lat, alarm_lon)
            url = f"http://{common_config['HOST']}:{common_config['PORT']}{j['file_path']}"

            clue_obj = {
                'id': count,
                'clue_name': j['className'],
                'panorama_image_id': image_id,
                'longitude': round(alarm_lon, 4),
                'latitude': round(alarm_lat, 4),
                'center_x': int(center_x),
                'center_y': int(center_y),
                'position': position.astype(int).tolist(),
                'address': address,
                'score': float(j['score']),
                'file_path': url,
                'clue_source': 1,  # 1为自动检测
                'in_not_detection_area': in_not_detection_area,
                'batch_id': panorama_image_obj['batch_id'],
                'new_clue': 0,
                'szdl': []
            }
            count += 1
            alarms.append(clue_obj)
    logger.info(f"当前任务的叠加业务数据数量为{len(all_resource)}")
    # 如果存在业务数据，则进行叠加
    if len(all_resource) > 0 and len(alarms) > 0:

        # checker = IServerPointInPolygonChecker()
        # # 批量检查所有点
        # result = checker.check_points_against_services(all_resource, alarms)
        checker = GeoServerPointInPolygonChecker()
        result = checker.check_points_against_services(all_resource, alarms)
    else:
        result = alarms
    cut_image_way = common_config['cut_image_way']
    if cut_image_way == "1":
        # 创建子进程
        p = Process(
            target=start_progress,
            args=(file_path, tile_output_path),
            name=f"tile-cutter-way-1"  # 给进程命名，便于调试
        )
        # 启动子进程
        p.start()
        print(f"子进程启动 (PID: {p.pid})，切割方式: {cut_image_way}")
    elif cut_image_way == "2":
        # 创建子进程
        p = Process(
            target=start_cut_image,
            args=(file_path, tile_output_path, panorama_image_obj['yaw_degree']),
            name=f"tile-cutter-way-2"  # 给进程命名，便于调试
        )
        # 启动子进程
        p.start()
        print(f"子进程启动 (PID: {p.pid})，切割方式: {cut_image_way}")
    else:
        pass
    # desc = call_vl_agent_and_save_desc(file_path)
    if len(res) > 15:
        desc = '当前区域已大面积开始施工'
    elif 15 > len(res) > 5:
        desc = '当前区域工程已小面积开始施工'
    else:
        desc = '当前区域尚未开始施工'

    # 先找当前全景图对应的全景点的多期全景
    if is_change_detection == "1":
        pre_obj = PanoramaImage.objects.filter(point_id=panorama_image_obj['point_id']).exclude(
            image_id=panorama_image_obj['image_id']).order_by('-create_time').first()
        if pre_obj:
            # change_results = start_change_detection(pre_obj['pk_id'], result,
            #                                         os.path.join(settings.BASE_DIR, 'static', 'temp',
            #                                                      pre_obj['image_name']),
            #                                         panorama_image_obj)
            bbox = start_detection(pre_obj.image_path, file_path, panorama_image_obj)

        else:
            logger.warning(f'全景图{image_id}没有找到前景数据')
            change_results = result
    else:
        change_results = result
    end_time = time.time()
    logger.info(f'全景图{panorama_image_obj["image_name"]}检测完成，耗时{end_time - start_time}秒')
    for i in change_results:
        Clue.objects.create(
            clue_name=i['clue_name'],
            panorama_image_id=image_id,
            longitude=i['longitude'],
            latitude=i['latitude'],
            center_x=i['center_x'],
            center_y=i['center_y'],
            position=i['position'],
            score=i['score'],
            clue_source=i['clue_source'],
            address=i['address'],
            file_path=i['file_path'],
            batch_id=panorama_image_obj['batch_id'],
            in_not_detection=i['in_not_detection_area'],
            is_new_clue=i['new_clue'],
            szdl=i['szdl']
        )
    PanoramaImage.objects.filter(image_id=image_id).update(status=1, desc=desc)
    return {'alarms': change_results, 'point_id': point_id, 'tile_output_path': tile_output_path,
            'image_path': panorama_image_obj['image_path']}


def start_detection(file1_path, file2_path, panorama_image_obj):
    """
    全景图变化检测
    """
    from ai_detection.draw_panorama import main_draw_panorama_with_bboxes
    from ai_detection.cut_image import main_cut_image
    from ai_detection.predict import main_detection
    output_dir = os.path.join(settings.BASE_DIR, 'static', 'output', panorama_image_obj['image_id'])
    os.makedirs(output_dir, exist_ok=True)
    main_cut_image(file1_path, file2_path, output_dir)
    save_path = os.path.join(settings.BASE_DIR, 'static', 'resultImg', panorama_image_obj['image_id'])

    save_path2 = os.path.join(output_dir, 'C')
    os.makedirs(save_path2, exist_ok=True)
    main_detection(output_dir, save_path, save_path2)
    pic_save_path = os.path.join(settings.BASE_DIR, 'static', 'finalImg', panorama_image_obj['image_id'])
    os.makedirs(pic_save_path, exist_ok=True)
    result = main_draw_panorama_with_bboxes(file1_path, save_path,
                                            os.path.join(pic_save_path, os.path.basename(file1_path)))
    for i in result:
        yaw = (i['center_x'] / panorama_image_obj['image_width']) * 360 - 180
        pitch = 90 - (i['center_y'] / panorama_image_obj['image_height']) * 180

        alarm_lat, alarm_lon = image_to_latlon(panorama_image_obj['latitude'],
                                               panorama_image_obj['longitude'],
                                               panorama_image_obj['height'], yaw, pitch,
                                               panorama_image_obj['yaw_degree'])
        i['latitude'] = alarm_lat
        i['longitude'] = alarm_lon
    return result


def start_change_detection(pre_image_id, last_results, pre_image_path, panorama_image_obj):
    """
    处理全景目标检测变化
    Args:
        pre_image_id:
        last_results:
        pre_image_path:
        panorama_image_obj:

    Returns:

    """
    logger.info("处理全景目标检测变化")
    pre_results = Clue.objects.filter(panorama_image_id=pre_image_id).values()
    pre_clues = []
    last_clues = []
    for row in pre_results:
        if not row['position']:
            continue
        position = row['position'].strip('[]')  # 去掉两边的方括号
        position = list(map(int, position.split()))  # 将空格替换为逗号
        if len(position) == 0:
            continue
        pre_clues.append({row['pk_id']: position})

    for row in last_results:
        position = row['position']
        if len(position) == 0:
            continue
        last_clues.append({row['id']: position})
    pre_panorama_image_file = pre_image_path
    last_panorama_image_file = panorama_image_obj['image_path']
    if len(pre_clues) > 0:
        change_results = panorama_image_registration_by_cube_image(pre_panorama_image_file,
                                                                   last_panorama_image_file,
                                                                   1024,
                                                                   pre_clues, last_clues)
        if len(change_results) > 0:
            logger.info(f"变化检测剔除后的线索数量:{change_results},{type(change_results[0])}")
            for i in last_results:
                print("123", i['id'], change_results)
                if i['id'] not in change_results:
                    i['new_clue'] = 0
                else:
                    i['new_clue'] = 1
    else:
        logger.info("当前全景图片没有前景数据，无需变化检测！")
    return last_results


def submit_panorama_detection(image_id, panorama_image_obj):
    """提交全景检测 Celery 任务，并记录入队结果便于排查"""
    try:
        async_result = panorama_detection.apply_async(
            args=[image_id, panorama_image_obj],
            task_id=str(image_id),
        )
        logger.info(
            'Celery任务已入队: task=%s, task_id=%s, celery_id=%s, broker=%s',
            panorama_detection.name,
            image_id,
            async_result.id,
            celery_app.conf.broker_url,
        )
        return async_result
    except Exception:
        logger.exception('Celery任务入队失败: task_id=%s', image_id)
        raise


app = celery_app
