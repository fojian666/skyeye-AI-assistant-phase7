# _*_ coding: utf-8 _*_
# @Time : 2023/7/27 16:07 
# @Author : xxx 
# @Version：V 0.1
# @File : custom_enumeration.py
# @desc : 自定义的枚举类
import enum


class DetectionType(enum.Enum):
    """
    检测类型枚举类
    """
    IMAGESEGMENTATION = '地类分割'
    PREDICTIONBASEDONCD = '基于地类变化模型预测'
    ERASEBASEDONIS = '基于地类分割擦除预测'
    OBJECTDETECTION = '目标检测'