# @Time : 2023/7/19 14:49
# @Author : Ma Guorui
# @Description : 📷

import numpy as np
import cv2 as cv
from apps.panorama.uav_monitoring_service_dev.module.ai_module import KeyPointsDetector
from scipy.spatial.transform import Rotation

class BaseCameraModel:
    """
    基础相机模型， 包含相机基本属性, 基本的参数求解功能， 坐标转换功能
    """
    SENSOR_PARAMS = {
        "1/2.8": [3.429, 4.571],
        "1/35": [36, 24]
    }

    def __init__(self, image_names):
        self.f = 4.8
        self.sensor_type = "1/2.8"  # 默认传感器尺寸
        self.capture_image_names = image_names  # 该摄相机抓拍的图片名称
        self.K = None
        self.R = None
        self.T = None
        self.OR = []
        self.RE = []

    def __getitem__(self):
        return self.f

    def init_extrinsic(self, world_points: np.array, image_points: np.array):
        """
        求解外参数据
        :param world_points:
        :param image_points:
        :param intrinsic_solve:
        :return:
        """
        """
        pycolmap.absolute_pose_estimation(
                    points2D, points3D, camera,
                    estimation_options={'ransac': {'max_error': 12.0}},
                    refinement_options={'refine_focal_length': True},
)
        """
        answer = pycolmap.absolute_pose_estimation(image_points,
                                                   world_points,
                                                   camera=self.camera_model,
                                                   estimation_options={'ransac': {'max_error': 2.0,
                                                                                  'min_num_trials': 10000,
                                                                                  'min_inlier_ratio': 0.01}})
        self.ret = answer['num_inliers']
        self.R = pycolmap.qvec_to_rotmat(answer['qvec'])
        self.T = answer['tvec']
        self.K = self.camera_model.calibration_matrix()

    def world2img(self, world_points):
        """
        TODO:世界点转换到像素坐标
        :return:
        """
        img_points_repro, _ = cv.projectPoints(world_points, cv.Rodrigues(self.R)[0], self.T.reshape((3, 1)),
                                               self.K, self.distortion)
        img_points_repro = img_points_repro.reshape((len(img_points_repro), 2))

        return img_points_repro

    def img2world(self, image_points):
        """
        TODO：像素点转换至世界坐标系
        :param image_points:
        :return:
        """
        # 相机内参
        intrinsic = np.asmatrix(self.K)

        # 齐次坐标系下的像素坐标, 3 x n
        homo_image_points = np.column_stack([image_points, np.ones((len(image_points), 1))]).T
        homo_image_points = np.asmatrix(homo_image_points)

        # 旋转矩阵
        rotate_matrix = np.asmatrix(self.R)
        # 平移
        translate_matrix = np.asmatrix(self.T)

        camera_rotate = intrinsic * rotate_matrix
        camera_translate = intrinsic * (translate_matrix.T)
        camera_rotate_inv = np.linalg.inv(camera_rotate)

        world_point_z = 0
        matrix1 = camera_rotate_inv * camera_translate

        matrix2 = camera_rotate_inv * homo_image_points

        world_point_x = ((matrix1[2][0] + world_point_z) * matrix2[0] / matrix2[2]) - matrix1[0]
        world_point_y = ((matrix1[2][0] + world_point_z) * matrix2[1] / matrix2[2]) - matrix1[1]

        return np.concatenate([np.array(world_point_x[0]), np.array(world_point_y[0])]).T

    def base_info_to_json(self):
        """
        TODO:  将相机的基准信息转换为json格式
        :return:
        """
        pass

    def load_camera_from_json(self):
        """
        TODO: 加载相机数据
        :return:
        """
        pass

    def orthophoto_mapping(self):
        """
        TODO: 生成正射影像
        """


