# _*_ coding: utf-8 _*_
# @Time : 2024/8/2 10:40 
# @Author : xxx 
# @Version：V 0.1
# @File : urls.py
# @desc :
from django.urls import path
from . import views
urlpatterns = [
    path('models_list', views.models_list, name='获取模型数据'),
    path('model/<model_id>',views.model,name='获取单个模型数据')
]