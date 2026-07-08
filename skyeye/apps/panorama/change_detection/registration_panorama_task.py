# @Time : 2025/2/24 11:12
# @Author : Ma Guorui
# @Description : 📷

import os
import sys
import shutil
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from shapely.geometry import *
from scipy.spatial.distance import cdist
import numpy as np
from PIL import Image
from PIL import ImageDraw
import matplotlib.pyplot as plt
from apps.panorama.common import get_yaw_degree

PROJECT_DIR = os.path.abspath(os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), os.pardir))


def create_and_clean_dir(folder_path):
    # 如果文件夹不存在，创建文件夹
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        # 如果文件夹存在，清空其中的文件
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)


def search_image_info1(engine, pre_batch_id, last_batch_id):
    # 2. 创建 MetaData 对象
    metadata = MetaData()

    # 3. 获取表对象
    clue_table = Table('t_clue', metadata, autoload_with=engine)

    # 4. 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    # 查询数据
    pre_clue = select(clue_table.c.panorama_image_id, clue_table.c.clue_id, clue_table.c.position).where(
        clue_table.c.panorama_image_id == pre_batch_id)
    last_clue = select(clue_table.c.panorama_image_id, clue_table.c.clue_id, clue_table.c.position).where(
        clue_table.c.panorama_image_id == last_batch_id)
    pre_results = session.execute(pre_clue)
    last_results = session.execute(last_clue)
    # 打印结果
    pre_clues = []
    last_clues = []
    for row in pre_results:
        position = row[-1].strip('[]')  # 去掉两边的方括号
        position = list(map(int, position.split()))  # 将空格替换为逗号
        if len(position) == 0:
            continue
        pre_clues.append({int(row[1]): position})

    for row in last_results:
        position = row[-1].strip('[]')  # 去掉两边的方括号
        position = list(map(int, position.split()))  # 将空格替换为逗号
        if len(position) == 0:
            continue
        last_clues.append({int(row[1]): position})
    return pre_clues, last_clues


def find_nearest_and_compute_distance(pre_points, last_points, threshold, image_width, image_height):
    """
    为每个后期目标点找到与其最邻近的前期目标点，并计算它们之间的距离。
    如果距离超过阈值，则返回 True，否则返回 False。
    同时返回所有成功配对的点对索引。

    :param pre_points: 前期目标点 (N x 2 数组)
    :param last_points: 后期目标点 (M x 2 数组)
    :param threshold: 距离阈值
    :param image_width: 图像的宽度
    :param image_height: 图像的高度
    :return: result: 一个与后期目标点数组相同长度的布尔数组，表示每个后期目标点的匹配结果
             matched_pairs: 所有成功配对的 (pre_idx, last_idx) 索引对列表
    """
    # 1. 过滤掉超出图像边界的后期目标点
    valid_mask = (last_points[:, 0] >= 0) & (last_points[:, 0] <= image_width) & \
                 (last_points[:, 1] >= 0) & (last_points[:, 1] <= image_height)
    last_points = last_points[valid_mask]

    # 2. 计算前期目标点与后期目标点的所有距离
    distances = cdist(pre_points, last_points)

    # 3. 创建所有点对组合
    pair_indices = np.array(np.where(distances < threshold)).T  # 得到所有满足距离小于阈值的点对的索引

    # 将索引转换为所需的格式 (i, j, distance)
    pair_indices = [(i, j, distances[i, j]) for i, j in pair_indices]

    # 4. 按照配对的距离排序（从小到大）
    pair_indices.sort(key=lambda x: x[2])

    # 5. 配对过程：选择最小距离的点进行配对
    result = np.ones(len(last_points), dtype=bool)
    matched_pairs = []  # 用于记录成功配对的索引对
    used_pre = set()  # 记录已配对的前期点索引
    used_last = set()  # 记录已配对的后期点索引

    # 6. 遍历所有配对组合，逐一配对
    for pre_idx, last_idx, _ in pair_indices:
        if pre_idx in used_pre or last_idx in used_last:
            continue

        result[last_idx] = False
        matched_pairs.append((pre_idx, last_idx))
        used_pre.add(pre_idx)
        used_last.add(last_idx)

    # 7. 返回最终结果和配对点索引
    return result, matched_pairs