class UAVCameraModel(BaseCameraModel):
    """
    无人机对应的相机模型, 包括初始化DJ参数， 初始化相机内参， 生成相机标定点对， 求解相机外参
    """

    def __init__(self,
                 image_names: list,
                 base_info: dict,
                 kp_detector,
                 idx: int,
                 ):
        super().__init__(image_names)

        # 拍摄时对应的经纬度
        self.latitude = None
        self.longitude = None
        self.fly_height = None
        self.proj_x = None
        self.proj_y = None
        # 拍摄照片的大小
        self.h, self.w = cv.imread(image_names[0]).shape[:2]
        # 相机角度信息
        self.pitch = None
        self.roll = None
        self.yaw = None
        # 相机内参、外参参数信息
        self.f_35mm = None
        self.relative_R = None  # 相对于基础坐标系的旋转矩阵
        self.distortion = [0, 0, 0, 0, 0]  # 已经去过畸变的图像
        self.ret = None  # 反投影像素误差值
        self.mapping_ratio = 1  # 相机坐标系投影到世界投影坐标系下的比例
        self.T = None  # 平移矩陣
        # 初始化相机参数
        if base_info is not None:
            self.init_dj_params(base_info)
            self.euler2rot()
        # 初始化关键点检测器
        self.kp_detector = kp_detector

        # 一些相机奇奇怪怪的属性, 相机模型采用小孔成像模型
        camera_model_option = pycolmap.ImageReaderOptions()
        camera_model_option.camera_model = 'SIMPLE_PINHOLE'
        self.camera_model = pycolmap.infer_camera_from_image(self.capture_image_names[idx],
                                                             options=camera_model_option)

        self.K = self.camera_model.calibration_matrix()
        self.base_camera_index = None  # 定位基准相机索引
        self.camera_min_bound = None  # 相机的最小定位范围
        self.bev_euler = None  # 俯视对应的位姿信息
        self.is_calibration = 0  # 相机对应的是否标定的标签
        self.H = np.identity(3)

        self.panorama_info = None  # 全景相片信息

    def init_dj_params(self, base_info):
        """
        TODO: 加载DJ图像基础信息
        :param base_info:
        :return:
        """
        if "DewarpData" in list(base_info.keys()):
            # cx, xy, k1, k2, k3, p1, p2
            self.distortion = [float(dist) for dist in base_info['DewarpData'].split('"')[1].split(";")[1].split(",")]
        self.latitude = float(base_info['GpsLatitude'].split('"')[1])
        self.longitude = float(base_info['GpsLongitude'].split('"')[1])
        self.fly_height = float(base_info['AbsoluteAltitude'].split('"')[1])
        self.yaw = float(base_info['GimbalYawDegree'].split('"')[1])
        self.pitch = float(base_info['GimbalPitchDegree'].split('"')[1])
        self.roll = float(base_info['GimbalRollDegree'].split('"')[1])
        self.f = float(base_info['focal'])
        self.T = np.array([[self.proj_x], [self.proj_y], [self.fly_height]])

    def euler2rot(self):
        self.relative_R = Rotation.from_euler('zxy', [self.roll, self.pitch, self.yaw], degrees=True).as_matrix()

    def img2world_without_calibration(self, points):
        """
        TODO: 获取图像四个角点的坐标
        param points: 圖像像素點齊次坐標, shape (3 * n), [[x1, x2, ...], [y1, y2, ...], [1, 1, ...]]
        """
        res_points = []
        for point in np.array(points):
            rows_mapped, cols_mapped, z = self.GetGroundCoordinates(point[1], point[0])
            # 計算平面坐標
            res_points.append([rows_mapped, cols_mapped])

        return np.array(res_points)

    def GetGroundCoordinates(self, x, y):
        max_angle = 90 + self.pitch * (180 / np.pi) - 5
        maxy = np.tan(np.radians(max_angle))*1
        image_point = np.array([[x], [y], [1]])
        cam_point = np.dot(np.linalg.inv(self.K), image_point)

        angle = self.angle_between_lines(np.array([[0], cam_point[1],
                                                   cam_point[2]]),
                                         np.array([[0], [0],
                                                   cam_point[2]]))
        condition = (angle-self.pitch * (180 / np.pi)) > 90

        if x.shape == ():
            cam_point[1][condition] = np.abs(cam_point[1])/cam_point[1]*maxy*0.99999
        else:
            cam_point[1][0][condition] = (np.sign(cam_point[1][0])*maxy*0.99999)[condition]
        res_point = np.dot(np.linalg.inv(self.relative_R), cam_point)

        res_pointM = res_point / 1000.0
        z_plane = self.fly_height
        x0, y0, z0 = [0, 0, 0]
        x1, y1, z1 = res_pointM
        t = (z_plane - z0) / (z1 - z0)
        x_intersect = x0 + t * (x1 - x0)
        y_intersect = y0 + t * (y1 - y0)
        z_intersect = z_plane

        world_pointR = np.array([-x_intersect, y_intersect, [z_intersect]])

        world_point = -world_pointR + self.T
        if x.shape == ():
            self.OR.append(cam_point)
            self.RE.append(res_point)
        return world_point[0, 0], world_point[1, 0], world_point[2, 0]


    def angle_between_lines(self, point1, point2):
        # 计算直线的方向向量
        vec1 = point1 - np.array([[0], [0], [0]])
        vec2 = point2 - np.array([[0], [0], [0]])

        # 计算向量的模
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        # 计算点积
        dot_product = np.dot(vec1.flatten(), vec2.flatten())

        # 计算夹角（弧度）
        angle_rad = np.arccos(dot_product / (norm1 * norm2))

        # 将弧度转换为度数
        angle_deg = np.degrees(angle_rad)

        return angle_deg


    def generate_calibration_points(self, bev_id, map_geo_trans, map_dataset):
        """
        生成标定点对
        1. 根据照片拍摄位置筛选出4张候选图片
        2. 利用LoFTR对候选图片进行匹配, 找到best one
        3. 生成点对（带dsm）
        :return:
        """
        # 以拍摄地为中心， 筛选出一块bound
        # print(self.proj_x, self.proj_y)
        # print(map_geo_trans)
        # print(self.proj_x - map_geo_trans[3])
        # print(self.proj_y - map_geo_trans[0])
        bound_min_y, bound_min_x = int((self.proj_x - map_geo_trans[0]) / map_geo_trans[1]) - 5000,\
                                                    int((self.proj_y - map_geo_trans[3]) / map_geo_trans[-1]) - 5000

        # print(bound_min_y, bound_min_y)
        # 超出边界需要修改(需要改进)
        if bound_min_x < 0:
            bound_min_x = 0
        if bound_min_y < 0:
            bound_min_y = 0

        # image matching , then find the best tif to generate caliration points
        img0 = cv.imread(self.capture_image_names[bev_id])
        # transfer to bev
        bev_img0 = self.bev_transform(img0)
        bev_img0 = cv.cvtColor(bev_img0, cv.COLOR_BGR2RGB)
        img1 = map_dataset.ReadAsArray(bound_min_y, bound_min_x, 5000, 5000).transpose(1, 2, 0)[:, :, :3]
        cv.imwrite("./test_bev.png", img1)
        # 获取对应图片的左上角点坐标和对应的分辨率信息
        cur_geotrans = [map_geo_trans[0] + map_geo_trans[1] * bound_min_y, map_geo_trans[1],
                        map_geo_trans[3] + map_geo_trans[5] * bound_min_x, map_geo_trans[5]]
        ret, matching_points_info = self.kp_detector.get_matching_points(bev_img0, img1)

        if ret == 0:
            return 0, None, None, None, None
        image_points, world_points = matching_points_info['key_points_pair']
        image_points = self.bev_perspective_recover(image_points)
        # transfer image points to origin
        homography_matrix = matching_points_info['homography_matrix']

        return ret, image_points, world_points, homography_matrix, cur_geotrans

    def bev_transform(self, img):
        """
        TODO: 将所有角度图片转换成BEV(纯旋转)
        1. 初始化内参信息(标定后的内参信息, 即self.K不为None)
        2. 恢复位姿(原始坐标系)
        3. 转换位姿(BEV)
        :return:
        """
        if self.K is None:
            assert "请先初始化内参信息"

        # 原始位姿 self.relative_R
        self.euler2rot()
        # BEV欧拉角, pitch为-90
        bev_rotate = Rotation.from_euler('zxy', [0, -90, 0], degrees=True).as_matrix()
        # 构建转换矩阵
        H = np.dot(self.K, np.dot(np.linalg.inv(bev_rotate),
                                  np.dot(self.relative_R, np.linalg.inv(self.K))))
        # BEV转换
        bev_img = cv.warpPerspective(img, H, (self.w, self.h))
        return bev_img

    def bev_perspective_recover(self, image_points):
        """
        TODO: 将BEV视角下的点坐标转换为原始坐标
        :param image_points:
        :return:
        """
        if self.K is None:
            assert "请先初始化内参信息"

        # 原始位姿 self.relative_R
        self.euler2rot()
        # BEV欧拉角, pitch为-90
        bev_rotate = Rotation.from_euler('zxy', [0, -90, 0], degrees=True).as_matrix()
        # 构建转换矩阵
        H = np.dot(self.K, np.dot(np.linalg.inv(self.relative_R),
                                  np.dot(bev_rotate, np.linalg.inv(self.K))))
        # recover pose
        original_points = cv.perspectiveTransform(image_points.reshape(-1, 1, 2).astype(np.float32), H)

        # print(original_points.reshape(-1, 2))

        return original_points.reshape(-1, 2)

    def bev_perspective(self, image_points):
        """
        TODO: 将原始坐标下的点坐标转换为BEV视角下
        :param image_points:
        :return:
        """
        if self.K is None:
            assert "请先初始化内参信息"

        # 原始位姿 self.relative_R
        self.euler2rot()
        # BEV欧拉角, pitch为-90
        bev_rotate = Rotation.from_euler('zxy', [0, -90, 0], degrees=True).as_matrix()
        # 构建转换矩阵
        H = np.dot(self.K, np.dot(np.linalg.inv(bev_rotate),
                                  np.dot(self.relative_R, np.linalg.inv(self.K))))
        # recover pose
        original_points = cv.perspectiveTransform(image_points.reshape(-1, 1, 2).astype(np.float32), H)

        # print(original_points.reshape(-1, 2))

        return original_points.reshape(-1, 2)

    def perspective_transform(self, adjacent_camera_model):
        """
        TODO:将当前图片转换至邻接图片
        :return:
        """
        # correct R
        adjacent_camera_model.relative_R = \
            Rotation.from_euler('zxy', [adjacent_camera_model.roll,
                                adjacent_camera_model.pitch - 15, adjacent_camera_model.yaw], degrees=True).as_matrix()
        # 视角转换矩阵
        transform_matrix = np.dot(self.K, np.dot(np.linalg.inv(adjacent_camera_model.relative_R),
                                                 np.dot(self.relative_R, np.linalg.inv(self.K))))
        return transform_matrix

    def perspective_recover(self, adjacent_camera_model):
        """
        TODO:将当前图片转换至邻接图片
        :return:
        """
        # 视角转换矩阵
        adjacent_camera_model.relative_R = \
            Rotation.from_euler('zxy', [adjacent_camera_model.roll,
                                        adjacent_camera_model.pitch - 15, adjacent_camera_model.yaw], degrees=True).as_matrix()

        recover_transform_matrix = np.dot(self.K, np.dot(np.linalg.inv(self.relative_R),
                                        np.dot(adjacent_camera_model.relative_R, np.linalg.inv(self.K))))
        return recover_transform_matrix

    def base_info_to_json(self):
        """
        TODO:  将相机的基准信息转换为json格式
        :return:
        """
        base_info = {
            'latitude':          self.latitude,
            'longitude':         self.longitude,
            'fly_height':        self.fly_height,
            'proj_x':            self.proj_x,
            'proj_y':            self.proj_y,
            'w':                 self.w,
            'h':                 self.h,
            'pitch':             self.pitch,
            'roll':              self.roll,
            'yaw':               self.yaw,
            'R':                 self.R,
            'T':                 self.T,
            'K':                 self.K,
            'is_calibration':    self.is_calibration,
            'base_camera_index': self.base_camera_index
        }

        return base_info

    def load_camera_from_json(self, base_info: dict):
        """
        TODO: 加载相机的基础信息
        :param base_info: 相机基础信息字典
        :return:
        """
        # 拍摄时对应的经纬度
        self.latitude = base_info['latitude']
        self.longitude = base_info['longitude']
        self.fly_height = base_info['fly_height']
        self.proj_x = base_info['proj_x']
        self.proj_y = base_info['proj_y']
        # 拍摄照片的大小
        self.w, self.h = base_info['w'], base_info['h']
        # 相机角度信息
        self.pitch = base_info['pitch']
        self.roll = base_info['roll']
        self.yaw = base_info['yaw']
        # 相机内参、外参参数信息
        self.R = base_info['R']
        self.T = base_info['T']
        self.K = base_info['K']
        # 初始化相机参数及一些奇奇怪怪的参数信息
        self.euler2rot()
        self.base_camera_index = base_info['base_camera_index']  # 定位基准相机索引
        self.is_calibration = base_info['is_calibration']  # 相机对应的是否标定的标签

    def raster2img(self, raster_points):
        """
        TODO:世界点转换到像素坐标
        :return:
        """
        img_points_repro, _ = cv.projectPoints(raster_points, cv.Rodrigues(self.R)[0], self.T.reshape((3, 1)),
                                               self.K, self.distortion)
        img_points_repro = img_points_repro.reshape((len(img_points_repro), 2))

        return img_points_repro

    def img2raster(self, image_points):
        """
        TODO：像素点转换至世界坐标系
        :param image_points:
        :return:
        """
        # 相机内参
        intrinsic = np.asmatrix(self.K)

        # 齐次坐标系下的像素坐标, 3 x n
        homo_image_points = np.column_stack([image_points, np.ones((len(image_points), 1))]).T
        homo_image_points = np.asmatrix(homo_image_points)

        # 旋转矩阵
        rotate_matrix = np.asmatrix(self.R)
        # 平移
        translate_matrix = np.asmatrix(self.T)

        camera_rotate = intrinsic * rotate_matrix
        camera_translate = intrinsic * (translate_matrix.T)
        camera_rotate_inv = np.linalg.inv(camera_rotate)

        world_point_z = 0
        matrix1 = camera_rotate_inv * camera_translate

        matrix2 = camera_rotate_inv * homo_image_points

        raster_point_x = ((matrix1[2][0] + world_point_z) * matrix2[0] / matrix2[2]) - matrix1[0]
        raster_point_y = ((matrix1[2][0] + world_point_z) * matrix2[1] / matrix2[2]) - matrix1[1]

        return np.concatenate([np.array(raster_point_x[0]), np.array(raster_point_y[0])]).T

    def orthophoto_mapping(self, img):
        """
        TODO: 根据相片信息生成正射影像
        """

        # transfer to BEV (north)
        bev_image = self.bev_transform(img)

        # 图片去畸变, un-distort(有畸变系数就做)
        if self.distortion is not None:
            bev_image = cv.undistort(bev_image, self.K, np.array(self.distortion[4:]))

        # 生成所有像素点坐标
        row = np.repeat(np.arange(0, self.h), self.w)
        col = np.tile(np.arange(0, self.w), self.h)
        # construct homo image points
        homo_image_points = np.column_stack([col, row, np.ones_like(row)])

        # points coord based on camera with camera intrinsics
        camera_points = np.dot(np.linalg.inv(self.K), homo_image_points.T)  # unit pixel
        # transfer points into bev coord
        camera_points_bev = np.dot(np.linalg.inv(self.relative_R), camera_points)[:2, :]

        # print(camera_points_bev)

        camera_points_bev = camera_points_bev * np.array([[self.sensor_size / self.w],
                                                  [self.sensor_size / self.h]])  # unit m
        # print(camera_points_bev)
        # # calculate per pixel length m/pixel
        resolution_per_pixel = self.mapping_ratio * camera_points_bev
        # print(resolution_per_pixel)
        # print(resolution_per_pixel[0])
        # print(resolution_per_pixel[1])
        #
        #
        # # generate corners coords
        #
        #
        # return relative_proj_coord, bev_image


