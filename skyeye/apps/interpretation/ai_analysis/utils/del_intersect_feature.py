# -*- coding: utf-8 -*-
import os

import geopandas as gpd
import warnings
import pandas as pd
import pyproj
import apps.interpretation.ai_config as cg
import pandas as pd
logger = cg.logger
# 忽略所有警告
warnings.filterwarnings("ignore")
def del_intersect_merge(shp1_path, shp2_path, merge_shp_path):
    """
    图层擦除
    Args:
        shp1_path: 第一个shp路径
        shp2_path: 第二个shp路径
        merge_shp_path: 输出路径
    """
    shp1 = gpd.read_file(shp1_path)
    shp2 = gpd.read_file(shp2_path)
    # 获取坐标系信息
    # crs_info = shp1.crs.to_wkt()
    if shp1.crs is None:
        crs_info = shp1.crs
    else:
        crs_info = shp1.crs.to_wkt()
    # 获取FID值
    shp1['FID_BAK1'] = shp1.index
    shp2['FID_BAK2'] = shp2.index
    #计算两个图层的相交部分
    intersection = gpd.overlay(shp1, shp2, how='intersection')
    #判断坐标系是否相等
    if crs_info is None:
        logger.infor("栅格转矢量:判断坐标系，crs_info is None.......")
        intersection_prj = intersection
        intersection_prj.crs = None
        shp1_prj = shp1
        shp2_prj = shp2
    else:
        logger.info("栅格转矢量:判断坐标系.......")
        if pyproj.CRS(crs_info).is_projected:
            intersection_prj = intersection
            shp1_prj = shp1
            shp2_prj = shp2
        else:
            #判断坐标系是不是与cgcs2000或者wgs84匹配
            if pyproj.Transformer.from_crs(crs_info, 4490, always_xy=True).has_inverse:
                #转换到投影坐标系
                intersection_prj = intersection.set_crs('EPSG:{}'.format(4490),allow_override=True).to_crs('EPSG:{}'.format(4549))
                shp1_prj = shp1.set_crs('EPSG:{}'.format(4490),allow_override=True).to_crs('EPSG:{}'.format(4549))
                shp2_prj = shp2.set_crs('EPSG:{}'.format(4490),allow_override=True).to_crs('EPSG:{}'.format(4549))
            elif pyproj.Transformer.from_crs(crs_info, 4326, always_xy=True).has_inverse:
                shp1_prj = shp1.set_crs('EPSG:{}'.format(4326),allow_override=True).to_crs('EPSG:{}'.format(3857))
                shp2_prj = shp2.set_crs('EPSG:{}'.format(4326),allow_override=True).to_crs('EPSG:{}'.format(3857))
            else:
                logger.info("栅格转矢量:坐标系既不是投影坐标系也不是2000或者84，可能转换失败.......")
                intersection_prj = intersection
                shp1_prj = shp1
                shp2_prj = shp2
    logger.info("栅格转矢量:开始计算面积............")
    #计算图斑面积
    intersection_prj['in_area'] = intersection_prj.geometry.area
    FID1 = "FID_BAK1"
    FID2 = "FID_BAK2"
    shp1_del_list = []
    shp2_del_list = []
    logger.info("栅格转矢量:开始剔除图斑............")
    # 遍历每一行，获取需要剔除的图斑
    for index, row in intersection_prj.iterrows():
        if (row["in_area"] / row["TBMJ_1"] > 0.5) or (row["in_area"] / row["TBMJ_2"] > 0.5):
            shp1_del_list.append(row[FID1])
            shp2_del_list.append(row[FID2])

    # 去重并进行排序
    shp1_del_list = sorted(list(set(shp1_del_list)))
    shp2_del_list = sorted(list(set(shp2_del_list)))
    # 批量删除
    shp1_prj = shp1_prj[~shp1_prj[FID1].isin(shp1_del_list)]
    shp2_prj = shp2_prj[~shp2_prj[FID2].isin(shp2_del_list)]
    logger.info("栅格转矢量:开始进行擦除操作............")
    # 执行擦除操作
    # 检查 intersection_prj 是否为空
    if not intersection_prj.empty:
        #计算不同的部分
        erase_shp1 = shp1_prj.difference(intersection_prj.unary_union)
        erase_shp1 = gpd.GeoDataFrame(geometry=erase_shp1)
    else:
        # 处理 intersection_prj 为空的情况
        erase_shp1 = shp1_prj.copy()  # 如果 intersection_prj 为空，直接复制 shp1_prj
    # 检查 intersection_prj 是否为空
    if not intersection_prj.empty:
        erase_shp2 = shp2_prj.difference(intersection_prj.unary_union)
        # # 将 GeoSeries 转换为 GeoDataFrame
        erase_shp2 = gpd.GeoDataFrame(geometry=erase_shp2)
    else:
        # 处理 intersection_prj 为空的情况
        erase_shp2 = shp2_prj.copy()  # 如果 intersection_prj 为空，直接复制 shp1_prj

    # 重命名列以保持原始列名
    erase_shp1.columns = [str(col) for col in erase_shp1.columns]
    erase_shp2.columns = [str(col) for col in erase_shp2.columns]
    logger.info("栅格转矢量:开始图层融合和计算质心坐标............")
    # 将处理完毕的两个源图层融合
    
    merge_shp_prj = gpd.GeoDataFrame(pd.concat([erase_shp1, erase_shp2], ignore_index=True))
    merge_shp_prj["TBMJ"] = merge_shp_prj.area
    # 计算质心 x 坐标、质心 y 坐标
    merge_shp_prj["ZXDX"] = merge_shp_prj.centroid.x
    merge_shp_prj["ZXDY"] = merge_shp_prj.centroid.y
    merge_shp_prj = merge_shp_prj.to_crs(crs_info)
    merge_shp_prj.to_file(merge_shp_path)
    return len(merge_shp_prj),merge_shp_prj


if __name__ == '__main__':
    input_path = r'C:\Users\Administrator\Desktop\shp\shp'
    out_path = r'C:\Users\Administrator\Desktop\shp\all'
    shp1_name = '异龙湖2022年一季度影像'
    shp2_name = '异龙湖影像2023一季度影像'
    for i in os.listdir(input_path):
        if i.endswith('.shp') and (shp1_name in i):

            shp1_path = os.path.join(input_path, i)
            shp2_path = os.path.join(input_path, shp2_name+i.split(f'{shp1_name}')[1])
            temp_path = r'C:\Users\Administrator\Desktop\shp\temp'
            merge_shp_path = os.path.join(out_path,os.path.basename(i).split('.')[0]+'_result.shp')
            # process_fid(shp1_path, shp2_path)
            del_intersect_merge(shp1_path, shp2_path,merge_shp_path)
            print("image_seg_erasure over!")
    
    
