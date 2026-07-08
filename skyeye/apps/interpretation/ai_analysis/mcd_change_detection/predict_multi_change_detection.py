# -*- coding: UTF-8 -*-
import sys,os
CURRENTDIR = os.path.dirname(os.path.abspath(__file__))
WORKDIR = os.path.dirname(CURRENTDIR)
sys.path.insert(0, CURRENTDIR)
sys.path.insert(0, WORKDIR)
sys.path.insert(0, os.path.join(WORKDIR,'utils'))
import shutil
try:
    import gdal, osr
except:
    from osgeo import gdal, osr
import numpy as np
import torch
from osgeo import gdal
import time
from math import *
import torch.nn.functional as F
from functools import partial
from PIL import Image
import torchvision.transforms as transforms
import ai_config as cg
import utils.common as common
import threadpool
import warnings
import torch.autograd
from torch.utils.data import DataLoader
from mcd_change_detection.datasets import RS_ST as RS
from mcd_change_detection.models.SSCDl import SSCDl as Net
# from mcd_change_detection.models.BiSRNet_riverline import BiSRNet as Net
import geopandas as gpd
from utils.merge_tiff_and_generate_shp_mcd import merge_multi_regions_raster_and_tif_to_shp
from utils.add_region_fields import add_XZQ_fields
from utils.sim_building import sim_main
# 忽略 FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
DATA_NAME = 'ST'
logger = cg.logger
# 设置工作路径与util路径
work_dir = cg.PROJECT_PATH
batchsize = cg.batch_size
blocksize = cg.block_size
poolnum = cg.pool_num
util_dir = os.path.join(work_dir, 'utils')
# # 初始化日志
# 静态文件路径设置
nonlinearity = partial(F.relu, inplace=True)
Image.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
# 每个分区所占预测进度百分比
SPLIT_STATUS_BAR_UNIT = 0
# 当前处理进度
STATUS_BAR_PROGRESS = 0
SPLIT_PREDICT_COUNT = 0
img_name_tag = ''
overlap_x = cg.overlap_x
overlap_y = cg.overlap_y


def self_sort(name_list):
    """
    生成list的排序关键词
    Args:
        name_list: 待排序list

    Returns:
        key: 新生成的关键词
    """

    x1 = int(name_list.split('-')[0])
    x2 = int(name_list.split('-')[1].split('.')[0])
    key = x1 * 1000000 + x2
    return key

def predict_change_detection_pieces(net,pred_loader):
    """
    多分类预测
    Args:
        net: 模型
        pred_loader: 数据加载

    Returns:

    """
    temp_result_list1, temp_result_list2 = [],[]
    temp_predicts_A,temp_predicts_B = [],[]
    for vi, data in enumerate(pred_loader):
        imgs_A, imgs_B = data
        imgs_A = imgs_A.cuda().float()
        imgs_B = imgs_B.cuda().float()
        with torch.no_grad():
            out_change, outputs_A, outputs_B = net(imgs_A, imgs_B)
            out_change = F.sigmoid(out_change)
        outputs_A = outputs_A.cpu().detach()
        outputs_B = outputs_B.cpu().detach()
        change_mask = out_change.cpu().detach() > 0.5
        change_mask = change_mask.squeeze()
        pred_A = torch.argmax(outputs_A, dim=1).squeeze()
        pred_B = torch.argmax(outputs_B, dim=1).squeeze()
        pred_A = (pred_A * change_mask.long()).numpy()
        pred_B = (pred_B * change_mask.long()).numpy()
        predictA = np.expand_dims(pred_A, axis=-1)
        predictB = np.expand_dims(pred_B, axis=-1)
        temp_predicts_A.append(predictA)
        temp_predicts_B.append(predictB)
    temp_result_list1.extend(temp_predicts_A)
    temp_result_list2.extend(temp_predicts_B)
    return temp_result_list1,temp_result_list2


