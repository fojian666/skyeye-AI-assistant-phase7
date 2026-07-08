import os
import argparse,sys
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(WORK_DIR)
import ai_config as cg
import shutil

import geopandas as gpd
from shapely.geometry import shape
import numpy as np
import warnings
import time
from datetime import datetime
import pandas as pd
# 忽略所有警告
warnings.filterwarnings("ignore")
work_dir = cg.WORK_DIR
img_name_tag = ''
logger = cg.logger

def raster_to_polygon(rasterfile,cldsnow_shp_path,nodata=0):
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
    end_time = datetime.fromtimestamp(time.time())
    # 计算时间差
    time_delta = end_time - start_datetime
    # 将时间差转换为本地时间的字符串
    time_delta_str = str(time_delta)
    print("优化栅格转面耗时{}".format(time_delta_str))
    out_shp.to_file(cldsnow_shp_path)

def selectbylocation(source_path, target_path, result_path):
    """
    选择分析，借用arcpy脚本中的按位置选择分析功能
    Args:
        source_path: 源对象
        target_path: 目标对象
        result_path: 结果存储路径
    """
    # 按位置选择
    target_gdf = gpd.read_file(target_path)
    source_gdf = gpd.read_file(source_path,include_fields=['Shape','FID'])
    intersection = gpd.sjoin(target_gdf, source_gdf, how='inner', op='intersects')
    # 如果 intersection 索引为空，则复制目标图层为空的 GeoDataFrame
    if intersection.empty:
        copied_gdf = target_gdf
    else:
        # 如果 intersection 索引不为空，则根据 intersection 索引从 target_gdf 中选择对应的行
        copied_gdf = target_gdf.loc[intersection.index]
    #重置索引
    copied_gdf = copied_gdf.reset_index(drop=True)
    copied_gdf.to_file(result_path)

def solo_result_process(mask_tif_path, change_shp_path, result_dir, folder_name):
    """
    对变化检测数据进行结果优化处理
    Args:
        mask_tif_path: mask.tif路径
        change_shp_path: 变化检测shp路径
        result_dir: 结果存储文件夹
        folder_name:文件夹名称
    Returns:

    """
    global img_name_tag
    img_name_tag = folder_name
    dem_slope_mask_path = os.path.join(WORK_DIR,'optimization_process', 'important_data\\mask_union.shp')
    temp_out_path = os.path.join(result_dir, 'temp_out')
    if not os.path.exists(temp_out_path):
        os.mkdir(temp_out_path)
    file_name = (os.path.basename(mask_tif_path)).split('.')[0]
    file_name1 = (os.path.basename(change_shp_path)).split('.')[0]
    cldsnow_shp_path = os.path.join(temp_out_path, '{}_snow_mask.shp'.format(file_name))
    result_path = os.path.join(temp_out_path, '{}_opttemp.shp'.format(file_name))
    result_path2 = os.path.join(result_dir, '{}_optimize.shp'.format(file_name1))
    logger.info("结果优化:开始变化检测结果优化@{}".format(img_name_tag))
    #掩膜文件转为面图层，转出的是非云的图斑
    raster_to_polygon(mask_tif_path,cldsnow_shp_path)
    logger.info("结果优化:Successful,{}栅格转面成功@{}".format(os.path.splitext(os.path.basename(mask_tif_path))[0],img_name_tag))
    #与mask_tif做选择分析，选择出不在云上的图斑
    selectbylocation(cldsnow_shp_path,change_shp_path,result_path)
    logger.info('结果优化:Successful,{}选择1分析结束@{}'.format(os.path.splitext(os.path.basename(change_shp_path))[0],img_name_tag))
    #与mask_union做选择分析，选择出不在山上的图斑
    selectbylocation(dem_slope_mask_path,result_path,result_path2)
    logger.info('结果优化:Successful,{}选择分析2结束!@{}'.format(os.path.splitext(os.path.basename(result_path2))[0],img_name_tag))
    shutil.rmtree(temp_out_path)


if __name__ == '__main__':
    mask_tif_path = r'E:\geo_ai_server\c#_test_data\result\1\data_process_result\in_10\mask_tif\0_0.tif'
    change_shp_path = r'E:\geo_ai_server\c#_test_data\result\1\change_detection\in_10\0_0\shp\in_101_0_0.shp'
    result_dir = r'E:\geo_ai_server\c#_test_data\result\1\result_optimization'
    folder_name = 'ledu'
    solo_result_process(mask_tif_path, change_shp_path, result_dir, folder_name)



