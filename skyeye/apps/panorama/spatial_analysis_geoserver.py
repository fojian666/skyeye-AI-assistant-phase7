# _*_ coding: utf-8 _*_
# @Time : 2025/8/12 13:58
# @Author : xxx
# @Version：V 0.1
# @File : spatial_analysis.py
# @desc : GeoServer点在面内判断工具
import math
import time
import requests
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import Point


class GeoServerPointInPolygonChecker:
    def __init__(self):
        """
        初始化GeoServer点在面内查询器
        """
        self.headers = {"Content-Type": "application/json"}
        # 服务缓存
        self.service_cache = {}

    def check_points_against_services(self, services, alarms):
        """
        批量检查多个点是否在多个GeoServer服务面内
        :param services: GeoServer服务配置列表
        :param alarms: 点列表，每个点为 (经度, 纬度) 字典
        :return: 带匹配结果的点列表
        """
        with ThreadPoolExecutor(max_workers=min(10, len(alarms))) as executor:
            futures = []
            for point in alarms:
                future = executor.submit(
                    self.check_point_against_services,
                    services,
                    point['longitude'],
                    point['latitude']
                )
                futures.append((point, future))

            # 赋值结果
            for point, future in futures:
                service_name = future.result()
                point['szdl'] = service_name

        return alarms

    def check_point_against_services(self, services: List[Dict], point_lon: float, point_lat: float):
        """
        检查单个点是否在多个GeoServer面内
        """
        result = []
        for service in services:
            if self.is_point_in_service_polygon(
                    service["url"],
                    service["datasource_name"],
                    service["datasets_name"],
                    point_lon,
                    point_lat
            ):
                result.append(service["data_type"][0:2])
        return result

    def is_point_in_service_polygon(
            self,
            geoserver_url: str,
            workspace: str,
            layer_name: str,
            point_lon: float,
            point_lat: float
    ) -> bool:
        """
        核心：通过GeoServer WFS接口判断点是否在面内（标准OGC空间查询）
        :param geoserver_url: GeoServer根地址 (如 http://localhost:8080/geoserver)
        :param workspace: GeoServer工作区名称
        :param layer_name: 发布的矢量图层名
        :param point_lon: 经度
        :param point_lat: 纬度
        :return: True/False
        """
        # WFS服务标准接口地址
        wfs_url = f"{geoserver_url}"

        # WFS查询参数（CQL_FILTER空间过滤：点在面内）
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": f"{workspace}:{layer_name}",  # 工作区:图层名
            "outputFormat": "application/json",  # 返回JSON格式
            # 核心：空间过滤条件，判断点是否包含在面要素中
            "CQL_FILTER": f"INTERSECTS(the_geom, POINT({point_lon} {point_lat}))",
            "maxFeatures": 1  # 只要找到1个匹配就返回，提升性能
        }

        try:
            response = requests.get(
                wfs_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # 判断是否查询到要素（有结果=点在面内）
            features = data.get("features", [])
            return len(features) > 0

        except Exception as e:
            print(f"GeoServer查询失败: {e}")
            return False


# --------------------------
# GeoServer 使用示例
# --------------------------
if __name__ == "__main__":
    start_time = time.time()

    # ===================== 配置你的GeoServer服务 =====================
    # 关键参数：url(GeoServer地址)、workspace(工作区)、layer_name(图层名)
    geoserver_services = [
        {
            "workspace": "ws",          # GeoServer工作区
            "layer_name": "GD_WGS84",  # 耕地图层名
            "data_type": "耕地服务",
            "url": "http://skyeye.isitai.cn:8086/geoserver/ws/wfs"  # GeoServer默认端口8080
        }
    ]

    # 测试点
    test_points = [
        {'latitude': 32.199, 'longitude': 118.956},
        {'latitude': 32.200, 'longitude': 118.950},
        {'latitude': 32.195, 'longitude': 118.990}
    ]

    # 初始化GeoServer校验器
    checker = GeoServerPointInPolygonChecker()
    results = checker.check_points_against_services(geoserver_services, test_points)

    # 输出结果
    print("\n=== 点面分析结果 ===")
    for point in results:
        print(point)
    print(f"\n总耗时: {time.time() - start_time:.2f}秒")