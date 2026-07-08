# _*_ coding: utf-8 _*_
import os
import math
import geopandas as gpd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Point

def new_file(dir, file_name):
    if not os.path.exists(os.path.join(dir, file_name)):
        return os.path.realpath(os.path.join(dir, file_name))
    else:
        os.remove(os.path.join(dir, file_name))
        return os.path.realpath(os.path.join(dir, file_name))


def get_finish_net_point(gdf,grid_size=700):
    # 读取输入的shp文件
    # print(f"正在读取输入的shapefile: {input_path}")
    # gdf = gpd.read_file(input_path)
    print(f"成功读取输入的shapefile，CRS: {gdf.crs}")

    if gdf.crs is None:
        print("输入数据没有坐标参考系，请确保输入数据的CRS已定义。")
        return

    if gdf.crs.to_epsg() != 3857:  # 如果CRS不是4549则转换
        print(f"正在将输入数据从 {gdf.crs.to_epsg()} 投影转换为 3857")
        gdf = gdf.to_crs(epsg=3857)
        print("投影转换成功。")


    # 创建渔网边界
    minx, miny, maxx, maxy = gdf.total_bounds
    print(f"输入数据的边界: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")

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
    fishnet_gdf = gpd.GeoDataFrame(geometry=fishnet_polygons, crs='EPSG:3857')
    # 渔网与输入图层相交
    print("正在执行空间连接...")
    intersect_gdf = gpd.sjoin( fishnet_gdf,gdf, how='inner', predicate='intersects')
    # print(f"空间连接完成，交集结果包含 {len(intersect_gdf)} 个几何体。")
    # 渔网中心点
    intersect_gdf['geometry'] = intersect_gdf['geometry'].centroid
    # 添加XY坐标
    intersect_gdf['POINT_X'] = intersect_gdf['geometry'].x
    intersect_gdf['POINT_Y'] = intersect_gdf['geometry'].y
    # print("导出完成。",out_path)
    return intersect_gdf


def generate_panoramic_point(input_content, radius, out_path):
    """
    根据上传的shp文件生成全景点
    :param input_content: shp文件路径
    :param radius: 全景规划半径
    :param out_path: 输出地址
    :return:
    """
    print(input_content, radius, out_path)
    out_shp_path = os.path.join(out_path, "result.shp")
    #计算全景半径
    # 正方形的边长 s = 对角线 / sqrt(2)
    square_side = math.ceil(2 * radius / math.sqrt(2))
    if isinstance(input_content, str):
        gdf = gpd.read_file(input_content)
    else:
        # 将坐标转换为 Shapely 的 Polygon 对象
        polygons = [Polygon(p) for p in input_content]
        # 创建 GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")

    point_gdf = get_finish_net_point(gdf,grid_size=square_side)
    # point_gdf = gpd.read_file(shp_path)
    if not point_gdf.crs == gdf.crs:
        point_gdf = point_gdf.to_crs(gdf.crs)
        point_gdf['ZXDX'] = point_gdf['geometry'].x
        point_gdf['ZXDY'] = point_gdf['geometry'].y
        point_gdf = point_gdf[['ZXDX', 'ZXDY','geometry']]
    # 根据边界裁剪点
    points_within_boundary = point_gdf[point_gdf.within(gdf.unary_union)]
    points_within_boundary = points_within_boundary[['ZXDX', 'ZXDY', 'geometry']]
    points_within_boundary.to_file(out_shp_path)
    point_coordinates = list(map(list, zip(points_within_boundary['ZXDY'], points_within_boundary['ZXDX'])))
    print("规划完成")
    return point_coordinates

def panoramic_point_to_shp(points_list, out_path):
    out_shp_path = os.path.join(out_path, "result.shp")
    # 将点坐标转换为 Shapely 的 Point 对象
    points = [Point(lon, lat) for lon, lat in points_list]
    # 创建 GeoDataFrame
    point_gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")  # 使用 WGS84 坐标系
    point_gdf['ZXDX'] = point_gdf['geometry'].x
    point_gdf['ZXDY'] = point_gdf['geometry'].y
    # 保存为 SHP 文件
    point_gdf.to_file(out_shp_path)


if __name__ == '__main__':
    input_path = r'C:\Users\Administrator\Desktop\19试点\19试点.shp'
    radius = 700
    out_path = r'C:\Users\Administrator\Desktop\19试点'
    # generate_panoramic_point(input_path, radius,out_path)

    coor = [[[118.99081707000732, 32.14294258429079], [118.9888858795166, 32.13791769378039],
          [118.9914608001709, 32.13456776677346], [118.99746894836426, 32.13473955790201],
          [118.99815559387207, 32.13783179821611], [118.99678230285645, 32.14186888973729],
          [118.99678230285645, 32.14186888973729], [118.99081707000732, 32.14294258429079]], [
             [119.00139570236206, 32.14142160350774], [119.00068759918213, 32.13985400945962],
             [119.00294065475464, 32.13744893365977], [119.00450706481934, 32.14043380451851],
             [119.0033483505249, 32.141593394636295], [119.0033483505249, 32.141593394636295],
             [119.00139570236206, 32.14142160350774]]]
    generate_panoramic_point(coor, 700, out_path)

    # points_list = [
    #     [118.99081707000732, 32.14294258429079],
    #     [118.9888858795166, 32.13791769378039],
    #     [118.9914608001709, 32.13456776677346],
    #     [118.99746894836426, 32.13473955790201]
    # ]
    # out_shp_path = r'E:\LTWG\1.shp'
    # panoramic_point_to_shp(points_list, out_shp_path)
