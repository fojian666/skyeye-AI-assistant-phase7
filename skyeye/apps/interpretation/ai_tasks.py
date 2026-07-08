# _*_ coding: utf-8 _*_
# @Time : 2024/8/13 18:59
# @Author : xxx
# @Version：V 0.1
# @File : ai_tasks.py
# @desc :
import os, sys
import django
import torch
work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, work_dir)
from gtus.celery_config_ai import celery_app
from celery import Task as CeleryTask
import time
django.setup()
from django.conf import settings
from apps.panorama.common import create_path,ip_connect_log
from apps.interpretation.models import InterpretationTask
from apps.interpretation.ai_analysis.function_api import change_detection_one_step_main,image_segmentation_predict_main,image_seg_er_predict_main
from apps.interpretation.ai_analysis.data_process.img_resampling_and_main import DataProcessMain
from apps.interpretation import ai_config
logger = ai_config.logger
ip_address = settings.IP_ADDRESS


class DatabaseTask(CeleryTask):
    # 数据处理任务回调函数，查询TaskDataProcess下的任务表
    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        print("ID为%s的任务已经完成!!!" % task_id)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(base=DatabaseTask)
def image_segmentation_predict(task_id,project_id,input_path,output_path, fragment, building_regular,
                               model_path, model_name, config_path, model_network):
    """
    影像分割
    """
    InterpretationTask.objects.filter(id=project_id).update(status=1)
    status_num_txt_path = ip_connect_log(settings.BASE_DIR,'logs/status.txt')
    # 查项目表
    try:
        result_status = image_segmentation_predict_main(input_path, output_path, fragment, building_regular,
                                                        model_path, status_num_txt_path, model_name, config_path, model_network)
        InterpretationTask.objects.filter(id=project_id).update(status=2)
    except Exception as e:
        print(e)
        # 结果状态
        result_status = False
        InterpretationTask.objects.filter(id=project_id).update(status=3)
        logger.error("结束:影像分割处理路由报错，报错内容{}".format(e))
    return result_status


@celery_app.task(base=DatabaseTask)
def change_detection_one_step(task_id,project_id,output_path,folder_name,prev_path,next_path,model_path,fragment,model_network,
                              building_regular):
    """
    变化检测一键通
    """
    #创建节点的状态信息文件
    # 获取任务的task_id
    InterpretationTask.objects.filter(id=project_id).update(status=1)
    status_num_txt_path = ip_connect_log(settings.BASE_DIR,'logs/status.txt')
    time.sleep(2)
    try:
        data_process_dir_i = os.path.join(output_path, "data_process_result", folder_name)
        change_detection_dir_i = os.path.join(output_path, "change_detection", folder_name)
        mask_tif_path = os.path.join(data_process_dir_i, 'mask_tif')
        successful_dir = os.path.join(data_process_dir_i, 'successful')
        failed_dir = os.path.join(data_process_dir_i, 'failed')
        create_path([data_process_dir_i, change_detection_dir_i, mask_tif_path, successful_dir, failed_dir])
        # 第一阶段：数据处理
        print(folder_name, prev_path, next_path, successful_dir,
                                                failed_dir, mask_tif_path, 0.5, '0',
                                                3, 28, status_num_txt_path)
        DataProcessMain().start_data_preprocess(folder_name, prev_path, next_path, successful_dir,
                                                failed_dir, mask_tif_path, 0.5, '0',
                                                3, 28, status_num_txt_path)
        # 计算变化检测每个任务所占进度间隔
        bar_interval = int(60 / len(os.listdir(successful_dir)))
        # # 第二阶段：变化检测
        change_detection_one_step_main(model_path, successful_dir, change_detection_dir_i, bar_interval,
                                       fragment, building_regular, '0', 0.5,
                                       status_num_txt_path, folder_name, model_network)
        # 清除gpu显存
        torch.cuda.empty_cache()

        InterpretationTask.objects.filter(id=project_id).update(status=2)
    except Exception as e:
        print(e)
        logger.error("结束:变化检测一键通错误,{}@{}".format(e, folder_name))
        InterpretationTask.objects.filter(id=project_id).update(status=3)
    return True

@celery_app.task(base=DatabaseTask)
def image_seg_er_predict(task_id,project_id,prev_path, next_path, model_path, model_network, fragment, building_regular,output_path,config_path):
    """
    基于影像分割擦除
    """
    InterpretationTask.objects.filter(id=project_id).update(status=1)
    status_num_txt_path = ip_connect_log(settings.BASE_DIR,'logs/status.txt')
    folder_name = ''
    try:
        print(task_id)
        time.sleep(2)
        image_seg_er_predict_main(prev_path, next_path, output_path, fragment, building_regular,
                                  model_path, status_num_txt_path, folder_name, config_path, model_network)
        InterpretationTask.objects.filter(id=project_id).update(status=2)
    except Exception as e:
        print(e)
        logger.error("结束:擦除一键通错误,{}@{}".format(e, folder_name))
        InterpretationTask.objects.filter(id=project_id).update(status=3)
    return True