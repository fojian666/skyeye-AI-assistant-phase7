# _*_ coding: utf-8 _*_
# @Time : 2024/8/2 10:40 
# @Author : xxx 
# @Version：V 0.1
# @File : urls.py
# @desc :
from django.urls import path
from . import views

urlpatterns = [
    # 体验中心
    path('experience_data', views.experience_data),
    path('files1', views.files1),
    path('task_lists', views.task_lists),
    path('od_image_list', views.od_image_list),
    path('task_data', views.task_data),
    path('panorama', views.panorama),
    path('project', views.project),
    path('project_delete', views.project_delete),
    path('get_shape', views.get_shape),
    path('label_data', views.label_data),
    path('get_alarms_list', views.get_alarms_list),
    path('alarms_delete', views.alarms_delete, name='删除报警信息'),
    path('get_alarms_by_id', views.get_alarms_by_id),
    path('video_task', views.video_task, name='视频检测'),
    path('panorama_task_del', views.panorama_task_delete, name='删除全景图任务'),
]
