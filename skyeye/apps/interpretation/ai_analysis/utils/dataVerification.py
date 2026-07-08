import os.path
from osgeo import osr,gdal
import re
import sys
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,WORK_DIR)
sys.path.insert(0,os.path.dirname(WORK_DIR))
import apps.interpretation.ai_config as cg
datasize = cg.dataSize

def data_verify(tif_path):
    """
    数据校验
    包括数据坐标系的判定，数据行列号判定
    :param tif_path:tif数据
    return:epsg为0,么有坐标系，为1，是投影坐标系，为4326是WGS_1984；为4490是CGCS2000，反之不支持
    """
    # 读取 TIFF 文件
    dataset = gdal.Open(tif_path)
    epsg = 0
    rasterXSize = dataset.RasterXSize
    rasterYSize = dataset.RasterYSize
    # 获取数据的坐标参考系统
    spatial_ref = osr.SpatialReference()
    projection = dataset.GetProjection()
    if projection:
        spatial_ref.ImportFromWkt(dataset.GetProjection())

        # 判断是投影坐标系还是地理坐标系
        coord_sys_type = "投影坐标系" if spatial_ref.IsProjected() else "地理坐标系"

        if coord_sys_type == "地理坐标系":
            # 获取地理坐标系的名称
            datum_name = spatial_ref.GetAttrValue("DATUM")

            # 判断是 WGS 84 还是 CGCS 2000
            if re.search(r'WGS_1984', datum_name, re.IGNORECASE):
                epsg =  4326
            elif re.search(r'CGCS2000', datum_name, re.IGNORECASE):
                epsg =  4490
            elif re.search(r'China_2000', datum_name, re.IGNORECASE):
                epsg =  4490
            else:
                print("无法确定地理坐标系的具体名称")
        else:
            epsg = 1
            print("该数据使用的是投影坐标系")
    dataset = None  # 关闭数据集

    # 数据校验
    tifinfo = {"dataMessage": '数据名称{}'.format(tif_path),'is_largedata':0,'is_errorEpsg':0}
    if rasterXSize > datasize or rasterYSize > datasize:
        tifinfo['dataMessage'] = '数据{}--范围过大,可能导致结果失败'.format(os.path.basename(tif_path))
        tifinfo['is_largedata'] += 1
    if not projection:
        tifinfo['dataMessage'] = tifinfo['dataMessage'] + '--数据无坐标信息'
    tifinfo['epsg'] = epsg
    if epsg == 0:
        tifinfo['is_errorEpsg'] += 1
    tifinfo['rasterXSize'] = rasterXSize
    tifinfo['rasterYSize'] = rasterYSize
    return tifinfo

# data_verify(r'E:\geo_ai_server\c#_test_data\result\7\SV1-01_20171021_L2A0000192762_1109170051408_01-.tif')