# -*- coding: utf-8 -*-
try:
    import gdal, gdalconst
except:
    from osgeo import gdal, gdalconst
import os, sys, shutil

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(WORK_DIR)
sys.path.append(os.path.dirname(WORK_DIR))
import apps.interpretation.ai_config as cg

logger = cg.logger


class Resampling():
    def dir_create(self, input_path):
        """
        创建文件
        Args:
            input_path: 创建文件路径
        Returns:

        """
        if not os.path.exists(input_path):
            os.mkdir(input_path)

    def open_img(self, img_path):
        """
        获取影像信息
        Args:
            img_path: 影像文件地址

        Returns:影像数据，波段数，长宽

        """
        img_dataset = gdal.Open(img_path, gdal.GA_ReadOnly)  # 打开影像
        band_count = img_dataset.RasterCount  # 波段数
        img_cols = img_dataset.RasterXSize  # 列数
        mg_rows = img_dataset.RasterYSize
        return img_dataset, band_count, img_cols, mg_rows

    def resampling_two_images(self, in_filename, ref_filename, out_filename):
        """

        Args:
            in_filename:前景地址
            ref_filename:后景地址
            out_filename:重采样后文件名

        Returns:

        """
        in_file = gdal.Open(in_filename, gdal.GA_ReadOnly)
        in_band = in_file.GetRasterBand(3)
        in_Proj = in_file.GetProjection()
        ref_file = gdal.Open(ref_filename, gdal.GA_ReadOnly)
        ref_geoTrans = ref_file.GetGeoTransform()
        ref_Proj = ref_file.GetProjection()
        ref_band = ref_file.GetRasterBand(1)
        # 读取影像信息，获取影像长宽以及波段数量
        x = ref_file.RasterXSize
        y = ref_file.RasterYSize
        bands = ref_file.RasterCount
        driver = gdal.GetDriverByName('GTiff')
        output = driver.Create(out_filename, x, y, bands, in_band.DataType)
        output.SetGeoTransform(ref_geoTrans)
        output.SetProjection(ref_Proj)
        # 重采样操作
        options = gdal.WarpOptions(srcSRS=in_Proj,
                                   dstSRS=ref_Proj,
                                   resampleAlg=gdalconst.GRA_NearestNeighbour,
                                   # dstNodata = 0,
                                   # srcNodata = 255,
                                   )
        gdal.Warp(output, in_filename, options=options)

    def start_resampling(self, pre_img_file, next_img_file, successful_dir, failed_dir, folder_name):
        """
        :param pre_img_file: 前景影像单个文件
        :param next_img_file: 后景影像单个文件
        :param successful_dir: 重采样成功文件放置路径
        :param failed_dir: 重采样失败文件放置路径
        :param pre_place: 影像名称
        :return: 标识码，重采样后的文件存储路径
        """
        # 获取前后两期影像的信息
        pre_img_dataset, pre_band_count, pre_img_cols, pre_img_rows = self.open_img(pre_img_file)
        next_img_dataset, next_band_count, next_img_cols, next_img_rows = self.open_img(next_img_file)
        pre_img_name = os.path.splitext(os.path.basename(pre_img_file))[0]
        next_img_name = os.path.splitext(os.path.basename(next_img_file))[0]
        # 判断是否进行重采样
        if pre_band_count == 0 or next_band_count == 0 or pre_band_count != next_band_count:
            logger.warning(
                "数据处理:error!前时或后时影像波段数为0或者前后时相波段数不一致，停止采样!前后影像地址{}---{}@{}".format(pre_img_name, next_img_name,
                                                                                   folder_name))
            failed_solo_dir = os.path.join(failed_dir, folder_name)
            self.dir_create(failed_solo_dir)
            shutil.copyfile(pre_img_file, os.path.join(failed_solo_dir, os.path.basename(pre_img_file)))
            shutil.copyfile(next_img_file, os.path.join(failed_solo_dir, os.path.basename(next_img_file)))
            return 0, '', ''

        elif (next_img_cols == pre_img_cols) and (next_img_rows == pre_img_rows):
            logger.info("数据处理:Successful,前时后时影像行数列数一样，后续将默认以后时影像为基准!{}@{}".format(pre_img_name, folder_name))
            success_solo_dir = os.path.join(successful_dir, folder_name)
            self.dir_create(success_solo_dir)
            pre_img_path = os.path.join(success_solo_dir, os.path.basename(pre_img_file))
            next_img_path = os.path.join(success_solo_dir, os.path.basename(next_img_file))
            shutil.copyfile(next_img_file, next_img_path)
            shutil.copyfile(pre_img_file, pre_img_path)
            del pre_img_dataset
            del next_img_dataset
            return 1, pre_img_path, next_img_path

        elif (next_img_cols - pre_img_cols > 10) or (next_img_cols - pre_img_cols < -10) or (
                next_img_rows - pre_img_rows > 10) or (next_img_rows - pre_img_rows <= -10):
            logger.warning(
                "数据处理:error!前时后时影像行列数误差过大，停止采样!前后影像地址{}--{}@{}".format(pre_img_name, next_img_name, folder_name))
            failed_solo_dir = os.path.join(failed_dir, folder_name)
            self.dir_create(failed_solo_dir)
            shutil.copyfile(pre_img_file, os.path.join(failed_solo_dir, os.path.basename(pre_img_file)))
            shutil.copyfile(next_img_file, os.path.join(failed_solo_dir, os.path.basename(next_img_file)))
            del pre_img_dataset
            del next_img_dataset
            return 0, '', ''

        else:
            logger.info(
                "数据处理:Successful,前后时相影像行列号不一致，后期影像开始重采样,后续处理将以前时影像为基准:——{}@{}".format(next_img_name, folder_name))
            success_solo_dir = os.path.join(successful_dir, folder_name)
            self.dir_create(success_solo_dir)
            pre_img_path = os.path.join(success_solo_dir, os.path.basename(pre_img_file))
            next_img_path = os.path.join(success_solo_dir, os.path.basename(next_img_file))
            shutil.copyfile(pre_img_file, pre_img_path)
            self.resampling_two_images(next_img_file, pre_img_path, next_img_path)
            del pre_img_dataset
            del next_img_dataset
            return 1, pre_img_path, next_img_path
