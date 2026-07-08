# -*- coding: utf-8 -*-
import os,sys
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,WORK_DIR)
from osgeo import gdal
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import pyproj
import warnings
from shapely.geometry import shape
from shapelysmooth import taubin_smooth
import ai_config as cg
from merge_tiffs_and_convert_tif_to_shp_common import convert_tiff_to_8bit,merge_images,raster_to_polygon,smooth_polygon,fill_holes
# 忽略所有警告
warnings.filterwarnings("ignore")
logger = cg.logger
max_savenum = cg.max_savenum
ST_COLORMAP = cg.ST_COLORMAP
ST_COLORMAP_pixel = cg.ST_COLORMAP_pixel
ST_CLASSES = cg.ST_CLASSES

def merge_multi_regions_raster_and_tif_to_shp(input_path, output_path, img_name, fragment, regions_count,reg_tag,reg_tag2):
    if int(regions_count) > 1:
        logger.info("栅格转矢量:执行多个region的合并，形成大的tif文件，自带重叠")
        input_tif_path = merge_multi_regions_to_one_tiff(input_path, img_name,reg_tag2)
        input_tif_path2 = merge_multi_regions_to_one_tiff(input_path, img_name,reg_tag2)

    else:  # regions_count == 1，无需合并
        input_tif_path = os.path.join(input_path, img_name + "_reg{}.tif".format(reg_tag))
        input_tif_path2 = os.path.join(input_path, img_name + "_reg{}.tif".format(reg_tag2))

    logger.info(r"栅格转矢量:开始栅格转矢量及矢量优化处理…………")
    logger.info("栅格转矢量:开始矢量优化处理......")
    # 计算变化结果
    output_raster = os.path.join(input_path,"change_result_8bit.tif")
    raster_array_computation(input_tif_path, input_tif_path2, output_raster)
    print("开始矢量优化处理......")
    prjtag,file_pathlist = raster_to_shp_smooth_elininate_fragment(fragment, output_raster, output_path)
    print(r"完成栅格转矢量及矢量优化处理")
    return prjtag,file_pathlist


def raster_to_shp_smooth_elininate_fragment(fragment, input_tif_path, output_path):
    """
    栅格转面，平滑处理，去除碎斑
    Args:
        fragment: 碎斑阈值，小于此阈值的碎斑会被剔除
        input_tif_path: 输入tif路径
        output_path: 输出路径
    Returns:

    """
    flag = 3
    rs_poly_gdf, img_crs = raster_to_polygon(input_tif_path)
    # 面打散操作，因为栅格转面后为整个面数据
    explode_gdf = rs_poly_gdf.explode()
    singlepart_data = explode_gdf
    logger.info("栅格转矢量:开始判断坐标系!!!")
    #更新类别信息
    cols = [i * 10 for i in ST_COLORMAP_pixel]  # col name
    res_array = np.zeros((len(ST_COLORMAP_pixel), len(cols)))
    for i in range(len(ST_COLORMAP_pixel)):
        for j in range(len(ST_COLORMAP_pixel)):
            res_array[i][j] = int(ST_COLORMAP_pixel[i] + cols[j]) #以行表示后景像素，列表示前景像素
    logger.info("栅格转矢量:开始更新类别信息!!!")
    for index, row in singlepart_data.iterrows():
        gridcode = int(row['pixel'])
        idx = np.where(res_array == gridcode) #找到该像素值对应的前后编码
        singlepart_data.at[index, 'class_next'] = ST_CLASSES[idx[0][0]] #获取后景类别
        singlepart_data.at[index, 'class_pre'] = ST_CLASSES[idx[1][0]] #获取前景类别
        #满足下面条件的，标注为需要剔除图斑
        if singlepart_data.at[index, 'class_next'] == 'unchanged' or singlepart_data.at[index, 'class_pre'] == 'unchanged' \
                or singlepart_data.at[index, 'class_next'] == singlepart_data.at[index, 'class_pre']:
            singlepart_data.at[index, 'drop_tag'] = '1'
        else:
            singlepart_data.at[index, 'drop_tag'] = '0'
    #判断是否具有坐标系
    if img_crs is None:
        rs_poly_gdf_prj = singlepart_data
        rs_poly_gdf_prj.crs = None
    elif img_crs.is_projected:
        rs_poly_gdf_prj = singlepart_data
        flag = 1
    else:
        flag = 0
        # if img_crs.to_epsg() == 4490:
        if pyproj.Transformer.from_crs(img_crs, 4490, always_xy=True).has_inverse:
            # 转换到投影坐标系
            # rs_poly_gdf_prj = singlepart_data.set_crs('EPSG:{}'.format(4490)).to_crs('EPSG:{}'.format(4549))
            rs_poly_gdf_prj = singlepart_data.to_crs('EPSG:{}'.format(4549))
        elif pyproj.Transformer.from_crs(img_crs, 4326, always_xy=True).has_inverse:
            # rs_poly_gdf_prj = singlepart_data.set_crs('EPSG:{}'.format(4326)).to_crs('EPSG:{}'.format(3857))
            rs_poly_gdf_prj = singlepart_data.to_crs('EPSG:{}'.format(3857))
        else:
            pass
    # 将 geometry 转换为 shapely 对象
    rs_poly_gdf_prj['geometry'] = rs_poly_gdf_prj['geometry'].apply(shape)
    # 对每个多边形进行边界平滑拟合
    logger.info("栅格转矢量:开始进行边界平滑!!!")
    rs_poly_gdf_prj['smoothed_geometry'] = rs_poly_gdf_prj['geometry'].apply(lambda geom: smooth_polygon(geom))
    logger.info("栅格转矢量:开始填补空洞!!!")
    explode_gdf['filled_geometry'] = rs_poly_gdf_prj['smoothed_geometry'].apply(lambda geom: fill_holes(geom, 0.5))
    smooth_result_gdf = gpd.GeoDataFrame(geometry=explode_gdf['filled_geometry'])
    #继承原有的属性
    smooth_result_gdf['pixel'] = rs_poly_gdf_prj['pixel']
    smooth_result_gdf['TBMJ'] = smooth_result_gdf.geometry.area
    smooth_result_gdf['class_next'] = rs_poly_gdf_prj['class_next']
    smooth_result_gdf['class_pre'] = rs_poly_gdf_prj['class_pre']
    smooth_result_gdf['drop_tag'] = rs_poly_gdf_prj['drop_tag']
    smooth_result_gdf = smooth_result_gdf[smooth_result_gdf['drop_tag'] != '1']
    if img_crs is None:
        logger.info("栅格转矢量:数据没有坐标系，不进行剔除碎斑操作!!!") #因为没有坐标系时，图斑的计算面积趋近于0，为防止误剃，所以没有坐标系的时候不进行剔除碎斑操作
        change_crs_result_gdf = smooth_result_gdf
        flag = 3

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