def create_cubemap_faces_fast(equirect_img, face_size, yaw_deg=0):
    h, w = equirect_img.shape[:2]
    faces = ['front', 'back', 'left', 'right', 'top', 'bottom']
    faceLetters = ['f', 'b', 'l', 'r', 'u', 'd']
    output_faces = {}

    grid = np.linspace(0.5 / face_size, 1 - 0.5 / face_size, face_size)
    uu, vv = np.meshgrid(grid, grid)

    yaw_rad = np.deg2rad(float(yaw_deg))
    cos_yaw = np.cos(yaw_rad)
    sin_yaw = np.sin(yaw_rad)

    def get_xyz(face):
        a = 2.0 * uu - 1.0
        b = 1.0 - 2.0 * vv
        if face == 'front':
            x, y, z = a, b, 1
        elif face == 'back':
            x, y, z = -a, b, -1
        elif face == 'left':
            x, y, z = -1, b, a
        elif face == 'right':
            x, y, z = 1, b, -a
        elif face == 'top':
            x, y, z = a, 1, -b
        elif face == 'bottom':
            x, y, z = a, -1, b
        return x, y, z

    def apply_yaw_rotation(x, y, z):
        x_rot = cos_yaw * x - sin_yaw * z
        z_rot = sin_yaw * x + cos_yaw * z
        return x_rot, y, z_rot

    def xyz_to_uv(x, y, z):
        norm = np.sqrt(x ** 2 + y ** 2 + z ** 2)
        theta = np.arctan2(x, z)
        phi = np.arcsin(y / norm)
        u = 0.5 + theta / (2 * np.pi)
        v = 0.5 - phi / np.pi
        return u, v

    for face, fl in zip(faces, faceLetters):
        x3d, y3d, z3d = get_xyz(face)
        x3d, y3d, z3d = apply_yaw_rotation(x3d, y3d, z3d)
        uf, vf = xyz_to_uv(x3d, y3d, z3d)

        px = np.clip((uf * w).astype(np.int32), 0, w - 1)
        py = np.clip((vf * h).astype(np.int32), 0, h - 1)

        face_img = equirect_img[py, px]
        output_faces[fl] = Image.fromarray(face_img)

    return output_faces


def equirect_pixel_to_cubemap_face_pixel(px, py, equirect_width, equirect_height, face_size, yaw_deg=0):
    u = (px + 0.5) / equirect_width
    v = (py + 0.5) / equirect_height

    yaw_rad = np.deg2rad(float(yaw_deg))
    cos_yaw = np.cos(yaw_rad)
    sin_yaw = np.sin(yaw_rad)

    theta = (u - 0.5) * 2 * np.pi
    phi = (0.5 - v) * np.pi

    x = np.sin(theta) * np.cos(phi)
    y = np.sin(phi)
    z = np.cos(theta) * np.cos(phi)

    # 反向旋转 yaw
    x_rot = cos_yaw * x + sin_yaw * z
    z_rot = -sin_yaw * x + cos_yaw * z
    y_rot = y

    abs_x = np.abs(x_rot)
    abs_y = np.abs(y_rot)
    abs_z = np.abs(z_rot)

    if abs_x >= abs_y and abs_x >= abs_z:
        if x_rot > 0:
            face = 'r'
            a = -z_rot / abs_x
            b = y_rot / abs_x
        else:
            face = 'l'
            a = z_rot / abs_x
            b = y_rot / abs_x
    elif abs_y >= abs_x and abs_y >= abs_z:
        if y_rot > 0:
            face = 'u'
            a = x_rot / abs_y
            b = -z_rot / abs_y
        else:
            face = 'd'
            a = x_rot / abs_y
            b = z_rot / abs_y
    else:
        if z_rot > 0:
            face = 'f'
            a = x_rot / abs_z
            b = y_rot / abs_z
        else:
            face = 'b'
            a = -x_rot / abs_z
            b = y_rot / abs_z

    fx = int(np.clip((a + 1) / 2 * face_size, 0, face_size - 1))
    fy = int(np.clip((1 - b) / 2 * face_size, 0, face_size - 1))

    return face, fx, fy


def parse_clues(clues):
    centers = []
    for clue in clues:
        for clue_id, box in clue.items():
            x1, y1, x2, y2 = box
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            centers.append({'id': clue_id, 'center': (cx, cy)})
    return centers


def visualize_mapped_points_on_faces(equirect_img, mapped_points, face_size, yaw_deg, title_prefix=""):
    cube_faces = create_cubemap_faces_fast(equirect_img, face_size, yaw_deg)
    for face_key, face_img in cube_faces.items():
        draw = ImageDraw.Draw(face_img)
        for p in mapped_points:
            if p['face'] == face_key:
                x, y = p['fx'], p['fy']
                draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill='red')
                draw.text((x + 5, y - 5), str(p['id']), fill='yellow')
        plt.figure(figsize=(4, 4))
        plt.imshow(face_img)
        plt.title(f"{title_prefix} Face: {face_key}")
        plt.axis('off')
        plt.show()


