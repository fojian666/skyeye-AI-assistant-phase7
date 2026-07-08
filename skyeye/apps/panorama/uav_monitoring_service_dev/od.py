# @Time : 2023/8/2 17:54
# @Author : Ma Guorui
# @Description : 📷

import bisect
import math
import configparser
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import requests
import cv2 as cv
import os
from PIL import Image, ImageDraw, ImageFont

work_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


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
        config (Dict): matcher config
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


def error_colormap(err, thr, alpha=1.0):
    assert alpha <= 1.0 and alpha > 0, f"Invaid alpha value: {alpha}"
    x = 1 - np.clip(err / (thr * 2), 0, 1)
    return np.clip(
        np.stack([2 - x * 2, x * 2, np.zeros]))


def equirectangular_to_perspective(equirectangular_image, fov, yaw, pitch, output_size):
    height, width = equirectangular_image.shape[:2]
    output_width, output_height = output_size

    # Create an empty output image
    perspective_image = np.zeros((output_height, output_width, 3), dtype=np.uint8)

    # Define the center of the equirectangular image
    center_x = width / 2
    center_y = height / 2

    # Convert FOV from degrees to radians
    fov_rad = math.radians(fov)

    # Calculate the focal length based on the FOV and output image width
    f = (output_width / 2) / math.tan(fov_rad / 2)

    # Convert yaw and pitch from degrees to radians
    yaw = math.radians(yaw)
    pitch = math.radians(pitch)

    # Calculate the normalized coordinates in the rectilinear image
    pixel_x = np.arange(output_width)
    pixel_y = np.arange(output_height)
    all_pixel_x = np.tile(pixel_x, len(pixel_y))
    all_pixel_y = np.repeat(pixel_y, len(pixel_x))

    nx = (all_pixel_x - output_width / 2) / f
    ny = (all_pixel_y - output_height / 2) / f

    # Calculate the 3D direction vector in the camera coordinate system
    dz = np.ones_like(nx)
    dx = nx
    dy = ny

    # Normalize the direction vector
    norm = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
    dx /= norm
    dy /= norm
    dz /= norm

    # Apply the pitch rotation
    d = dy
    dy = d * np.cos(pitch) - dz * np.sin(pitch)
    dz = d * np.sin(pitch) + dz * np.cos(pitch)

    # Apply the yaw rotation
    d = dx
    dx = d * np.cos(yaw) - dz * np.sin(yaw)
    dz = d * np.sin(yaw) + dz * np.cos(yaw)

    # Convert the 3D direction vector to spherical coordinates
    lon = np.arctan2(dx, dz)
    lat = np.arcsin(dy)

    # Map the spherical coordinates to the equirectangular image coordinates
    src_x = ((lon / np.pi + 1) * center_x).astype(np.int32)
    src_y = ((lat / (np.pi / 2) + 1) * center_y).astype(np.int32)
    x_idx = (src_x >= 0) & (src_x < width)
    y_idx = (src_y >= 0) & (src_y < height)
    idx = np.where(x_idx & y_idx == 1)[0]
    perspective_image[all_pixel_y[idx], all_pixel_x[idx], :] = equirectangular_image[src_y[idx], src_x[idx]]

    return perspective_image, [np.column_stack([all_pixel_y[idx], all_pixel_x[idx]]),
                               np.column_stack([src_y[idx], src_x[idx]])]


def crop_image(img, crop_size=1200, scale=0.9):
    """
    TODO:按照crop_size切割图片， 不做补全
    """
    # 生成切分行列数
    crop_row_nums = np.ceil(img.shape[1] / crop_size).astype(np.int32)
    crop_col_nums = np.ceil(img.shape[0] / crop_size).astype(np.int32)

    # 生成切分的图片顶点
    row_vertices_idx = np.arange(0, crop_row_nums)
    col_vertices_idx = np.arange(0, crop_col_nums)
    crop_vertices_idx = np.column_stack([np.tile(col_vertices_idx, crop_row_nums),
                                         np.repeat(row_vertices_idx, crop_col_nums)])
    crop_vertices_coord = crop_vertices_idx * crop_size
    # 返回顶点信息
    return crop_vertices_coord


