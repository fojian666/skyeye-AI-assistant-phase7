# @Time : 2024/10/10 11:35
# @Author : Ma Guorui
# @Description : 📷
import cv2
import os
from tqdm import tqdm
import numpy as np
import math
import shutil
import re
import xmltodict
import matplotlib.pyplot as plt
import math
from PIL import Image
import pyexif
from pyproj import Transformer
import time
import exifread
from osgeo import osr, ogr, gdal
from scipy.spatial.transform import Rotation




# 常见传感器规格及其物理尺寸（单位：毫米）
SENSOR_SIZE_TABLE = {
    '1':        (12.8, 9.6),
    '1/1.2':    (11.0, 8.3),
    '1/1.3':    (9.6, 7.2),
    '1/1.7':    (7.6, 5.7),
    '1/2':      (6.4, 4.8),
    '1/2.3':    (6.17, 4.55),
    '1/2.5':    (5.76, 4.29),
    '1/3':      (4.8, 3.6),
    '1/3.2':    (4.54, 3.42),
    '1/4':      (3.2, 2.4),
}


def extract_frames_by_fps(video_path, output_dir, target_size, frames_per_second=5, frames_per_folder=200):
    """
    每秒抽取指定数量的帧，将每 200 帧存入一个子文件夹，并将每一帧调整为指定大小进行保存。

    :param video_path: 视频文件路径
    :param output_dir: 输出图像文件夹路径
    :param target_size: 目标图像大小 (宽度, 高度)
    :param frames_per_second: 每秒抽取的帧数
    :param frames_per_folder: 每个子文件夹中存储的帧数
    """
    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("无法打开视频文件:", video_path)
        return

    # 获取视频的帧率（FPS）
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"视频帧率: {fps} FPS")

    # 计算帧的间隔：每秒抽取 frames_per_second 帧
    frame_interval = int(fps // frames_per_second)
    print(f"每秒抽取 {frames_per_second} 帧，每隔 {frame_interval} 帧抽取一次")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频总帧数
    print(f"视频总帧数: {frame_count}")

    idx = 0  # 当前帧索引
    saved_frame_idx = 0  # 已保存帧的索引
    folder_count = 1  # 当前文件夹编号

    # 创建第一个子文件夹
    current_folder = os.path.join(output_dir, f'frames_{folder_count}')
    os.makedirs(current_folder, exist_ok=True)

    while True:
        ret, frame = cap.read()

        if not ret:
            break  # 如果读取失败，则退出循环

        # 按照计算出的间隔提取帧
        if idx % frame_interval == 0:
            # 检查是否需要切换文件夹
            if saved_frame_idx > 0 and saved_frame_idx % frames_per_folder == 0:
                folder_count += 1
                current_folder = os.path.join(output_dir, f'frames_{folder_count}')
                os.makedirs(current_folder, exist_ok=True)

            # 调整帧大小
            resized_frame = cv2.resize(frame, target_size)

            # 保存调整后的帧到当前文件夹
            output_path = os.path.join(current_folder, f'{saved_frame_idx:04d}.jpg')  # 格式化帧名
            cv2.imwrite(output_path, resized_frame)
            print(f"成功提取并保存帧 {idx} 为 {output_path}")
            saved_frame_idx += 1

        idx += 1

    # 释放视频捕捉对象
    cap.release()
    print("帧提取完成")


def ensure_empty_dir(directory):
    # 如果目录存在，先删除
    if os.path.exists(directory):
        shutil.rmtree(directory)
    # 重新创建空目录
    os.makedirs(directory)

def crop_image_no_padding(image_path, output_dir, crop_size=(512, 512)):
    """
    按照指定大小裁切图像并保存，舍弃不足裁切大小的部分。

    Args:
        image_path (str): 输入图像路径。
        output_dir (str): 裁切后图像保存目录。
        crop_size (tuple): 裁切图像大小，默认(512, 512)。
    """
    # 创建输出目录
    ensure_empty_dir(output_dir)
    # os.makedirs(output_dir, exist_ok=True)

    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("图像无法加载，请检查路径！")

    img_height, img_width, _ = image.shape
    crop_height, crop_width = crop_size

    # 计算裁切顶点
    start_points = [
        (row, col)
        for row in range(int(img_height / 2), img_height - crop_height + 1, crop_height)
        for col in range(0, img_width - crop_width + 1, crop_width)
    ]

    # 单循环裁切
    for row, col in start_points:
        # 裁切图像
        crop_img = image[row:row + crop_height, col:col + crop_width]

        # 保存裁切后的图像，命名方式为 row_col.jpg
        output_filename = f"{row // crop_height}_{col // crop_width}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        cv2.imwrite(output_path, crop_img)

    print(f"图像裁切完成，结果保存在：{output_dir}")


def list_frames_sorted(directory, file_extension=".png"):
    """
    列出指定目录中按顺序排列的所有帧文件。

    :param directory: 帧文件所在目录
    :param file_extension: 帧文件的扩展名（默认为".png"）
    :return: 按顺序排列的帧文件列表
    """
    # 列出目录中的所有文件
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(file_extension)]
    # 使用sorted()对文件进行排序，确保按数字顺序排列
    # sorted_files = sorted(files, key=lambda x: int(x.split('_')[-1].split('.')[0]))
    sorted_files = sorted(files, key=lambda x: int(x.split('/')[-1].split('.')[0]))

    return sorted_files


