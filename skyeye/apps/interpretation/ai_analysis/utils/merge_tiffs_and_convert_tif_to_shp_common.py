# -*- coding: utf-8 -*-
import os,sys
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,WORK_DIR)
sys.path.insert(0,os.path.dirname(WORK_DIR))
from osgeo import gdal
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import pyproj
import warnings
from shapely.geometry import shape
from shapelysmooth import taubin_smooth
import apps.interpretation.ai_config as cg
import time
from datetime import datetime
import pandas as pd
# 忽略所有警告
warnings.filterwarnings("ignore")
logger = cg.logger
max_savenum = cg.max_savenum

def merge_images(input_folder, output_path):
    """
    影像拼接
    Args:
        input_folder: 输入文件夹
        output_path: 拼接影像存储路径
    """
    # 获取所有待拼接的影像文件路径
    image_paths = input_folder
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
        try:
            image_dataset = gdal.Open(image_path)
            x_offset = int((image_dataset.GetGeoTransform()[0] - min_x) / abs(geo_transform[1]))
            y_offset = int((max_y - image_dataset.GetGeoTransform()[3]) / abs(geo_transform[5]))
            for band in range(band_count):
                band_data = image_dataset.GetRasterBand(band + 1).ReadAsArray()
                # 获取重叠部分的像素值
                print("获取重叠部分的像素值{}".format(image_path))
                overlap_data = merged_image_dataset.GetRasterBand(band + 1).ReadAsArray(x_offset, y_offset, band_data.shape[1], band_data.shape[0])
                print("计算影像中非零像素的值")
                # 将影像中非零像素的值覆盖到拼接后影像中
                mask = (overlap_data == 0)
                print("计算影像中非零像素的值写入影像中")
                merged_image_dataset.GetRasterBand(band + 1).WriteArray(np.where(mask, band_data, overlap_data), x_offset, y_offset)
        except:
            pass

    # 释放资源并关闭数据集
    merged_image_dataset = None
    logger.info("栅格转矢量:影像拼接完成!")

def merge_multi_regions_to_one_tiff(input_path, img_name):
    """
    合并tif
    Args:
        input_path: 输入路径文件夹，包含全部全部的分区预测结果tif
        img_name: 影像名称，依据该名称找对应的分区文件
    Returns:

    """
    result_tif_path = os.path.join(input_path, "result_" + img_name + ".tif")
    input_list = []
    for file in os.listdir(input_path):
        if img_name in file and "reg" in file and file.endswith('.tif'):
            file_path = os.path.join(input_path,file)
            input_list.append(file_path)
    merge_images(input_list,result_tif_path)
    return result_tif_path

def convert_tiff_to_8bit(input_path, output_path):
    """
    将合并后的tif转为8bit类型，原来是32bit
    Args:
        input_path: 输入tif路径
        output_path: 输出tif路径
    Returns:

    """
    dataset = gdal.Open(input_path)
    band_count = dataset.RasterCount
    driver = gdal.GetDriverByName("GTiff")
    output_dataset = driver.CreateCopy(output_path, dataset)
    for band in range(band_count):
        band_data = dataset.GetRasterBand(band + 1).ReadAsArray()
        if np.max(band_data) <= 1:
            scaled_data = ((band_data - np.min(band_data)) / (np.max(band_data) - np.min(band_data))).astype('uint8')
        else:
            scaled_data = ((band_data - np.min(band_data)) / (np.max(band_data) - np.min(band_data))) * 255
            scaled_data = scaled_data.astype('uint8')
        output_dataset.GetRasterBand(band + 1).WriteArray(scaled_data)

    output_dataset.FlushCache()
    output_dataset = None
    logger.info("栅格转矢量:转换为8位完成！")

def raster_to_polygon_bak(rasterfile,nodata=0):
    """
    栅格转面
    Args:
        rasterfile:要转换的栅格文件
        nodata:nodata赋值为0

    Returns:栅格转面后的gdf数据和影像的空间参考

    """
    out_shp = gpd.GeoDataFrame(columns=['pixel', 'geometry'])
    with rio.open(rasterfile) as f:
        image = f.read(1)
        img_crs = f.crs
        image[image == f.nodata] = nodata
        image = image.astype(np.float32)  # 上面那步把缺失值处理为0之后加上这步可以防止数据类型出错导致的报错
        i = 0
        for coords, value in features.shapes(image, transform=f.transform):
            if value != nodata:
                geom = shape(coords)
                out_shp.loc[i] = [value, geom]
                i += 1
    out_shp.set_geometry('geometry', inplace=True)
    out_shp = out_shp.dissolve(by='pixel', as_index=False)
    # out_shp.set_crs(img_crs)
    if img_crs is not None:
        if img_crs.is_projected:
            print("是投影坐标系")
            out_shp.crs = img_crs
        elif img_crs.is_geographic:
            print("是地理坐标系")
            out_shp.set_crs(img_crs)
    logger.info('栅格转矢量:栅格转面结束!')
    return out_shp,img_crs