def predict_image_change_detection(image_dir1, image_dir2,
                                   change_detection_model):
    """
    预测
    Args:
        image_dir1: 第一时相图片路径
        image_dir2: 第二时相图片路径
        change_detection_model: 模型权重

    Returns:

    """
    namelist = os.listdir(image_dir1)
    result_dict1 = {}
    result_dict2 = {}
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
        temp_image_list1 = []
        temp_image_list2 = []
        for name in name_dict[key]:
            # 对双时相图片都用cv2读取，并存入temp_image_list中
            temp_image_list1.append(os.path.join(image_dir1, name))
            temp_image_list2.append(os.path.join(image_dir2, name))

        pred_set = RS.Data_test1(temp_image_list1, temp_image_list2)
        pred_loader = DataLoader(pred_set, batch_size=1)
        temp_result_list1,temp_result_list2 = predict_change_detection_pieces(change_detection_model,pred_loader)
        col += 1
        # 存入result_dict
        result_dict1[key] = temp_result_list1
        result_dict2[key] = temp_result_list2
        torch.cuda.empty_cache()
    return result_dict1,result_dict2


def merge_all_grids_pieces(predict_results, image_index, output_path, geo_info, band_data_type,overlap_size=(overlap_x, overlap_y)):
    """
    合并所有预测图片
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
                                                 predict_results[item][image][int(overlap_size[0] // 2):]), axis=0)  #行连接
            else:
                src_data[item] = np.concatenate((src_data[item],predict_results[item][image]), axis=0)
    # 合并行
    merge_result = src_data[str(item_list[0])]
    for i in range(1, len(item_list)):
        if overlap_size[0] != 0:
            merge_result = np.concatenate((merge_result[:, :int(-(overlap_size[0] // 2))],
                                       src_data[str(item_list[i])][:, int((overlap_size[0] // 2)):]), axis=1)
        else:
            merge_result = np.concatenate((merge_result[:,:],src_data[str(item_list[i])][:, :]), axis=1)

    dst_name = str(image_index) + '.tif'
    output_file = os.path.join(output_path, dst_name)
    # 对merge_result进行reshape，转成最终的二维一张图结果
    merge_result = merge_result.reshape(merge_result.shape[0], merge_result.shape[1])

    # 创建输出数据流
    gtif_driver = gdal.GetDriverByName("GTiff")
    out_ds = gtif_driver.Create(output_file, merge_result.shape[1], merge_result.shape[0], 1, gdal.GDT_Int32)
    # 取第一张图的index
    for key in geo_info:
        new_index = int(key)
        break

    # 获取第一张图的坐标信息，并将其赋予合并的预测结果数据流out_ds
    out_ds.SetGeoTransform(geo_info[int(new_index)])
    merge_result = RS.Index2Color(merge_result)
    #只写入第三波段
    out_ds.GetRasterBand(1).WriteArray(merge_result[:, :, 2])
    # 将缓存写入磁盘
    out_ds.FlushCache()
    del out_ds
    return output_file


def transform():
    """
    对图片进行批量标准化
    Returns:

    """
    transform_list = []
    transform_list += [transforms.ToTensor()]
    transform_list += [transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]
    return transforms.Compose(transform_list)


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

    if overlap_col <=0:
        overlap_col = 1
    if overlap_row <=0:
        overlap_row = 1

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

    Returns:

    """

    # 读取原图中的每个波段
    image_bound1 = image_dataset.GetRasterBand(1)
    image_bound2 = image_dataset.GetRasterBand(2)
    image_bound3 = image_dataset.GetRasterBand(3)

    col_pad_array = np.zeros((block_size, pad_xsize))

    row_pad_array = np.zeros((pad_ysize, block_size))

    num_col = end_col - start_col + 1
    num_row = end_row - start_row + 1
    sum_pic = str(num_col * num_row)
    count = 0
    for i in range(start_col, end_col + 1):
        offset_x = i * (block_size - overlap_size[1])
        for j in range(start_row, end_row + 1):
            count += 1
            offset_y = j * (block_size - overlap_size[0])

            if (j == sum_row - 1) and (i == sum_col - 1):
                out_band1 = image_bound1.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size - pad_ysize)
                out_band2 = image_bound2.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size - pad_ysize)
                out_band3 = image_bound3.ReadAsArray(offset_x, offset_y, block_size - pad_xsize,
                                                     block_size - pad_ysize)

                row_pad_array = np.zeros((pad_ysize, block_size - pad_xsize))

                if out_band1 is None or out_band2 is None or out_band3 is None:
                    continue

                out_band1 = np.concatenate((out_band1, row_pad_array), axis=0)
                out_band2 = np.concatenate((out_band2, row_pad_array), axis=0)
                out_band3 = np.concatenate((out_band3, row_pad_array), axis=0)

                out_band1 = np.concatenate((out_band1, col_pad_array), axis=1)
                out_band2 = np.concatenate((out_band2, col_pad_array), axis=1)
                out_band3 = np.concatenate((out_band3, col_pad_array), axis=1)

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
            # 写入目标文件
            out_ds.GetRasterBand(1).WriteArray(out_band1)
            out_ds.GetRasterBand(2).WriteArray(out_band2)
            out_ds.GetRasterBand(3).WriteArray(out_band3)
            # 将缓存写入磁盘
            out_ds.FlushCache()
            del out_ds


