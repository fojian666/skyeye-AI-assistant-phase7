# @Time : 2023/8/2 17:54
# @Author : Ma Guorui
# @Description : 📷

import bisect
import os
import matplotlib.pyplot as plt
import matplotlib
import cv2 as cv
import numpy as np
import pickle
import requests
from pyproj import Transformer
from map_module import UAVMap
from camera_module import UAVCameraModel
from pathlib import Path
from multiprocessing import Pool, cpu_count
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import *
work_dir =    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _compute_conf_thresh(data):
    dataset_name = data['dataset_name'][0].lower()
    if dataset_name == 'scannet':
        thr = 5e-4
    elif dataset_name == 'megadepth':
        thr = 1e-4
    else:
        raise ValueError(f'Unknown dataset: {dataset_name}')
    return thr


# --- VISUALIZATION --- #

def make_matching_figure(
        img0, img1, mkpts0, mkpts1,
        kpts0=None, kpts1=None, text=[], dpi=75, path=None):
    # draw image pair
    assert mkpts0.shape[0] == mkpts1.shape[0], f'mkpts0: {mkpts0.shape[0]} v.s. mkpts1: {mkpts1.shape[0]}'
    fig, axes = plt.subplots(1, 2, figsize=(10, 6), dpi=dpi)
    axes[0].imshow(img0, cmap='gray')
    axes[1].imshow(img1, cmap='gray')
    for i in range(2):  # clear all frames
        axes[i].get_yaxis().set_ticks([])
        axes[i].get_xaxis().set_ticks([])
        for spine in axes[i].spines.values():
            spine.set_visible(False)
    plt.tight_layout(pad=1)

    if kpts0 is not None:
        assert kpts1 is not None
        axes[0].scatter(kpts0[:, 0], kpts0[:, 1], c='w', s=2)
        axes[1].scatter(kpts1[:, 0], kpts1[:, 1], c='w', s=2)

    # draw matches
    if mkpts0.shape[0] != 0 and mkpts1.shape[0] != 0:
        fig.canvas.draw()
        transFigure = fig.transFigure.inverted()
        fkpts0 = transFigure.transform(axes[0].transData.transform(mkpts0))
        fkpts1 = transFigure.transform(axes[1].transData.transform(mkpts1))
        fig.lines = [matplotlib.lines.Line2D((fkpts0[i, 0], fkpts1[i, 0]),
                                             (fkpts0[i, 1], fkpts1[i, 1]),
                                             transform=fig.transFigure, linewidth=1)
                     for i in range(len(mkpts0))]

        axes[0].scatter(mkpts0[:, 0], mkpts0[:, 1], s=4)
        axes[1].scatter(mkpts1[:, 0], mkpts1[:, 1], s=4)

    # put txts
    txt_color = 'k' if img0[:100, :200].mean() > 200 else 'w'
    fig.text(
        0.01, 0.99, '\n'.join(text), transform=fig.axes[0].transAxes,
        fontsize=15, va='top', ha='left', color=txt_color)

    # save or return figure
    if path:
        plt.savefig(str(path), bbox_inches='tight', pad_inches=0)
        plt.close()
    else:
        return fig


