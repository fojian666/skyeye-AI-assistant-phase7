# -*- coding: utf-8 -*-
from osgeo import gdal, ogr,osr
import numpy as np
import os,sys,shutil
import ai_config as cg
logger = cg.logger

def merge_images(input_folder, output_path):
    # 获取所有待拼接的影像文件路径
    image_paths = [os.path.join(input_folder,f)  for f in os.listdir(input_folder) if f.endswith('.tif')]
    # image_paths = input_folder
    first_image_path = image_paths[0]
    first_image_dataset = gdal.Open(first_image_path)
    geo_projection = first_image_dataset.GetProjection()
    band_count = first_image_dataset.RasterCount
    data_type = first_image_dataset.GetRasterBand(1).DataType
    # 计算拼接后影像的范围
    min_x, max_x, min_y, max_y = None, None, None, None
    for image_path in image_paths:
        image_dataset = gdal.Open(image_path)
        geo_transform = image_dataset.GetGeoTransform()
        x_size = image_dataset.RasterXSize
        y_size = image_dataset.RasterYSize

        # 计算影像范围
        image_min_x = geo_transform[0]
        image_max_x = geo_transform[0] + (x_size * geo_transform[1])
        image_min_y = geo_transform[3] + (y_size * geo_transform[5])
        image_max_y = geo_transform[3]

        # 更新拼接后影像的范围
        if min_x is None or image_min_x < min_x:
            min_x = image_min_x
        if max_x is None or image_max_x > max_x:
            max_x = image_max_x
        if min_y is None or image_min_y < min_y:
            min_y = image_min_y
        if max_y is None or image_max_y > max_y:
            max_y = image_max_y

    # 计算拼接后影像的大小和分辨率
    merged_width = int((max_x - min_x) / abs(geo_transform[1]))
    merged_height = int((max_y - min_y) / abs(geo_transform[5]))
    merged_geo_transform = (min_x, abs(geo_transform[1]), geo_transform[2], max_y, geo_transform[4], -abs(geo_transform[5]))

    # 创建输出影像
    driver = gdal.GetDriverByName('GTiff')
    merged_image_dataset = driver.Create(output_path, merged_width, merged_height, band_count, data_type)

    # 设置输出影像的地理参考信息
    merged_image_dataset.SetProjection(geo_projection)
    merged_image_dataset.SetGeoTransform(merged_geo_transform)

    # 将每个影像映射到拼接后的位置
    for image_path in image_paths:
        image_dataset = gdal.Open(image_path)
        x_offset = int((image_dataset.GetGeoTransform()[0] - min_x) / abs(geo_transform[1]))
        y_offset = int((max_y - image_dataset.GetGeoTransform()[3]) / abs(geo_transform[5]))

        for band in range(band_count):
            band_data = image_dataset.GetRasterBand(band + 1).ReadAsArray()
            # 获取重叠部分的像素值
            overlap_data = merged_image_dataset.GetRasterBand(band + 1).ReadAsArray(x_offset, y_offset, band_data.shape[1], band_data.shape[0])

            # 将影像中非零像素的值覆盖到拼接后影像中
            mask = (overlap_data == 0)
            merged_image_dataset.GetRasterBand(band + 1).WriteArray(np.where(mask, band_data, overlap_data), x_offset, y_offset)

    # 释放资源并关闭数据集
    merged_image_dataset = None
    logger.info("影像拼接完成!")

def batch_clip_img(image_dir_path, output_path, clip_shp_dir):
    """
    批量按照shp裁剪影像
    :param image_dir_path: 需要裁剪的文件夹
    :param output_path: 输出文件夹
    :param clip_shp_dir: 存放shp的文件夹
    :return:
    """
    shp_files = os.listdir(clip_shp_dir)
    # 以列表展开所有目录下的文件名
    for shp_file in shp_files:
        # 从列表中遍历
        if shp_file.endswith('.shp'):
            # 判断是否为shp文件
            shp_name = os.path.join(clip_shp_dir, shp_file)
            # 定义shp文件的目录+名称
            files = os.listdir(image_dir_path)
            # 打开需要裁剪的文件夹,将所有文件以列表的形式列出
            for file in files:
                if file.endswith('.tif'):
                    # 判断文件是否为.tif结尾
                    filename = os.path.join(image_dir_path, file)
                    # 确定找到的文件名
                    in_raster = gdal.Open(filename)
                    out_raster = os.path.join(output_path, os.path.splitext(os.path.basename(filename))[0]+".tif")
                    ds = gdal.Warp(out_raster, in_raster, format='GTiff',
                                   cutlineDSName=shp_name,
                                   cropToCutline=True,
                                   cutlineWhere=None, dstNodata=0)
                    ds = None
                    # 关闭处理空间，释放内存

def batch_shp_clip_img(merge_tif_path, output_path, clip_shp_dir, status_num_txt_path):
    """
        merge_tif_path: 需要裁剪的文件夹
        output_path: 输出文件夹
        clip_shp_dir: 存放shp的文件夹
        status_num_txt_path:日志更新文件
        :return:
    """
    shp_files = os.listdir(clip_shp_dir)
    bar_interval = int(60/len(shp_files))
    # 以列表展开所有目录下的文件名
    for index,shp_file in enumerate(shp_files):
        # 从列表中遍历
        if shp_file.endswith('.shp'):
            # 判断是否为shp文件
            shp_name = os.path.join(clip_shp_dir, shp_file)
            in_raster = gdal.Open(merge_tif_path)
            out_raster = os.path.join(output_path, os.path.splitext(os.path.basename(shp_name))[0]+".tif")
            logger.info("开始剪裁{}文件".format(shp_file))
            ds = gdal.Warp(out_raster, in_raster, format='GTiff',
                           cutlineDSName=shp_name,
                           cropToCutline=True,
                           cutlineWhere=None, dstNodata=0)
            ds = None
            update_status_bar(40 + (index+1)*bar_interval, status_num_txt_path)

            # 关闭处理空间，释放内存
    # shutil.rmtree(output_path)
    logger.info("影像裁剪完成，请查看输出路径下剪裁结果!")

def update_status_bar(num,txt_path):
    with open(txt_path, 'w+') as f:
        f.write(str(num))


if __name__ == '__main__':
    input_folder = r'E:\geo_ai_server\c#_test_data\unjson\1\tif'
    output_path = r'E:\geo_ai_server\c#_test_data\unjson\1\1.tif'
    merge_images(input_folder, output_path)
    output_path1 = r'E:\geo_ai_server\c#_test_data\unjson\1\s'
    clip_shp_dir = r'E:\geo_ai_server\c#_test_data\unjson\1\shp'
    status_num_txt_path = r'E:\geo_ai_server\gtrs_cs_server23\logs\status_num\192-168-60-22_status.txt'
    batch_shp_clip_img(output_path, output_path1, clip_shp_dir,status_num_txt_path)
