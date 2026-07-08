# -*- coding: UTF-8 -*-
# 影像分割预测代码
import shutil
try:
    import gdal,osr
except:
    from osgeo import gdal,osr
import numpy as np
import torch
from osgeo import gdal
import time
import cv2
import os,sys
from math import *
sys.path.append('..')
import torch.nn as nn
from torchvision import models
import torch.nn.functional as F
from functools import partial
from PIL import Image
from sklearn.cluster import KMeans
import pandas as pd
import threadpool
from utils.merge_tiffs_and_convert_tif_to_shp_common import merge_tif_and_convert_to_shp
from utils.add_region_fields import add_XZQ_fields
from utils.sim_building import sim_main
import apps.interpretation.ai_config as cg
import utils.common as common
# 每个分区所占预测进度百分比
SPLIT_STATUS_BAR_UNIT = 0
SPLIT_PREDICT_COUNT = 0
# 初始化状态全局变量
# 设置工作路径与util路径
work_dir = cg.PROJECT_PATH
batchsize = cg.batch_size
blocksize = cg.block_size
poolnum = cg.pool_num
logger = cg.logger
util_dir = os.path.join(work_dir, 'utils')
nonlinearity = partial(F.relu, inplace=True)
# 解除影像读取大小限制
Image.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
is_add_radio = '0'
img_name_tag = ''
overlap_x = cg.overlap_x
overlap_y = cg.overlap_y

class Dblock_more_dilate(nn.Module):
    # DLinkNet空洞卷积块
    def __init__(self, channel):
        super(Dblock_more_dilate, self).__init__()
        self.dilate1 = nn.Conv2d(channel, channel, kernel_size=3, dilation=1, padding=1)
        self.dilate2 = nn.Conv2d(channel, channel, kernel_size=3, dilation=2, padding=2)
        self.dilate3 = nn.Conv2d(channel, channel, kernel_size=3, dilation=4, padding=4)
        self.dilate4 = nn.Conv2d(channel, channel, kernel_size=3, dilation=8, padding=8)
        self.dilate5 = nn.Conv2d(channel, channel, kernel_size=3, dilation=16, padding=16)
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.ConvTranspose2d):
                if m.bias is not None:
                    m.bias.data.zero_()

    def forward(self, x):
        dilate1_out = nonlinearity(self.dilate1(x))
        dilate2_out = nonlinearity(self.dilate2(dilate1_out))
        dilate3_out = nonlinearity(self.dilate3(dilate2_out))
        dilate4_out = nonlinearity(self.dilate4(dilate3_out))
        dilate5_out = nonlinearity(self.dilate5(dilate4_out))
        out = x + dilate1_out + dilate2_out + dilate3_out + dilate4_out + dilate5_out
        return out


class Dblock(nn.Module):
    # DLinkNet结构块
    def __init__(self, channel):
        super(Dblock, self).__init__()
        self.dilate1 = nn.Conv2d(channel, channel, kernel_size=3, dilation=1, padding=1)
        self.dilate2 = nn.Conv2d(channel, channel, kernel_size=3, dilation=2, padding=2)
        self.dilate3 = nn.Conv2d(channel, channel, kernel_size=3, dilation=4, padding=4)
        self.dilate4 = nn.Conv2d(channel, channel, kernel_size=3, dilation=8, padding=8)
        # self.dilate5 = nn.Conv2d(channel, channel, kernel_size=3, dilation=16, padding=16)
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.ConvTranspose2d):
                if m.bias is not None:
                    m.bias.data.zero_()

    def forward(self, x):
        dilate1_out = nonlinearity(self.dilate1(x))
        dilate2_out = nonlinearity(self.dilate2(dilate1_out))
        dilate3_out = nonlinearity(self.dilate3(dilate2_out))
        dilate4_out = nonlinearity(self.dilate4(dilate3_out))
        out = x + dilate1_out + dilate2_out + dilate3_out + dilate4_out  # + dilate5_out
        return out


