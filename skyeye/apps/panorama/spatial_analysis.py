# _*_ coding: utf-8 _*_
# @Time : 2025/8/12 13:58 
# @Author : xxx 
# @Version：V 0.1
# @File : spatial_analysis.py
# @desc :
import math
import time
import requests
import json
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor
from pyproj import CRS, Transformer
from shapely import Polygon
from shapely.geometry import Point, shape
from shapely.ops import transform


class IServerPointInPolygonChecker:
    def __init__(self):
        """
        初始化iServer点在面内查询器
        :param iserver_url: iServer服务地址（如 http://localhost:8090/iserver）
        """
        self.headers = {"Content-Type": "application/json"}
        # 服务缓存，避免重复创建
        self.service_cache = {}

    def check_points_against_services(self, services, alarms):
        """
        批量检查多个点是否在多个服务中的任何一个面内
        :param services: 服务配置列表，每个服务包含：
                         - data_service_name: 数据服务名称
                         - dataset_name: 数据集名称
                         - data_type: 服务名称
        :param alarms: 点列表，每个点为 (经度, 纬度) 元组
        :return: 结果字典，key为点坐标字符串，value为匹配的服务名称

        Returns:
            object:
        """
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=min(10, len(alarms))) as executor:
            for point in alarms:
                future = executor.submit(
                    self.check_point_against_services,
                    services,
                    point['longitude'],
                    point['latitude']
                )
                service_name = future.result()
                point['szdl'] = service_name

        return alarms

    def check_point_against_services(self, services: List[Dict], point_lon: float, point_lat: float):
        """
        检查单个点是否在多个服务中的任何一个面内
        :param services: 服务配置列表
        :param point_lon: 点的经度
        :param point_lat: 点的纬度
        :return: 匹配的服务名称（None表示不在任何面内）
        """
        result = []
        for service in services:
            # 检查点是否在当前服务的面内
            if self.is_point_in_service_polygon(
                    service["url"],
                    service['datasource_name'],
                    service["datasets_name"],
                    point_lon,
                    point_lat
            ):
                result.append(service["data_type"][0:2])

        return result

    def is_point_in_service_polygon(self, url: str,datasource_name:str, datasets_name: str,
                                    point_lon: float, point_lat: float) -> bool:
        """
        判断点是否在指定服务的矢量面内
        :param url: 数据服务
        :param datasets_name: 数据集名称
        :param point_lon: 点的经度
        :param point_lat: 点的纬度
        :return: True表示点在面内，False表示不在
        """
        # 地球半径(米)
        earth_radius = 6378137.0
        value = 700 / (math.pi * 2 * earth_radius / 360)

        # 构建查询参数
        query_params = {
            "getFeatureMode": "BUFFER",
            "datasetNames": [f"{datasource_name}:{datasets_name}"],
            "geometry": {
                "id": 0,
                "style": None,
                "parts": [1],
                "points": [{"x": point_lon, "y": point_lat}],
                "type": "POINT"
            },
            "bufferDistance": value
        }

        # 发送查询请求
        url = f"{url}/featureResults.json"
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=query_params,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
        except Exception as e:
            print(f"服务查询失败: {e}")
            return False

        # 检查查询是否成功
        if not result.get("succeed", False):
            print(f"查询失败: '未知错误')")
            return False

        # 获取新资源位置
        new_resource_url = result.get('newResourceLocation')
        if not new_resource_url:
            return False

        # 获取实际查询结果
        try:
            res_response = requests.get(
                new_resource_url,
                headers=self.headers,
                timeout=15
            )
            res_response.raise_for_status()
            res = res_response.json()
        except Exception as e:
            print(f"获取查询结果失败: {new_resource_url} - {e}")
            return False

        # 获取特征URI列表
        feature_uris = res.get("featureUriList", [])
        if not feature_uris:
            return False

        # 创建点几何对象
        point = Point(point_lon, point_lat)

        # 遍历所有特征URI，检查点是否在面内
        for feature_uri in feature_uris:
            # 获取完整特征信息
            feature = self._get_feature(feature_uri)
            if not feature:
                continue

            # 获取几何信息
            geometry = feature.get("geometry")
            if not geometry:
                continue

            # 创建多边形对象
            polygon = self._create_polygon_from_geometry(geometry)
            if polygon and polygon.contains(point):
                return True

        return False

    def _get_feature(self, feature_uri: str) -> Optional[Dict]:
        """获取单个特征的完整信息"""
        try:
            # 确保URI以.json结尾
            if not feature_uri.endswith(".json"):
                feature_uri += ".json"

            response = requests.get(
                feature_uri,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取特征失败 ({feature_uri}): {e}")
            return None

    def _create_polygon_from_geometry(self, geometry: Dict) -> Optional[Polygon]:
        """从几何描述创建Shapely多边形"""
        try:
            # 尝试直接使用GeoJSON格式创建
            if geometry.get("type") == "Polygon":
                coordinates = geometry.get("coordinates")
                if coordinates and len(coordinates) > 0:
                    # 只取外环（忽略内环）
                    return Polygon(coordinates[0])
            # 尝试使用iServer自定义格式
            if geometry.get("type") == "REGION" and "points" in geometry:
                points = geometry["points"]
                coords = [(pt["x"], pt["y"]) for pt in points]
                return Polygon(coords)

            # 尝试使用GeoJSON特征格式
            if geometry.get("type") == "Feature":
                return shape(geometry["geometry"])
        except Exception as e:
            print(f"创建多边形失败: {e}")
        return None


# --------------------------
# 使用示例
# --------------------------
if __name__ == "__main__":
    start_time = time.time()
    # 定义多个服务
    services = [
        {
            "datasource_name": "jscj",
            "dataset_name": "cj",
            "data_type": "耕地服务",
            "url": "http://192.168.60.42:8090/iserver/services/data-cj/rest/data"
        },
        {
            "datasource_name": "jscj",
            "dataset_name": "cj",
            "data_type": "林地服务",
            "url": "http://192.168.60.42:8090/iserver/services/data-cj/rest/data"
        }
    ]
    # 定义多个点
    points = [{
        'latitude': 32.199,
        'longitude': 118.956
    }, {
        'latitude': 32.200,
        'longitude': 118.950
    }, {
        'latitude': 32.195,
        'longitude': 118.990
    }

    ]

    # 初始化查询器
    checker = IServerPointInPolygonChecker()

    # 批量检查所有点
    results = checker.check_points_against_services(services, points)

    # 打印结果
    print("\n结果汇总:")
    for point_str in results:
        print(point_str)

    print(f"\n总耗时: {time.time() - start_time:.2f}秒")