def visualize_detected_changes(equirect_img, changes, face_size, yaw_deg):
    cube_faces = create_cubemap_faces_fast(equirect_img, face_size, yaw_deg)
    for face_key, face_img in cube_faces.items():
        draw = ImageDraw.Draw(face_img)
        for chg in changes:
            if chg['face'] == face_key:
                x, y = chg['fx'], chg['fy']
                color = 'lime' if chg['change'] == 'new' else 'blue'
                draw.rectangle((x - 5, y - 5, x + 5, y + 5), outline=color, width=2)
                draw.text((x + 8, y - 8), f"{chg['change']} {chg['id']}", fill=color)
        plt.figure(figsize=(4, 4))
        plt.imshow(face_img)
        plt.title(f"Detected Changes on Face: {face_key}")
        plt.axis('off')
        plt.show()


def map_centers_to_faces(center_list, equirect_img, face_size, yaw_deg):
    h, w = equirect_img.shape[:2]
    mapped = []
    for item in center_list:
        cid = item['id']
        cx, cy = item['center']
        face, fx, fy = equirect_pixel_to_cubemap_face_pixel(cx, cy, w, h, face_size, yaw_deg)
        mapped.append({'id': cid, 'face': face, 'fx': fx, 'fy': fy})
    return mapped


def detect_changes_with_pairing(mapped_prev, mapped_curr, face_size, threshold=10):
    changes = []
    faces = ['f', 'b', 'l', 'r', 'd']

    for face in faces:
        prev_pts = [(p['fx'], p['fy']) for p in mapped_prev if p['face'] == face]
        prev_idx = [p['id'] for p in mapped_prev if p['face'] == face]
        curr_pts = [(c['fx'], c['fy']) for c in mapped_curr if c['face'] == face]
        curr_idx = [p['id'] for p in mapped_curr if p['face'] == face]

        if not prev_pts and not curr_pts:
            continue

        prev_pts_np = np.array(prev_pts) if prev_pts else np.zeros((0, 2))
        curr_pts_np = np.array(curr_pts) if curr_pts else np.zeros((0, 2))

        # 调用你的配对逻辑
        unmatched_mask, matched_pairs = find_nearest_and_compute_distance(
            pre_points=prev_pts_np,
            last_points=curr_pts_np,
            threshold=threshold,
            image_width=face_size,
            image_height=face_size
        )

        # 新增目标（后期中未配对上的）
        for idx, is_unmatched in enumerate(unmatched_mask):
            if is_unmatched:
                changes.append(curr_idx[idx])

        # 消失目标（前期中未配对上的） | 暂时注释
        # matched_prev_idx = set(pre_idx for pre_idx, _ in matched_pairs)
        # for idx in range(len(prev_pts_np)):
        #     if idx not in matched_prev_idx:
        #         changes.append({'change': 0, 'face': face, 'id': prev_idx[idx], 'fx': prev_pts_np[idx][0],
        #                         'fy': prev_pts_np[idx][1]})

    return changes


def get_new_clue_ids(changes):
    new_ids = [chg['id'] for chg in changes if chg['change'] == 1]
    return new_ids if new_ids else []