def panorama_img_detection(panorama_img, detection_service_url, fov=84, output_size=(1500, 1500)):
    yaw = np.arange(0, 360, 80)
    pitch = np.arange(-90, -15, 15)
    pose_list = np.column_stack([np.tile(yaw, len(pitch)), np.repeat(pitch, len(yaw))])
    images_with_different_views = []
    pixel_idx_with_different_views = []
    for pose in pose_list:
        y, p = pose
        perspective_image, pixel_idx = equirectangular_to_perspective(panorama_img, fov, y, p, output_size)
        images_with_different_views.append(perspective_image)
        pixel_idx_with_different_views.append(pixel_idx)

    detection_res = []
    count = 1
    for crop_img, cur_pixel_idx in zip(images_with_different_views, pixel_idx_with_different_views):
        base_success, base_img_encode = cv.imencode(".png", crop_img)
        images_info = {"image": ('views', base_img_encode.tostring(), 'image/png')}
        data = {
            "filename": f'{str(count)}.jpg',
            "camera_id": "32040123082409010301010000323251",
            "file_path": ''}
        headers = {'Connection': 'close'}
        # 返回的结果信息
        res = requests.post(url=detection_service_url, headers=headers, data=data, files=images_info).json()
        error_code = res['statusCode']  # 错误代码， 0为没有任何东西， 201为有正常返回值， 401为报错
        count += 1
        if error_code == '200':
            # 对检测出的目标物信息进行处理
            for alarms_res in res['alarms']:
                position = alarms_res['position']
                # 生成左上左下角点坐标
                vertex = np.array([[position[0], position[1]],
                                   [position[2], position[3]]])
                category = alarms_res['className']
                # 转换当前图片坐标至原始全景图中并生成检测框
                panorama_idx_left_top = (cur_pixel_idx[0][:, 0] == vertex[0][1]) & (
                            cur_pixel_idx[0][:, 1] == vertex[0][0])
                panorama_idx_right_bottom = (cur_pixel_idx[0][:, 0] == vertex[1][1]) & (
                            cur_pixel_idx[0][:, 1] == vertex[1][0])
                panorama_points_left_top = cur_pixel_idx[1][panorama_idx_left_top][0]
                panorama_points_right_bottom = cur_pixel_idx[1][panorama_idx_right_bottom][0]
                detection_res.append({'class_name': category,
                                      'position': [panorama_points_left_top, panorama_points_right_bottom]})

    return detection_res


def panorama_img_detection_v2(panorama_img, detection_service_url,batch_id,image_id, fov=84, output_size=(1200, 1200)):
    # 切割图片
    part_panorama = panorama_img[int(panorama_img.shape[0] / 2):int(panorama_img.shape[0] * 0.8), :, :]
    vertices_coord = crop_image(part_panorama)
    result_alarms = []
    count = 1
    for i in range(vertices_coord.shape[0]):
        crop_img = part_panorama[vertices_coord[i][0]: vertices_coord[i][0] + output_size[0],
                   vertices_coord[i][1]: vertices_coord[i][1] + output_size[1]]
        base_success, base_img_encode = cv.imencode(".png", crop_img)
        #continue
        images_info = {"image": ('test', base_img_encode.tostring(), 'image/png')}
        data = {
            "filename": f'{str(count)}.jpg',
            "camera_id": "32040123082409010301010000323251",
            "batch_id":batch_id,
            "image_id":image_id,
            "file_path": ''}
        headers = {'Connection': 'close'}
        # 返回的结果信息
        res = requests.post(url=detection_service_url, headers=headers, data=data, files=images_info).json()
        error_code = res['statusCode']  # 错误代码， 0为没有任何东西， 201为有正常返回值， 401为报错
        count += 1
        if error_code == '200':
            # 对检测出的目标物信息进行处理
            for alarms in res['alarms']:
                position = alarms['position']
                category = alarms['className']
                cur_position = np.array([position[0], position[1],
                                         position[2], position[3]]) + np.array(
                    [vertices_coord[i][1], vertices_coord[i][0], vertices_coord[i][1], vertices_coord[i][0]]) + \
                               np.array([0, int(panorama_img.shape[0] / 2), 0, int(panorama_img.shape[0] / 2)])

                cv.rectangle(panorama_img, [cur_position[0], cur_position[1]],
                             [cur_position[2], cur_position[3]], [0, 0, 255], thickness=2)
                panorama_img = cv2AddChineseText(panorama_img, str(category),
                                                 (int(cur_position[0]) - 20, int(cur_position[1]) - 20),
                                                 (0, 255, 0), 30)
                alarms['position'] = cur_position
        result_alarms.extend(res['alarms'])
    return panorama_img, result_alarms


def cv2AddChineseText(img, text, position, textColor=(0, 255, 0), textSize=12):
    if (isinstance(img, np.ndarray)):  # 判断是否OpenCV图片类型
        img = Image.fromarray(cv.cvtColor(img, cv.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(os.path.join(work_dir, "static/font/msyh.ttf"), textSize,
                                   encoding="utf-8")
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


def main_v1(equirectangular_image):
    res = panorama_img_detection(equirectangular_image)
    for r in res:
        position = r['position']
        # 绘制矩形
        cv.rectangle(equirectangular_image, [position[0][1], position[0][0]],
                     [position[1][1], position[1][0]], [0, 0, 255], thickness=2)

    return equirectangular_image


def main_v2(equirectangular_image):
    res = panorama_img_detection(equirectangular_image)
    for r in res:
        position = r['position']
        # 绘制矩形
        cv.rectangle(equirectangular_image, [position[0][1], position[0][0]],
                     [position[1][1], position[1][0]], [0, 0, 255], thickness=2)

    return equirectangular_image


if __name__ == '__main__':
    # 读取球面投影的全景图
    equirectangular_image = cv.imread(
        r'E:\supermap_gitlab\gtus\static\temp\0046\DJI_20241220120943_0046_D.JPG')

    detection_service_url = 'http://192.168.60.6:5556/detection_web'
    res_img = panorama_img_detection_v2(equirectangular_image,detection_service_url)