def _make_evaluation_figure(data, b_id, alpha='dynamic'):
    b_mask = data['m_bids'] == b_id
    conf_thr = _compute_conf_thresh(data)

    img0 = (data['image0'][b_id][0].cpu().numpy() * 255).round().astype(np.int32)
    img1 = (data['image1'][b_id][0].cpu().numpy() * 255).round().astype(np.int32)
    kpts0 = data['mkpts0_f'][b_mask].cpu().numpy()
    kpts1 = data['mkpts1_f'][b_mask].cpu().numpy()

    # for megadepth, we visualize matches on the resized image
    if 'scale0' in data:
        kpts0 = kpts0 / data['scale0'][b_id].cpu().numpy()[[1, 0]]
        kpts1 = kpts1 / data['scale1'][b_id].cpu().numpy()[[1, 0]]

    epi_errs = data['epi_errs'][b_mask].cpu().numpy()
    correct_mask = epi_errs < conf_thr
    precision = np.mean(correct_mask) if len(correct_mask) > 0 else 0
    n_correct = np.sum(correct_mask)
    n_gt_matches = int(data['conf_matrix_gt'][b_id].sum().cpu())
    recall = 0 if n_gt_matches == 0 else n_correct / (n_gt_matches)
    # recall might be larger than 1, since the calculation of conf_matrix_gt
    # uses groundtruth depths and camera poses, but epipolar distance is used here.

    # matching info
    if alpha == 'dynamic':
        alpha = dynamic_alpha(len(correct_mask))
    color = error_colormap(epi_errs, conf_thr, alpha=alpha)

    text = [
        f'#Matches {len(kpts0)}',
        f'Precision({conf_thr:.2e}) ({100 * precision:.1f}%): {n_correct}/{len(kpts0)}',
        f'Recall({conf_thr:.2e}) ({100 * recall:.1f}%): {n_correct}/{n_gt_matches}'
    ]

    # make the figure
    figure = make_matching_figure(img0, img1, kpts0, kpts1,
                                  color, text=text)
    return figure


def _make_confidence_figure(data, b_id):
    # TODO: Implement confidence figure
    raise NotImplementedError()


def make_matching_figures(data, config, mode='evaluation'):
    """ Make matching figures for a batch.

    Args:
        data (Dict): a batch updated by PL_LoFTR.
        config (Dict): matcher configs
    Returns:
        figures (Dict[str, List[plt.figure]]
    """
    assert mode in ['evaluation', 'confidence']  # 'confidence'
    figures = {mode: []}
    for b_id in range(data['image0'].size(0)):
        if mode == 'evaluation':
            fig = _make_evaluation_figure(
                data, b_id,
                alpha=config.TRAINER.PLOT_MATCHES_ALPHA)
        elif mode == 'confidence':
            fig = _make_confidence_figure(data, b_id)
        else:
            raise ValueError(f'Unknown plot mode: {mode}')
        figures[mode].append(fig)
    return figures


def dynamic_alpha(n_matches,
                  milestones=[0, 300, 1000, 2000],
                  alphas=[1.0, 0.8, 0.4, 0.2]):
    if n_matches == 0:
        return 1.0
    ranges = list(zip(alphas, alphas[1:] + [None]))
    loc = bisect.bisect_right(milestones, n_matches) - 1
    _range = ranges[loc]
    if _range[1] is None:
        return _range[0]
    return _range[1] + (milestones[loc + 1] - n_matches) / (
            milestones[loc + 1] - milestones[loc]) * (_range[0] - _range[1])


def cultivate_mask_merge(cultivate_mask_list, color, resize=(22973, 7022), label_list=None):
    """
    TODO: 将耕地mask进行合并, 轉成多進程
    :return:
    """
    from multi_processing_utils import draw_countours_mp
    res_masks = np.zeros((resize[0], resize[1], 3), dtype=np.uint8)
    pool = Pool(int(cpu_count() / 2))  # 多進程進行處理
    # pool = Pool(int(cpu_count()))  # 多進程進行處理
    results = []
    for i in range(len(cultivate_mask_list)):
        mask = cv.resize(cultivate_mask_list[i], (resize[1], resize[0]), cv.INTER_AREA)
        if label_list is None:
            results.append(pool.apply_async(draw_countours_mp, args=(mask, color, label_list)))
        else:
            results.append(pool.apply_async(draw_countours_mp, args=(mask, color, label_list[i])))
    pool.close()
    pool.join()
    for res in results:
        contours, labeled, vertex = res.get()
        # 简化轮廓点
        res_masks = cv.drawContours(res_masks, contours, -1, color, 10)
        # 加上标签
        if labeled is not None:
            for v in vertex:
                res_masks = cv2AddChineseText(res_masks, str(labeled),
                                              (int(v[0][0]) - 20, int(v[0][1]) - 20),
                                              (0, 255, 0), 30)

    res_masks[-1:, :] = [0, 0, 0]
    res_masks[:, :1] = [0, 0, 0]
    res_masks[:, -1:] = [0, 0, 0]
    res_masks[:500, :] = [0, 0, 0]

    plt.imshow(res_masks)

    # # # 对半切开, 连接, 通过膨胀腐蚀将接缝处进行连接
    # dilate_masks = np.column_stack([res_masks[:, int(res_masks.shape[1] / 2):, :],
    #                                 res_masks[:, :res_masks.shape[1] - int(res_masks.shape[1] / 2), :]])
    # # 定义膨胀的结构元素（kernel）
    # kernel = np.ones((2, 2), np.uint8)
    # # 进行膨胀操作
    # dilate_image = cv.dilate(dilate_masks, kernel, iterations=3)
    # dilate_masks = np.column_stack([dilate_image[:, res_masks.shape[1] - int(res_masks.shape[1] / 2):, :],
    #                                 dilate_image[:, :res_masks.shape[1] - int(res_masks.shape[1] / 2), :]])

    return res_masks