def mcdchange_predict(prev_path, next_path, output_path, fragment, building_regular,
                      mcd_model, base_progress, sum_progress, status_num_txt_path, folder_name):
    """

    Args:
        prev_path: 前景地址
        next_path: 后景地址
        output_path: 输出结果路径
        pixel: 影像分辨率
        fragment: 图斑阈值
        building_regular:是否规则化
        region_field: 行政区字段
        mcd_model:多分类变化检测模型
        base_progress:基础进度
        sum_progress:总进度
        status_num_txt_path:进度更新文件
        folder_name:文件夹

    Returns:

    """
    global img_name_tag
    img_name_tag = folder_name
    # 切片小图尺寸
    block_size = blocksize
    # 从opt中获取参数
    prev_path = prev_path  # 第一张图的路径
    next_path = next_path  # 第二张图的路径
    output_path = output_path  # 输出结果保存文件夹路径
    img_name = os.path.basename(prev_path).split(".")[0]  # 图片名称，默认使用第一张图的名称
    img_name_next = os.path.basename(next_path).split(".")[0]  # 图片名称，默认使用第一张图的名称
    fragment = fragment  # 碎斑阈值
    building_regular = building_regular
    # 创建临时文件目录
    logger.info("变化检测开始:创建临时文件目录@{}".format(img_name_tag))
    root_temp_path = common.create_ori_path(os.path.join(output_path, "temp"))
    update_status_bar((base_progress+sum_progress*0.1),status_num_txt_path)
    # 分别读取两张影像的信息
    logger.info("计算影像分区信息:计算影像分区信息@{}".format(img_name_tag))
    split_info, sum_col, sum_row, split_col, split_row = tiff_regions_meta_info_precalculating(prev_path,
                                                                                               block_size,
                                                                                               root_temp_path)
    split_info2, sum_col2, sum_row2, split_col2, split_row2 = tiff_regions_meta_info_precalculating(next_path,
                                                                                                    block_size,
                                                                                                    root_temp_path)
    update_status_bar((base_progress+sum_progress*0.2),status_num_txt_path)
    # 获取分区总数
    regions_count = len(split_info)

    # 面向影像文件的分区、切片、预测、每个分区切片的合并
    logger.info("分区检测:开始进行每个分区预测@{}".format(img_name_tag))
    splitregions_splitpieces_predict_picecesmerge_core(block_size, prev_path, next_path, img_name,
                                                       output_path, regions_count,
                                                       root_temp_path, split_info, sum_col, sum_col2, sum_row,
                                                       sum_row2, mcd_model)
    update_status_bar((base_progress+sum_progress*0.8),status_num_txt_path)
    # GIS后处理的核心逻辑部分，通过python27 os命令的方式运行
    logger.info("栅格转矢量:分区预测结束@{}".format(img_name_tag))
    result_path = region_merge_shp_gis_optimize_core(fragment, img_name,img_name_next, output_path, regions_count, building_regular)
    update_status_bar((base_progress+sum_progress*1),status_num_txt_path)
    logger.info("栅格转矢量:正在删除临时文件夹@{}".format(img_name_tag))
    shutil.rmtree(root_temp_path)
    logger.info("预测完成:@{}".format(img_name_tag))
    return result_path


