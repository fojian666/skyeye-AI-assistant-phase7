# -*- coding: utf-8 -*-
from osgeo import gdal
import os
import ai_config as cg
logger = cg.logger
def img_to_tif_main(img_dir, output_path, status_num_txt_path):
    """
    img格式数据转换为tif数据
    Args:
        img_dir: img影像文件夹地址
        output_path: 输出路径
        status_num_txt_path:进度更新文件路径
    Returns:
    """
    try:
        # 打开 IMG 文件
        file_list = [i for i in os.listdir(img_dir) if i.endswith(".img")]
        interval_bar = int(80 / len(file_list))
        for index, i in enumerate(file_list):
            img_file = os.path.join(img_dir, i)
            logger.info("开始转换{}文件".format(i))
            img_dataset = gdal.Open(img_file)
            if img_dataset is None:
                raise Exception("无法打开 IMG 文件")
            # 获取图像宽度、高度和波段数量
            width = img_dataset.RasterXSize
            height = img_dataset.RasterYSize
            num_bands = img_dataset.RasterCount
            save_tif_path = os.path.join(output_path,os.path.basename(img_file).split('.')[0]+'.tif')
            # 创建输出 TIFF 文件
            driver = gdal.GetDriverByName("GTiff")
            tif_dataset = driver.Create(save_tif_path, width, height, num_bands, gdal.GDT_Byte)
            # 遍历每个波段并写入 TIFF 文件
            for i in range(1, num_bands + 1):
                band = img_dataset.GetRasterBand(i)
                band_data = band.ReadAsArray()
                tif_dataset.GetRasterBand(i).WriteArray(band_data)
                band = None
            # 设置原始投影和地理变换信息到输出 TIFF 文件
            tif_dataset.SetProjection(img_dataset.GetProjection())
            tif_dataset.SetGeoTransform(img_dataset.GetGeoTransform())
            # 关闭数据集
            img_dataset = None
            tif_dataset = None
            update_status_bar((10 + index * interval_bar), status_num_txt_path)
        print("IMG 文件转换为 TIFF 文件完成！")
    except Exception as e:
        print("转换失败:", str(e))

def update_status_bar(num,txt_path):
    """
    更新进度条进度百分比,写入log
    Args:
        num: 进度百分比

    Returns:
    """
    with open(txt_path, 'w+') as f:
        f.write(str(num))

if __name__ == '__main__':
    # 示例使用
    img_file = r'E:\geo_ai_server\c#_test_data\img_to_tif_data\mengya'
    tiff_file = r'E:\geo_ai_server\c#_test_data\result\13'
    status_num_txt_path = r''
    img_to_tif_main(img_file, tiff_file, status_num_txt_path)