def error_colormap(err, thr, alpha=1.0):
    assert alpha <= 1.0 and alpha > 0, f"Invaid alpha value: {alpha}"
    x = 1 - np.clip(err / (thr * 2), 0, 1)
    return np.clip(
        np.stack([2 - x * 2, x * 2, np.zeros]))


def plot_image(img, figsize_in_inches=(5, 5)):
    fig, ax = plt.subplots(figsize=figsize_in_inches)
    ax.imshow(cv.cvtColor(img, cv.COLOR_BGR2RGB))


def filter_opposite_points(origin_point, world_points):
    """
    TODO: 筛选剔除掉反向定位点
    :param origin_point:
    :param world_points:
    :return:
    """
    res_idx = (world_points - origin_point)[:, 1] >= ((world_points[-1] - origin_point).astype(np.float64)[1] - 20)
    res_idx[: int(len(res_idx) * 3 / 4)] = False
    return res_idx


def filter_image_points(cur_polygon, points_df):
    """
    TODO: polygon 对应的points筛选
    :param cur_polygon:
    :param points_df:
    :return:
    """
    # 1. 筛选部分离cur_polygon较近的点
    points_df = points_df[points_df['geometry'].distance(cur_polygon) < 20]
    # 2. within polygon
    points_df = points_df[points_df['geometry'].within(cur_polygon)]
    return points_df.index.to_numpy()


def get_image_paths(image_dir, image_type="JPG"):
    return {str(path).split("\\")[-1][:-4]: str(path) for path in Path(image_dir).glob(f'*.' + image_type)}


def inpaint_sky_regions(image):
    """
    补全天空
    :param image: 图像
    """
    # 将图像转换为灰度图
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

    # 创建一个掩码，标记图像中的黑色区域
    mask = (gray == 0).astype(np.uint8)

    # 使用 inpaint 函数对黑色区域进行插值补全
    inpainted_image = cv.inpaint(image, mask, inpaintRadius=3, flags=cv.INPAINT_TELEA)

    return inpainted_image


def load_infos(name):
    """
    TODO:加载配置信息
    """
    cultivate_polygon_list = []
    with open(r'../data/detection_info/{}.pkl'.format(str(name)), 'rb') as f:
        detection_info = pickle.load(f)
    with open(r'../data/points_info/{}.pkl'.format(str(name)), 'rb') as f:
        points_info = pickle.load(f)
    with open('../data/shp/shp_info.pkl', 'rb') as f:
        cultivate_polygon_list_all = pickle.load(f)
    for idx in points_info.keys():
        cultivate_polygon_list.append(cultivate_polygon_list_all.iloc[idx, -1])
    return cultivate_polygon_list, points_info, detection_info


