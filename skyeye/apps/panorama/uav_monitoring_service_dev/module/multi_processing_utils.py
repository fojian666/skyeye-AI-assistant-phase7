import matplotlib.pyplot as plt
from camera_module import UAVCameraModel
from shapely.geometry import *
from logger import Logger
import geopandas as gpd
import numpy as np
import cv2 as cv
import os
from stitching_module import AutoPanoramaStitcher
from stitching.cropper import Rectangle
import time


LOGGER = Logger(logname='device_module.log', loglevel=4, logger='DeviceModuleInfo').getlog()


def generate_cultivate_mask_mp(cur_camera_model_base_info, cur_image_name, candidate_col, candidate_row, map_info,
                               h, proj_code, land_patches, image_files, cur_camera_idx):
    """
    TODO: 并行的方式生成每張圖片對應的耕地mask
    """
    res_info = {}
    # 新建一個相機類
    cur_camera_model = UAVCameraModel(image_files, None, None, cur_camera_idx)
    cur_camera_model.load_camera_from_json(cur_camera_model_base_info)
    # 生成真实世界坐标
    candidate_image_points = np.vstack([candidate_col, candidate_row]).T
    if cur_camera_model.pitch > -5:
        # 目前写死了，后期可以做优化
        candidate_image_points = candidate_image_points[candidate_image_points[:, 1] > h / 2]
        world_points = list(cur_camera_model.img2world(candidate_image_points) * np.array([map_info[1], map_info[-1]]) +
                            np.array([map_info[0], map_info[2]]))
    else:
        world_points = list(cur_camera_model.img2world(candidate_image_points) * np.array([map_info[1], map_info[-1]]) +
                            np.array([map_info[0], map_info[2]]))
    # 过滤不同polygon所对应的点
    projection_transform_points_gdf = gpd.GeoDataFrame(
        {"geometry": [Point(p) for p in world_points]}
    )

    projection_transform_points_gdf.crs = "EPSG:{}".format(proj_code)
    try:
        # spatial join using 'within'  method
        cur_polygon_info_df = gpd.sjoin(projection_transform_points_gdf, land_patches, how='left', predicate='within')
        cur_polygon_info_df = cur_polygon_info_df[~cur_polygon_info_df['index_right'].isnull()]
        # 遍历每个符合条件的耕地索引, 给出点索引信息
        points_idx_df = cur_polygon_info_df.groupby('index_right').aggregate(lambda x: x.index.tolist())
        for idx, points_idx in zip(points_idx_df.index, points_idx_df['geometry']):
            # img = cv.imread(cur_image_name)
            # for p in candidate_image_points[points_idx]:
            #     cv.circle(img, (int(p[0]), int(p[1])), 3, (0, 255, 0), -1)
            # plt.imshow(img)
            # plt.show()
            if res_info.get(int(idx)) is None:
                res_info[int(idx)] = {cur_image_name: candidate_image_points[points_idx]}
            else:
                res_info[int(idx)][cur_image_name] = candidate_image_points[points_idx]
        return res_info

    except Exception as e:
        LOGGER.error(str(e))
        LOGGER.error("【Land Patch Pasting】*************图斑绘制失败*************")
        return res_info


def draw_countours_mp(mask, color, labeled=None):
    """
    TODO： 繪畫輪廓函數
    """
    gray_mask = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)
    ret, binary_mask = cv.threshold(gray_mask, 50, 255, 0)

    # 查找轮廓
    contours, hierarchy = cv.findContours(binary_mask.astype(np.uint8), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    # 簡化輪廓
    res_contours = []
    res_contours_vertex = []
    for contour in contours:
        epsilon = 0.005 * cv.arcLength(contour, True)
        approx = cv.approxPolyDP(contour, epsilon, True)
        res_contours.append(approx)
        res_contours_vertex.append(approx[0] - 10)
    return res_contours, labeled, res_contours_vertex


def multi_stitch_mp(stiching_base_info, origin_image_idx, value, imgs, ratio, aspects,
                    warp_low_masks, warp_low_corners, warp_low_sizes, seam_masks_np, lir):
    """
    TODO: 全景拼接multi
    """
    # 新建一個stiching類
    stitcher = AutoPanoramaStitcher(detector="sift", nfeatures=8000)     # stitcher
    # 初始化stitcher
    stitcher.load_json_info(stiching_base_info)
    stitcher.warper.set_scale(stitcher.panorama_cameras)  # set camera scale
    # 按步驟進行貼圖
    # 1. 找到每个掩膜所对应的image index(根据indices再过滤一下)
    mask_idx = [origin_image_idx[os.path.normpath(image_name).split('\\')[-1][:-4]] for image_name in value.keys() if
                origin_image_idx[os.path.normpath(image_name).split('\\')[-1][:-4]] in stitcher.indices]
    # mask_idx = [idx for idx in mask_idx if idx in self.indices]
    # 2. 生成mask
    polygon_imgs = [np.zeros_like(imgs[0]) for i in range(len(stitcher.indices))]
    # 3. resize 对应的像素点坐标(当前分辨率是低分辨率)
    polygon_points = [np.floor(p * ratio).astype(np.int32) for p in value.values()]
    # 4. 给mask标记点信息(这个循环可以避免)
    for i in range(len(stitcher.indices)):
        if stitcher.indices[i] not in mask_idx:
            continue
        cur_idx = mask_idx.index(stitcher.indices[i])
        points_index = (polygon_points[cur_idx][:, 1] < imgs[0].shape[0]) & \
                       (polygon_points[cur_idx][:, 0] < imgs[0].shape[1])

        polygon_imgs[i][polygon_points[cur_idx][points_index, 1], polygon_points[cur_idx][points_index, 0]] = [255, 255, 255]

    # warp imgs
    warp_low_polygon_imgs = list(stitcher.warper.warp_images(polygon_imgs, stitcher.panorama_cameras, aspects[0]))
    # prepare panorama info
    corners = stitcher.cropper.get_zero_center_corners(warp_low_corners)
    rectangles = stitcher.cropper.get_rectangles(corners, warp_low_sizes)
    stitcher.cropper.overlapping_rectangles = stitcher.cropper.get_overlaps(rectangles, Rectangle(*lir))
    stitcher.cropper.intersection_rectangles = stitcher.cropper.get_intersections(
        rectangles, stitcher.cropper.overlapping_rectangles
    )

    #  crop image
    crop_low_polygon_imgs, crop_low_masks, crop_low_corners, crop_low_sizes = stitcher.crop_low_resolution(
        warp_low_polygon_imgs, warp_low_masks, warp_low_corners, warp_low_sizes
    )

    # seam finder replace
    seam_masks = [stitcher.seam_finder.resize(cv.UMat(seam_mask), mask) for seam_mask, mask in zip(seam_masks_np, crop_low_masks)]

    crop_low_masks = stitcher.cropper.crop_images(warp_low_masks)
    crop_low_polygon_imgs = stitcher.cropper.crop_images(warp_low_polygon_imgs)

    stitcher.set_masks(crop_low_masks)

    stitcher.initialize_composition(crop_low_corners, crop_low_sizes)
    stitcher.blend_images(crop_low_polygon_imgs, seam_masks, crop_low_corners)
    polygon_panorama_img = stitcher.create_final_panorama()  # 多边形全景图斑,非黑色部分


    return polygon_panorama_img