class DecoderBlock(nn.Module):
    # DLinkNet解码块
    def __init__(self, in_channels, n_filters):
        super(DecoderBlock, self).__init__()

        self.conv1 = nn.Conv2d(in_channels, in_channels // 4, 1)
        self.norm1 = nn.BatchNorm2d(in_channels // 4)
        self.relu1 = nonlinearity

        self.deconv2 = nn.ConvTranspose2d(in_channels // 4, in_channels // 4, 3, stride=2, padding=1, output_padding=1)
        self.norm2 = nn.BatchNorm2d(in_channels // 4)
        self.relu2 = nonlinearity

        self.conv3 = nn.Conv2d(in_channels // 4, n_filters, 1)
        self.norm3 = nn.BatchNorm2d(n_filters)
        self.relu3 = nonlinearity

    def forward(self, x):
        x = self.conv1(x)
        x = self.norm1(x)
        x = self.relu1(x)
        x = self.deconv2(x)
        x = self.norm2(x)
        x = self.relu2(x)
        x = self.conv3(x)
        x = self.norm3(x)
        x = self.relu3(x)
        return x


class DinkNet101(nn.Module):
    # DLinkNet101网络结构
    def __init__(self, num_classes=1):
        super(DinkNet101, self).__init__()

        filters = [256, 512, 1024, 2048]
        resnet = models.resnet101(pretrained=True)
        self.firstconv = resnet.conv1
        self.firstbn = resnet.bn1
        self.firstrelu = resnet.relu
        self.firstmaxpool = resnet.maxpool
        self.encoder1 = resnet.layer1
        self.encoder2 = resnet.layer2
        self.encoder3 = resnet.layer3
        self.encoder4 = resnet.layer4

        self.dblock = Dblock_more_dilate(2048)

        self.decoder4 = DecoderBlock(filters[3], filters[2])
        self.decoder3 = DecoderBlock(filters[2], filters[1])
        self.decoder2 = DecoderBlock(filters[1], filters[0])
        self.decoder1 = DecoderBlock(filters[0], filters[0])

        self.finaldeconv1 = nn.ConvTranspose2d(filters[0], 32, 4, 2, 1)
        self.finalrelu1 = nonlinearity
        self.finalconv2 = nn.Conv2d(32, 32, 3, padding=1)
        self.finalrelu2 = nonlinearity
        self.finalconv3 = nn.Conv2d(32, num_classes, 3, padding=1)

    def forward(self, x):
        # Encoder
        x = self.firstconv(x)
        x = self.firstbn(x)
        x = self.firstrelu(x)
        x = self.firstmaxpool(x)
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)

        # Center
        e4 = self.dblock(e4)
        # Decoder
        d4 = self.decoder4(e4) + e3
        d3 = self.decoder3(d4) + e2
        d2 = self.decoder2(d3) + e1
        d1 = self.decoder1(d2)
        out = self.finaldeconv1(d1)
        out = self.finalrelu1(out)
        out = self.finalconv2(out)
        out = self.finalrelu2(out)
        out = self.finalconv3(out)
        return F.sigmoid(out)


class DinkNet50(nn.Module):
    # DLinkNet50网络结构
    def __init__(self, num_classes=1):
        super(DinkNet50, self).__init__()

        filters = [256, 512, 1024, 2048]
        resnet = models.resnet50(pretrained=True)
        # resnet = res2net50_26w_4s(pretrained=True)
        self.firstconv = resnet.conv1
        self.firstbn = resnet.bn1
        self.firstrelu = resnet.relu
        self.firstmaxpool = resnet.maxpool
        self.encoder1 = resnet.layer1
        self.encoder2 = resnet.layer2
        self.encoder3 = resnet.layer3
        self.encoder4 = resnet.layer4

        self.dblock = Dblock_more_dilate(2048)

        self.decoder4 = DecoderBlock(filters[3], filters[2])
        self.decoder3 = DecoderBlock(filters[2], filters[1])
        self.decoder2 = DecoderBlock(filters[1], filters[0])
        self.decoder1 = DecoderBlock(filters[0], filters[0])

        self.finaldeconv1 = nn.ConvTranspose2d(filters[0], 32, 4, 2, 1)
        self.finalrelu1 = nonlinearity
        self.finalconv2 = nn.Conv2d(32, 32, 3, padding=1)
        self.finalrelu2 = nonlinearity
        self.finalconv3 = nn.Conv2d(32, num_classes, 3, padding=1)

    def forward(self, x):
        # Encoder
        x = self.firstconv(x)
        x = self.firstbn(x)
        x = self.firstrelu(x)
        x = self.firstmaxpool(x)
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)

        # Center
        e4 = self.dblock(e4)

        # Decoder
        d4 = self.decoder4(e4) + e3
        d3 = self.decoder3(d4) + e2
        d2 = self.decoder2(d3) + e1
        d1 = self.decoder1(d2)
        out = self.finaldeconv1(d1)
        out = self.finalrelu1(out)
        out = self.finalconv2(out)
        out = self.finalrelu2(out)
        out = self.finalconv3(out)

        return F.sigmoid(out)
        # return out

    def predict(self, x):
        return self.forward(x)


class DinkNet34(nn.Module):
    # DLinkNet34网络结构
    def __init__(self, num_classes=1, num_channels=3):
        super(DinkNet34, self).__init__()

        filters = [64, 128, 256, 512]
        resnet = models.resnet34(pretrained=True)
        self.firstconv = resnet.conv1
        self.firstbn = resnet.bn1
        self.firstrelu = resnet.relu
        self.firstmaxpool = resnet.maxpool
        self.encoder1 = resnet.layer1
        self.encoder2 = resnet.layer2
        self.encoder3 = resnet.layer3
        self.encoder4 = resnet.layer4

        self.dblock = Dblock(512)

        self.decoder4 = DecoderBlock(filters[3], filters[2])
        self.decoder3 = DecoderBlock(filters[2], filters[1])
        self.decoder2 = DecoderBlock(filters[1], filters[0])
        self.decoder1 = DecoderBlock(filters[0], filters[0])

        self.finaldeconv1 = nn.ConvTranspose2d(filters[0], 32, 4, 2, 1)
        self.finalrelu1 = nonlinearity
        self.finalconv2 = nn.Conv2d(32, 32, 3, padding=1)
        self.finalrelu2 = nonlinearity
        self.finalconv3 = nn.Conv2d(32, num_classes, 3, padding=1)

    def forward(self, x):
        # Encoder
        x = self.firstconv(x)
        x = self.firstbn(x)
        x = self.firstrelu(x)
        x = self.firstmaxpool(x)
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)

        # Center
        e4 = self.dblock(e4)

        # Decoder
        d4 = self.decoder4(e4) + e3
        d3 = self.decoder3(d4) + e2
        d2 = self.decoder2(d3) + e1
        d1 = self.decoder1(d2)

        out = self.finaldeconv1(d1)
        out = self.finalrelu1(out)
        out = self.finalconv2(out)
        out = self.finalrelu2(out)
        out = self.finalconv3(out)

        return F.sigmoid(out)

    def predict(self, x):
        return self.forward(x)


def get_dinknet(weight_path):
    """
    获取模型权重
    Args:
        weight_path: 模型路径
    Returns:
        net: 模型权重
    """
    # net = DinkNet34(num_classes=1).cuda()
    # net = DinkNet50(num_classes=1).cuda()
    # 读取DLinkNet101权重
    if os.path.basename(weight_path).find("multi") != -1 or os.path.basename(weight_path).find("Multi") != -1:
        net = DinkNet101(num_classes=5).cuda()  # 多分类
    else:
        net = DinkNet101(num_classes=1).cuda()  # 单分类
    # 读取以pth结尾的模型
    if weight_path.split(".")[1] == "pth":
        state = torch.load(weight_path, map_location='cpu')
        pro = {}
        for t in state.keys():
            pro[t] = state[t]
        net.load_state_dict(pro)
        net.eval()
    # 读取以th结尾的模型
    else:
        net = net.cuda()
        net = torch.nn.DataParallel(net, device_ids=range(torch.cuda.device_count()))
        net.load_state_dict(torch.load(weight_path))
    return net


def tiff_regions_meta_info_precalculating(image_path, block_size, output_path, overlap_size=(overlap_x, overlap_y)):
    """
    图像分幅，获取整张图片相关信息(重叠分割)
    Args:
        image_path: 图像路径
        block_size: 切分单元大小
        output_path: 输出路径
        overlap_size: 重叠带大小

    Returns:
        split_info: 分区信息
        overlap_col: 重叠带列数
        overlap_row: 重叠带行数
        split_col: 切分列数
        split_row: 切分行数
    """

    # 读取图片信息
    image_dataset = gdal.Open(image_path)
    # 导入投影参数至srs
    srs = osr.SpatialReference()
    srs.ImportFromWkt(image_dataset.GetProjection())
    # 重叠带行数
    overlap_row = 1 + ceil((image_dataset.RasterYSize - block_size) / (block_size - overlap_size[1]))
    # 重叠带列数
    overlap_col = 1 + ceil((image_dataset.RasterXSize - block_size) / (block_size - overlap_size[0]))

    # 记录每个分区的起点坐标、终点坐标、起始列、起始行、终止列、终止行、存储路径
    split_info = {}
    # 记录每个分区左上角顶点行列号
    split_point = []
    # 默认全部分幅，只有一张的就是0_0
    # 分幅行列数
    split_col = ceil(overlap_col / cg.SPLIT_UNIT)
    split_row = ceil(overlap_row / cg.SPLIT_UNIT)
    # 切割边缘区域的长宽张数
    left_col = overlap_col % cg.SPLIT_UNIT
    if left_col == 0:
        left_col = cg.SPLIT_UNIT
    left_row = overlap_row % cg.SPLIT_UNIT
    if left_row == 0:
        left_row = cg.SPLIT_UNIT
    # 新建对应分区文件夹，命名格式为列_行，并将各个分区的起终行列号存入split_info中，键值为"分区列号_分区行号"
    for col in range(split_col):
        for row in range(split_row):
            split_info[str(col) + "_" + str(row)] = {}
            split_path = common.create_path(output_path, str(col) + "_" + str(row))
            split_info[str(col) + "_" + str(row)]["path"] = split_path
            split_info[str(col) + "_" + str(row)]["start_col"] = cg.SPLIT_UNIT * col
            split_info[str(col) + "_" + str(row)]["start_row"] = cg.SPLIT_UNIT * row
            if col < split_col - 1:
                split_info[str(col) + "_" + str(row)]["end_col"] = cg.SPLIT_UNIT * (col + 1) - 1
            else:
                split_info[str(col) + "_" + str(row)]["end_col"] = cg.SPLIT_UNIT * col + left_col - 1
            if row < split_row - 1:
                split_info[str(col) + "_" + str(row)]["end_row"] = cg.SPLIT_UNIT * (row + 1) - 1
            else:
                split_info[str(col) + "_" + str(row)]["end_row"] = cg.SPLIT_UNIT * row + left_row - 1
            split_point.append([cg.SPLIT_UNIT * col, cg.SPLIT_UNIT * row])
    # 计算每个分区的角点（左上start，右下end）
    for col in range(overlap_col):
        # 计算当前x方向的重叠带累计长度，后续计算分区原点坐标时要加上
        offset_x = col * (block_size - overlap_size[1])
        for row in range(overlap_row):
            # 计算当前x方向的重叠带累计长度
            offset_y = row * (block_size - overlap_size[0])
            if [col, row] in split_point:
                ori_transform = image_dataset.GetGeoTransform()
                # 读取原图仿射变换参数值
                top_left_x = ori_transform[0]  # 左上角x坐标
                w_e_pixel_resolution = ori_transform[1]  # 东西方向像素分辨率
                top_left_y = ori_transform[3]  # 左上角y坐标
                n_s_pixel_resolution = ori_transform[5]  # 南北方向像素分辨率
                # 根据仿射变换参数计算新图的原点坐标
                top_left_x = top_left_x + offset_x * w_e_pixel_resolution
                top_left_y = top_left_y + offset_y * n_s_pixel_resolution

                # 取分区编号
                s_col = floor(col / cg.SPLIT_UNIT)
                s_row = floor(row / cg.SPLIT_UNIT)
                # 记录左上角点（起点）坐标
                split_info[str(s_col) + "_" + str(s_row)]["start"] = [top_left_x, top_left_y]
                # 记录右下角点（终点）坐标
                # 计算当前分区有多少列
                num_col = split_info[str(s_col) + "_" + str(s_row)]["end_col"] - \
                          split_info[str(s_col) + "_" + str(s_row)]["start_col"] + 1
                # 计算当前分区有多少行
                num_row = split_info[str(s_col) + "_" + str(s_row)]["end_row"] - \
                          split_info[str(s_col) + "_" + str(s_row)]["start_row"] + 1
                bottom_right_x = top_left_x + (
                        block_size * num_col - (num_col - 1) * overlap_size[1]) * w_e_pixel_resolution
                bottom_right_y = top_left_y + (
                        block_size * num_row - (num_row - 1) * overlap_size[0]) * n_s_pixel_resolution
                split_info[str(s_col) + "_" + str(s_row)]["end"] = [bottom_right_x, bottom_right_y]

    return split_info, overlap_col, overlap_row, split_col, split_row


def block_img_msg_over(img, block_size, start_col, start_row, end_col, end_row, overlap_size=(overlap_x, overlap_y)):
    """
    获取分区图片相关信息(重叠分割)
    Args:
        img: 图片路径
        block_size: 切分单元大小
        start_col: 起始列号
        start_row: 起始行号
        end_col: 终止列号
        end_row: 终止行号
        overlap_size: 重叠带大小

    Returns:
        image_dataset: 图片GDAL地理数据
        geo_trans: 经过坐标转换的坐标信息
        srs: 坐标系
        overlap_pad_x_size: x轴方向的去除所有overlap的实际长度
        overlap_pad_y_size: y轴方向的去除所有overlap的实际长度
        left_top: 左上角坐标
        right_bottom: 右下角坐标
        overlap_row: 重叠行数
        overlap_col: 重叠列数
        band_data_type: 波段数据类型
        geo_info: 进行坐标转换后的图像数据
    """

    # 读取图片信息
    image_dataset = gdal.Open(img)
    # 导入投影参数至srs
    srs = osr.SpatialReference()
    srs.ImportFromWkt(image_dataset.GetProjection())
    # 读取经过坐标转换的坐标信息
    geo_trans = image_dataset.GetGeoTransform()
    # 取影像顶点坐标
    left_top = [geo_trans[0], geo_trans[3]]
    right_top_x = geo_trans[0] + (image_dataset.RasterXSize - 1) * geo_trans[1] + (
            image_dataset.RasterYSize - 1) * geo_trans[2]
    right_top_y = geo_trans[3] + (image_dataset.RasterXSize - 1) * geo_trans[4] + (
            image_dataset.RasterYSize - 1) * geo_trans[5]
    right_bottom = [right_top_x, right_top_y]

    # 重叠带行数
    overlap_row = 1 + ceil((image_dataset.RasterYSize - block_size) / (block_size - overlap_size[1]))
    # y方向总填充大小
    overlap_pad_y_size = block_size + (overlap_row - 1) * \
                         (block_size - overlap_size[1]) - image_dataset.RasterYSize

    # 重叠带列数
    overlap_col = 1 + ceil((image_dataset.RasterXSize - block_size) / (block_size - overlap_size[0]))
    # x方向总填充大小
    overlap_pad_x_size = block_size + (overlap_col - 1) * \
                         (block_size - overlap_size[0]) - image_dataset.RasterXSize
    # 获取波段类型信息
    image_bound1 = image_dataset.GetRasterBand(1)
    band_data_type = image_bound1.DataType
    geo_info = {}
    # 计算每个分区的新角点坐标
    for col in range(start_col, end_col + 1):
        # 计算当前x方向的重叠带累计长度，后续计算分区原点坐标时要加上
        offset_x = col * (block_size - overlap_size[1])
        for row in range(start_row, end_row + 1):
            # 计算当前y方向的重叠带累计长度，后续计算分区原点坐标时要加上
            offset_y = row * (block_size - overlap_size[0])
            ori_transform = image_dataset.GetGeoTransform()
            # 读取原图仿射变换参数值
            top_left_x = ori_transform[0]  # 左上角x坐标
            w_e_pixel_resolution = ori_transform[1]  # 东西方向像素分辨率
            top_left_y = ori_transform[3]  # 左上角y坐标
            n_s_pixel_resolution = ori_transform[5]  # 南北方向像素分辨率
            # 根据反射变换参数计算新图的原点坐标
            top_left_x = top_left_x + offset_x * w_e_pixel_resolution
            top_left_y = top_left_y + offset_y * n_s_pixel_resolution

            # 将计算后的值组装为一个元组，以方便设置
            dst_transform = (
                top_left_x, ori_transform[1], ori_transform[2], top_left_y, ori_transform[4], ori_transform[5])
            if not geo_info.get(col):
                geo_info[col] = dst_transform

    return image_dataset, geo_trans, srs, overlap_pad_x_size, overlap_pad_y_size, left_top, right_bottom, overlap_row, overlap_col, band_data_type, geo_info


def split_img(image_dataset, output_pic_path, block_size, pad_xsize, pad_ysize, sum_row, sum_col, start_col, start_row,
              end_col, end_row, area_info, overlap_size=(overlap_x, overlap_y)):
    """
    图片分区，切分图片，并保证切分后的每张图片有一定的重叠部分
    Args:
        image_dataset: GDAL图像数据
        output_pic_path: 输出图像路径
        block_size: 切分单元大小
        pad_xsize: x轴方向的去除所有overlap的实际长度
        pad_ysize: y轴方向的去除所有overlap的实际长度
        sum_row: 总行数
        sum_col: 总列数
        start_col: 起始列号
        start_row: 起始行号
        end_col: 终止列号
        end_row: 终止行号
        area_info: 区域信息
        overlap_size: 重叠带大小
    """

    # 读取原图中的每个波段
    image_bound1 = image_dataset.GetRasterBand(1)
    image_bound2 = image_dataset.GetRasterBand(2)
    image_bound3 = image_dataset.GetRasterBand(3)
    # 初始化行列外边矩阵，全部置零，因为要将不满256的部分用0值补全
    col_pad_array = np.zeros((block_size, pad_xsize))
    row_pad_array = np.zeros((pad_ysize, block_size))
    # 计算行列数和图片总数
    num_col = end_col - start_col + 1
    num_row = end_row - start_row + 1
    sum_pic = str(num_col * num_row)
    count = 0
    for i in range(start_col, end_col + 1):
        # 计算当前x方向的重叠带累计长度
        offset_x = i * (block_size - overlap_size[1])
        for j in range(start_row, end_row + 1):
            count += 1
            # 计算当前y方向的重叠带累计长度
            offset_y = j * (block_size - overlap_size[0])
            # 如果读到最后一行最后一列，补全行列外边
            if (j == sum_row - 1) and (i == sum_col - 1):
                # 以矩阵形式读取影像的3个波段
                out_band1 = image_bound1.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size - pad_ysize)
                out_band2 = image_bound2.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size - pad_ysize)
                out_band3 = image_bound3.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size - pad_ysize)
                # 重新初始化行重叠带矩阵
                row_pad_array = np.zeros((pad_ysize, block_size - pad_xsize))

                if out_band1 is None or out_band2 is None or out_band3 is None:
                    continue
                # 将三波段分别接上行列边
                out_band1 = np.concatenate((out_band1, row_pad_array), axis=0)
                out_band2 = np.concatenate((out_band2, row_pad_array), axis=0)
                out_band3 = np.concatenate((out_band3, row_pad_array), axis=0)

                out_band1 = np.concatenate((out_band1, col_pad_array), axis=1)
                out_band2 = np.concatenate((out_band2, col_pad_array), axis=1)
                out_band3 = np.concatenate((out_band3, col_pad_array), axis=1)
            # 如果是最后一行则接行外边
            elif j == sum_row - 1:
                out_band1 = image_bound1.ReadAsArray(offset_x, offset_y, block_size,
                                                     block_size - pad_ysize)
                out_band2 = image_bound2.ReadAsArray(offset_x, offset_y, block_size,
                                                     block_size - pad_ysize)
                out_band3 = image_bound3.ReadAsArray(offset_x, offset_y, block_size,
                                                     block_size - pad_ysize)

                if out_band1 is None or out_band2 is None or out_band3 is None:
                    continue
                out_band1 = np.concatenate((out_band1, row_pad_array), axis=0)
                out_band2 = np.concatenate((out_band2, row_pad_array), axis=0)
                out_band3 = np.concatenate((out_band3, row_pad_array), axis=0)
            # 如果是最后一列则接列外边
            elif i == sum_col - 1:
                out_band1 = image_bound1.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size)
                out_band2 = image_bound2.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size)
                out_band3 = image_bound3.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size)
                if out_band1 is None or out_band2 is None or out_band3 is None:
                    continue
                out_band1 = np.concatenate((out_band1, col_pad_array), axis=1)
                out_band2 = np.concatenate((out_band2, col_pad_array), axis=1)
                out_band3 = np.concatenate((out_band3, col_pad_array), axis=1)

            else:
                out_band1 = image_bound1.ReadAsArray(offset_x, offset_y, block_size, block_size)
                out_band2 = image_bound2.ReadAsArray(offset_x, offset_y, block_size, block_size)
                out_band3 = image_bound3.ReadAsArray(offset_x, offset_y, block_size, block_size)

            # # 获取Tif的驱动，为创建切出来的图文件做准备
            gtif_driver = gdal.GetDriverByName("GTiff")
            out_ds = gtif_driver.Create(output_pic_path + "/" + str(i) + "-" + str(j) + '.tif',
                                        block_size, block_size, 3, image_bound1.DataType)

            # 获取原图的原点坐标信息
            ori_transform = image_dataset.GetGeoTransform()
            # 读取原图仿射变换参数值
            top_left_x = ori_transform[0]  # 左上角x坐标
            w_e_pixel_resolution = ori_transform[1]  # 东西方向像素分辨率
            top_left_y = ori_transform[3]  # 左上角y坐标
            n_s_pixel_resolution = ori_transform[5]  # 南北方向像素分辨率
            # 根据反射变换参数计算新图的原点坐标
            top_left_x = top_left_x + offset_x * w_e_pixel_resolution
            top_left_y = top_left_y + offset_y * n_s_pixel_resolution
            # 将计算后的值组装为一个元组，以方便设置
            dst_transform = (
                top_left_x, ori_transform[1], ori_transform[2], top_left_y, ori_transform[4], ori_transform[5])

            # 设置裁剪出来图的原点坐标
            out_ds.SetGeoTransform(dst_transform)
            # print("波段值",out_band1,out_band2,out_band3)
            # 写入目标文件
            out_ds.GetRasterBand(1).WriteArray(out_band1)
            out_ds.GetRasterBand(2).WriteArray(out_band2)
            out_ds.GetRasterBand(3).WriteArray(out_band3)
            # 将缓存写入磁盘
            out_ds.FlushCache()
            del out_ds