def splitregions_splitpieces_predict_picecesmerge_core(block_size, prev_path, next_path, img_name,
                                                       output_path, regions_count, root_temp_path,
                                                       split_info, sum_col, sum_col2, sum_row, sum_row2, mcd_model):
    """
    内核1：核心的分区、切片、预测、切片合并
    Args:
        block_size: 切片尺寸
        prev_path: 第一张原始待预测的图像文件所在路径
        next_path: 第二张原始待预测的图像文件所在路径
        img_name: 第一张原始待预测的图像名称，即预测结果名称
        output_path: 输出路径
        regions_count: 当前区域号
        root_temp_path: temp根目录路径
        split_info: 分区信息list
        sum_col: 第一张图总列数
        sum_col2: 第二张图总列数
        sum_row: 第一张图总行数
        sum_row2: 第二张图总行数
        mcd_model:多分类模型

    Returns:

    """
    # 将当前处理区域索引置零
    current_region_index = 0
    # 计算分区总数
    sum_count_of_split_region = len(split_info)
    # 创建保存预测时间的字典
    predict_time = {}
    # 计算分区预测进度单元，即每个分区的预测流程占总流程多少
    SPLIT_STATUS_BAR_UNIT = int(70 / sum_count_of_split_region)
    # 开始生成模型
    parm_list = []
    # 开始分区处理影像
    for reigon_id in split_info:
        model = []
        parm = []
        parm.append(SPLIT_STATUS_BAR_UNIT)
        parm.append(block_size)
        parm.append(current_region_index)
        parm.append(img_name)
        parm.append(model)
        parm.append(next_path)
        parm.append(mcd_model)
        parm.append(output_path)
        parm.append(predict_time)
        parm.append(prev_path)
        parm.append(regions_count)
        parm.append(reigon_id)
        parm.append(root_temp_path)
        parm.append(split_info)
        parm.append(sum_col)
        parm.append(sum_col2)
        parm.append(sum_row)
        parm.append(sum_row2)
        parm_list.append(parm)
        current_region_index += 1
        # multi_thresding_method(parm)
    pool = threadpool.ThreadPool(poolnum)
    reqs = threadpool.makeRequests(multi_thresding_method, parm_list)
    for req in reqs:
        pool.putRequest(req)
    pool.wait()

    global SPLIT_PREDICT_COUNT
    while True:
        if SPLIT_PREDICT_COUNT >= len(split_info):
            break

