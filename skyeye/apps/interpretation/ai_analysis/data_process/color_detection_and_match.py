# -*- coding: utf-8 -*-
try:
    import gdal, gdalconst
except:
    from osgeo import gdal, gdalconst
import os
from PIL import Image
from PIL import ImageFile
import cv2, sys
import numpy as np
import read_write_tif

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import apps.interpretation.ai_config as cg

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 40).__str__()
work_dir = cg.PROJECT_PATH

class Color_Detection():
    ##比较两影像的颜色是否一致
    def get_hsv(self, img):
        """
        :param img: RGB影像，以imread形式读取的影像的ndarray格式
        :return: 影像hsv分量的h分量
        """
        ##获得影像hsv分量的h分量
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h = hsv[:, :, 0]
        return h

    def hsv_histgram_contrast(self, h1, h2):
        """
        :param h1: 前影像的h分量
        :param h2: 后影像的h分量
        :return: 影像色调比对结果，若两幅影像的色调一致，返回flag=True，否则返回False
        """
        ##比较两影像hsv分量的h分量
        img_color_flag = False
        hist1 = cv2.calcHist([h1], [0], None, [180], [1, 180])  # 2.获取图像的灰度直方图
        hist1 = (hist1 / (h1.shape[0] * h1.shape[1])).flatten()
        hist2 = cv2.calcHist([h2], [0], None, [180], [1, 180])  # 2.获取图像的灰度直方图
        hist2 = (hist2 / (h2.shape[0] * h2.shape[1])).flatten()
        coeffient = np.corrcoef(hist1, hist2)
        if coeffient[0, 1] > 0.7:
            img_color_flag = True
        else:
            img_color_flag = False
        return img_color_flag


    def run_color_contrast(self, img1_path, img2_path):
        """
        :param img1_path: 前影像的路径
        :param img2_path: 后影响的路径
        :return: 两影像进行色调一致性比对结果，若两幅影像的色调一致，返回flag=True，否则返回False
        """
        img1, im_width, im_height, im_bands, im_geotrans, im_proj = read_write_tif.readtiff(img1_path)
        band1 = img1[0, :, :]
        band2 = img1[1, :, :]
        band3 = img1[2, :, :]
        img1 = np.stack([band3, band2, band1], axis=2)

        img2, im_width, im_height, im_bands, im_geotrans, im_proj = read_write_tif.readtiff(img2_path)
        band1 = img2[0, :, :]
        band2 = img2[1, :, :]
        band3 = img2[2, :, :]
        img2 = np.stack([band3, band2, band1], axis=2)
        h1 = self.get_hsv(img1)
        h2 = self.get_hsv(img2)
        #比较两期影像色彩是否匹配
        img_color_flag = self.hsv_histgram_contrast(h1, h2)
        return img_color_flag

class Image_Match():

    def get_gray_cumulative_prop(self, gray):
        """获取图像的累积分布直方图，即就P{X<=x}的概率
    		- 大X表示随机变量
    		- 小x表示取值边界
    	"""
        cum_gray = []
        sum_prop = 0.
        for i in gray:
            sum_prop += i
            cum_gray.append(sum_prop)  # 累计概率求和
        return cum_gray

    def pix_fill(self, img, cum_gray, height, width):
        """像素填充"""
        des_img = np.zeros((height, width), dtype=np.uint8)  # 定义目标图像矩阵
        for h in range(height):
            for w in range(width):
                # 把每一个像素点根据累积概率求得均衡化后的像素值
                des_img[h][w] = int(cum_gray[img[h][w]] * 255.0 + 0.5)
        return des_img

    def histogram_match(self, img_pix1, img_pix2):
        """
        运行图像直方图匹配
        :param img_pix1:前影像矩阵
        :param img_pix2:后影像矩阵
        :return: 以后影像为参考的前影像直方图匹配结果
        """
        his1 = cv2.calcHist([img_pix1], [0], None, [256], [0, 256])  # 2.获取图像的灰度直方图
        his1 = (his1 / (img_pix1.shape[0] * img_pix1.shape[1])).flatten()
        his2 = cv2.calcHist([img_pix2], [0], None, [256], [0, 256])
        his2 = (his2 / (img_pix2.shape[0] * img_pix2.shape[1])).flatten()
        cul_his1 = self.get_gray_cumulative_prop(his1)  # 3.获取图像的累积分布函数
        cul_his2 = self.get_gray_cumulative_prop(his2)

        # 寻找像素映射（累积概率，就进原则）
        new_index = []
        for each_gray in cul_his1:
            # 求出原直方图每一个灰度级累计概率在指定直方图上的灰度索引
            diff = list(abs(np.array(cul_his2 - each_gray)))
            closest_index = diff.index(min(diff))  # 索引代表对应填充的灰度级
            new_index.append(closest_index)
        new_index = np.array(new_index)
        # 填充像素
        height, width = img_pix1.shape
        new_img_pix = np.zeros((height, width), dtype=np.int)
        for h in range(height):
            new_img_pix[h, :] = new_index[img_pix1[h, :]]
        return new_img_pix

    def run_histogram_match(self, file_path, ref_file_path, out_file_path):
        """

        :param file_path: 影像路径
        :param ref_file_path: 参考影像路径
        :param out_file_path: 以参考影像为准的影像色调匹配影像输出路径
        :return:
        """
        img_pix, im_width, im_height, im_bands, im_geotrans, im_proj = read_write_tif.readtiff(file_path)
        ref_img_pix, ref_width, ref_height, ref_bands, ref_geotrans, ref_proj = read_write_tif.readtiff(
            ref_file_path)
        img_pix = np.uint8(img_pix)
        ref_img_pix = np.uint8(ref_img_pix)
        new_img = np.zeros((im_bands, im_height, im_width), dtype=np.uint8)
        for i in range(im_bands):
            new_img[i, :, :] = self.histogram_match(img_pix[i, :, :], ref_img_pix[i, :, :])  # 执行图像规定化
        read_write_tif.writetiff(new_img, im_width, im_height, im_bands, im_geotrans, im_proj, out_file_path)

class Image_Color_Equalization():
    # 定义函数，用于读取中文路径下的图像
    def read_chinese_img(self, img_path):
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        return img

    def color_equalization(self, img):
        # 读取图像
        # img = Image_color_equalization().read_chinese_img(img_path)
        # 将图像转换为HSV颜色空间
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # 分离H、S、V三个通道
        h, s, v = cv2.split(hsv_img)
        # 对亮度通道进行直方图均衡化
        v = cv2.equalizeHist(v)
        # 对色度和饱和度通道进行平滑处理
        s = cv2.GaussianBlur(s, (5, 5), 0)
        h = cv2.GaussianBlur(h, (5, 5), 0)

        # 合并分离后的三个通道，并将图像转换回BGR颜色空间
        hsv_img = cv2.merge([h, s, v])
        result = cv2.cvtColor(hsv_img, cv2.COLOR_HSV2BGR)

        return result

    def run_color_equalization(self, file_path, out_file_path):
        img_pix, im_width, im_height, im_bands, im_geotrans, im_proj = read_write_tif.readtiff(file_path)
        img_pix = np.transpose(img_pix,(2,1,0))
        img_pix = np.transpose(img_pix,(1,0,2))
        img_color_equ = Image_Color_Equalization().color_equalization(img_pix)
        img_color_equ = np.transpose(img_color_equ,(1,0,2))
        img_color_equ = np.transpose(img_color_equ,(2,1,0))
        read_write_tif.writetiff(img_color_equ, im_width, im_height, im_bands, im_geotrans, im_proj, out_file_path)

