# -*- coding: utf-8 -*-
import os
import geopandas as gpd
import pandas as pd

def merge_shp_fun(input_dir, output_file):
    """
    合并shp图层
    Args:
        input_dir:需合并文件的文件夹
        output_file: 合并文件输出路径

    Returns:

    """
    shp_list, gdf_list = [], []
    for i_path in os.listdir(input_dir):
        if i_path.endswith('.shp'):
            file = os.path.join(input_dir, i_path)
            shp_list.append(file)
            gdf_list.append(gpd.read_file(file))

    # 输出文件
    merged_shapefile = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    merged_shapefile.to_file(output_file)


if __name__ == '__main__':
    input_dir = r"C:\Users\Administrator\Desktop\shp\all"
    output_file = r"C:\Users\Administrator\Desktop\shp\all\异龙湖2022_2023结果合并_Merge.shp"
    merge_shp_fun(input_dir, output_file)
