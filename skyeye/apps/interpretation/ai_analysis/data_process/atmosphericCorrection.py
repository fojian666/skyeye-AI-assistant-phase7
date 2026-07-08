#! usr/bin/env python
# -*- coding:utf-8 -*-
import glob
import os
import sys
import tarfile            #解压缩
import json
import numpy as np
from osgeo import gdal
import math
import time
import xml.dom.minidom    #读取xml格式的影像头文件
from tqdm import tqdm     #进度条
from Py6S import *
import shutil
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(WORK_DIR)
import ai_config as cg
config_file = cg.RADIOJSON_FILE
dem_path = cg.DEM_PATH
logger = cg.logger
def MeanDEM(pointUL, pointDR):
    '''
    计算影像所在区域的平均高程.
    '''

    try:
        DEMIDataSet = gdal.Open(dem_path)
    except Exception as e:
        pass

    DEMBand = DEMIDataSet.GetRasterBand(1)
    geotransform = DEMIDataSet.GetGeoTransform()
    # DEM分辨率
    pixelWidth = geotransform[1]
    pixelHight = geotransform[5]

    # DEM起始点：左上角，X：经度，Y：纬度
    originX = geotransform[0]
    originY = geotransform[3]

    # 研究区左上角在DEM矩阵中的位置
    yoffset1 = int((originY - pointUL['lat']) / pixelWidth)
    xoffset1 = int((pointUL['lon'] - originX) / (-pixelHight))

    # 研究区右下角在DEM矩阵中的位置
    yoffset2 = int((originY - pointDR['lat']) / pixelWidth)
    xoffset2 = int((pointDR['lon'] - originX) / (-pixelHight))

    # 研究区矩阵行列数
    xx = xoffset2 - xoffset1
    yy = yoffset2 - yoffset1
    # 读取研究区内的数据，并计算高程
    DEMRasterData = DEMBand.ReadAsArray(xoffset1, yoffset1, xx, yy)

    MeanAltitude = np.mean(DEMRasterData)
    return MeanAltitude

def Block(IDataSet,SatelliteID,SensorID,Year,atcfiles,config,metedata,outFileName,ScaleFactor):
    # global cols,rows,atcfiles
    cols = IDataSet.RasterXSize
    rows = IDataSet.RasterYSize
    bands = IDataSet.RasterCount
    # SatelliteID = filename_split[0]
    # SensorID = filename_split[1]
    # Year = filename_split[4][:4]

    #设置输出波段
    Driver = IDataSet.GetDriver()
    geoTransform1 = IDataSet.GetGeoTransform()
    ListgeoTransform1 = list(geoTransform1)
    ListgeoTransform1[5] = -ListgeoTransform1[5]
    newgeoTransform1 = tuple(ListgeoTransform1)
    proj1 = IDataSet.GetProjection()

    OutRCname = os.path.join(atcfiles,outFileName)
    if ScaleFactor == 1:
        data_type = gdal.GDT_Float32
    elif ScaleFactor == 10000:
        data_type = gdal.GDT_UInt16
    else:
        data_type = gdal.GDT_UInt32
    outDataset = Driver.Create(OutRCname,cols,rows,4,data_type)
    outDataset.SetGeoTransform(newgeoTransform1)
    outDataset.SetProjection(proj1)
    #分别读取4个波段
    logger.info("读取数据...")
    for band in range(bands):
        m = band+1
        ReadBand = IDataSet.GetRasterBand(m)
        outband = outDataset.GetRasterBand(m)
        outband.SetNoDataValue(-9999)
        logger.info("获取大气校正系数")
        #获取大气校正系数
        AtcCofa, AtcCofb, AtcCofc = AtmosphericCorrection(m,metedata,config,SatelliteID,SensorID)
        nBlockSize = 2048
        i = 0
        j = 0
        b = cols*rows
        #进度条参数
        XBlockcount = math.ceil(cols/nBlockSize)
        YBlockcount = math.ceil(rows/nBlockSize)
        # print("第%d波段校正："%m)
        logger.info("第%d波段校正："%m)
        try:
            with tqdm(total=XBlockcount*YBlockcount,iterable='iterable',desc = '第%i波段:'%m,mininterval=10) as pbar:
            # with tqdm(total=XBlockcount*YBlockcount) as pbar:
                # print(pbar)
                while i<rows:
                    while j <cols:
                        #保存分块大小
                        nXBK = nBlockSize
                        nYBK = nBlockSize

                        #最后不够分块的区域，有多少读取多少
                        if i+nBlockSize>rows:
                            nYBK = rows - i
                        if j+nBlockSize>cols:
                            nXBK=cols - j

                        #分块读取影像
                        Image = ReadBand.ReadAsArray(j,i,nXBK,nYBK)

                        # outImage =np.where(Image>0,Image*Gain + Bias,-9999)
                        outImage = Image
                        y = np.where(outImage!=-9999,AtcCofa * outImage - AtcCofb,-9999)
                        # atcImage = np.where(y!=-9999,(y / (1 + y * AtcCofc))*10000,-9999)
                        atcImage = np.where(y!=-9999,(y / (1 + y * AtcCofc))*ScaleFactor,-9999)
                        atcImage = np.where(atcImage < 0, 0,  atcImage)
                        outband.WriteArray(atcImage,j,i)

                        j=j+nXBK
                        time.sleep(1)
                        pbar.update(1)
                    j=0
                    i=i+nYBK
        except KeyboardInterrupt:
            pbar.close()
            raise
        pbar.close()


