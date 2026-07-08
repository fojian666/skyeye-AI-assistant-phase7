# @Time : 2023/7/19 17:40
# @Author : Ma Guorui
# @Description : 🗺

import geopandas as gpd
from pyproj import Transformer
import numpy as np
import cv2 as cv
from osgeo import gdal
from logger import Logger
from shapely.geometry import *
from apps.panorama.uav_monitoring_service_dev.configs.device_config import *
import os

LOGGER = Logger(logname='map_module.log', loglevel=4, logger='MapModuleInfo').getlog()


class BaseMap:
    def __init__(self,
                 map_name: str,
                 dsm_map_name: str,
                 land_patch_name: str):

        if not os.path.exists(map_name):
            LOGGER.error("正射影像文件路径不存在")
            raise '请检查正射影像文件路径是否正确'
        self.map_name = map_name  # 地图名称
        self.dsm_map_name = dsm_map_name
        if not os.path.exists(land_patch_name):
            LOGGER.error("图斑文件路径不存在")
            raise '请检查图斑文件路径是否正确'
        self.land_patch_name = land_patch_name  # 多边形信息
        # 坐标系投影等信息
        self.proj_code = None
        self.geo_code = None
        self.geo_trans = None
        self.dsm_geo_trans = None
        # 地图tiff相关信息
        self.map_dataset = None
        self.dsm_map_dataset = None
        self.width = None
        self.height = None
        self.channel = None

    def load_map_info(self):
        """
        加载地图信息, 获取坐标系、分辨率、栅格size等信息
        :return:
        """
        self.map_dataset = gdal.Open('{}'.format(self.map_name))

        # 读取坐标相关信息
        # self.proj_code = osr.SpatialReference(wkt=self.map_dataset.GetProjection()).GetAttrValue('AUTHORITY', 1)
        # print(self.proj_code)
        self.geo_trans = self.map_dataset.GetGeoTransform()
        print(self.geo_trans)
        self.width, self.height, self.channel = self.map_dataset.RasterXSize, self.map_dataset.RasterYSize, \
                                               self.map_dataset.RasterCount

    def load_dsm_map_info(self):
        """
        加载DSM信息
        :return:
        """
        self.dsm_map_dataset = gdal.Open('{}.tif'.format(MAP_PATH + self.dsm_map_name))
        # 读取坐标相关信息
        # self.proj_code = osr.SpatialReference(wkt=self.map_dataset.GetProjection()).GetAttrValue('AUTHORITY', 1)
        self.dsm_geo_trans = self.dsm_map_dataset.GetGeoTransform()


class UAVMap(BaseMap):
    """
    地图
    """

    def __init__(self,
                 map_name: str,
                 dsm_map_name: str,
                 land_patch_name: str,
                 proj_code: int = 4549,
                 geo_code: int = 4326):
        super().__init__(map_name, dsm_map_name, land_patch_name)
        LOGGER.info("【Map Info Initialize】*************初始化正射影像数据(地理坐标系EPSG:{}, 投影坐标系EPSG:{})*************".format(geo_code, proj_code))
        self.load_map_info()
        if self.dsm_map_name is not None:
            self.load_dsm_map_info()
        self.proj_code = proj_code
        self.geo_code = geo_code
        self.map_match_info = None
        self.proj_transform = Transformer.from_crs("epsg:{}".format(self.proj_code), "epsg:{}".format(self.geo_code))    # 平面转经纬度
        self.reproj_transform = Transformer.from_crs("epsg:{}".format(self.geo_code), "epsg:{}".format(self.proj_code))  # 经纬度转平面

    def load_land_patch_info(self, lat, lon, radius=700):
        """
        加载图斑数据信息信息
        :return:
        """
        LOGGER.info("【Map Info Initialize】*************加载图斑数据*************")
        land_patch_gdf = gpd.read_file('{}'.format(self.land_patch_name)).\
                    to_crs('EPSG:{}'.format(self.proj_code))
        point = self.geo2proj(lat, lon)
        land_patch_gdf['DLBM'] = ['0101'] * len(land_patch_gdf)
        land_patches = land_patch_gdf[land_patch_gdf['geometry'].
                                       distance(Point([point[0][0], point[0][1]])) < radius][['DLBM', 'geometry']]
        return land_patches

    def geo2proj(self, lat, lon):
        """
        TODO: 经纬度转平面坐标
        """
        x, y = self.reproj_transform.transform(lat, lon)
        return np.column_stack([x, y])

    def proj2geo(self, x, y):
        """
        TODO:经纬度转投影，后续需修改为transform方法,返回（lat,long）
        """
        lat, lon = self.proj_transform.transform(x, y)
        return np.column_stack([lat, lon])

    def raster2proj(self, ras_points):
        """
        TODO: 栅格坐标转投影坐标
        """
        proj_points = ras_points * np.array([self.map_match_info[1], self.map_match_info[-1]]) + \
                      np.array([self.map_match_info[0], self.map_match_info[2]])
        return proj_points

    def proj2raster(self, proj_points):
        """
        TODO: 投影坐标转栅格坐标
        """
        ras_points = (proj_points - np.array([self.map_match_info[0], self.map_match_info[2]])) / \
                      np.array([self.map_match_info[1], self.map_match_info[-1]])
        return ras_points

    def shp2raster(self, shp_file):
        """
        TODO: 将shape file里的多边形坐标转换为栅格坐标
        """
        # 数据坐标系统一
        gdf = gpd.read_file(shp_file)
        gdf = gdf[gdf['geometry'].distance(Point([120.04, 32.856])) < 0.08]
        # gdf.to_file(r'D:\mgr\uav video\test_video\23\road.shp')
        # 转换栅格
        line_string = gdf.geometry.apply(lambda x: x.coords[:]).tolist()
        line_points = [np.array(sublist) for sublist in line_string]

        raster_line_points = [np.ceil((line - np.array([self.geo_trans[0], self.geo_trans[3]])) /
                              np.array([self.geo_trans[1], self.geo_trans[5]])).astype(int) for line in line_points]
        return raster_line_points


if __name__ == '__main__':
    uav_map = UAVMap(r'D:\mgr\uav video\test_video\影像.tif', None, r'D:\mgr\uav video\test_video\23\gis_osm_roads_free_1.shp')
    raster_line_points = uav_map.shp2raster(r'D:\mgr\uav video\test_video\23\road.shp')
    # # 读取图像
    img = cv.imread(r'D:\mgr\uav video\test_video\test_tif.png')
    res_img = np.zeros_like(img)
    # 画line
    for line in raster_line_points:
        # print(line)
        # print(line[[1, 0]])
        cv.polylines(res_img, [line], False, (255, 0, 255), thickness=5)
    cv.imwrite(r'D:\mgr\uav video\test_video\road_mask.png', res_img)
    # # uav_map.splitting_map()
    # # print(uav_map.geo_trans)