def object_detection_server(image_paths, cameras, land, uav_map, save_path, serve_address='http://127.0.0.1:9000/object_detection/inference', crop_size=1024):
    """
    TODO: 目标检测服务
    """
    # 存放每张图片对应的目标检测框和对应的类别
    res_alarms = {}
    result_alarms = []
    detect_idx = 0
    for i in range(len(image_paths)):
        image_path = image_paths[i]
        # 读取图片信息
        base_name = os.path.basename(image_path)
        bgr_img = cv.imread(image_path)
        cur_camera = cameras[i]
        if cur_camera is None:
            continue
        # 切割图片
        vertices_coord = crop_image(bgr_img)

        for i in range(vertices_coord.shape[0]):
            crop_img = bgr_img[vertices_coord[i][0]: vertices_coord[i][0] + crop_size,
                               vertices_coord[i][1]: vertices_coord[i][1] + crop_size]
            base_success, base_img_encode = cv.imencode(".png", crop_img)
            images_info = {"image": (base_name, base_img_encode.tostring(), 'image/png')}
            data = {
                "filename": base_name,
                "camera_id": "32040123082409010301010000323251",
                "file_path": image_path}
            headers = {'Connection': 'close'}
            # 返回的结果信息
            res = requests.post(url=serve_address, headers=headers, data=data, files=images_info).json()
            error_code = res['statusCode']   # 错误代码， 0为没有任何东西， 201为有正常返回值， 401为报错
            # print(res)
            if error_code == '200':
                # 对检测出的目标物信息进行处理
                for idx in range(len(res['alarms'])):
                    # 将对应的alarm类别进行存储
                    #
                    position = res['alarms'][idx]['position']
                    polygon = create_rec(np.array([position[0], position[1],
                                                   position[2] - position[0], position[3] - position[1]]))
                    if res['alarms'][idx]['class'] not in ["板房棚房", "起重机"]:
                        continue
                    # crop_img = cv.rectangle(crop_img, (polygon[0][0], polygon[0][1]), (polygon[2][0], polygon[2][1]), (0, 255, 0), 2)
                    # text = res['alarms'][idx]['class']
                    # crop_img = cv2AddChineseText(crop_img, text, (polygon[0][0], polygon[0][1] - 10))

                    # 计算世界点
                    center = (int(position[0] + (position[2] - position[0]) / 2 + vertices_coord[i][1]),
                              int(position[1] + (position[3] - position[1]) / 2 + vertices_coord[i][0]))

                    raster_points = cur_camera.img2world([center])
                    proj_points = uav_map.raster2proj(raster_points)[0]

                    geo_points = uav_map.proj2geo([proj_points[0]], [proj_points[1]])
                    # print(geo_points)
                    # 判断是否在耕地内
                    # print(land)
                    # print(proj_points)
                    # print(len(land[land.geometry.contains(Point(proj_points))]))
                    if len(land[land.geometry.intersects(Point(proj_points).buffer(50))]) == 0:
                        continue
                    print('=====================')
                    cur_position = np.array([position[0], position[1],
                                            position[2] - position[0], position[3] - position[1]]) + np.array([vertices_coord[i][1], vertices_coord[i][0], 0, 0])
                    # 存放检测目标图片
                    # print(center)
                    cur_center = [int((position[2] - position[0]) / 2), int((position[3] - position[1]) / 2)]
                    left_x = cur_center[0] - 256 if cur_center[0] >= 256 else 0
                    left_y = cur_center[1] - 256 if cur_center[1] >= 256 else 0
                    save_img = crop_img[left_x: cur_center[0] + 256, left_y: cur_center[1] + 256]

                    cv.imwrite(os.path.join(save_path, '{}_{}_{}.jpg'.format(vertices_coord[i][0],
                                                                             vertices_coord[i][1],
                                                                             detect_idx)), save_img)
                    result_alarms.append({
                        'class':res['alarms'][idx]['class'],
                        'possibility':res['alarms'][idx]['posibility'],
                        'position':cur_position.tolist(),
                        'location':geo_points.tolist()[0],
                        'result_path':os.path.join(save_path, '{}_{}_{}.jpg'.format(vertices_coord[i][0], vertices_coord[i][1],detect_idx))
                    })
                    if res_alarms.get(res['alarms'][idx]['class']) is None:
                        res_alarms[res['alarms'][idx]['class']] = {image_path: {'polygons': [create_rec(cur_position)],
                                                                                'possibility': [res['alarms'][idx]['posibility']],
                                                                                "coords": [geo_points],
                                                                                'save_path':[os.path.join(save_path, '{}_{}_{}.jpg'.
                                                                                                          format(vertices_coord[i][0], vertices_coord[i][1],detect_idx))]}}
                    else:
                        if res_alarms[res['alarms'][idx]['class']].get(image_path) is None:
                            res_alarms[res['alarms'][idx]['class']][image_path] = {'polygons': [create_rec(cur_position)],
                                                                                   'possibility': [res['alarms'][idx]['posibility']],
                                                                                   "coords": [geo_points],
                                                                                   "save_path":[os.path.join(save_path, '{}_{}_{}.jpg'.
                                                                                                          format(vertices_coord[i][0], vertices_coord[i][1],detect_idx))]}
                        else:
                            res_alarms[res['alarms'][idx]['class']][image_path]['polygons'].append(create_rec(cur_position))
                            res_alarms[res['alarms'][idx]['class']][image_path]['possibility'].append(res['alarms'][idx]['posibility'])
                            res_alarms[res['alarms'][idx]['class']][image_path]['coords'].append(geo_points)
                            res_alarms[res['alarms'][idx]['class']][image_path]['save_path'].append(os.path.join(save_path, '{}_{}_{}.jpg'.
                                                                                                          format(vertices_coord[i][0], vertices_coord[i][1],detect_idx)))
                    detect_idx += 1
    return res_alarms,result_alarms