# 6s大气校正
def AtmosphericCorrection(BandId,metedata,config,SatelliteID,SensorID):
    #读取头文件
    dom = xml.dom.minidom.parse(metedata)

    # 6S模型
    s = SixS()

    # 传感器类型 自定义
    s.geometry = Geometry.User()
    s.geometry.solar_z = 90-float(dom.getElementsByTagName('SolarZenith')[0].firstChild.data)
    s.geometry.solar_a = float(dom.getElementsByTagName('SolarAzimuth')[0].firstChild.data)
    # s.geometry.view_z = float(dom.getElementsByTagName('SatelliteZenith')[0].firstChild.data)
    # s.geometry.view_a = float(dom.getElementsByTagName('SatelliteAzimuth')[0].firstChild.data)
    s.geometry.view_z = 0
    s.geometry.view_a = 0
    # 日期
    DateTimeparm = dom.getElementsByTagName('CenterTime')[0].firstChild.data
    DateTime = DateTimeparm.split(' ')
    Date = DateTime[0].split('-')
    s.geometry.month = int(Date[1])
    s.geometry.day = int(Date[2])

    # print(s.geometry)
    # 中心经纬度
    TopLeftLat = float(dom.getElementsByTagName('TopLeftLatitude')[0].firstChild.data)
    TopLeftLon = float(dom.getElementsByTagName('TopLeftLongitude')[0].firstChild.data)
    TopRightLat = float(dom.getElementsByTagName('TopRightLatitude')[0].firstChild.data)
    TopRightLon = float(dom.getElementsByTagName('TopRightLongitude')[0].firstChild.data)
    BottomRightLat = float(dom.getElementsByTagName('BottomRightLatitude')[0].firstChild.data)
    BottomRightLon = float(dom.getElementsByTagName('BottomRightLongitude')[0].firstChild.data)
    BottomLeftLat = float(dom.getElementsByTagName('BottomLeftLatitude')[0].firstChild.data)
    BottomLeftLon = float(dom.getElementsByTagName('BottomLeftLongitude')[0].firstChild.data)

    ImageCenterLat = (TopLeftLat + TopRightLat + BottomRightLat + BottomLeftLat) / 4

    # 大气模式类型
    if ImageCenterLat > -15 and ImageCenterLat < 15:
        s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.Tropical)

    if ImageCenterLat > 15 and ImageCenterLat < 45:
        if s.geometry.month > 4 and s.geometry.month < 9:
            s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeSummer)
        else:
            s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.MidlatitudeWinter)

    if ImageCenterLat > 45 and ImageCenterLat < 60:
        if s.geometry.month > 4 and s.geometry.month < 9:
            s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.SubarcticSummer)
        else:
            s.atmos_profile = AtmosProfile.PredefinedType(AtmosProfile.SubarcticWinter)

    # 气溶胶类型大陆
    s.aero_profile = AtmosProfile.PredefinedType(AeroProfile.Continental)

    # 下垫面类型
    s.ground_reflectance = GroundReflectance.HomogeneousLambertian(0.36)

    # 550nm气溶胶光学厚度,对应能见度为40km
    s.aot550 = 0.14497

    # 通过研究去区的范围去求DEM高度。
    pointUL = dict()
    pointDR = dict()
    pointUL["lat"] = max(TopLeftLat,TopRightLat,BottomRightLat,BottomLeftLat)
    pointUL["lon"] = min(TopLeftLon,TopRightLon,BottomRightLon,BottomLeftLon)
    pointDR["lat"] = min(TopLeftLat,TopRightLat,BottomRightLat,BottomLeftLat)
    pointDR["lon"] = max(TopLeftLon,TopRightLon,BottomRightLon,BottomLeftLon)
    meanDEM = (MeanDEM(pointUL, pointDR)) * 0.001

    # 研究区海拔、卫星传感器轨道高度
    s.altitudes = Altitudes()
    s.altitudes.set_target_custom_altitude(meanDEM)
    s.altitudes.set_sensor_satellite_level()

    # 校正波段（根据波段名称）
    if BandId == 1:
        SRFband = config["Parameter"][SatelliteID][SensorID]["SRF"]["1"]
        s.wavelength = Wavelength(0.450,0.520,SRFband)

    elif BandId == 2:
        SRFband = config["Parameter"][SatelliteID][SensorID]["SRF"]["2"]

        s.wavelength = Wavelength(0.520,0.590,SRFband)

    elif BandId == 3:
        SRFband = config["Parameter"][SatelliteID][SensorID]["SRF"]["3"]

        s.wavelength = Wavelength(0.630,0.690,SRFband)

    elif BandId == 4:
        SRFband = config["Parameter"][SatelliteID][SensorID]["SRF"]["4"]
        s.wavelength = Wavelength(0.770,0.890,SRFband)

    s.atmos_corr = AtmosCorr.AtmosCorrLambertianFromReflectance(-0.1)

    # 运行6s大气模型
    s.run()
    xa = s.outputs.coef_xa
    xb = s.outputs.coef_xb
    xc = s.outputs.coef_xc
    # x = s.outputs.values
    return (xa, xb, xc)

