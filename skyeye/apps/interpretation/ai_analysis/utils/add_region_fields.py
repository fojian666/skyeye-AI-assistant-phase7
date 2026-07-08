#-*- coding: utf-8 -*-
import geopandas as gpd

def add_XZQ_fields(target_shp, area_field):
    """
    添加行政区字段值
    Args:
        target_shp: 目标图层
        area_field: 添加字段名称

    """
    # 读取原始Shapefile文件
    gdf = gpd.read_file(target_shp)
    # add XZQ field
    gdf['XZQ'] = area_field
    # 输出文件
    gdf.to_file(target_shp)


def join_area_fields(target_shp, reference_shp, output_file, area_field):
    """
    将根据地区图层，将地区字段赋予相交要素,多对一时用";"隔开并存在同一字段里
    :param target_shp: 目标图层（要素图层）
    :param reference_shp: 参照图层（地区图层）
    :param output_file: 输出结果图层
    :param area_field: 地区字段
    :return:
    """

    # 读取原始Shapefile文件
    gdf = gpd.read_file(target_shp)
    # add XZQ field
    gdf['XZQ'] = area_field
    # 读取参考Shapefile文件
    ref_gdf = gpd.read_file(reference_shp)
    # 设置投影
    ref_gdf_ = ref_gdf.to_crs('EPSG:{}'.format(gdf.crs.to_epsg()))
    # 计算交集
    intersection = gpd.overlay(gdf, ref_gdf_, how='intersection')
    # 输出文件
    intersection.to_file(output_file)
    return intersection


if __name__ == '__main__':

    target_shp1 = r"C:\Users\Administrator\Desktop\test\1.shp"
    reference_shp1 = 0
    output_file1 = r''
    area_field1 = 'NJ'
    print("栅格转矢量:开始添加属性字段")
    if reference_shp1 != "1":
        join_area_fields(target_shp1, reference_shp1, output_file1, area_field1)
    else:
        print(add_XZQ_fields(target_shp1, area_field1))

    print("属性字段添加完成")