def self_sort(name_list):
    """
    生成list的排序关键词
    Args:
        name_list: 待排序list

    Returns:
        key: 新生成的关键词
    """

    x11 = int(name_list.split('-')[0])
    x12 = int(name_list.split('-')[1].split('.')[0])
    key = x11 * 1000000 + x12
    return key

def transform(image_list):
    """
    对列表中的图片进行统一的坐标转换
    Args:
        image_list: 图片列表，存有每张图片的数据流

    Returns:
        tensor_image：经过转换的图片tensor
    """

    mean = [115.6545965 / 255., 117.62014299 / 255., 106.01483799 / 255.]
    std = [56.82521775 / 255., 53.46318049 / 255., 56.07113724 / 255.]
    # 使像元值缩放至[0,1]之间
    np_image = np.array(image_list, dtype=np.float32) / 255.0
    # 纬度转换，将0,1,2,3维度的值转换至0,3,1,2纬度
    np_image = np_image.transpose((0, 3, 1, 2))
    # 将图像转为tensor格式
    tensor_image = torch.from_numpy(np_image).type(torch.FloatTensor)
    # 取tensor_image的数据类型
    data_type = tensor_image.dtype
    mean = torch.as_tensor(mean, dtype=data_type, device=tensor_image.device)
    std = torch.as_tensor(std, dtype=data_type, device=tensor_image.device)
    mean = mean[None, :, None, None]
    std = std[None, :, None, None]
    # 对张量做标准化，使其均值为0，标准差为0.1
    tensor_image.sub_(mean).div_(std)
    return tensor_image


