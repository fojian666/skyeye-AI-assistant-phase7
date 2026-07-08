# coding=utf-8
import os
import sys
import socket
from pathlib import Path

from django.conf import settings

from logger import Logger
import configparser
WORK_DIR = Path(__file__).parent
config = configparser.ConfigParser()
config.read(os.path.join(settings.BASE_DIR, 'config.ini'),encoding='utf-8')
config_ai_interpretation = config['ai_interpretation']

STANET_ENV = sys.executable
# 模型预测batch_size大小，即一次预测多少张
batch_size = int(config_ai_interpretation.get('batch_size'))
#模型剪裁图片大小
block_size = int(config_ai_interpretation.get('block_size'))
#需要开多少个线程，一般设为1
pool_num = int(config_ai_interpretation.get('pool_num'))
#数据超过指定大小时，剪裁大小，变化检测用到
clip_size = int(config_ai_interpretation.get('clip_size'))
#数据的最大尺寸判断
max_single_img_size = int(config_ai_interpretation.get('max_single_img_size'))
#变化检测概率计算时，设置的上图面积
area_of_figure_above = float(config_ai_interpretation.get('area_of_figure_above'))
#重叠度设置
overlap_x = int(config_ai_interpretation.get('overlap_x'))
overlap_y = int(config_ai_interpretation.get('overlap_y'))
#超过指定数量得属性记录时。分为多个shp存储
max_savenum = int(config_ai_interpretation.get('max_savenum'))
dataSize = int(config_ai_interpretation.get('dataSize'))
AI_DB = config['redis'].get('ai_db')

IP_ADDRESS = config_ai_interpretation.get('ip_address')
REDISIP = config_ai_interpretation.get('redis_ip')
logger = Logger(logname='ai_interpretation.log', loglevel=5, logger='ai_interpretation').getlog()

# 本项目绝对路径
PROJECT_PATH = WORK_DIR
BUILDING_REGULAR = False
#显示节点
node_information_all = {'地类分割':['影像裁剪','加载模型','影像分割预测','栅格转矢量','预测完成','结束'],
                        '基于地类变化模型预测':['数据处理', '变化检测开始', '计算影像分区信息', '分区检测', '栅格转矢量', '预测完成','结束'],
                        '基于地类分割擦除预测':['数据处理', '影像分割','加载模型','影像分割预测','栅格转矢量','预测完成','结果优化','结束'],
                        }

# 影像参数设置
# 分幅阈值，行*列/分辨率
OVERSIZE = int(config_ai_interpretation.get('oversize'))
# 分幅最小行列长宽（单位：张，每张大小：256*256）
SPLIT_UNIT = int(config_ai_interpretation.get('split_unit'))
# 缩略图最短边长度
SQUEEZE_UNIT = int(config_ai_interpretation.get('squeeze_unit'))
#多分类配置
num_classes = config_ai_interpretation.get('num_classes')
ST_COLORMAP = config_ai_interpretation.get('st_colormap')
ST_CLASSES = config_ai_interpretation.get('st_classes')
ST_COLORMAP_pixel = config_ai_interpretation.get('st_colormap_pixel')

# 影像分割模型与预测类别
IMAGE_SEGMENTATION_MODEL = {
    "道路": os.path.join(WORK_DIR, r"models\DLinkNet_ResNet101_road_QH_2m_256_10k_230622.th"),
    "水系": os.path.join(WORK_DIR, r"models\Segformer_Mitb5_water_HD_1m05m03m_256_300k_240328.pth"),
    "耕地": os.path.join(WORK_DIR, r"models\Segformer_Mitb5_farmland_YN_05m_256_10k_240618.pth"),
    "建筑物": os.path.join(WORK_DIR, r"models\Segformer_Mitb5_building_QG_1m05m03m_256_530k_230928.th"),

}

MMSEG_CONFIGPY = {
    "水系": os.path.join(WORK_DIR, r"models\configpy\Segformer_Mitb5_water_HD_1m05m03m_256_300k_240328.py"),
    "耕地": os.path.join(WORK_DIR, r"models\configpy\Segformer_Mitb5_farmland_YN_05m_256_10k_240618_config_v30.py"),
    "建筑物": os.path.join(WORK_DIR, r"models\configpy\Segformer_Mitb5_building_QG_1m05m03m_256_530k_230928.py"),
}


# 变化检测模型与预测类别
CHANGE_DETECTION_MODEL = {
    "建设用地变化检测": os.path.join(WORK_DIR, "models/STANet_ResNet18_buildingCD_QH_2m_256_20k_230719_net_A.pth"),
    "建设用地变化检测(BIT)": os.path.join(WORK_DIR, "models/change_detection/BIT_ResNet18_buildingCD_QH_2M_256_30k_231122.pt"),
    # "建设用地变化检测(MCD)": os.path.join(WORK_DIR, "model/BiSRNet_ResNet18_mcd_JS_1m_256_3k_231104.pth")
}



