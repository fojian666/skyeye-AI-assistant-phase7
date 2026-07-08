# @Time : 2023/10/23 10:14
# @Author : Ma Guorui
# @Description : 🌏
# coding=UTF-8
import gc
import os
import matplotlib.pyplot as plt
import json
import cv2 as cv
import numpy as np
from stitching import Stitcher
from stitching.images import Images
from stitching.subsetter import Subsetter
from logger import Logger
from tqdm import tqdm
from apps.panorama.uav_monitoring_service_dev.module.common import cultivate_mask_merge
import prettytable as pt
import pickle
import time
from stitching.timelapser import Timelapser
from multiprocessing import Pool, cpu_count
from stitching.warper import Warper
LOGGER = Logger(logname='stitching_module.log', loglevel=4, logger='StitchingModuleInfo').getlog()


class AutoPanoramaStitcher(Stitcher):
    """
    部分参数获取较为冗余
    """
    DEFAULT_SETTINGS = Stitcher.DEFAULT_SETTINGS.copy()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.camera_aspect = None                       # 相机比例, 用于仿射变换
        self.panorama_rectangle_info = None             # crop max rectangle left top point
        self.panorama_warp_sizes = None                 # 全景图片仿射变换后的图片大小信息
        self.panorama_warp_corners = None               # 全景图片仿射变换后的顶点坐标信息（相较于全图而言）
        self.panorama_crop_corners = None               # 全景图片切片的顶点坐标信息（相较于全图而言）
        self.panorama_cameras = None                    # 全景图片对应的相机模型
        self.panorama_blend_color_mask = None           # 全景图片对应的blend color mask信息
        self.panorama_color_map = None                  # 全景图对应的seam mask color info
        self.indices = None                             # 全景图对应的seam mask indices
        self.panorama_size = None                       # 全景图的size信息
        self.panorama_warp_image_size = None            # warp全景图对应的image size信息

    def stitch_final_resolution(self, images, feature_masks=[]):
        """
        TODO: 拼接原始分辨率全景图(相機參數估計部分是否可以直接拿初始化的進行使用？)
        :param images:
        :param feature_masks:
        :return:
        """
        start_time = time.time()
        self.images = Images.of(
            images, self.medium_megapix, self.low_megapix, self.final_megapix
        )
        # print(time.time() - start_time)

        start_time = time.time()
        imgs = self.resize_medium_resolution()
        features = self.find_features(imgs, feature_masks)
        matches = self.match_features(features)
        imgs, features, matches, indices = self.subset(imgs, features, matches)
        cameras = self.estimate_camera_parameters(features, matches)
        cameras = self.refine_camera_parameters(features, matches, cameras)
        cameras = self.perform_wave_correction(cameras)
        self.estimate_scale(cameras)
        # print(time.time() - start_time)

        # 全景图片对应相机信息
        self.panorama_cameras = [cameras[i] for i in range(len(imgs))]
        self.indices = indices

        start_time = time.time()
        imgs = self.resize_low_resolution(imgs)
        warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes = self.warp_low_resolution(imgs, cameras)
        self.prepare_cropper(warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes)
        crop_low_imgs, crop_low_masks, crop_low_corners, crop_low_sizes = self.crop_low_resolution(
            warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes
        )
        # print(time.time() - start_time)

        start_time = time.time()
        self.estimate_exposure_errors(crop_low_corners, crop_low_imgs, crop_low_masks)
        seam_masks = self.find_seam_masks(crop_low_imgs, crop_low_corners, crop_low_masks)
        # print(time.time() - start_time)

        start_time = time.time()

        final_imgs = self.resize_final_resolution()
        warp_imgs, warp_masks, warp_corners, warp_sizes = self.warp_final_resolution(final_imgs, cameras)
        crop_imgs, crop_masks, crop_corners, crop_sizes = self.crop_final_resolution(
            warp_imgs, warp_masks, warp_corners, warp_sizes
        )
        # print(time.time() - start_time)

        start_time = time.time()
        self.set_masks(crop_masks)
        imgs = self.compensate_exposure_errors(crop_corners, crop_imgs)
        final_seam_masks = self.resize_seam_masks(seam_masks)

        self.initialize_composition(crop_corners, crop_sizes)
        self.blend_images(imgs, final_seam_masks, crop_corners)
        panorama_img = self.create_final_panorama()

        self.panorama_size = panorama_img.shape
        self.camera_aspect = self.images.get_ratio(
            Images.Resolution.MEDIUM, Images.Resolution.FINAL
        )
        # print(time.time() - start_time)

        return panorama_img

    def stitch_final_resolution_blend_color_mask(self, images, feature_masks=[]):
        """
        TODO: 拼接生成color mask
        """
        self.images = Images.of(
            images, self.medium_megapix, self.low_megapix, self.final_megapix
        )
        self.warper.set_scale(self.panorama_cameras)  # set camera scale

        # candidate images
        low_imgs = self.resize_low_resolution(self.images)
        final_imgs = self.resize_final_resolution_v2(self.images)

        # color map
        color_map = np.arange(100, len(images) + 100)
        self.panorama_color_map = color_map
        for i in range(len(color_map)):
            final_imgs[i].fill(color_map[i])

        low_imgs = self.subsetter.subset_list(low_imgs, self.indices)
        final_imgs = self.subsetter.subset_list(final_imgs, self.indices)

        # warp for low(list: img, mask) & final
        warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes = self.warp_low_resolution(low_imgs, self.panorama_cameras)
        warp_final_imgs, warp_final_masks, warp_final_corners, warp_final_sizes = self.warp_final_resolution(final_imgs, self.panorama_cameras)
        self.panorama_warp_corners = warp_final_corners

        self.panorama_warp_sizes = warp_final_sizes
        # crop for low(list: img, mask) & final
        self.prepare_cropper(warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes)
        crop_low_imgs, crop_low_masks, crop_low_corners, crop_low_sizes = self.crop_low_resolution(
            warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes
        )

        self.estimate_exposure_errors(crop_low_corners, crop_low_imgs, crop_low_masks)
        seam_masks = self.find_seam_masks(crop_low_imgs, crop_low_corners, crop_low_masks)

        crop_final_imgs, crop_final_masks, crop_final_corners, crop_final_sizes = self.crop_final_resolution(
            warp_final_imgs, warp_final_masks, warp_final_corners, warp_final_sizes
        )

        self.set_masks(crop_final_masks)
        final_seam_masks = self.resize_seam_masks(seam_masks)

        timelapser = Timelapser('as_is', 'fixed_')
        timelapser.initialize(crop_final_corners, crop_final_sizes)
        # seams plotting
        seam_masks_plots = []
        for img, seam_mask in zip(crop_final_imgs, final_seam_masks):
            seam_mask = cv.UMat.get(seam_mask)
            overlaid_img = np.copy(img)
            overlaid_img[seam_mask == 0] = (0, 0, 0)
            seam_masks_plots.append(overlaid_img)

        self.panorama_crop_corners = crop_final_corners

        # fill blend color map
        self.panorama_blend_color_mask = np.zeros(self.panorama_size, dtype=np.uint8)
        for img, corner in zip(seam_masks_plots, crop_final_corners):
            timelapser.process_frame(img, corner)
            frame = timelapser.get_frame()
            self.panorama_blend_color_mask = cv.add(self.panorama_blend_color_mask, frame)

        # 预防 blend color mask 出现没有颜色的情况
        if len(np.unique(self.panorama_blend_color_mask)) < len(np.unique(color_map)):
            LOGGER.error("Blend color mask 生成出错， 请检查")
            raise "Blend color mask 生成出错， 请检查"

    def stitch_crop_rectangle_info(self):
        """
        TODO: 裁剪矩形框信息
        """
        self.warper.set_scale(self.panorama_cameras)  # set camera scale

        # candidate images
        low_imgs = self.resize_low_resolution(self.images)
        final_imgs = self.resize_final_resolution_v2(self.images)

        low_imgs = self.subsetter.subset_list(low_imgs, self.indices)
        final_imgs = self.subsetter.subset_list(final_imgs, self.indices)

        # get final rectangle info
        warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes = self.warp_low_resolution(low_imgs, self.panorama_cameras)
        warp_final_imgs, warp_final_masks, warp_final_corners, warp_final_sizes = self.warp_final_resolution(final_imgs, self.panorama_cameras)
        self.panorama_warp_corners = warp_final_corners
        mask = self.cropper.estimate_panorama_mask(warp_final_imgs, warp_final_masks, warp_final_corners, warp_final_sizes)
        lir = self.cropper.estimate_largest_interior_rectangle(mask)
        self.panorama_rectangle_info = [lir.x, lir.y]

        # get final warp final info
        timelapser = Timelapser('as_is', 'fixed_')
        timelapser.initialize(warp_final_corners, warp_final_sizes)
        for img, corner in zip(warp_final_imgs, warp_final_corners):
            timelapser.process_frame(img, corner)
            frame = timelapser.get_frame()
            self.panorama_warp_image_size = frame.shape

    def stitch_warp_size_info(self):
        """
        TODO: warp 画布大小
        """
        # candidate images
        low_imgs = self.resize_low_resolution(self.images)
        final_imgs = self.resize_final_resolution_v2(self.images)

        low_imgs = self.subsetter.subset_list(low_imgs, self.indices)
        final_imgs = self.subsetter.subset_list(final_imgs, self.indices)

        # get final rectangle info
        warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes = self.warp_low_resolution(low_imgs, self.panorama_cameras)
        warp_final_imgs, warp_final_masks, warp_final_corners, warp_final_sizes = self.warp_final_resolution(final_imgs, self.panorama_cameras)
        self.panorama_warp_corners = warp_final_corners

        # get final warp final info
        timelapser = Timelapser('as_is', 'fixed_')
        timelapser.initialize(warp_final_corners, warp_final_sizes)
        for img, corner in zip(warp_final_imgs, warp_final_corners):
            timelapser.process_frame(img, corner)
            frame = timelapser.get_frame()
            self.panorama_warp_image_size = frame.shape
            break

    def stitch_cultivate_patch(self,
                     origin_image_infos: dict,
                     mask_image_infos: dict,
                     feature_masks=[]):
        """
        TODO: 拼接图斑全景图, final resolution
        :param origin_image_infos:
        :param mask_image_infos:
        :param feature_masks:
        :return:
        """
        from multi_processing_utils import multi_stitch_mp
        # 原始图像信息
        origin_images = [image_dir for image_dir in origin_image_infos.values()]
        origin_image_idx = {img_name: origin_images.index(origin_image_infos[img_name]) for \
                            img_name in origin_image_infos.keys()}
        self.images = Images.of(
            origin_images, self.medium_megapix, self.low_megapix, self.final_megapix
        )
        self.warper.set_scale(self.panorama_cameras)  # set camera scale
        # 原图进行全景變換
        imgs = self.resize_low_resolution(self.images)
        warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes = self.warp_low_resolution(imgs, self.panorama_cameras)
        self.prepare_cropper(warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes)
        panorama_mask = self.cropper.estimate_panorama_mask(warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes)
        lir = self.cropper.estimate_largest_interior_rectangle_v2(panorama_mask)
        crop_low_imgs, crop_low_masks, crop_low_corners, crop_low_sizes = self.crop_low_resolution(
            warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes
        )
        seam_masks_umat = self.find_seam_masks(crop_low_imgs, crop_low_corners, crop_low_masks)
        seam_masks_np = [cv.UMat.get(seam_mask_umat) for seam_mask_umat in seam_masks_umat]
        #
        ratio = self.images.get_ratio(Images.Resolution.FINAL, Images.Resolution.LOW)

        camera_aspect_low = self.images.get_ratio(
            Images.Resolution.MEDIUM, Images.Resolution.LOW
        )

        camera_aspect_final = self.images.get_ratio(
            Images.Resolution.MEDIUM, Images.Resolution.FINAL
        )

        camera_aspect_median = self.images.get_ratio(
            Images.Resolution.MEDIUM, Images.Resolution.MEDIUM
        )
        # json info
        json_info = self.stitching_info_to_json()
        # 图斑贴合拼接
        polygon_list = []
        pool = Pool(int(cpu_count() / 2) + 1)
        # pool = Pool(int(cpu_count()))
        # 存儲結果列表
        results = []
        for polygon_idx, value in tqdm(mask_image_infos.items()):
            res = pool.apply_async(multi_stitch_mp, args=(json_info, origin_image_idx, value, imgs,
                                                          ratio,
                                                          [camera_aspect_low, camera_aspect_median, camera_aspect_final],
                                                          warp_low_masks, warp_low_corners, warp_low_sizes, seam_masks_np, lir))
            results.append(res)
        pool.close()
        pool.join()
        for res in results:
            single_panorama = res.get()
            polygon_list.append(single_panorama)

        panorama = cultivate_mask_merge(polygon_list, (0, 255, 0),  self.panorama_size)
        return panorama

    def stitch_object_patch(self,
                     origin_image_infos: dict,
                     mask_image_infos: dict,
                     feature_masks=[]):
        """
        TODO: 拼接图斑全景图, final resolution
        :param origin_image_infos:
        :param mask_image_infos:
        :param feature_masks:
        :return:
        """
        self.blender.blender_type = 'no'
        # 原始图像信息
        origin_images = [image_dir for image_dir in origin_image_infos.values()]
        origin_image_idx = {img_name: origin_images.index(origin_image_infos[img_name]) for \
                            img_name in origin_image_infos.keys()}
        print(origin_image_idx)
        self.images = Images.of(
            origin_images, self.medium_megapix, self.low_megapix, self.final_megapix
        )
        self.warper.set_scale(self.panorama_cameras)  # set camera scale
        # 原图进行仿射变换
        imgs = self.resize_low_resolution(self.images)
        # 图斑贴合拼接
        detection_list = []
        for category, value in tqdm(mask_image_infos.items()):
            # 1. 找到每个类别所对应的image index(根据indices再过滤一下)
            mask_idx = [origin_image_idx[image_name.split('\\')[-1][:-4]] for image_name in list(value.keys())]
            mask_idx = [idx for idx in mask_idx if idx in self.indices]
            # 2. 生成mask
            polygon_imgs = [np.zeros_like(imgs[0]) for i in range(len(imgs))]
            # 3. resize 对应的像素点坐标(当前分辨率是低分辨率)
            # print(self.images.get_ratio(Images.Resolution.FINAL, Images.Resolution.LOW))
            # print(value.values())

            polygons = [np.floor(np.array(v['polygons']) * np.tile(self.images.get_ratio(Images.Resolution.FINAL, Images.Resolution.LOW),
                        len(v['polygons']) * 8).reshape((len(v['polygons']), 4, 2))).astype(np.int32) for v in value.values()]
            # print(len(polygons))
            # print(len(mask_idx))

            # 4. 给mask标记点信息(这个循环可以避免)
            for idx in mask_idx:
                cur_idx = mask_idx.index(idx)
                # 填充多边形
                cv.fillPoly(polygon_imgs[idx], polygons[cur_idx], (255, 255, 255))

            origin_imgs = [imgs[i] for i in self.indices]
            polygon_imgs = [polygon_imgs[i]for i in self.indices]
            # 5. 全景图拼接
            # 原图的拼接和估计
            warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes = self.warp_low_resolution(origin_imgs, self.panorama_cameras)
            self.prepare_cropper(warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes)
            crop_low_imgs, crop_low_masks, crop_low_corners, crop_low_sizes = self.crop_low_resolution(
                warp_low_imgs, warp_low_masks, warp_low_corners, warp_low_sizes
            )

            # self.estimate_exposure_errors(crop_low_corners, crop_low_polygon_imgs, crop_low_masks)
            seam_masks = self.find_seam_masks(crop_low_imgs, crop_low_corners, crop_low_masks)
            # blended_seam_masks = self.seam_finder.blend_seam_masks(seam_masks, crop_low_corners, crop_low_sizes)
            # plot_image(blended_seam_masks, (5, 5))

            warp_low_polygon_imgs, warp_low_polygon_masks, warp_low_polygon_corners, warp_low_polygon_sizes = self.warp_low_resolution(polygon_imgs, self.panorama_cameras)
            self.prepare_cropper(warp_low_polygon_imgs, warp_low_polygon_masks, warp_low_polygon_corners, warp_low_sizes)
            crop_low_polygon_imgs, crop_low_polygon_masks, crop_low_polygon_corners, crop_low_polygon_sizes = self.crop_low_resolution(
                warp_low_polygon_imgs, warp_low_polygon_masks, warp_low_polygon_corners, warp_low_sizes
            )

            # crop_low_polygon_imgs, crop_low_masks, crop_low_corners, crop_low_sizes = self.crop_low_resolution_v2(
            #     warp_low_polygon_imgs, warp_low_masks, warp_low_corners, warp_low_sizes
            # )
            self.set_masks(crop_low_masks)

            self.initialize_composition(crop_low_corners, crop_low_sizes)
            self.blend_images(crop_low_polygon_imgs, seam_masks, crop_low_corners)
            detection_panorama_img = self.create_final_panorama()  # 多边形全景图斑,非黑色部分


            detection_list.append(detection_panorama_img)
            # plot_image(detection_panorama_img)

        panorama = cultivate_mask_merge(detection_list, (0, 0, 255),
                                        self.panorama_size, list(mask_image_infos.keys()))
        # plot_image(panorama)
        return panorama

    def warp_median_resolution(self, imgs, cameras):
        sizes = self.images.get_scaled_img_sizes(Images.Resolution.FINAL)
        camera_aspect = self.images.get_ratio(
            Images.Resolution.MEDIUM, Images.Resolution.MEDIUM
        )
        return self.warp(imgs, cameras, sizes, camera_aspect)

    def warp_low_resolution_mp(self, imgs, cameras, sizes, camera_aspect):
        imgs, masks, corners, sizes = self.warp(imgs, cameras, sizes, camera_aspect)
        return list(imgs), list(masks), corners, sizes

    def crop_median_resolution(self, imgs, masks, corners, sizes):
        lir_aspect = self.images.get_ratio(
            Images.Resolution.LOW, Images.Resolution.MEDIUM
        )
        return self.crop(imgs, masks, corners, sizes, lir_aspect)

    def crop_low_resolution_v2(self, imgs, masks, corners, sizes):
        imgs, masks, corners, sizes = self.crop(imgs, masks, corners, sizes)
        return imgs, masks, corners, sizes

    def subset(self, imgs, features, matches):
        indices = self.subsetter.subset(self.images.names, features, matches)
        imgs = Subsetter.subset_list(imgs, indices)
        features = Subsetter.subset_list(features, indices)
        matches = Subsetter.subset_matches(matches, indices)
        self.images.subset(indices)
        return imgs, features, matches, indices

    def resize_final_resolution_v2(self, images):
        return list(self.images.resize(Images.Resolution.FINAL, images))

    def resize_medium_resolution_v2(self, images):
        return list(self.images.resize(Images.Resolution.MEDIUM, images))

    def panorama2img(self, panorama_image_points, origin_image_size=(5472, 3648)):
        """
        TODO: 全景图坐标转原始像素点坐标(高分辨率下的转换, 暂不考虑拼接缝的问题)
        """
        # panorama_img = cv.imread(r"D:\mgr\GTMap\uav-monitoring-service\data\stitching\info\1.png")

        point_colors = self.panorama_blend_color_mask[panorama_image_points[:, 0], panorama_image_points[:, 1]]
        point_colors = [color[0] for color in point_colors]

        # 候选摄像机对应像素点坐标 {idx: [p1, p2, p3]}
        candidate_camera_idx = []
        for i in range(len(point_colors)):
            try:
                cur_camera_idx = int(np.where(self.indices == np.where(self.panorama_color_map == point_colors[i])[0])[0])
            except:
                cur_camera_idx = 0

            candidate_camera_idx.append(cur_camera_idx)
        candidate_camera_idx = np.array(candidate_camera_idx)

        # 选出对应的候选相机, 候选crop corner 、 warp corner
        candidate_camera = np.array([self.panorama_cameras[idx] for idx in candidate_camera_idx])
        candidate_warp_corner = np.array([np.array(self.panorama_warp_corners[idx]) for idx in candidate_camera_idx])
        candidate_warp_size = np.array([self.panorama_warp_sizes[idx] for idx in candidate_camera_idx])

        # panorama points to warp panorama points
        panorama_warp_points = panorama_image_points + np.array(self.panorama_rectangle_info)[[1, 0]]

        # warp panorama points to warp image points
        candidate_warp_corner[:, 0] = np.floor(self.panorama_warp_image_size[1] / 2) + candidate_warp_corner[:, 0]

        warp_image_points = panorama_warp_points - candidate_warp_corner[:, [1, 0]]

        # warp image points to origin image points

        camera_focal_list = [camera.focal for camera in self.panorama_cameras]
        warper = cv.PyRotationWarper('spherical', np.median(camera_focal_list) * self.camera_aspect)

        # transform points(目前转坐标的方式有点复杂, 因为opencv 还没有实现warp point backward函数, 不太好直接调用)
        res_image_points = {}
        for idx in candidate_camera_idx:
            # cur_warp_image = cv.imread(r"D:\mgr\GTMap\uav-monitoring-service\data\stitching\warp_{}.png".format(self.indices[idx]))
            cur_panorama_image_points = np.array(panorama_image_points, dtype=np.int32)[candidate_camera_idx == idx][0]
            # cv.circle(panorama_img, (cur_panorama_image_points[1], cur_panorama_image_points[0]), 25, (0, 0, 255), -1)
            # plot_image(panorama_img)

            cur_warp_image_size = candidate_warp_size[candidate_camera_idx == idx][0]
            cur_camera = candidate_camera[candidate_camera_idx == idx][0]
            # construct warp image
            temp_img = np.zeros((cur_warp_image_size[1], cur_warp_image_size[0], 3), dtype=np.uint8)
            # fill colors with warped image points
            cur_warp_image_points = warp_image_points[candidate_camera_idx == idx]
            # cv.circle(cur_warp_image, (int(cur_warp_image_points[0][1]), int(cur_warp_image_points[0][0])), 25, (0, 0, 255), -1)
            # plot_image(cur_warp_image)
            try:
                temp_img[cur_warp_image_points[:, 0], cur_warp_image_points[:, 1]] = [255, 255, 255]
                # cv.circle(temp_img, (cur_warp_image_points[0, 1], cur_warp_image_points[0, 0]), 50, (0, 0, 255), -1)

                warp_backward_image = warper.warpBackward(temp_img,
                                                          Warper.get_K(cur_camera, self.camera_aspect),
                                                          cur_camera.R,
                                                          cv.INTER_LINEAR,
                                                          None,
                                                          origin_image_size)

                # # warp backward image sum
                # plot_image(warp_backward_image)
                warp_backward_image_sum = np.sum(warp_backward_image, axis=2)
                origin_image_points_idx = np.where(warp_backward_image_sum == np.max(warp_backward_image_sum))
                if len(origin_image_points_idx[0]) != 1:
                    LOGGER.error("【Stitching Module】坐标转换出错, 请检查")
                origin_image_points = np.hstack([origin_image_points_idx[0], origin_image_points_idx[1]])
                # origin_image = cv.imread(r"D:\mgr\GTMap\uav-monitoring-service\data\panorama\1\origin\PANO00{}.JPG".
                #                          format("0" +  str((self.indices[idx] + 1)) if (self.indices[idx] + 1) < 10 else self.indices[idx] + 1))
                # cv.circle(origin_image, (int(origin_image_points[1]), int(origin_image_points[0])), 25, (0, 0, 255), -1)
                # plot_image(origin_image)
            except:
                origin_image_points = np.array([[255, 255]])
            if res_image_points.get(idx) is None:
                res_image_points[idx] = [origin_image_points]
            else:
                res_image_points[idx].append(origin_image_points)

        return res_image_points

    def img2panorama(self, image_points: dict, origin_image_size=(5472, 3648)):
        """
        TODO: 像素点转全景坐标
        """
        # warp image points to origin image points
        camera_focal_list = [camera.focal for camera in self.panorama_cameras]
        warper = cv.PyRotationWarper('spherical', np.median(camera_focal_list) * self.camera_aspect)

        origin_image = cv.imread(r"D:\mgr\GTMap\uav-monitoring-service\data\stitching\info\3.png")

        # warp all cameras' image points
        have_calculate_points = {}   # 已经计算过的点坐标
        none_calculate_points = {}   # 还未计算过的点坐标
        for camera_id, points in image_points.items():
            if camera_id not in self.indices:
                none_calculate_points[camera_id] = points
                continue
            cur_camera_idx = np.where(self.indices == camera_id)[0][0]
            cur_camera = self.panorama_cameras[cur_camera_idx]
            warp_points = [warper.warpPoint(point.astype(np.float32),
                                            Warper.get_K(cur_camera, self.camera_aspect), cur_camera.R) for point in points]

            # # print(r'D:\mgr\GTMap\uav-monitoring-service\data\panorama\3\PANO00{}.JPG'.format(camera_id if camera_id >= 10 else "0" + str(camera_id)))
            # img = cv.imread(r'D:\mgr\GTMap\uav-monitoring-service\data\panorama\3\PANO00{}.JPG'.format(camera_id+1 if camera_id+1 >= 10 else "0" + str(camera_id+1)))
            # # _, warped_image = warper.warp(
            # #                     img,
            # #                     Warper.get_K(cur_camera, self.camera_aspect),
            # #                     cur_camera.R,
            # #                     cv.INTER_LINEAR,
            # #                     cv.BORDER_REFLECT,
            # #                 )
            # for p in points:
            #     cv.circle(img, (int(p[0]), int(p[1])), 5, (0, 0, 255), -1)
            # cv.imwrite('./PANO00{}.JPG'.format(camera_id+1 if camera_id+1 >= 10 else "0" + str(camera_id+1)), img)
            # 全景图中的warp坐标
            panorama_warp_points = warp_points + np.array([np.floor(self.panorama_warp_image_size[1] / 2), 0])

            # 裁剪坐标
            panorama_image_points = np.floor(panorama_warp_points - np.array(self.panorama_rectangle_info))
            have_calculate_points[camera_id] = panorama_image_points
            # for p in panorama_image_points:
            #     cv.circle(origin_image, (int(p[0]), int(p[1])), 5, (0, 0, 255), -1)
            # plot_image(origin_image)

        if len(have_calculate_points.keys()) == 0:
            LOGGER.error('【Stitching Module】转换出错请联系管理员')
            print('【Stitching Module】转换出错请联系管理员')

        return have_calculate_points, none_calculate_points

    def final_stitching_info_saving(self, file):
        """
        TODO: 保存高分辨率拼接信息
        """
        tb = pt.PrettyTable(title='Stitching Base Infos')
        tb.field_names = ["Candidate Image Nums", "Panorama Image Size"]
        final_panorama_info = {"panorama_indices": self.indices,
                               "panorama_cameras_median_focal": [camera.focal for camera in self.panorama_cameras],
                               "panorama_cameras_median_aspect": [camera.aspect for camera in self.panorama_cameras],
                               "panorama_cameras_median_ppx": [camera.ppx for camera in self.panorama_cameras],
                               "panorama_cameras_median_ppy": [camera.ppy for camera in self.panorama_cameras],
                               "panorama_cameras_median_R": [camera.R for camera in self.panorama_cameras],
                               "panorama_cameras_median_T": [camera.t for camera in self.panorama_cameras],
                               "panorama_blend_color_mask": self.panorama_blend_color_mask,
                               "panorama_color_map": self.panorama_color_map,
                               "panorama_size": self.panorama_size,
                               "panorama_warp_sizes": self.panorama_warp_sizes,
                               "panorama_warp_corners": self.panorama_warp_corners,
                               "panorama_crop_corners": self.panorama_crop_corners,
                               "panorama_warp_image_size": self.panorama_warp_image_size,
                               "panorama_rectangle_info": self.panorama_rectangle_info,
                               "camera_aspect": self.camera_aspect}
        # print(final_panorama_info)
        tb.add_row(["{}".format(len(self.indices)),
                    "{}".format(self.panorama_size)])
        LOGGER.info(tb)

        with open(file, 'wb') as f:
            pickle.dump(final_panorama_info, f)

    def load_stitching_info(self, file):
        """
        TODO: 加载全景拼接信息
        """
        if not os.path.exists(file):
            assert "原始全景图层未生成， 请完成初始化"
        with open(file, "rb") as f:
            panorama_info = pickle.load(f)

        self.indices = panorama_info["panorama_indices"]
        self.panorama_warp_corners = panorama_info["panorama_warp_corners"]
        self.panorama_crop_corners = panorama_info["panorama_crop_corners"]
        self.panorama_blend_color_mask = panorama_info["panorama_blend_color_mask"]
        self.panorama_color_map = panorama_info["panorama_color_map"]
        self.panorama_warp_sizes = panorama_info["panorama_warp_sizes"]
        self.panorama_warp_image_size = panorama_info["panorama_warp_image_size"]
        self.panorama_size = panorama_info["panorama_size"]
        self.panorama_rectangle_info = panorama_info["panorama_rectangle_info"]
        self.camera_aspect = panorama_info["camera_aspect"]
        self.panorama_cameras = [cv.detail.CameraParams() for i in range(len(list(panorama_info["panorama_cameras_median_focal"])))]
        temp_camera_v = [list(panorama_info["panorama_cameras_median_focal"]),
                         list(panorama_info["panorama_cameras_median_aspect"]),
                         list(panorama_info["panorama_cameras_median_ppx"]),
                         list(panorama_info["panorama_cameras_median_ppy"]),
                         list(panorama_info["panorama_cameras_median_R"]),
                         list(panorama_info["panorama_cameras_median_T"])
                         ]
        for i in range(len(self.panorama_cameras)):
            self.panorama_cameras[i].focal = temp_camera_v[0][i]
            self.panorama_cameras[i].aspect = temp_camera_v[1][i]
            self.panorama_cameras[i].ppx = temp_camera_v[2][i]
            self.panorama_cameras[i].ppy = temp_camera_v[3][i]
            self.panorama_cameras[i].R = temp_camera_v[4][i]
            self.panorama_cameras[i].t = temp_camera_v[5][i]

    def stitching_info_to_json(self):
        """
        TODO:將stitcher的信息轉成json格式
        """
        final_panorama_info = {"panorama_indices": self.indices,
                               "panorama_cameras_median_focal": [camera.focal for camera in self.panorama_cameras],
                               "panorama_cameras_median_aspect": [camera.aspect for camera in self.panorama_cameras],
                               "panorama_cameras_median_ppx": [camera.ppx for camera in self.panorama_cameras],
                               "panorama_cameras_median_ppy": [camera.ppy for camera in self.panorama_cameras],
                               "panorama_cameras_median_R": [camera.R for camera in self.panorama_cameras],
                               "panorama_cameras_median_T": [camera.t for camera in self.panorama_cameras],
                               "panorama_blend_color_mask": self.panorama_blend_color_mask,
                               "panorama_color_map": self.panorama_color_map,
                               "panorama_size": self.panorama_size,
                               "panorama_warp_sizes": self.panorama_warp_sizes,
                               "panorama_warp_corners": self.panorama_warp_corners,
                               "panorama_crop_corners": self.panorama_crop_corners,
                               "panorama_warp_image_size": self.panorama_warp_image_size,
                               "panorama_rectangle_info": self.panorama_rectangle_info,
                               "camera_aspect": self.camera_aspect}
        return final_panorama_info

    def load_json_info(self, panorama_info):
        """
        TODO: 加載json信息
        """

        self.indices = panorama_info["panorama_indices"]
        self.panorama_warp_corners = panorama_info["panorama_warp_corners"]
        self.panorama_crop_corners = panorama_info["panorama_crop_corners"]
        self.panorama_blend_color_mask = panorama_info["panorama_blend_color_mask"]
        self.panorama_color_map = panorama_info["panorama_color_map"]
        self.panorama_warp_sizes = panorama_info["panorama_warp_sizes"]
        self.panorama_warp_image_size = panorama_info["panorama_warp_image_size"]
        self.panorama_size = panorama_info["panorama_size"]
        self.panorama_rectangle_info = panorama_info["panorama_rectangle_info"]
        self.camera_aspect = panorama_info["camera_aspect"]
        self.panorama_cameras = [cv.detail.CameraParams() for i in range(len(list(panorama_info["panorama_cameras_median_focal"])))]
        temp_camera_v = [list(panorama_info["panorama_cameras_median_focal"]),
                         list(panorama_info["panorama_cameras_median_aspect"]),
                         list(panorama_info["panorama_cameras_median_ppx"]),
                         list(panorama_info["panorama_cameras_median_ppy"]),
                         list(panorama_info["panorama_cameras_median_R"]),
                         list(panorama_info["panorama_cameras_median_T"])
                         ]
        for i in range(len(self.panorama_cameras)):
            self.panorama_cameras[i].focal = temp_camera_v[0][i]
            self.panorama_cameras[i].aspect = temp_camera_v[1][i]
            self.panorama_cameras[i].ppx = temp_camera_v[2][i]
            self.panorama_cameras[i].ppy = temp_camera_v[3][i]
            self.panorama_cameras[i].R = temp_camera_v[4][i]
            self.panorama_cameras[i].t = temp_camera_v[5][i]