def predict_binary_th_single(model, image_path_list, sum_pic_num, col, pic_num_per_row, area_info):
    """
    预测函数，一次预测一组，使用以th结尾的模型
    Args:
        model: 模型权重
        image_path_list: 图片路径列表
        sum_pic_num: 图片总数
        current_col: 当前列
        pic_num_per_row: 每行有多少张图片
        area_info: 区域信息

    Returns:
        result_list: 预测结果list
    """
    device = torch.device('cuda:0')
    result_list = []
    count = 0
    SHAPE = (blocksize, blocksize)
    for img_path in image_path_list:
        count = count + 1
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), 3)
        img = cv2.resize(img, SHAPE, interpolation=cv2.INTER_NEAREST)
        # 数据标准化
        img = np.array(img, np.float32).transpose(2, 0, 1) / 255.0 * 3.2 - 1.6
        img = np.expand_dims(img, 0)
        img = torch.Tensor(img)
        img = img.to(device)
        model.eval()
        with torch.no_grad():
            img = img.cuda()
            predict = model.forward(img).cpu().numpy()
        # 取置信度大于0.5的像元结果，并转为int
        # predicts = np.array(predicts > 0.5, np.int)
        predict = predict.transpose((0, 2, 3, 1))
        temp_predicts = [predict[i] for i in range(predict.shape[0])]
        result_list.extend(temp_predicts)
        torch.cuda.empty_cache()
    return result_list


def predict_binary_pth_single(model, image_path_list, sum_pic_num, current_col, pic_num_per_row, area_info):
    """
    预测函数，一次预测一组，使用以pth结尾的模型
    Args:
        model: 模型权重
        image_path_list: 图片路径列表
        sum_pic_num: 图片总数
        current_col: 当前列
        pic_num_per_row: 每行有多少张图片
        area_info: 区域信息

    Returns:
        result_list: 预测结果list
    """

    image_list = []
    # 将所有图片用cv2读取后存入image_list
    for img_path in image_path_list:
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), 3)
        img = np.array(img, dtype=np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image_list.append(img)
    # 取image_list长度
    length_image_list = len(image_list)
    batch_size = batchsize
    result_list = []
    # 如果length_image_list小于batch_size
    if length_image_list // batch_size == 0:
        # 对image_list里的图进行标准化处理
        images = transform(image_list)
        with torch.no_grad():
            images = images.cuda()
            predicts = model.forward(images).cpu().numpy()
        # 取置信度大于0.5的像元结果，并转为int
        predicts = np.array(predicts > 0.5, np.int)
        predicts = predicts.transpose((0, 2, 3, 1))
        temp_predicts = [predicts[i] for i in range(predicts.shape[0])]
        result_list.extend(temp_predicts)
        return result_list
    # 如果length_image_list能整除batch_size
    if length_image_list % batch_size == 0:
        pic_index = length_image_list // batch_size
    # 如果只是不能整除，pic_index取length_image_list除以batch_size向下取整加一
    else:
        pic_index = 1 + length_image_list // batch_size
    for i in range(pic_index):
        start = i * batch_size
        end = (i + 1) * batch_size if (i + 1) * batch_size <= length_image_list else length_image_list
        timage_list = image_list[start:end]
        images = transform(timage_list)
        with torch.no_grad():
            images = images.cuda()
            predicts = model.forward(images).cpu().numpy()
        # predicts = np.array(predicts > 0.5, np.int)
        predicts = predicts.transpose((0, 2, 3, 1))
        temp_predicts = [predicts[i] for i in range(predicts.shape[0])]
        result_list.extend(temp_predicts)
        torch.cuda.empty_cache()
    return result_list


def predict_multi_th_single1(model, image_path_list, sum_pic_num, current_col, pic_num_per_row, area_info):
    """
    多分类预测函数，一次预测一组，使用以th结尾的模型
    Args:
        model: 模型权重
        image_path_list: 图片路径列表
        sum_pic_num: 图片总数
        current_col: 当前列
        pic_num_per_row: 每行有多少张图片
        area_info: 区域信息

    Returns:
        result_list: 预测结果list
    """

    device = torch.device('cuda:0')
    result_list = []
    count = 0
    SHAPE = (blocksize, blocksize)
    for img_path in image_path_list:
        count = count + 1
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), 3)
        img = cv2.resize(img, SHAPE, interpolation=cv2.INTER_NEAREST)
        # 标准化
        img = np.array(img, np.float32).transpose(2, 0, 1) / 255.0 * 3.2 - 1.6
        img = np.expand_dims(img, 0)
        img = torch.Tensor(img)
        img = img.to(device)
        model.eval()
        with torch.no_grad():
            img = img.cuda()
            predict = model.forward(img)
        # 激活函数
        predict = F.softmax(predict, dim=1)
        # 取每个维度最大值，合并成1维
        predict = torch.argmax(predict, dim=1)
        predict = np.asarray(np.squeeze(predict.cpu().numpy()), dtype=np.int8)
        # 多分类赋值，每个值代表一类，数值区分不同颜色
        # predict[predict == 1] = 15
        # predict[predict == 2] = 44
        # predict[predict == 3] = 89
        # predict[predict == 4] = 143
        # predict[predict == 5] = 189
        # predict[predict == 6] = 255
        predict[predict == 0] = 52
        predict[predict == 1] = 123
        predict[predict == 2] = 41
        predict[predict == 3] = 46
        predict[predict == 4] = 255
        cv2.imwrite(r'E:\geo_ai_server\c#_test_data\result\6\1.tif', predict.astype(np.uint8))
        predict = torch.from_numpy(predict).unsqueeze(0).unsqueeze(0)
        predict = np.asarray(predict.cpu().numpy(), dtype=np.int8)
        predict = predict.transpose((0, 2, 3, 1))
        temp_predicts = [predict[i] for i in range(predict.shape[0])]
        result_list.extend(temp_predicts)
        torch.cuda.empty_cache()
    return result_list

