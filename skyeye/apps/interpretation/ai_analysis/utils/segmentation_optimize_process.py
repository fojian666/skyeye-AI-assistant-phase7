# -*- coding: utf-8 -*-
import geopandas as gpd
import warnings
# 忽略所有警告
warnings.filterwarnings("ignore")

def intersectfeatures(source_path, target_path, result_path):
    """
    相交性分析
    Args:
        source_path: 源数据路径
        target_path: 目标路径
        result_path: 结果存储路径

    Returns:

    """

    print("执行分割结果处理")
    shp1 = gpd.read_file(source_path)
    shp2 = gpd.read_file(target_path)
    # 获取FID值
    shp1['FID_BAK1'] = shp1.index
    shp2['FID_BAK2'] = shp2.index
    intersection = gpd.overlay(shp1, shp2, how='intersection')
    intersection.to_file(result_path)


def selectLayerByLocation(source_path,target_path):
    """
    按位置选择分析
    Args:
        source_path:源数据路径
        target_path:目标路径

    Returns:

    """
    target_gdf = gpd.read_file(target_path)
    source_gdf = gpd.read_file(source_path)
    intersection = gpd.sjoin(target_gdf, source_gdf, how='inner', op='intersects')
    target_gdf = target_gdf.loc[intersection.index]


if __name__ == '__main__':
    source_path = r'C:\Users\Administrator\Desktop\test\2\in_10_segmentation.shp'
    target_path = r'C:\Users\Administrator\Desktop\test\2\in_101_segmentation.shp'
    result_path = r'C:\Users\Administrator\Desktop\test\seg.shp'
    intersectfeatures(source_path, target_path, result_path)
    # selectLayerByLocation(source_path, target_path)