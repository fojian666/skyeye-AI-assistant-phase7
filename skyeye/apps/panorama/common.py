import datetime
import hashlib
import json
import math
import re
import socket
import uuid
import zipfile
import numpy as np
import sys
import os
from io import BytesIO
from geopy.distance import great_circle
import pandas as pd
import requests
import xmltodict
from PIL import Image, ImageDraw, ImageFont
import simplekml
import geopandas as gpd

import django
import exifread
# from osgeo import ogr
from shapely.geometry import Point
from pyproj import CRS
import shutil
from osgeo import ogr


# from django.conf import settings
# 确保 Django 环境被设置
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gtus.settings")
# django.setup()
# from apps.panorama.generate_license import decryptedfile

# work_dir = os.path.dirname(os.path.abspath(__file__))
# filepath = os.path.join(settings.BASE_DIR, f'license.lic')
# tagex, msg = decryptedfile(filepath)
# print("软件许可校验情况：", tagex, msg)
# if not tagex:
#     # raise Exception(msg)
#     sys.exit(1)


def find_village_by_point(shapefile_path, lat, lon):
    """
    查找给定经纬度坐标点所在的村庄。

    :param shapefile_path: 村界 Shapefile 文件的路径
    :param lat: 经度坐标
    :param lon: 纬度坐标
    :return: 包含该点的村庄的 DataFrame 行，如果未找到则返回 None
    """
    try:
        # 创建一个点几何对象
        point = Point(lon, lat)
        # 读取 Shapefile 文件
        if os.path.exists(shapefile_path):
            villages_gdf = gpd.read_file(shapefile_path)
            # 使用 GeoDataFrame 的 spatial join 方法来查找包含该点的多边形
            # 这里使用了 `within` 方法，该方法返回 True 如果点位于多边形内
            result = villages_gdf[villages_gdf.geometry.contains(point)]
            if not result.empty:
                r = result.iloc[0]
                address = r['NAME']
                return address
            else:
                return '未查询到地址信息'
        return '未查询到地址信息'
    except Exception as e:
        print(e)
        return '未查询到地址信息'


def calculate_date_ranges(start_date, end_date, interval_days):
    """
    计算给定开始日期、结束日期和间隔天数的日期批次。
    参数:
    start_date (str): 开始日期，格式为'YYYY-MM-DD'。
    end_date (str): 结束日期，格式为'YYYY-MM-DD'。
    interval_days (int): 间隔天数。
    返回:
    list of tuples: 包含每个批次开始日期和结束日期的列表。
    """
    # start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    # end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    date_ranges = []
    current_start = start_date
    while current_start + datetime.timedelta(days=interval_days) <= end_date:
        current_end = current_start + datetime.timedelta(days=interval_days) - datetime.timedelta(days=1)
        if current_end > end_date:
            current_end = end_date
        date_ranges.append(
            {'start_date': current_start.strftime('%Y-%m-%d'), "end_date": current_end.strftime('%Y-%m-%d')})
        # 更新当前批次的开始日期
        current_start += datetime.timedelta(days=interval_days)
    # 处理最后一个批次可能超过结束日期的情况
    # if current_start <= end:
    #    date_ranges.append({'start_date': current_start.strftime('%Y-%m-%d'), "end_date": end.strftime('%Y-%m-%d')})
    return date_ranges


def shp_to_kml(shp_path, output_dir):
    """
    将全景点位shp文件转换为kml文件。
    @param shp_path:
    @param kml_path:
    @return:
    """

    gdf = gpd.GeoDataFrame.from_file(shp_path)
    grouped = gdf.groupby('WGNAME')
    # 遍历每个组，并创建KML文件
    for wgname, group_df in grouped:
        kml = simplekml.Kml()
        # 为当前组中的每一行创建一个点
        for index, row in group_df.iterrows():
            kml.newpoint(name=row.name, coords=[(row.geometry.x, row.geometry.y)])
        # 保存KML文件
        kml_file_path = os.path.join(output_dir, f'{wgname}.kml')
        kml.save(kml_file_path)
    return wgname


def read_grid_shp2(shp_file_path):
    """
    读取网格员shp文件（使用GDAL/OGR替代geopandas）
    @param shp_file_path: shp文件完整路径（支持中文路径）
    @return: 包含网格员信息的列表
    """
    # 1. 校验文件是否存在
    if not os.path.exists(shp_file_path):
        raise FileNotFoundError(f"SHP文件不存在：{shp_file_path}")

    # 2. 打开SHP数据集（只读模式）
    ds = ogr.Open(shp_file_path, 0)
    if ds is None:
        raise RuntimeError(f"无法打开SHP文件，请检查文件完整性或权限：{shp_file_path}")

    # 3. 获取第一个图层（SHP文件默认只有一个图层）
    layer = ds.GetLayer(0)
    layer_def = layer.GetLayerDefn()  # 获取图层字段定义

    # 4. 定义需要提取的字段及对应别名，与原函数字段一一对应
    field_mapping = {
        "grid_operator": "WGYNAME",  # 网格员姓名
        "center_x": "ZXDX",  # 网格中心X坐标
        "center_y": "ZXDY",  # 网格中心Y坐标
        "grid_name": "WGNAME",  # 网格名称
        "street": "JDNAME",  # 街道名称
        "street_id": "JDID"  # 街道ID
    }

    # 5. 校验字段是否存在，获取字段索引
    field_index = {}
    missing_fields = []
    for alias, field_name in field_mapping.items():
        idx = layer_def.GetFieldIndex(field_name)
        if idx == -1:
            missing_fields.append(field_name)
        else:
            field_index[alias] = idx

    # 字段缺失时抛出异常，提示用户
    if missing_fields:
        raise ValueError(f"SHP文件缺少必要字段：{missing_fields}，请检查数据结构")

    # 6. 遍历所有要素，提取属性数据
    data = []
    for feat in layer:
        # 提取每个字段的值
        record = {
            alias: feat.GetField(idx) for alias, idx in field_index.items()
        }
        data.append(record)

        # 释放要素资源（避免内存泄漏）
        feat.Destroy()

    # 7. 释放数据集资源
    ds.Destroy()
    return data