def predict_multi_th_single(model, image_path_list, sum_pic_num, current_col, pic_num_per_row, area_info):
    """
    多分类预测函数，一次预测一组，使用以th结尾的模型
    Args:
        model: 模型权重
        image_path_list: 图片路径列表
        sum_pic_num: 图片总数
        current_col: 当前列
        pic_num_per_row: 每行有多少张图片
        area_info: 区域信息

    Returns:
        result_list: 预测结果list
    """

    device = torch.device('cuda:0')
    result_list = []
    count = 0
    SHAPE = (blocksize, blocksize)
    for img_path in image_path_list:
        count = count + 1
        img = cv2.imread(img_path)
        img = cv2.resize(img, SHAPE, interpolation=cv2.INTER_NEAREST)
        # 标准化
        img = np.array(img, np.float32).transpose(2, 0, 1) / 255.0 * 3.2 - 1.6
        img = np.expand_dims(img, 0)
        img = torch.Tensor(img)
        img = img.to(device)
        model.eval()
        with torch.no_grad():
            predict = model.forward(img)
        # 激活函数
        predict = F.softmax(predict, dim=1)
        # 取每个维度最大值，合并成1维
        predict = torch.argmax(predict, dim=1)
        predict = np.asarray(np.squeeze(predict.cpu().numpy()), dtype=np.int8)
        # 多分类赋值，每个值代表一类，数值区分不同颜色
        # predict[predict == 1] = 15
        # predict[predict == 2] = 44
        # predict[predict == 3] = 89
        # predict[predict == 4] = 143
        # predict[predict == 5] = 189
        # predict[predict == 6] = 255
        predict[predict == 0] = 52
        predict[predict == 1] = 123
        predict[predict == 2] = 41
        predict[predict == 3] = 46
        predict[predict == 4] = 255
        predict = torch.from_numpy(predict).unsqueeze(0).unsqueeze(0)
        predict = np.asarray(predict.cpu().numpy(), dtype=np.int8)
        predict = predict.transpose((0, 2, 3, 1))
        temp_predicts = [predict[i] for i in range(predict.shape[0])]
        result_list.extend(temp_predicts)
        torch.cuda.empty_cache()
    return result_list