def multi_thresding_method(parm):
    global img_name_tag
    SPLIT_STATUS_BAR_UNIT = parm[0]
    block_size = parm[1]
    current_region_index = parm[2]
    img_name = parm[3]
    model2 = parm[4]
    next_path = parm[5]
    change_detection_model = parm[6]
    output_path = parm[7]
    predict_time = parm[8]
    prev_path = parm[9]
    regions_count = parm[10]
    reigon_id = parm[11]
    root_temp_path = parm[12]
    split_info = parm[13]
    sum_col = parm[14]
    sum_col2 = parm[15]
    sum_row = parm[16]
    sum_row2 = parm[17]

    area = split_info[reigon_id]
    current_region_index = current_region_index + 1
    logger.info('分区检测:'+"开始处理第" + reigon_id + "区" +"@{}".format(img_name_tag))
    message_str = ""
    img_name2 = img_name
    if len(split_info) > 1:
        img_name2 = img_name + "_" + reigon_id
    logger.info("分区检测:读取分区影像信息@{}".format(img_name_tag))
    image_dataset, geo_trans, srs, pad_xsize, pad_ysize, left_top, right_bottom, row, col, band_data_type, geo_info = block_img_msg_over(
        prev_path, block_size, area["start_col"], area["start_row"], area["end_col"], area["end_row"])
    image_dataset2, geo_trans2, srs2, pad_xsize2, pad_ysize2, left_top2, right_bottom2, row2, col2, img_data_type2, geo_info2 = block_img_msg_over(
        next_path, block_size, area["start_col"], area["start_row"], area["end_col"], area["end_row"])
    # 记录分区角点坐标
    left_top = area["start"]
    right_bottom = area["end"]
    # 创建存储当前区域过程文件的temp文件夹
    region_temp_path = common.create_path(root_temp_path, reigon_id)
    # 创建影像切片存储文件夹
    pieces_path = common.create_path(region_temp_path, "pieces")
    pieces_path2 = common.create_path(region_temp_path, "pieces2")
    logger.info('分区检测:开始切割影像' + reigon_id + "区" + "@{}".format(img_name_tag))
    # 开始切割影像
    split_img(image_dataset, pieces_path, block_size, pad_xsize, pad_ysize, sum_row, sum_col,
              area["start_col"], area["start_row"],
              area["end_col"], area["end_row"], message_str)
    split_img(image_dataset2, pieces_path2, block_size, pad_xsize2, pad_ysize2, sum_row2, sum_col2,
              area["start_col"], area["start_row"],
              area["end_col"], area["end_row"], message_str)
    logger.info("分区检测:切割完成@{}".format(img_name_tag))
    # 预测影像切片结果的存放位置
    pieces_predict_path = common.create_path(region_temp_path, "pieces_predict")
    # 预测影像切片合并后结果的存放位置
    pieces_predict_cls_merge_path = common.create_path(pieces_predict_path, "merge_tif")
    # 记录预测开始时间
    time_begin = time.time()
    # 创建当前分区预测结果存储路径
    pieces_predict_cls_path = common.create_path(pieces_predict_cls_merge_path, img_name2)
    # 计算当前分区总切片数
    sum_pics = (area["end_row"] - area["start_row"] + 1) * (
            area["end_col"] - area["start_col"] + 1)
    # 预测影像
    logger.info("分区检测:开始预测{}@{}".format(reigon_id + "区",img_name_tag))
    predict_results1, predict_results2 = predict_image_change_detection(pieces_path, pieces_path2, change_detection_model)
    # 多个切片预测结果的合并
    logger.info("分区检测:正在合并预测结果{}@{}".format(reigon_id + "区",img_name_tag))
    predict_result_tif_path = merge_all_grids_pieces(predict_results1, "pre", pieces_predict_cls_path, geo_info,
                                                     band_data_type)
    predict_result_tif_path2 = merge_all_grids_pieces(predict_results2, "next", pieces_predict_cls_path, geo_info,
                                                     band_data_type)
    # 记录预测及合并时间
    time_end = time.time()
    # 记录预测总时间
    predict_time[img_name2] = common.time_interval(time_end, time_begin)
    logger.info("分区检测:预测及合并完成，共耗时" + predict_time[img_name2] + ""+"@{}".format(img_name_tag))
    # 创建保存预测结果tif的文件夹路径
    result_tif_path = common.create_path(output_path, "tif")
    # 生成预测结果tif的文件完整保存路径
    registration_path = os.path.join(result_tif_path, img_name2 + "_reg1.tif")
    registration_path2 = os.path.join(result_tif_path, img_name2 + "_reg2.tif")
    # 将接边偏移量设为0
    pad_ysize = 0
    pad_xsize = 0
    # 处理并输出结果tif
    common.registration(predict_result_tif_path, registration_path, left_top, right_bottom, pad_ysize,
                        pad_xsize, srs)
    common.registration(predict_result_tif_path2, registration_path2, left_top, right_bottom, pad_ysize,
                        pad_xsize, srs)

    # 如果未经分区，则将当前区的预测结果转为int8，用于展示

    logger.info("分区检测:正在删除当前分区中的临时文件夹@{}".format(img_name_tag))
    # 清除每个小分区的temp中所有的内容
    global SPLIT_PREDICT_COUNT
    SPLIT_PREDICT_COUNT += 1

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

