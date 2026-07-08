# -*- coding: utf-8 -*-
try :
    import gdal,gdalconst
except:
    from osgeo import gdal,gdalconst
import os,sys
WORK_DIR =os.path.dirname(os.path.abspath(__file__))

from PIL import Image
from PIL import ImageFile
import numpy as np
import apps.interpretation.ai_config as cg
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
work_dir = cg.PROJECT_PATH
max_single_img_size = cg.max_single_img_size
clip_size = cg.clip_size

def clip_image(pre_path, next_path, output_dir, interval):
    """
    影像裁剪
    Args:
        pre_path: 前景地址
        next_path: 后景地址
        output_dir: 输出文件夹路径
        interval: 裁剪大小

    Returns:

    """
    folder_path = [pre_path, next_path]
    for single_img in folder_path:
        # 读取输入影像
        input_ds = gdal.Open(single_img)
        # 获取输入影像的宽、高和波段数
        width = input_ds.RasterXSize
        height = input_ds.RasterYSize
        num_band = input_ds.RasterCount
        num_col = width // interval
        num_row = height // interval
        if num_col == 0:
            num_col = 1
        if num_row == 0:
            num_row = 1
        x_info = []
        size_info = []
        for i_start in range(num_col):
            for j_start in range(num_row):
                x_info.append([i_start * interval, j_start * interval])
                if i_start == num_col - 1 and j_start != num_row - 1:
                    size_info.append([width - (i_start * interval), interval])
                elif i_start != num_col - 1 and j_start == num_row - 1:
                    size_info.append([interval, height - (j_start * interval)])
                elif i_start == num_col - 1 and j_start == num_row - 1:
                    size_info.append([width - (i_start * interval), height - (j_start * interval)])
                else:
                    size_info.append([interval, interval])

        for i in range(len(x_info)):
            i_start = x_info[i][0]
            j_start = x_info[i][1]
            xsize = size_info[i][0]
            ysize = size_info[i][1]
            solo = os.path.join(output_dir,
                                '{}_{}'.format(int(i_start / int(interval)), int(j_start / int(interval))))
            if not os.path.exists(solo):
                os.mkdir(solo)
            output_name = os.path.basename(single_img).split('.')[
                              0] + f'_{int(i_start / int(interval))}_{int(j_start / int(interval))}.tif'
            output_file = os.path.join(solo, output_name)
            # 设置输出影像驱动和选项
            driver = gdal.GetDriverByName('GTiff')
            options = ['COMPRESS=PACKBITS']
            # 创建输出数据集
            output_ds = driver.Create(output_file, xsize, ysize, num_band,
                                      input_ds.GetRasterBand(1).DataType, options)
            # 设置投影和地理坐标信息
            output_ds.SetProjection(input_ds.GetProjection())
            output_ds.SetGeoTransform((input_ds.GetGeoTransform()[0] + i_start * input_ds.GetGeoTransform()[1],
                                       input_ds.GetGeoTransform()[1], 0,
                                       input_ds.GetGeoTransform()[3] + j_start * input_ds.GetGeoTransform()[5],
                                       0, input_ds.GetGeoTransform()[5]))
            # 复制数据到输出数据集
            for k in range(num_band):
                input_band = input_ds.GetRasterBand(k + 1)
                output_band = output_ds.GetRasterBand(k + 1)
                data = input_band.ReadAsArray(i_start, j_start, xsize, ysize)
                output_band.WriteArray(data, 0, 0)
            # 删除输出影像
            del output_ds
        # 删除输入影像
        del input_ds


def is_tif_all_black(tif_path):
    """
    判断tif文件是否全黑
    Args:
        tif_path: tif文件路径

    Returns:

    """
    # 打开tif文件
    tif = gdal.Open(tif_path)
    # 获取影像宽度、高度、波段数
    band_nums = tif.RasterCount
    for i in range(1, band_nums + 1):
        # 读取各波段
        band = tif.GetRasterBand(i)
        band_data = band.ReadAsArray()
        band_data = np.nan_to_num(band_data)
        # 判断该波段是否全为0
        if not np.all(band_data == 0):
            tif = None
            del tif
            return False

    tif = None
    del tif
    return True

def clip_image1(pre_path, next_path, output_dir,pre_dir_path, next_dir_path,interval):
    """
    影像裁剪
    Args:
        pre_path: 前景地址
        next_path: 后景地址
        output_dir: 输出文件夹路径
        interval: 裁剪大小

    Returns:

    """
    folder_path = [pre_path, next_path]
    for index,single_img in enumerate(folder_path):
        # 读取输入影像
        input_ds = gdal.Open(single_img)
        # 获取输入影像的宽、高和波段数
        width = input_ds.RasterXSize
        height = input_ds.RasterYSize
        num_band = input_ds.RasterCount
        num_col = width // interval
        num_row = height // interval
        if num_col == 0:
            num_col = 1
        if num_row == 0:
            num_row = 1
        x_info = []
        size_info = []
        for i_start in range(num_col):
            for j_start in range(num_row):
                x_info.append([i_start * interval, j_start * interval])
                if i_start == num_col - 1 and j_start != num_row - 1:
                    size_info.append([width - (i_start * interval), interval])
                elif i_start != num_col - 1 and j_start == num_row - 1:
                    size_info.append([interval, height - (j_start * interval)])
                elif i_start == num_col - 1 and j_start == num_row - 1:
                    size_info.append([width - (i_start * interval), height - (j_start * interval)])
                else:
                    size_info.append([interval, interval])

        for i in range(len(x_info)):
            i_start = x_info[i][0]
            j_start = x_info[i][1]
            xsize = size_info[i][0]
            ysize = size_info[i][1]
            # solo = os.path.join(output_dir,
            #                     '{}_{}'.format(int(i_start / int(interval)), int(j_start / int(interval))))
            # if not os.path.exists(solo):
            #     os.mkdir(solo)
            output_name = os.path.basename(single_img).split('.')[
                              0] + f'_{int(i_start / int(interval))}_{int(j_start / int(interval))}.tif'
            if index == 0:
                output_file = os.path.join(pre_dir_path, output_name)
            else:
                output_file = os.path.join(next_dir_path, output_name)
            # 设置输出影像驱动和选项
            driver = gdal.GetDriverByName('GTiff')
            options = ['COMPRESS=PACKBITS']
            # 创建输出数据集
            output_ds = driver.Create(output_file, xsize, ysize, num_band,
                                      input_ds.GetRasterBand(1).DataType, options)
            # 设置投影和地理坐标信息
            output_ds.SetProjection(input_ds.GetProjection())
            output_ds.SetGeoTransform((input_ds.GetGeoTransform()[0] + i_start * input_ds.GetGeoTransform()[1],
                                       input_ds.GetGeoTransform()[1], 0,
                                       input_ds.GetGeoTransform()[3] + j_start * input_ds.GetGeoTransform()[5],
                                       0, input_ds.GetGeoTransform()[5]))
            # 复制数据到输出数据集
            for k in range(num_band):
                input_band = input_ds.GetRasterBand(k + 1)
                output_band = output_ds.GetRasterBand(k + 1)
                data = input_band.ReadAsArray(i_start, j_start, xsize, ysize)
                output_band.WriteArray(data, 0, 0)
            # 删除输出影像
            del output_ds
        # 删除输入影像
        del input_ds