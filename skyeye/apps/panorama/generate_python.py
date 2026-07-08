# @Time : 2025/7/8 14:31
# @Author : Ma Guorui
# @Description : 📷
import os
import math
import shutil
import json
import cv2
import numpy as np
from PIL import Image
from .common import get_yaw_degree

# 立方体六面标签顺序：前、后、上、下、左、右
faceLetters = ['f', 'b', 'u', 'd', 'l', 'r']
CUBE_FACES = ['front', 'back', 'top', 'bottom', 'left', 'right']
ANTIALIAS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS

def create_cubemap_faces_fast(equirect_img, face_size, yaw_deg=0):
    h, w = equirect_img.shape[:2]
    faces = ['front', 'back', 'left', 'right', 'top', 'bottom']
    faceLetters = ['f', 'b', 'l', 'r', 'u', 'd']
    output_faces = {}

    # 网格 (u, v)
    grid = np.linspace(0.5 / face_size, 1 - 0.5 / face_size, face_size)
    uu, vv = np.meshgrid(grid, grid)  # shape: (face_size, face_size)

    # yaw angle in radians (positive: turn right)
    yaw_rad = np.deg2rad(float(yaw_deg))
    cos_yaw = np.cos(yaw_rad)
    sin_yaw = np.sin(yaw_rad)

    def get_xyz(face):
        a = 2.0 * uu - 1.0
        b = 1.0 - 2.0 * vv  # 注意翻转 v
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
        # 绕 y 轴旋转 yaw
        x_rot = cos_yaw * x - sin_yaw * z
        z_rot = sin_yaw * x + cos_yaw * z
        return x_rot, y, z_rot

    def xyz_to_uv(x, y, z):
        norm = np.sqrt(x**2 + y**2 + z**2)
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


def tile_and_save(face_images, output_path, cubeSize, tileSize, levels, extension=".png"):
    """将六面图像切 tile 并保存"""
    for idx, letter in enumerate(faceLetters):
        face = face_images[letter]
        size = cubeSize
        for level in range(levels, 0, -1):
            level_dir = os.path.join(output_path, str(level))
            os.makedirs(level_dir, exist_ok=True)
            tiles = math.ceil(size / tileSize)
            if level < levels:
                face = face.resize([size, size], ANTIALIAS)
            for i in range(tiles):
                for j in range(tiles):
                    tile = face.crop([j * tileSize, i * tileSize,
                                      min((j + 1) * tileSize, size),
                                      min((i + 1) * tileSize, size)])
                    tile.save(os.path.join(level_dir, f"{letter}{i}_{j}{extension}"))
            size = size // 2


def generate_fallback(face_images, output_path, extension=".png"):
    fallback_dir = os.path.join(output_path, 'fallback')
    os.makedirs(fallback_dir, exist_ok=True)
    for letter in faceLetters:
        face = face_images[letter].resize((1024, 1024), ANTIALIAS)
        face.save(os.path.join(fallback_dir, f"{letter}{extension}"))


def generate_config(output_path, haov, vaov, tileSize, levels, cubeSize, extension=".png"):
    config = {
        "hfov": 100.0,
        "autoLoad": True,
        "type": "multires",
        "multiRes": {
            "path": "/%l/%s%y_%x",
            "fallbackPath": "/fallback/%s",
            "extension": extension[1:],
            "tileResolution": tileSize,
            "maxLevel": levels,
            "cubeResolution": cubeSize
        }
    }
    with open(os.path.join(output_path, "config.json"), "w") as f:
        json.dump(config, f, indent=4)


def start_cut_image(input_path, output_path, yaw_degree):
    print(input_path, output_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path, exist_ok=True)

    origWidth, origHeight = Image.open(input_path).size
    haov = 360.0
    vaov = 180.0

    # cube 分辨率推算
    cubeSize = 8 * math.ceil((360 / haov) * origWidth / math.pi / 8)
    # print(origWidth, origHeight)
    # print(cubeSize)
    tileSize = min(512, cubeSize)

    levels = int(math.ceil(math.log(float(cubeSize) / tileSize, 2))) + 1
    if int(cubeSize / 2 ** (levels - 2)) == tileSize:
        levels -= 1

    print("Converting equirectangular to cubemap faces...")
    #image_yaw = get_yaw_degree(input_path)[0]
    equirect_img = cv2.imdecode(np.fromfile(input_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    equirect_img = cv2.cvtColor(equirect_img, cv2.COLOR_BGR2RGB)
    # print(equirect_img.shape)
    face_images = create_cubemap_faces_fast(equirect_img, cubeSize)

    print("Tiling and saving...")
    tile_and_save(face_images, output_path, cubeSize, tileSize, levels)

    print("Generating fallback tiles...")
    generate_fallback(face_images, output_path)

    print("Generating config...")
    generate_config(output_path, haov, vaov, tileSize, levels, cubeSize)

    print("Done! Output saved to:", output_path)


if __name__ ==  '__main__':
    input_path = r'./change_detection/nj/DJI_20250605171550_0007_V.JPG'
    output_path = r'./output'
    start_cut_image(input_path, output_path,1)