def merge_multi_regions_to_one_tiff(input_path, img_name,reg_tag):
    """
    合并tif
    Args:
        input_path: 输入路径文件夹，包含全部全部的分区预测结果tif
        img_name: 影像名称，依据该名称找对应的分区文件
        reg_tag：reg的tag标志，分为1和2，1表示前景的结果合并，2表示后景的结果合并
    Returns:

    """
    result_tif_path = os.path.join(input_path, "result_" + img_name + "{}.tif".format(reg_tag))
    input_list = []
    for file in os.listdir(input_path):
        if img_name in file and "reg{}".format(reg_tag) in file and file.endswith('.tif'):
            file_path = os.path.join(input_path,file)
            input_list.append(file_path)
    merge_images(input_list,result_tif_path)
    return result_tif_path

def raster_array_computation(input_tif_path,input_tif_path2,output_tif_path):
    """
    计算两个栅格相加的结果
    Args:
        input_tif_path:前景合并结果
        input_tif_path2: 后景合并结果
        output_tif_path: 输出结果路径

    Returns:

    """

    # 打开输入栅格数据
    dataset = gdal.Open(input_tif_path)
    band1 = dataset.GetRasterBand(1)
    array1 = band1.ReadAsArray()
    transform = dataset.GetGeoTransform()

    dataset2 = gdal.Open(input_tif_path2)
    band2 = dataset2.GetRasterBand(1)
    array2 = band2.ReadAsArray()

    # 执行栅格数据减法操作
    result_array = array1 * 10 + array2 #计算方式

    # 创建输出栅格数据
    driver = gdal.GetDriverByName("GTiff") #创建输出文件
    output_dataset = driver.Create(output_tif_path, dataset.RasterXSize, dataset.RasterYSize, 1, band1.DataType)
    output_dataset.SetGeoTransform(transform)
    output_dataset.SetProjection(dataset.GetProjection())#设置空间参考

    # 将结果数组写入栅格数据中
    output_band = output_dataset.GetRasterBand(1)
    output_band.WriteArray(result_array)
    output_band.FlushCache()

    print("栅格数据已保存到", output_tif_path)

    # 释放资源
    output_band = None
    output_dataset = None
    band1 = None
    dataset = None


if __name__ == '__main__':

    input_path = r'E:\geo_ai_server\c#_test_data\result\5\tif'
    output_path = r'E:\geo_ai_server\c#_test_data\result\5\6\\1.shp'
    image_name = 'R36T_10240_11264_7168_8192_A'
    fragment = '0'
    regions_count = 1
    is_add_radio = '0'
    probability_threshold = 0.5
    reg_tag = '1'
    reg_tag2 = '2'
    merge_multi_regions_raster_and_tif_to_shp(input_path, output_path, image_name, fragment, regions_count,reg_tag,reg_tag2)