def predict_multi_pth_single(model, image_path_list, sum_pic_num, current_col, pic_num_per_row, area_info):
    """
    多分类预测函数，一次预测一组，使用以pth结尾的模型
    Args:
        model: 模型权重
        image_path_list: 图片路径列表
        sum_pic_num: 图片总数
        current_col: 当前列
        pic_num_per_row: 每行有多少张图片
        area_info: 区域信息

    Returns:
        result_list: 预测结果list
    """

    image_list = []
    for img_path in image_path_list:
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), 3)
        img = np.array(img, dtype=np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image_list.append(img)
    length_image_list = len(image_list)
    batch_size = batchsize
    result_list = []
    # 如果length_image_list能整除batch_size
    if length_image_list // batch_size == 0:
        images = transform(image_list)
        with torch.no_grad():
            images = images.cuda()
            predicts = model.forward(images).cpu().numpy()
        predict = F.softmax(predicts, dim=1)
        predict = torch.argmax(predict, dim=1)
        predict = np.asarray(np.squeeze(predict.cpu().numpy()), dtype=np.int8)
        predict[predict == 1] = 15
        predict[predict == 2] = 44
        predict[predict == 3] = 89
        predict[predict == 4] = 143
        predict[predict == 5] = 189
        predict[predict == 6] = 255

        predict = torch.from_numpy(predict).unsqueeze(0).unsqueeze(0)
        predict = np.asarray(predict.cpu().numpy(), dtype=np.int8)
        predict = predict.transpose((0, 2, 3, 1))
        temp_predicts = [predict[i] for i in range(predict.shape[0])]
        result_list.extend(temp_predicts)
        return result_list
    # 如果length_image_list能整除batch_size
    if length_image_list % batch_size == 0:
        pic_index = length_image_list // batch_size
    else:
        pic_index = 1 + length_image_list // batch_size
    for i in range(pic_index):
        start = i * batch_size
        end = (i + 1) * batch_size if (i + 1) * batch_size <= length_image_list else length_image_list
        timagelist = image_list[start:end]
        images = transform(timagelist)
        with torch.no_grad():
            images = images.cuda()
            predicts = model.forward(images).cpu().numpy()
        # 激活函数
        predict = F.softmax(predicts, dim=1)
        # 取各维度最大值并合并为一维
        predict = torch.argmax(predict, dim=1)
        predict = np.asarray(np.squeeze(predict.cpu().numpy()), dtype=np.int8)
        # 定义不同类别颜色
        predict[predict == 1] = 15
        predict[predict == 2] = 44
        predict[predict == 3] = 89
        predict[predict == 4] = 143
        predict[predict == 5] = 189
        predict[predict == 6] = 255

        predict = torch.from_numpy(predict).unsqueeze(0).unsqueeze(0)
        predict = np.asarray(predict.cpu().numpy(), dtype=np.int8)
        predict = predict.transpose((0, 2, 3, 1))
        temp_predicts = [predict[i] for i in range(predict.shape[0])]
        result_list.extend(temp_predicts)
        torch.cuda.empty_cache()
    return result_list


def predict_image_segmentation(image_dir, model, sum_pic_num, pic_num_per_row, area_info, model_type, class_type):
    """
    影像分割预测入口函数
    Args:
        image_dir: 图片路径
        model: 模型权重
        sum_pic_num: 待预测图片总数
        pic_num_per_row: 每行有多少张图片
        area_info: 区域信息
        model_type: 模型类型，是th还是pth
        class_type: 预测类别，是binary二分类还是multi多分类

    Returns:
        result_dict: 预测结果list
    """
    namelist = os.listdir(image_dir)
    result_dict = {}
    name_dict = {}
    namelist = sorted(namelist, key=self_sort)
    current_col_index = '-1'
    temp_namelist = []
    col_index = ''
    for index, name in enumerate(namelist):
        # 取name被'-'分割后的第一个值,即列号
        col_index = name.split('-')[0]
        # 如果是第一张图，将current_col_index设为当前name_prefix
        if index == 0:
            current_col_index = col_index
        # 将拥有相同列号的存入temp_namelist
        if col_index == current_col_index:
            temp_namelist.append(name)
        # 当到达下一列时，保存当前列所有结果，并清空temp_namelist
        else:
            name_dict[current_col_index] = temp_namelist
            temp_namelist = []
            # 将当前图片存入新的temp_namelist中，开启新循环
            temp_namelist.append(name)
            current_col_index = col_index
    name_dict[col_index] = temp_namelist
    col = 1
    for key in name_dict.keys():
        temp_imagelist = []
        for name in name_dict[key]:
            a = os.path.join(image_dir, name)
            temp_imagelist.append(a)  # 存放图片路径
        # 预测当前图片组
        if model_type == "th":
            if class_type == "binary":
                temp_result_list = predict_binary_th_single(model, temp_imagelist, sum_pic_num, col,
                                                            pic_num_per_row, area_info)
            elif class_type == "multi":
                temp_result_list = predict_multi_th_single(model, temp_imagelist, sum_pic_num, col, pic_num_per_row,
                                                           area_info)
        else:  # model_type == "pth"
            if class_type == "binary":
                temp_result_list = predict_binary_pth_single(model, temp_imagelist, sum_pic_num, col,
                                                             pic_num_per_row, area_info)
            else:  # class_type == "multi"
                temp_result_list = predict_multi_pth_single(model, temp_imagelist, sum_pic_num, col,
                                                            pic_num_per_row, area_info)
        col += 1
        # 存入result_dict
        result_dict[key] = temp_result_list
    return result_dict

def Normalize(array):
    """
    数组归一化
    Args:
        array: 数组

    Returns:归一化结果

    """
    mx = np.nanmax(array)
    mn = np.nanmin(array)
    t = (array-mn)/(mx-mn)
    return t


def get_probability_by_connected_area(image):
    num_objects, labels = cv2.connectedComponents(image)
    if num_objects > 1:
        for i in range(num_objects - 1):
            label_i_data = np.where(labels == (i + 1), 1, 0)
            image_nonzero_i = image.ravel()[np.flatnonzero(label_i_data)]
            upper_quantile = np.percentile(image_nonzero_i, 90)
            lower_quantile = np.percentile(image_nonzero_i, 10)
            percentile_data = image_nonzero_i[image_nonzero_i < upper_quantile]
            percentile_data = percentile_data[percentile_data > lower_quantile]
            probability_i = np.uint8(np.mean(percentile_data))
            labels = np.where(labels == (i + 1), probability_i, labels)
    return labels


def get_probability_by_connected_area_julei(image,merge_result1):
    """
    按概率算
    Args:
        image:影像数据
        merge_result1:分区合并结果

    Returns:每个图斑的像素值
    """
    num_objects, labels1 = cv2.connectedComponents(image)
    if num_objects > 1:
        for i in range(num_objects - 1):
            label_i_data = np.where(labels1 == (i + 1), merge_result1, 0)
            image_nonzero_i = merge_result1[labels1 == (i + 1)]  # 使用与标签值匹配的位置在 image 中获取对应的值
            prob = Normalize(image_nonzero_i)
            # 示例二维数组
            data = prob.reshape((image_nonzero_i.shape[0], 1))
            if len(image_nonzero_i.tolist()) > 1:
                # 创建K-means模型并进行聚类
                kmeans = KMeans(n_clusters=2)
                kmeans.fit(data)
                # 获取每个数据点的所属聚类标签
                labels = kmeans.labels_
                df = pd.DataFrame({'data': data.flatten(), 'labels': labels})

                # 按照标签分组并计算平均值
                average_by_label = df.groupby('labels').mean()
                count_by_label = df.groupby('labels').size()
                # 找到平均值最大的标签
                max_average_label = average_by_label['data'].idxmax()
                # 获取平均值最大标签对应的数据数量
                count_of_max_average_label = count_by_label[max_average_label]
                #找到平均值最小的标签
                min_average_label = average_by_label['data'].idxmin()
                # 获取平均值最大标签对应的数据数量
                count_of_min_average_label = count_by_label[min_average_label]

                #获取最大值
                max_average_value = average_by_label.loc[max_average_label, 'data']
                min_average_value = average_by_label.loc[min_average_label, 'data']

                #根据加权平均值计算
                # pro_data = np.array(max_average_value,min_average_value)
                # weight = np.array(count_of_max_average_label,count_of_min_average_label)
                # weighted_average = np.average(pro_data, weights=weight)
                #根据平均值计算
                # mea = average_by_label['data'].mean()
                #根据上图面积
                max_rate = count_of_max_average_label/(count_of_max_average_label+count_of_min_average_label)
                if max_rate > cg.area_of_figure_above :
                    rate = np.uint8(max_average_value * 255)
                else:
                    rate = np.uint8(min_average_value * 255)
                labels1 = np.where(labels1 == (i + 1), rate, labels1)
            else:
                labels1 = np.where(labels1 == (i + 1), np.uint8(prob * 255), labels1)

    return labels1

def merge_all_grids_pieces_binary(predict_results, image_index, output_path, geo_info, band_data_type,
                                  overlap_size=(overlap_x, overlap_y)):
    """
    合并所有预测图片(单分类版）
    Args:
        predict_results: 图片预测结果集合
        image_index: 当前图片集合对应索引
        output_path: 输出路径
        geo_info: 原始影像的地理信息（坐标等）
        band_data_type: 波段数据类型
        overlap_size: 重叠带尺寸

    Returns:
        output_file: 预测结果文件路径
    """

    src_data = {}
    item_list = []
    for item in predict_results:
        # 每列的第一张图
        item_list.append(int(item))
        src_data[item] = predict_results[item][0]
        for image in range(1, len(predict_results[item])):
            if overlap_size[0] != 0:
                src_data[item] = np.concatenate((src_data[item][:int(-(overlap_size[0] // 2))],
                                                 predict_results[item][image][int(overlap_size[0] // 2):]),
                                                axis=0)  # 行连接
            else:
                src_data[item] = np.concatenate((src_data[item], predict_results[item][image]), axis=0)
    # 合并行
    merge_result = src_data[str(item_list[0])]
    for i in range(1, len(item_list)):
        if overlap_size[0] != 0:
            merge_result = np.concatenate((merge_result[:, :int(-(overlap_size[0] // 2))],
                                           src_data[str(item_list[i])][:, int((overlap_size[0] // 2)):]), axis=1)
        else:
            merge_result = np.concatenate((merge_result[:, :], src_data[str(item_list[i])][:, :]), axis=1)

    dst_name = str(image_index) + '.tif'
    output_file = os.path.join(output_path, dst_name)
    # 对merge_result进行reshape，转成最终的二维一张图结果
    merge_result = merge_result.reshape(merge_result.shape[0], merge_result.shape[1])

    if is_add_radio == '0':
        # ********不加概率************
        merge_result = np.where(merge_result > 0.5, 1, 0)
        # **********结束*************
    else:
        # ********加概率************
        merge_result1 = merge_result
        merge_result = np.where(merge_result > 0.5, merge_result, 0)
        merge_result = np.uint8(Normalize(merge_result) * 255)
        # merge_result = np.uint8(get_probability_by_connected_area(merge_result))
        merge_result = np.uint8(get_probability_by_connected_area_julei(merge_result,merge_result1))
        # **********结束*************

    # 创建输出数据流
    gtif_driver = gdal.GetDriverByName("GTiff")
    out_ds = gtif_driver.Create(output_file, merge_result.shape[1], merge_result.shape[0], 1, band_data_type)
    # 取第一张图的index
    new_index = 0
    for key in geo_info:
        new_index = int(key)
        break
    # 获取第一张图的坐标信息，并将其赋予合并的预测结果数据流out_ds
    out_ds.SetGeoTransform(geo_info[int(new_index)])
    out_ds.GetRasterBand(1).WriteArray(merge_result)
    # 将缓存写入磁盘
    out_ds.FlushCache()
    del out_ds
    return output_file

def merge_all_grids_pieces_multi(predict_results, image_index, output_path, geo_info, band_data_type,
                                 overlap_size=(overlap_x, overlap_y)):
    """
    合并所有预测图片(多分类版）
    Args:
        predict_results: 图片预测结果集合
        image_index: 当前图片集合对应索引
        output_path: 输出路径
        geo_info: 原始影像的地理信息（坐标等）
        band_data_type: 波段数据类型
        overlap_size: 重叠带尺寸

    Returns:
        output_file: 预测结果文件路径
    """
    src_data = {}
    item_list = []
    # 合并列

    for item in predict_results:
        # 每列的第一张图
        item_list.append(int(item))
        src_data[item] = predict_results[item][0]
        for image in range(1, len(predict_results[item])):
            src_data[item] = np.concatenate((src_data[item][:int(-(overlap_size[0] // 2))],
                                             predict_results[item][image][int(overlap_size[0] // 2):]), axis=0)

    # 合并行
    merge_result = src_data[str(item_list[0])]
    for i in range(1, len(item_list)):
        merge_result = np.concatenate((merge_result[:, :int(-(overlap_size[0] // 2))],
                                       src_data[str(item_list[i])][:, int((overlap_size[0] // 2)):]), axis=1)

    dst_name = str(image_index) + '.tif'
    output_file = os.path.join(output_path, dst_name)
    # 对merge_result进行reshape，转成最终的二维一张图结果
    merge_result = merge_result.reshape(merge_result.shape[0], merge_result.shape[1])
    gtif_driver = gdal.GetDriverByName("GTiff")
    out_ds = gtif_driver.Create(output_file, merge_result.shape[1], merge_result.shape[0], 3, band_data_type)
    new_index = 0
    for key in geo_info:
        new_index = int(key)
        break
    # 获取第一张图的坐标信息，并将其赋予合并的预测结果数据流out_ds
    out_ds.SetGeoTransform(geo_info[int(new_index)])
    out_ds.GetRasterBand(1).WriteArray(merge_result)
    # 将缓存写入磁盘
    out_ds.FlushCache()
    del out_ds
    return output_file


def copy_key_files(src_dir_path, to_dir_path, key):
    """
    复制所有含有关键词key的文件
    Args:
        src_dir_path: 复制来源文件夹
        to_dir_path:  复制目的地文件夹
        key: 关键词

    Returns:

    """
    file_list = os.listdir(src_dir_path)
    for file in file_list:
        # 获取文件全路径
        file_full_path = os.path.join(src_dir_path, file)
        # 如果出现关键词，则进行复制
        if key in file:
            shutil.copy(file_full_path, to_dir_path)


def tif_to_int8(input_path, output_path):
    """
    将tif转为int8格式
    Args:
        input_path: 原始tif路径
        output_path: 输出tif路径

    Returns:

    """
    img = cv2.imdecode(np.fromfile(input_path, dtype=np.uint8), 3)
    # 转成int8
    img = np.asarray(img, dtype=np.uint8)
    # 保存图片
    cv2.imencode('.tif', img)[1].tofile(output_path)


def segmentation_predict(tiff_file_input_path, output_path, model_path, img_name, fragment, building_regular,
                         model, base_progress, sum_progress, status_num_txt_path):
    """
    影像分割预测
    Args:
        tiff_file_input_path: tif文件输入路径
        output_path: 输出路径
        model_path: 模型路径
        img_name: 图片名称
        pixel: 图片分辨率
        fragment: 碎斑阈值
        building_regular:是否建筑物规则化
        region_field:地区字段
        is_add_rate: 是否添加概率
        probability_threshold: 概率阈值
        model:模型
        base_progress: 进度条开始值
        sum_progress: 进度条结束值
        status_num_txt_path: 进度更新文件路径
        folder_name: 当前正在处理的文件夹名字
    Returns:
        img_name: 图片名称
    """
    # 预测图片单元大小
    global img_name_tag
    img_name_tag = img_name
    logger.info("影像分割:开始进行{}@{}".format(tiff_file_input_path, img_name_tag))
    block_size = blocksize
    # 更新日志内容
    logger.info("影像分割:创建临时文件目录@{}".format(img_name_tag))
    # 创建临时文件目录2
    root_temp_path = common.create_ori_path(os.path.join(output_path, "temp"))
    if not os.path.exists(tiff_file_input_path):
        return False
    # update_status_bar(5)
    update_status_bar((base_progress + sum_progress * 0.1), status_num_txt_path)

    # 更新日志内容
    logger.info("影像分割:正在读取影像信息@{}".format(img_name_tag))
    # 分区信息计算（计算出有多少个分区），大图总列数，大图总行数，分区总列数，分区总行数
    logger.info("影像分割:计算影像分区信息@{}".format(img_name_tag))
    split_info, sum_col, sum_row, split_col, split_row = tiff_regions_meta_info_precalculating(tiff_file_input_path,
                                                                                               block_size,
                                                                                               root_temp_path)
    # update_status_bar(10)
    update_status_bar((base_progress + sum_progress * 0.2), status_num_txt_path)

    regions_count = len(split_info)
    # 加载模型
    logger.info("加载模型:加载模型@{}".format(img_name_tag))
    # dlinknet_model = get_dinknet(model_path)
    dlinknet_model = model
    # update_status_bar(15)
    update_status_bar((base_progress + sum_progress * 0.4), status_num_txt_path)

    logger.info("加载模型:读取影像信息@{}".format(img_name_tag))
    # 面向影像文件的分区、切片、预测、每个分区切片的合并
    logger.info("影像分割预测:开始影像预测流程@{}".format(img_name_tag))
    splitregions_splitpieces_predict_picecesmerge_core(block_size, tiff_file_input_path, dlinknet_model,
                                                       model_path, output_path, regions_count,
                                                       root_temp_path, split_info, sum_col, sum_row, img_name)
    # update_status_bar(80)
    update_status_bar((base_progress + sum_progress * 0.6), status_num_txt_path)
    # GIS后处理的核心逻辑部分，通过python27 os命令的方式运行
    logger.info("栅格转矢量:进行预测结果后处理@{}".format(img_name_tag))
    # update_status_bar(95)
    global SPLIT_PREDICT_COUNT
    region_merge_shp_gis_optimize_core(fragment, output_path, regions_count, img_name, building_regular)
    # 更新状态栏
    update_status_bar((base_progress + sum_progress * 1), status_num_txt_path)
    # 删除temp根目录
    logger.info("栅格转矢量:正在删除临时根目录文件夹@{}".format(img_name_tag))
    shutil.rmtree(root_temp_path)
    logger.info("预测完成:@{}".format(img_name_tag))
    return img_name

def add_field_and_sim(inputpath,prjtag,output_path,building_regular):
    # if region_field != '':
    #     logger.info("栅格转矢量:开始添加行政区字段@{}".format(img_name_tag))
    #     add_XZQ_fields(inputpath, region_field)
    # 是否进行规则化，没有坐标系的情况下不进行规则化操作
    if building_regular == '1' and os.path.exists(inputpath) and prjtag != 3:
        logger.info("栅格转矢量:开始进行规则化操作@{}".format(img_name_tag))
        tempath = os.path.join(output_path, "shp", 'temp')
        sim_building_path = os.path.join(output_path, "shp","{}_sim.shp".format(os.path.splitext(os.path.basename(inputpath))[0]))
        if prjtag == 1:
            sim_main(inputpath, sim_building_path, tempath, 1)
        else:
            sim_main(inputpath, sim_building_path, tempath, 0)

def region_merge_shp_gis_optimize_core(fragment, output_path, regions_count, img_name, building_regular):
    """
    内核2：预测结果的合并、简化、转shp
    Args:
        fragment: 碎斑阈值，小于此阈值的碎斑会被剔除
        output_path: 输出路径
        regions_count: 分区总数
        img_name: 图片名称
        building_regular:是否建筑物规则化
        region_field:地区字段
        probability_threshold:概率阈值
    Returns:

    """
    global img_name_tag,is_add_radio
    common.create_path(output_path, "shp")
    tif_path = os.path.join(output_path, "tif")
    vector_path = os.path.join(output_path, "shp", img_name + ".shp")
    # 进行栅格合并以及shp转换
    prjtag,file_pathlist = merge_tif_and_convert_to_shp(tif_path, vector_path, img_name, fragment, regions_count)
    for i in file_pathlist:
        add_field_and_sim(i, prjtag, output_path, building_regular)
    # # 判断是否添加字段,行政区shp去掉
    # if region_field != '':
    #     add_XZQ_fields(vector_path, region_field)
    # # 是否进行规则化
    # if building_regular == '1' and os.path.exists(vector_path) and prjtag != 3:
    #     sim_building_path = os.path.join(output_path, "shp", img_name + "_sim.shp")
    #     tempath = os.path.join(output_path, "shp", 'temp')
    #     sim_main(vector_path, sim_building_path, tempath, 0)
    # return vector_path


def splitregions_splitpieces_predict_picecesmerge_core(block_size, tiff_file_input_path, dlinknet_model, model_path,
                                                       output_path, regions_count, root_temp_path,split_info, sum_col,
                                                       sum_row, img_name):
    """
    内核1：核心的分区、切片、预测、切片合并
    Args:
        block_size: 切片尺寸
        tiff_file_input_path: 原始待预测的TIFF文件所在路径
        dlinknet_model: 预测模型
        model_path: 预测模型的文件路径
        output_path: 输出路径
        regions_count: 当前区域号
        root_temp_path: temp根目录路径
        split_info: 分区信息list
        sum_col: 总列数
        sum_row: 总行数
        img_name: 图片名称

    Returns:

    """
    # 将当前处理区域索引置零
    current_region_index = 0
    # 创建保存预测时间的字典
    predict_time = {}
    # 计算分区总数
    sum_count_of_split_region = len(split_info)
    # 计算分区预测进度单元，即每个分区的预测流程占总流程多少
    SPLIT_STATUS_BAR_UNIT = int(65 / sum_count_of_split_region)
    # 开始分区处理影像
    parm_list = []
    time_start = time.time()
    for region_id in split_info:
        parm = []
        parm.append(block_size)
        parm.append(current_region_index)
        parm.append(dlinknet_model)
        parm.append(img_name)
        parm.append(model_path)
        parm.append(output_path)
        parm.append(predict_time)
        parm.append(region_id)
        parm.append(regions_count)
        parm.append(root_temp_path)
        parm.append(split_info)
        parm.append(sum_col)
        parm.append(sum_row)
        parm.append(tiff_file_input_path)
        parm.append(SPLIT_STATUS_BAR_UNIT)
        parm_list.append(parm)
        current_region_index += 1
    pool = threadpool.ThreadPool(poolnum)
    reqs = threadpool.makeRequests(split_predict, parm_list)
    for req in reqs:
        pool.putRequest(req)
    pool.wait()
    global SPLIT_PREDICT_COUNT
    while True:
        if SPLIT_PREDICT_COUNT >= len(split_info):
            break
    time_end = time.time()
    time_cost = time_end - time_start
    print('time cost:', time_cost)


def split_predict(parm):
    global img_name_tag
    block_size = parm[0]
    current_region_index = parm[1]
    dlinknet_model = parm[2]
    img_name = parm[3]
    model_path = parm[4]
    output_path = parm[5]
    predict_time = parm[6]
    region_id = parm[7]
    regions_count = parm[8]
    root_temp_path = parm[9]
    split_info = parm[10]
    sum_col = parm[11]
    sum_row = parm[12]
    tiff_file_input_path = parm[13]
    SPLIT_STATUS_BAR_UNIT = parm[14]
    current_region = split_info[region_id]
    current_region_index = current_region_index + 1
    logger.info('影像分割预测:'+" " + region_id + "区" +"@{}".format(img_name_tag))
    # 用字符串存储当前处理区域索引和总区域数，用于在log中添加信息
    # message_str = "(第" + str(current_region_index) + "/" + str(regions_count) + "区)" + "@{}".format(img_name_tag)
    message_str = ""
    # 如果分区了，会在图片名后加上索引号
    if len(split_info) > 1:
        current_img_name = img_name + "_" + region_id
    else:
        current_img_name = img_name
    logger.info("影像分割预测:读取分区影像信息@{}".format(img_name_tag))
    image_dataset, geo_trans, srs, pad_xsize, pad_ysize, left_top, right_bottom, row, col, band_data_type, geo_info = block_img_msg_over(
        tiff_file_input_path, block_size, current_region["start_col"], current_region["start_row"],
        current_region["end_col"],
        current_region["end_row"])
    # 百分比写入log
    # 记录分区角点坐标
    left_top = current_region["start"]
    right_bottom = current_region["end"]
    # 创建存储当前区域过程文件的temp文件夹
    region_temp_path = common.create_path(root_temp_path, region_id)
    # 创建影像切片存储文件夹
    pieces_path = common.create_path(region_temp_path, "pieces")
    logger.info("影像分割预测:开始切割影像@{}".format(img_name_tag))
    # 运行切割影像的代码
    split_img(image_dataset, pieces_path, block_size, pad_xsize, pad_ysize, sum_row, sum_col,
              current_region["start_col"], current_region["start_row"],
              current_region["end_col"], current_region["end_row"], message_str, overlap_size=(overlap_x, overlap_y))
    logger.info("影像分割预测:切割完成@{}".format(img_name_tag))
    # 预测单片照片结果的存放位置
    pieces_predict_path = common.create_path(region_temp_path, "pieces_predict")
    # 预测单片照片合并后结果的存放位置
    pieces_predict_cls_merge_path = common.create_path(pieces_predict_path, "merge_tif")
    # 记录预测开始时间
    time_begin = time.time()
    # 创建当前分区预测结果存储路径
    pieces_predict_cls_path = common.create_path(pieces_predict_cls_merge_path, current_img_name)
    # 计算当前分区总切片数
    sum_pics = (current_region["end_row"] - current_region["start_row"] + 1) * (
            current_region["end_col"] - current_region["start_col"] + 1)
    # 开始预测，区分th模型文件和pth模型文件
    model_type = "th"
    class_type = "binary"
    if model_path.split(".")[1] == "pth":
        model_type = "pth"
    if os.path.basename(model_path).find("multi") != -1 or os.path.basename(model_path).find("Multi") != -1:
        class_type = "multi"
    # 开始预测
    logger.info("影像分割预测:开始预测@{}".format(img_name_tag))
    predict_results = predict_image_segmentation(pieces_path, dlinknet_model, sum_pics,
                                                 current_region["end_row"] - current_region["start_row"] + 1,
                                                 message_str,
                                                 model_type, class_type)
    # 多个切片预测结果的合并
    logger.info("影像分割预测:正在合并预测结果@{}".format(img_name_tag))
    if class_type == "binary":
        # 二分类
        predict_result_tif_path = merge_all_grids_pieces_binary(predict_results, "0", pieces_predict_cls_path,
                                                                geo_info, band_data_type)
    else:
        # 多分类
        predict_result_tif_path = merge_all_grids_pieces_multi(predict_results, "0", pieces_predict_cls_path,
                                                               geo_info, band_data_type)
    # 记录预测及合并时间
    time_end = time.time()
    # 记录预测总时间
    predict_time[current_img_name] = common.time_interval(time_end, time_begin)
    logger.info("影像分割预测:预测及合并完成，共耗时" + predict_time[current_img_name] + "" + "@{}".format(img_name_tag))
    # 创建保存预测结果tif的文件夹路径
    result_tif_path = common.create_path(output_path, "tif")
    # 生成预测结果tif的文件完整保存路径
    registration_path = os.path.join(result_tif_path, current_img_name + "_reg.tif")
    # 将接边偏移量设为0
    pad_ysize = 0
    pad_xsize = 0
    # 处理并输出结果tif
    common.registration(predict_result_tif_path, registration_path, left_top, right_bottom, pad_ysize,
                        pad_xsize, srs)
    # 生成用于展示的int8结果图片
    # 如果未经分区，则将当前区的预测结果转为int8，用于展示
    # if current_region_index == 1:
    #     logger.info("正在将预测结果转为8位")
    #     tif_to_int8(registration_path, os.path.join(result_tif_path, current_img_name + "int8.tif"))
    logger.info("影像分割预测:正在删除当前分区中的临时文件夹@{}".format(img_name_tag))
    # 清除每个小分区的temp中所有的内容
    shutil.rmtree(region_temp_path)
    global SPLIT_PREDICT_COUNT
    SPLIT_PREDICT_COUNT += 1

def update_status_bar(num,status_num_txt_path):
    """
    更新进度条进度百分比,写入log
    Args:
        num: 进度百分比
        status_num_txt_path:进度更新文件路径
    Returns:

    """
    global STATUS_BAR_PROGRESS
    STATUS_BAR_PROGRESS = num
    with open(status_num_txt_path, 'w+') as f:
        f.write(str(int(STATUS_BAR_PROGRESS)))



if __name__ == '__main__':
    work_dir = work_dir
    # tiff_file_input_path = r'E:\geo_ai_server\c#_test_data\remote_images\in_101\in_101.tif'
    tiff_file_input_path = r'E:\geo_ai_server\c#_test_data\remote_images\in_10.tif'
    output_path = r'E:\geo_ai_server\c#_test_data\result\6'
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    model_path = r'E:\geo_ai_server\c#_test_data\models\DLinkNet_ResNet101_road_JS_1m_256_20k_230620.th'
    img_name = 'ea'
    pixel = '0.1'
    fragment = '0'
    building_regular = '1'
    region_field = '1'
    is_add_radio = '1'
    # status_num_txt_path = r'E:\geo_ai_server\gtrs_cs_server\logs\status_num\192-168-60-20_status.txt'
    status_num_txt_path = r'E:\geo_ai_server\gtrs_cs_server\logs\status_num\192-168-60-20_status.txt'
    folder_name = '12'
    model = get_dinknet(model_path)
    probability_threshold = '0.1'
    segmentation_predict(tiff_file_input_path, output_path, model_path, img_name,  fragment, building_regular, model, 0, 100, status_num_txt_path)