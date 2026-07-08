# -*- coding:utf-8-*-
import geopandas as gpd
from shapely.geometry import Point, Polygon
import os
import sys
import time

def new_file(dir, file_name):
    if not os.path.exists(os.path.join(dir, file_name)):
        return os.path.realpath(os.path.join(dir, file_name))
    else:
        os.remove(os.path.join(dir, file_name))
        return os.path.realpath(os.path.join(dir, file_name))


def time_interval(time_end, time_start):
    seconds = time_end - time_start
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def get_finish_net_point(input_path, out_path,prj_path,grid_size=150):
    temp_dir = os.path.dirname(input_path)
    print(f"临时目录: {temp_dir}")

    # 读取输入的shp文件
    print(f"正在读取输入的shapefile: {input_path}")
    gdf = gpd.read_file(input_path)
    print(f"成功读取输入的shapefile，CRS: {gdf.crs}")

    # 投影转换：如果输入数据的CRS是4490，转换为4549
    if gdf.crs is None:
        print("输入数据没有坐标参考系，请确保输入数据的CRS已定义。")
        return

    if gdf.crs.to_epsg() != 4549:  # 如果CRS不是4549则转换
        print(f"正在将输入数据从 {gdf.crs.to_epsg()} 投影转换为 4549")
        gdf = gdf.to_crs(epsg=4549)
        print("投影转换成功。")
        # gdf.to_file(os.path.join(temp_dir, "input_prj.shp"))
        gdf.to_file(prj_path, encoding='utf-8')


    # 创建渔网边界
    minx, miny, maxx, maxy = gdf.total_bounds
    print(f"输入数据的边界: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")
    fishnet_shp = new_file(temp_dir, "fishnet.shp")

    # 创建面状渔网
    # print("正在创建面状渔网...")
    fishnet_polygons = []
    # grid_size = 150  # 定义渔网的格子大小
    for x in range(int((maxx - minx) / grid_size)+1):
        for y in range(int((maxy - miny) / grid_size)+1):
            polygon = Polygon([
                (minx + x * grid_size, miny + y * grid_size),
                (minx + x * grid_size, miny + (y + 1) * grid_size),
                (minx + (x + 1) * grid_size, miny + (y + 1) * grid_size),
                (minx + (x + 1) * grid_size, miny + y * grid_size),
            ])
            if polygon.is_valid:  # 检查多边形的有效性
                fishnet_polygons.append(polygon)
            else:
                print(f"无效的多边形在位置: {(x, y)}")

    # 创建GeoDataFrame
    fishnet_gdf = gpd.GeoDataFrame(geometry=fishnet_polygons, crs='EPSG:4549')
    # fishnet_gdf.to_file(fishnet_shp)
    # print("面状渔网创建成功。")

    # 渔网与输入图层相交
    print("正在执行空间连接...")
    intersect_gdf = gpd.sjoin( fishnet_gdf,gdf, how='inner', predicate='intersects')
    # print(f"空间连接完成，交集结果包含 {len(intersect_gdf)} 个几何体。")
    # 渔网中心点
    intersect_gdf['geometry'] = intersect_gdf['geometry'].centroid
    # 添加XY坐标
    intersect_gdf['POINT_X'] = intersect_gdf['geometry'].x
    intersect_gdf['POINT_Y'] = intersect_gdf['geometry'].y
    # fishnet_centroid_shp = new_file(temp_dir, "fishnet_centroid.shp")
    # intersect_gdf.to_file(fishnet_centroid_shp)

    # 导出属性表至Excel
    export_df = intersect_gdf[['POINT_X', 'POINT_Y']]
    if out_path.endswith('.xlsx'):
        export_df.to_excel(out_path,  index=False)
    else:
        intersect_gdf.to_file(out_path)
    print("导出完成。",out_path)
    # return export_df,gdf.crs.to_epsg()



if __name__ == '__main__':
    time_begin = time.time()

    # 仅需要输入输入文件路径和输出文件路径
    input_path = r'E:\02Gitcode\gtus\static\shp\tz_tbhz\tz_tbhz.shp'
    xls_path = os.path.join(os.path.dirname(input_path), "result.xlsx")
    prj_path = os.path.join(os.path.dirname(input_path), "input_prj.shp")
    get_finish_net_point(input_path, xls_path,prj_path)

    time_end = time.time()
    print("times: %s" % time_interval(time_end, time_begin))