def create_video_from_images(image_folder, output_video='./test_sam.mp4', fps=1, img_size=None):
    """
    从指定文件夹中的图片按顺序生成视频。

    :param image_folder: 包含图片的文件夹路径
    :param output_video: 输出视频文件路径
    :param fps: 视频的帧率 (frames per second)
    :param img_size: 图像大小（宽, 高）。若为 None，则采用第一张图片的大小。
    """
    # 获取文件夹中的所有图片文件
    images = list_frames_sorted(image_folder)

    # 读取第一张图片以获取视频尺寸
    first_image_path = images[0]
    first_image = cv2.imread(first_image_path)

    if img_size is None:
        height, width, layers = first_image.shape
        img_size = (width, height)

    # 初始化视频写入对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 指定视频编码格式，使用 mp4v 编码器
    video_writer = cv2.VideoWriter(output_video, fourcc, fps, img_size)

    # 将每一张图片写入视频，插入重复帧
    for image_file in images:
        image = cv2.imread(image_file)

        if image is None:
            print(f"跳过无法读取的文件: {image_file}")
            continue

        # 如果图片大小不匹配，则调整图片大小
        if image.shape[1::-1] != img_size:
            image = cv2.resize(image, img_size)

        # 每张图片插入多帧
        video_writer.write(image)  # 写入当前帧

    # 释放视频写入对象
    video_writer.release()

    print(f"流畅视频生成完成，保存为 {output_video}")


def sparse_frame():
    # 创建输出文件夹（如果不存在）
    if not os.path.exists('../data/base_frame_sparse_h'):
        os.makedirs('../data/base_frame_sparse_h')

    if not os.path.exists('../data/registration_frame_sparse_h'):
        os.makedirs('../data/registration_frame_sparse_h')
    # 获取文件夹中的所有图片文件
    base_images = list_frames_sorted('../data/base_frame_origin')
    registration_images = list_frames_sorted('../data/registration_res')
    for i in tqdm(range(len(base_images)), total=len(base_images)):
        if i % 5 == 0:
            # first_image = cv2.imread(first_image_path)
            base_frame = cv2.imread(base_images[i])
            base_resized_frame = cv2.resize(base_frame, (1920, 1080))

            registration_frame = cv2.imread(registration_images[i])
            registration_resize_frame = cv2.resize(registration_frame, (1920, 1080))

            base_output_path = os.path.join('../data/base_frame_sparse_h', f'frame_{i:04d}.png')  # 格式化帧名
            cv2.imwrite(base_output_path, base_resized_frame)

            registration_output_path = os.path.join('../data/registration_frame_sparse_h', f'frame_{i:04d}.png')  # 格式化帧名
            cv2.imwrite(registration_output_path, registration_resize_frame)

        else:
            continue


