import os,json,sys
import shutil
from osgeo import gdal
import numpy as np
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(WORK_DIR)
import ai_config as cg
config_file = cg.RADIOJSON_FILE
config = json.load(open(config_file))
logger = cg.logger
def ReadTiff(fileName):
    '''
    读取tif影像
    :param fileName: 输入文件路径
    :return: 影像的波段值、行列数、坐标系
    '''
    dataset = gdal.Open(fileName)
    if dataset == None:
        print(fileName + "文件无法打开")
        return
    im_width = dataset.RasterXSize  # 栅格矩阵的列数
    im_height = dataset.RasterYSize  # 栅格矩阵的行数
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    return im_data, im_width, im_height, im_geotrans, im_proj


def WriteTiff(im_data, im_width, im_height, im_bands, im_geotrans, im_proj, path):
    '''
    写tif影像
    :param im_data: 要写入的数据
    :param im_width: 列数
    :param im_height: 行数
    :param im_bands: 波段数
    :param im_geotrans: 坐标系
    :param im_proj: 投影
    :param path: 保存路径
    :return: 0
    '''
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
        # 创建文件
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if (dataset != None):
        dataset.SetGeoTransform(im_geotrans)  # 写入仿射变换参数
        dataset.SetProjection(im_proj)  # 写入投影
    for i in range(im_bands):
        dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
    del dataset

def get_data_information(file_path):
    '''
    获取文件的卫星、传感器等信息
    :param file_path: 输入的文件夹路径
    :return: 数据来源卫星、传感器、获取年份、数据级别
    '''
    filename_split = os.path.basename(file_path).split('_')
    satelliteID = filename_split[0]
    sensorID = filename_split[1]
    data_year = filename_split[4][:4]
    image_type = filename_split[5][0:3]
    return satelliteID, sensorID, data_year, image_type

def get_gain_bias(BandId,SatelliteID,SensorID,Year,ImageType,config):
    '''
    获取数据的增益和偏置
    :param BandId: 数据的波段
    :param SatelliteID: 卫星类型
    :param SensorID: 传感器类型
    :param Year: 数据获取年份
    :param ImageType: 数据的级别
    :param config: 增益偏置文件
    :return: 数据的定标系数增益和偏置
    '''
    # global cols,rows,SatelliteID,SensorID,Year,ImageType,config
    if SensorID[0:3] == "WFV":
        Gain_ =config["Parameter"][SatelliteID][SensorID][Year]["gain"][BandId-1]
        Bias_ =config["Parameter"][SatelliteID][SensorID][Year]["offset"][BandId-1]
    else:
        Gain_ =config["Parameter"][SatelliteID][SensorID][Year][ImageType]["gain"][BandId-1]
        Bias_ =config["Parameter"][SatelliteID][SensorID][Year][ImageType]["offset"][BandId-1]

    return Gain_,Bias_

def radiometric_calibration(img_root, SatelliteID, SensorID, ImagingYear, ImageTypeFlag_isL1A, out_root):
    '''
    对数据进行辐射定标
    以上所有定标系数计算公式为 L= Gain*DN + Bias，式中 DN 为卫星影像的观测数字值，L 为卫星载荷通道入瞳处等效辐射亮度，单位为 W⋅m-2⋅
    sr-1⋅μm-1，Gain 和 Bias 分别为定标系数增益和偏移量，没有标注 Bias 值的情况下代表 Bias 值为 0
    :param img_root:输入数据的文件夹路径
    :param out_root: 输出结果的保存路径
    :return: 0
    '''
    if ImageTypeFlag_isL1A:
        try:
            os.mkdir(out_root)
        except Exception as e:
            print(e)
            pass
        for file in os.listdir(img_root):
            if file.endswith('.tiff'):
                file_path = os.path.join(img_root, file)
                save_path = os.path.join(out_root, file)
                # 将头文件和几何校正文件拷贝到大气校正结果文件中
                filename = os.path.basename(file_path)
                atcfiles = os.path.dirname(save_path)
                fileType = SatelliteID[0:2]
                # filename_split = filename.split("_")
                logger.info("确认数据类型!!!@{}".format(file))
                if fileType == 'GF':
                    GFType = SensorID[0:3]
                    # GFType = filename[4:7]
                    # GFType = filename_split[1][:3]
                    outFileName = filename[:-7]
                    if GFType == 'WFV':
                        metedata = file_path.replace('.tiff','.xml')
                        rpb_file = file_path.replace('.tiff','.rpb')

                    elif GFType == 'PMS':
                        metedata = file_path.replace('.tiff', 'MSS.xml')
                        rpb_file = file_path.replace('.tiff','MSS.rpb')
                logger.info("拷贝xml文件和rpb文件!!!@{}".format(file))
                metedata_basename = os.path.basename(metedata)
                copy_metedata = os.path.join(atcfiles, metedata_basename)
                shutil.copy(metedata, copy_metedata)

                rpb_basename = os.path.basename(rpb_file)
                copy_rpb_file = os.path.join(atcfiles, rpb_basename)
                shutil.copy(rpb_file, copy_rpb_file)

                im_data, im_width, im_height, im_geotrans, im_proj = ReadTiff(file_path)
                im_bands, im_height, im_width = im_data.shape
                im_calibration = np.zeros_like(im_data, np.float32)
                ImageType = 'L1A'
                logger.info("读取配置文件!!!@{}".format(file))
                for band_i in range(im_bands):
                    sensor_gain, sensor_bias = get_gain_bias(band_i, SatelliteID, SensorID, ImagingYear, ImageType, config)
                    im_calibration[band_i] = np.float32(im_data[band_i])*sensor_gain+sensor_bias
                logger.info("写入辐射定标后的文件!!!@{}".format(file))
                WriteTiff(im_calibration, im_width, im_height, im_bands, im_geotrans, im_proj, save_path)
    else:
        print('输入数据级别不正确，不能进行辐射定标！')

if __name__ == '__main__':
    file_root = r'E:\TEST\test\GF1_WFV1_E120.2_N31.3_20240405_L1A13352764001'
    out_root = r'E:\TEST\test\out\7'
    SatelliteID = 'GF1'
    SensorID = 'WFV1'
    ImagingYear = '2024'
    ImageTypeFlag_isL1A = True
    radiometric_calibration(file_root, SatelliteID, SensorID, ImagingYear, ImageTypeFlag_isL1A, out_root)





