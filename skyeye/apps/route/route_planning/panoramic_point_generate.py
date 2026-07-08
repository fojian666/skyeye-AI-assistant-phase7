# _*_ coding: utf-8 _*_
import os
import math
import geopandas as gpd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import Point
import pandas as pd
from shapely.geometry import Point, Polygon, MultiPoint
from shapely.ops import voronoi_diagram, unary_union
from pyproj import Transformer


def generate_panoramic_candidates(
    geojson_data,
    source_crs='EPSG:4490',
    radius=605.8,
):
    """按浦南全景点算法生成全局对齐的六边形中心点。"""
    features = (
        geojson_data.get('features') or []
        if isinstance(geojson_data, dict)
        and geojson_data.get('type') == 'FeatureCollection'
        else [geojson_data]
    )
    gdf = gpd.GeoDataFrame.from_features(features, crs=source_crs)
    if gdf.empty:
        return [], []
    projected = gdf.to_crs(epsg=4528)
    boundary = unary_union(projected.geometry)
    minx, miny, maxx, maxy = projected.total_bounds
    hex_width = float(radius) * 2
    hex_height = float(radius) * math.sqrt(3)
    minx -= hex_width
    maxx += hex_width
    miny -= hex_height
    maxy += hex_height
    start_x = minx - (minx % hex_width)
    start_y = miny - (miny % hex_height)

    projected_points = []
    y = start_y
    row = 0
    while y <= maxy + 1e-6:
        offset_x = hex_width / 2 if row % 2 else 0
        x = start_x
        while x <= maxx + 1e-6:
            center = Point(x + offset_x, y)
            vertices = [
                (
                    center.x + float(radius) * math.cos(index * math.pi / 3),
                    center.y + float(radius) * math.sin(index * math.pi / 3),
                )
                for index in range(6)
            ]
            if Polygon(vertices).intersects(boundary):
                projected_points.append([center.x, center.y])
            x += hex_width
        y += hex_height
        row += 1

    to_lonlat = Transformer.from_crs(4528, 4490, always_xy=True)
    lonlat_points = [
        list(to_lonlat.transform(point[0], point[1]))
        for point in projected_points
    ]
    return projected_points, lonlat_points
def new_file(dir, file_name):
    if not os.path.exists(os.path.join(dir, file_name)):
        return os.path.realpath(os.path.join(dir, file_name))
    else:
        os.remove(os.path.join(dir, file_name))
        return os.path.realpath(os.path.join(dir, file_name))

def get_square_finish_net_point(gdf, grid_size=700):
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
    out_shp_path = os.path.join(out_path, "result.shp")
    #计算全景半径
    # 正方形的边长 s = 对角线 / sqrt(2)
    # square_side = math.ceil(2 * radius / math.sqrt(2))

    # 计算六边形大小(外接圆半径)
    hex_radius = radius

    if isinstance(input_content, str):
        gdf = gpd.read_file(input_content)
    else:
        # 将坐标转换为 Shapely 的 Polygon 对象
        polygons = [Polygon(p) for p in input_content]
        # 创建 GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")

    # point_gdf = get_square_finish_net_point(gdf, grid_size=square_side) #正方形
    point_gdf = get_hexagon_finish_net_point(gdf, radius,out_path) #六边形
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


