import glob
import json
import os
import time
import urllib
import uuid
import zipfile

import requests
from xml.etree import ElementTree as ET
import xmltodict
from django.http import JsonResponse
from rest_framework_jwt.utils import jwt_decode_handler
from apps.system.models import SysLog, User


def find_shp_from_folder(folder):
    """快速查找.shp文件"""
    shp_files = glob.glob(os.path.join(folder, "*.shp"))
    return shp_files[0] if shp_files else None


def get_center(layer_url):
    """获取iServer影像服务中心点
    :@ param: layer_url 影像URL地址
    :@ return: center 中心点信息 例:[35.73,118.92]
    :@ return: srs 坐标系  例: 4326
    """
    headers = {
        'user-agent': 'Mozilla / 5.0(Windows NT 10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 111.0.0.0Safari / 537.36',
        # "cookie": "JSESSIONID=4625592BAD7BDD37FCA4BD6DF60636F8",
    }
    resp = requests.get(url=layer_url + '.json', headers=headers).json()
    srs = resp['prjCoordSys']['epsgCode']
    center_x = float(resp['center']['x'])
    center_y = float(resp['center']['y'])
    center = [center_y, center_x]
    return center, srs


def get_geoserver_center(geoserver_url, workspace, layer_name):
    """
       获取GeoServer WMS服务中地图的中心点

       参数:
       geoserver_url: GeoServer WMS服务的GetCapabilities地址

       返回:
       中心点坐标 (经度, 纬度) 或 None（如果获取失败）
       """
    try:
        # 构建GetCapabilities请求URL
        params = {
            'service': 'WMS',
            'version': '1.3.0',
            'request': 'GetCapabilities'
        }

        # 发送请求
        response = requests.get(geoserver_url, params=params)
        response.raise_for_status()  # 检查请求是否成功

        # 解析XML响应
        root = ET.fromstring(response.content)

        # 注册命名空间
        namespaces = {
            'wms': 'http://www.opengis.net/wms',
            'xlink': 'http://www.w3.org/1999/xlink'
        }

        # 查找第一个图层的边界框
        # 注意：这里获取的是第一个图层的中心点，您可能需要根据图层名称特定获取
        layers = root.findall('.//wms:Layer', namespaces)
        target_layer = None

        for layer in layers:
            # 查找图层名称元素
            name_element = layer.find('wms:Name', namespaces)
            if name_element is not None and name_element.text == layer_name:
                target_layer = layer
                break
        if target_layer is not None:
            # 查找EX_GeographicBoundingBox
            geo_bbox = target_layer.find('.//wms:EX_GeographicBoundingBox', namespaces)
            if geo_bbox is not None:
                west = float(geo_bbox.find('wms:westBoundLongitude', namespaces).text)
                east = float(geo_bbox.find('wms:eastBoundLongitude', namespaces).text)
                south = float(geo_bbox.find('wms:southBoundLatitude', namespaces).text)
                north = float(geo_bbox.find('wms:northBoundLatitude', namespaces).text)

                # 计算中心点
                center_lon = (west + east) / 2
                center_lat = (south + north) / 2

                return [center_lon, center_lat], 4326

        # 如果找不到EX_GeographicBoundingBox，尝试查找BoundingBox
        bbox = target_layer.find('.//wms:BoundingBox', namespaces)
        if bbox is not None:
            # 获取CRS
            crs = bbox.attrib.get('CRS', 4326)

            # 获取边界坐标
            minx = float(bbox.attrib.get('minx', 0))
            maxx = float(bbox.attrib.get('maxx', 0))
            miny = float(bbox.attrib.get('miny', 0))
            maxy = float(bbox.attrib.get('maxy', 0))

            # 计算中心点
            center_x = (minx + maxx) / 2
            center_y = (miny + maxy) / 2

            return [center_y, center_x], crs

        return []
    except Exception as e:
        print(f"发生错误: {e}")
        return []


def get_arcgis_center(layer_url):
    """
    获取Arcgis影像服务中心点
    :@ param layer_url:
    :@ return: center 中心点信息 例:[35.73,118.92]
    :@ return: srs 坐标系  例: 4326
    """
    layer_url = layer_url.split("/WMTS")[0] + "?f=json"
    document = urllib.request.urlopen(layer_url).read()
    data = json.loads(document)
    # 左上、右下坐标统一格式
    loc = data["fullExtent"]
    left_top = [loc["xmin"], loc["ymin"]]
    right_bottom = [loc["xmax"], loc["ymax"]]
    center_x = (left_top[0] + right_bottom[0]) / 2
    center_y = (right_bottom[1] + left_top[1]) / 2
    srs = loc["spatialReference"]["wkid"]
    center = [center_y, center_x]
    return center, srs