def panorama_image_registration_by_cube_image(pre_panorama_image_file,
                                              last_panorama_image_file,
                                              cube_size,
                                              pre_clues, last_clues,
                                              exploit: str = 'jpg'):
    """
    全景照片配准流程

    :param pre_panorama_image_file: 前一期照片
    :param last_panorama_image_file: 后一期照片
    :param crop_size: 裁剪大小
    :param pre_clues: 前一期 batch id
    :param last_clues: 后一期 batch id
    :param exploit:
    """
    print("已找线索点", pre_clues, last_clues)
    # 如果前一期没有线索， 直接返回后一期所有线索
    if len(pre_clues) == 0:
        idx_list = np.array([list(point.keys())[0] for point in last_clues]).flatten()
        return idx_list, []
    # 如果后一期没有线索， 直接返回[]
    if len(last_clues) == 0:
        return [], []
    pre_centers = parse_clues(pre_clues)
    last_centers = parse_clues(last_clues)
    # 1.切割6视角(考虑偏北角)
    # load img & load yaw degree
    pre_equirect_img_pil = Image.open(pre_panorama_image_file).convert('RGB')
    pre_equirect_img = np.array(pre_equirect_img_pil)  # shape: (H, W, 3)
    pre_yaw_deg = get_yaw_degree(pre_panorama_image_file)[0]

    last_equirect_img_pil = Image.open(last_panorama_image_file).convert('RGB')
    last_equirect_img = np.array(last_equirect_img_pil)  # shape: (H, W, 3)
    last_yaw_deg = get_yaw_degree(last_panorama_image_file)[0]

    # 2. 映射全景图目标到六视图
    mapped_prev = map_centers_to_faces(pre_centers, pre_equirect_img, cube_size, pre_yaw_deg)
    mapped_last = map_centers_to_faces(last_centers, last_equirect_img, cube_size, last_yaw_deg)

    # 3.进行变化检测
    detected_changes = detect_changes_with_pairing(mapped_prev, mapped_last, cube_size, threshold=10)
    # new_clue_ids = get_new_clue_ids(detected_changes)

    # 2. 可视化已映射的线索点
    # visualize_mapped_points_on_faces(pre_equirect_img, mapped_prev, cube_size, pre_yaw_deg, title_prefix="Pre")
    # visualize_mapped_points_on_faces(last_equirect_img, mapped_last, cube_size, last_yaw_deg, title_prefix="Last")
    # 3. 可视化变化检测结果
    # visualize_detected_changes(last_equirect_img, detected_changes, cube_size, last_yaw_deg)

    return detected_changes


def get_panorama_image_pairs(root_dir):
    image_pairs = []  # 存储 (pre_image_path, last_image_path)

    for folder_name in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        images = [f for f in os.listdir(folder_path) if f.lower().endswith(".jpg")]
        if len(images) < 2:
            continue  # 至少需要两张图才能配对

        pre_image = os.path.join(folder_path, images[0])
        last_image = os.path.join(folder_path, images[-1])

        image_pairs.append((pre_image, last_image))

    return image_pairs


if __name__ == '__main__':
    os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
    # pre_clues, last_clues = search_image_info(engine, '32011300500220250217', '32011300500220250101')
    # last_clue_positions = np.array([list(point.values()) for point in last_clues]).flatten().reshape(-1, 2, 2)
    # last_clue_center_positions = [np.mean(p, axis=0).tolist() for p in last_clue_positions]
    # print(last_clue_center_positions)
    image_pairs = get_panorama_image_pairs('./2人工飞行')

    pre_image_id = '4f33443a23d011f0b4c1d843aebb37eb'
    last_image_id = '4f33443a23d011f0b4c1d843aebb37eb'
    # 获取图片路径， 批次
    for pair in image_pairs[:1]:
        pre_panorama_image_file = pair[0]  # 前一期路径
        last_panorama_image_file = pair[0]  # 后一期路径
        pre_output_dir = "/home/mgr/gtus/static/temp/crop_pre"  # 前一期裁剪临时存放目录
        last_output_dir = "/home/mgr/gtus/static/temp/crop_last"  # 后一期裁剪临时存放目录
        dino_model_path = '/home/mgr/gtus/backend/apps/change_detection/dinov2_large'
        cube_size = 1024
        pre_clues = [{2982: [2715, 2961, 2772, 3007]}, {2983: [2539, 2641, 2568, 2665]},
                     {2984: [4077, 2302, 4098, 2320]}, {2985: [4268, 2240, 4315, 2279]},
                     {2986: [4097, 3248, 4143, 3276]}, {2987: [4801, 2846, 4948, 2936]},
                     {2988: [6166, 3098, 6291, 3169]}]
        last_clues = [{2982: [2715, 2961, 2772, 3007]}, {2983: [2539, 2641, 2568, 2665]},
                      {3000: [2000, 2302, 2000, 2320]}, {2985: [4268, 2240, 4315, 2279]},
                      {2986: [4097, 3248, 4143, 3276]}, {2987: [4801, 2846, 4948, 2936]},
                      {2988: [6166, 3098, 6291, 3169]}]

        # panorama_image_processing_workflow(pre_panorama_image_file,
        #                                    last_panorama_image_file,crop_size,
        #                                    pre_output_dir,
        #                                    last_output_dir,pre_image_id,
        #                                    last_image_id,dino_model_path)
        panorama_image_registration_by_cube_image(pre_panorama_image_file,
                                                  last_panorama_image_file,
                                                  cube_size,
                                                  pre_clues, last_clues)
