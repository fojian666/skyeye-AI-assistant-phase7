import datetime
import hashlib
import socket
import uuid
import zipfile
import os, shutil
import math
import cv2
import numpy as np
import sys
import pandas as pd
from osgeo import osr
from osgeo import gdal, ogr
import json
from pathlib import Path
import os
work_dir = os.path.dirname(os.path.abspath(__file__))
# import config
# BASE_DIR = os.path.dirname(Path(__file__).resolve().parent.parent)
# sys.path.append(BASE_DIR+"//user")
# from django.conf import settings
# import django
# project_directory = BASE_DIR
# if project_directory not in sys.path:
#     sys.path.append(project_directory)
# # 确保 Django 环境被设置
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gtrs_interacting.settings")
# django.setup()
# from user.license_module.generate_license import decryptedfile
# product_id =  settings.PRODUCTID
# filepath = os.path.join(settings.BASE_DIR, f'{product_id}license.lic')
# tagex,msg = decryptedfile(filepath)
# if not tagex:
#     raise Exception(msg)

def convert_seconds(seconds):
    """
    格式化时间戳
    @param seconds:
    @return:
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    # 格式化字符串并返回结果
    time_format = "{:02d}:{:02d}:{:02d}".format(int(hours), int(minutes), int(seconds))
    return hours

def create_text_file(file_dir):
    for i in file_dir:
        file_path = i
        with open(file_path, 'w') as file:
            file.write('0')
        print(f'文本文件 {file_path} 已创建成功。')


def update_status_bar(num, txt_path):
    """
    更新进度条进度百分比,写入log
    Args:
        num: 进度百分比

    Returns:
    """
    with open(txt_path, 'w+') as f:
        f.write(str(num))


def read_logs(target_file):
    try:
        log_path = os.path.join(work_dir, 'logs', target_file)
        with open(log_path, "r") as f:
            value = f.readlines()[0].strip()
    except Exception as e:
        print(e)
        value = '1'
    return value


def read_txt(path):
    """
    读取txt为文件
    Args:
        path: 读取txt文件路径

    Returns:

    """
    with open(path, 'r') as f:
        return f.readline()


def read_log(log_file_path):
    """
    读取log日志
    Args:
        log_file_path: log日志路径

    Returns:读取的最后一行内容

    """
    with open(log_file_path, 'r', encoding='UTF-8') as file:
        lines = file.readlines()

    last_line_list = []
    last_line = ''
    penultimate_line = ''
    i = 0
    for line in reversed(lines):
        if "INFO" in line or "WARNING" in line or "ERROR" in line:
            if i == 0:
                last_line = line
                i += 1
            elif i == 1:
                penultimate_line = '-'.join((line.split('-')[3:])).replace(' ', '').strip()
                break
        else:
            last_line_list.append(line)

    # 将最后一行拼接
    last_line_merge = (''.join(reversed(last_line_list + [last_line])))
    last_line = '-'.join((last_line_merge.split('-')[3:])).replace(' ', '').strip()
    return penultimate_line, last_line

def day_get():
    d = datetime.datetime.now()
    # 通过for 循环得到天数，如果想得到两周的时间，只需要把8改成15就可以了。
    for i in range(0, 7):
        oneday = datetime.timedelta(days=i)
        day = d - oneday
        date_to = datetime.datetime(day.year, day.month, day.day)
        yield str(date_to)[0:10]

def get_recent_seven_day():
    """
    获取最近的七天日期
    @return:
    """
    qq = day_get()
    day_list = []
    for obj in qq:
        day_list.append(obj)
    list_week_day = day_list[::-1]
    return list_week_day

def read_log_lastline(log_file_path):
    """
    读取log日志
    Args:
        log_file_path: log日志路径

    Returns:读取的最后一行内容

    """
    with open(log_file_path, 'r', encoding='UTF-8') as file:
        lines = file.readlines()
    # 获取最后一行日志内容
    last_line = '-'.join((lines[-1].split('-')[3:5])).replace(' ', '').strip()
    return last_line


def read_json_data(json_path):
    """
    读取json数据
    Returns:数据json格式
    """
    if os.path.exists(json_path):
        with open(json_path, encoding='utf-8') as r:
            # 将dict写入名称为r的文件中
            line = r.read()
            if line:
                params = json.loads(line)
            else:
                params = {"data": []}
        return params
    else:
        return {"data": []}


# 写入json文件
def write_json_data(params):
    # 使用写模式，名称定义为r
    # 其中路径如果和读json方法中的名称不一致，会重新创建一个名称为该方法中写的文件名
    # with open('./status.json', 'w', encoding='utf-8') as r:
    with open(config.json_path, 'w', encoding='utf-8') as r:
        # 将dict写入名称为r的文件中
        json.dump(params, r)


def create_shp(csv_path, save_path):
    """
    航线规划 读取csv点文件，创建矢量图层
    :param csv_path:
    :param save_path:
    :return:
    """
    # 读入csv文件信息，设置点几何的字段属性
    csv_df = pd.read_csv(csv_path)
    # 利用.csv文件创建一个点shp文件
    # 获取驱动
    driver = ogr.GetDriverByName('ESRI Shapefile')
    # 创建数据源
    shp_filename = os.path.basename(csv_path)[:-4] + '.shp'
    # 检查数据源是否已存在
    if os.path.exists(os.path.join(save_path, shp_filename)):
        driver.DeleteDataSource(os.path.join(save_path, shp_filename))
    ds = driver.CreateDataSource(os.path.join(save_path, shp_filename))
    # 图层名
    layer_name = os.path.basename(csv_path)[:-4]
    # 定义坐标系对象
    sr = osr.SpatialReference()
    # 使用WGS84地理坐标系
    sr.ImportFromEPSG(4326)
    # 创建点图层, 并设置坐标系
    out_lyr = ds.CreateLayer(layer_name, srs=sr, geom_type=ogr.wkbLineString)
    # 创建图层定义
    # 利用csv文件中有四个字段创建4个属性字段
    # Latitude字段
    lat_fld = ogr.FieldDefn('lat', ogr.OFTReal)
    lat_fld.SetWidth(9)
    lat_fld.SetPrecision(5)
    out_lyr.createfield(lat_fld)
    # Longitude字段
    lon_fld = ogr.FieldDefn('lon', ogr.OFTReal)
    lon_fld.SetWidth(9)
    lon_fld.SetPrecision(5)
    out_lyr.createfield(lon_fld)
    # 从layer中读取相应的feature类型，并创建feature
    featureDefn = out_lyr.GetLayerDefn()
    feature = ogr.Feature(featureDefn)
    # 设定几何形状
    point = ogr.Geometry(ogr.wkbLineString)
    # 读入csv文件信息，设置点几何的字段属性
    for i in range(1, len(csv_df)):
        # 纬度
        feature.SetField('lat', float(csv_df.iloc[i, 1]))
        # 经度
        feature.SetField('lon', float(csv_df.iloc[i, 2]))
        # 设置几何信息部分
        # 利用经纬度创建点， X为经度， Y为纬度
        point.AddPoint(float(csv_df.iloc[i, 2]), float(csv_df.iloc[i, 1]))
        feature.SetGeometry(point)
        # 将feature写入layer
        out_lyr.CreateFeature(feature)
    # 从内存中清除 ds，将数据写入磁盘中
    ds.Destroy()


class Point:
    """点类"""
    x = 0.0
    y = 0.0
    index = 0  # 点在线上的索引

    def __init__(self, x, y, index):
        self.x = x
        self.y = y
        self.index = index


def create_ori_path(path):
    """
    创建文件夹
    @param path:
    @return:
    """
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def create_path(file_path, path=None):
    """
    创建文件夹
    @param file_path:
    @param path:
    @return:
    """
    if not path:
        if isinstance(file_path,str):
            if os.path.exists(file_path):
                shutil.rmtree(file_path)
            os.makedirs(file_path)
        elif isinstance(file_path,list):
            for i in file_path:
                if os.path.exists(i):
                    shutil.rmtree(file_path)
                os.makedirs(i)
        else:
            print("文件类型有问题！")
        return file_path

    else:
        file_path = os.path.join(file_path, path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        return file_path


def walk_file(path, flag):
    file_list = []
    dir_list = []
    for root, dirs, files in os.walk(path):
        if flag == "file":
            files.sort(key=lambda x: int(x.split('.')[0]))
            for f in files:
                file_list.append(os.path.join(root, f))
        if flag == "dir":
            dirs.sort(key=lambda x: int(x))
            for d in dirs:
                dir_list.append(os.path.join(root, d))
    return dir_list, file_list


def walk_file_no_sort(path, flag):
    file_list = []
    dir_list = []
    for root, dirs, files in os.walk(path):
        if flag == "file":
            # files.sort(key=lambda x: int(x.split('.')[0]))
            for f in files:
                file_list.append(os.path.join(root, f))
        if flag == "dir":
            # dirs.sort(key=lambda x: int(x))
            for d in dirs:
                dir_list.append(os.path.join(root, d))
    return dir_list, file_list


def path_to_real_path(path):
    return os.getcwd() + path.split('.')[1]


def path_to_real_path_file(path, file_name):
    return os.getcwd() + path.split('.')[1] + file_name


def time_interval(time_end, time_start):
    seconds = time_end - time_start
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def CheckFileExists(filePath):
    '''
    描述：检查文件路径是否存在
    输入：文件路径
    return：1（存在），0（不存在）
    '''
    if os.path.exists(filePath):
        return 1
    print("文件【%s】不存在！" % filePath)
    return 0


def ReadVectorLayer(strVectorFile):
    '''
    描述：打开shp文件
    输入：shp文件路径
    return：shp数据集
    '''
    driver = ogr.GetDriverByName("ESRI Shapefile")
    ds = driver.Open(strVectorFile, 1)
    if ds == None:
        print("打开文件【%s】失败！" % strVectorFile)
        return 0
    print("打开文件【%s】成功！" % strVectorFile)
    return ds


def ReadVectorMessage(ds):
    '''
    描述：读取shp数据集信息
    输入：shp数据集
    return：空间参考，要素类型（点/线/面），属性表字段集合
    '''
    layer = ds.GetLayer(0)
    lydefn = layer.GetLayerDefn()
    spatialref = layer.GetSpatialRef()
    geomtype = lydefn.GetGeomType()

    fieldlist = []
    for i in range(lydefn.GetFieldCount()):
        fddefn = lydefn.GetFieldDefn(i)
        fddict = {'name': fddefn.GetName(), 'type': fddefn.GetType(),
                  'width': fddefn.GetWidth(), 'decimal': fddefn.GetPrecision()}
        fieldlist += [fddict]

    return (spatialref, geomtype, fieldlist)

def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = config.ipp
    finally:
        s.close()
    return ip.replace('.', '-')

def CreateVectorFile(strVectorFile, sourceData):
    '''
    描述：新建shp文件
    输入：新建shp文件的路径，文件信息（空间参考，要素类型，属性字段集合）
    return：新建的shp数据集
    '''
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
    spatialref, geomtype, fieldlist = sourceData

    driver = ogr.GetDriverByName("ESRI Shapefile")
    DeleteVectorFile(driver, strVectorFile)
    ds = driver.CreateDataSource(strVectorFile)
    # print(os.path.basename(strVectorFile)[:-4])
    layer = ds.CreateLayer(os.path.basename(strVectorFile), srs=spatialref, geom_type=geomtype)
    for fd in fieldlist:
        field = ogr.FieldDefn(fd['name'], fd['type'])
        if 'width' in fd:
            field.SetWidth(fd['width'])
        if 'decimal' in fd:
            field.SetPrecision(fd['decimal'])
        layer.createfield(field)

    return ds


def CreateLayer(strVectorFile, ds, sourceData):
    spatialref, geomtype, fieldlist = sourceData
    layer = ds.CreateLayer(strVectorFile, srs=spatialref, geom_type=geomtype)
    for fd in fieldlist:
        field = ogr.FieldDefn(fd['name'], fd['type'])
        if 'width' in fd:
            field.SetWidth(fd['width'])
        if 'decimal' in fd:
            field.SetPrecision(fd['decimal'])
        layer.createfield(field)

    return ds


def CreatePtVectorFile(strVectorFile, sourceData):
    '''
    描述：新建点shp文件
    输入：新建的点shp文件的路径，文件信息（空间参考，要素类型，属性字段集合）
    return：新建的点shp数据集（不带属性字段）
    '''
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
    spatialref, geomtype, fieldlist = sourceData

    driver = ogr.GetDriverByName("ESRI Shapefile")
    DeleteVectorFile(driver, strVectorFile)
    ds = driver.CreateDataSource(strVectorFile)
    layer = ds.CreateLayer(os.path.basename(strVectorFile)[:-4], srs=spatialref, geom_type=ogr.wkbPoint)

    return ds


def DeleteVectorFile(driver, strVectorFile):
    '''
    描述：删除shp文件
    输入：文件驱动，shp文件路径
    '''
    try:
        if os.path.exists(strVectorFile):
            driver.DeleteDataSource(strVectorFile)
    except Exception as e:
        print("删除文件【%s】失败！" % strVectorFile)
        print("ERROR:", e)


# 新建要素（无属性）
def CreateGemetry(ds, polygon):
    layer = ds.GetLayer(0)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(polygon)
    layer.CreateFeature(feature)


# 道格拉斯平滑
def compress(p1, p2, points, deleteIds):
    D = 3
    swichvalue = False
    # 一般式直线方程系数 A*x+B*y+C=0,利用点斜式,分母可以省略约区
    # A=(p1.y-p2.y)/math.sqrt(math.pow(p1.y-p2.y,2)+math.pow(p1.x-p2.x,2))
    A = (p1.y - p2.y)
    # B=(p2.x-p1.x)/math.sqrt(math.pow(p1.y-p2.y,2)+math.pow(p1.x-p2.x,2))
    B = (p2.x - p1.x)
    # C=(p1.x*p2.y-p2.x*p1.y)/math.sqrt(math.pow(p1.y-p2.y,2)+math.pow(p1.x-p2.x,2))
    C = (p1.x * p2.y - p2.x * p1.y)

    m = points.index(p1)
    n = points.index(p2)
    distance = []

    middle = None

    if (n == m + 1):
        return
    # 计算中间点到直线的距离
    for i in range(m + 1, n):
        d = abs(A * points[i].x + B * points[i].y + C) / math.sqrt(math.pow(A, 2) + math.pow(B, 2))
        distance.append(d)

    dmax = max(distance)
    # print(dmax)

    if dmax > D:
        swichvalue = True
    else:
        swichvalue = False
    if (not swichvalue):
        for i in range(m + 1, n):
            # print(i)
            deleteIds.append(i)
            # del points[i]
    else:
        for i in range(m + 1, n):
            if (abs(A * points[i].x + B * points[i].y + C) / math.sqrt(math.pow(A, 2) + math.pow(B, 2)) == dmax):
                middle = points[i]
        compress(p1, middle, points, deleteIds)
        compress(middle, p2, points, deleteIds)

    return deleteIds


def Ring2Pts(ring):
    pts = []
    ptCount = ring.GetPointCount()
    for i in range(ptCount):
        if i != ptCount - 1:
            pts.append(Point(ring.GetX(i), ring.GetY(i), i))
    return pts


def Pts2Polygon(pts):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for i in pts:
        ring.AddPoint(i.x, i.y)
    ring.CloseRings()
    return ring


def upload_shp(namespace, datastore_name, fpname, host):
    """
        上传shp文件至geoserver
        :param fpname: 文件路径
        :param datastore_name: 数据存储名称
        :param host: geoserver服务器地址:端口
        :param namespace:工作空间命名
        :return:
    """
    try:
        # 创建工作空间
        # os.system(
        #    'curl -v -u admin:geoserver -X POST -H "Content-type: text/xml" -d "<workspace><name>' + namespace + '</name></workspace>" http://'+ host + '/geoserver/rest/workspaces')

        # 新建图层，上传shapefile
        # 一次只能打包一个shp，否则只能上传最后一个
        os.system(
            'curl -u admin:geoserver -X PUT -H "Content-type: application/zip" --data-binary @' + fpname + ' http://' + host + '/geoserver/rest/workspaces/' + namespace + '/datastores/' + datastore_name + '/file.shp')
        print("上传完毕")
    except Exception as e:
        print("上传失败：" + str(e))


def left_pic(image_path):
    if not os.path.exists(image_path):
        raise ValueError('文件不存在！')
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    try:
        height, width, channel = image.shape
        alpha_channel = image[:, :, 3]
        _, mask = cv2.threshold(alpha_channel, 254, 255, cv2.THRESH_BINARY)  # binarize mask
        color = image[:, :, :3]
        new_img = cv2.bitwise_not(cv2.bitwise_not(color, mask=mask))
        for i in range(height):
            for j in range(width):
                b, g, r = new_img[j, i]
                if int(b) + int(g) + int(r) != 765:
                    del new_img
                    return i, j
        else:
            return height, width
    except Exception as e:
        print(e)
        return height, width


def top_pic(image_path):
    if not os.path.exists(image_path):
        raise ValueError('文件不存在！')
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    try:
        height, width, channel = image.shape
        alpha_channel = image[:, :, 3]
        _, mask = cv2.threshold(alpha_channel, 254, 255, cv2.THRESH_BINARY)  # binarize mask
        color = image[:, :, :3]
        new_img = cv2.bitwise_not(cv2.bitwise_not(color, mask=mask))
        for i in range(height):
            for j in range(width):
                b, g, r = new_img[i, j]
                if int(b) + int(g) + int(r) != 765:
                    del new_img
                    return i, j
        else:
            return height, width
    except Exception as e:
        print(e)
        return height, width


def bottom_pic(image_path):
    if not os.path.exists(image_path):
        raise ValueError('文件不存在！')
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    try:
        height, width, channel = image.shape
        alpha_channel = image[:, :, 3]
        _, mask = cv2.threshold(alpha_channel, 254, 255, cv2.THRESH_BINARY)  # binarize mask
        color = image[:, :, :3]
        new_img = cv2.bitwise_not(cv2.bitwise_not(color, mask=mask))
        img180 = np.rot90(new_img, 2)
        for i in range(height):
            for j in range(width):
                b, g, r = img180[i, j]
                if int(b) + int(g) + int(r) != 765:
                    del img180
                    return i, j
        else:
            return height, width
    except Exception as e:
        print(e)
        return height, width


def right_pic(image_path):
    if not os.path.exists(image_path):
        raise ValueError('文件不存在！')
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    try:
        height, width, channel = image.shape
        alpha_channel = image[:, :, 3]
        _, mask = cv2.threshold(alpha_channel, 254, 255, cv2.THRESH_BINARY)  # binarize mask
        color = image[:, :, :3]
        new_img = cv2.bitwise_not(cv2.bitwise_not(color, mask=mask))
        img180 = np.rot90(new_img, 2)
        for i in range(height):
            for j in range(width):
                b, g, r = img180[j, i]
                if int(b) + int(g) + int(r) != 765:
                    del img180
                    return i, j
        else:
            return height, width
    except Exception as e:
        print(e)
        return height, width


def unzip(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        try:
            fz = zipfile.ZipFile(zip_src, 'r')
            for file in fz.namelist():
                print(file)
                fz.extract(file, dst_dir)
        except:
            return {'error': 'Zip File Error', 'message': 'extract zip file failed'}
    else:
        return {'error': 'Zip File Error', 'message': 'zip file damaged or not zip file'}


def encrypt_password(passwd):
    """
    md5加密用户密码
    :param passwd:
    :return:
    """
    # 创建md5对象
    m = hashlib.md5()
    b = passwd.encode(encoding='utf-8')
    m.update(b)
    str_md5 = m.hexdigest()
    return str_md5


flag = False  # flag为True代表是地理经纬度坐标,为false代表平面投影坐标


# =============================================================================
# 	基于python GDAL配准
# =============================================================================
def registration(input_path, out_path, top_left, bottom_right, ik, jk, srs):
    gdal_sieve(str(input_path))
    # 打开栅格文件
    dataset = gdal.Open(input_path, gdal.GA_Update)

    geo_trans = dataset.GetGeoTransform()
    if geo_trans[5] > 0:
        top_left = [top_left[0], top_left[1]]
        bottom_right = [bottom_right[0], -bottom_right[1]]
        top_right = [bottom_right[0], -top_left[1]]
        bottom_left = [-top_left[0], bottom_right[1]]
    else:
        top_right = [bottom_right[0], top_left[1]]
        bottom_left = [top_left[0], bottom_right[1]]
    # 构造控制点列表 gcps_list
    x = dataset.RasterXSize
    y = dataset.RasterYSize

    gcps_list = [gdal.GCP(top_left[0], top_left[1], 0, 0, 0),
                 gdal.GCP(top_right[0], top_right[1], 0, x - jk, 0),
                 gdal.GCP(bottom_left[0], bottom_left[1], 0, 0, y - ik),
                 gdal.GCP(bottom_right[0], bottom_right[1], 0, x - jk, y - ik)]

    # 设置空间参考
    spatial_reference = osr.SpatialReference()
    '''
    if flag:
        spatial_reference.SetWellKnownGeogCS('WGS84')
    else:
        spatial_reference.SetWellKnownGeogCS('CGCS2000')
    '''
    # 添加控制点
    # dataset.SetGCPs(gcps_list, spatial_reference.ExportToWkt())
    dataset.SetGCPs(gcps_list, srs)
    # tps校正 重采样:最邻近法
    dst_ds = gdal.Warp(out_path, dataset, format='GTiff', tps=True, width=x, height=y,
                       resampleAlg=gdal.GRIORA_NearestNeighbour)
    return out_path


# =============================================================================
# 	基于python GDAL栅格滤波
# =============================================================================
def gdal_sieve(src_filename, threshold=10):
    # 4表示对角像素不被视为直接相邻用于多边形成员资格，8表示对角像素不相邻
    connectedness = 4
    gdal.AllRegister()
    dataset = gdal.Open(src_filename, gdal.GA_Update)
    if dataset is None:
        sys.exit(1)
    # 获取需要处理的源栅格波段
    src_band = dataset.GetRasterBand(1)
    mask_band = src_band.GetMaskBand()
    dst_band = src_band
    prog_func = gdal.TermProgress_nocb
    # 调用gdal滤波函数
    result = gdal.SieveFilter(src_band, mask_band, dst_band, threshold, connectedness, callback=prog_func)
    src_ds = None


def registration_change(input_path, out_path, top_left, bottom_right, ik, jk, srs):
    gdal_sieve(input_path)
    # 打开栅格文件
    dataset = gdal.Open(input_path, gdal.GA_Update)
    # 构造控制点列表 gcps_list
    x = dataset.RasterXSize
    y = dataset.RasterYSize
    top_right = [bottom_right[0], top_left[1]]
    bottom_left = [top_left[0], bottom_right[1]]
    gcps_list = [gdal.GCP(top_left[0], top_left[1], 0, 0, 0),
                 gdal.GCP(top_right[0], top_right[1], 0, x - jk, 0),
                 gdal.GCP(bottom_left[0], bottom_left[1], 0, 0, y - ik),
                 gdal.GCP(bottom_right[0], bottom_right[1], 0, x - jk, y - ik)]
    # 设置空间参考
    spatial_reference = osr.SpatialReference()
    # if flag:
    #     spatial_reference.SetWellKnownGeogCS('WGS84')
    # else:
    #     spatial_reference.SetWellKnownGeogCS('CGCS2000')
    # 添加控制点
    dataset.SetGCPs(gcps_list, spatial_reference)
    # tps校正 重采样:最邻近法
    dst_ds = gdal.Warp(out_path, dataset, format='GTiff', tps=True, width=x, height=y,
                       resampleAlg=gdal.GRIORA_NearestNeighbour)
    return out_path


def get_uuid():
    """
    获取不重复的8位随机数
    :return:
    """
    number_lists = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    number_id = str(uuid.uuid4()).replace("-", '')  # 注意这里需要用uuid4
    buffer = []
    for i in range(0, 8):
        start = i * 4
        end = i * 4 + 4
        val = int(number_id[start:end], 16)
        buffer.append(number_lists[val % 10])
    return "".join(buffer)


def pretty_xml(element, indent, newline, level=0):
    """
    格式化xml文件(缩进,换行)
    :param element: elemnt为传进来的Elment类
    :param indent: indent用于缩进
    :param newline: newline用于换行
    :param level:
    :return:
    """
    if element:  # 判断element是否有子元素
        if (element.text is None) or element.text.isspace():  # 如果element的text没有内容
            element.text = newline + indent * (level + 1)
        else:
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)
            # element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * level
    temp = list(element)  # 将element转成list
    for subelement in temp:
        if temp.index(subelement) < (len(temp) - 1):  # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致
            subelement.tail = newline + indent * (level + 1)
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个
            subelement.tail = newline + indent * level
        pretty_xml(subelement, indent, newline, level=level + 1)  # 对子元素进行递归操作


def create_log(request, account, values, text):
    user_ip = request.META.get('REMOTE_ADDR')
    text = account + text
    from applications.models import Log
    Log.objects.create(account=account,type=values,msg=text,ipaddr=user_ip)
