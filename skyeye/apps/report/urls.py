# _*_ coding: utf-8 _*_
# @Time : 2024/8/2 10:40 
# @Author : xxx 
# @Version：V 0.1
# @File : urls.py
# @desc :
from django.urls import path
from . import views

urlpatterns = [
    # 报告管理
    path('report_list', views.report_list),
    path('report_params', views.report_params),
    path('report_generate', views.report_generate),  # 报告生成
    path('report_delete', views.report_delete),  # 报告删除
    path('batch_report', views.batch_report),  # 获取批次报告
    path('download/<batch_report_id>',views.report_download),
]