def atmomain(inputpath, outputpath, satelliteID, sensorID, imagingYear, scaleFactor):
    config = json.load(open(config_file))

    for root, dirs, files in os.walk(inputpath):
        pass

    for file in files:
        # print(File)
        if file.endswith('.tiff') or file.endswith('.tif'):
            filename = os.path.basename(file)
            fileType = satelliteID[0:2]
            filename_split = filename.split("_")
            if fileType == 'GF':
                GFType = sensorID[0:3]
                inputpath = os.path.join(inputpath, filename)
                outFileName = filename
                atcfiles = os.path.join(outputpath, outFileName.replace('.tiff', ''))

                if GFType == 'WFV':
                    metedata = inputpath.replace('.tiff', '.xml')
                    rpb_file = inputpath.replace('.tiff', '.rpb')

                elif GFType == 'PMS':
                    metedata = inputpath.replace('.tiff', 'MSS.xml')
                    rpb_file = inputpath.replace('.tiff', 'MSS.rpb')

                try:
                    os.mkdir(atcfiles)
                except Exception as e:
                    pass
                logger.info("拷贝依赖文件xml和rpb!!!@{}".format(file))
                # 将头文件和几何校正文件拷贝到大气校正结果文件中
                metedata_basename = os.path.basename(metedata)
                copy_metedata = os.path.join(atcfiles, metedata_basename)
                shutil.copy(metedata, copy_metedata)

                rpb_basename = os.path.basename(rpb_file)
                copy_rpb_file = os.path.join(atcfiles, rpb_basename)
                shutil.copy(rpb_file, copy_rpb_file)

                try:
                    IDataSet = gdal.Open(inputpath)
                except Exception as e:
                    print("文件%S打开失败" % inputpath)

                Block(IDataSet, satelliteID, sensorID, imagingYear, atcfiles, config, metedata, outFileName,
                      scaleFactor)

if __name__ == '__main__':
    pass