def get_hexagon_finish_net_point(gdf, grid_size,out_path):
    # 读取输入的shp文件
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
    cellWidth = 3 * grid_size  ## 渔网宽度
    cellHeight = (math.sqrt(3)) * grid_size  ## 渔网高度
    minx, miny, maxx, maxy = minx - cellWidth, miny - cellHeight, maxx + cellWidth, maxy + cellHeight

    # 创建面状渔网
    # print("正在创建面状渔网...")
    fishnet_polygons = []
    for x in range(int((maxx - minx) / cellWidth)+1):
        for y in range(int((maxy - miny) / cellHeight)+1):
            polygon = Polygon([
                (minx + x * cellWidth, miny + y * cellHeight),
                (minx + x * cellWidth, miny + (y + 1) * cellHeight),
                (minx + (x + 1) * cellWidth, miny + (y + 1) * cellHeight),
                (minx + (x + 1) * cellWidth, miny + y * cellHeight),
            ])
            if polygon.is_valid:  # 检查多边形的有效性
                fishnet_polygons.append(polygon)
            else:
                print(f"无效的多边形在位置: {(x, y)}")

    # 创建GeoDataFrame
    fishnet_gdf = gpd.GeoDataFrame(geometry=fishnet_polygons, crs='EPSG:3857')
    # 渔网与输入图层相交
    print("正在执行空间连接...")
    intersect_gdf = fishnet_gdf
    # 渔网中心点
    intersect_gdf['geometry'] = intersect_gdf['geometry'].centroid
    # 添加XY坐标
    intersect_gdf['POINT_X'] = intersect_gdf['geometry'].x
    intersect_gdf['POINT_Y'] = intersect_gdf['geometry'].y
    # print("导出完成。",out_path)
    # intersect_gdf.to_file(os.path.join(output_dir, 'point.shp'))
    gdf_copy = move_point(grid_size, intersect_gdf)
    gdf_list = [intersect_gdf, gdf_copy]
    merged_shapefile = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
    # merged_shapefile.to_file(os.path.join(output_dir, 'merge.shp'))
    # generate_hexagon_thiessen(merged_shapefile, out_path, grid_size) #生成六边形
    return merged_shapefile

def move_point(radius, gdf):
    deltaX = 1.5 * radius  ## 横向偏移
    deltaY = (math.sqrt(3) / 2) * radius  ## 纵向偏移
    gdf_copy = gdf.copy()
    gdf_copy['geometry'] = gdf_copy['geometry'].apply(lambda p: Point(p.x + deltaX, p.y + deltaY))
    return gdf_copy

def generate_hexagon_thiessen(points_gdf, output_path, hex_size=700):
    """
    生成六边形泰森多边形（确保非空结果）

    参数:
        input_points: 输入点要素(shp路径或GeoDataFrame)
        output_path: 输出目录路径
        hex_size: 六边形边长(米)

    返回:
        GeoDataFrame 包含六边形泰森多边形
    """

    if len(points_gdf) == 0:
        raise ValueError("输入点图层不能为空")

    # 2. 坐标系处理（转换为米制单位）
    if points_gdf.crs is None or points_gdf.crs.to_epsg() != 3857:
        points_gdf = points_gdf.to_crs(epsg=3857)

    # 3. 生成泰森多边形
    print("正在生成泰森多边形...")
    voronoi = voronoi_diagram(MultiPoint(points_gdf.geometry.tolist()))

    # 4. 转换为六边形网格
    print("正在转换为六边形网格...")
    hex_features = []
    print("共生成面：",len(voronoi.geoms),"共有点位：",len(points_gdf))
    for i, poly in enumerate(voronoi.geoms):
        if not poly.is_valid:
            continue

        center = poly.centroid
        if center.is_empty:
            continue

        # 生成六边形顶点
        hex_vertices = []
        for j in range(6):
            angle = math.radians(60 * j)  # 0度起始确保底边水平
            x = center.x + hex_size * math.cos(angle)
            y = center.y + hex_size * math.sin(angle)
            hex_vertices.append((x, y))

        hex_poly = Polygon(hex_vertices)
        if not hex_poly.is_valid:
            continue

        # 裁剪到泰森多边形范围内
        clipped = hex_poly.intersection(poly)
        if clipped.is_empty:
            continue

        hex_features.append({
            'geometry': clipped,
            'point_id': i + 1,
            'area': clipped.area,
            'edge_len': hex_size
        })

    if not hex_features:
        raise RuntimeError("未能生成任何六边形泰森多边形，请检查输入数据")

    # 5. 创建结果GeoDataFrame
    result_gdf = gpd.GeoDataFrame(hex_features, crs='EPSG:3857')

    # 6. 保存结果
    os.makedirs(output_path, exist_ok=True)
    output_shp = os.path.join(output_path, 'hexagon_thiessen.shp')
    result_gdf.to_file(output_shp)

    print(f"成功生成 {len(result_gdf)} 个六边形泰森多边形")
    return result_gdf


# if __name__ == '__main__':
#     input_path = r'E:\test\LTWG_原始\LTWG.shp'
#     radius = 700
#     out_path = r'E:\test\2'
#     generate_panoramic_point(input_path, radius,out_path)