def cv2AddChineseText(img, text, position, textColor=(0, 255, 0), textSize=30):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv.cvtColor(img, cv.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
        os.path.join(work_dir,"static/font/msyh.ttf"), textSize, encoding="utf-8")
    # 绘制文本
    draw.text(position, text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv.cvtColor(np.asarray(img), cv.COLOR_RGB2BGR)


def create_rec(position):
    """
    TODO:生成举行四个顶点信息
    """
    left_top = position[:2]
    right_top = position[:2] + np.array([position[2], 0])
    right_bottom = position[:2] + position[2:]
    left_bottom = position[:2] + np.array([0, position[3]])

    return np.array([left_top, right_top, right_bottom, left_bottom])


def crop_image(img, crop_size=1024):
    """
    TODO:按照crop_size切割图片， 不做补全
    """
    # 生成切分行列数
    crop_row_nums = img.shape[1] // crop_size + 1
    crop_col_nums = img.shape[0] // crop_size + 1
    # 生成切分的图片顶点
    row_vertices_idx = np.arange(0, crop_row_nums)
    col_vertices_idx = np.arange(0, crop_col_nums)
    crop_vertices_idx = np.column_stack([np.tile(col_vertices_idx, crop_row_nums),
                                          np.repeat(row_vertices_idx, crop_col_nums)])
    crop_vertices_coord = crop_vertices_idx * crop_size
    # 返回顶点信息
    return crop_vertices_coord


def get_angle_with_north(lat0, long0, lat1, long1):
    """
    TODO: 求与地理正北的夹角
    :param lat0: np.array
    :param long0: np.array
    :param lat1: np.array
    :param long1: np.array
    """
    # repeat origin points like target points shape
    lat0 = np.repeat(lat0, len(lat1))
    long0 = np.repeat(long0, len(long1))
    # 构建点坐标
    origin_points = np.column_stack([lat0, long0])
    target_points = np.column_stack([lat1, long1])
    # 将经纬度转换为弧度
    origin_points_rad, target_points_rad = np.radians(origin_points), np.radians(target_points)
    # 计算与正北方向夹角
    delta_long = target_points_rad[:, 1] - origin_points_rad[:, 1]
    y = np.sin(delta_long) * np.cos(target_points_rad[:, 0])
    x = (np.cos(origin_points_rad[:, 0]) * np.sin(target_points_rad[:, 0]) -
         np.sin(origin_points_rad[:, 0]) * np.cos(target_points_rad[:, 0]) * np.cos(delta_long))
    result = np.rad2deg(np.arctan2(y, x))
    return result


def single_img_location(image_file: str, detection_info: dict):
    """
    TODO: 单张图像的定位, 坐标系4326
    detection_info = [{'class':, 'position':, 'prob':,}]
    """
    try:
        # 初始化定位器
        Orthophoto = Aerial2Orthophoto()
        Orthophoto.ReadIMGfile(image_file)   # 不同机型读取方式有些许不同
        Orthophoto.distortionRectifying()
        Orthophoto.CacularConer()
        Orthophoto.Orthophoto2()
        res_info = []
        for i in range(len(detection_info)):
            info = detection_info[i]
            points = np.array([info['position'][0]])
            world_points = Orthophoto.location(points)
            print(world_points)
            transformer = Transformer.from_crs("epsg:{}".format(4549), "epsg:{}".format(4326))    # 平面转经纬度
            lat, lon = transformer.transform(world_points[:, 1], world_points[:, 0])
            info['location'] = [lon[0], lat[0]]
            res_info.append(info)
        return res_info
    except Exception as e:
        print(e)
        for j in range(i, len(detection_info)):
            info = detection_info[i]
            info['location'] = [118.60622, 32.50423]
            res_info.append(info)
        return res_info


def mono_location(file, map_uav, detector, matcher, stitcher, points):
    uav_initializer = DJCameraDeviceInitializer(file, map_uav, detector, matcher, stitcher)
    # 初始化相机信息
    uav_initializer.load_base_info()
    camera_model = UAVCameraModel(uav_initializer.base_info_files, uav_initializer.base_info[0], uav_initializer.kp_detector, 0)
    # 平面坐标系下的拍摄地经纬度坐标pr
    camera_model.proj_x, camera_model.proj_y = uav_initializer.uav_map.geo2proj(camera_model.latitude,
                                                                                camera_model.longitude)[0]
    camera_model.T = [[camera_model.proj_x], [camera_model.proj_y], [camera_model.fly_height]]
    res_points = camera_model.img2world_without_calibration(points)
    # 轉經緯度
    res_world_points = map_uav.proj2geo(res_points[:, 0], res_points[:, 1])
    print(res_world_points)
    return res_world_points


if __name__ == '__main__':
    # base_img = cv.imread(r'C:\Users\Administrator\Desktop\object_detection_origin.png')
    # base_img = cv.resize(base_img, (22987, 6994), interpolation=cv.INTER_LINEAR)
    # print(base_img.shape)
    # img = cv.imread(r'D:\mgr\GTMap\uav-monitoring-service\data\stitching\cultivate_3.png')
    # img = cv.resize(img, (22987, 6994), interpolation=cv.INTER_LINEAR)
    # # 对半切开, 连接, 通过膨胀腐蚀将接缝处进行连接
    # temp_merge_masks = np.column_stack([img[:, 15000:, :], img[:, :15000, :]])
    # # 定义腐蚀的结构元素（kernel）
    # kernel = np.ones((3, 3), np.uint8)
    #
    # # 进行腐蚀操作
    # eroded_image = cv.dilate(temp_merge_masks, kernel, iterations=12)
    # temp_merge_masks = np.column_stack([eroded_image[:, 22987 - 15000:, :], eroded_image[:, :22987 - 15000, :]])
    # # plot_image(temp_merge_masks)
    # res_img = cv.add(temp_merge_masks, base_img)
    # plot_image(res_img)
    # cv.imwrite(r'C:\Users\Administrator\Desktop\detection_cultivate_origin.png', res_img)
    # pass
    # object_detection_server([r'D:\mgr\GTMap\uav-monitoring-service\data\hailin_panorama\DJI_202404081429_016\016_0002\PANO0004.JPG'])
    from configs.device_config import *
    from ai_module import KeyPointsDetector, LightGlueMatcher
    from device_module import DJCameraDeviceInitializer

    path_list = [r'../data\panorama/3/']
    calibration_info = r'../data/calibration_info/3.pkl'
    panorama_info = r'../data/stitching/info/3.pkl'
    map_uav = UAVMap(MAP_PATH, None, LAND_PATCH_INFO)  # map
    detector = KeyPointsDetector(r'D:\mgr\GTMap\uav-monitoring-service\model\model.ckpt')
    matcher = LightGlueMatcher()  # ai

    for path in path_list:
        # try:
        origin_image_info = get_image_paths(path, 'JPG')
        files = np.array([path + file for file in os.listdir(path) if '.JPG' in file])
        mono_location([files[0]], map_uav, detector, matcher, None, [[0, 0]])

