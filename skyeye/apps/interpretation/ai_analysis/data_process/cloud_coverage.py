# -*- coding: utf-8 -*-
try:
    import gdal,gdal_array
except:
    from osgeo import gdal,gdal_array
import numpy as np
import os,sys,shutil,cv2,math
from PIL import Image
from PIL import ImageFile
import read_write_tif
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 40).__str__()
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(WORK_DIR)
import apps.interpretation.ai_config as cg
work_dir = cg.PROJECT_PATH

class Cloud_Coverage():
    def down_resample(self, scale, infile_path, outfile_path, im_bands):
        in_ds = gdal.Open(infile_path)
        geotrans = list(in_ds.GetGeoTransform())
        geotrans[1] *= scale  # 像元宽度变为原来的两倍
        geotrans[5] *= scale  # 像元高度也变为原来的两倍
        in_band = in_ds.GetRasterBand(1)
        xsize = in_band.XSize
        ysize = in_band.YSize
        x_resolution = int(xsize / scale)  # 影像的行列都变为原来的一半
        y_resolution = int(ysize / scale)
        if os.path.exists(outfile_path):  # 如果存在重采样后的影像，则删除之
            os.remove(outfile_path)

        out_ds = gdal.GetDriverByName("GTiff").Create(outfile_path, x_resolution, y_resolution, im_bands,
                                                      gdal.GDT_Byte)  # 创建一个构建重采样影像的句柄
        out_ds.SetGeoTransform(geotrans)  # 设置地理变换信息
        out_ds.SetProjection(in_ds.GetProjection())  # 设置投影信息
        data = np.empty((im_bands, y_resolution, x_resolution), np.uint8)  # 设置一个与重采样影像行列号相等的矩阵去接受读取所得的像元值
        for i in range(im_bands):
            in_band = in_ds.GetRasterBand(i + 1)
            in_band.ReadAsArray(buf_obj=data[i])
            out_band = out_ds.GetRasterBand(i + 1)
            out_band.WriteArray(data[i])
        out_band.FlushCache()
        out_band.ComputeStatistics(False)  # 计算统计信息
        # out_ds.BuildOverviews('average', [1, 2, 4, 8, 16, 32])  # 构建金字塔
        del in_ds  # 删除句柄
        del out_ds
        # print("down_resample process has succeeded!")


    def img_dilate(self, img):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        img_dilated = cv2.dilate(img, kernel)
        return img_dilated

    def img_erode(self, img):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        img_erosion = cv2.erode(img, kernel)
        return img_erosion

    def img_cut(self, img, output_path):
        """
            裁剪图像为指定格式并保存成tiff
            输入为array形式的数组
            """
        # num = 0
        cropsize = 10000
        height = img.shape[1]
        width = img.shape[2]
        row_col_list = []
        # 从左上开始裁剪
        for i in range(int((height) / (cropsize))):  # 行裁剪次数
            for j in range(int((width) / (cropsize))):  # 列裁剪次数
                cropped = img[:,  # 通道不裁剪
                          i * cropsize: i * cropsize + cropsize,
                          j * cropsize: j * cropsize + cropsize,
                          ]
                cropped = np.uint8(cropped)
                im_height = cropped.shape[1]
                im_width = cropped.shape[2]
                row_col_list.append([i, j])
                # num = num + 1
                target = output_path + '/cropped{}{}.tif'.format(i, j)
                out = gdal_array.SaveArray(cropped, target, format="GTiff")

        # #  向前裁剪最后一列
        for i in range(int((height) / (cropsize))):
            for j in range(int((width) / (cropsize))):
                cropped = img[:,  # 通道不裁剪
                          i * cropsize: i * cropsize + cropsize,  # 所有行
                          (math.ceil(width / cropsize) - 1) * cropsize: width,  # 最后256列
                          ]
                cropped = np.uint8(cropped)
                im_height = cropped.shape[1]
                im_width = cropped.shape[2]
                # num = num + 1
                target = output_path + '/cropped{}{}.tif'.format(i, math.ceil(width / cropsize) - 1)
                out = gdal_array.SaveArray(cropped, target, format="GTiff")

        # #  向前裁剪最后一行
        for i in range(int((height) / (cropsize))):
            for j in range(int((width) / (cropsize))):
                cropped = img[:,  # 通道不裁剪
                          (math.ceil(height / cropsize) - 1) * cropsize: height,  # 最后256行
                          j * cropsize: j * cropsize + cropsize,  # 所有列
                          ]
                cropped = np.uint8(cropped)
                im_height = cropped.shape[1]
                im_width = cropped.shape[2]
                # cropped_3bands = four_bands_to_three_bands(cropped)
                # num = num + 1
                target = output_path + '/cropped{}{}.tif'.format(math.ceil(height / cropsize) - 1, j)
                # writeTiff(cropped, im_width, im_height, 3, target)
                out = gdal_array.SaveArray(cropped, target, format="GTiff")

        # 裁剪右下角
        cropped = img[:,  # 通道不裁剪
                  (math.ceil(height / cropsize) - 1) * cropsize: height,
                  (math.ceil(width / cropsize) - 1) * cropsize: width,
                  ]
        cropped = np.uint8(cropped)
        im_height = cropped.shape[1]
        im_width = cropped.shape[2]
        i = math.ceil(height / cropsize) - 1
        j = math.ceil(width / cropsize) - 1
        # cropped_3bands = four_bands_to_three_bands(cropped)
        # num = num + 1
        target = output_path + '/cropped{}{}.tif'.format(i, j)
        # writeTiff(cropped, im_width, im_height, 3, target)
        gdal_array.SaveArray(cropped, target, format="GTiff")


    def img_combine(self, input_dir):
        file_list = os.listdir(input_dir)
        row_list = []
        col_list = []
        img = []
        img_col = []
        img_row = []
        k = 0
        for filename in file_list:
            if filename.endswith('.tif') and 'cropped' in filename:
                filepath = os.path.join(input_dir, filename)
                i = int(filename.split('.')[0][-2:-1])
                j = int(filename.split('.')[0][-1:])

                if k != i:
                    k = i
                    img_col.append(img)
                    img = np.array(Image.open(filepath))
                else:
                    if j == 0:
                        img = np.array(Image.open(filepath))
                    else:
                        img = np.hstack([img, np.array(Image.open(filepath))])
        img_col.append(img)

        for i in range(len(img_col)):
            if i == 0:
                img_row = img_col[0]
            else:
                img_row = np.vstack([img_row, img_col[i]])
        return img_row

    def img_clip(self, img, im_width, im_height):
        center_row = np.int(im_height/2)
        center_col = np.int(im_width/2)
        img1 = img[0:center_row, 0:center_col]
        img2 = img[0:center_row, center_col:im_width]
        img3 = img[center_row:im_height, 0:center_col]
        img4 = img[center_row:im_height, center_col:im_width]
        return [img1, img2, img3, img4]

    # 获取影像的云雪覆盖量并生成云掩膜文件
    def get_cloud_coverage(self,img_path,mask_threshold):
        """
        :param img_path: 输入影像的路径
        :return: 影像云雪覆盖量（以%为单位），云雪二值化掩膜文件（0为云雪、1为其他地物）
        """
        # img, im_width, im_height, im_bands, im_geotrans, im_proj = read_write_tif.readTiff(img_path)

        outfile_dir = os.path.join(os.path.dirname(img_path),os.path.basename(img_path).split('.')[0]+'temp_cldsnow')
        if os.path.exists(outfile_dir):
            shutil.rmtree(outfile_dir)
            os.mkdir(outfile_dir)
        else:
            os.mkdir(outfile_dir)
        outfile_path = os.path.join(outfile_dir, os.path.basename(img_path).split('.')[0]+'_resm.tif')
        self.down_resample(2, img_path, outfile_path, 3)

        img, im_width, im_height, im_bands, im_geotrans, im_proj = read_write_tif.readtiff(outfile_path)
        band1 = img[0, :, :]
        band3 = img[2, :, :]
        mask_threshold = np.float32(mask_threshold)
        base_threshold = 0
        threshold = (float(mask_threshold) - 0.5)*20

        if im_width < 10000 and im_height < 10000:
            HOT = np.float32(band3) - np.float32(0.5) * np.float32(band1) - np.float32(90.4)
            mask1 = HOT > threshold
            mask2 = HOT <= threshold
            HOT[mask1] = 1
            HOT[mask2] = 0
            mask3 = band1 > 0
            mask4 = band1 <= 0
            band1[mask3] = 1
            band1[mask4] = 0

        else:
            band1 = img[0, :, :]
            band3 = img[2, :, :]
            img_clip_b1 = []
            img_clip_b3 = []
            img_clip_b1 = Cloud_Coverage.img_clip(self, band1, im_width, im_height)
            img_clip_b3 = Cloud_Coverage.img_clip(self, band3, im_width, im_height)
            HOT = []
            for i in range(len(img_clip_b3)):
                HOT.append( np.float32(img_clip_b3[i]) - np.float32(0.5) * np.float32(img_clip_b1[i]) - np.float32(90.4))
                mask1 = HOT[i] > threshold
                mask2 = HOT[i] <= threshold
                HOT[i][mask1] = 1
                HOT[i][mask2] = 0
                mask3 = img_clip_b1[i] > 0
                mask4 = img_clip_b1[i] <= 0
                img_clip_b1[i][mask3] = 1
                img_clip_b1[i][mask4] = 0
            HOT_12 = np.uint8(np.concatenate([HOT[0], HOT[1]], axis=1))
            HOT_34 = np.uint8(np.concatenate([HOT[2], HOT[3]], axis=1))
            HOT = np.concatenate([HOT_12, HOT_34], axis=0)
            band1_12 = np.uint8(np.concatenate([img_clip_b1[0], img_clip_b1[1]], axis=1))
            band1_34 = np.uint8(np.concatenate([img_clip_b1[2], img_clip_b1[3]], axis=1))
            band1 = np.concatenate([band1_12,band1_34], axis=0)

        img_sum = np.sum(band1)
        HOT_cloud_sum = np.sum(HOT)
        cloud_covrage = HOT_cloud_sum / img_sum * 100
        mask = np.uint8(np.where(HOT<1, 1, 0))

        mask_dilated = self.img_dilate(mask)
        mask_ecosion = self.img_erode(mask_dilated)

        shutil.rmtree(outfile_dir)
        return cloud_covrage, mask_ecosion, im_width, im_height, im_bands, im_geotrans, im_proj