def raster_to_polygon(rasterfile,nodata=0):
    """
    栅格转面
    Args:
        rasterfile:要转换的栅格文件
        nodata:nodata赋值为0

    Returns:栅格转面后的gdf数据和影像的空间参考

    """

    import rasterio as rio
    from rasterio import features
    start_datetime = datetime.fromtimestamp(time.time())
    with rio.open(rasterfile) as f:
        image = f.read(1)
        img_crs = f.crs
        image[image == f.nodata] = nodata
        image = image.astype(np.float32)  # 上面那步把缺失值处理为0之后加上这步可以防止数据类型出错导致的报错
        # 生成几何图形并创建包含数值和坐标的 DataFrame 对象
        df = pd.DataFrame(list(features.shapes(image, transform=f.transform)), columns=['geometry', 'pixel'])
        # 删除数据值为nodata的行
        df = df[df['pixel'] != nodata]  # 删除无用行，减少循环操作
        geometrys = df['geometry'].apply(lambda x: shape(x))  # 转换为包含坐标的 Series 对象  apply() 方法和 lambda 函数可以避免使用显式的循环处理,可以同时处理多个元素
        out_shp = gpd.GeoDataFrame({'geometry': geometrys, 'pixel': df.pixel}, crs=f.crs)
    out_shp.set_geometry('geometry', inplace=True)
    if img_crs is not None:
        if img_crs.is_projected:
            print("是投影坐标系")
            out_shp.crs = img_crs
        elif img_crs.is_geographic:
            print("是地理坐标系")
            out_shp.set_crs(img_crs)
    logger.info('栅格转矢量:栅格转面结束!')
    end_time = datetime.fromtimestamp(time.time())
    # 计算时间差
    time_delta = end_time - start_datetime
    # 将时间差转换为本地时间的字符串
    time_delta_str = str(time_delta)
    print("栅格转面耗时{}".format(time_delta_str))
    return out_shp, img_crs


def merge_tif_and_convert_to_shp(input_path, output_path, img_name, fragment, regions_count):
    """
    合并tif，转shp，平滑处理，去除碎斑
    Args:
        input_path: 输入图片路径
        output_path: 输出路径
        img_name: 图片名称
        fragment: 碎斑阈值
        regions_count: 分区总数
        probability_threshold:概率阈值

    Returns:

    """
    if int(regions_count) > 1:
        logger.info("栅格转矢量:执行多个region的合并，形成大的tif文件，自带重叠")
        input_tif_path = merge_multi_regions_to_one_tiff(input_path, img_name)
    else:  # regions_count == 1，无需合并
        input_tif_path = os.path.join(input_path, img_name + "_reg.tif")
    logger.info(r"栅格转矢量:开始栅格转矢量及矢量优化处理…………")
    # convert_tif_path = os.path.join(os.path.dirname(input_tif_path),os.path.splitext(os.path.basename(input_tif_path))[0]+'_8bit.tif')
    # convert_tiff_to_8bit(input_tif_path,convert_tif_path)
    logger.info("栅格转矢量:开始矢量优化处理......")
    prjtag,file_pathlist = raster_to_shp_smooth_elininate_fragment(fragment, input_tif_path, output_path)
    logger.info(r"栅格转矢量:完成栅格转矢量及矢量优化处理")
    return prjtag,file_pathlist


def smooth_polygon(geom):
    """
    边界平滑
    Args:
        geom: 当前属性面

    Returns:平滑后的面

    """
    try:
        smoothed_geometry = taubin_smooth(geom, 0.5, -0.5, 5)
        if not smoothed_geometry.is_valid:
            smoothed_geometry = smoothed_geometry.buffer(0)
        #判断面是否有效，若有效，返回平滑后的面
        if smoothed_geometry.is_valid or smoothed_geometry.geom_type == 'Polygon':
            return smoothed_geometry
        #判断面的属性，若为多面体，将面进行union操作，防止自相交问题出现
        elif smoothed_geometry.geom_type == 'MultiPolygon':
            return smoothed_geometry.union(smoothed_geometry)  # 使用union方法修复自相交
        return smoothed_geometry
    except:
        return geom

def fill_holes(geom,threshold):
    """
    空洞填充
    Args:
        geom: 面
        threshold: 空洞所占总面积的比例

    Returns:填补后的面

    """
    total_area = geom.area
    holes_area = 0
    if geom.geom_type == 'MultiPolygon':
        return geom
    for interior in geom.interiors:
        # 创建面的几何对象
        polygon = Polygon(interior)
        area = polygon.area
        holes_area += area
    if total_area == 0:
        return geom
    holes_ratio = holes_area / total_area
    #空洞面积小于指定比例，则进行边界扩展
    if holes_ratio < threshold:
        return Polygon(geom.exterior)
    else:
        return geom

