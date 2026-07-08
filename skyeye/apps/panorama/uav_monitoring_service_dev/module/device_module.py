# @Time : 2023/7/19 14:49
# @Author : Ma Guorui
# @Description : 📷
import os
import sys
import numpy as np
from osgeo import gdal
from camera_module import UAVCameraModel
from map_module import UAVMap
from shapely.geometry import *
from logger import Logger
import prettytable as pt
import exifread
import cv2 as cv
import networkx as nx
from apps.panorama.uav_monitoring_service_dev.module.ai_module import KeyPointsDetector, LightGlueMatcher
from apps.panorama.uav_monitoring_service_dev.module.common import get_image_paths, get_angle_with_north, inpaint_sky_regions, object_detection_server
from apps.panorama.uav_monitoring_service_dev.module.multi_processing_utils import generate_cultivate_mask_mp
from apps.panorama.uav_monitoring_service_dev.configs.device_config import *
import pycolmap
from scipy.cluster.vq import kmeans, vq
from multiprocessing import Pool, cpu_count
import re
import pickle
from tqdm import tqdm
from apps.panorama.uav_monitoring_service_dev.module.stitching_module import AutoPanoramaStitcher

LOGGER = Logger(logname='device_module.log', loglevel=4, logger='DeviceModuleInfo').getlog()
work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class DJCameraDeviceInitializer:
    """
    大疆设备初始化类, 初始化相机、初始化耕地--相机、初始化全景图片图层
    """

    color_code_list = [
        [187, 255, 255], [127, 255, 212], [224, 255, 255],
        [255, 255, 240], [84, 255, 159], [176, 226, 255],
        [255, 255, 0], [255, 106, 106], [255, 250, 205],
        [144, 238, 144], [240, 255, 255], [191, 239, 255],
        [191, 239, 255], [154, 192, 205]
    ]

    def __init__(self,
                 dj_base_info_files: np.array,
                 uav_map: UAVMap,
                 key_points_detector: KeyPointsDetector,
                 image_matcher: LightGlueMatcher,
                 auto_panorama_stitcher: AutoPanoramaStitcher,
                 optimal_inliers: int = 6000,
                 min_points_threshold: int = 60,
                 max_uav_pitch: int = -78,
                 calibration_dir: str = os.path.join(work_dir, 'data/calibration_info'),
                 patch_dir: str = os.path.join(work_dir,'data/points_info/'),
                 stitch_dir: str = os.path.join(work_dir, 'data/stitching/info/'),
                 layers_dir: str = os.path.join(work_dir, 'data/layers/'),
                 tif_dir: str = os.path.join(work_dir, 'data/TIF/'),
                 detected_patch_dir: str = os.path.join(work_dir, 'data/detected_patch/'),
                 detection_url: str = 'http://192.168.60.42:9000/object_detection/inference'
                 ):
        self.detection_url = detection_url
        self.adjacent_info = None
        self.adjacent_graph = None
        self.optimal_inliers = optimal_inliers
        self.min_points_threshold = min_points_threshold
        self.max_uav_pitch = max_uav_pitch
        self.matching_info = {}
        if len(dj_base_info_files) < 2:
            assert "请检查全景图片数量"
        self.image_files_root_dir = os.path.dirname(dj_base_info_files[0])
        self.n_cluster = len(dj_base_info_files) if len(dj_base_info_files) < 2 else 3  # 聚类数
        self.base_info_files = dj_base_info_files  # DJ无人机基础信息文件（每张图片包含的信息）
        self.candidate_files_index = []
        self.base_info = []
        self.cameras = []  # DJ无人机每张图片对应的相机模型
        self.f_35mm = None  # DJ无人机35mm ccd 对应的焦距值
        self.f = None

        # 初始化地图
        self.uav_map = uav_map
        # 初始化关键点检测器
        self.kp_detector = key_points_detector
        self.image_matcher = image_matcher
        # 初始化全景图拼接器
        self.auto_panorama_stitcher = auto_panorama_stitcher

        # 鸟瞰图id
        self.bev_image_id = 0

        # 标定信息情况
        self.have_calibration_camera = {}
        self.no_calibration_image_name = []
        self.folder_name = os.path.basename(os.path.dirname(dj_base_info_files[0]))
        # 保存信息文件名
        self.calibration_file_name = os.path.join(calibration_dir, self.folder_name + '.pkl')  # 标定信息文件
        self.patch_points_info_file_name = os.path.join(patch_dir, self.folder_name + '.pkl')  # 耕地图斑点信息文件
        self.stitching_info_file_name = os.path.join(stitch_dir, self.folder_name + '.pkl')  # 全景图拼接信息文件
        self.final_panorama_dir = os.path.join(layers_dir, self.folder_name)  # 原始高分辨率全景图层存放文件夹位置
        self.tif_dir = os.path.join(tif_dir, self.folder_name)  # 生成的TIF存放位置
        self.detection_save_path = os.path.join(detected_patch_dir, self.folder_name) # 生成的检测目标图片存放位置
        if not os.path.exists(self.tif_dir):
            os.makedirs(self.tif_dir)

        if not os.path.exists(self.final_panorama_dir):
            os.makedirs(self.final_panorama_dir)

        if not os.path.exists(self.detection_save_path):
            os.makedirs(self.detection_save_path)

    def init_camera(self):
        """
        TODO: 初始化每张图片对应的相机模型
        :return:
        """
        # 加载所有照片信息
        LOGGER.info("【Camera Base Info Initialize】*************加载照片EXIF信息*************")
        self.load_base_info()
        pitch_list = []
        yaw_list = []
        tb = pt.PrettyTable(title='Camera Base Infos')
        tb.field_names = ["Location", "Total Nums", "Used Nums"]
        LOGGER.info("【Camera Base Info Initialize】*************初始化相机模型信息*************")
        print(len(self.base_info_files))
        for i in range(len(self.base_info)):
            camera_model = UAVCameraModel(self.base_info_files, self.base_info[i], self.kp_detector, i)
            if camera_model.pitch < 5:
                self.candidate_files_index.append(i)
                pitch_list.append(camera_model.pitch)
                yaw_list.append(camera_model.yaw)
            self.cameras.append(camera_model)

        self.candidate_files_index = np.array(self.candidate_files_index)[np.argsort(pitch_list)]
        self.cameras = np.array(self.cameras)[self.candidate_files_index]
        self.base_info_files = self.base_info_files[self.candidate_files_index]

        # 输出表格， 打印信息
        tb.add_row(["{}".format(",".join([self.base_info[0]['GpsLatitude'],
                                          self.base_info[0]['GpsLongitude']])),
                    "{}".format(len(self.base_info)),
                    "{}".format(len(self.candidate_files_index))])
        LOGGER.info(tb)

        # 构建相机的邻接图
        LOGGER.info("【Camera Base Info Initialize】*************构建相机邻接图*************")
        self.adjacent_info = self.get_camera_adjacent_graph()

        for i in range(len(self.cameras)):
            self.cameras[i].capture_image_names = self.base_info_files
            self.cameras[i].bev_euler = [self.cameras[0].roll, self.cameras[0].pitch, self.cameras[0].yaw]

    def load_base_info(self):
        """
        TODO: 加载拍摄照片的基础信息
        :return:
        """
        end_info = b"\x3c\x2f\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x3e"
        start_info = b"\x3c\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x20"
        flag = False
        try:
            for img_file in self.base_info_files:
                with open(img_file, 'rb') as img:
                    data = bytearray()
                    lines = img.readlines()
                    for line in lines:
                        if start_info in line:
                            flag = True
                        if flag:
                            data += line
                        if end_info in line:
                            break
                if len(data) > 0:
                    data = str(data.decode('ascii'))
                    drone_dji_info = re.findall(r'drone-dji\:.*?=\".*?\"', data)
                    dj_data_dict = {}
                    for d in drone_dji_info:
                        # remove 'drone-dji:'
                        k, v = d.replace("drone-dji:", "").strip().split("=")
                        dj_data_dict[k] = v

                with open(img_file, 'rb') as f:
                    tags = exifread.process_file(f)

                latitude_info = str(tags['GPS GPSLatitude']).replace("[", "").replace("]", '').split(",")
                longitude_info = str(tags['GPS GPSLongitude']).replace("[", "").replace("]", '').split(",")
                focal_func = str(tags['EXIF FocalLength']).split('/')
                self.f = float(focal_func[0]) / float(focal_func[1])

                dj_data_dict['focal'] = self.f
                dj_data_dict['img'] = img_file

                self.base_info.append(dj_data_dict)
                flag = False
                dj_data_dict['GpsLatitude'] = '"{}"'.format(float(latitude_info[0]) + float(latitude_info[1]) / 60 + eval(latitude_info[2]) / 3600)
                dj_data_dict['GpsLongitude'] = '"{}"'.format(
                    float(longitude_info[0]) + float(longitude_info[1]) / 60 + eval(longitude_info[2]) / 3600)
                print(dj_data_dict)
        except Exception as e:
            LOGGER.error("【Camera Base Info Initialize】*************{}*************".format(str(e)))
            LOGGER.error("【Camera Base Info Initialize】*************EXIF数据信息格式有误请检查*************")

    def get_camera_adjacent_graph(self):
        """
        TODO: 构建相机邻接矩阵, 利用stitching包构建
        :return:
        """
        pitch_array = np.array([camera.pitch for camera in self.cameras])  # 无人机的pitch角
        yaw_array = np.array([camera.yaw for camera in self.cameras])  # 无人机的yaw角
        adjacent_matrix = np.zeros((len(pitch_array), len(pitch_array)))  # 邻接矩阵
        # 按照pitch角进行聚类
        centroids, distortion = kmeans(pitch_array, self.n_cluster)
        centroids = np.sort(centroids)
        labels, _ = vq(pitch_array, centroids)
        labels = np.array(labels)
        # 按照pitch分组
        bev_idx = np.where(labels == 0)[0]  # bev视角图片
        middle_idx = np.where(labels == 1)[0]  # bev + 1 视角图片
        high_idx = np.where(labels == 2)[0]  # bev + 2 视角图片
        higher_idx = np.where(labels == 3)[0]  # bev + 2 视角图片
        # 根据分组进行第一层邻接构建
        adjacent_matrix[np.repeat(bev_idx, len(middle_idx)), middle_idx] = 1
        adjacent_matrix[middle_idx, np.repeat(bev_idx, len(middle_idx))] = 1
        # 根据yaw 角度对middle角度的图片进行邻接构建
        middle_pitch_sorted_idx = list(middle_idx[np.argsort(yaw_array[middle_idx])])
        middle_pitch_sorted_idx.append(middle_pitch_sorted_idx[0])  # 首尾相连
        adjacent_matrix[middle_pitch_sorted_idx[:-1], middle_pitch_sorted_idx[1:]] = 1
        adjacent_matrix[middle_pitch_sorted_idx[1:], middle_pitch_sorted_idx[:-1]] = 1
        # 根据yaw 角度对high角度的图片进行邻接构建
        high_pitch_sorted_idx = list(high_idx[np.argsort(yaw_array[high_idx])])
        high_pitch_sorted_idx.append(high_pitch_sorted_idx[0])  # 首尾相连
        adjacent_matrix[high_pitch_sorted_idx[:-1], high_pitch_sorted_idx[1:]] = 1
        adjacent_matrix[high_pitch_sorted_idx[1:], high_pitch_sorted_idx[:-1]] = 1
        for idx in high_idx:
            delta_yaw = np.absolute(yaw_array[middle_idx] - yaw_array[idx])
            adjacent_yaw_idx = middle_idx[delta_yaw < 30]
            adjacent_matrix[adjacent_yaw_idx, np.repeat(idx, len(adjacent_yaw_idx))] = 1
            adjacent_matrix[np.repeat(idx, len(adjacent_yaw_idx)), adjacent_yaw_idx] = 1

        # # 根据yaw 角度对higher角度的图片进行邻接构建
        # higher_pitch_sorted_idx = list(higher_idx[np.argsort(yaw_array[higher_idx])])
        # higher_pitch_sorted_idx.append(higher_pitch_sorted_idx[0])  # 首尾相连
        # adjacent_matrix[higher_pitch_sorted_idx[:-1], higher_pitch_sorted_idx[1:]] = 1
        # adjacent_matrix[higher_pitch_sorted_idx[1:], higher_pitch_sorted_idx[:-1]] = 1
        # for idx in higher_idx:
        #     delta_yaw = np.absolute(yaw_array[high_idx] - yaw_array[idx])
        #     adjacent_yaw_idx = high_idx[delta_yaw < 30]
        #     adjacent_matrix[adjacent_yaw_idx, np.repeat(idx, len(adjacent_yaw_idx))] = 1
        #     adjacent_matrix[np.repeat(idx, len(adjacent_yaw_idx)), adjacent_yaw_idx] = 1

        dig_row, dig_col = np.diag_indices_from(adjacent_matrix)
        adjacent_matrix[dig_row, dig_col] = 0
        # node_labels = {i: self.base_info_files[i] for i in range(len(self.base_info_files))}
        # adjacent_graph = nx.Graph(adjacent_matrix)
        #
        # print(node_labels)
        # pos = nx.spring_layout(adjacent_graph)
        # nx.draw(adjacent_graph, pos, with_labels=True, labels=node_labels, node_size=500)
        # plt.show()
        return adjacent_matrix

    def calibration(self):
        """
        设备标定
        :return:
        """
        LOGGER.info("【Bev Camera Calibration】*************Bev图片标定*************")
        tb = pt.PrettyTable(title='Camera Init Calibration Infos')
        tb.field_names = ["Image Name", "Fx", "Fy", "Cx", "Cy", "Q_vec", "T_vec", "Num inliers"]
        # 取出符合要求的图片对应的id
        for i in range(len(self.cameras)):
            camera_model = self.cameras[i]
            if camera_model.pitch > -85:
                self.no_calibration_image_name.append(self.base_info_files[i])
                continue
            camera_model.kp_detector = self.kp_detector

            # 平面坐标系下的拍摄地经纬度坐标pr
            camera_model.proj_x, camera_model.proj_y = self.uav_map.geo2proj(camera_model.latitude,
                                                                             camera_model.longitude)[0]

            # 生成标定点对
            ret, image_points, world_points, homography, map_info = camera_model. \
                generate_calibration_points(i, self.uav_map.geo_trans, self.uav_map.map_dataset)

            if (ret < self.min_points_threshold) or (camera_model.pitch > self.max_uav_pitch):
                self.no_calibration_image_name.append(self.base_info_files[i])
                continue
            self.uav_map.map_match_info = map_info

            world_points_3d = np.column_stack([world_points,
                                               np.zeros((len(world_points), 1))]).astype(np.float64)

            camera_model.init_extrinsic(world_points_3d, image_points.astype(np.float64))
            if camera_model.ret < 10:
                self.no_calibration_image_name.append(self.base_info_files[i])
                continue
            camera_model.base_camera_index = i

            self.cameras[i] = camera_model
            self.have_calibration_camera[self.base_info_files[i]] = camera_model

            # 输出表格， 打印初始化信息
            tb.add_row(["{}".format(self.base_info_files[i]), "{}".format(camera_model.K[0, 0].tolist()),
                        "{}".format(camera_model.K[1, 1]), "{}".format(camera_model.K[0, 2].tolist()),
                        "{}".format(camera_model.K[1, 2]), "{}".format(pycolmap.rotmat_to_qvec(camera_model.R)
                                                                       if camera_model.R is not None else None),
                        "{}".format(camera_model.T if camera_model.T is not None else None),
                        "{}".format(ret)])
        #  输出标定成功与否
        if len(self.have_calibration_camera) == 0:
            LOGGER.error("【Bev Camera Calibration】*************Bev图片标定失败*************")
            assert "no calibrated camera in 'have_calibration_camera', please check the image"
        LOGGER.info(tb)

    def calibration_other_camera_from_graph(self):
        """
        TODO: 根据世界点解算绝对位姿
        :return:
        """
        target_camera_name = list(self.have_calibration_camera.keys())[0]
        for camera_name in self.no_calibration_image_name:
            # 找出匹配最优路径
            path = nx.shortest_path(self.adjacent_graph, source=camera_name, target=target_camera_name, weight='weight')
            # print(path)
            # 取出转换关系矩阵
            base_name = path[1:]
            target_name = path[:-1]
            base_name.reverse()
            target_name.reverse()
            # 匹配点坐标对

            matching_points = [self.matching_info[base_name[i]][target_name[i]]['key_points_pair'] for i in \
                               range(len(base_name))]
            for j in range(len(base_name)):
                if self.have_calibration_camera.get(target_name[j]) is not None:
                    continue
                relative_camera = self.have_calibration_camera[base_name[j]]
                target_camera_id = int(np.where(self.base_info_files == target_name[j])[0])
                cur_camera = self.cameras[target_camera_id]

                # 获取匹配点, 多加一些点
                relative_matching_points, cur_matching_points = matching_points[j]
                # 计算转换矩阵
                homography_matrix, _ = cv.findHomography(cur_matching_points, relative_matching_points, cv.RANSAC, 2.0)
                # print(homography_matrix)
                # 构造像素点坐标(用于耕地贴合图斑)
                row_idx_range = np.arange(int(self.cameras[0].h / 3), self.cameras[0].h, 100)
                col_idx_range = np.arange(int(self.cameras[0].w / 4),  int(3 * self.cameras[0].w / 4), 100)
                candidate_row = np.repeat(row_idx_range, len(col_idx_range))
                candidate_col = np.tile(col_idx_range, len(row_idx_range))
                candidate_image_points = np.vstack([candidate_col, candidate_row]).T
                # 转换relative_points
                relative_matching_points = cv.perspectiveTransform(candidate_image_points.reshape(-1, 1, 2).astype(np.float32),
                                                                   homography_matrix).reshape(-1, 2)
                # 计算世界点
                # # 将cur matching points 进行转换
                # rotation = cur_camera.perspective_recover(relative_camera)
                # cur_matching_points = cv.perspectiveTransform(cur_matching_points.reshape(-1, 1, 2). \
                #                                               astype(np.float32), rotation).reshape(-1, 2)

                # 将relative points转换为世界点坐标
                world_points = relative_camera.img2world(relative_matching_points)
                world_points_3d = np.column_stack([world_points,
                                                   np.zeros((len(world_points), 1))]).astype(np.float64)

                # 标定当前相机
                cur_camera.init_extrinsic(world_points_3d, candidate_image_points.astype(np.float64))
                cur_camera.base_camera_index = relative_camera.base_camera_index
                self.cameras[target_camera_id] = cur_camera
                self.have_calibration_camera[target_name[j]] = cur_camera

    def generate_camera_graph(self):
        """
        TODO: 根据邻接关系计算两两图片之间的匹配点, 并生成带有权重的邻接图
        :return:
        """
        adjacent_matrix_copy = self.adjacent_info.copy()  # 邻接信息
        # adjacent_homography_info = []    # 邻接图片间的homography信息
        edges_with_weights = []
        G = nx.Graph()  # 生成图
        node = list(self.base_info_files)  # 节点名
        G.add_nodes_from(node)  # 生成节点
        for i in range(len(self.base_info_files)):
            # 提取当前摄像头信息
            cur_base_image_name = self.base_info_files[i]
            cur_camera_id = int(np.where(self.base_info_files == cur_base_image_name)[0])
            cur_camera = self.cameras[cur_camera_id]
            # 提取当前摄像头相邻的图片信息
            adjacent_idx = np.where(adjacent_matrix_copy[i] == 1)[0].astype(np.int32)
            if len(adjacent_idx) == 0:
                continue
            adjacent_cameras = {image_name: camera for image_name, camera in
                                zip(self.base_info_files[adjacent_idx], self.cameras[adjacent_idx])}
            # # 获取匹配信息
            num_inliers, image_name, matching_info = self.image_matcher.generating_matching_info_with_pose( \
                cur_base_image_name, cur_camera, list(adjacent_cameras.keys()), list(adjacent_cameras.values()))

            # num_inliers, image_name, matching_info = self.image_matcher.get_matching_points(cur_base_image_name, self.base_info_files[adjacent_idx])
            # num_inliers, image_name, matching_info = self.kp_detector.\
            #     generating_matching_info(cur_base_image_name, list(adjacent_cameras.keys()))
            weights = np.round(self.optimal_inliers / num_inliers, 3)  # 边权重
            # 给边赋予权重
            edges_with_weights += [(cur_base_image_name, image_name[j], weights[j]) for j in range(len(image_name))]
            # adjacent_homography_info.append(matching_info)
            # 将第i列置0
            adjacent_matrix_copy[:, i] = 0

            # 两层循环是否可以进行修改！！！！
            for base_name, base_info in matching_info.items():
                for key, value in base_info.items():
                    if self.matching_info.get(base_name) is None:
                        self.matching_info[base_name] = {key: value}
                    else:
                        self.matching_info[base_name][key] = value
            # print(self.matching_info)

        G.add_weighted_edges_from(edges_with_weights)
        edge_weights = nx.get_edge_attributes(G, 'weight')

        # # 画图
        # pos = nx.spring_layout(G)
        # nx.draw(G, pos, with_labels=True, font_size=8, node_size=500)
        # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights)
        # plt.show()

        self.adjacent_graph = G

    def origin_panorama_generation(self):
        """
        TODO: 原始图像图层全景图片拼接， 保存拼接信息
        """
        LOGGER.info("【UavInitializeInfo】  正在生成原始全景图")
        origin_image_info = get_image_paths("{}/".format(self.image_files_root_dir), 'JPG')  # 原始图像文件信息
        panorama = self.auto_panorama_stitcher.stitch_final_resolution(list(origin_image_info.values()))  # 高分辨率全景图片拼接

        # 生成等距柱状投影
        temp_img = np.zeros((panorama.shape[1] // 2, panorama.shape[1], 3)).astype(np.uint8)
        # 填充颜色
        temp_img[temp_img.shape[0] - panorama.shape[0]:, :, :] = panorama
        # 对黑色区域进行插值补全
        res_panorama = inpaint_sky_regions(temp_img)

        cv.imwrite(os.path.join(self.final_panorama_dir, 'origin_panorama.png'), res_panorama)  # 保存图片

        self.auto_panorama_stitcher.final_stitching_info_saving(self.stitching_info_file_name)  # 保存拼接信息

    def land_patch_mask_generation(self):
        """
        TODO:图斑掩膜
        :return:
        """
        LOGGER.info("【UavInitializeInfo】  正在进行耕地贴图")
        # 获取图斑polygon
        land_patches = self.uav_map.load_land_patch_info(self.cameras[0].latitude, self.cameras[0].longitude)
        category = land_patches.groupby('DLBM').count().index.tolist()
        # 随机选取颜色代码, 随机数种子固定
        np.random.seed(42)
        colors_code = np.random.choice(np.arange(len(self.color_code_list)), len(category), replace=True)
        colors = {category[i]: tuple(int(j) for j in self.color_code_list[colors_code[i]]) for i in range(len(category))}

        # 构造像素点坐标(用于耕地贴合图斑)
        row_idx_range = np.arange(0, self.cameras[0].h, 5)
        col_idx_range = np.arange(0, self.cameras[0].w, 5)
        candidate_row = np.repeat(row_idx_range, len(col_idx_range))
        candidate_col = np.tile(col_idx_range, len(row_idx_range))

        res_info = {}  # 图像结果点信息
        map_info = self.uav_map.map_match_info  # 当前地图
        # 初始化并行池, 進程數用cpu核心數的一半
        pool = Pool(int(cpu_count() / 2))
        # pool = Pool(int(cpu_count()))
        # 改寫成并行
        results = []
        for i in tqdm(range(len(self.cameras))):
            cur_camera_model = self.cameras[i]  # 当前相机模型
            if cur_camera_model is None:
                continue
            # 可视化
            cur_image_name = self.base_info_files[i]
            cur_camera_model_base_info = cur_camera_model.base_info_to_json()
            h = self.cameras[0].h
            proj_code = self.uav_map.proj_code
            result = pool.apply_async(generate_cultivate_mask_mp, args=(cur_camera_model_base_info, cur_image_name, candidate_col, candidate_row,
                                                                         map_info, h, proj_code, land_patches, self.base_info_files, i))
            results.append(result)

        pool.close()
        pool.join()
        for res in results:
            for idx, value in res.get().items():
                if res_info.get(idx) is None:
                    res_info[idx] = value
                else:
                    res_info[idx].update(value)

        return res_info

    def cultivate_panorama_generation(self):
        """
        TODO: 耕地图层图斑全景图生成
        """
        LOGGER.info("【UavInitializeInfo】  正在生成耕地全景图")
        # 生成mask
        points_info = self.land_patch_mask_generation()
        # 加载 stitcher 的数据信息
        self.auto_panorama_stitcher.load_stitching_info(self.stitching_info_file_name)
        origin_infos = get_image_paths(r"{}/".format(self.image_files_root_dir), 'JPG')
        # print(points_info.keys())
        cultivate_panorama = self.auto_panorama_stitcher.stitch_cultivate_patch(origin_infos, points_info)

        # 生成等距柱状投影
        temp_img = np.zeros((cultivate_panorama.shape[1] // 2, cultivate_panorama.shape[1], 3)).astype(np.uint8)
        # 填充颜色
        # temp_img[:temp_img.shape[0] - img.shape[0], :, :] = [253, 254, 236]
        temp_img[temp_img.shape[0] - cultivate_panorama.shape[0]:, :, :] = cultivate_panorama
        # 在原图基础上叠加耕地图
        if os.path.exists(os.path.join(self.final_panorama_dir, 'origin_panorama.png')):
            origin_img = cv.imread(os.path.join(self.final_panorama_dir, 'origin_panorama.png'))
            detect_img = cv.imread(os.path.join(self.final_panorama_dir, 'detection_panorama.png'))
            temp_img = cv.resize(temp_img, (origin_img.shape[1], origin_img.shape[0]), cv.INTER_AREA)
            res_cultivate_panorama = cv.add(origin_img, temp_img)
            mix_panorama = cv.add(detect_img, temp_img)
            cv.imwrite(os.path.join(self.final_panorama_dir, 'cultivate_panorama.png'), res_cultivate_panorama)  # 保存图片
            cv.imwrite(os.path.join(self.final_panorama_dir, 'mix_panorama.png'), mix_panorama)
        else:
            LOGGER.error("原始全景图层还未生成, 请检查")
            raise '原始全景图层还未生成, 请检查'

    def extra_panorama_info_generation(self):
        """
        TODO: 一些拼接全景的信息生成
        """
        # stitching with res alarms
        self.auto_panorama_stitcher.load_stitching_info(self.stitching_info_file_name)
        #
        origin_image_info = {str(name).split("\\")[-1][:-4]: str(name) for name in self.base_info_files}
        self.auto_panorama_stitcher.stitch_final_resolution_blend_color_mask(list(origin_image_info.values()))  # 拼接color map
        self.auto_panorama_stitcher.stitch_crop_rectangle_info()  # max rectangle info
        self.auto_panorama_stitcher.stitch_warp_size_info()       # warp size info
        if not os.path.exists(r"../data/stitching/info"):
            os.mkdir(r"../data/stitching/info")
        self.auto_panorama_stitcher.final_stitching_info_saving(r'../data/stitching/info/{}.pkl'.format(self.base_info_files[0].split("/")[-2]))

    def detection_panorama_generation(self):
        """
        TODO: 目标检测全景图生成
        """
        # 耕地数据
        # 获取图斑polygon
        land_patches = self.uav_map.load_land_patch_info(self.cameras[0].latitude, self.cameras[0].longitude)
        # 目标检测全景图信息{‘类别’：‘拍摄图片’：{信息}}
        res_alarms,result_alarms = object_detection_server(self.base_info_files, self.cameras, land_patches, self.uav_map, self.detection_save_path, 'http://192.168.60.6:5556/detection_web')
        # {‘类别’:{''}}
        # stitching with res alarms
        self.auto_panorama_stitcher.load_stitching_info(self.stitching_info_file_name)
        origin_infos = get_image_paths(r"{}/".format(self.image_files_root_dir), 'JPG')
        detection_panorama = self.auto_panorama_stitcher.stitch_object_patch(origin_infos, res_alarms)
        cv.imwrite(os.path.join(self.final_panorama_dir, 'detection_panorama_mask.png'), detection_panorama)  # 保存图片

        # 生成等距柱状投影
        temp_img = np.zeros((detection_panorama.shape[1] // 2, detection_panorama.shape[1], 3)).astype(np.uint8)
        # 填充颜色
        # temp_img[:temp_img.shape[0] - img.shape[0], :, :] = [253, 254, 236]
        temp_img[temp_img.shape[0] - detection_panorama.shape[0]:, :, :] = detection_panorama

        if os.path.exists(os.path.join(self.final_panorama_dir, 'origin_panorama.png')):
            origin_img = cv.imread(os.path.join(self.final_panorama_dir, 'origin_panorama.png'))
            temp_img = cv.resize(temp_img, (origin_img.shape[1], origin_img.shape[0]), cv.INTER_AREA)
            temp_img = cv.add(origin_img, temp_img)
            cv.imwrite(os.path.join(self.final_panorama_dir, 'detection_panorama.png'), temp_img)  # 保存图片
        else:
            LOGGER.error("原始全景图层还未生成, 请检查")
            raise '原始全景图层还未生成, 请检查'
        return res_alarms,result_alarms

    def camera_info_save(self):
        """
        TODO: 相机配准等信息保存
        :return:
        """
        camera_infos = {}
        for i in range(len(self.cameras)):
            base_info = self.cameras[i].base_info_to_json()
            camera_key = os.path.normpath(self.base_info_files[i].split('\\')[-1])
            camera_infos[camera_key] = base_info

        camera_infos['map_match_info'] = self.uav_map.map_match_info
        # 保存信息
        with open(self.calibration_file_name, 'wb') as f:
            pickle.dump(camera_infos, f)

    def load_camera_info(self, file):
        """
        TODO: 加载相机信息
        :return:
        """
        with open(file, 'rb') as f:
            camera_infos = pickle.load(f)
        # 加载uav地图信息
        self.uav_map.map_match_info = camera_infos['map_match_info']
        # 加载uav相机信息
        for i in range(len(self.base_info_files)):
            # 新建一个相机类
            camera_model = UAVCameraModel(self.base_info_files, None, self.kp_detector, i)
            camera_key = os.path.normpath(self.base_info_files[i].split('\\')[-1])
            # 加载相机信息
            if camera_infos.get(camera_key) is None:
                self.cameras.append(None)
            else:
                camera_model.load_camera_from_json(camera_infos[camera_key])
                self.cameras.append(camera_model)


class BaseCameraDevice:
    """
    基础监控设施类， 包含位置坐标， 预估安装高度， 设备ID， group等等
    """

    def __init__(self):
        self.device_id = None  # str
        self.install_longitude = None
        self.install_latitude = None
        self.install_altitude = None
        self.install_height = None  # 是否可以进行预测?


class DJCameraDevice(BaseCameraDevice):
    """
    大疆设备类
    """
    color_code_list = [
        [187, 255, 255], [127, 255, 212], [224, 255, 255],
        [255, 255, 240], [84, 255, 159], [176, 226, 255],
        [255, 255, 0], [255, 106, 106], [255, 250, 205],
        [144, 238, 144], [240, 255, 255], [191, 239, 255],
        [191, 239, 255], [154, 192, 205]
    ]

    def __init__(self,
                 dj_base_info_files: np.array,
                 uav_map: UAVMap,
                 key_points_detector: KeyPointsDetector,
                 auto_panorama_stitcher: AutoPanoramaStitcher,
                 calibration_file: str,
                 panorama_file: str
                 ):
        super().__init__()

        if len(dj_base_info_files) < 4:
            assert "请检查全景图片数量"
        self.base_info_files = dj_base_info_files  # DJ无人机基础信息文件（每张图片包含的信息）
        self.cameras = []  # DJ无人机每张图片对应的相机模型
        # 初始化地图
        self.uav_map = uav_map
        # 初始化全景图拼接器(包含加载全景信息)
        self.auto_panorama_stitcher = auto_panorama_stitcher
        if not os.path.exists(panorama_file):
            raise "全景信息路径不正确，请检查"
        self.auto_panorama_stitcher.load_stitching_info(panorama_file)
        # 初始化关键点检测器
        self.kp_detector = key_points_detector

        if not os.path.exists(calibration_file):
            raise "标定信息路径不正确，请检查"
        self.load_camera_info(calibration_file)
        # 鸟瞰图id
        self.bev_image_id = 0

    def load_camera_info(self, file):
        """
        TODO: 加载相机信息
        :return:
        """
        with open(file, 'rb') as f:
            camera_infos = pickle.load(f)
        # 加载uav地图信息
        self.uav_map.map_match_info = camera_infos['map_match_info']
        # 加载uav相机信息
        for i in range(len(self.base_info_files)):
            # 新建一个相机类
            camera_model = UAVCameraModel(self.base_info_files, None, self.kp_detector, i)
            camera_key = os.path.normpath(self.base_info_files[i].split('\\')[-1])
            # 加载相机信息
            if camera_infos.get(camera_key) is None:
                self.cameras.append(None)
            else:
                camera_model.load_camera_from_json(camera_infos[camera_key])
                self.cameras.append(camera_model)

    def illegal_overlay_analysis(self, cultivate_polygon_list, detection_boxs):
        """
        TODO: 违法行为目标框与耕地图斑的叠加分析， 返回在耕地内的违法目标和对应的经纬度
        :param cultivate_polygon_list: 耕地图斑（经纬度坐标， 坐标系未定）
        :param detection_boxs: 违法行为检测目标框, {pic_name: [[], []]}
        :return: 耕地范围内的违法目标和对应目标的经纬度
        """
        illegal_boxs = {}
        result = []
        for idx, name in enumerate(self.base_info_files):
            camera = self.cameras[idx]
            if camera == None or name not in detection_boxs.keys():
                continue
            boxs = detection_boxs[name]
            for box in boxs:
                k = 1
                x, y, w, h = box
                ras_points = camera.img2world([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (int(x + w / 2), int(y + h / 2))])
                proj_points = self.uav_map.raster2proj(ras_points)
                geo_points = self.uav_map.proj2geo(proj_points)
                lnglat = geo_points.pop()
                illegal_boxs['points'] = geo_points
                illegal_boxs['center'] = list(lnglat)
                for polygon in cultivate_polygon_list:
                    bool = (polygon.contains(Point(geo_points[0])) +
                            polygon.contains(Point(geo_points[1])) +
                            polygon.contains(Point(geo_points[2])) +
                            polygon.contains(Point(geo_points[3])))
                    if bool:
                        k = 0
                        illegal_boxs['islegal'] = False
                        break
                if k:
                    illegal_boxs['islegal'] = True
                result.append(illegal_boxs.copy())
        return result

    def panorama2world(self, panorama_points):
        """
        TODO: 全景坐标转经纬度坐标
        """
        # panorama to image points(未考虑天空存在缺陷！！！！)
        image_points = self.auto_panorama_stitcher.panorama2img(panorama_points, (self.cameras[0].w, self.cameras[0].h))
        # image to raster, image points {'camera idx': image points}
        raster_points = []
        for idx, points in image_points.items():
            cur_points = self.cameras[self.auto_panorama_stitcher.indices[idx]].img2raster(np.array(points).reshape((len(points), 2)))
            for p in cur_points:
                raster_points.append(p)
        # raster to proj
        print(raster_points)
        proj_points = self.uav_map.raster2proj(np.array(raster_points))
        # proj to world
        world_points = self.uav_map.proj2geo(proj_points[:, 0], proj_points[:, 1])

        return world_points

    def world2panorama(self, geo_points: np.array):
        """
        TODO: 经纬度坐标转全景坐标(存在缺陷)
        :param geo_points: [(long,lat),...]
        :return:
        """
        # 经纬度坐标转投影坐标()
        proj_points = self.uav_map.geo2proj(geo_points[:, 1], geo_points[:, 0])[:, [1, 0]]
        # 投影坐标转栅格坐标  (相对的, 顶点是base map的顶点)
        raster_points = self.uav_map.proj2raster(proj_points)
        raster_points_3d = np.column_stack([raster_points, np.zeros((len(raster_points), 1))]).astype(np.float64)
        # 栅格坐标转图像坐标 (涉及到多个相机模型)
        # [w, h]
        image_points_per_camera = {i: self.cameras[i].raster2img(raster_points_3d) for i in range(len(self.cameras)) if (self.cameras[i] is not None)}
        # 筛选点和对应的图片
        candidate_image_points_per_camera = {}
        candidate_image_points_idx_per_camera = {}
        for camera_idx, image_points in image_points_per_camera.items():
            filter_idx = (image_points[:, 0] < 0) + (image_points[:, 1] < 0) + \
                        (image_points[:, 0] > self.cameras[camera_idx].w) + (image_points[:, 1] > self.cameras[camera_idx].h)
            if np.sum(~filter_idx) == 0:
                continue
            candidate_image_points_idx = np.unique(np.where(~filter_idx == 1)[0])
            if self.cameras[camera_idx].pitch <= -10:
                candidate_image_points_per_camera[camera_idx] = image_points_per_camera[camera_idx][candidate_image_points_idx, :].astype(np.int32)
                candidate_image_points_idx_per_camera[camera_idx] = candidate_image_points_idx
            else:
                # 计算夹角
                angle_with_north = get_angle_with_north(self.cameras[0].latitude, self.cameras[0].longitude,
                                                        geo_points[candidate_image_points_idx, 1], geo_points[candidate_image_points_idx, 0])
                # 过滤反向点
                filter_idx = np.absolute(angle_with_north - self.cameras[camera_idx].yaw) > 35
                if np.sum(~filter_idx) == 0:
                    continue
                filter_image_points_idx = candidate_image_points_idx[~filter_idx]
                candidate_image_points_per_camera[camera_idx] = image_points_per_camera[camera_idx][filter_image_points_idx, :].astype(np.int32)

                candidate_image_points_idx_per_camera[camera_idx] = filter_image_points_idx

        # to panorama image
        have_calculate_points, _ = self.auto_panorama_stitcher.img2panorama(candidate_image_points_per_camera)
        # conformity
        res_panorama_points = np.zeros((len(geo_points), 2))
        for camera_idx, points in have_calculate_points.items():
            # 筛选points
            filter_points_idx = ((points[:, 0] < 0) + (points[:, 1] < 0) +
                                 (points[:, 0] > self.auto_panorama_stitcher.panorama_size[1]) +
                                 (points[:, 1] > self.auto_panorama_stitcher.panorama_size[0]))
            # 获取筛选之后的点坐标
            filter_image_idx = candidate_image_points_idx_per_camera[camera_idx][~filter_points_idx]
            res_panorama_points[filter_image_idx, :] = points[~filter_points_idx, :]

        return res_panorama_points


if __name__ == '__main__':
    #object_detection_server([r"D:\mgr\GTMap\uav-monitoring-service\data\hailin_panorama\DJI_202404081502_017\017_0001\PANO0001.JPG"])
    path_list = [r'../data\hailin_panorama\DJI_202404081502_017\017_0001',
                 r'../data\hailin_panorama\DJI_202404081502_017\017_0002',
                 r'../data\hailin_panorama\DJI_202404081502_017\017_0003',
                 r'../data\hailin_panorama\DJI_202404081502_017\017_0004']
    calibration_info = [r'../data/calibration_info/017_0001.pkl',
                        r'../data/calibration_info/017_0002.pkl',
                        r'../data/calibration_info/017_0003.pkl',
                        r'../data/calibration_info/017_0004.pkl']
    panorama_info = [r'../data\stitching\info\016_0002.pkl']
    map_uav = UAVMap(MAP_PATH, None, LAND_PATCH_INFO, proj_code=32650)       # map
    detector = KeyPointsDetector(r'D:\mgr\GTMap\uav-monitoring-service\model\model.ckpt')
    matcher = LightGlueMatcher()                                       # ai

    stitcher = AutoPanoramaStitcher(detector="sift", nfeatures=8000)     # stitcher
    for i in range(len(path_list)):
        # try:
        path = path_list[i]
        origin_image_info = get_image_paths(path, 'JPG')
        files = np.array([os.path.join(path, file) for file in os.listdir(path) if '.JPG' in file])
        #
        uav_initializer = DJCameraDeviceInitializer(files, map_uav, detector, matcher, stitcher)
        # uav_initializer.init_camera()
        # #生成邻接权重图
        # uav_initializer.generate_camera_graph()
        # # bev视角相机标定
        # uav_initializer.calibration()
        # # # 其他视角相机标定
        # uav_initializer.calibration_other_camera_from_graph()
        # 相机信息保存
        # uav_initializer.camera_info_save()
        # 加载信息
        uav_initializer.load_camera_info(calibration_info[i])
        # uav_initializer.origin_panorama_generation()
        # uav_initializer.extra_panorama_info_generation()
        uav_initializer.detection_panorama_generation()
        # uav_initializer.cultivate_panorama_generation()
        # uav_initializer.orthophoto_map_generation()
        # # # 读取目标检测框
        # detection_mask = cv.imread(os.path.join("../data/layers", path.split("/")[-1], 'detection_panorama_mask.png'), 0)
        # # # print(detection_mask.shape)
        # # # # # 获取目标检测框轮廓
        # # # gray_mask = cv.cvtColor(detection_mask, cv.COLOR_BGR2GRAY)
        # ret, binary_mask = cv.threshold(detection_mask, 50, 255, 0)
        # # # 查找轮廓
        # contours, hierarchy = cv.findContours(binary_mask.astype(np.uint8), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        # #
        # # 簡化輪廓
        # res_center = []
        # for contour in contours:
        #     M = cv.moments(contour)
        #     cX = int(M["m10"] / M["m00"])
        #     cY = int(M["m01"] / M["m00"])
        #     res_center.append([cY, cX])
        #
        # uav = DJCameraDevice(files, map_uav, detector, stitcher, calibration_info[i], panorama_info[i])   # 初始化设备类
        # uav.load_camera_info(calibration_info[i])
        # world_point = uav.panorama2world(np.array(res_center))
        # print(world_point)
        # # uav.world2panorama(np.array([[118.606901, 32.504790],
        # #                              [118.606807, 32.504710],
        # #                              [118.606562, 32.504912],
        # #                              [118.606656, 32.504996]]))
        # # uav.panorama2world(np.array(
        # #             [[3000, 3890],
        # #              [3000, 3890],
        # #              [4400, 17910],
        # #              [6140, 5440],
        # #              [5440, 6120]]
        # # ))
        #
        # # panorama_patch = uav.auto_panorama_stitcher.stitch_patch(origin_image_info, cultivated_points_info)   # 获取图斑全景图
        #
        # pass
        #
        #
