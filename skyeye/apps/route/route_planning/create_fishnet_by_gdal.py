# -*- coding:utf-8-*-
import geopandas as gpd
from shapely.geometry import Polygon
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


def calc_adaptive_grid_size(minx, miny, maxx, maxy, default=150, min_grid=20, min_cells=3):
    """根据规划区域范围自适应计算渔网格子大小，避免小区域只生成 1 个航点。"""
    width = maxx - minx
    height = maxy - miny
    max_dim = max(width, height)
    if max_dim <= 0:
        return min_grid
    grid_size = min(default, max_dim / min_cells)
    return max(min_grid, grid_size)


def _build_fishnet_intersections(gdf, grid_size, progress_callback=None):
    """生成渔网并返回与规划面相交的中心点。"""
    minx, miny, maxx, maxy = gdf.total_bounds
    fishnet_polygons = []
    x_steps = max(1, int((maxx - minx) / grid_size) + 1)
    y_steps = max(1, int((maxy - miny) / grid_size) + 1)
    for x in range(x_steps):
        for y in range(y_steps):
            polygon = Polygon([
                (minx + x * grid_size, miny + y * grid_size),
                (minx + x * grid_size, miny + (y + 1) * grid_size),
                (minx + (x + 1) * grid_size, miny + (y + 1) * grid_size),
                (minx + (x + 1) * grid_size, miny + y * grid_size),
            ])
            if polygon.is_valid:
                fishnet_polygons.append(polygon)
        if progress_callback:
            progress_callback(x + 1, x_steps)

    if progress_callback:
        progress_callback(x_steps, x_steps, '正在执行地块与渔网空间相交')
    fishnet_gdf = gpd.GeoDataFrame(geometry=fishnet_polygons, crs=gdf.crs)
    intersect_gdf = gpd.sjoin(fishnet_gdf, gdf, how='inner', predicate='intersects')
    if intersect_gdf.empty:
        return intersect_gdf
    intersect_gdf = intersect_gdf.copy()
    # 同一个渔网格可能同时与多个相邻地块相交，spatial join 会为它生成多行。
    # 规划只需要每个格子一个航点，按渔网原始索引去重可避免重复规划。
    intersect_gdf = intersect_gdf[
        ~intersect_gdf.index.duplicated(keep='first')
    ]
    intersect_gdf['geometry'] = intersect_gdf['geometry'].centroid
    intersect_gdf['POINT_X'] = intersect_gdf['geometry'].x
    intersect_gdf['POINT_Y'] = intersect_gdf['geometry'].y
    intersect_gdf = intersect_gdf.drop_duplicates(
        subset=['POINT_X', 'POINT_Y'],
        keep='first',
    )
    return intersect_gdf


def get_finish_net_point(
    input_path,
    out_path,
    prj_path,
    grid_size=150,
    min_points=3,
    min_grid=20,
    adaptive_grid=True,
    progress_callback=None,
):
    temp_dir = os.path.dirname(input_path)
    print(f"临时目录: {temp_dir}")

    # 读取输入的shp文件
    print(f"正在读取输入的shapefile: {input_path}")
    gdf = gpd.read_file(input_path)
    if progress_callback:
        progress_callback(1, 1, '规划区域读取完成')
    print(f"成功读取输入的shapefile，CRS: {gdf.crs}")

    # 投影转换：如果输入数据的CRS是4490，转换为4549
    if gdf.crs is None:
        raise ValueError('规划区域缺少坐标系信息')

    if gdf.crs.to_epsg() != 4549:
        print(f"正在将输入数据从 {gdf.crs.to_epsg()} 投影转换为 4549")
        gdf = gdf.to_crs(epsg=4549)
        print("投影转换成功。")
    gdf.to_file(prj_path, encoding='utf-8')
    if progress_callback:
        progress_callback(1, 1, '规划区域投影转换完成')

    minx, miny, maxx, maxy = gdf.total_bounds
    print(f"输入数据的边界: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")

    current_grid = (
        calc_adaptive_grid_size(
            minx,
            miny,
            maxx,
            maxy,
            default=grid_size,
            min_grid=min_grid,
        )
        if adaptive_grid
        else float(grid_size)
    )
    intersect_gdf = _build_fishnet_intersections(
        gdf, current_grid, progress_callback=progress_callback
    )
    while (
        adaptive_grid
        and len(intersect_gdf) < min_points
        and current_grid > min_grid
    ):
        current_grid = max(min_grid, current_grid // 2)
        print(f"航点不足，缩小渔网格子为 {current_grid}m 后重试")
        intersect_gdf = _build_fishnet_intersections(
            gdf, current_grid, progress_callback=progress_callback
        )

    if intersect_gdf.empty:
        raise ValueError('规划区域过小或无效，无法生成航点，请扩大绘制范围')

    print(f"渔网格子大小: {current_grid}m，生成航点数: {len(intersect_gdf)}")

    export_df = intersect_gdf[['POINT_X', 'POINT_Y']]
    if out_path.endswith('.xlsx'):
        export_df.to_excel(out_path, index=False)
    else:
        intersect_gdf.to_file(out_path)
    print("导出完成。", out_path)
    if progress_callback:
        progress_callback(1, 1, f'航点渔网生成完成，共 {len(intersect_gdf)} 个航点')



if __name__ == '__main__':
    time_begin = time.time()

    # 仅需要输入输入文件路径和输出文件路径
    input_path = r'E:\02Gitcode\gtus\static\shp\tz_tbhz\tz_tbhz.shp'
    xls_path = os.path.join(os.path.dirname(input_path), "result.xlsx")
    prj_path = os.path.join(os.path.dirname(input_path), "input_prj.shp")
    get_finish_net_point(input_path, xls_path,prj_path)

    time_end = time.time()
    print("times: %s" % time_interval(time_end, time_begin))











