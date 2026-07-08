#-*- coding: utf-8 -*-
import os
import sys
import geopandas as gpd
import numpy as np

from shapely.geometry import shape
import warnings
warnings.filterwarnings("ignore")

def raster2polygon(tif_path: str, shp_path: str, result_dir: str = None, nodata=0):
    """
    栅格转面操作，主要是用与变化检测结果优化，剔除在云雪之上的图斑
    Args:
        tif_path: mask.tif路径
        shp_path: 变化检测shp文件
        nodata: 背景值
        result_dir: 结果存储文件夹

    Returns:

    """
    import rasterio as rio
    from rasterio import features
    try:
        # 栅格转面
        out_shp = gpd.GeoDataFrame(columns=['pixel', 'geometry'])
        with rio.open(tif_path) as f:
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
        try:
            # 执行选择操作
            selected_data = out_shp[out_shp['GRIDCODE'] == 1]
            # 将结果保存到 shapefile
            selected_data.to_file(shp_path)
            print('raster to polygon have finished!')
            return out_shp, img_crs
        except:
            # 将结果保存到 shapefile
            out_shp.to_file(shp_path)
    except Exception as e:
        print('Raster to Polygon error!', e)


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
    source_gdf = gpd.read_file(source_path)

    intersection = gpd.sjoin(target_gdf, source_gdf, how='inner', op='intersects')
    target_gdf = target_gdf.loc[intersection.index]
    target_gdf = target_gdf.reset_index(drop=True)
    intersection.to_file(result_path)


def selectbylocation_switch(source_path, target_path, result_path):
    """
        选择分析，借用arcpy脚本中的按属性选择分析功能
        Args:
            source_path: 源对象
            target_path: 目标对象
            result_path: 结果存储路径
        """
    pass


def shpintersect(in_feature1, in_feature2, out_features):
    """
    相交性分析
    Args:
        in_feature1: 图层1路径
        in_feature2: 图层2路径
        out_features: 相交性分析后结果存储路径
    """
    # 相交性分析
    if in_feature1.endswith('.shp'):
        shp1_gdf = gpd.read_file(in_feature1)
    else:
        shp1_gdf = in_feature1
    if in_feature2.endswith('.shp'):
        shp2_gdf = gpd.read_file(in_feature2)
    else:
        shp2_gdf = in_feature2
    intersection = gpd.overlay(shp1_gdf, shp2_gdf, how='intersection')

    # 输出
    if out_features.endswith('.shp'):
        if not os.path.exists(os.path.dirname(out_features)):
            os.makedirs(os.path.dirname(out_features))
        intersection.to_file(out_features)

    return intersection


def copyfeature(in_feature1, in_feature2):
    """
    执行复制
    Args:
        in_feature1: 待复制图层
        in_feature2: 复制图层
    Returns:
    # """
    # 读取源要素
    if in_feature1.endswith('.shp'):
        shp1_gdf = gpd.read_file(in_feature1)
    else:
        shp1_gdf = in_feature1
    # 复制要素
    shp2_gdf = shp1_gdf.copy()

    if in_feature2.endswith('.shp'):
        # 输出
        if not os.path.exists(os.path.dirname(in_feature2)):
            os.makedirs(os.path.dirname(in_feature2))
        shp2_gdf.to_file(in_feature2)

    return shp2_gdf


if __name__ == '__main__':

    flag = 'SelectByLocation'
    if flag == 'Raster2Polygon':
        tif_path = sys.argv[2]
        shp_path = sys.argv[3]
        result_path = sys.argv[4]
        raster2polygon(tif_path, shp_path, result_path)
    elif flag == 'SelectByLocation':
        Source_path = r'F:\0MPData\Py_20230926_gtrs_cs_server\shpProcessingTest\mask_union_clip.shp'
        Target_path = r'F:\0MPData\Py_20230926_gtrs_cs_server\shpProcessingTest\shp\LEDU202301_Clip.shp'
        Result_path = r'F:\0MPData\Py_20230926_gtrs_cs_server\shpProcessingTest\result\result_.shp'
        selectbylocation(Source_path, Target_path, Result_path)
    elif flag == 'SelectByLocationSwitch':
        Source_path = sys.argv[2]
        Target_path = sys.argv[3]
        Result_path = sys.argv[4]
        selectbylocation_switch(Source_path, Target_path, Result_path)
    elif flag == 'CopyFeatures':
        Source_path = sys.argv[2]
        Target_path = sys.argv[3]
        copyfeature(Source_path, Target_path)
    else:
        in_feature1 = sys.argv[2]
        in_feature2 = sys.argv[3]
        out_features = sys.argv[4]
        shpintersect(in_feature1, in_feature2, out_features)