def read_grid_shp(shp_file_path):
    """
    读取网格员shp文件
    @param shp_file_path:
    @return:
    """
    gdf = gpd.read_file(shp_file_path)
    data = []
    for index, row in gdf.iterrows():
        print(row)
        center_x = row['ZXDX']
        center_y = row['ZXDY']
        grid_name = row['WGNAME']
        street = row['WGNAME']
        street_id = row['JDID']
        record = {
            "grid_operator": '',
            "center_x": center_x,
            "center_y": center_y,
            "grid_name": grid_name,
            "street": street,
            "street_id": street_id
        }
        data.append(record)
    print(data)
    return data


def read_point_shp(shp_file_path):
    """
    读取全景点位shp文件（使用GDAL/OGR替代geopandas）
    @param shp_file_path: shp文件路径
    @return: 包含点位信息的列表
    """
    # 打开shp文件
    ds = ogr.Open(shp_file_path, 0)  # 0=只读模式
    if ds is None:
        raise FileNotFoundError(f"无法打开SHP文件：{shp_file_path}")

    layer = ds.GetLayer(0)
    # 获取字段索引
    field_index = {
        "PointX": layer.GetLayerDefn().GetFieldIndex("PointX"),
        "PointY": layer.GetLayerDefn().GetFieldIndex("PointY"),
        "WGNAME": layer.GetLayerDefn().GetFieldIndex("WGNAME"),
        "JDNAME": layer.GetLayerDefn().GetFieldIndex("JDNAME"),
        "JDID": layer.GetLayerDefn().GetFieldIndex("JDID")
    }
    # 校验字段
    missing_fields = [k for k, v in field_index.items() if v == -1]
    if missing_fields:
        raise ValueError(f"SHP文件缺少必要字段：{missing_fields}")

    data = []
    # 遍历要素
    for feat in layer:
        record = {
            "center_x": feat.GetField(field_index["PointX"]),
            "center_y": feat.GetField(field_index["PointY"]),
            "grid_name": feat.GetField(field_index["WGNAME"]),
            "street": feat.GetField(field_index["JDNAME"]),
            "street_id": feat.GetField(field_index["JDID"])
        }
        data.append(record)
        # 释放要素资源
        feat.Destroy()

    # 释放数据集资源
    ds.Destroy()
    return data


def read_point_shp2(shp_file_path):
    """
    读取全景点位shp文件
    @param shp_file_path:
    @return:
    """
    gdf = gpd.read_file(shp_file_path)
    data = []
    for index, row in gdf.iterrows():
        center_x = row['PointX']
        center_y = row['PointY']
        grid_name = row['WGNAME']
        street = row['JDNAME']
        street_id = row['JDID']
        record = {
            "center_x": center_x,
            "center_y": center_y,
            "grid_name": grid_name,
            "street": street,
            "street_id": street_id
        }
        data.append(record)
    return data


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


def time_interval(time_end, time_start):
    seconds = time_end - time_start
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


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
        ip = '-'
    finally:
        s.close()
    return ip.replace('.', '-')


def unzip(zip_src, dst_dir):
    r = zipfile.is_zipfile(zip_src)
    if r:
        try:
            fz = zipfile.ZipFile(zip_src, 'r')
            for file in fz.namelist():
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


def get_decimal_from_dms(dms, ref):
    """从度分秒转换为十进制度数"""
    degrees = dms.values[0].num / dms.values[0].den
    minutes = dms.values[1].num / dms.values[1].den / 60.0
    seconds = dms.values[2].num / dms.values[2].den / 3600.0

    if ref in ['S', 'W']:
        return -(degrees + minutes + seconds)
    else:
        return degrees + minutes + seconds


def get_coordinates(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)
    """从 EXIF 数据中提取经纬度"""
    lat = None
    lon = None

    gps_latitude = tags.get('GPS GPSLatitude')
    gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
    gps_longitude = tags.get('GPS GPSLongitude')
    gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

    if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
        lat = round(get_decimal_from_dms(gps_latitude, gps_latitude_ref.values), 4)
        lon = round(get_decimal_from_dms(gps_longitude, gps_longitude_ref.values), 4)
    # 检查是否存在GPS高度信息
    if 'GPS GPSAltitude' in tags:
        altitude = tags['GPS GPSAltitude']
        altitude_value = str(altitude).strip()
        altitude_value = altitude_value.split(' ')[0]
        try:
            numerator, denominator = map(int, altitude_value.split('/'))
            altitude_float = numerator / denominator
            gps_height = altitude_float
        except ValueError:
            gps_height = float(altitude_value)
    else:
        gps_height = 0
    return lat, lon, gps_height


def get_yaw_degree2(image_path):
    img = Image(image_path)
    xmp_info = img.read_xmp()
    gimbalYawDegree = xmp_info['Xmp.drone-dji.GimbalYawDegree']
    relativeAltitude = xmp_info['Xmp.drone-dji.RelativeAltitude']
    y = img.read_exif()
    flightYawDegree = str(gimbalYawDegree).replace('+', '')
    return flightYawDegree, relativeAltitude


def get_yaw_degree(image_path):
    """
    获取全景图的yaw和真实的高度
    Args:
        image_path: 图片路径

    Returns:yaw值，真实高度

    """
    with open(image_path, 'rb')as fileobj:
        contents = fileobj.read()
    start_positions = [m.start() for m in re.finditer(b"<?xpacket begin=", contents)]
    xmp_packet_index = 0
    start = start_positions[xmp_packet_index] - 2
    end = contents.index(b"</x:xmpmeta>", start) + 12
    value = contents[start:end]
    value = value.decode('utf-8')
    v = xmltodict.parse(value)
    gimbalYawDegree = v['x:xmpmeta']['rdf:RDF']['rdf:Description']['@drone-dji:GimbalYawDegree']
    relativeAltitude = v['x:xmpmeta']['rdf:RDF']['rdf:Description']['@drone-dji:RelativeAltitude']
    flightYawDegree = str(gimbalYawDegree).replace('+', '')
    relativeAltitude = str(relativeAltitude).replace('+', '')
    return flightYawDegree, relativeAltitude


def get_unique_filename(dest_dir, original_filename):
    """
    辅助函数：生成目标目录中不重复的文件名（避免覆盖）
    :param dest_dir: 目标目录
    :param original_filename: 原始文件名（如 "photo.jpg"）
    :return: 不重复的目标文件路径（如 "dest_dir/photo(1).jpg"）
    """
    # 拆分文件名和后缀（如 "photo.jpg" → ("photo", ".jpg")）
    base_name, ext = os.path.splitext(original_filename)
    counter = 1
    # 初始目标路径（用原始文件名）
    target_path = os.path.join(dest_dir, original_filename)

    # 循环检查：若文件已存在，在文件名后加序号（如 "photo(1).jpg"）
    while os.path.exists(target_path):
        unique_filename = f"{base_name}({counter}){ext}"
        target_path = os.path.join(dest_dir, unique_filename)
        counter += 1
    return target_path


