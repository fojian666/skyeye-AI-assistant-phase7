# @Time : 2023/11/1 10:39
# @Author : chen zhenying
# @Description : 🌏
# coding=UTF-8

import os
import cv2 as cv
import numpy as np
from apps.uav_monitoring_service_dev.configs.stitching_config import *
import requests, re
from PIL import Image
import shutil
from ai_module import KeyPointsDetector
import os



color = {
    '彩钢瓦': [187, 255, 255],
    '挖掘机': [127, 255, 212],
    '板房棚房': [255, 106, 106],
    '运输车': [84, 255, 159],
    '翻斗车': [176, 226, 255],
    '堆土': [224, 255, 255],
    '水泥管': [191, 239, 255],
    '工程管': [144, 238, 144],
    '防尘网': [24, 24, 24],
    '火焰': [20, 189, 255],
    '打桩机': [59, 98, 200],
    '推土车': [67, 28, 129],
    '钢筋': [12, 98, 200],
    '搅拌车': [77, 29, 211],
}

def object_detection(PATH):
    url = 'http://192.168.60.52:9000/object_detection/inference'
    img = os.listdir(PATH)
    img_files = [PATH + file for file in img if ".JPG" in file]
    img_files_origin = [PATH + file for file in img if ".JPG" in file]
    for file, file_origin in zip(img_files, img_files_origin):
        img = cv.imread(file)
        img_origin = cv.imread(file_origin)
        with open(file, 'rb') as f:
            name = os.path.basename(f.name)
            files = {'image': f}
            data = {
                "filename": name,
                "camera_id": "32040123082409010301010000323251",
                "file_path": file}
            headers = {'Connection': 'close'}
            res = requests.post(url=url, headers=headers, data=data, files=files).json()
            if 'alarms' in res.keys():
                count = res['count']
                for i in range(count):
                    posibility = res['alarms'][i]['posibility']
                    if posibility > 0:
                        row, col, row_len, col_len = res['alarms'][i]['position']
                        clas = res['alarms'][i]['class']
                        if img[row-1, col-1,:].max()==0 or img[row + row_len-1, col-1,:].max()==0 or img[row + row_len-1, col + col_len-1,:].max()==0 or img[row-1, col + col_len-1,:].max()==0:
                            continue
                        if row_len > 700:
                            continue
                        rectangle = np.array([[row-1, col-1], [row + row_len-1, col-1], [row + row_len-1, col + col_len-1], [row-1, col + col_len-1]])
                        rectangle = rectangle.reshape((-1, 1, 2))
                        # cv.polylines(img, [rectangle], True, (200, 255, 187), 5)
                        cv.polylines(img_origin, [rectangle], True, [0,255,255], 8)
                        # cv.imwrite(path + file.split('/')[-1], img)
                        cv.imwrite(PATH + file_origin.split('/')[-1], img_origin)

def merge(path, size):
    """
    图像合并成原图像
    :param path: 裁剪后的图像路径
    :param size: 原图像的尺寸（h，w）
    :return: 写入文件
    """
    h, w = size
    img = os.listdir(path)
    imgs = [path + file for file in img if '.png' in file]
    name = imgs[0].split('/')[-1].split('_')[0]
    result = Image.new('RGB', (w,h))
    r = int(h / 1024)
    c = int(w / 1024)
    for row in range(r+1):
        for col in range(c+1):
            image = Image.open(imgs[(c+1)*row+col])
            result.paste(image, box=(1024*col, 1024*row))
    path = path.replace('clip/'+name, 'merge')
    if not os.path.exists(path):
        os.makedirs(path)
    result.save(path + name + '.png')

def clip(PATH, image_type='JPG'):
    """
    图像裁剪
    :param PATH: 待裁剪的图像路径（可以多个图像）
    :param image_type: 图像格式
    :return: 返回图像的高度，宽度
    """
    img = os.listdir(PATH)
    img_files = [PATH + file for file in img if ('.'+image_type) in file]
    for file in img_files:
        img = cv.imread(file)
        h, w, c = img.shape
        arr = [k*1024 for k in range(20)]
        row = int(h/1024)
        col = int(w/1024)
        mask = np.zeros([(row+1)*1024, (col+1)*1024, 3],dtype='uint8')
        mask[0:h,0:w,:] = img[0:h,0:w,:]
        cropped = []
        for i in range(row+1):
            for j in range(col+1):
                crop = mask[arr[i]:arr[i+1], arr[j]:arr[j+1],:]
                cropped.append(crop)
        path = PATH + 'clip/'+file.split('/')[-1].split('.')[0]
        if not os.path.exists(path):
            os.makedirs(path)
        for k in range(len(cropped)):
            cv.imwrite(path+'/'+ file.split('/')[-1].split('.')[0]+'_'+str(k).rjust(3,'0')+'.'+image_type, np.array(cropped[k]))
    return h,w

