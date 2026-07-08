# -*- coding:utf-8-*-
"""
@Author         :  hanpeipei
@Version        :
------------------------------------
@File           :  create_fishNet_point.py
@Description    :  Arcpy 航线规划创建渔网
@CreateTime     :  2021/09/21 11:10
------------------------------------
@ModifyTime     :
"""

import arcpy
arcpy.env.overwriteOutput = True
from arcpy import env
import os, sys, time

def newFile(dir, fileName):
    file0 = ""
    if not arcpy.Exists(os.path.join(dir, fileName)):
        file0 = os.path.realpath(os.path.join(dir, fileName))
    else:
        arcpy.Delete_management(os.path.join(dir, fileName))
        file0 = os.path.realpath(os.path.join(dir, fileName))
    return file0

def time_interval(time_end, time_start):
    seconds = time_end - time_start
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def Get_finshnet_point(input_path, prj_path, out_path):
    temp_dir = os.path.dirname(input_path)
    env.workspace = temp_dir
    env.overwriteOutput = True
    """
    对图斑做投影转换，将地理坐标系CGCS2000转换为高斯克吕格3度带120E
    """

    # 获取输入坐标系
    input_des = arcpy.Describe(input_path)
    input_sys = input_des.spatialReference   #投影转换后的坐标

    # 输入数据投影
    if input_sys.GCSCode == 4490:  #wGS-84
        sys = arcpy.SpatialReference(4549)  #4549  120E
        arcpy.Project_management(input_path, prj_path, sys)
        out_des = arcpy.Describe(prj_path)

    elif input_sys.GCSCode == 4326:
        sys = arcpy.SpatialReference(4549)
        arcpy.Project_management(input_path, prj_path, sys)
        out_des = arcpy.Describe(prj_path)
    else:
        prj_path = input_path
        out_des = arcpy.Describe(prj_path)

    """
    创建渔网
    思路：1.首先对转换投影后的shp文件做-创建渔网，保留labels标签
            2.对渔网创建一个临时图层，按位置选择出与监测图斑相交的渔网
            3.对labels标签点创建图层，将该图层与2中的结果做相交得到渔网中心点
            4.对3中的shp结果添加X,Y字段，并计算中心带你坐标
    """

    # Process: 创建渔网
    fishnet_shp = newFile(temp_dir, "fishnet.shp")   #存储渔网的路径
    fishnet_label_shp = newFile(temp_dir, "fishnet_label.shp")  #Arcgis会自己生成渔网的中心点，该变量为生成的渔网中心点存储路径
    arcpy.CreateFishnet_management(fishnet_shp,
                                   str(out_des.extent.XMin) + " " + str(out_des.extent.YMin), str(out_des.extent.XMin) + " " + str(out_des.extent.YMin + 10),
                                   "150", "150", "", "",
                                   str(out_des.extent.XMax) + " " + str(out_des.extent.YMax), "LABELS", out_des.extent, "POLYGON")

    # Process: 创建渔网要素图层
    fishnet_Layer = "fishnet_Layer"
    arcpy.MakeFeatureLayer_management(fishnet_shp, fishnet_Layer)

    # Process: 按位置选择图层
    arcpy.SelectLayerByLocation_management(fishnet_Layer, "INTERSECT", prj_path, "", "NEW_SELECTION")

    # Process: 创建要素图层 (2)
    fishnet_label_Layer = "fishnet_label_Layer"
    arcpy.MakeFeatureLayer_management(fishnet_label_shp, fishnet_label_Layer)

    # Process: 相交
    Intersect_center_point_shp = newFile(temp_dir, "Intersect_center_point.shp")
    arcpy.Intersect_analysis("fishnet_Layer #;fishnet_label_Layer #", Intersect_center_point_shp, "ALL", "", "INPUT")

    # 添加XY坐标
    arcpy.AddXY_management(Intersect_center_point_shp)

    #导出属性表至excel表
    #v1_xls = os.path.join(temp_dir, 'result.xls')
    arcpy.TableToExcel_conversion(Intersect_center_point_shp, out_path, "NAME", "CODE")


if __name__ == '__main__':
    time_begin = time.time()
    input_path = sys.argv[1]
    prj_path = sys.argv[2]
    out_path = sys.argv[3]
    Get_finshnet_point(input_path, prj_path, out_path)
    time_end = time.time()