# 登录认证装饰器
def login_request(func):
    def wrapper(request, *args, **kwargs):
        jwt_value = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        if jwt_value:
            try:
                token_user = jwt_decode_handler(jwt_value)
                username = token_user['username']
                if username:
                    request.session['username'] = username
                    request.session['user_id'] = token_user['user_id']
                    current_user = User.objects.get(id=token_user['user_id'])
                    request.session['role'] = current_user.role
                    request.session['county'] = current_user.county
                    # request.user = current_user
                    return func(request, *args, **kwargs)
                else:
                    return JsonResponse({'msg': '登录过期！', 'code': 405})
            except Exception as e:
                print(e)
                return JsonResponse({'msg': '登录过期！', 'code': 405})
        else:
            return JsonResponse({'msg': '登录过期！', 'code': 405})

    return wrapper


def parse_jwt_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    parts = auth_header.split(' ')
    jwt_value = parts[1] if len(parts) > 1 else ''
    print(f"[DEBUG parse_jwt_token] auth_header={auth_header[:60]}..., jwt_value_exists={bool(jwt_value)}")
    if jwt_value:
        try:
            token_user = jwt_decode_handler(jwt_value)
            username = token_user['username']
            if username:
                request.session['username'] = username
                request.session['user_id'] = token_user['user_id']
                current_user = User.objects.get(id=token_user['user_id'])
                return current_user
        except Exception as e:
            print(e)
            return None
    return


def now_time():
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return current_time


def uid():
    uid = str(uuid.uuid1())
    suid = ''.join(uid.split('-'))
    return suid


def create_log(request, account, name, values, text, status=1, desc=None):
    user_ip = request.META.get('REMOTE_ADDR')
    text = account + text
    SysLog.objects.create(account=account, name=name, type=values, content=text, ip=user_ip, status=status, desc=desc)


def ok(msg):
    return JsonResponse({
        "msg": msg,
        'code': 0,
        'data': []
    })


def error(msg):
    return JsonResponse({
        "msg": msg,
        'code': 400
    })


def warning(msg):
    return JsonResponse({
        "msg": msg,
        'code': 403
    }, status=200)


def ok_data(data):
    return JsonResponse({
        "msg": '数据获取成果！',
        "data": data,
        'code': 0
    })


def login_invalid(msg):
    return JsonResponse({
        "msg": msg,
        'status': False
    }, status=405)


def transform_xy(pixel_x, pixel_y):
    """
    像素坐标转地理坐标
    @param pixel_x:
    @param pixel_y:
    @return:
    """
    from pyproj import CRS
    from pyproj import Transformer
    crs_CGCS2000 = CRS.from_epsg(4528)
    crs_WGS84 = CRS.from_epsg(4490)
    from_crs = crs_CGCS2000
    to_crs = crs_WGS84
    transformer = Transformer.from_crs(from_crs, to_crs)
    # 即为转换后的坐标，也可以分别使⽤数组
    new_x, new_y = transformer.transform(pixel_x, pixel_y)
    return new_y, new_x


def file_iterator(file_path, chunk_size=512):
    """
    文件生成器,防止文件过大，导致内存溢出
    :param file_path: 文件绝对路径
    :param chunk_size: 块大小
    :return: 生成器
    """
    try:
        with open(file_path, mode='rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    except FileNotFoundError as e:
        print(e)


def zip_folder(src_dir, dst_zip):
    """
    将指定文件夹打包成ZIP文件

    参数:
    src_dir (str): 要打包的源文件夹路径
    dst_zip (str): 目标ZIP文件路径

    返回:
    str: 目标ZIP文件的路径
    """
    # 确保src_dir是绝对路径
    src_dir = os.path.abspath(src_dir)
    # 获取源文件夹的父目录，用于计算相对路径
    parent_dir = os.path.dirname(src_dir)

    with zipfile.ZipFile(dst_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(src_dir):
            # 计算当前目录的相对路径，并替换路径分隔符为/
            relative_dir = os.path.relpath(root, parent_dir)
            zip_dir = relative_dir.replace(os.path.sep, '/') + '/'

            # 创建目录条目（确保空目录也被添加）
            zip_info = zipfile.ZipInfo(zip_dir)
            # 设置目录权限（Unix系统有效）
            zip_info.external_attr = (0o755 << 16)
            # 写入空数据以创建目录
            zipf.writestr(zip_info, '')

            # 将目录中的所有文件添加到ZIP
            for file in files:
                file_path = os.path.join(root, file)
                # 计算文件的相对路径
                relative_path = os.path.relpath(file_path, parent_dir)
                # 替换路径分隔符为/
                relative_path = relative_path.replace(os.path.sep, '/')
                # 写入文件
                zipf.write(file_path, relative_path)

    return dst_zip


def read_json(file_path):
    # 读取 JSON 文件
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 获取 multiRes 对象
    multi_res = data.get('multiRes', {})

    return multi_res