def clip_panorama(image,image_type='JPG'):
    """
    全景图裁剪1024*1024
    :param image: 要裁剪的全景图
    :param image_type: 全景图的格式
    :return: 全景图的高度和宽度
    """
    img = cv.imread(image)
    h, w, c = img.shape
    arr = [k * 1024 for k in range(30)]
    row = int(h / 1024)
    col = int(w / 1024)
    mask = np.zeros([(row + 1) * 1024, (col + 1) * 1024, 3], dtype='uint8')
    mask[0:h, 0:w, :] = img[0:h, 0:w, :]
    cropped = []
    for i in range(row + 1):
        for j in range(col + 1):
            crop = mask[arr[i]:arr[i + 1], arr[j]:arr[j + 1], :]
            cropped.append(crop)
    # path = '../data/IMAGE/taizhou/detection/clip/' + image.split('/')[-1].split('.')[0]
    # if not os.path.exists(path):
    #     os.makedirs(path)
    # for k in range(len(cropped)):
    #     cv.imwrite(path + '/' + image.split('/')[-1].split('.')[0] + '_' + str(k).rjust(3, '0') + '.'+image_type,
    #                np.array(cropped[k]))
    return h, w, cropped

def overlayer(path_detection,path_farmland,color_farmland):
    """
    提取mask——叠加到图像
    :param path_detection: 要叠加的图像路径（JPG）
    :param path_farmland: 提取mask的图像路径（png）
    :param color_farmland: mask的颜色
    :return: 写入文件（'../data/IMAGE/liuhe/overlayer/'）
    """
    files = os.listdir(path_detection)
    images_detection = [path_detection + image for image in files if '.JPG' in image]
    files = os.listdir(path_farmland)
    images_farmland = [path_farmland + image for image in files if '.png' in image]
    path = '../data/IMAGE/liuhe/overlayer/'+path_detection.split('/')[-4]+'/'
    if not os.path.exists(path):
        os.makedirs(path)
    for image_detection in images_detection:
        a=1
        for image_farmland in images_farmland:
            if image_detection.split('/')[-1].split('.')[0] == image_farmland.split('/')[-1].split('.')[0]:
                img_detection = cv.imread(image_detection)
                img_farmland = cv.imread(image_farmland)
                mask = np.zeros_like(img_detection, dtype=np.uint8)
                boolean = img_farmland == color_farmland
                # print(boolean)
                dst = mask[:, :, 0] + boolean[:, :, 0] + boolean[:, :, 1] + boolean[:, :, 2]
                mask[dst == 3, :] = [144,238,144]
                # cv.imwrite('../data/IMAGE/test/1.png', mask)
                img_detection[dst == 3, :] = [0, 0, 0]
                result = mask + img_detection
                cv.imwrite(path+image_detection.split('/')[-1].replace('JPG','png'),result)
                a=0
            else:
                continue
        if a:
            shutil.copy(image_detection, path)

def overlay_panorama(image_detection,image_farmland,color_farmland=[230,230,100]):
    """
    提取全景图mask——叠加到全景图图像
    :param image_detection:
    :param image_farmland:
    :param color_farmland:
    :return:
    """
    # img_detection = cv.imread(image_detection)
    img_farmland = cv.imread(image_farmland)
    # mask = np.zeros_like(img_detection, dtype=np.uint8)
    mask = np.zeros_like(img_farmland, dtype=np.uint8)

    boolean = img_farmland > color_farmland
    # print(boolean)
    dst = mask[:, :, 0] + boolean[:, :, 0] + boolean[:, :, 1] + (boolean[:, :, 2]+mask[:, :, 0])*5
    img_farmland[dst==2,:] = [0,0,0]
    result = img_farmland
    # img_detection[dst == 3, :] = [0, 0, 0]
    # result = mask + img_detection
    # cv.imwrite(image_detection.replace('JPG','png'), result)
    # cv.imwrite(image_farmland.replace('jpg', 'png'), result)
    return result

def get_dir(path):
    dirs = os.listdir(path)
    return [path + dir + '/' for dir in dirs if '.' not in dir]

def overlay_mask(mask,img):
    """
    叠加mask到图像
    :param path:
    :param mask:
    :param img:
    :param name:
    :return:
    """
    zero = np.zeros_like(img,dtype=np.uint8)
    boolean = mask > [0,0,0]
    # print(boolean)
    dst = zero[:, :, 0] + boolean[:, :, 0] + boolean[:, :, 1] + boolean[:, :, 2]
    img[dst == 3, :] = [144,238,144]
    return img

def get_mask(mask_image,color):
    """
    获取图像mask
    :param mask_image:
    :param color:
    :return:
    """
    mask = np.zeros_like(mask_image, dtype=np.uint8)
    boolean = mask_image == color
    dst = mask[:, :, 0] + boolean[:, :, 0] + boolean[:, :, 1] + boolean[:, :, 2]
    mask[dst == 3, :] = [144, 238, 144]
    return mask

if __name__ == '__main__':
    path = '../data/IMAGE/025_0002/origin/'
    images = os.listdir(path)
    images = [path + image for image in images if '.JPG' in image]





