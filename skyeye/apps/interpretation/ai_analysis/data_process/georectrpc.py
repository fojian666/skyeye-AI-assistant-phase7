import os,sys
import re
import numpy as np
from osgeo import gdal
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(WORK_DIR)
import ai_config as cg
dem_path = cg.GEO_DEM_PATH
logger = cg.logger
def rpcrect(input_path, output_path, resample_method):
    """
    使用根据影像自带的RPC文件，利用RPC校正方法对影像进行正射校正
    :param input:输入原始影像
    :param output:输出正射影像
    """
    print(input_path, output_path,resample_method)
    for file in os.listdir(input_path):
        if file.endswith('.tiff') or file.endswith('.tif'):
            file_path = os.path.join(input_path, file)
            dataset = gdal.Open(file_path, gdal.GA_Update)#读入影像
            rpc = dataset.GetMetadata("RPC")#读入影像，rpc
            if resample_method == 'Bilinear':
                resample_method_flag = gdal.GRIORA_Bilinear
            else:
                resample_method_flag = gdal.GRIORA_NearestNeighbour
            print("校正中..............")
            logger.info("校正中@{}".format(file))
            output_path = output_path + '.tif'
            dst_ds = gdal.Warp(output_path, dataset, dstSRS='EPSG:4326',
                               # xRes=x_resolution,#x方向正射影像分辨率
                               # yRes=y_resolution, #y方向正射影像分辨率
                               resampleAlg=resample_method_flag,#插值方式，默认为最最邻近，我们一般使用双线性
                               rpc=True, #使用RPC模型进行校正
                               transformerOptions=[dem_path]#参考DEM
                               )

def get_input_image_path(input_root, output_root):
    '''
    批量进行校正时，获取文件夹下的文件
    '''
    input_path_list = []
    output_path_list = []
    for file in os.listdir(input_root):
        if file.endswith('.tif') or file.endswith('tiff'):
            input_path = os.path.join(input_root, file)
            output_path = os.path.join(output_root, file)
            input_path_list.append(input_path)
            output_path_list.append(output_path)
    return [input_path_list, output_path_list]


if __name__ == '__main__':
    input_root= r'D:\data\example_data\out\calibration'
    output_root = r'D:\data\example_data\out\geo'
    if not output_root:
        os.makedirs(output_root)
    [input_path, output_path] = get_input_image_path(input_root, output_root)
    x_resolution = 0.00016
    y_resolution = 0.00016
    resample_method = 'NearestNeighbour' # OR 'Bilinear'
    for i in range(len(input_path)):
        rpcrect(input_path[i], output_path[i], x_resolution, y_resolution, resample_method = resample_method)

