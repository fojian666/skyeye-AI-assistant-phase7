# @Time : 2023/7/20 10:14
# @Author : Ma Guorui
# @Description : 📷

import torch
import cv2 as cv
import numpy as np
from kornia.feature import LoFTR
from logger import Logger
from tqdm import *
import matplotlib.pyplot as plt
#from lightglue import LightGlue, SuperPoint, viz2d
#from lightglue.utils import load_image, rbd, numpy_image_to_torch


logger = Logger(logname='camera_ai_model.log', loglevel=4, logger='ModelInfo').getlog()


class KeyPointsDetector:
    """
    @article{sun2021loftr,
    title={{LoFTR}: Detector-Free Local Feature Matching with Transformers},
    author={Sun, Jiaming and Shen, Zehong and Wang, Yuang and Bao, Hujun and Zhou, Xiaowei},
    journal={{CVPR}},
    year={2021}
    }
    """
    def __init__(self, ckpt, h_threshold=1.5, h_confidence=0.999, h_iternums=10000):
        """
        TODO:
        :param h_threshold:
        :param h_confidence:
        :param h_iternums:
        """
        # RANSAC算法相关参数
        self.h_threshold = h_threshold
        self.h_confidence = h_confidence
        self.h_iternums = h_iternums
        # 初始化LoFTR
        self.matcher = LoFTR(None)
        self.matcher.load_state_dict(torch.load(ckpt)['state_dict'])
        self.init_loftr(torch.cuda.is_available())

        # 匹配的两张图片对应的尺寸信息
        self.image_resize_ratio = {}

    def init_loftr(self, cuda):
        """
        TODO: 初始化loftr模型
        :param cuda:
        :return:
        """
        logger.info("初始化LoFTR模型，GPU{}".format('可用' if cuda else '不可用'))
        if cuda:
            self.matcher = self.matcher.eval().cuda()  #

    def load_torch_image(self, img: np.array, image_name: str,
                         resize_width=1440, resize_height=1440):
        """
        TODO: 将 numpy 图片数据转换成 torch 图片数据
        :param img:
        :param image_name:
        :return:
        """
        height, width = img.shape[:2]
        self.image_resize_ratio[image_name] = np.array([img.shape[1] / resize_width, img.shape[0] / resize_height])

        if (width < resize_width) or (height < resize_height):
            img = cv.resize(img, (resize_width, resize_height), interpolation=cv.INTER_LINEAR)
        else:
            img = cv.resize(img, (resize_width, resize_height), interpolation=cv.INTER_AREA)

        if torch.cuda.is_available():
            gray_scale_img = torch.from_numpy(cv.cvtColor(img, cv.COLOR_RGB2GRAY))[None][None].cuda() / 255.
        else:
            gray_scale_img = torch.from_numpy(cv.cvtColor(img, cv.COLOR_RGB2GRAY))[None][None] / 255.

        return gray_scale_img

    def get_matching_points(self, img0, img1):
        """
        TODO: 利用Loftr生成相邻图片的关键点对, 对应内点数
        :return:
        """
        # 加载灰度图至gpu
        cur_torch_grayscale_image = self.load_torch_image(img0, 'image0')
        adjacent_torch_grayscale_image = self.load_torch_image(img1, 'image1')

        # 关键点检测
        adjacent_images_info = {"image0": cur_torch_grayscale_image, "image1": adjacent_torch_grayscale_image}

        cur_kps, adjacent_kps = self.getKeyPoints(adjacent_images_info)
        if len(cur_kps) < 40:
            return 0, None

        homography_matrix, inliers = cv.findHomography(cur_kps * self.image_resize_ratio['image0'],
                                                       adjacent_kps * self.image_resize_ratio['image1'], cv.USAC_MAGSAC,
                                                   self.h_threshold, self.h_confidence, self.h_iternums)
        inliers_index = np.where(inliers == 1)

        matching_points_info = {"key_points_pair": [cur_kps[inliers_index[0], :] * self.image_resize_ratio['image0'],
                                                    adjacent_kps[inliers_index[0], :] * self.image_resize_ratio['image1']],
                                'num_inlier_point': np.sum(inliers),
                                'homography_matrix': homography_matrix}
        # # 可视化
        # draw_LAF_matches(
        #     KF.laf_from_center_scale_ori(torch.from_numpy(cur_kps).view(1, -1, 2),
        #                                  torch.ones(cur_kps.shape[0]).view(1, -1, 1, 1),
        #                                  torch.ones(cur_kps.shape[0]).view(1, -1, 1)),
        #
        #     KF.laf_from_center_scale_ori(torch.from_numpy(adjacent_kps).view(1, -1, 2),
        #                                  torch.ones(adjacent_kps.shape[0]).view(1, -1, 1, 1),
        #                                  torch.ones(adjacent_kps.shape[0]).view(1, -1, 1)),
        #     torch.arange(cur_kps.shape[0]).view(-1, 1).repeat(1, 2),
        #     cur_torch_grayscale_image,
        #     adjacent_torch_grayscale_image,
        #     inliers,
        #     draw_dict={'inlier_color': (0.2, 1, 0.2),
        #                'tentative_color': None,
        #                'feature_color': (0.2, 0.2, 1), 'vertical': False})
        return np.sum(inliers), matching_points_info

    def generating_matching_points(self, cur_image_name, adjacent_image_name, is_split_image=0):
        """
        TODO: 利用Loftr生成相邻图片(需要视角转换)的关键点对, 对应内点数
        :return:
        """
        img0 = cv.imread(cur_image_name)
        img0 = cv.cvtColor(img0, cv.COLOR_BGR2RGB)
        cur_torch_grayscale_image = self.load_torch_image(img0, cur_image_name)
        matching_points_info = {cur_image_name: {}}

        num_inliers = []
        cover_area = []
        for i_name in tqdm(adjacent_image_name):
            img1 = cv.imread(i_name)
            img1 = cv.cvtColor(img1, cv.COLOR_BGR2RGB)
            adjacent_torch_grayscale_image = self.load_torch_image(img1, i_name)
            # 关键点检测
            adjacent_images_info = {"image0": cur_torch_grayscale_image, "image1": adjacent_torch_grayscale_image}

            cur_kps, adjacent_kps = self.getKeyPoints(adjacent_images_info)
            if len(cur_kps) < 40:
                matching_points_info[cur_image_name][i_name] = None
                num_inliers.append(0)
                continue

            homography_matrix, inliers = cv.findHomography(cur_kps * self.image_resize_ratio[cur_image_name],
                                                           adjacent_kps * self.image_resize_ratio[i_name],
                                                           cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)
            homography_matrix_inv, inliers_inv = cv.findHomography(adjacent_kps * self.image_resize_ratio[i_name],
                                                                   cur_kps * self.image_resize_ratio[cur_image_name],
                                                           cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)
            inliers_index = np.where(inliers == 1)
            matching_points_info[cur_image_name][i_name] = {"key_points_pair":
                                                                [cur_kps[inliers_index[0], :] * self.image_resize_ratio[
                                                                    cur_image_name],
                                                                 adjacent_kps[inliers_index[0], :] *
                                                                 self.image_resize_ratio[i_name]],
                                                            'num_inlier_point': np.sum(inliers),
                                                            'homography_matrix': homography_matrix,
                                                            'homography_matrix_inv':homography_matrix_inv}

            min_rec = cv.minAreaRect(cur_kps[inliers_index[0], :].astype(np.float32))
            weight, height = min_rec[1]
            area = weight * height
            cover_area.append(area)
            num_inliers.append(np.sum(inliers))
            #
            # 可视化
            # draw_LAF_matches(
            #     KF.laf_from_center_scale_ori(torch.from_numpy(cur_kps).view(1, -1, 2),
            #                                  torch.ones(cur_kps.shape[0]).view(1, -1, 1, 1),
            #                                  torch.ones(cur_kps.shape[0]).view(1, -1, 1)),
            #
            #     KF.laf_from_center_scale_ori(torch.from_numpy(adjacent_kps).view(1, -1, 2),
            #                                  torch.ones(adjacent_kps.shape[0]).view(1, -1, 1, 1),
            #                                  torch.ones(adjacent_kps.shape[0]).view(1, -1, 1)),
            #     torch.arange(cur_kps.shape[0]).view(-1, 1).repeat(1, 2),
            #     cur_torch_grayscale_image,
            #     adjacent_torch_grayscale_image,
            #     inliers,
            #     draw_dict={'inlier_color': (0.2, 1, 0.2),
            #                'tentative_color': (0.8, 0.8, 0),
            #                'feature_color': (0.2, 0.2, 1), 'vertical': False})
            # print(num_inliers)

        # 选择最优的图片索引
        optimize_idx = None
        max_area = 0
        for i in range(len(num_inliers)):
            if num_inliers[i] > 500:
                if max_area < cover_area[i]:
                    optimize_idx = i

        if optimize_idx is None:
            optimize_idx = np.argmax(num_inliers)

        return np.max(num_inliers), adjacent_image_name[optimize_idx], \
            matching_points_info[cur_image_name][adjacent_image_name[optimize_idx]]

    def generating_matching_points_with_pose(self, cur_image_name, cur_camera_model, adjacent_image_name,
                                             adjacent_camera_model):
        """
        TODO: 利用Loftr生成相邻图片(需要视角转换)的关键点对, 对应内点数
        :return:
        """
        # 读取当前
        img0 = cv.imread(cur_image_name)
        img0 = cv.cvtColor(img0, cv.COLOR_BGR2RGB)
        cur_torch_grayscale_image = self.load_torch_image(img0, cur_image_name, 1400, 1400)
        matching_points_info = {cur_image_name: {}}

        num_inliers = []
        cover_area = []
        for i in tqdm(range(len(adjacent_image_name))):
            i_name = adjacent_image_name[i]
            img1 = cv.imread(i_name)
            img1 = cv.cvtColor(img1, cv.COLOR_BGR2RGB)
            # 将img1转换视角
            camera1 = adjacent_camera_model[i]

            transform_matrix = camera1.perspective_transform(cur_camera_model)  # 视角转换矩阵
            # perspective transformer
            perspective_img1 = cv.warpPerspective(img1, transform_matrix, (img1.shape[1], img1.shape[0]))
            adjacent_torch_grayscale_image = self.load_torch_image(perspective_img1, i_name, 1400, 1400)
            # 关键点检测
            adjacent_images_info = {"image0": cur_torch_grayscale_image, "image1": adjacent_torch_grayscale_image}

            cur_kps, adjacent_kps = self.getKeyPoints(adjacent_images_info)

            if len(cur_kps) < 40:
                matching_points_info[cur_image_name][i_name] = None
                num_inliers.append(0)
                continue

            # 像素点坐标恢复到原图大小
            # print(self.image_resize_ratio)
            cur_kps = cur_kps * self.image_resize_ratio[cur_image_name]
            adjacent_kps = adjacent_kps * self.image_resize_ratio[i_name]
            # 将坐标点进行恢复
            homography_matrix, inliers = cv.findHomography(cur_kps, adjacent_kps, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            homography_matrix_inv, inliers_inv = cv.findHomography(adjacent_kps, cur_kps, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            # perspective_img2 = cv.warpPerspective(perspective_img1, homography_matrix_inv, (img1.shape[1], img1.shape[0]))

            inliers_index = np.where(inliers == 1)
            matching_points_info[cur_image_name][i_name] = {"key_points_pair": [cur_kps[inliers_index[0], :],
                                                                                adjacent_kps[inliers_index[0], :]],
                                                            'num_inlier_point': np.sum(inliers),
                                                            'homography_matrix': homography_matrix,
                                                            'homography_matrix_inv':homography_matrix_inv}

            min_rec = cv.minAreaRect(cur_kps[inliers_index[0], :].astype(np.float32))
            weight, height = min_rec[1]
            area = weight * height
            cover_area.append(area)
            num_inliers.append(np.sum(inliers))

            # # 可视化
            # draw_LAF_matches(
            #     KF.laf_from_center_scale_ori(torch.from_numpy(cur_kps).view(1, -1, 2),
            #                                  torch.ones(cur_kps.shape[0]).view(1, -1, 1, 1),
            #                                  torch.ones(cur_kps.shape[0]).view(1, -1, 1)),
            #
            #     KF.laf_from_center_scale_ori(torch.from_numpy(adjacent_kps).view(1, -1, 2),
            #                                  torch.ones(adjacent_kps.shape[0]).view(1, -1, 1, 1),
            #                                  torch.ones(adjacent_kps.shape[0]).view(1, -1, 1)),
            #     torch.arange(cur_kps.shape[0]).view(-1, 1).repeat(1, 2),
            #     img0,
            #     perspective_img1,
            #     inliers,
            #     draw_dict={'inlier_color': (0.2, 1, 0.2),
            #                'tentative_color': (0.8, 0.8, 0),
            #                'feature_color': (0.2, 0.2, 1), 'vertical': False})
            # print(num_inliers)

        # 选择最优的图片索引
        optimize_idx = None

        for i in range(len(num_inliers)):
            if num_inliers[i] > 2000:
                optimize_idx = i

        if optimize_idx is None:
            optimize_idx = np.argmax(num_inliers)

        return np.max(num_inliers), adjacent_image_name[optimize_idx], \
            matching_points_info[cur_image_name][adjacent_image_name[optimize_idx]]

    def generating_matching_info_with_pose(self, cur_image_name, cur_camera_model, adjacent_image_name,
                                             adjacent_camera_model):
        """
        TODO: 利用Loftr生成相邻图片(需要视角转换)的关键点对, 对应内点数
        :return:
        """
        # 读取当前
        img0 = cv.imread(cur_image_name)
        img0 = cv.cvtColor(img0, cv.COLOR_BGR2RGB)
        cur_torch_grayscale_image = self.load_torch_image(img0, cur_image_name, 1440, 1440)
        matching_points_info = {cur_image_name: {}}
        num_inliers = []

        for i in tqdm(range(len(adjacent_image_name))):
            i_name = adjacent_image_name[i]
            img1 = cv.imread(i_name)
            img1 = cv.cvtColor(img1, cv.COLOR_BGR2RGB)
            relative_torch_grayscale_image = self.load_torch_image(img1, i_name, 1440, 1440)
            # 将img1转换视角
            camera1 = adjacent_camera_model[i]

            # 关键点检测
            cur_kps, adjacent_kps = self.get_key_points_with_pose(cur_torch_grayscale_image, cur_camera_model,
                                                                  i_name, camera1)

            # 像素点坐标恢复到原图大小
            cur_kps = cur_kps * self.image_resize_ratio[cur_image_name]
            adjacent_kps = adjacent_kps * self.image_resize_ratio[i_name]
            # 将坐标点进行恢复
            homography_matrix, inliers = cv.findHomography(cur_kps, adjacent_kps, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            inliers_index = np.where(inliers == 1)
            matching_points_info[cur_image_name][i_name] = {"key_points_pair": [cur_kps[inliers_index[0], :],
                                                                                 adjacent_kps[inliers_index[0], :]]}

            # 关键点检测
            cur_kps, adjacent_kps = self.get_key_points_with_pose(relative_torch_grayscale_image, camera1,
                                                                  cur_image_name, cur_camera_model)

            # 像素点坐标恢复到原图大小
            cur_kps = cur_kps * self.image_resize_ratio[cur_image_name]
            adjacent_kps = adjacent_kps * self.image_resize_ratio[i_name]
            # 将坐标点进行恢复
            homography_matrix, inliers = cv.findHomography(cur_kps, adjacent_kps, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            inliers_index = np.where(inliers == 1)
            matching_points_info[i_name] = {cur_image_name: {"key_points_pair": [cur_kps[inliers_index[0], :],
                                                                                adjacent_kps[inliers_index[0], :],
                                                                                ]}}

            num_inliers.append(np.sum(inliers))

        return np.array(num_inliers), adjacent_image_name, matching_points_info

    def get_key_points_with_pose(self, cur_torch_grayscale_image, cur_camera_model,
                                 adjacent_image_name, adjacent_camera_model):
        """
        TODO: 根据位姿信息获取关键点
        :return:
        """
        # 加载图片
        adjacent_image = cv.imread(adjacent_image_name)
        adjacent_image = cv.cvtColor(adjacent_image, cv.COLOR_BGR2RGB)
        transform_matrix = adjacent_camera_model.perspective_transform(cur_camera_model)  # 视角转换矩阵
        perspective_img1 = cv.warpPerspective(adjacent_image, transform_matrix,
                                              (adjacent_image.shape[1], adjacent_image.shape[0]))

        adjacent_torch_grayscale_image = self.load_torch_image(perspective_img1, adjacent_image_name, 1440, 1440)

        # 关键点检测
        adjacent_images_info = {"image0": cur_torch_grayscale_image, "image1": adjacent_torch_grayscale_image}
        cur_kps, adjacent_kps = self.getKeyPoints(adjacent_images_info)

        return cur_kps, adjacent_kps

    def generating_matching_info(self, cur_image_name, adjacent_image_name, is_split_image=0):
        """
        TODO: 利用Loftr生成相邻图片(需要视角转换)的关键点对, 对应内点数
        :return:
        """
        img0 = cv.imread(cur_image_name)
        cur_torch_grayscale_image = self.load_torch_image(img0, cur_image_name)
        matching_points_info = {cur_image_name: {}}

        num_inliers = []
        cover_area = []
        for i_name in tqdm(adjacent_image_name):
            img1 = cv.imread(i_name)
            adjacent_torch_grayscale_image = self.load_torch_image(img1, i_name)
            # 关键点检测
            adjacent_images_info = {"image0": cur_torch_grayscale_image, "image1": adjacent_torch_grayscale_image}

            cur_kps, adjacent_kps = self.getKeyPoints(adjacent_images_info)
            if len(cur_kps) < 40:
                matching_points_info[cur_image_name][i_name] = None
                num_inliers.append(len(cur_kps))
                continue

            homography_matrix, inliers = cv.findHomography(cur_kps * self.image_resize_ratio[cur_image_name],
                                                           adjacent_kps * self.image_resize_ratio[i_name],
                                                           cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)
            homography_matrix_inv, inliers_inv = cv.findHomography(adjacent_kps * self.image_resize_ratio[i_name],
                                                                   cur_kps * self.image_resize_ratio[cur_image_name],
                                                           cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)
            inliers_index = np.where(inliers == 1)
            matching_points_info[cur_image_name][i_name] = {"key_points_pair":
                                                                [cur_kps[inliers_index[0], :] * self.image_resize_ratio[
                                                                    cur_image_name],
                                                                 adjacent_kps[inliers_index[0], :] *
                                                                 self.image_resize_ratio[i_name]],
                                                            'num_inlier_point': np.sum(inliers),
                                                            'homography_matrix': homography_matrix}
            matching_points_info[i_name] = {cur_image_name:
                                            {'homography_matrix': homography_matrix,
                                             "key_points_pair": [adjacent_kps[inliers_index[0], :] *\
                                              self.image_resize_ratio[i_name],
                                              cur_kps[inliers_index[0], :] * self.image_resize_ratio[cur_image_name]]}}

            num_inliers.append(np.sum(inliers))

        return np.array(num_inliers), adjacent_image_name, matching_points_info

    def getKeyPoints(self, images_info):
        """
        TODO: 检测图片的关键点对信息
        :param images_info:
        :return:
        """
        # 生成关键点
        with torch.inference_mode():
            correspondences = self.matcher(images_info)

        mkpts0 = correspondences['keypoints0'].cpu().numpy()
        mkpts1 = correspondences['keypoints1'].cpu().numpy()

        return mkpts0, mkpts1


class LightGlueMatcher:
    """
    @inproceedings{lindenberger2023lightglue,
    author    = {Philipp Lindenberger and Paul-Edouard Sarlin and Marc Pollefeys},
    title     = {{LightGlue: Local Feature Matching at Light Speed}},
    booktitle = {ICCV},
    year      = {2023}
    }
    """

    def __init__(self, h_threshold=2, h_confidence=0.999, h_iternums=10000):
        """
        TODO:
        :param h_threshold:
        :param h_confidence:
        :param h_iternums:
        """
        # RANSAC算法相关参数
        self.h_threshold = h_threshold
        self.h_confidence = h_confidence
        self.h_iternums = h_iternums
        # 初始化Extractor & Matcher
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")  # 'mps', 'cpu'
        self.extractor = SuperPoint(ckpt=r'D:\mgr\GTMap\uav-monitoring-service\model\superpoint_v1.pth', max_num_keypoints=2048).eval().to(self.device)  # load the extractor
        self.matcher = LightGlue(features="superpoint").eval().to(self.device)

    def get_matching_points(self, image0, image1):
        """
        TODO: 获取匹配信息
        """
        # 读取图片
        img0 = cv.imread(image0)
        img0 = cv.cvtColor(img0, cv.COLOR_BGR2RGB)
        matching_points_info = {image0: {}}
        num_inliers = []
        for name in image1:
            img1 = cv.imread(name)
            img1 = cv.cvtColor(img1, cv.COLOR_BGR2RGB)
            # 提取关键点
            kps0, kps1 = self.get_key_points(img0, img1)
            # 生成homography matrix
            homography_matrix, inliers = cv.findFundamentalMat(kps0, kps1, cv.USAC_MAGSAC,
                                                       self.h_threshold, self.h_confidence, self.h_iternums)
            inliers_index = np.where(inliers == 1)

            matching_points_info[image0][name] = {"key_points_pair": [kps0[inliers_index[0], :],
                                                        kps1[inliers_index[0], :]],
                                    'num_inlier_point': np.sum(inliers),
                                    'homography_matrix': homography_matrix}
            # 将坐标点进行恢复
            homography_matrix, inliers = cv.findFundamentalMat(kps1, kps0, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            inliers_index = np.where(inliers == 1)
            matching_points_info[name] = {image0: {"key_points_pair": [kps1[inliers_index[0], :],
                                                                        kps0[inliers_index[0], :],
                                                                                 ]}}
            num_inliers.append(np.sum(inliers))


            num_inliers.append(np.sum(inliers))
        return np.array(num_inliers), image1, matching_points_info

    def get_key_points(self, image0, image1):
        """
        TODO: 获取关键点信息
        """
        # 特征点提取
        if isinstance(image0, np.ndarray):
            image0_tensor = numpy_image_to_torch(image0)
        else:
            image0_tensor = image0

        if isinstance(image1, np.ndarray):
            image1_tensor = numpy_image_to_torch(image1)
        else:
            image1_tensor = image1

        feats0 = self.extractor.extract(image0_tensor.to(self.device))
        feats1 = self.extractor.extract(image1_tensor.to(self.device))
        matches01 = self.matcher({"image0": feats0, "image1": feats1})

        feats0, feats1, matches01 = [
            rbd(x) for x in [feats0, feats1, matches01]
        ]  # remove batch dimension
        # 生成最终结果
        kpts0, kpts1, matches = feats0["keypoints"], feats1["keypoints"], matches01["matches"]
        # print(matches.detach().cpu().numpy().reshape(-1, 2))
        m_kpts0, m_kpts1 = kpts0[matches[..., 0]], kpts1[matches[..., 1]]
        # print(m_kpts0)
        # self.visualize(image0, image1, m_kpts0, m_kpts1, matches01)

        return m_kpts0.cpu().numpy(), m_kpts1.cpu().numpy()

    def get_key_points_with_pose(self, image0, cur_camera_model,
                                 adjacent_image_name, adjacent_camera_model):
        """
        TODO: 根据位姿信息获取关键点
        :return:
        """
        # 加载图片
        adjacent_image = cv.imread(adjacent_image_name)
        adjacent_image = cv.cvtColor(adjacent_image, cv.COLOR_BGR2RGB)
        transform_matrix = adjacent_camera_model.perspective_transform(cur_camera_model)  # 视角转换矩阵
        perspective_img1 = cv.warpPerspective(adjacent_image, transform_matrix,
                                              (adjacent_image.shape[1], adjacent_image.shape[0]))

        # 关键点检测

        cur_kps, adjacent_kps = self.get_key_points(image0, perspective_img1)
        # # 恢复点坐标
        # recovery_matrix = adjacent_camera_model.perspective_recover()
        # recover pose
        adjacent_kps_v = cv.perspectiveTransform(adjacent_kps.reshape(-1, 1, 2).astype(np.float32), np.linalg.inv(transform_matrix)
                                                ).reshape(-1, 2)
        # for p in adjacent_kps_v:
        #     cv.circle(adjacent_image, (int(p[0]), int(p[1])), 10, (0, 0, 255), -1)

        #
        # for p in adjacent_kps:
        #     cv.circle(perspective_img1, (int(p[0]), int(p[1])), 10, (0, 0, 255), -1)



        return cur_kps, adjacent_kps_v

    def generating_matching_info_with_pose(self, cur_image_name, cur_camera_model, adjacent_image_name,
                                           adjacent_camera_model):
        """
        TODO: 利用Loftr生成相邻图片(需要视角转换)的关键点对, 对应内点数
        :return:
        """
        # 读取当前照片
        image0 = load_image(cur_image_name)
        matching_points_info = {cur_image_name: {}}
        num_inliers = []
        for i in tqdm(range(len(adjacent_image_name))):
            i_name = adjacent_image_name[i]
            image1 = load_image(i_name)
            # 将img1转换视角
            camera1 = adjacent_camera_model[i]
            # 关键点检测
            cur_kps, adjacent_kps = self.get_key_points_with_pose(image0, cur_camera_model, i_name, camera1)

            # 将坐标点进行恢复
            homography_matrix, inliers = cv.findFundamentalMat(cur_kps, adjacent_kps, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            inliers_index = np.where(inliers == 1)
            matching_points_info[cur_image_name][i_name] = {"key_points_pair": [cur_kps[inliers_index[0], :],
                                                                                adjacent_kps[inliers_index[0], :]]}

            # 关键点检测
            cur_kps, adjacent_kps = self.get_key_points_with_pose(image1, camera1,
                                                                  cur_image_name, cur_camera_model)

            # 将坐标点进行恢复
            homography_matrix, inliers = cv.findFundamentalMat(cur_kps, adjacent_kps, cv.USAC_MAGSAC,
                                                           self.h_threshold, self.h_confidence, self.h_iternums)

            inliers_index = np.where(inliers == 1)
            matching_points_info[i_name] = {cur_image_name: {"key_points_pair": [cur_kps[inliers_index[0], :],
                                                                                 adjacent_kps[inliers_index[0], :],
                                                                                 ]}}
            num_inliers.append(np.sum(inliers))

        return np.array(num_inliers), adjacent_image_name, matching_points_info

    def visualize(self, image0, image1, m_kpts0, m_kpts1, matches01):
        """
        可视化匹配结果
        """
        axes = viz2d.plot_images([image0, image1])
        viz2d.plot_matches(m_kpts0, m_kpts1, color="lime", lw=0.2)
        viz2d.add_text(0, f'Stop after {matches01["stop"]} layers', fs=20)


if __name__ == '__main__':
    # 文件名1463,[6230, 450]
    files = [r'D:\mgr\uav video\test_video\video1/video_{}.jpg'.format(i) for i in range(301, 601)]
    base_img = cv.imread(r'D:\mgr\uav video\test_video\test_tif.png')
    road_img = cv.imread(r'D:\mgr\uav video\test_video\road_mask.png')
    #
    base_h = np.array([[-1.42346866e+00,  1.85762211e-01,  3.63644744e+03],
                       [-1.71170434e+00,  3.13713757e-01,  4.21595950e+03],
                       [-4.06965969e-04,  5.36530000e-05,  1.00000000e+00]])
    #
    h = [base_h]
    # 初始化lightglue
    detector = LightGlueMatcher(h_threshold=2)
    matching_points_info = detector.get_matching_points(cv.imread(files[0]), cv.imread(files[1]))
    # for i in tqdm(range(301, 303)):
        # if i < 301:
        #     continue
        # elif i == 301:
        #     cur_img = cv.imread(r'D:\mgr\uav video\test_video\video_result\video_{}.jpg'.format(i))
        #     warp_img = cv.warpPerspective(cur_img, base_h, (base_img.shape[1], base_img.shape[0]))
        #     temp_sum = np.sum(warp_img, axis=2)
        #     warp_img[temp_sum == 0] = base_img[temp_sum == 0]
        #     warp_img = cv.add(warp_img, road_img)
        #     cv.imwrite(r'D:\mgr\uav video\test_video/detection_video/bev_video_{}.png'.format(i), warp_img)
        # else:
        #     cur_img = cv.imread(r'D:\mgr\uav video\test_video\video1/video_{}.jpg'.format(i))
        #     cur_img_detection = cv.imread(r'D:\mgr\uav video\test_video\video_result\video_{}.jpg'.format(i))
        #     # 获取匹配信息
        # matching_points_info = detector.get_matching_points(files[i], files[i-1])
            # cur_h = h[-1].dot(matching_points_info['homography_matrix'])
            # h.append(cur_h)
            # # 透视变换
            # warp_img = cv.warpPerspective(cur_img_detection, cur_h, (base_img.shape[1], base_img.shape[0]))
            # temp_sum = np.sum(warp_img, axis=2)
            # warp_img[temp_sum == 0] = base_img[temp_sum == 0]
            # # if i > 100:
            # warp_img = cv.add(warp_img, road_img)

            # cv.imwrite(r'D:\mgr\uav video\test_video/detection_video/bev_video_{}.png'.format(i),
            #            warp_img[3800:3800 + 1024, 3400:3400+1024, :])

    # file1 = r'D:\mgr\uav video\test_video\base1.png'
    # file2 = r'D:\mgr\uav video\test_video\video1\video_301.jpg'
    # # img = cv.imread(file1)
    # # # print(img.shape)
    # # cv.imwrite(r'D:\mgr\uav video\test_video\base4.png', img[3800:3800+256, 3600:3600+256, :])
    # # # file2 = r'D:\mgr\uav video\test_video\video1\video_0.jpg'
    # detector = LightGlueMatcher(h_threshold=2)
    # # # 获取匹配信息
    # matching_points_info = detector.get_matching_info(file2, file1)
    # # # 透视变换
    # cur_img = cv.imread(file2)
    # prev_img = cv.imread(file1)
    # # print(cur_img.shape)
    # points = matching_points_info['key_points_pair']
    # m_kpts0, m_kpts1 = points[0], points[1]
    # m_kpts1 = m_kpts1 + np.array([[3600, 4200]])
    # H, inliers = cv.findHomography(m_kpts0, m_kpts1, cv.USAC_MAGSAC,
    #                                                2, 0.999, 100000)
    # print(H)
    # #
    # warp_img = cv.warpPerspective(cur_img, H, (7760, 7018))
    # temp_sum = np.sum(warp_img, axis=2)
    # t_img = cv.imread(r'D:\mgr\uav video\test_video\test_tif.png')
    # warp_img[temp_sum == 0] = t_img[temp_sum == 0]
    # # # cv.imwrite(r'D:\mgr\uav video\test_video/base.png', img[6230: 6230 + 256, 450: 450 + 256, :])