if __name__ == '__main__':
    # 原始图片:
    origin_image_paths = ["3"]
    stitcher = AutoPanoramaStitcher(detector="sift", nfeatures=8000)
    with open(r'D:\mgr\GTMap\uav-monitoring-service\data\points_info\3.pkl', 'rb') as f:
        cultivated_points_info = pickle.load(f)
    print(cultivated_points_info)
    for origin_path in origin_image_paths:
        # 创建文件夹
        origin_image_info = get_image_paths(r"../data/panorama/{}/".format(origin_path), 'JPG')

        # 获取完整的全景图
        # panorama = stitcher.stitch_final_resolution(list(origin_image_info.values()))  # 拼接全景图
        # stitcher.stitch_final_resolution_blend_color_mask(list(origin_image_info.values()))  # 拼接color map
        # stitcher.stitch_crop_rectangle_info()  # max rectangle info
        # stitcher.stitch_warp_size_info()       # warp size info
        # stitcher.final_stitching_info_saving(r'../data/stitching/info/{}.pkl'.format(origin_path))
        stitcher.load_stitching_info(r'../data/stitching/info/{}.pkl'.format(origin_path))
        panorama = stitcher.stitch_cultivate_patch(origin_image_info, cultivated_points_info)
        cv.imwrite('../data/stitching/cultivate_3.png', panorama)

        #
        # plot_image(cv.imread(r"D:\mgr\GTMap\uav-monitoring-service\data\stitching\warp_1.png"))
        # stitcher.panorama2img(np.array([[3000, 3890],
        #                                 [3000, 3890],
        #                                 [4400, 17910],
        #                                 [6140, 5440],
        #                                 [5440, 6120]]))