class UAVVideoModel(UAVCameraModel):
    """
    大疆无人机视频类
    """

    def __init__(self, video_name: str,
                 key_points_detector: KeyPointsDetector):
        """
        TODO: 初始化视频相关参数
        :param video_name: 视频名称
        :param key_points_detector: 关键点检测器
        """
        self.f = 4.8
        self.video_name = video_name  # 无人机拍摄的视频名称
        # 获取视频流对象
        self.video_capture = cv.VideoCapture(self.video_name)   # 获取视频流类
        self.frame_per_second = []  # 视频每一秒对应的图片信息
        self.timestamp = []  # 对应的时间戳信息
        self.Ks_t = None  # 视频每一秒对应的相机内参
        self.Rs_t = []  # 视频每一秒对应的旋转参数
        self.Ts_t = []  # 视频每一秒对应的平移参数
        self.width = None  # 视频画面宽
        self.height = None  # 视频画面高
        self.fps = None  # 视频的帧率
        self.total_frames = None  # 视频总帧率
        self.key_points_detector = key_points_detector  # 视频点检测器

        # 一些相机对应的奇奇怪怪的属性, pycolmap
        # self.camera_model_option = pycolmap.ImageReaderOptions()
        # self.camera_model_option.camera_model = 'SIMPLE_PINHOLE'
        self.camera_models = []

    def read_video(self):
        """
        TODO：读取视频流
        """

        self.fps = self.video_capture.get(cv.CAP_PROP_FPS)      # 获取视频帧率
        self.width, self.height = int(self.video_capture.get(cv.CAP_PROP_FRAME_WIDTH)), int(
            self.video_capture.get(cv.CAP_PROP_FRAME_HEIGHT))  # 获取视频的分辨率
        self.total_frames = self.video_capture.get(7)
        # 抽帧
        success, frame = self.video_capture.read()  # 从第0帧开始读取视频
        second_idx = 0
        while success:
            # 添加帧信息
            self.frame_per_second.append(frame)
            self.timestamp.append(second_idx)
            # focal: 145 = 2 atan(0.5 * image_width / focal(pixel))
            self.camera_models.append(pycolmap.Camera({'model': 'SIMPLE_PINHOLE',
                                                       'width': self.width,
                                                       'height': self.height,
                                                       'params': [1728, self.width / 2, self.height / 2],
                                                       }))

            cv.imwrite(r'D:\mgr\uav video\test_video\Frame/{}.png'.format(second_idx), frame)
            # 获取下一秒的数据
            second_idx += 1
            self.video_capture.set(cv.CAP_PROP_POS_FRAMES, second_idx)
            success, frame = self.video_capture.read()
        self.Ks = [camera_model.calibration_matrix() for camera_model in self.camera_models]


