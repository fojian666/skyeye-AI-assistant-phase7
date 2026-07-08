# -*- coding: utf-8 -*-
import os,sys
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,WORK_DIR)
import geopandas as gpd
import pyproj
import warnings
from shapely.geometry import shape
import apps.interpretation.ai_config as cg
from merge_tiffs_and_convert_tif_to_shp_common import convert_tiff_to_8bit,merge_images,raster_to_polygon,\
                                                merge_multi_regions_to_one_tiff,smooth_polygon,fill_holes
# 忽略所有警告
warnings.filterwarnings("ignore")
logger = cg.logger
max_savenum = cg.max_savenum


def merge_multi_regions_raster_and_tif_to_shp(input_path, output_path, img_name, fragment, regions_count,is_add_radio,probability_threshold):
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
    # convert_tiff_to_8bit(input_tif_path,convert_tif_path) #转换为8bit，原来为32bit
    logger.info("栅格转矢量:开始矢量优化处理......")
    prjtag ,file_pathlist= raster_to_shp_smooth_elininate_fragment(fragment, input_tif_path, output_path,is_add_radio,probability_threshold)
    logger.info(r"栅格转矢量:完成栅格转矢量及矢量优化处理")
    return prjtag,file_pathlist

def calculate_probability(row):
    """
    计算概率的数学公式
    Args:
        row:当前行数据

    Returns:计算后的概率

    """
    # 在这个示例中，我们假设要计算每一行的new_field值为
    return int(row['pixel']) /255.0

def raster_to_shp_smooth_elininate_fragment(fragment, input_tif_path, output_path,is_add_radio,probability_threshold):
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
    singlepart_data = explode_gdf
    if is_add_radio == '1':
        fieldname = "probablity"
        if len(singlepart_data) != 0:
            singlepart_data[fieldname] = singlepart_data.apply(calculate_probability, axis=1)  # 添加一个名为 'new_field' 的字段，并赋予默认初始值为0.0
            selected_data = singlepart_data[singlepart_data[fieldname] < float(probability_threshold)]
            # 删除选中的行
            rs_poly_gdf_new = singlepart_data.drop(selected_data.index)
        else:
            singlepart_data[fieldname] = 0
            rs_poly_gdf_new = singlepart_data
    else:
        rs_poly_gdf_new = singlepart_data
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
        else:
            pass
    # 将 geometry 转换为 shapely 对象
    rs_poly_gdf_prj['geometry'] = rs_poly_gdf_prj['geometry'].apply(shape)
    # 对每个多边形进行边界平滑拟合
    logger.info("栅格转矢量:开始进行边界平滑!!!")
    rs_poly_gdf_prj['smoothed_geometry'] = rs_poly_gdf_prj['geometry'].apply(lambda geom: smooth_polygon(geom))
    logger.info("栅格转矢量:开始填补空洞!!!")
    explode_gdf['filled_geometry'] = rs_poly_gdf_prj['smoothed_geometry'].apply(lambda geom:fill_holes(geom,0.5))
    smooth_result_gdf = gpd.GeoDataFrame(geometry=explode_gdf['filled_geometry'])
    smooth_result_gdf['pixel'] = rs_poly_gdf_prj['pixel']
    smooth_result_gdf['TBMJ'] = smooth_result_gdf.geometry.area.fillna(0)
    if is_add_radio == '1':
        smooth_result_gdf['probablity'] = rs_poly_gdf_prj['probablity']

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
    # result_gdf.to_file(output_path)
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
    print(flag,file_pathlist)
    return flag,file_pathlist


if __name__ == '__main__':

    input_path = r'C:\Users\Administrator\Desktop\q2_0_1_reg'
    output_path = r'C:\Users\Administrator\Desktop\q2_0_1_reg\all.shp'
    image_name = '玉树q2_0_1'
    fragment = '0'
    regions_count = 1
    is_add_radio = '1'
    probability_threshold = 0
    merge_multi_regions_raster_and_tif_to_shp(input_path, output_path, image_name, fragment, regions_count,is_add_radio,probability_threshold)