def safe_unzip(zip_file_path, dest_dir):
    """
    安全解压ZIP文件：嵌套文件夹的图片统一存入目标根目录（无二级目录）
    :param zip_file_path: 待解压的ZIP文件路径
    :param dest_dir: 解压目标根目录
    :raises Exception: 解压过程中的异常（如文件损坏、权限不足）
    """
    # 1. 确保目标根目录存在（不存在则创建）
    os.makedirs(dest_dir, exist_ok=True)
    # 2. 校验目标目录绝对路径（防范ZIP Slip攻击）
    dest_dir_abs = os.path.abspath(dest_dir)

    # 3. 定义需要处理的图片格式（可根据需求扩展）
    SUPPORTED_IMAGE_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

    # 4. 打开ZIP文件并遍历所有压缩项
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for zip_member in zip_ref.infolist():
            zip_member_name = zip_member.filename  # 压缩项原始路径（如 "folder1/sub/photo.jpg"）

            # -------------------------- 关键修改1：筛选图片文件 + 跳过目录 --------------------------
            # 跳过目录项（不需要创建二级目录）
            if zip_member.is_dir():
                continue
            # 仅处理后缀匹配的图片文件（忽略大小写）
            if not zip_member_name.lower().endswith(SUPPORTED_IMAGE_EXTS):
                continue  # 非图片文件跳过

            # -------------------------- 关键修改2：剥离目录结构 + 处理文件名重复 --------------------------
            # 提取纯文件名（去掉嵌套路径，如 "folder1/sub/photo.jpg" → "photo.jpg"）
            pure_filename = os.path.basename(zip_member_name)
            # 生成目标目录中不重复的文件路径（避免覆盖）
            target_path_abs = get_unique_filename(dest_dir_abs, pure_filename)

            # -------------------------- 关键修改3：校验路径安全 + 写入文件 --------------------------
            # 防范ZIP Slip：确保目标路径在根目录内（双重保险）
            if not target_path_abs.startswith(dest_dir_abs + os.sep):
                continue

            # 写入图片文件到目标根目录（无需创建二级目录，因dest_dir已存在）
            with zip_ref.open(zip_member) as source_file, \
                    open(target_path_abs, 'wb') as target_file:
                # 分块写入（优化大图片处理，避免内存占用过高）
                while chunk := source_file.read(1024 * 1024):  # 1MB/块
                    target_file.write(chunk)

            print(f"已提取图片：{zip_member_name} → {os.path.relpath(target_path_abs, dest_dir_abs)}")


def unzip_file(zip_save_path, unzip_dir_path):
    """
    解压zip文件：解决编码问题
    """
    r = zipfile.is_zipfile(zip_save_path)
    if r:
        try:
            with zipfile.ZipFile(file=zip_save_path, mode='r') as zf:
                # 解压到指定⽬录,⾸先创建⼀个解压⽬录
                if os.path.exists(unzip_dir_path) is False:
                    os.mkdir(unzip_dir_path)
                for old_name in zf.namelist():
                    # 获取⽂件⼤⼩，⽬的是区分⽂件夹还是⽂件，如果是空⽂件应该不好⽤。
                    file_size = zf.getinfo(old_name).file_size
                    # 由于源码遇到中⽂是cp437⽅式，所以解码成gbk，windows即可正常
                    new_name = old_name.encode('cp437').decode('gbk')
                    # 拼接⽂件的保存路径
                    new_path = os.path.join(unzip_dir_path, new_name)
                    # 判断⽂件是⽂件夹还是⽂件
                    if file_size > 0:
                        # 是⽂件，通过open创建⽂件，写⼊数据
                        with open(file=new_path, mode='wb') as f:
                            # zf.read 是读取压缩包⾥的⽂件内容
                            f.write(zf.read(old_name))
                    else:
                        # 是⽂件夹，就创建
                        os.mkdir(new_path)
        except:
            fz = zipfile.ZipFile(zip_save_path, 'r')
            fz.extractall(unzip_dir_path)
        return True
    else:
        print('This is not zip')
        return False


def image_to_latlon(lat, lon, h, yaw, pitch, north_offset):
    """
    将 yaw 和 pitch 转换为弧度
    Args:
        lat:纬度
        lon: 经度
        h: 高度
        yaw: yaw值
        pitch:
        north_offset: 偏向角

    Returns:

    """
    yaw_rad = math.radians(float(yaw) + float(north_offset))
    pitch_rad = math.radians(90 - abs(pitch))

    # 计算D时需要考虑 pitch 的范围
    if pitch == -90 or pitch == 90:
        # 当 pitch 为 ±90 度时，垂直方向正对上下，不存在水平偏移
        delta_lat = 0
        delta_lon = 0
    else:
        # 否则，按照正常方法计算
        # 计算到目标点的水平距离 D
        # 计算水平距离：d = h / tan(|pitch|)
        print(f"h:{h},pitch_rad:{pitch_rad},type:{type(h), type(pitch_rad)}")
        horizontal_distance = h * math.tan(pitch_rad)

        dE = horizontal_distance * math.sin(yaw_rad)
        dN = horizontal_distance * math.cos(yaw_rad)

        R = 6378137
        delta_lat = dN / R * (180 / math.pi)
        delta_lon = dE / (R * math.cos(math.radians(lat))) * (180 / math.pi)

    final_lat = lat + delta_lat
    final_lon = lon + delta_lon

    return final_lat, final_lon