def is_rectangle_like(contour, aspect_ratio_threshold=0.3, solidity_threshold=0.9):
    """
    判断轮廓是否接近矩形形状
    :param contour: 轮廓
    :param aspect_ratio_threshold: 长宽比接近矩形的阈值
    :param solidity_threshold: 实心度的阈值
    :return: 是否为接近矩形
    """
    rect = cv2.minAreaRect(contour)
    width, height = rect[1]
    aspect_ratio = min(width, height) / max(width, height)

    # 计算轮廓的面积和凸包面积的比率
    area = cv2.contourArea(contour)
    hull_area = cv2.contourArea(cv2.convexHull(contour))
    solidity = area / hull_area if hull_area > 0 else 0

    return aspect_ratio >= aspect_ratio_threshold and solidity >= solidity_threshold


def process_masks(mask_folder, output_folder, angle_threshold=10):
    """
    处理 mask 文件夹中的所有 mask 图像
    :param mask_folder: mask 文件夹路径
    :param output_folder: 输出图像文件夹路径
    :param angle_threshold: 角度阈值，判断是否接近水平
    """
    os.makedirs(output_folder, exist_ok=True)
    files = list_frames_sorted(mask_folder, '.jpg')
    for filename in files[500:5000]:
        # mask_path = os.path.join(mask_folder, filename)
        mask = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        _, mask = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY)
        # 检测轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # 仅对主要轮廓进行处理
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 100:
                continue
            # 获取最小外接矩形
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)

            # 获取旋转角度
            angle = rect[2]
            if angle < -45:
                angle += 90  # 统一角度范围为 -45 到 +45

            # 如果角度接近水平，则跳过
            if abs(angle) < angle_threshold:
                continue

            # 以矩形中心生成两条边界线
            center = (int(rect[0][0]), int(rect[0][1]))
            offset = 50  # 边界线延伸的距离，可根据需要调整
            if center[0] < 120 or center[0] > 175:
                continue

            if center[1] < 125 or center[1] > 165:
                continue
            # plt.imshow(mask)
            # plt.show()
            # 计算边界线的起点和终点
            dx = int(offset * math.cos(math.radians(angle)))
            dy = int(offset * math.sin(math.radians(angle)))

            bound_line1_strat = (center[0] - dx - 75, 0)
            bound_line1_end = (center[0] + dx - 75, 256)

            bound_line2_strat = (center[0] - dx + 75, 0)
            bound_line2_end = (center[0] + dx + 75, 256)

            # line2_start = (center[0] + dy, center[1] - dx)
            # line2_end = (center[0] - dy, center[1] + dx)

            # 绘制边界线并保存结果
            # color_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            color_mask = np.zeros_like(mask, dtype=np.uint8)
            # cv2.line(color_mask, line2_start, line2_end, (0, 255, 0), 2)
            cv2.line(color_mask, bound_line1_strat, bound_line1_end, 255, 1)
            cv2.line(color_mask, bound_line2_strat, bound_line2_end, 255, 1)
            # plt.imshow(color_mask)
            # plt.show()
            # # 保存处理后的图像
            output_path = os.path.join(output_folder, filename.split('/')[-1])
            cv2.imwrite(output_path, color_mask)
            print(f"处理并保存 {filename} 为 {output_path}")


