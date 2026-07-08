# @Time : 2024/1/2 11:09
# @Author : Ma Guorui
# @Description : 📷

import numpy as np
import cv2 as cv
#import pycolmap
from scipy.spatial.transform import Rotation
import pickle


class BaseVideoLoader:
    """
    基础视频加载器
    """
    SENSOR_PARAMS = {
        "1/2.8": [3.429, 4.571],
        "1/35": [36, 24]
    }

    def __init__(self, video_name, key_points_detector):
        self.f = 4.8
        self.video_name = video_name                    # 无人机拍摄的视频名称
        self.frame_per_second = []                      # 视频每一秒对应的图片信息
        self.timestamp = []                             # 对应的时间戳信息
        self.Ks_t = None                                # 视频每一秒对应的相机内参
        self.Rs_t = []                                  # 视频每一秒对应的旋转参数
        self.Ts_t = []                                  # 视频每一秒对应的平移参数
        self.width = None                               # 视频画面宽
        self.height = None                              # 视频画面高
        self.fps = None                                 # 视频的帧率
        self.total_frames = None                        # 视频总帧率
        self.key_points_detector = key_points_detector  # 视频点检测器

        # 一些相机对应的奇奇怪怪的属性, pycolmap
        # self.camera_model_option = pycolmap.ImageReaderOptions()
        # self.camera_model_option.camera_model = 'SIMPLE_PINHOLE'
        self.camera_models = []
        self.ransac_options = pycolmap.RANSACOptions(
                            max_error=2.0,         # reprojection error in pixels
                            min_inlier_ratio=0.01,
                            confidence=0.9999,
                            min_num_trials=10000,
                            max_num_trials=100000,
                            )

    def read_video(self):
        """
        读取视频流
        """
        # 获取视频流对象
        self.video_capture = cv.VideoCapture(self.video_name)         # 获取视频流类
        self.fps = self.video_capture .get(cv.CAP_PROP_FPS)            # 获取视频帧率
        self.width, self.height = int(self.video_capture .get(cv.CAP_PROP_FRAME_WIDTH)), int(self.video_capture .get(cv.CAP_PROP_FRAME_HEIGHT))  # 获取视频的分辨率
        self.total_frames = self.video_capture.get(7)
        # 抽帧
        success, frame = self.video_capture.read()   # 从第0帧开始读取视频
        second_idx = 0
        while success:
            # 添加帧信息
            self.frame_per_second.append(frame)
            self.timestamp.append(second_idx)
            # focal: 145 = 2 atan(0.5 * image_width / focal(pixel))
            self.camera_models.append(pycolmap.Camera({'model':  'SIMPLE_PINHOLE',
                                                       'width':  self.width,
                                                       'height': self.height,
                                                       'params': [1728, self.width / 2, self.height / 2],
                                                       }))

            # plt.imshow(frame)
            # plt.show()
            # 获取下一秒的数据
            second_idx += 1
            self.video_capture.set(cv.CAP_PROP_POS_FRAMES, second_idx * self.fps)
            success, frame = self.video_capture.read()
        print(len(self.timestamp))
        self.Ks = [camera_model.calibration_matrix() for camera_model in self.camera_models]

    def relative_pose_solve(self):
        """
        相对位姿解算, 前一帧和后一帧图像的相对位姿
        """
        pre_frame = self.frame_per_second[:-1]
        cur_frame = self.frame_per_second[1:]
        for i in range(0, min(360, len(pre_frame))):
            try:
                # plt.imshow(np.concatenate([pre_frame[i], cur_frame[i]], axis=1))
                # plt.show()
                matching_points_info = self.key_points_detector.get_matching_points(pre_frame[i], cur_frame[i])
                points1, points2 = matching_points_info['key_points_pair']
                answer = pycolmap.essential_matrix_estimation(points2,
                                                              points1,
                                                              self.camera_models[i],
                                                              self.camera_models[i + 1],
                                                              estimation_options=self.ransac_options
                                                              )
                self.Ts.append(answer['tvec'])
                self.Rs.append(answer['qvec'])
            except:
                self.Ts.append(None)
                self.Rs.append(None)
                continue
        # print(np.array(self.Ts))
        # plt.plot(np.arange(0, len(self.Ts)), np.cumsum(np.array(self.Ts)[:, 2]))
        # plt.show()
        # plt.plot(np.arange(0, len(self.Rs)), np.sum(self.Rs, axis=1))
        # plt.show()
        with open(r"597 12.4.pkl", 'wb') as f:
            pickle.dump({
                "T": self.Ts,
                "R": self.Rs
            }, f)


if __name__ == '__main__':
    # key_points_detector = KeyPointsDetector()
    # video_module = BaseVideoLoader(r'D:\mgr\uav video\12.1\597 12.4.mp4', key_points_detector)
    # video_module.read_video()
    # video_module.relative_pose_solve()

    import pandas as pd
    with open(r"D:\mgr\GTMap\BEVFormer\tools\analysis_tools\597 12.4.pkl", 'rb') as f:
        data = pickle.load(f)
    # print(data['T'])

    t = []
    for i in data['T']:
        if i is None:
            t.append(np.array([np.nan, np.nan, np.nan]))
        else:
            t.append(i)

    r = []
    for i in data['R']:
        if i is None:
            r.append(np.array([np.nan, np.nan, np.nan]))
            print("")
        else:
            rotation = pycolmap.qvec_to_rotmat(i)
            euler = Rotation.from_matrix(rotation).as_euler('zxy', degrees=True)
            print(euler)
            r.append(euler)

    T_df = pd.DataFrame(data=t)
    R_df = pd.DataFrame(data=r)
    T_df.to_excel("597 12.4_T.xlsx")
    R_df.to_excel("597 12.4_R.xlsx")