if __name__ == '__main__':
    # uav = UAVCameraModel()
    file = r'D:\mgr\GTMap\uav-monitoring-service\data\panorama\17\PANO0001.JPG'
    img1 = r'F:\GTMap\CameraLocalization\data\DJ_IMG\1.jpg'
    img2 = r'F:\GTMap\CameraLocalization\data\DJ_IMG\2.jpg'
    """
     [[ 1.15149197e+00 -8.51614938e-01  5.32020493e+01]
     [ 8.00931115e-01  1.13905861e+00 -8.40478512e+01]
     [-2.89242343e-05 -1.05105013e-04  1.00000000e+00]]
    """
    # H = np.array([[1.15149197e+00, -8.51614938e-01, 5.32020493e+01],
    #               [8.00931115e-01,  1.13905861e+00, -8.40478512e+01],
    #               [-2.89242343e-05, -1.05105013e-04,  1.00000000e+00]])
    # res_img = cv.warpPerspective(cv.imread(img1), H, (1024, 1024))

    # print(pycolmap.absolute_pose_estimation([np.array([np.array([[2], [1]],dtype=np.float64)])],
    #                                         [np.array([np.array([[2], [2], [1]], dtype=np.float64)]),
    #                                          pycolmap.Camera]))
    img = cv.imread(r'D:\mgr\GTMap\uav-monitoring-service\data\panorama\17\PANO0001.JPG')
    camera = pycolmap.infer_camera_from_image(r'D:\mgr\GTMap\uav-monitoring-service\data\panorama\17\PANO0001.JPG')
    # camera.params[0] = 1500
    relative_R = Rotation.from_euler('zxy', [0, -90, -42.90], degrees=True).as_matrix()
    # BEV欧拉角, pitch为-90
    bev_rotate = Rotation.from_euler('zxy', [0, -60.2, -42.9], degrees=True).as_matrix()
    # 构建转换矩阵
    H = np.dot(camera.calibration_matrix(), np.dot(np.linalg.inv(bev_rotate),
                              np.dot(relative_R, np.linalg.inv(camera.calibration_matrix()))))
    # BEV转换
    bev_img = cv.warpPerspective(img, H, (5472, 3648))