def interpolate_polygon(polygon, step_size=10e-5):
    """
    使用固定步长对多边形点进行加密（增加点数）。
    :param polygon: 多边形点列表 [(lat1, lon1), (lat2, lon2), ...]
    :param step_size: 目标步长（约 1e-5 表示 1 米，5e-5 表示 5 米）
    :return: 加密后的多边形点列表
    """
    new_points = []
    for i in range(len(polygon) - 1):
        lat1, lon1 = polygon[i]
        lat2, lon2 = polygon[i + 1]
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        num_steps = max(1, int(dist / 10))  # 直接使用计算距离的步数
        lats = np.linspace(lat1, lat2, num_steps)
        lons = np.linspace(lon1, lon2, num_steps)
        new_points.extend(zip(lats, lons))
    return new_points


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    计算两点之间的球面距离（单位：米），使用 Haversine 公式。
    """
    R = 6371000  # 地球半径（单位：米）
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def geodetic_to_spherical(lat, lon, alt, ref_lat, ref_lon, ref_alt):
    """
    将经纬度坐标转换为球面坐标（相对无人机）。
    """
    d = haversine_distance(ref_lat, ref_lon, lat, lon)
    bearing = np.arctan2(np.radians(lon - ref_lon), np.radians(lat - ref_lat))
    x = d * np.cos(bearing)
    y = d * np.sin(bearing)
    z = alt - ref_alt  # 相对高度
    return x, y, z


def compute_yaw_pitch(lat, lon, drone_lat, drone_lon, drone_alt, north_offset):
    """
    计算每个点相对于无人机的 yaw 和 pitch。
    """
    x, y, z = geodetic_to_spherical(lat, lon, 0, drone_lat, drone_lon, drone_alt)
    yaw = np.degrees(np.arctan2(y, x)) - north_offset  # 计算方位角
    pitch = np.degrees(np.arctan2(z, np.sqrt(x ** 2 + y ** 2)))  # 计算俯仰角
    return yaw, pitch


def calculate_distances(point, points_list, threshold=20):
    """
    计算给定点与一组点之间的距离，并返回距离及其对应的点。
    参数:
        point (tuple): 给定的经纬度坐标点，格式为 (latitude, longitude)。
        points_list (list of tuples): 一组经纬度坐标点列表，每个点也是 (latitude, longitude) 格式。
        threshold (int/float): 距离阈值，单位米，默认20米
     返回:
    tuple: 距离最近的点及其距离。
    """

    min_distance = float('inf')
    closest_point = None
    for p in points_list:
        point_id = p['point_id']
        lon_lat = p['point']
        distance = great_circle(point, lon_lat).meters  # 计算两点之间的距离（米）
        if distance < min_distance:
            min_distance = distance
            closest_point = point_id
    # 判断最小距离是否超过阈值
    if min_distance > threshold:
        return None, None
    return closest_point, min_distance


# 监测图斑关联全景图/俯视图的最大距离（米）
POLYGON_LINK_MAX_DISTANCE_M = 20


def find_nearest_point_id(latitude, longitude, county='', max_distance=POLYGON_LINK_MAX_DISTANCE_M):
    """
    根据经纬度查找最近全景点 point_id。
    若最近全景点距离超过 max_distance（默认 100 米），则不关联。
    max_distance=None 时不限制距离。
    """
    from apps.panorama.models import PointLocation

    point_qs = PointLocation.objects.all()
    if county:
        county_name = county.split('(')[0]
        point_qs = point_qs.filter(grid__county__contains=county_name)

    nearest_point_id = ''
    min_distance = float('inf')
    for point in point_qs:
        if not point.latitude or not point.longitude:
            continue
        distance = great_circle(
            (latitude, longitude),
            (point.latitude, point.longitude)
        ).meters
        if distance < min_distance:
            min_distance = distance
            nearest_point_id = point.point_id

    if not nearest_point_id:
        return '', None
    if max_distance is not None and min_distance > max_distance:
        return '', None
    return nearest_point_id, min_distance


def calculate_distances2(point, points_list, threshold=100):
    """
    计算给定点与一组点之间的距离，并返回距离及其对应的点。
    参数:
        point (tuple): 给定的经纬度坐标点，格式为 (latitude, longitude)。
        points_list (list of tuples): 一组经纬度坐标点列表，每个点也是 (latitude, longitude) 格式。
        threshold (int/float): 距离阈值，单位米，默认20米
     返回:
    tuple: 距离最近的点及其距离。
    """

    min_distance = float('inf')
    closest_point = None
    for p in points_list:
        point_id = p['point_id']
        lon_lat = p['point']
        distance = great_circle(point, lon_lat).meters  # 计算两点之间的距离（米）
        if distance < min_distance:
            min_distance = distance
            closest_point = point_id
    # 判断最小距离是否超过阈值
    if min_distance > threshold:
        return None, None
    return closest_point, min_distance


def draw_picture(filePath, result_list, save_path):
    """
    根据框绘制结果图片
    :param fileName:图片名
    :param response_data:检测结果json
    :return:
    """
    img = Image.open(filePath)
    draw = ImageDraw.Draw(img)
    count = 1
    for i in result_list:
        position = i["position"]
        text = i["className"]
        draw.rectangle(xy=(position[0], position[1], position[2], position[3]), fill=None,
                       outline=(255, 0, 0), width=2)
        im = Image.new('RGBA', (80, 16), (255, 0, 0))
        draw_table = ImageDraw.Draw(im=im)
        draw_table.text(xy=(1, 1), text=text, fill='black',
                        font=ImageFont.truetype(os.path.join(settings.BASE_DIR, 'static/font/msyh.ttf'), 12))
        img.paste(im, (position[0], position[1] - 14))
        count += 1
    img_buffer = BytesIO()
    img = img.convert('RGB')
    if filePath.endswith('png') or filePath.endswith('PNG'):
        img.save(img_buffer, format='png')
    else:
        img.save(img_buffer, format='jpeg')
    img = img.convert('RGB')
    img.save(save_path)
    print("检测结果已保存至" + save_path)


def get_geometry_coordinates(data_source_path):
    """
    获取矢量面的坐标
    :param data_source_path:
    :return:
    """
    # 打开数据源
    ds = ogr.Open(data_source_path, 1)  # 1 表示以只读模式打开
    if ds is None:
        print("Failed to open dataset")
        return

    # 获取第一个图层
    layer = ds.GetLayer()
    if layer is None:
        print("No layers found in the dataset")
        return
    polygon_lists = []
    # 遍历图层中的所有要素
    for feature in layer:
        geometry = feature.GetGeometryRef()
        if geometry is None:
            continue  # 如果几何对象为空，跳过当前循环
        d = []
        for i in range(geometry.GetGeometryCount()):
            iring = geometry.GetGeometryRef(i)
            ptCount = iring.GetPointCount()
            for i in range(ptCount):
                if i != ptCount - 1:
                    d.append([iring.GetY(i), iring.GetX(i)])
        polygon_lists.append(d)
    return polygon_lists


def get_epsg_code(crs):
    """智能获取EPSG代码（支持CGCS2000/WGS84的.prj自定义定义）"""
    if crs is None:
        return None

    # 情况1：已经是EPSG代码
    if hasattr(crs, 'to_epsg'):
        epsg = crs.to_epsg()
        if epsg is not None:
            return epsg

    # 情况2：解析WKT字符串
    crs_wkt = str(crs).lower()

    # 匹配CGCS2000（EPSG:4490）
    if 'china_geodetic' in crs_wkt or 'cgcs2000' in crs_wkt:
        return 4490

    # 匹配WGS84（EPSG:4326）
    if 'wgs_1984' in crs_wkt or 'wgs84' in crs_wkt:
        return 4326

    # 其他情况尝试强制转换
    try:
        return CRS(crs).to_epsg()
    except:
        return None


def get_point_buffer_gd_geoserver(point, geoserver_url, workspace, layer_name):
    """
    获取点700米缓冲区内的耕地范围（GeoServer版本）
    参数：
    point (tuple): 点的坐标[x,y]，应与GeoServer数据坐标系一致
    geoserver_url (str): GeoServer WFS服务地址，如：http://localhost:8080/geoserver/wfs
    workspace (str): 工作空间名称
    layer_name (str): 图层名称

    返回：
    list: 700米缓冲区内的耕地图层坐标，或错误信息字符串
    """
    try:
        # 构建WFS请求URL
        wfs_url = f"{geoserver_url}?service=WFS&version=1.1.0&request=GetFeature"
        wfs_url += f"&typeName={workspace}:{layer_name}&outputFormat=application/json"

        # 获取要素数据
        response = requests.get(wfs_url, timeout=20)

        if response.status_code != 200:
            print(f"  GeoServer数据获取失败，状态码: {response.status_code}")
            return f"GeoServer数据获取失败: {response.status_code}"

        features = response.json()
        feature_count = len(features['features'])
        print(f"  获取到 {feature_count} 个要素")

        # 将GeoJSON转换为GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(features['features'])

        # 从GeoJSON中获取坐标系信息
        if 'crs' in features:
            crs_info = features['crs']
            if crs_info['type'] == 'name':
                crs_name = crs_info['properties']['name']
                # 提取EPSG代码
                if 'EPSG:' in crs_name:
                    epsgcode = 4326
                else:
                    # 如果没有明确EPSG，默认使用WGS84
                    epsgcode = 4326
            else:
                epsgcode = 4326
        else:
            # 如果没有CRS信息，默认使用WGS84
            epsgcode = 4326

        gdf.crs = f"EPSG:{epsgcode}"
        print(f"  数据坐标系: EPSG:{epsgcode}")

        # 允许的坐标系（WGS84或CGCS2000）
        allowed_geographic = [4326, 4490]  # WGS84和CGCS2000的EPSG代码

        # 检查是否为允许的坐标系
        if epsgcode not in allowed_geographic:
            return "错误：数据服务坐标系必须是WGS84或CGCS2000"

        # 创建点几何对象
        point_geom = Point(point)

        # 投影到CGCS2000 3度带坐标系(EPSG:4528)进行距离计算
        target_crs = 'EPSG:4528'
        gdf_projected = gdf.to_crs(target_crs)
        point_projected = gpd.GeoSeries([point_geom], crs=gdf.crs).to_crs(target_crs)[0]

        # 创建700米缓冲区
        buffer = point_projected.buffer(700)

        # 提取缓冲区内的耕地
        cropland_in_buffer = gdf_projected[gdf_projected.intersects(buffer)]

        # 转换回原始坐标系
        if not cropland_in_buffer.empty:
            cropland_in_buffer = cropland_in_buffer.to_crs(gdf.crs)

        # 将每个多边形的坐标转换为 [[[x1,y1],[x2,y2],...]] 格式
        coordinates_list = []
        for geom in cropland_in_buffer.geometry:
            if geom.geom_type == 'Polygon':
                # 多边形坐标（包括外环和可能的孔洞）
                coords = list(geom.exterior.coords)
                coordinates_list.append([[x, y] for x, y in coords])
            elif geom.geom_type == 'MultiPolygon':
                # 多部分多边形（逐个处理）
                for poly in geom.geoms:
                    coords = list(poly.exterior.coords)
                    coordinates_list.append([[x, y] for x, y in coords])

        print(f"  找到 {len(coordinates_list)} 个缓冲区内的耕地要素")
        return coordinates_list

    except Exception as e:
        print(f"  获取缓冲区数据报错，报错内容是: {e}")
        return f"数据处理错误：{str(e)}"


def get_point_buffer_gd_geoserver2(point, geoserver_url, workspace, layer_name):
    """
    获取点700米缓冲区内的耕地范围（GeoServer版本 - 服务端过滤优化）

    参数：
    point (tuple): 点的坐标[x,y]，应与GeoServer数据坐标系一致
    geoserver_url (str): GeoServer WFS服务地址
    workspace (str): 工作空间名称
    layer_name (str): 图层名称

    返回：
    list: 700米缓冲区内的耕地图层坐标，或错误信息字符串
    """
    # 创建点几何对象
    point_geom = Point(point)

    # 获取原始数据的坐标系
    # 先获取单个要素来确定坐标系
    test_url = f"{geoserver_url}?service=WFS&version=1.1.0&request=GetFeature"
    test_url += f"&typeName={workspace}:{layer_name}&outputFormat=application/json&maxFeatures=1"

    test_response = requests.get(test_url, timeout=20)
    if test_response.status_code != 200:
        return f"GeoServer数据获取失败: {test_response.status_code}"

    test_features = test_response.json()
    if 'crs' in test_features:
        crs_name = test_features['crs']['properties']['name']
        if 'EPSG:' in crs_name:
            epsgcode = int(crs_name.split(':')[-1])
        else:
            epsgcode = 4326
    else:
        epsgcode = 4326

    # 允许的坐标系
    allowed_geographic = [4326, 4490]
    print(f"  数据坐标系: EPSG:{epsgcode}")

    # 步骤1：将点投影到目标投影坐标系（EPSG:4528）创建缓冲区
    target_crs = 'EPSG:4528'

    # 创建临时GeoDataFrame用于坐标转换
    temp_gdf = gpd.GeoDataFrame(geometry=[point_geom], crs=f"EPSG:{epsgcode}")
    point_projected = temp_gdf.to_crs(target_crs).geometry[0]

    # 创建700米缓冲区（投影坐标系下单位是米）
    buffer_projected = point_projected.buffer(700)

    # 将缓冲区转换回原始坐标系用于WFS查询
    buffer_gdf = gpd.GeoDataFrame(geometry=[buffer_projected], crs=target_crs)
    buffer_original_crs = buffer_gdf.to_crs(f"EPSG:{epsgcode}").geometry[0]

    # 步骤2：构建WFS查询，使用空间过滤只返回缓冲区内的要素
    # 获取缓冲区的边界框
    minx, miny, maxx, maxy = buffer_original_crs.bounds

    # 构建CQL_FILTER空间过滤条件
    # 方法1：使用BBOX过滤（先粗筛）
    bbox_filter = f"BBOX(the_geom, {minx},{miny},{maxx},{maxy})"

    # 方法2：使用INTERSECTS精确过滤（需要知道几何字段名，通常是the_geom或geom）
    # 获取几何字段名（从测试数据中推断）
    if test_features['features']:
        geom_field = None
        props = test_features['features'][0]['geometry']
        # 通常几何字段名是 'the_geom' 或 'geom'
        geom_field = 'the_geom'  # GeoServer默认几何字段名

    # 将缓冲区转换为WKT格式用于查询
    from shapely import wkt
    buffer_wkt = buffer_original_crs.wkt

    # 使用CQL_FILTER进行空间查询
    cql_filter = f"INTERSECTS(the_geom, {buffer_wkt})"

    # 构建WFS请求URL（使用服务端过滤）
    wfs_url = f"{geoserver_url}?service=WFS&version=1.1.0&request=GetFeature"
    wfs_url += f"&typeName={workspace}:{layer_name}"
    wfs_url += f"&outputFormat=application/json"
    wfs_url += f"&CQL_FILTER={cql_filter}"  # 关键：服务端过滤
    # 可选：添加BBOX进一步优化性能
    # wfs_url += f"&BBOX={minx},{miny},{maxx},{maxy}"

    print(f"  执行服务端空间查询...")
    response = requests.get(wfs_url, timeout=30)

    if response.status_code != 200:
        print(f"  GeoServer查询失败，状态码: {response.status_code}")
        return f"GeoServer查询失败: {response.status_code}"

    features = response.json()
    feature_count = len(features['features'])
    print(f"  服务端过滤后获取到 {feature_count} 个要素")

    if feature_count == 0:
        print("  缓冲区范围内没有耕地图斑")
        return []

    # 将GeoJSON转换为GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(features['features'])
    gdf.crs = f"EPSG:{epsgcode}"

    # 将每个多边形的坐标转换为所需格式
    coordinates_list = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            coords = list(geom.exterior.coords)
            coordinates_list.append([[x, y] for x, y in coords])
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                coords = list(poly.exterior.coords)
                coordinates_list.append([[x, y] for x, y in coords])

    print(f"  找到 {len(coordinates_list)} 个缓冲区内的耕地要素")
    return coordinates_list


def get_point_buffer_gd(point, iserver_url, datasource_name, datasets_name):
    """
    获取点700米缓冲区内的耕地范围

    参数：
    point (tuple): 点的坐标[x,y]，应与iServer数据服务坐标系一致
    iserver_url (str): SuperMap iServer数据服务地址
    返回：
    list: 700米缓冲区内的耕地图层，或错误信息字符串
    """
    # 获取坐标系信息
    coor_query = f"{iserver_url}/datasources/{datasource_name}/datasets/{datasets_name}.json"
    coor_response = requests.get(coor_query)

    if coor_response.status_code != 200:
        print(f"请求服务{coor_query}坐标系获取失败，跳过服务")

    coor_data = coor_response.json()
    epsgcode = coor_data['datasetInfo']['prjCoordSys']['epsgCode']

    # 获取要素数据
    query_url = f"{iserver_url}/datasources/{datasource_name}/datasets/{datasets_name}/features.geojson"
    response = requests.get(query_url, params={
        "returnContent": "true",
        "fromIndex": 0,
        "toIndex": -1
    }, timeout=20)

    if response.status_code != 200:
        print(f"  数据获取失败，跳过服务")

    features = response.json()
    feature_count = len(features['features'])
    print(f"  获取到 {feature_count} 个要素")
    # 将GeoJSON转换为GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(features['features'])

    gdf.crs = f"EPSG:{epsgcode}"

    # 允许的坐标系（WGS84或CGCS2000）
    allowed_geographic = [4326, 4490]  # WGS84和CGCS2000的EPSG代码

    # 检查是否为允许的坐标系
    if epsgcode not in allowed_geographic:
        return "错误：数据服务坐标系必须是WGS84或CGCS2000"

    # 创建点几何对象
    point_geom = Point(point)

    # 投影到CGCS2000 3度带坐标系(EPSG:4528)
    target_crs = 'EPSG:4528'
    gdf_projected = gdf.to_crs(target_crs)
    point_projected = gpd.GeoSeries([point_geom], crs=gdf.crs).to_crs(target_crs)[0]

    # 创建700米缓冲区
    buffer = point_projected.buffer(700)

    # 提取缓冲区内的耕地
    cropland_in_buffer = gdf_projected[gdf_projected.intersects(buffer)]

    # 转换回原始坐标系
    if not cropland_in_buffer.empty:
        cropland_in_buffer = cropland_in_buffer.to_crs(gdf.crs)

    # 将每个多边形的坐标转换为 [[[x1,y1],[x2,y2],...]] 格式
    coordinates_list = []
    for geom in cropland_in_buffer.geometry:
        if geom.geom_type == 'Polygon':
            # 多边形坐标（包括外环和可能的孔洞）
            coords = list(geom.exterior.coords)
            coordinates_list.append([[x, y] for x, y in coords])
        elif geom.geom_type == 'MultiPolygon':
            # 多部分多边形（逐个处理）
            for poly in geom.geoms:
                coords = list(poly.exterior.coords)
                coordinates_list.append([[x, y] for x, y in coords])
    print(coordinates_list)
    return coordinates_list

    # except Exception as e:
    #     print("获取缓冲区数据报错，报错内容是:",e)
    #     return f"数据处理错误：{str(e)}"


def create_path(file_path, path=None):
    """
    创建文件夹
    @param file_path:
    @param path:
    @return:
    """
    if not path:
        if isinstance(file_path, str):
            if os.path.exists(file_path):
                shutil.rmtree(file_path)
            os.makedirs(file_path)
        elif isinstance(file_path, list):
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


def create_text_file(file_dir):
    for i in file_dir:
        file_path = i
        with open(file_path, 'w') as file:
            file.write('0')
        print(f'文本文件 {file_path} 已创建成功。')


def ip_connect_log(log_path, ip_address):
    """
    创建对应节点的状态信息文件
    Args:
        log_path:文件创建路径
    Returns:建立后的节点状态txt文件

    """
    status_num_txt_path = os.path.join(log_path, ip_address)
    create_text_file([status_num_txt_path])
    return status_num_txt_path


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


def zip_folder(folder_path, output_zip):
    """
    打包整个文件夹到ZIP
    :param folder_path: 要打包的文件夹路径
    :param output_zip: 输出的ZIP文件路径
    """
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # 在ZIP中保持相对路径结构
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                zipf.write(file_path, arcname)
    print(f"成功打包: {output_zip}")


def export_combined_data2(service_list, point_coord, outpath, test_point_coord):
    """
    将服务列表、点坐标、输出路径和测试点坐标作为参数，将服务列表中的每个服务与点坐标进行缓冲区分析，判断点是否在服务中的面当中。
    Args:
        service_list: 服务列表
        point_coord: 全景点坐标
        outpath: 输出路径
        test_point_coord: 线索点坐标

    Returns:

    """
    # 初始化结果容器
    combined_gdf = gpd.GeoDataFrame()
    intersecting_services = []  # 存储与测试点相交的服务名称
    print(f"全景点数据{point_coord},线索点数据{test_point_coord}")
    # 创建查询点
    point_gdf = gpd.GeoDataFrame(geometry=[Point(point_coord)], crs=CRS.from_epsg(4326))
    point_gdf.to_file(os.path.join(outpath, "query_point.shp"))
    test_point = Point(test_point_coord)
    test_point_gdf = gpd.GeoDataFrame(geometry=[test_point], crs=CRS.from_epsg(4326))
    test_point_gdf.to_file(os.path.join(outpath, "test_point_gdf.shp"))
    result = []
    # 遍历所有服务
    for service in service_list:
        try:
            # 首先查询坐标系
            coor_query = f"{service['url']}/datasources/{service['datasource_name']}/datasets/{service['datasets_name']}.json"
            coor_response = requests.get(coor_query)
            if coor_response.status_code == 200:
                coor_data = coor_response.json()
                epsgcode = coor_data['datasetInfo']['prjCoordSys']['epsgCode']
                # 构建查询URL
                query_url = f"{service['url']}/datasources/{service['datasource_name']}/datasets/{service['datasets_name']}/features.geojson"
                # 发送请求
                response = requests.get(query_url, params={
                    "returnContent": "true",
                    "fromIndex": 0,
                    "toIndex": -1
                }, timeout=20)

                if response.status_code == 200:
                    features = response.json()
                    print(f"服务 {service['datasets_name']} 找到 {len(features['features'])} 个要素")
                    if epsgcode == 4326 or epsgcode == 4490:  # 地理坐标系
                        if epsgcode == 4326:
                            target_crs = 'EPSG:4528'
                        else:
                            target_crs = 'EPSG:4549'

                        buffer = point_gdf.to_crs(target_crs).buffer(700)
                        buffer_gdf = gpd.GeoDataFrame(geometry=buffer, crs=target_crs)
                        buffer_gdf.to_file(os.path.join(outpath, "buffer_zone.shp"))
                        # 转换为GeoDataFrame
                        temp_gdf = gpd.GeoDataFrame.from_features(features['features'], crs=CRS.from_epsg(epsgcode))
                        temp_gdf.to_file(os.path.join(outpath, "temp_gdf.shp"), encoding='utf-8')
                        # 添加服务标识列
                        temp_gdf['service_name'] = service['datasets_name']  # 添加服务名称标识
                        # 空间查询（在投影坐标系下执行）
                        temp_projected = temp_gdf.to_crs(target_crs)
                        temp_projected.to_file(os.path.join(outpath, "temp_projected.shp"), encoding='utf-8')
                        selected = temp_projected[temp_projected.intersects(buffer.iloc[0])]
                        selected.to_file(os.path.join(outpath, "selected.shp"), encoding='utf-8')
                        if not selected.empty:
                            # 转换回WGS84并添加到合并结果
                            combined_gdf = gpd.GeoDataFrame(
                                pd.concat([combined_gdf, selected.to_crs('EPSG:{}'.format(epsgcode))],
                                          ignore_index=True)
                            )
                            # 检查测试点是否与该服务数据相交
                            service_data = selected.to_crs('EPSG:{}'.format(epsgcode))
                            service_data.to_file(os.path.join(outpath, "service_data.shp"), encoding='utf-8')
                            if service_data.geometry.intersects(test_point).any():
                                intersecting_services.append(service['datasets_name'])
                                result.append(service['data_type'][0:2])
                                print(f"服务 {service['datasets_name']} 与测试点相交")
                    else:
                        crs = CRS.from_epsg(epsgcode)
                        if crs.is_projected:  # 说明是投影坐标系
                            geographic_crs = crs.geodetic_crs
                            jude_epsgcode = geographic_crs.to_epsg()
                            if jude_epsgcode == 4326 or jude_epsgcode == 4490:  # 系统支持
                                buffer = point_gdf.to_crs('EPSG:{}'.format(epsgcode)).buffer(700)
                                buffer_gdf = gpd.GeoDataFrame(geometry=buffer, crs='EPSG:{}'.format(epsgcode))
                                buffer_gdf.to_file(os.path.join(outpath, "buffer_zone.shp"))
                                # 转换为GeoDataFrame
                                temp_gdf = gpd.GeoDataFrame.from_features(features['features'],
                                                                          crs=CRS.from_epsg(epsgcode))
                                temp_gdf.to_file(os.path.join(outpath, "temp_gdf.shp"), encoding='utf-8')
                                # 添加服务标识列
                                temp_gdf['service_name'] = service['datasets_name']  # 添加服务名称标识
                                # 空间查询（在投影坐标系下执行）
                                selected = temp_gdf[temp_gdf.intersects(buffer.iloc[0])]
                                selected.to_file(os.path.join(outpath, "selected.shp"), encoding='utf-8')
                                if not selected.empty:
                                    # 转换回WGS84并添加到合并结果
                                    combined_gdf = gpd.GeoDataFrame(
                                        pd.concat(
                                            [combined_gdf, selected.to_crs('EPSG:{}'.format(geographic_crs.to_epsg()))],
                                            ignore_index=True)
                                    )
                                    # 检查测试点是否与该服务数据相交
                                    service_data = selected.to_crs('EPSG:{}'.format(geographic_crs.to_epsg()))
                                    if service_data.geometry.intersects(test_point).any():
                                        intersecting_services.append(service['datasets_name'])
                                        result.append(service['data_type'][0:2])
                                        print(f"服务 {service['datasets_name']} 与测试点相交")
                        else:
                            print("不是系统支持的坐标系，不进行过滤!!!")

            else:
                print("未获取到数据坐标系，不进行过滤!!!")
        except Exception as e:
            print(f"处理服务 {service['datasets_name']} 时出错: {str(e)}")
            continue
    return result


def export_combined_data(service_list, point_coord, outpath, alarms):
    """
    处理单个全景点与多个测试点：对全景点进行缓冲区分析，判断每个测试点是否在服务面中。

    Args:
        service_list: 服务列表
        point_coord: 单个全景点坐标 (x, y)
        outpath: 输出路径
        alarms: 多个测试点坐标列表 [(x1,y1), (x2,y2), ...]

    Returns:
        results: 每个测试点对应的服务类型结果列表 [[type1, type2], [type3], ...]
    """
    print(f"全景点数据: {point_coord}, 点位数量: {len(alarms)}")

    # 创建全景点GeoDataFrame
    point_gdf = gpd.GeoDataFrame(geometry=[Point(point_coord)], crs=CRS.from_epsg(4326))

    # 准备结果容器
    all_results = []
    service_cache = {}  # 缓存服务数据，避免重复请求

    # 遍历所有服务
    for service in service_list:
        service_name = service['datasets_name']
        print(f"\n处理服务: {service_name}")

        try:
            # 获取坐标系信息
            coor_query = f"{service['url']}/datasources/{service['datasource_name']}/datasets/{service_name}.json"
            coor_response = requests.get(coor_query)

            if coor_response.status_code != 200:
                print(f"  坐标系获取失败，跳过服务")
                continue

            coor_data = coor_response.json()
            epsgcode = coor_data['datasetInfo']['prjCoordSys']['epsgCode']

            # 获取要素数据
            query_url = f"{service['url']}/datasources/{service['datasource_name']}/datasets/{service_name}/features.geojson"
            response = requests.get(query_url, params={
                "returnContent": "true",
                "fromIndex": 0,
                "toIndex": -1
            }, timeout=20)

            if response.status_code != 200:
                print(f"  数据获取失败，跳过服务")
                continue

            features = response.json()
            feature_count = len(features['features'])
            print(f"  获取到 {feature_count} 个要素")

            # 创建服务GeoDataFrame
            service_gdf = gpd.GeoDataFrame.from_features(features['features'], crs=CRS.from_epsg(epsgcode))
            service_gdf['service_name'] = service_name

            # 处理地理坐标系 (4326/4490)
            if epsgcode in (4326, 4490):
                target_crs = 'EPSG:4528' if epsgcode == 4326 else 'EPSG:4549'

                # 创建缓冲区
                buffer = point_gdf.to_crs(target_crs).buffer(700)

                # 投影转换
                service_projected = service_gdf.to_crs(target_crs)

                # 空间查询 - 获取缓冲区内的服务要素
                selected = service_projected[service_projected.intersects(buffer.iloc[0])]

                if not selected.empty:
                    # 转换回WGS84并缓存
                    service_cache[service_name] = selected.to_crs('EPSG:4326')
                    print(f"  找到 {len(selected)} 个要素在缓冲区内")
                else:
                    print(f"  没有要素在缓冲区内")

            # 处理投影坐标系
            else:
                crs = CRS.from_epsg(epsgcode)
                if not crs.is_projected:
                    print(f"  非常用坐标系，跳过服务")
                    continue

                # 创建缓冲区
                buffer = point_gdf.to_crs(f'EPSG:{epsgcode}').buffer(700)

                # 空间查询 - 获取缓冲区内的服务要素
                selected = service_gdf[service_gdf.intersects(buffer.iloc[0])]

                if not selected.empty:
                    # 转换回WGS84并缓存
                    service_cache[service_name] = selected.to_crs('EPSG:4326')
                    print(f"  找到 {len(selected)} 个要素在缓冲区内")
                else:
                    print(f"  没有要素在缓冲区内")

        except Exception as e:
            print(f"  处理服务时出错: {str(e)}")
            continue

    # 处理每个测试点
    print("\n处理测试点...")
    for alarm in alarms:
        test_point = Point([alarm['longitude'], alarm['latitude']])
        point_result = set()
        # 检查每个服务的缓存数据
        for service_name, service_data in service_cache.items():
            # 判断测试点是否在服务要素中
            if service_data.geometry.intersects(test_point).any():
                # 获取服务类型前缀
                service_type = next(
                    (s['data_type'][:2] for s in service_list
                     if s['datasets_name'] == service_name),
                    '??'
                )
                point_result.add(service_type)
                print(f"√ 与 {service_name} 相交 ({service_type})")
        alarm['szdl'] = list(point_result)
        all_results.append(alarm)
    return all_results


def frame_area_remove(shp_path, alarms):
    """
    根据不检测区域剔除线索点
    Args:
        shp_path:
        alarms:

    Returns:

    """
    # 读取SHP文件
    gdf = gpd.read_file(shp_path)
    # GeoPandas创建空间索引
    sindex = gdf.sindex
    new_result = []
    for alarm in alarms:
        # 先通过空间索引获取可能的候选多边形
        point = Point(alarm['longitude'], alarm['latitude'])
        possible_matches_index = list(sindex.intersection(point.bounds))
        possible_matches = gdf.iloc[possible_matches_index]
        # 再精确判断
        exact_match = possible_matches[possible_matches.contains(point)]
        if exact_match.empty:
            print(f"点 {alarm} 不在多边形内")
            new_result.append(alarm)
    return new_result


if __name__ == '__main__':
    shp_to_kml(r'E:\02prjs\gtus\static\shp\水湖镇全景点\SHZ_QJD.shp', r'E:\02prjs\gtus\static\kml\SHZQJD')
    # result = get_point_buffer_gd([119.182285644, 32.2042089914], r'E:\ltgd\ltgd.shp')
    # print(result)
    # get_geoserver_center()