def generate_mask_video(video_path, mask_folder, frames_per_second=5):
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("无法打开视频文件:", video_path)
        return

    # 获取视频的帧率（FPS）
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"视频帧率: {fps} FPS")

    # 计算帧的间隔：每秒抽取 frames_per_second 帧
    frame_interval = int(fps // frames_per_second)
    print(f"每秒抽取 {frames_per_second} 帧，每隔 {frame_interval} 帧抽取一次")

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 获取视频总帧数
    print(f"视频总帧数: {frame_count}")

    # mask_files = list_frames_sorted(mask_folder, '.jpg')

    idx = 0  # 当前帧索引
    # 创建视频写入对象
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('./output_video.mp4', fourcc, fps, (1920, 1080))

    while True:
        ret, frame = cap.read()
        if not ret:
            break  # 如果读取失败，则退出循环

        # 按照计算出的间隔提取帧
        if idx % frame_interval == 0:
            if not os.path.exists(os.path.join(mask_folder, f'{idx:04d}.jpg')):
                # 将处理后的帧写入新视频
                out.write(frame)
            else:
                # 调整帧大小
                add_mask = cv2.imread(os.path.join(mask_folder, f'{idx:04d}.jpg'), cv2.IMREAD_GRAYSCALE)
                add_mask = cv2.resize(add_mask, (1920, 1080))
                frame[add_mask > 10] = [0, 0, 255]# 将 mask 不为 0 的区域设置为红色
                # plt.imshow(frame)
                # plt.show()
                out.write(frame)
        idx += 1
    # 释放视频捕捉对象
    cap.release()
    # 将处理后的帧写入新视频
    out.release()
    print("帧提取完成")


# === 提取 GPS 数据 ===
def dms_to_dd(s):
    dms = re.findall(r'(\d+)\s+deg\s+(\d+)\'\s+([\d.]+)"\s+([NSEW])', s)
    def convert(deg, min_, sec, hemi):
        dd = int(deg) + int(min_) / 60 + float(sec) / 3600
        dd = round(dd, 6)
        return dd if hemi in ['N', 'E'] else -dd
    return tuple(convert(*part) for part in dms)


# === 加载图像 EXIF 信息 ===
def get_exif_data(image_path):
    img = pyexif.ExifEditor(image_path)
    return img.getDictTags()


def extract_exif_data_from_dict(meta_data):
    """从字典提取 EXIF 数据"""
    # 经纬度
    lat, lon = dms_to_dd(meta_data["GPSPosition"])
    alt = float(meta_data["LRFTargetDistance"])  # AbsoluteAltitude

    gimbal_pitch = float(meta_data["GimbalPitchDegree"])
    gimbal_yaw = float(meta_data["GimbalYawDegree"])

    flight_pitch = float(meta_data["FlightPitchDegree"])
    flight_yaw = float(meta_data["FlightPitchDegree"])
    flight_row = float(meta_data['FlightRollDegree'])
    # print(meta_data)
    # gimbal_yaw = float(meta_data["GimbalYawDegree"])

    fov = float(re.search(r"[-+]?\d*\.\d+|\d+", meta_data["FOV"]).group())
    focal = float(re.search(r"[-+]?\d*\.\d+|\d+", meta_data["FocalLength"]).group())

    # 返回提取的 GPS 和姿态信息
    return {"GpsLatitude": lat,
        "GpsLongitude": lon,
        "AbsoluteAltitude": alt,
        "GimbalPitchDegree": gimbal_pitch,
        "GimbalYawDegree": gimbal_yaw,
        "FlightRollDegree": flight_row,
        "FOV": fov,
        "FocalLength": focal}


def compute_camera_intrinsics(f_mm, sensor, img_width, img_height):
    """
    根据焦距和传感器尺寸计算相机内参矩阵 K。

    参数：
    - f_mm: 焦距（单位 mm）
    - sensor_width: 传感器宽度（单位 mm）
    - sensor_height: 传感器高度（单位 mm）
    - img_width: 图像宽度（单位像素）
    - img_height: 图像高度（单位像素）

    返回：
    - K: 相机内参矩阵 (3x3)
    """
    sensor_width, sensor_height = sensor
    # 每毫米多少像素（像素密度）
    px_per_mm_x = img_width / sensor_width
    px_per_mm_y = img_height / sensor_height

    # 像素坐标系下的焦距
    fx = f_mm * px_per_mm_x
    fy = f_mm * px_per_mm_y

    # 主点一般设为图像中心
    cx = img_width / 2
    cy = img_height / 2

    # 构造内参矩阵
    K = np.array([
        [fx,  0, cx],
        [ 0, fy, cy],
        [ 0,  0,  1]
    ])

    return K


def euler2rot(roll, pitch, yaw):
    return Rotation.from_euler('zxy', [roll, pitch, yaw], degrees=True).as_matrix()


def bev_transform(img, K, relative_R, w, h):
    """
    TODO: 将所有角度图片转换成BEV(纯旋转)
    1. 初始化内参信息(标定后的内参信息, 即self.K不为None)
    2. 恢复位姿(原始坐标系)
    3. 转换位姿(BEV)
    :return:
    """

    # BEV欧拉角, pitch为-90
    bev_rotate = Rotation.from_euler('zxy', [0, -90, 0], degrees=True).as_matrix()
    # 构建转换矩阵
    H = np.dot(K, np.dot(np.linalg.inv(bev_rotate),
                              np.dot(relative_R, np.linalg.inv(K))))
    # BEV转换

    # 图像四个角坐标（齐次坐标）
    corners = np.array([
        [0, 0],
        [w, 0],
        [w, h],
        [0, h]
    ], dtype=np.float32).reshape(-1, 1, 2)

    # 变换四个角
    transformed_corners = cv2.perspectiveTransform(corners, H)

    # 计算新的输出图像尺寸
    [xmin, ymin] = np.floor(transformed_corners.min(axis=0).ravel()).astype(int)
    [xmax, ymax] = np.ceil(transformed_corners.max(axis=0).ravel()).astype(int)

    new_w = xmax - xmin
    new_h = ymax - ymin

    # 添加平移，使输出图像落在正坐标区
    translation = np.array([
        [1, 0, -xmin],
        [0, 1, -ymin],
        [0, 0, 1]
    ], dtype=np.float64)

    H_adjusted = translation @ H

    # 应用warpPerspective
    bev_img = cv2.warpPerspective(img, H_adjusted, (new_w, new_h))

    # # 显示结果
    # plt.imshow(bev_img)
    # plt.title(f"BEV image ({new_w} x {new_h})")
    # plt.axis('off')
    # plt.show()

    return bev_img


def aerial_to_orthophoto(image_path, yaw, pitch, roll,lat, lon, alt, f, output_path, sensor_size):
    # 加载图片
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # image info
    h, w = img.shape[:2]
    # transfer to bev
    K = compute_camera_intrinsics(f, sensor_size, w, h)  # 内参矩阵
    relative_R = euler2rot(roll, pitch, yaw)  #
    bev_img = bev_transform(img, K, relative_R, w, h)

    sensor_width_mm = sensor_size[0]  # width
    img_width = bev_img.shape[1]
    img_height = bev_img.shape[0]

    # 估算经纬度单位的像素间距
    deg_per_pixel_lon, deg_per_pixel_lat = estimate_deg_per_pixel(
        sensor_width_mm, img_width, alt, f, lat
    )

    # 构造仿射变换
    geo_transform = construct_geotransform_wgs84(
        lon, lat, deg_per_pixel_lon, deg_per_pixel_lat, img_width, img_height
    )
    right_top, left_bottom = save_bev_to_tiff(bev_img, output_path, geo_transform)
    return right_top, left_bottom


def estimate_deg_per_pixel(sensor_width_mm, img_width_px, altitude_m, focal_mm, lat):
    """
    估算每像素对应的经度/纬度分辨率（单位: 度）
    """
    # sensor_width_m = sensor_width_mm / 1000.0
    gsd_m_per_pixel = (sensor_width_mm * altitude_m) / (focal_mm * img_width_px)

    # 基于当前纬度估算：经度和纬度方向上每米的度数
    meters_per_deg_lon = 111320 * np.cos(np.deg2rad(lat))
    meters_per_deg_lat = 111320  # 近似为常数也可

    deg_per_pixel_lon = gsd_m_per_pixel / meters_per_deg_lon
    deg_per_pixel_lat = gsd_m_per_pixel / meters_per_deg_lat

    return deg_per_pixel_lon, deg_per_pixel_lat

def construct_geotransform_wgs84(center_lon, center_lat, deg_per_pixel_lon, deg_per_pixel_lat, img_width, img_height):
    """
    构造 GDAL 仿射变换（单位：度/像素）
    """
    origin_x = center_lon - (img_width / 2) * deg_per_pixel_lon
    origin_y = center_lat + (img_height / 2) * deg_per_pixel_lat  # 纬度向下是负

    return (origin_x, deg_per_pixel_lon, 0, origin_y, 0, -deg_per_pixel_lat)


def save_bev_to_tiff(bev_img, out_path, geotransform=None, projection_epsg=4326):
    """
    将 BEV 图像保存为支持透明的 GeoTIFF 格式（黑色变透明）。
    """
    # 统一为 3 通道或 4 通道
    if bev_img.ndim == 2:
        bev_img = np.stack([bev_img] * 3, axis=-1)

    height, width, channels = bev_img.shape

    # 生成 Alpha 通道：如果 RGB 全为 0，设为透明
    alpha = np.where(np.all(bev_img == 0, axis=-1), 0, 255).astype(np.uint8)
    bev_with_alpha = np.dstack([bev_img, alpha])  # 变成 RGBA
    image = Image.fromarray(bev_with_alpha, mode='RGBA')
    image.save(out_path, 'PNG')
    origin_x, pixel_width, _, origin_y, _, pixel_height = geotransform

    right_top = (origin_x + pixel_width * width, origin_y)
    left_bottom = (origin_x, origin_y + pixel_height * height)

    print(f"✅ Saved IMG with transparency to {out_path}")
    return right_top, left_bottom


def tiff_to_png(input_path, output_path):
    # 打开TIFF文件

    tiff_image = Image.open(input_path)
    # 确保图像是RGBA模式（带透明度）
    if tiff_image.mode != 'RGBA':
        tiff_image = tiff_image.convert('RGBA')
    # 将TIFF文件保存为PNG文件
    tiff_image.save(output_path, 'PNG')


def batch_generate_geotiffs(input_path, output_path,sensor_size):
    """
    批量处理 input_folder 中所有 .jpeg 图像，调用 generate_geotiff 并保存到 output_folder。
    每张图的 exif 信息从 exif_dict 中查找。

    参数:
        input_folder: 输入图像文件夹路径
        output_folder: 输出 GeoTIFF 文件夹路径
        exif_dict: {filename: exif_data} 映射，key 不含扩展名
    """
    exif_data = extract_exif_data_from_dict(get_exif_data(input_path))
    print(f"➡️ 正在处理: {input_path}")


    # 你可以稍微改一下 generate_geotiff，使其接收 output_path 参数
    right_top, left_bottom = aerial_to_orthophoto(input_path,exif_data['GimbalYawDegree'],
                                          exif_data['GimbalPitchDegree'], 0,
                                          exif_data['GpsLatitude'],
                                          exif_data['GpsLongitude'],
                                          exif_data['AbsoluteAltitude'],
                                          exif_data['FocalLength'],
                                          output_path,
                                          sensor_size)
    return right_top, left_bottom

if __name__ == '__main__':
    # 示例用法
    # === 示例用法 ===
    st = time.time()
    input_folder = "/home/mgr/gtus/backend/apps/change_detection/【批量压缩】 Remote-Control 2025-05-19 08_32_14 (UTC+08)/新建计划12 2025-05-16 16_27_36 (UTC+08)/Remote-Control"
    output_folder = "/home/mgr/gtus/backend/apps/change_detection/output_tif"

    # print(exif_data)
    batch_generate_geotiffs(input_folder, output_folder)
    print(time.time() - st)

    # image_path = "../data/all_panorama_imgs/19/DJI_20241220132554_0057_D.JPG"  # 输入图像路径
    # output_dir = "../data/panorama_img/crop_2"  # 裁切后图像保存目录
    # crop_image_no_padding(image_path, output_dir)


    # # 使用示例
    # video_file = '../data/9_6.mp4'  # 替换为你的视频文件路径
    # # # output_directory = '../data/base_frame_origin'  # 输出图像文件夹路径
    # output_directory = '../data/origin_9_6_frame'  # 输出图像文件夹路径
    # # target_size = (1920, 1080)  # 目标图像大小（宽度, 高度）
    # target_size = (256, 256)  # 目标图像大小（宽度, 高度）
    # #
    # extract_frames_by_fps(video_file, output_directory, target_size)
    # # create_video_from_images('../data/origin_9_6_frame')
    # # sparse_frame()
    # process_masks('../data/origin_9_6_mask', '../data/origin_9_6_mask_line_frame')
    # generate_mask_video('../data/9_26.mp4', '../data/origin_9_6_mask_line_frame')
