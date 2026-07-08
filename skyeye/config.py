# _*_ coding: utf-8 _*_
# @Time : 2022/10/11 9:49 
# @Author : xxx 
# @Version：V 0.1
# @File : config.py
# @desc :
import enum


class OperationOptions(enum.Enum):
    """
    枚举列出操作选项
    """
    PANORAMA = '全景图'
    OBJECT_DETECTION = '目标检测'