def raster_to_shp_smooth_elininate_fragment(fragment, input_tif_path, output_path):
    """
    栅格转面，平滑处理，去除碎斑
    Args:
        fragment: 碎斑阈值，小于此阈值的碎斑会被剔除
        input_tif_path: 输入tif路径
        output_path: 输出路径
        is_add_radio:是否添加概率
        probability_threshold:概率阈值
    Returns:

    """
    flag = 3
    rs_poly_gdf,img_crs = raster_to_polygon(input_tif_path)
    # if img_crs is None:
    #     img_crs = img_crs
    # else:
    #     img_crs = img_crs.to_wkt()
    #面打散操作，因为栅格转面后为整个面数据
    explode_gdf = rs_poly_gdf.explode()
    rs_poly_gdf_new = explode_gdf
    logger.info("栅格转矢量:开始判断坐标系!!!")

    if img_crs is None:
        rs_poly_gdf_prj = rs_poly_gdf_new
        rs_poly_gdf_prj.crs = None
    elif img_crs.is_projected:
        rs_poly_gdf_prj = rs_poly_gdf_new
        flag = 1
    else:
        flag = 0
        if pyproj.Transformer.from_crs(img_crs, 4490, always_xy=True).has_inverse:
            #转换到投影坐标系
            # rs_poly_gdf_prj = rs_poly_gdf_new.set_crs('EPSG:{}'.format(4490)).to_crs('EPSG:{}'.format(4549))
            rs_poly_gdf_prj = rs_poly_gdf_new.to_crs('EPSG:{}'.format(4549))
        elif pyproj.Transformer.from_crs(img_crs, 4326, always_xy=True).has_inverse:
            # rs_poly_gdf_prj = rs_poly_gdf_new.set_crs('EPSG:{}'.format(4326)).to_crs('EPSG:{}'.format(3857))
            rs_poly_gdf_prj = rs_poly_gdf_new.to_crs('EPSG:{}'.format(3857))

    # 将 geometry 转换为 shapely 对象
    rs_poly_gdf_prj['geometry'] = rs_poly_gdf_prj['geometry'].apply(shape)
    # 对每个多边形进行边界平滑拟合
    logger.info("栅格转矢量:开始进行边界平滑!!!")
    rs_poly_gdf_prj['smoothed_geometry'] = rs_poly_gdf_prj['geometry'].apply(lambda geom: smooth_polygon(geom))
    logger.info("栅格转矢量:开始填补空洞!!!")
    explode_gdf['filled_geometry'] = rs_poly_gdf_prj['smoothed_geometry'].apply(lambda geom:fill_holes(geom,0.5))
    smooth_result_gdf = gpd.GeoDataFrame(geometry=explode_gdf['filled_geometry'])
    smooth_result_gdf['pixel'] = rs_poly_gdf_prj['pixel']
    smooth_result_gdf['TBMJ'] = smooth_result_gdf.geometry.area
    if img_crs is None:
        logger.info("栅格转矢量:数据没有坐标系，不进行剔除碎斑操作!!!")
        change_crs_result_gdf = smooth_result_gdf
    else:
        logger.info("栅格转矢量:数据具有坐标系，开始剔除碎斑!!!")
        smooth_result_gdf = smooth_result_gdf[smooth_result_gdf['TBMJ'] >= float(fragment)]
        change_crs_result_gdf = smooth_result_gdf.to_crs(img_crs)
    # 计算每个要素的质心点坐标
    change_crs_result_gdf['centroid'] = change_crs_result_gdf['geometry'].centroid
    change_crs_result_gdf['X'] = change_crs_result_gdf['centroid'].x
    change_crs_result_gdf['Y'] = change_crs_result_gdf['centroid'].y
    # 移除不需要的列
    result_gdf = change_crs_result_gdf.drop(columns=['centroid'])
    #分块处理，防止shp存储达到上限
    file_pathlist = []
    if len(result_gdf) > max_savenum:
        logger.info("栅格转矢量:数据量较大，开始执行分块存储!!!")
        file_basename = os.path.splitext(os.path.basename(output_path))[0]
        chunk = int(len(result_gdf) / max_savenum)
        j = 0
        for i in range(chunk):
            save_path = os.path.join(os.path.dirname(output_path),'{}_{}.shp'.format(file_basename,i))
            (result_gdf[j:j + max_savenum]).to_file(save_path)
            file_pathlist.append(save_path)
            j += max_savenum
        if len(result_gdf[j:]) != 0:
            (result_gdf[j:]).to_file(os.path.join(os.path.dirname(output_path),'{}_{}.shp'.format(file_basename,chunk)))
            file_pathlist.append(os.path.join(os.path.dirname(output_path),'{}_{}.shp'.format(file_basename,chunk)))
    else:
        result_gdf.to_file(output_path)
        file_pathlist.append(output_path)
    return flag,file_pathlist


if __name__ == '__main__':
    start_datetime = datetime.fromtimestamp(time.time())
    input_path = r'C:\Users\Administrator\Desktop\test'
    output_path = r'C:\Users\Administrator\Desktop\test\all.shp'
    image_name = 'ea'
    fragment = '0'
    regions_count = 1
    merge_tif_and_convert_to_shp(input_path, output_path, image_name, fragment, regions_count)
    end_time = datetime.fromtimestamp(time.time())
    # 计算时间差
    time_delta = end_time - start_datetime
    # 将时间差转换为本地时间的字符串
    time_delta_str = str(time_delta)
    print("总耗时{}".format(time_delta_str))