def region_merge_shp_gis_optimize_core(fragment, img_name,img_name_next, output_path, regions_count, building_regular):
    """
    内核2：预测结果的合并、简化、转shp
    Args:
        fragment: 碎斑阈值
        img_name: 图片名
        img_name_next:下一个影像名称
        output_path: 输出路径
        regions_count: 分区总数
        building_regular:是否建筑物规则化
        region_field:地区字段
    Returns:

    """
    global img_name_tag
    common.create_path(output_path, "shp")
    tif_path = os.path.join(output_path, "tif")
    result_path = os.path.join(output_path, 'shp',img_name + "_mcd_result.shp")
    #进行栅格合并以及shp转换
    prjtag,file_pathlist = merge_multi_regions_raster_and_tif_to_shp(tif_path, result_path, img_name, fragment, regions_count,'1','2')
    for i in file_pathlist:
        add_field_and_sim(i, prjtag, output_path, building_regular)

    # #判断是否添加字段,行政区shp去掉
    # if region_field != '':
    #     add_XZQ_fields(result_path,region_field)
    # #是否进行规则化
    # if building_regular == '1' and os.path.exists(result_path) and prjtag != 3:
    #     sim_building_path = os.path.join(output_path, "shp", img_name + "_sim.shp")
    #     tempath = os.path.join(output_path, "shp",'temp')
    #     sim_main(result_path, sim_building_path, tempath, 0)
    return file_pathlist

def update_status_bar(num,status_num_txt_path):
    """
    更新进度条进度百分比,写入log
    Args:
        num: 进度百分比

    Returns:

    """
    global STATUS_BAR_PROGRESS
    STATUS_BAR_PROGRESS = num
    with open(status_num_txt_path, 'w+') as f:
        f.write(str(int(STATUS_BAR_PROGRESS)))

def start_model(model_path):
    """
    起模型
    Args:
        model_path:

    Returns:

    """
    net = Net(3, RS.num_classes).cuda()
    net.load_state_dict(torch.load(model_path))
    net.eval()
    return net


if __name__ == '__main__':

    model_path = r'C:\Users\Administrator\Desktop\model\BiSRNet_50e_mIoU81.62_Sek49.08_Fscd79.51_OA88.53.pth'
    model_change_detection = start_model(model_path)

    prev_path = r'E:\geo_ai_server\c#_test_data\remote_images\1\R36T_10240_11264_7168_8192_A.tif'
    next_path = r'E:\geo_ai_server\c#_test_data\remote_images\1\R36T_10240_11264_7168_8192_B.tif'
    output_path = r'E:\geo_ai_server\c#_test_data\result\5'
    pixel = '0.1'
    fragment = '0'
    building_regular = '1'
    region_field = '1'
    status_num_txt_path = r'E:\geo_ai_server\gtrs_cs_server\logs\status_num\192-168-60-20_status.txt'
    folder_name = 'pw'
    building_regular_threshold = '10'
    mcdchange_predict(prev_path, next_path, output_path,  fragment, building_regular,
                      model_change_detection, 0, 90, status_num_txt_path, folder_name)


