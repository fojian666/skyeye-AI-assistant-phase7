# _*_ coding: utf-8 _*_
# @Time : 2024/12/18 13:46
# @Author : xxx
# @Version：V 0.1
# @File : route_views.py
# @desc :
import json
import multiprocessing
import os
import random
import re
import shutil
import uuid
import zipfile
from datetime import date, datetime

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from django.conf import settings
from django.core.paginator import Paginator
from django.db import close_old_connections, transaction
from django.http import FileResponse, JsonResponse
from django.test import RequestFactory
from geopy.distance import great_circle
from pyproj import Transformer
from shapely.geometry import Point, box, shape
from shapely.ops import transform as shapely_transform, unary_union

from apps.panorama.common import unzip_file, get_geometry_coordinates, find_nearest_point_id
from apps.panorama.generate_file import generate_kmz, zip_folder
from apps.panorama.models import (
    Route, BufferFile, SupervisionProject, SupervisionProjectRoute, SupervisionProjectPolygon,
)
from apps.route.route_planning.multi_aircraft import plan_multi_base_sorties
from apps.route.route_planning.parcel_filter import (
    AIRCRAFT_PARCEL_RANGE_KM,
    build_filtered_geojson_from_features,
    eligible_aircraft_for_geometry,
    filter_features_by_aircraft_range,
)
from apps.route.job_manager import (
    create_job,
    job_file,
    read_job,
    read_payload,
    update_status,
    validate_job_id,
    write_result,
)
from apps.route.job_worker import run_filter_job, run_route_plan_job
from apps.route.route_planning.predict_flight import (
    generate_flight_candidates,
    lonlat2geo,
    predict_flight_points,
)
from apps.route.route_planning.panoramic_point_generate import (
    generate_panoramic_candidates,
    generate_panoramic_point,
    panoramic_point_to_shp,
)
from apps.system.models import Nest
from logger import Logger
from utils_tools.common import parse_jwt_token

logger = Logger(logname='route_views.log', loglevel=5, logger='route').getlog()

EXTERNAL_DEFAULT_AIRCRAFT_NAME = '无锡01'
EXTERNAL_JOB_KMZ_URL_PREFIX = '/api/route/jobs/'
EXTERNAL_JOB_KMZ_URL_SUFFIX = '/kmz'


def _parse_geojson_crs(geojson_data):
    """从 GeoJSON 中解析坐标系，默认 CGCS2000(EPSG:4490)。"""
    if not isinstance(geojson_data, dict):
        return 'EPSG:4490'
    crs_info = geojson_data.get('crs')
    if not crs_info:
        return 'EPSG:4490'
    if crs_info.get('type') == 'name':
        crs_name = crs_info.get('properties', {}).get('name', '')
        if 'EPSG:' in crs_name.upper():
            epsg_code = crs_name.upper().split('EPSG:')[-1].strip()
            if epsg_code.isdigit():
                return f'EPSG:{epsg_code}'
    return 'EPSG:4490'


def _normalize_geojson_feature(geojson_data):
    """将前端传入的 GeoJSON 统一为 Feature。"""
    features = _normalize_geojson_features(geojson_data)
    if len(features) != 1:
        raise ValueError('当前操作仅支持单个地块')
    return features[0]


def _normalize_geojson_features(geojson_data):
    """将 GeoJSON 统一为 Feature 列表，支持多个地块。"""
    if not geojson_data:
        raise ValueError('缺少规划区域 GeoJSON 数据')
    if isinstance(geojson_data, list):
        features = []
        for item in geojson_data:
            if not isinstance(item, dict):
                raise ValueError('地块列表中包含无效 GeoJSON')
            if item.get('type') == 'Feature' and item.get('geometry'):
                features.append(item)
            elif item.get('type') in ('Polygon', 'MultiPolygon'):
                features.append({
                    'type': 'Feature',
                    'geometry': item,
                    'properties': {},
                })
            else:
                raise ValueError('地块列表中包含无效 GeoJSON')
        return features
    if geojson_data.get('type') == 'FeatureCollection':
        features = geojson_data.get('features') or []
        if not features:
            raise ValueError('规划区域中没有地块')
        for feature in features:
            if feature.get('type') != 'Feature' or not feature.get('geometry'):
                raise ValueError('FeatureCollection 中包含无效地块')
        return features
    if geojson_data.get('type') == 'Feature':
        return [geojson_data]
    if geojson_data.get('type') in ('Polygon', 'MultiPolygon'):
        return [{'type': 'Feature', 'geometry': geojson_data, 'properties': {}}]
    raise ValueError('不支持的 GeoJSON 类型，请传入 FeatureCollection、Feature 或 Polygon')


def _first_property(properties, candidates, default=''):
    """按常见字段名（忽略大小写）读取 SHP 属性。"""
    normalized = {
        str(key).lower(): value
        for key, value in (properties or {}).items()
    }
    for candidate in candidates:
        value = normalized.get(candidate.lower())
        if (
            value is not None
            and value == value
            and str(value).strip()
        ):
            return value
    return default


def _collect_shp_paths(root_path):
    shp_paths = []
    for root, _, files in os.walk(root_path):
        shp_paths.extend(
            os.path.join(root, file_name)
            for file_name in files
            if file_name.lower().endswith('.shp')
        )
    return sorted(shp_paths)


def _json_safe_scalar(value):
    """将 pandas/numpy 标量转为 JSON 可序列化的原生 Python 类型。"""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, np.datetime64):
        try:
            return pd.Timestamp(value).isoformat()
        except (ValueError, OSError, OverflowError):
            return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def _gdf_to_geojson_features(gdf):
    """将 GeoDataFrame 转为 GeoJSON features，避免 Timestamp 等类型无法序列化。"""
    gdf = gdf.copy()
    for col in gdf.columns:
        if col == 'geometry':
            continue
        gdf[col] = gdf[col].apply(_json_safe_scalar)
    return json.loads(gdf.to_json()).get('features', [])


def _parse_polygon_features_from_shp_paths(shp_paths):
    polygon_features = []
    polygon_files = []
    for shp_path in shp_paths:
        gdf = gpd.read_file(shp_path)
        if gdf.empty:
            continue
        if gdf.crs is None:
            raise ValueError(f'{os.path.basename(shp_path)} 缺少坐标系信息（.prj）')
        gdf = gdf.to_crs('EPSG:4490')
        geometry_types = set(gdf.geometry.geom_type.dropna())
        if not geometry_types.intersection({'Polygon', 'MultiPolygon'}):
            continue
        polygon_gdf = gdf[
            gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])
        ].copy()
        polygon_features.extend(_gdf_to_geojson_features(polygon_gdf))
        polygon_files.append(os.path.basename(shp_path))
    return polygon_features, polygon_files


def _parse_aircraft_from_shp_paths(shp_paths):
    aircraft = []
    aircraft_files = []
    for shp_path in shp_paths:
        gdf = gpd.read_file(shp_path)
        if gdf.empty:
            continue
        if gdf.crs is None:
            raise ValueError(f'{os.path.basename(shp_path)} 缺少坐标系信息（.prj）')
        gdf = gdf.to_crs('EPSG:4490')
        geometry_types = set(gdf.geometry.geom_type.dropna())
        if not geometry_types.intersection({'Point', 'MultiPoint'}):
            continue
        point_gdf = gdf[
            gdf.geometry.geom_type.isin(['Point', 'MultiPoint'])
        ].copy()
        aircraft_files.append(os.path.basename(shp_path))
        for _, row in point_gdf.iterrows():
            properties = row.drop(labels=['geometry']).to_dict()
            geometries = (
                list(row.geometry.geoms)
                if row.geometry.geom_type == 'MultiPoint'
                else [row.geometry]
            )
            for point in geometries:
                aircraft_index = len(aircraft) + 1
                aircraft.append({
                    'id': str(_first_property(
                        properties,
                        [
                            'id', 'nest_id', 'aircraft_id', 'plane_id',
                            'uav_id', '机巢ID', '机巢编号',
                        ],
                        aircraft_index,
                    )),
                    'name': str(_first_property(
                        properties,
                        [
                            'name', 'nest_name', 'aircraft_name',
                            'plane_name', 'uav_name', '机巢名称',
                            '飞机名称',
                        ],
                        f'飞机{aircraft_index}',
                    )),
                    'planeSn': str(_first_property(
                        properties,
                        ['plane_sn', 'planesn', 'sn', 'uav_sn', '飞机sn'],
                        '',
                    )),
                    'longitude': float(point.x),
                    'latitude': float(point.y),
                })
    return aircraft, aircraft_files


def _build_parcel_geojson(polygon_features):
    return {
        'type': 'FeatureCollection',
        'features': polygon_features,
        'crs': {
            'type': 'name',
            'properties': {'name': 'EPSG:4490'},
        },
    }


def _parse_parcel_archive(unzip_path):
    """解析地块 ZIP：合并所有 Polygon/MultiPolygon SHP。"""
    shp_paths = _collect_shp_paths(unzip_path)
    if not shp_paths:
        raise ValueError('压缩包中未检测到 SHP 文件')
    polygon_features, polygon_files = _parse_polygon_features_from_shp_paths(shp_paths)
    if not polygon_features:
        raise ValueError('压缩包中未检测到面地块 SHP')
    return {
        'geojson': _build_parcel_geojson(polygon_features),
        'summary': {
            'parcelCount': len(polygon_features),
            'polygonFiles': polygon_files,
        },
    }


def _parse_aircraft_shp_directory(directory_path):
    """解析飞机点位 SHP 目录。"""
    shp_paths = _collect_shp_paths(directory_path)
    if not shp_paths:
        raise ValueError('未检测到 SHP 文件')
    aircraft, aircraft_files = _parse_aircraft_from_shp_paths(shp_paths)
    if not aircraft:
        raise ValueError('未检测到飞机点位 SHP')
    return {
        'aircraft': aircraft,
        'summary': {
            'aircraftCount': len(aircraft),
            'aircraftFiles': aircraft_files,
        },
    }


def _parse_route_input_archive(unzip_path):
    """
    解析完整航线规划数据包（兼容旧版单 ZIP 上传）：
    - 所有 Polygon/MultiPolygon SHP 合并为地块 FeatureCollection；
    - 所有 Point/MultiPoint SHP 解析为飞机起降点。
    """
    shp_paths = _collect_shp_paths(unzip_path)
    if not shp_paths:
        raise ValueError('压缩包中未检测到 SHP 文件')

    polygon_features, polygon_files = _parse_polygon_features_from_shp_paths(shp_paths)
    aircraft, aircraft_files = _parse_aircraft_from_shp_paths(shp_paths)

    if not polygon_features:
        raise ValueError('压缩包中未检测到面地块 SHP')
    if not aircraft:
        raise ValueError('压缩包中未检测到飞机点位 SHP')

    return {
        'geojson': _build_parcel_geojson(polygon_features),
        'aircraft': aircraft,
        'summary': {
            'parcelCount': len(polygon_features),
            'aircraftCount': len(aircraft),
            'polygonFiles': polygon_files,
            'aircraftFiles': aircraft_files,
        },
    }


def _save_uploaded_files(uploaded_files, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    saved_paths = []
    for uploaded_file in uploaded_files:
        safe_file_name = os.path.basename(uploaded_file.name)
        file_path = os.path.join(target_dir, safe_file_name)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        saved_paths.append(file_path)
    return saved_paths


def _safe_route_segment(name, fallback):
    cleaned = re.sub(
        r'[\\/:*?"<>|\s]+',
        '_',
        '' if name is None else str(name).strip(),
    )
    return cleaned or fallback


def _filter_parcels_for_aircraft(geojson_data, aircraft_list, radius_km=AIRCRAFT_PARCEL_RANGE_KM):
    features = _normalize_geojson_features(geojson_data)
    crs = geojson_data.get('crs') if isinstance(geojson_data, dict) else None
    return build_filtered_geojson_from_features(
        features,
        aircraft_list,
        radius_km=radius_km,
        crs=crs,
    )


def _assign_features_to_nearest_aircraft(
    geojson_data,
    aircraft_list,
    radius_km=AIRCRAFT_PARCEL_RANGE_KM,
):
    """在可独立完整覆盖地块的机巢中，按形心距离选择最近机巢。"""
    if not aircraft_list:
        raise ValueError('请先上传机巢点位')
    features = _normalize_geojson_features(geojson_data)
    assignments = {
        aircraft_item['index']: []
        for aircraft_item in aircraft_list
    }
    feature_assignments = []
    for feature_index, feature in enumerate(features):
        centroid = shape(feature['geometry']).centroid
        eligible_aircraft = eligible_aircraft_for_geometry(
            feature['geometry'],
            aircraft_list,
            radius_km=radius_km,
        )
        if not eligible_aircraft:
            raise ValueError(
                f'第 {feature_index + 1} 个地块无法被任一机巢在 '
                f'{radius_km:g} km 范围内独立完整覆盖'
            )
        eligible_by_index = {
            item['index']: max_boundary_distance_km
            for item, max_boundary_distance_km in eligible_aircraft
        }
        aircraft_item, distance_m = min(
            (
                (
                    item,
                    great_circle(
                        (centroid.y, centroid.x),
                        (item['latitude'], item['longitude']),
                    ).meters,
                )
                for item, _ in eligible_aircraft
            ),
            key=lambda candidate: candidate[1],
        )
        assignments[aircraft_item['index']].append(feature)
        feature_assignments.append({
            'featureIndex': feature_index,
            'aircraftIndex': aircraft_item['index'],
            'aircraftId': aircraft_item.get('id'),
            'aircraftName': aircraft_item.get('name'),
            'centroidDistanceKm': round(distance_m / 1000, 3),
            'maxBoundaryDistanceKm': round(
                eligible_by_index[aircraft_item['index']],
                3,
            ),
        })
    return assignments, feature_assignments


def _filter_reachable_target_points(
    projected_points,
    lonlat_points,
    depot,
    max_distance_km,
):
    """按单架次往返最大距离过滤网格中心点。"""
    max_distance_m = float(max_distance_km) * 1000
    reachable_projected = []
    reachable_lonlat = []
    unreachable = []
    for point_index, (projected_point, lonlat_point) in enumerate(
        zip(projected_points, lonlat_points),
        start=1,
    ):
        round_trip_m = 2 * (
            (float(projected_point[0]) - float(depot[0])) ** 2
            + (float(projected_point[1]) - float(depot[1])) ** 2
        ) ** 0.5
        if round_trip_m <= max_distance_m + 1e-6:
            reachable_projected.append(projected_point)
            reachable_lonlat.append(lonlat_point)
            continue
        unreachable.append({
            'index': point_index,
            'longitude': lonlat_point[0],
            'latitude': lonlat_point[1],
            'roundTripKm': round(round_trip_m / 1000, 3),
        })
    return reachable_projected, reachable_lonlat, unreachable


def _feature_collection(features, source_geojson):
    result = {
        'type': 'FeatureCollection',
        'features': features,
    }
    if isinstance(source_geojson, dict) and source_geojson.get('crs'):
        result['crs'] = source_geojson['crs']
    return result


def _covered_feature_indexes_for_route(
    route_points,
    features,
    feature_indexes,
    source_geojson,
    half_grid_size=75.0,
):
    """根据航线经过的网格中心点，返回该架次实际覆盖的原始地块下标。"""
    if not route_points or len(route_points) <= 2:
        return []

    lonlat_to_projected = Transformer.from_crs(
        4490,
        4549,
        always_xy=True,
    )
    coverage_cells = []
    for point in route_points[1:-1]:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        x, y = lonlat_to_projected.transform(
            float(point[0]),
            float(point[1]),
        )
        coverage_cells.append(
            box(
                x - half_grid_size,
                y - half_grid_size,
                x + half_grid_size,
                y + half_grid_size,
            )
        )
    if not coverage_cells:
        return []

    polygon_crs = _parse_geojson_crs(
        source_geojson if isinstance(source_geojson, dict) else {}
    )
    polygon_to_projected = Transformer.from_crs(
        polygon_crs,
        4549,
        always_xy=True,
    )
    covered_indexes = []
    for feature, feature_index in zip(features, feature_indexes):
        try:
            geometry = shape(feature['geometry'])
            projected_geometry = shapely_transform(
                polygon_to_projected.transform,
                geometry,
            )
        except (TypeError, ValueError, KeyError):
            continue
        if any(
            coverage_cell.intersects(projected_geometry)
            for coverage_cell in coverage_cells
        ):
            covered_indexes.append(feature_index)
    return covered_indexes


def _parcel_display_name(feature, index):
    properties = feature.get('properties') or {}
    value = _first_property(
        properties,
        [
            'name', 'NAME', '地块名称', '项目名称', 'project_name',
            'parcel_name', 'DKMC', 'BSM', 'id', 'ID',
        ],
        '',
    )
    return str(value).strip() or f'地块{index}'


def _write_excluded_parcels_zip(job_id, features, crs):
    if not features:
        return ''
    output_dir = job_file(job_id, 'excluded_parcels')
    os.makedirs(output_dir, exist_ok=True)
    gdf = gpd.GeoDataFrame.from_features(features, crs=_parse_geojson_crs({'crs': crs}))
    gdf.to_file(
        os.path.join(output_dir, '超出飞机服务范围地块.shp'),
        encoding='utf-8',
    )
    zip_path = job_file(job_id, 'excluded_parcels.zip')
    zip_folder(output_dir, zip_path)
    return zip_path


def _run_filter_job(job_id):
    close_old_connections()
    try:
        update_status(job_id, status='running', progress=2, message='正在读取地块和飞机点位')
        params = read_payload(job_id)
        geojson_data = params.get('geojson') or params.get('polygon')
        aircraft_list = params.get('aircraft') or []
        radius_km = float(params.get('radiusKm', AIRCRAFT_PARCEL_RANGE_KM))
        features = _normalize_geojson_features(geojson_data)
        crs = geojson_data.get('crs') if isinstance(geojson_data, dict) else None

        def report(current, total):
            update_step = max(1, total // 100)
            if current != total and current % update_step != 0:
                return
            progress = 5 + int(current / max(total, 1) * 80)
            update_status(
                job_id,
                status='running',
                progress=min(progress, 85),
                message=f'正在筛选地块 {current}/{total}',
            )

        kept, excluded = filter_features_by_aircraft_range(
            features,
            aircraft_list,
            radius_km=radius_km,
            progress_callback=report,
        )
        if not kept:
            raise ValueError(
                f'{radius_km:g} km 范围内没有有效地块，共 {len(features)} 个地块均被剔除'
            )
        update_status(job_id, status='running', progress=88, message='正在生成超范围地块下载文件')
        excluded_names = [
            _parcel_display_name(feature, index)
            for index, feature in enumerate(excluded, start=1)
        ]
        _write_excluded_parcels_zip(job_id, excluded, crs)
        filtered_geojson = {'type': 'FeatureCollection', 'features': kept}
        excluded_geojson = {'type': 'FeatureCollection', 'features': excluded}
        if crs:
            filtered_geojson['crs'] = crs
            excluded_geojson['crs'] = crs
        result = {
            'geojson': filtered_geojson,
            'excludedGeojson': excluded_geojson,
            'summary': {
                'totalParcelCount': len(features),
                'parcelCount': len(kept),
                'excludedParcelCount': len(excluded),
                'aircraftCount': len(aircraft_list),
                'rangeKm': radius_km,
            },
            'excludedParcelNames': excluded_names,
            'excludedDownloadAvailable': bool(excluded),
        }
        write_result(job_id, result)
        update_status(job_id, status='completed', progress=100, message='地块筛选完成')
    except Exception as exc:
        logger.exception('后台地块筛选失败')
        update_status(job_id, status='failed', progress=100, message=str(exc))
    finally:
        close_old_connections()


def _start_background_process(target, job_id):
    process = multiprocessing.get_context('spawn').Process(
        target=target,
        args=(job_id,),
        daemon=False,
    )
    process.start()
    return process.pid


def _resolve_external_default_aircraft():
    """外部接口默认使用机巢/飞机表中的无锡01。"""
    nest = (
        Nest.objects.filter(name=EXTERNAL_DEFAULT_AIRCRAFT_NAME, status=1)
        .exclude(longitude=0)
        .exclude(latitude=0)
        .first()
    )
    if not nest:
        nest = (
            Nest.objects.filter(plane_sn=EXTERNAL_DEFAULT_AIRCRAFT_NAME, status=1)
            .exclude(longitude=0)
            .exclude(latitude=0)
            .first()
        )
    if not nest:
        raise ValueError(
            f'未找到默认飞机/机巢：{EXTERNAL_DEFAULT_AIRCRAFT_NAME}，请先维护机巢信息'
        )
    return [{
        'id': nest.id,
        'name': nest.name,
        'planeSn': nest.plane_sn,
        'longitude': nest.longitude,
        'latitude': nest.latitude,
    }]


def _collect_job_overview_kmz_files(job_result):
    """从规划任务结果中提取俯视图 KMZ 文件路径。"""
    routes = job_result.get('overviewRoutes')
    if not routes:
        routes = [
            route
            for route in (job_result.get('routes') or [])
            if route.get('captureType', 'overview') == 'overview'
        ]
    file_ids = [
        route['fileId']
        for route in routes
        if route.get('fileId')
    ]
    if not file_ids:
        return []

    buffer_files = BufferFile.objects.filter(file_id__in=file_ids)
    file_map = {item.file_id: item for item in buffer_files}
    kmz_files = []
    for file_id in file_ids:
        buffer_file = file_map.get(file_id)
        if not buffer_file or not buffer_file.file_path:
            continue
        if not os.path.exists(buffer_file.file_path):
            continue
        kmz_files.append(buffer_file)
    return kmz_files


def _geojson_centroid(geojson_data):
    geometries = [shape(feature['geometry']) for feature in _normalize_geojson_features(geojson_data)]
    return unary_union(geometries).centroid


def _parse_algorithm_route_name(route_name):
    """兼容解析新旧算法航线命名。"""
    value = str(route_name or '').strip()
    matched = re.match(r'^(.*)-(\d{12})-([^-]+)-航线(\d+)$', value)
    if matched:
        return {
            'task_name': matched.group(1),
            'plan_generated_at': matched.group(2),
            'aircraft_name': matched.group(3),
            'sortie_index': int(matched.group(4)),
        }
    matched = re.match(r'^(.*)-([^-]+)-架次(\d+)$', value)
    if matched:
        return {
            'task_name': matched.group(1),
            'plan_generated_at': '',
            'aircraft_name': matched.group(2),
            'sortie_index': int(matched.group(3)),
        }
    return {
        'task_name': value or '未命名任务',
        'plan_generated_at': '',
        'aircraft_name': '未分组飞机',
        'sortie_index': None,
    }


def geojson_to_shp(geojson_data, output_dir):
    """将 GeoJSON 面要素写入 shapefile，供航线规划算法使用。"""
    os.makedirs(output_dir, exist_ok=True)
    features = _normalize_geojson_features(geojson_data)
    gdf = gpd.GeoDataFrame.from_features(features, crs=_parse_geojson_crs(geojson_data))
    shp_path = os.path.join(output_dir, 'input.shp')
    gdf.to_file(shp_path, encoding='utf-8')
    return shp_path


def find_nearest_nest(geojson_data):
    """根据规划区域中心点查找最近机巢。"""
    centroid = _geojson_centroid(geojson_data)
    ref_point = (centroid.y, centroid.x)

    nests = Nest.objects.exclude(longitude=0).exclude(latitude=0)
    if not nests.exists():
        return None, None

    nearest_nest = None
    min_distance = float('inf')
    for nest in nests:
        distance = great_circle(ref_point, (nest.latitude, nest.longitude)).meters
        if distance < min_distance:
            min_distance = distance
            nearest_nest = nest
    return nearest_nest, min_distance


def _resolve_aircraft(params, geojson_data, aircraft_count=4):
    """
    Resolve aircraft and their independent start points.

    Request data takes priority. When omitted, use the nearest active Nest
    records because each Nest row already contains one aircraft and its depot.
    """
    raw_aircraft = (
        params.get('aircraft')
        or params.get('aircraftList')
        or params.get('aircrafts')
    )
    if raw_aircraft:
        if not isinstance(raw_aircraft, list):
            raise ValueError('aircraft 必须是飞机列表')
        result = []
        for index, item in enumerate(raw_aircraft, start=1):
            if not isinstance(item, dict):
                raise ValueError(f'第 {index} 架飞机参数无效')
            start = (
                item.get('startPoint')
                or item.get('start_point')
                or item.get('depot')
            )
            longitude = item.get('longitude')
            latitude = item.get('latitude')
            if start:
                if not isinstance(start, (list, tuple)) or len(start) != 2:
                    raise ValueError(f'第 {index} 架飞机起点格式无效')
                longitude, latitude = start[0], start[1]
            if longitude is None or latitude is None:
                raise ValueError(f'第 {index} 架飞机缺少起点经纬度')
            result.append({
                'index': index,
                'id': item.get('id'),
                'name': item.get('name') or item.get('planeName') or f'飞机{index}',
                'plane_sn': item.get('planeSn') or item.get('plane_sn') or '',
                'longitude': float(longitude),
                'latitude': float(latitude),
            })
        return result

    raw_start_points = params.get('startPoints') or params.get('aircraftStartPoints')
    if raw_start_points:
        if not isinstance(raw_start_points, list):
            raise ValueError('startPoints 必须是经纬度列表')
        if any(
            not isinstance(point, (list, tuple)) or len(point) != 2
            for point in raw_start_points
        ):
            raise ValueError('startPoints 中包含无效经纬度')
        return [
            {
                'index': index,
                'id': None,
                'name': f'飞机{index}',
                'plane_sn': '',
                'longitude': float(point[0]),
                'latitude': float(point[1]),
            }
            for index, point in enumerate(raw_start_points, start=1)
        ]

    centroid = _geojson_centroid(geojson_data)
    ref_point = (centroid.y, centroid.x)
    nests = list(
        Nest.objects.filter(status=1).exclude(longitude=0).exclude(latitude=0)
    )
    nests.sort(
        key=lambda nest: great_circle(
            ref_point, (nest.latitude, nest.longitude)
        ).meters
    )
    selected = nests[:aircraft_count]
    if len(selected) < aircraft_count:
        raise ValueError(
            f'有效飞机/机巢不足：需要 {aircraft_count} 架，当前仅 {len(selected)} 架；'
            '也可以通过 aircraft 参数直接传入飞机起点'
        )
    return [
        {
            'index': index,
            'id': nest.id,
            'name': nest.name or f'飞机{index}',
            'plane_sn': nest.plane_sn,
            'longitude': nest.longitude,
            'latitude': nest.latitude,
        }
        for index, nest in enumerate(selected, start=1)
    ]


def _generate_file_id():
    while True:
        file_id = f"62{random.randint(10000000000000, 99999999999999)}"
        if not BufferFile.objects.filter(file_id=file_id).exists():
            return file_id


def _parse_collect_date(value):
    """解析采集日期参数。"""
    if not value:
        return datetime.now().date()
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()


def _create_supervision_task(
    geojson_data,
    route_objs,
    params,
    username,
    county,
    route_feature_indexes=None,
):
    """
    创建监管任务，并关联航线与图斑。
    """
    features = _normalize_geojson_features(geojson_data)
    if not isinstance(route_objs, (list, tuple)):
        route_objs = [route_objs]

    supervision_projects = []
    polygon_objs = []
    point_results = []
    normalized_route_feature_indexes = None
    if route_feature_indexes is not None:
        normalized_route_feature_indexes = {
            route_id: set(indexes or [])
            for route_id, indexes in route_feature_indexes.items()
        }

    for feature_index, feature in enumerate(features):
        supervision_project = SupervisionProject.objects.create(
            data_type=params.get('dataType') or params.get('data_type') or 3,
            count=1,
            create_person=username,
            status=int(params.get('status', 0)),
            county=county,
            collect_time=_parse_collect_date(params.get('collectTime') or params.get('collect_time')),
        )
        supervision_projects.append(supervision_project)

        for route_obj in route_objs:
            if (
                normalized_route_feature_indexes is not None
                and feature_index not in normalized_route_feature_indexes.get(route_obj.id, set())
            ):
                continue
            SupervisionProjectRoute.objects.create(
                supervision_project_id=supervision_project.id,
                route_id=route_obj.id,
            )

        properties = feature.get('properties') or {}
        centroid = shape(feature['geometry']).centroid
        nearest_point_id, nearest_distance = find_nearest_point_id(
            centroid.y, centroid.x, county
        )
        polygon_objs.append(SupervisionProjectPolygon.objects.create(
            supervision_project_id=supervision_project.id,
            polygon=json.dumps(feature, ensure_ascii=False),
            latitude=centroid.y,
            longitude=centroid.x,
            polygon_type=(params.get('data_type') or params.get('dataType') or 3),
            construction_desc=(
                properties.get('constructionDesc') or properties.get('construction_desc')
                or params.get('constructionDesc') or params.get('construction_desc') or ''
            ),
            color_desc=(
                properties.get('colorDesc') or properties.get('color_desc')
                or params.get('colorDesc') or params.get('color_desc') or ''
            ),
            point_id=nearest_point_id or '',
            create_person=username,
            status=int(properties.get('status', params.get('polygonStatus', 0))),
        ))
        point_results.append({
            'projectId': supervision_project.id,
            'pointId': nearest_point_id,
            'pointDistance': (
                round(nearest_distance, 2) if nearest_distance is not None else None
            ),
        })
    return supervision_projects, polygon_objs, point_results


def route_plan(request):
    """
    存储定义航线
    """
    response_data = {'code': 0, 'msg': '航线规划成功！', 'data': {}}
    if request.method == 'POST':
        file_paths = []
        with transaction.atomic():
            try:
                logger.info("接受航线规划任务")
                # 获取用户名
                username = request.session.get('username', 'admin')
                # 获取请求参数
                params = json.loads(request.body.decode('utf-8'))
                plan_type = str(params.get('routeType'))
                plan_name = str(params.get('name', ''))
                camera_size = int(params.get('cameraSize', 1))
                uavflightheight = params.get('uavflightheight', 12)

                shp_name = params.get('fileName', '')
                fly_points_obj = []
                # 查询航线名称是否已存在
                plan_obj = Route.objects.filter(name=plan_name).all()
                if plan_obj:
                    logger.info(f"{plan_name}航线名称已存在")
                    return JsonResponse({'code': 1, 'msg': '该航线名称已存在', 'data': {}})
                # 根据航线类型进行不同的处理
                if plan_type == '人工选点':
                    start_point = ''
                    end_point = ''
                    fly_points = params.get('points')
                    # 将经纬度转换为浮点数
                    for i in fly_points:
                        fly_points_obj.append([float(i[0]), float(i[1])])
                elif plan_type == '算法规划':
                    start_point = json.loads(params.get('startPoint'))
                    end_point = json.loads(params.get('endPoint'))
                    # 获取shp文件路径
                    path = os.path.join(settings.BASE_DIR, 'static', 'shp', shp_name.split('.')[0])
                    if not os.path.exists(path):
                        logger.info('压缩包未找到')
                        return JsonResponse({'code': 0, 'msg': '文件未找到', 'data': []})
                    shp_list = [os.path.join(path, i) for i in os.listdir(path) if i.endswith('.shp')]
                    if len(shp_list) == 0:
                        logger.info('压缩包中未找到shp文件')
                        return JsonResponse({'code': 0, 'msg': '文件未找到', 'data': []})
                    else:
                        # 生成uuid
                        uuid_value = str(uuid.uuid4())
                        # 调用算法规划函数
                        print(start_point,end_point)
                        fly_points_obj = predict_flight_points(shp_list[0], start_point, end_point, uuid_value)
                # 生成kmz文件
                route_plan_path = os.path.join(settings.BASE_DIR, 'static', 'route_plan')
                if not os.path.exists(route_plan_path):
                    os.makedirs(route_plan_path)
                out_path = os.path.join(route_plan_path, plan_name)
                if os.path.exists(out_path + '.kmz'):
                    os.remove(out_path + '.kmz')
                generate_kmz(out_path, fly_points_obj, uavflightheight)
                # 存储文件路径以便后续删除
                file_paths = [out_path + '.kmz']
                # 生成文件id
                while True:
                    file_id = f"62{random.randint(10000000000000, 99999999999999)}"
                    is_exist = BufferFile.objects.filter(file_id=file_id)
                    if not is_exist:
                        break
                kmz_file_path = out_path + '.kmz'
                # 存储文件信息
                BufferFile.objects.create(
                    file_id=file_id,
                    file_name=plan_name + '.kmz',
                    file_extension='.kmz',
                    file_path=kmz_file_path,
                    owner=username,
                    file_type='kml',
                    file_size=os.path.getsize(kmz_file_path)
                )
                logger.info('kmz文件生成成功')
                # 存储航线信息
                Route.objects.create(
                    route_type=plan_type,
                    name=plan_name,
                    camera_size=int(camera_size),
                    height=int(uavflightheight),
                    file_id=file_id,
                    start_point=start_point,
                    end_point=end_point,
                )
                response_data['data'] = fly_points_obj
                return JsonResponse(response_data)
            except Exception as e:
                logger.error(f'后台错误，请查看{e}')
                # 删除生成的文件
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                # 回滚数据库事务
                transaction.set_rollback(
                    True)  # transaction.set_rollback(True) 是一个更安全的选项，因为它允许Django的事务管理器在事务结束时决定是否回滚，这有助于保持数据库的一致性。而 transaction.rollback() 则提供了更直接的控制，允许立即回滚事务，但需要开发者确保在正确的时机使用它，以避免潜在的数据不一致问题。
                return JsonResponse({'code': 500, 'msg': "后台错误，请查看", 'data': {}})


def _execute_route_plan_request(request):
    """
    根据前端传入的单个或多个 GeoJSON 地块自动生成多基地、多架次航线。
    每架飞机从自己的起点起降，同一飞机的多个架次顺序执行。
    """
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})

    response_data = {'code': 0, 'msg': '航线规划成功！', 'data': {}}
    file_paths = []
    route_directories = []
    temp_dir = ''

    with transaction.atomic():
        try:
            progress_callback = getattr(request, '_route_job_progress', lambda *_: None)
            progress_callback(5, '正在校验规划参数')
            logger.info('接收 GeoJSON 航线规划任务')
            username = getattr(request, '_route_job_username', None)
            county = getattr(request, '_route_job_county', None)
            if not username or not county:
                try:
                    current_user = parse_jwt_token(request)
                    username = current_user.username
                    county = current_user.county
                except Exception as e:
                    print(e)
                    username = request.session.get('username', 'WXAdmin')
                    county = '无锡市(320200)'
            print(county)
            params = json.loads(request.body.decode('utf-8'))
            geojson_data = params.get('polygon') or params.get('geojson') or params
            plan_name = params.get('name') or params.get('planName') or f"route_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            auto_flight_speed_mps = float(
                params.get(
                    'autoFlightSpeed',
                    params.get('auto_flight_speed', 15.0),
                )
            )
            speed_kmh = auto_flight_speed_mps * 3.6
            max_flight_minutes = float(
                params.get(
                    'maxFlightMinutes',
                    params.get('max_flight_minutes', 20.0),
                )
            )
            take_off_security_height = float(
                params.get(
                    'takeOffSecurityHeight',
                    params.get('take_off_security_height', 115.0),
                )
            )
            uavflightheight = float(
                params.get(
                    'uavflightheight',
                    params.get('uavFlightHeight', take_off_security_height),
                )
            )
            turnaround_minutes = 0.0
            raw_alns_iterations = params.get(
                'alnsIterations', params.get('alns_iterations')
            )
            alns_iterations = (
                int(raw_alns_iterations)
                if raw_alns_iterations is not None
                else None
            )
            max_distance_km = float(
                params.get(
                    'maxDistanceKm',
                    params.get(
                        'max_distance_km',
                        auto_flight_speed_mps * max_flight_minutes * 60 / 1000,
                    ),
                )
            )
            radius_km = float(
                params.get('rangeKm', params.get('range_km', AIRCRAFT_PARCEL_RANGE_KM))
            )

            if (
                Route.objects.filter(name=plan_name).exists()
                or Route.objects.filter(name__startswith=f'{plan_name}-').exists()
            ):
                return JsonResponse({'code': 1, 'msg': '该航线名称已存在', 'data': {}})

            raw_aircraft = (
                params.get('aircraft')
                or params.get('aircraftList')
                or params.get('aircrafts')
            )
            if raw_aircraft:
                aircraft_items = _resolve_aircraft(params, geojson_data)
            else:
                aircraft_count = int(params.get('aircraftCount', 4))
                aircraft_items = _resolve_aircraft(
                    params, geojson_data, aircraft_count=aircraft_count
                )
            aircraft_count = len(aircraft_items)

            parcel_filter_summary = None
            if raw_aircraft and not params.get('alreadyFiltered'):
                progress_callback(10, '正在复核飞机服务范围')
                filtered_result = _filter_parcels_for_aircraft(
                    geojson_data, aircraft_items, radius_km=radius_km
                )
                geojson_data = filtered_result['geojson']
                parcel_filter_summary = filtered_result['summary']
                logger.info(
                    '地块筛选完成：保留 %s 个，剔除 %s 个（半径 %s km）',
                    parcel_filter_summary['parcelCount'],
                    parcel_filter_summary['excludedParcelCount'],
                    radius_km,
                )

            progress_callback(18, '正在按地块形心关联最近机巢')
            assigned_features, feature_assignments = (
                _assign_features_to_nearest_aircraft(
                    geojson_data,
                    aircraft_items,
                    radius_km=radius_km,
                )
            )
            feature_indexes_by_aircraft = {
                aircraft_item['index']: []
                for aircraft_item in aircraft_items
            }
            for assignment in feature_assignments:
                feature_indexes_by_aircraft[
                    assignment['aircraftIndex']
                ].append(assignment['featureIndex'])
            temp_dir = os.path.join(
                settings.BASE_DIR,
                'static',
                'shp',
                f'route_geojson_{uuid.uuid4().hex}',
            )
            os.makedirs(temp_dir, exist_ok=True)
            active_aircraft = [
                item
                for item in aircraft_items
                if assigned_features[item['index']]
            ]
            planned_groups = []
            for group_position, aircraft_item in enumerate(
                active_aircraft,
                start=1,
            ):
                aircraft_index = aircraft_item['index']
                aircraft_features = assigned_features[aircraft_index]
                aircraft_feature_indexes = feature_indexes_by_aircraft.get(
                    aircraft_index,
                    [],
                )
                group_base = 22 + (
                    (group_position - 1)
                    / max(len(active_aircraft), 1)
                    * 33
                )
                group_span = 33 / max(len(active_aircraft), 1)
                progress_callback(
                    round(group_base, 1),
                    (
                        f'正在为机巢 {aircraft_item["name"]} 生成 '
                        f'150m×150m 网格'
                    ),
                )
                aircraft_temp_dir = os.path.join(
                    temp_dir,
                    f'aircraft_{aircraft_index}',
                )
                aircraft_geojson = _feature_collection(
                    aircraft_features,
                    geojson_data,
                )
                shp_path = geojson_to_shp(
                    aircraft_geojson,
                    aircraft_temp_dir,
                )

                def report_candidate_progress(
                    current,
                    total,
                    message='正在生成150m×150m航点网格',
                    base=group_base,
                    span=group_span,
                ):
                    ratio = current / max(total, 1)
                    progress_callback(
                        round(base + min(ratio, 1) * span * 0.45, 1),
                        message,
                    )

                projected_points, lonlat_points, prj_path = (
                    generate_flight_candidates(
                        shp_path,
                        progress_callback=report_candidate_progress,
                        grid_size=150,
                        adaptive_grid=False,
                    )
                )
                if not projected_points:
                    raise ValueError(
                        f'机巢 {aircraft_item["name"]} 关联地块未生成有效网格中心点'
                    )
                planner_aircraft = {
                    **aircraft_item,
                    'depot': lonlat2geo(
                        prj_path,
                        aircraft_item['longitude'],
                        aircraft_item['latitude'],
                    ),
                }
                (
                    projected_points,
                    lonlat_points,
                    unreachable_target_points,
                ) = _filter_reachable_target_points(
                    projected_points,
                    lonlat_points,
                    planner_aircraft['depot'],
                    max_distance_km=max_distance_km,
                )
                if unreachable_target_points:
                    logger.warning(
                        '机巢 %s 有 %s 个网格中心点往返超过 %s km，已剔除',
                        aircraft_item['name'],
                        len(unreachable_target_points),
                        max_distance_km,
                    )
                if not projected_points:
                    raise ValueError(
                        f'机巢 {aircraft_item["name"]} 的网格中心点均超过 '
                        f'{max_distance_km:g} km 单架次往返约束，无法规划'
                    )
                progress_callback(
                    round(group_base + group_span * 0.5, 1),
                    f'正在独立规划机巢 {aircraft_item["name"]} 的多条航线',
                )
                plan_result = plan_multi_base_sorties(
                    projected_points,
                    [planner_aircraft],
                    speed_kmh=speed_kmh,
                    max_flight_minutes=max_flight_minutes,
                    max_distance_km=max_distance_km,
                    # ALNS 目标严格按航线总长度最短；再次起飞准备时间
                    # 仅用于规划完成后的时刻表计算，不参与路径目标函数。
                    turnaround_minutes=0,
                    attempts=12,
                    early_stop_rounds=3,
                    parallel=False,
                    alns_iterations=alns_iterations,
                    progress_callback=lambda current, total, base=group_base, span=group_span, name=aircraft_item['name']: progress_callback(
                        round(
                            base
                            + span
                            * (
                                0.5
                                + current / max(total, 1) * 0.5
                            ),
                            1,
                        ),
                        (
                            f'正在执行机巢 {name} 的 ALNS 优化 '
                            f'{min(int(current), total)}/{total}'
                        ),
                    ),
                )
                planned_groups.append({
                    'aircraft': aircraft_item,
                    'aircraftFeatures': aircraft_features,
                    'featureIndexes': aircraft_feature_indexes,
                    'lonlatPoints': lonlat_points,
                    'planResult': plan_result,
                    'parcelCount': len(aircraft_features),
                    'targetPointCount': len(lonlat_points),
                    'excludedTargetPointCount': len(unreachable_target_points),
                    'excludedTargetPoints': unreachable_target_points,
                })

            route_plan_path = os.path.join(settings.BASE_DIR, 'static', 'route_plan')
            os.makedirs(route_plan_path, exist_ok=True)
            route_objs = []
            route_feature_indexes = {}
            route_results = []
            aircraft_schedules = []
            panoramic_route_results = []
            panoramic_aircraft_schedules = []
            plan_generated_at = datetime.now().strftime('%Y%m%d%H%M')
            total_sorties_value = sum(
                group['planResult']['total_sorties']
                for group in planned_groups
            )
            target_point_count = sum(
                group.get('targetPointCount', 0)
                for group in planned_groups
            )
            excluded_target_point_count = sum(
                group.get('excludedTargetPointCount', 0)
                for group in planned_groups
            )
            total_sorties = max(total_sorties_value, 1)
            completed_sorties = 0
            total_distance_m = 0.0
            makespan_minutes = 0.0
            alns_iteration_values = []
            for group in planned_groups:
                aircraft_item = group['aircraft']
                aircraft_index = aircraft_item['index']
                lonlat_points = group['lonlatPoints']
                plan_result = group['planResult']
                schedule = plan_result['aircraft_schedules'][0]
                elapsed_minutes = 0.0
                for sortie in schedule['sorties']:
                    sortie['start_minute'] = elapsed_minutes
                    sortie['end_minute'] = (
                        elapsed_minutes
                        + sortie['flight_time_minutes']
                    )
                    elapsed_minutes = (
                        sortie['end_minute']
                        + turnaround_minutes
                    )
                schedule['completion_minutes'] = (
                    elapsed_minutes - turnaround_minutes
                    if schedule['sorties']
                    else 0.0
                )
                plan_result['makespan_minutes'] = (
                    schedule['completion_minutes']
                )
                total_distance_m += plan_result['total_distance_m']
                makespan_minutes = max(
                    makespan_minutes,
                    plan_result['makespan_minutes'],
                )
                alns_iteration_values.append(
                    plan_result.get('alns_iterations') or 0
                )
                start_point = [
                    aircraft_item['longitude'],
                    aircraft_item['latitude'],
                ]
                sortie_results = []
                for sortie in schedule['sorties']:
                    sortie_index = sortie['sortie_index']
                    aircraft_label = _safe_route_segment(
                        aircraft_item['name'],
                        f'飞机{aircraft_index}',
                    )
                    route_name = (
                        f'{plan_name}-{plan_generated_at}-{aircraft_label}-航线{sortie_index}'
                    )
                    fly_points_obj = [start_point]
                    fly_points_obj.extend(
                        lonlat_points[index]
                        for index in sortie['point_indexes']
                    )
                    fly_points_obj.append(start_point)

                    file_id = _generate_file_id()
                    route_obj = Route.objects.create(
                        route_type='算法规划-多机巢多航线',
                        name=route_name,
                        camera_size=int(params.get('cameraSize', 1)),
                        height=int(uavflightheight),
                        file_id=file_id,
                        start_point=json.dumps(start_point, ensure_ascii=False),
                        end_point=json.dumps(start_point, ensure_ascii=False),
                        lines=json.dumps(fly_points_obj, ensure_ascii=False),
                    )
                    nest_id = _safe_route_segment(
                        aircraft_item.get('id'),
                        f'nest{aircraft_index}',
                    )
                    kmz_base_name = (
                        f'{nest_id}_{route_obj.id}_{plan_generated_at}'
                    )
                    out_path = os.path.join(
                        route_plan_path,
                        kmz_base_name,
                    )
                    kmz_file_path = out_path + '.kmz'
                    if os.path.exists(kmz_file_path):
                        os.remove(kmz_file_path)
                    if os.path.exists(out_path):
                        shutil.rmtree(out_path)

                    # 机巢仅作为起降参考点；KMZ 中的 Placemark 全部是
                    # 网格任务点，因此每个航点都执行 -90° 正射拍照。
                    kmz_task_points = fly_points_obj[1:-1]
                    generate_kmz(
                        out_path,
                        kmz_task_points,
                        uavflightheight,
                        photo_waypoint_indexes=range(len(kmz_task_points)),
                        speed_mps=auto_flight_speed_mps,
                        take_off_security_height=take_off_security_height,
                        take_off_point=start_point,
                    )
                    file_paths.append(kmz_file_path)
                    route_directories.append(out_path)

                    BufferFile.objects.create(
                        file_id=file_id,
                        file_name=kmz_base_name + '.kmz',
                        file_extension='.kmz',
                        file_path=kmz_file_path,
                        owner=username,
                        file_type='kml',
                        file_size=os.path.getsize(kmz_file_path)
                    )
                    route_objs.append(route_obj)
                    covered_feature_indexes = _covered_feature_indexes_for_route(
                        fly_points_obj,
                        group['aircraftFeatures'],
                        group['featureIndexes'],
                        geojson_data,
                    )
                    route_feature_indexes[route_obj.id] = covered_feature_indexes
                    completed_sorties += 1
                    progress_callback(
                        55 + int(completed_sorties / total_sorties * 25),
                        f'正在生成航线文件 {completed_sorties}/{total_sorties}',
                    )
                    sortie_result = {
                        'captureType': 'overview',
                        'aircraftIndex': aircraft_index,
                        'aircraftName': aircraft_item['name'],
                        'sortieIndex': sortie_index,
                        'routeId': route_obj.id,
                        'fileId': file_id,
                        'name': route_name,
                        'fileName': kmz_base_name + '.kmz',
                        'planGeneratedAt': plan_generated_at,
                        'distanceKm': round(sortie['distance_m'] / 1000, 3),
                        'flightTimeMinutes': round(
                            sortie['flight_time_minutes'], 2
                        ),
                        'startMinute': round(sortie['start_minute'], 2),
                        'endMinute': round(sortie['end_minute'], 2),
                        'points': fly_points_obj,
                        'coveredFeatureIndexes': covered_feature_indexes,
                    }
                    sortie_results.append(sortie_result)
                    route_results.append(sortie_result)

                aircraft_schedules.append({
                    'aircraftIndex': aircraft_index,
                    'aircraftId': aircraft_item.get('id'),
                    'aircraftName': aircraft_item['name'],
                    'planeSn': aircraft_item.get('plane_sn', ''),
                    'startPoint': start_point,
                    'parcelCount': group['parcelCount'],
                    'targetPointCount': group.get('targetPointCount', 0),
                    'excludedTargetPointCount': group.get(
                        'excludedTargetPointCount',
                        0,
                    ),
                    'sortieCount': schedule['sortie_count'],
                    'distanceKm': round(schedule['distance_m'] / 1000, 3),
                    'completionMinutes': round(
                        schedule['completion_minutes'], 2
                    ),
                    'sorties': sortie_results,
                })

            # 俯视图规划完成后，按浦南算法生成六边形覆盖中心点，
            # 再将全景点分配给最近机巢并独立执行多架次 ALNS 规划。
            progress_callback(81, '俯视图航线完成，正在生成全景图覆盖点')
            panoramic_projected, panoramic_lonlat = generate_panoramic_candidates(
                geojson_data,
                source_crs=_parse_geojson_crs(geojson_data),
                radius=float(params.get('panoramicHexRadius', 605.8)),
            )
            panoramic_groups = {
                item['index']: {'projected': [], 'lonlat': [], 'excluded': []}
                for item in aircraft_items
            }
            to_panoramic_crs = Transformer.from_crs(4490, 4528, always_xy=True)
            panoramic_depots = {
                item['index']: list(to_panoramic_crs.transform(
                    float(item['longitude']), float(item['latitude'])
                ))
                for item in aircraft_items
            }
            max_distance_m = max_distance_km * 1000
            excluded_panoramic_points = []
            for point_index, (projected_point, lonlat_point) in enumerate(
                zip(panoramic_projected, panoramic_lonlat), start=1
            ):
                nearest_aircraft = min(
                    aircraft_items,
                    key=lambda item: (
                        (projected_point[0] - panoramic_depots[item['index']][0]) ** 2
                        + (projected_point[1] - panoramic_depots[item['index']][1]) ** 2
                    ),
                )
                aircraft_index = nearest_aircraft['index']
                depot = panoramic_depots[aircraft_index]
                round_trip_m = 2 * (
                    (projected_point[0] - depot[0]) ** 2
                    + (projected_point[1] - depot[1]) ** 2
                ) ** 0.5
                if round_trip_m > max_distance_m + 1e-6:
                    excluded_panoramic_points.append({
                        'index': point_index,
                        'longitude': lonlat_point[0],
                        'latitude': lonlat_point[1],
                        'roundTripKm': round(round_trip_m / 1000, 3),
                    })
                    continue
                panoramic_groups[aircraft_index]['projected'].append(projected_point)
                panoramic_groups[aircraft_index]['lonlat'].append(lonlat_point)

            total_panoramic_distance_m = 0.0
            panoramic_makespan_minutes = 0.0
            for group_position, aircraft_item in enumerate(aircraft_items, start=1):
                aircraft_index = aircraft_item['index']
                target_group = panoramic_groups[aircraft_index]
                if not target_group['projected']:
                    panoramic_aircraft_schedules.append({
                        'aircraftIndex': aircraft_index,
                        'aircraftId': aircraft_item.get('id'),
                        'aircraftName': aircraft_item['name'],
                        'startPoint': [aircraft_item['longitude'], aircraft_item['latitude']],
                        'targetPointCount': 0,
                        'sortieCount': 0,
                        'distanceKm': 0,
                        'completionMinutes': 0,
                        'sorties': [],
                    })
                    continue
                progress_callback(
                    82 + group_position / max(aircraft_count, 1) * 8,
                    f'正在规划机巢 {aircraft_item["name"]} 的全景图航线',
                )
                planner_aircraft = {
                    **aircraft_item,
                    'depot': panoramic_depots[aircraft_index],
                }
                pano_plan = plan_multi_base_sorties(
                    target_group['projected'],
                    [planner_aircraft],
                    speed_kmh=speed_kmh,
                    max_flight_minutes=max_flight_minutes,
                    max_distance_km=max_distance_km,
                    turnaround_minutes=0,
                    attempts=12,
                    early_stop_rounds=3,
                    parallel=False,
                    alns_iterations=alns_iterations,
                )
                schedule = pano_plan['aircraft_schedules'][0]
                elapsed_minutes = 0.0
                start_point = [aircraft_item['longitude'], aircraft_item['latitude']]
                sortie_results = []
                for sortie in schedule['sorties']:
                    sortie['start_minute'] = elapsed_minutes
                    sortie['end_minute'] = elapsed_minutes + sortie['flight_time_minutes']
                    elapsed_minutes = sortie['end_minute']
                    sortie_index = sortie['sortie_index']
                    aircraft_label = _safe_route_segment(
                        aircraft_item['name'], f'飞机{aircraft_index}'
                    )
                    route_name = (
                        f'{plan_name}-{plan_generated_at}-{aircraft_label}-航线{sortie_index}'
                    )
                    fly_points_obj = [start_point]
                    fly_points_obj.extend(
                        target_group['lonlat'][index]
                        for index in sortie['point_indexes']
                    )
                    fly_points_obj.append(start_point)
                    file_id = _generate_file_id()
                    route_obj = Route.objects.create(
                        route_type='算法规划-全景图-多机巢多航线',
                        name=route_name,
                        camera_size=int(params.get('cameraSize', 1)),
                        height=int(uavflightheight),
                        file_id=file_id,
                        start_point=json.dumps(start_point, ensure_ascii=False),
                        end_point=json.dumps(start_point, ensure_ascii=False),
                        lines=json.dumps(fly_points_obj, ensure_ascii=False),
                    )
                    nest_id = _safe_route_segment(
                        aircraft_item.get('id'), f'nest{aircraft_index}'
                    )
                    kmz_base_name = (
                        f'{nest_id}_{route_obj.id}_{plan_generated_at}_panorama'
                    )
                    out_path = os.path.join(route_plan_path, kmz_base_name)
                    kmz_file_path = out_path + '.kmz'
                    if os.path.exists(kmz_file_path):
                        os.remove(kmz_file_path)
                    if os.path.exists(out_path):
                        shutil.rmtree(out_path)
                    kmz_task_points = fly_points_obj[1:-1]
                    generate_kmz(
                        out_path,
                        kmz_task_points,
                        uavflightheight,
                        photo_waypoint_indexes=range(len(kmz_task_points)),
                        speed_mps=auto_flight_speed_mps,
                        take_off_security_height=take_off_security_height,
                        take_off_point=start_point,
                        capture_mode='panorama',
                    )
                    file_paths.append(kmz_file_path)
                    route_directories.append(out_path)
                    BufferFile.objects.create(
                        file_id=file_id,
                        file_name=kmz_base_name + '.kmz',
                        file_extension='.kmz',
                        file_path=kmz_file_path,
                        owner=username,
                        file_type='kml',
                        file_size=os.path.getsize(kmz_file_path),
                    )
                    route_objs.append(route_obj)
                    covered_feature_indexes = _covered_feature_indexes_for_route(
                        fly_points_obj,
                        _normalize_geojson_features(geojson_data),
                        list(range(len(_normalize_geojson_features(geojson_data)))),
                        geojson_data,
                        half_grid_size=700.0,
                    )
                    route_feature_indexes[route_obj.id] = covered_feature_indexes
                    sortie_result = {
                        'captureType': 'panorama',
                        'aircraftIndex': aircraft_index,
                        'aircraftName': aircraft_item['name'],
                        'sortieIndex': sortie_index,
                        'routeId': route_obj.id,
                        'fileId': file_id,
                        'name': route_name,
                        'fileName': kmz_base_name + '.kmz',
                        'planGeneratedAt': plan_generated_at,
                        'distanceKm': round(sortie['distance_m'] / 1000, 3),
                        'flightTimeMinutes': round(sortie['flight_time_minutes'], 2),
                        'startMinute': round(sortie['start_minute'], 2),
                        'endMinute': round(sortie['end_minute'], 2),
                        'points': fly_points_obj,
                        'coveredFeatureIndexes': covered_feature_indexes,
                    }
                    sortie_results.append(sortie_result)
                    panoramic_route_results.append(sortie_result)
                completion_minutes = elapsed_minutes if schedule['sorties'] else 0.0
                total_panoramic_distance_m += pano_plan['total_distance_m']
                panoramic_makespan_minutes = max(
                    panoramic_makespan_minutes, completion_minutes
                )
                panoramic_aircraft_schedules.append({
                    'aircraftIndex': aircraft_index,
                    'aircraftId': aircraft_item.get('id'),
                    'aircraftName': aircraft_item['name'],
                    'startPoint': start_point,
                    'targetPointCount': len(target_group['lonlat']),
                    'sortieCount': schedule['sortie_count'],
                    'distanceKm': round(schedule['distance_m'] / 1000, 3),
                    'completionMinutes': round(completion_minutes, 2),
                    'sorties': sortie_results,
                })

            for aircraft_item in aircraft_items:
                if assigned_features[aircraft_item['index']]:
                    continue
                aircraft_schedules.append({
                    'aircraftIndex': aircraft_item['index'],
                    'aircraftId': aircraft_item.get('id'),
                    'aircraftName': aircraft_item['name'],
                    'planeSn': aircraft_item.get('plane_sn', ''),
                    'startPoint': [
                        aircraft_item['longitude'],
                        aircraft_item['latitude'],
                    ],
                    'parcelCount': 0,
                    'sortieCount': 0,
                    'distanceKm': 0,
                    'completionMinutes': 0,
                    'sorties': [],
                })

            progress_callback(92, '正在保存监管任务和地块关联')
            supervision_projects, polygon_objs, point_results = _create_supervision_task(
                geojson_data,
                route_objs,
                params,
                username,
                county,
                route_feature_indexes=route_feature_indexes,
            )
            supervision_project = supervision_projects[0] if supervision_projects else None

            logger.info(
                f'多机多架次规划成功，监管任务数: {len(supervision_projects)}，'
                f'飞机数: {aircraft_count}，总架次: {len(route_objs)}，'
                f'完工时间: {makespan_minutes:.2f} 分钟'
            )
            response_data['data'] = {
                'points': route_results[0]['points'] if len(route_results) == 1 else [],
                'routes': route_results + panoramic_route_results,
                'overviewRoutes': route_results,
                'panoramaRoutes': panoramic_route_results,
                'aircraftSchedules': aircraft_schedules,
                'panoramaAircraftSchedules': panoramic_aircraft_schedules,
                'aircraftCount': aircraft_count,
                'usedAircraftCount': sum(
                    1 for schedule in aircraft_schedules
                    if schedule['sortieCount'] > 0
                ),
                'totalSorties': total_sorties_value + len(panoramic_route_results),
                'overviewSorties': total_sorties_value,
                'panoramaSorties': len(panoramic_route_results),
                'planGeneratedAt': plan_generated_at,
                'speedKmh': speed_kmh,
                'autoFlightSpeed': auto_flight_speed_mps,
                'maxFlightMinutes': max_flight_minutes,
                'maxDistanceKm': max_distance_km,
                'takeOffSecurityHeight': take_off_security_height,
                'turnaroundMinutes': turnaround_minutes,
                'optimizer': 'ALNS-按机巢独立规划',
                'alnsIterations': max(alns_iteration_values, default=0),
                'totalDistanceKm': round(
                    (total_distance_m + total_panoramic_distance_m) / 1000, 3
                ),
                'estimatedCompletionMinutes': round(
                    makespan_minutes + panoramic_makespan_minutes, 2
                ),
                'gridSizeMeters': 150,
                'targetPointCount': target_point_count,
                'panoramaHexRadiusMeters': float(params.get('panoramicHexRadius', 605.8)),
                'panoramaCoverageRadiusMeters': 700,
                'panoramaTargetPointCount': len(panoramic_lonlat),
                'excludedPanoramaTargetPointCount': len(excluded_panoramic_points),
                'excludedTargetPointCount': excluded_target_point_count,
                'featureAssignments': feature_assignments,
                'parcelFilter': parcel_filter_summary,
                'supervisionProjectId': supervision_project.id if supervision_project else None,
                'supervisionProjectIds': [p.id for p in supervision_projects],
                'polygonId': polygon_objs[0].id if polygon_objs else None,
                'polygonIds': [polygon.id for polygon in polygon_objs],
                'pointId': point_results[0]['pointId'],
                'pointDistance': point_results[0]['pointDistance'],
                'polygonPointResults': point_results,
            }
            progress_callback(98, '正在整理规划结果')
            return JsonResponse(response_data)
        except ValueError as e:
            logger.error(f'GeoJSON 航线规划参数错误: {e}')
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            for route_directory in route_directories:
                if os.path.exists(route_directory):
                    shutil.rmtree(route_directory, ignore_errors=True)
            transaction.set_rollback(True)
            return JsonResponse({'code': 1, 'msg': str(e), 'data': {}})
        except Exception as e:
            logger.error(f'GeoJSON 航线规划失败: {e}')
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            for route_directory in route_directories:
                if os.path.exists(route_directory):
                    shutil.rmtree(route_directory, ignore_errors=True)
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': f'航线规划失败: {e}', 'data': {}})
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


def _run_route_plan_job(job_id):
    close_old_connections()
    try:
        params = read_payload(job_id)
        username = params.pop('_jobUsername', 'WXAdmin')
        county = params.pop('_jobCounty', '无锡市(320200)')
        update_status(job_id, status='running', progress=2, message='后台规划进程已启动')
        request = RequestFactory().post(
            '/api/route/route_plan',
            data=json.dumps(params, ensure_ascii=False),
            content_type='application/json',
        )
        request.session = {'username': username}
        request._route_job_username = username
        request._route_job_county = county
        request._route_job_progress = lambda progress, message: update_status(
            job_id,
            status='running',
            progress=progress,
            message=message,
        )
        response = _execute_route_plan_request(request)
        response_data = json.loads(response.content.decode('utf-8'))
        if response_data.get('code') != 0:
            raise ValueError(response_data.get('msg') or '航线规划失败')
        write_result(job_id, response_data.get('data') or {})
        update_status(job_id, status='completed', progress=100, message='航线规划完成')
    except Exception as exc:
        logger.exception('后台航线规划失败')
        update_status(job_id, status='failed', progress=100, message=str(exc))
    finally:
        close_old_connections()


def _execute_legacy_route_plan_request(request):
    """

    请求和响应字段保持旧版不变，内部航点排序使用当前 ALNS 规划器。
    """
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})

    response_data = {'code': 0, 'msg': '航线规划成功！', 'data': {}}
    file_paths = []
    route_directories = []
    temp_dir = ''

    with transaction.atomic():
        try:
            logger.info('接收兼容版 GeoJSON 航线规划任务')
            try:
                current_user = parse_jwt_token(request)
                username = current_user.username
                county = current_user.county
            except Exception as exc:
                logger.warning('兼容版航线接口未读取到登录用户: %s', exc)
                username = request.session.get('username', 'WXAdmin')
                county = '无锡市(320200)'

            params = json.loads(request.body.decode('utf-8'))
            geojson_data = params.get('polygon') or params.get('geojson') or params
            features = _normalize_geojson_features(geojson_data)
            planning_geojson = _feature_collection(features, geojson_data)
            plan_name = (
                params.get('name')
                or params.get('planName')
                or f"route_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            auto_flight_speed_mps = float(
                params.get(
                    'autoFlightSpeed',
                    params.get('auto_flight_speed', 15.0),
                )
            )
            speed_kmh = auto_flight_speed_mps * 3.6
            max_flight_minutes = float(
                params.get(
                    'maxFlightMinutes',
                    params.get('max_flight_minutes', 20.0),
                )
            )
            take_off_security_height = float(
                params.get(
                    'takeOffSecurityHeight',
                    params.get('take_off_security_height', 115.0),
                )
            )
            uavflightheight = float(
                params.get(
                    'uavflightheight',
                    params.get('uavFlightHeight', take_off_security_height),
                )
            )

            if Route.objects.filter(name=plan_name).exists():
                return JsonResponse({'code': 1, 'msg': '该航线名称已存在', 'data': {}})

            nearest_nest, nest_distance = find_nearest_nest(planning_geojson)
            if not nearest_nest:
                return JsonResponse({
                    'code': 1,
                    'msg': '未找到可用机巢，请先维护机巢经纬度',
                    'data': {},
                })

            start_point = [nearest_nest.longitude, nearest_nest.latitude]
            end_point = [nearest_nest.longitude, nearest_nest.latitude]
            temp_dir = os.path.join(
                settings.BASE_DIR,
                'static',
                'shp',
                f'route_geojson_{uuid.uuid4().hex}',
            )
            shp_path = geojson_to_shp(planning_geojson, temp_dir)
            projected_points, lonlat_points, prj_path = generate_flight_candidates(
                shp_path
            )
            if not projected_points:
                return JsonResponse({
                    'code': 1,
                    'msg': '航线规划失败，未生成有效航点',
                    'data': {},
                })

            depot = lonlat2geo(
                prj_path,
                nearest_nest.longitude,
                nearest_nest.latitude,
            )
            plan_result = plan_multi_base_sorties(
                projected_points,
                [{
                    'index': 1,
                    'id': nearest_nest.id,
                    'name': nearest_nest.name,
                    'plane_sn': nearest_nest.plane_sn,
                    'depot': depot,
                }],
                speed_kmh=speed_kmh,
                max_flight_minutes=max_flight_minutes,
                turnaround_minutes=0.0,
                parallel=False,
            )

            schedule = plan_result['aircraft_schedules'][0]
            if schedule['sortie_count'] > 1:
                return JsonResponse({
                    'code': 1,
                    'msg': '当前目标无法用单一航线巡飞，请检查数量或距离',
                    'data': {},
                })
            fly_points_obj = [start_point]
            for sortie in schedule['sorties']:
                fly_points_obj.extend(
                    lonlat_points[index]
                    for index in sortie['point_indexes']
                )
                fly_points_obj.append(start_point)
            if len(fly_points_obj) <= 1:
                return JsonResponse({
                    'code': 1,
                    'msg': '航线规划失败，未生成有效航点',
                    'data': {},
                })

            route_plan_path = os.path.join(
                settings.BASE_DIR, 'static', 'route_plan'
            )
            os.makedirs(route_plan_path, exist_ok=True)
            out_path = os.path.join(route_plan_path, plan_name)
            kmz_file_path = out_path + '.kmz'
            if os.path.exists(kmz_file_path):
                os.remove(kmz_file_path)
            if os.path.exists(out_path):
                shutil.rmtree(out_path)

            generate_kmz(
                out_path,
                fly_points_obj,
                uavflightheight,
                speed_mps=auto_flight_speed_mps,
                take_off_security_height=take_off_security_height,
            )
            file_paths = [kmz_file_path]
            route_directories = [out_path]

            file_id = _generate_file_id()
            BufferFile.objects.create(
                file_id=file_id,
                file_name=plan_name + '.kmz',
                file_extension='.kmz',
                file_path=kmz_file_path,
                owner=username,
                file_type='kml',
                file_size=os.path.getsize(kmz_file_path),
            )
            route_obj = Route.objects.create(
                route_type='算法规划',
                name=plan_name,
                camera_size=int(params.get('cameraSize', 1)),
                height=int(uavflightheight),
                file_id=file_id,
                start_point=json.dumps(start_point, ensure_ascii=False),
                end_point=json.dumps(end_point, ensure_ascii=False),
                lines=json.dumps(fly_points_obj, ensure_ascii=False),
            )
            supervision_projects, polygon_objs, point_results = (
                _create_supervision_task(
                    planning_geojson,
                    [route_obj],
                    params,
                    username,
                    county,
                )
            )
            supervision_project = supervision_projects[0] if supervision_projects else None
            polygon_obj = polygon_objs[0] if polygon_objs else None
            point_result = point_results[0] if point_results else {}

            logger.info(
                '兼容版 GeoJSON 航线规划成功，机巢: %s，监管任务数: %s',
                nearest_nest.name,
                len(supervision_projects),
            )
            response_data['data'] = {
                'points': fly_points_obj,
                'fileId': file_id,
                'routeId': route_obj.id,
                'supervisionProjectId': supervision_project.id if supervision_project else None,
                'supervisionProjectIds': [p.id for p in supervision_projects],
                'polygonId': polygon_obj.id if polygon_obj else None,
                'pointId': point_result.get('pointId'),
                'pointDistance': point_result.get('pointDistance'),
                'nest': {
                    'id': nearest_nest.id,
                    'name': nearest_nest.name,
                    'longitude': nearest_nest.longitude,
                    'latitude': nearest_nest.latitude,
                    'distance': round(nest_distance, 2),
                },
                'startPoint': start_point,
                'endPoint': end_point,
            }
            return JsonResponse(response_data)
        except ValueError as exc:
            logger.error('兼容版 GeoJSON 航线规划参数错误: %s', exc)
            transaction.set_rollback(True)
            return JsonResponse({'code': 1, 'msg': str(exc), 'data': {}})
        except Exception as exc:
            logger.exception('兼容版 GeoJSON 航线规划失败')
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
            for route_directory in route_directories:
                if os.path.exists(route_directory):
                    shutil.rmtree(route_directory, ignore_errors=True)
            transaction.set_rollback(True)
            return JsonResponse({
                'code': 500,
                'msg': f'航线规划失败: {exc}',
                'data': {},
            })
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


def add_route_plan(request):
    """
    专供外部系统调用的航线规划接口。

    接收地块 GeoJSON，默认使用机巢表中的「无锡01」执行与 route_plan_async
    相同的多机巢多航线后台规划，并返回任务 ID 与 KMZ 下载地址前缀。
    """
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        params = json.loads(request.body.decode('utf-8'))
        geojson_data = params.get('polygon') or params.get('geojson')
        if not geojson_data:
            return JsonResponse({'code': 1, 'msg': '缺少地块 GeoJSON 数据', 'data': {}})

        _normalize_geojson_features(geojson_data)

        plan_name = (
            params.get('name')
            or params.get('planName')
            or f"external_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        if (
            Route.objects.filter(name=plan_name).exists()
            or Route.objects.filter(name__startswith=f'{plan_name}-').exists()
        ):
            return JsonResponse({'code': 1, 'msg': '该航线名称已存在', 'data': {}})

        aircraft = (
            params.get('aircraft')
            or params.get('aircraftList')
            or params.get('aircrafts')
        )
        if not aircraft:
            aircraft = _resolve_external_default_aircraft()

        params['name'] = plan_name
        params['polygon'] = geojson_data
        params['aircraft'] = aircraft
        params.setdefault('autoFlightSpeed', 15)
        params.setdefault('maxFlightMinutes', 20)
        params.setdefault('takeOffSecurityHeight', 115)
        params.setdefault('rangeKm', AIRCRAFT_PARCEL_RANGE_KM)
        params.setdefault('alreadyFiltered', False)

        try:
            current_user = parse_jwt_token(request)
            params['_jobUsername'] = current_user.username
            params['_jobCounty'] = current_user.county
        except Exception:
            params['_jobUsername'] = request.session.get('username', 'WXAdmin')
            params['_jobCounty'] = '无锡市(320200)'

        job_id = create_job('route-plan', params)
        pid = _start_background_process(run_route_plan_job, job_id)
        update_status(job_id, processId=pid)

        return JsonResponse({
            'code': 0,
            'msg': '规划任务已提交',
            'data': {
                'jobId': job_id,
                'kmzDownloadUrl': EXTERNAL_JOB_KMZ_URL_PREFIX,
                'kmzDownloadSuffix': EXTERNAL_JOB_KMZ_URL_SUFFIX,
            },
        })
    except ValueError as exc:
        return JsonResponse({'code': 1, 'msg': str(exc), 'data': {}})
    except Exception as exc:
        logger.exception('外部航线规划任务创建失败')
        return JsonResponse({'code': 500, 'msg': str(exc), 'data': {}})


def add_route_plan_async(request):
    """创建多飞机、多架次后台规划任务并立即返回任务编号。"""
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        params = json.loads(request.body.decode('utf-8'))
        geojson_data = params.get('polygon') or params.get('geojson')
        aircraft = params.get('aircraft') or params.get('aircraftList') or []
        if not geojson_data:
            return JsonResponse({'code': 1, 'msg': '缺少规划区域 GeoJSON 数据', 'data': {}})
        if not aircraft:
            return JsonResponse({'code': 1, 'msg': '请先上传飞机点位', 'data': {}})
        plan_name = params.get('name') or params.get('planName')
        if not plan_name:
            return JsonResponse({'code': 1, 'msg': '请输入任务名称', 'data': {}})
        if (
            Route.objects.filter(name=plan_name).exists()
            or Route.objects.filter(name__startswith=f'{plan_name}-').exists()
        ):
            return JsonResponse({'code': 1, 'msg': '该航线名称已存在', 'data': {}})
        try:
            current_user = parse_jwt_token(request)
            params['_jobUsername'] = current_user.username
            params['_jobCounty'] = current_user.county
        except Exception:
            params['_jobUsername'] = request.session.get('username', 'WXAdmin')
            params['_jobCounty'] = '无锡市(320200)'
        job_id = create_job('route-plan', params)
        pid = _start_background_process(run_route_plan_job, job_id)
        update_status(job_id, processId=pid)
        return JsonResponse({
            'code': 0,
            'msg': '规划任务已提交',
            'data': {'jobId': job_id},
        })
    except Exception as exc:
        logger.exception('创建后台规划任务失败')
        return JsonResponse({'code': 500, 'msg': str(exc), 'data': {}})


def route_list(request):
    """
    获取已有航线列表
    """
    try:
        if request.method == 'POST':
            para = json.loads(request.body)
            page = para.get('pageIndex', 1)
            limit = para.get('pageSize', 5)
            route_type = para.get('routeType', '')
            route_type = route_type.split(',')
            result_objs = Route.objects.filter(route_type__in=route_type).all().order_by('-create_time')
            paginator = Paginator(result_objs, limit)
            results = paginator.page(page)
            data_list = []
            for i in results:
                try:
                    route_points = json.loads(i.lines or '[]')
                except (TypeError, json.JSONDecodeError):
                    route_points = []
                distance_km = 0.0
                for start, end in zip(route_points, route_points[1:]):
                    if (
                        not isinstance(start, (list, tuple))
                        or not isinstance(end, (list, tuple))
                        or len(start) < 2
                        or len(end) < 2
                    ):
                        continue
                    distance_km += great_circle(
                        (float(start[1]), float(start[0])),
                        (float(end[1]), float(end[0])),
                    ).kilometers
                data_obj = {
                    'id': i.id,
                    'name': i.name,
                    'fileId': i.file_id,
                    'routeType': i.route_type,
                    'captureType': (
                        'panorama' if '全景图' in i.route_type else 'overview'
                    ),
                    'distanceKm': round(distance_km, 3),
                    'createTime': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                data_list.append(data_obj)
            logger.info(f'查询已有航线成功,数量为{result_objs.count()}')
            return JsonResponse(
                {'code': 0, 'msg': '查询已有航线成功!!!', 'data': data_list, 'total': result_objs.count()})
        else:
            return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    except Exception as e:
        logger.error("查询已有航线失败，错误信息为{}".format(e))
        return JsonResponse({'code': 500, 'msg': e, 'data': {}})


def route_map_detail(request, file_id):
    """返回历史架次的航线、飞机起降点以及该架次覆盖的目标地块。"""
    try:
        route_obj = Route.objects.filter(file_id=file_id).first()
        if not route_obj:
            return JsonResponse({'code': 1, 'msg': '航线不存在', 'data': {}})

        try:
            route_points = json.loads(route_obj.lines or '[]')
        except (TypeError, json.JSONDecodeError):
            route_points = []
        try:
            start_point = json.loads(route_obj.start_point or '[]')
        except (TypeError, json.JSONDecodeError):
            start_point = []

        relations = list(
            SupervisionProjectRoute.objects.filter(
                route_id=route_obj.id
            ).order_by('-id')
        )
        relation_project_ids = list(dict.fromkeys(
            relation.supervision_project_id
            for relation in relations
        ))
        target_polygons = []
        route_name_info = _parse_algorithm_route_name(route_obj.name)
        aircraft_name = route_name_info['aircraft_name']
        sortie_index = route_name_info['sortie_index']
        if relation_project_ids and len(route_points) > 2:
            lonlat_to_projected = Transformer.from_crs(
                4490,
                4549,
                always_xy=True,
            )
            coverage_cells = []
            capture_type = (
                'panorama' if '全景图' in route_obj.route_type else 'overview'
            )
            half_grid_size = 700.0 if capture_type == 'panorama' else 75.0
            for point in route_points[1:-1]:
                if not isinstance(point, (list, tuple)) or len(point) < 2:
                    continue
                x, y = lonlat_to_projected.transform(
                    float(point[0]),
                    float(point[1]),
                )
                coverage_cells.append(
                    box(
                        x - half_grid_size,
                        y - half_grid_size,
                        x + half_grid_size,
                        y + half_grid_size,
                    )
                )
            polygon_records = SupervisionProjectPolygon.objects.filter(
                supervision_project_id__in=relation_project_ids,
                is_del=0,
            )
            for polygon_record in polygon_records:
                try:
                    feature = json.loads(polygon_record.polygon)
                    geometry_data = (
                        feature.get('geometry')
                        if isinstance(feature, dict) and feature.get('type') == 'Feature'
                        else feature
                    )
                    geometry = shape(geometry_data)
                    polygon_crs = _parse_geojson_crs(
                        feature if isinstance(feature, dict) else {}
                    )
                    polygon_to_projected = Transformer.from_crs(
                        polygon_crs,
                        4549,
                        always_xy=True,
                    )
                    projected_geometry = shapely_transform(
                        polygon_to_projected.transform,
                        geometry,
                    )
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                covered_indexes = [
                    index
                    for index, coverage_cell in enumerate(
                        coverage_cells,
                        start=1,
                    )
                    if coverage_cell.intersects(projected_geometry)
                ]
                if covered_indexes:
                    target_polygons.append({
                        'id': polygon_record.id,
                        'supervisionProjectId': polygon_record.supervision_project_id,
                        'feature': feature,
                        'aircraftName': aircraft_name,
                        'routeName': route_obj.name,
                        'sortieIndex': sortie_index,
                        'coveredPhotoPointCount': len(covered_indexes),
                        'coveredPhotoPointIndexes': covered_indexes,
                    })

        return JsonResponse({
            'code': 0,
            'msg': '查询成功',
            'data': {
                'routeId': route_obj.id,
                'routeName': route_obj.name,
                'routeType': route_obj.route_type,
                'captureType': (
                    'panorama' if '全景图' in route_obj.route_type else 'overview'
                ),
                'planGeneratedAt': route_name_info['plan_generated_at'],
                'aircraftName': aircraft_name,
                'sortieIndex': sortie_index,
                'routePoints': route_points,
                'startPoint': start_point,
                'supervisionProjectId': (
                    relation_project_ids[0] if relation_project_ids else None
                ),
                'supervisionProjectIds': relation_project_ids,
                'targetPolygons': target_polygons,
            },
        })
    except Exception as exc:
        logger.exception('历史架次地图详情查询失败')
        return JsonResponse({'code': 500, 'msg': str(exc), 'data': {}})


def _delete_route_records(file_ids):
    """事务内删除航线相关记录，事务提交后再清理磁盘文件。"""
    file_ids = list(dict.fromkeys(
        str(item).strip()
        for item in file_ids
        if item is not None and str(item).strip()
    ))
    if not file_ids:
        raise ValueError('没有可删除的航线')

    route_objs = list(Route.objects.filter(file_id__in=file_ids))
    route_ids = [route.id for route in route_objs]
    relations = list(
        SupervisionProjectRoute.objects.filter(route_id__in=route_ids)
    )
    project_ids = {relation.supervision_project_id for relation in relations}
    buffer_files = list(BufferFile.objects.filter(file_id__in=file_ids))
    file_paths = [item.file_path for item in buffer_files if item.file_path]

    SupervisionProjectRoute.objects.filter(route_id__in=route_ids).delete()
    Route.objects.filter(id__in=route_ids).delete()
    BufferFile.objects.filter(file_id__in=file_ids).delete()

    deleted_project_ids = []
    for project_id in project_ids:
        if SupervisionProjectRoute.objects.filter(
            supervision_project_id=project_id
        ).exists():
            continue
        SupervisionProjectPolygon.objects.filter(
            supervision_project_id=project_id
        ).delete()
        SupervisionProject.objects.filter(id=project_id).delete()
        deleted_project_ids.append(project_id)

    route_plan_root = os.path.abspath(
        os.path.join(settings.BASE_DIR, 'static', 'route_plan')
    )

    def remove_files():
        for file_path in file_paths:
            absolute_path = os.path.abspath(file_path)
            try:
                is_inside_route_plan = (
                    os.path.commonpath([route_plan_root, absolute_path])
                    == route_plan_root
                )
            except ValueError:
                is_inside_route_plan = False
            if not is_inside_route_plan:
                logger.warning('跳过工作目录外的航线文件: %s', absolute_path)
                continue
            try:
                if os.path.isfile(absolute_path):
                    os.remove(absolute_path)
                route_directory = os.path.splitext(absolute_path)[0]
                if os.path.isdir(route_directory):
                    shutil.rmtree(route_directory, ignore_errors=True)
            except OSError:
                logger.exception('删除航线文件失败: %s', absolute_path)

    transaction.on_commit(remove_files)
    return {
        'deletedRouteCount': len(route_objs),
        'deletedProjectCount': len(deleted_project_ids),
    }


def delete_plan(request):
    """
    删除航线
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            file_id = params.get('route_id')
            logger.info("接收删除航线请求")
            result = _delete_route_records([file_id])
            logger.info({'code': 0, 'msg': '删除成功'})
            return JsonResponse({'code': 0, 'msg': '删除成功', 'data': result})
        except Exception as e:
            logger.error("删除航线失败，错误信息为{}".format(e))
            transaction.set_rollback(True)
            return JsonResponse({'code': 500, 'msg': f'{e}'})


def batch_delete_plans(request):
    """批量删除任务或某架飞机的全部架次。"""
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        params = json.loads(request.body.decode('utf-8'))
        file_ids = params.get('fileIds') or params.get('file_ids') or []
        if not isinstance(file_ids, list):
            return JsonResponse({'code': 1, 'msg': 'fileIds 必须是数组', 'data': {}})
        if len(file_ids) > 10000:
            return JsonResponse({'code': 1, 'msg': '单次最多删除 10000 条航线', 'data': {}})
        with transaction.atomic():
            result = _delete_route_records(file_ids)
        return JsonResponse({'code': 0, 'msg': '批量删除成功', 'data': result})
    except ValueError as exc:
        return JsonResponse({'code': 1, 'msg': str(exc), 'data': {}})
    except Exception as exc:
        logger.exception('批量删除航线失败')
        return JsonResponse({'code': 500, 'msg': str(exc), 'data': {}})


def filter_parcels_by_range(request):
    """创建地块范围后台筛选任务。"""
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        params = json.loads(request.body.decode('utf-8'))
        geojson_data = params.get('geojson') or params.get('polygon')
        aircraft_list = (
            params.get('aircraft')
            or params.get('aircraftList')
            or params.get('aircrafts')
            or []
        )
        radius_km = float(
            params.get('radiusKm', params.get('rangeKm', AIRCRAFT_PARCEL_RANGE_KM))
        )
        if not aircraft_list:
            return JsonResponse({'code': 1, 'msg': '请先上传飞机点位', 'data': {}})
        _normalize_geojson_features(geojson_data)
        job_id = create_job('parcel-filter', {
            'geojson': geojson_data,
            'aircraft': aircraft_list,
            'radiusKm': radius_km,
        })
        pid = _start_background_process(run_filter_job, job_id)
        update_status(job_id, processId=pid)
        return JsonResponse({
            'code': 0,
            'msg': '地块筛选任务已提交',
            'data': {'jobId': job_id},
        })
    except ValueError as e:
        return JsonResponse({'code': 1, 'msg': str(e), 'data': {}})
    except Exception as e:
        logger.error(f'地块筛选失败: {e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': {}})


def route_job_status(request, job_id):
    if request.method != 'GET':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        return JsonResponse({
            'code': 0,
            'msg': '查询成功',
            'data': read_job(job_id),
        })
    except (ValueError, FileNotFoundError) as exc:
        return JsonResponse({'code': 404, 'msg': str(exc), 'data': {}})
    except Exception as exc:
        logger.exception('查询航线后台任务失败')
        return JsonResponse({'code': 500, 'msg': str(exc), 'data': {}})


def download_job_kmz(request, job_id):
    """下载外部规划任务生成的俯视图 KMZ 文件（统一打包为 ZIP）。"""
    if request.method != 'GET':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        validate_job_id(job_id)
        job = read_job(job_id)
        if job.get('status') != 'completed':
            return JsonResponse({
                'code': 1,
                'msg': f"任务尚未完成，当前状态：{job.get('status')}",
                'data': {
                    'status': job.get('status'),
                    'progress': job.get('progress'),
                    'message': job.get('message'),
                },
            })
        kmz_files = _collect_job_overview_kmz_files(job.get('result') or {})
        if not kmz_files:
            return JsonResponse({'code': 404, 'msg': '该任务没有可下载的 KMZ 文件', 'data': {}})

        zip_path = job_file(job_id, 'overview_routes.kmz.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            for buffer_file in kmz_files:
                archive.write(buffer_file.file_path, arcname=buffer_file.file_name)
        return FileResponse(
            open(zip_path, 'rb'),
            as_attachment=True,
            filename=f'{job_id}_routes.kmz.zip',
            content_type='application/zip',
        )
    except ValueError as exc:
        return JsonResponse({'code': 404, 'msg': str(exc), 'data': {}})
    except Exception as exc:
        logger.exception('下载规划任务 KMZ 失败')
        return JsonResponse({'code': 500, 'msg': str(exc), 'data': {}})


def download_excluded_parcels(request, job_id):
    if request.method != 'GET':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式', 'data': {}})
    try:
        validate_job_id(job_id)
        zip_path = job_file(job_id, 'excluded_parcels.zip')
        if not os.path.exists(zip_path):
            return JsonResponse({'code': 404, 'msg': '该任务没有可下载的超范围地块', 'data': {}})
        return FileResponse(
            open(zip_path, 'rb'),
            as_attachment=True,
            filename='超出飞机服务范围地块.zip',
            content_type='application/zip',
        )
    except ValueError as exc:
        return JsonResponse({'code': 404, 'msg': str(exc), 'data': {}})


def receive_zip(request):
    """
    接收航线规划检测区域压缩包
    :param request:
    :return:
    """
    logger.info('接收航线规划检测区域压缩包上传请求')
    file_path_list = []
    try:
        upload_type = request.POST.get('uploadType')
        shp_dir = os.path.join(settings.BASE_DIR, 'static/shp')
        os.makedirs(shp_dir, exist_ok=True)

        if upload_type == 'multi-aircraft-aircraft':
            aircraft_files = request.FILES.getlist('files')
            if not aircraft_files:
                return JsonResponse({'code': 1, 'msg': '请选择飞机点位 SHP 文件'})
            if not any(file.name.lower().endswith('.shp') for file in aircraft_files):
                return JsonResponse({'code': 1, 'msg': '请同时上传 .shp 及 .dbf、.shx、.prj 等配套文件'})
            aircraft_dir = os.path.join(shp_dir, f'aircraft_{uuid.uuid4().hex}')
            file_path_list.append(aircraft_dir)
            _save_uploaded_files(aircraft_files, aircraft_dir)
            parsed_data = _parse_aircraft_shp_directory(aircraft_dir)
            logger.info(
                '飞机点位解析成功，飞机 %s 架',
                parsed_data['summary']['aircraftCount'],
            )
            return JsonResponse({
                'code': 0,
                'msg': '飞机点位解析成功',
                'data': parsed_data,
            })

        shp_zip_file = request.FILES.get('files')
        if not shp_zip_file:
            return JsonResponse({'code': 1, 'msg': '请选择要上传的 ZIP 数据包'})
        if not shp_zip_file.name.lower().endswith('.zip'):
            return JsonResponse({'code': 1, 'msg': '航线规划数据包仅支持 ZIP 格式'})
        safe_file_name = os.path.basename(shp_zip_file.name)
        nodetection_shp_path = os.path.join(shp_dir, safe_file_name)
        if os.path.exists(nodetection_shp_path):
            os.remove(nodetection_shp_path)
        if os.path.exists(os.path.splitext(nodetection_shp_path)[0]):
            shutil.rmtree(os.path.splitext(nodetection_shp_path)[0])
        with open(nodetection_shp_path, 'wb+') as destination:
            for chunk in shp_zip_file.chunks():
                destination.write(chunk)
        file_path_list.append(nodetection_shp_path)
        # 解压shp文件夹
        unzip_path = os.path.splitext(nodetection_shp_path)[0]
        unzip_file(nodetection_shp_path, unzip_path)
        file_path_list.append(unzip_path)
        if upload_type == 'multi-aircraft-parcel':
            parsed_data = _parse_parcel_archive(unzip_path)
            logger.info(
                '地块数据包解析成功，地块 %s 个',
                parsed_data['summary']['parcelCount'],
            )
            return JsonResponse({
                'code': 0,
                'msg': '地块数据包解析成功',
                'data': parsed_data,
            })
        if upload_type == 'multi-aircraft-route':
            parsed_data = _parse_route_input_archive(unzip_path)
            logger.info(
                '航线规划数据包解析成功，地块 %s 个，飞机 %s 架',
                parsed_data['summary']['parcelCount'],
                parsed_data['summary']['aircraftCount'],
            )
            return JsonResponse({
                'code': 0,
                'msg': '航线规划数据包解析成功',
                'data': parsed_data,
            })

        shp_list = [
            os.path.join(root, file_name)
            for root, _, files in os.walk(unzip_path)
            for file_name in files
            if file_name.lower().endswith('.shp')
        ]
        if len(shp_list) == 0:
            logger.info('未检测到shp文件')
            return JsonResponse({'code': 500, 'msg': "未检测到shp文件"})
        else:
            shp_path = shp_list[0]
            point_data = get_geometry_coordinates(shp_path)
            if len(point_data) == 0:
                logger.info('未检测到shp数据')
                return JsonResponse({'code': 500, 'msg': "未检测到shp数据"})
            else:
                logger.info('上传检测区域压缩包成功！！！')
                return JsonResponse({'code': 0, 'msg': "检测到shp数据", 'data': point_data})
        pass
    except Exception as e:
        print("添加航线检测区域报错：", e)
        for file_path in file_path_list:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path, ignore_errors=True)
                else:
                    os.remove(file_path)
        logger.error(f"添加航线检测区域报错：{e}")
        return JsonResponse({'code': 500, 'msg': f"{e}"})


def get_onlineuav_info(request):
    """
    获取在线无人机信息
    """
    try:
        logger.info("获取在线无人机信息")
        url = 'http://221.230.150.241:8889/prod-api/auth/ticketLogin'
        data = {
            'ticket': '7ZiCCyDn+XmW2eJJ9sVcuKmBitMJLVNhboJvJJ0YBuU='
        }
        res = requests.post(url=url, json=data).json()
        token = res['token']
        response = requests.get('http://221.230.150.241:8889/prod-api/ctuav/openapi/ctuav/v4/onlineuav/list', headers={
            'Authorization': f'Bearer {token}'})
        data = json.loads(response.text)
        if data['code'] == 200:
            if len(data['data']) != 0:
                return JsonResponse({'code': 0, 'msg': 'success', 'data': data['data']})
            else:
                # d = [{'uavName': 'sss', 'recordId': 6367, 'deptName': '20202', 'deptId': 162}]
                return JsonResponse({'code': 0, 'msg': 'success', 'data': []})
        else:
            # d = [{'uavName': 'sss', 'recordId': 6367, 'deptName': '20202', 'deptId': 162}]
            return JsonResponse({'code': 0, 'msg': 'success', 'data': []})
    except Exception as e:
        logger.error(f"获取在线无人机数据失败{e}")
        return JsonResponse({'code': 500, 'msg': "{}".format(e), 'data': []})


COUNT = 0

COUNT = 0


def get_uav_fly_track(request):
    """
    获取无人机飞行轨迹
    """
    try:
        logger.info(f"获取无人机飞行轨迹")
        global COUNT
        COUNT += 1  # 主要是用来测试无人机飞行轨迹的绘制
        params = json.loads(request.body.decode('utf-8'))
        recordid = int(params.get('recordId'))
        deptid = int(params.get('deptId'))
        url = 'http://221.230.150.241:8889/prod-api/auth/ticketLogin'
        data = {
            'ticket': '7ZiCCyDn+XmW2eJJ9sVcuKmBitMJLVNhboJvJJ0YBuU='
        }
        res = requests.post(url=url, json=data).json()
        token = res['token']
        response = requests.post('http://221.230.150.241:8889/prod-api/ctuav/openapi/ctuav/v4/flydata/list',
                                 json={'recordId': recordid, 'deptId': deptid},
                                 headers={
                                     'Authorization': f'Bearer {token}'})
        data = json.loads(response.text)
        print("飞行轨迹信息", data)
        if data['code'] == 200:
            data_obj = []
            for i in data['data']:
                data_obj.append([i['lng'], i['lat']])
            logger.info("飞行轨迹获取成功")
            return JsonResponse({'code': 0, 'msg': 'success', 'data': data_obj})
        else:
            logger.warning("未获取到飞行轨迹数据")
            return JsonResponse({'code': 500, 'msg': '获取数据失败', 'data': []})
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': "{}".format(e), 'data': []})


def get_uav_info(request):
    """
    获取无人机像元尺寸，焦距等信息
    :return:
    """
    try:
        logger.info("获取无人机像元尺寸，焦距等信息")
        uav_info = [{
            'label': '大疆 Mavic 3 系列，焦距 24mm',
            'value': '24',
        }]
        return JsonResponse({'code': 0, 'msg': "检测到点数据", 'data': uav_info})
    except Exception as e:
        logger.error(f"获取无人机像元尺寸，焦距等信息失败{e}")
        return JsonResponse({'code': '500', 'msg': "{}".format(e), 'data': []})


def panoramic_point_plan(request):
    # 全景点规划
    response_data = {'code': 0, 'msg': '全景点规划成功！', 'data': []}
    with transaction.atomic():
        try:
            logger.info("接受全景规划任务")
            username = request.session.get('username', 'admin')
            params = json.loads(request.body)
            plan_type = str(params.get('planType'))
            plan_name = str(params.get('planName', ''))
            radius = int(params.get('radius'))
            plan_area = params.get('planArea')
            shp_name = params.get('shpName', '')
            plan_area_upload_tag = params.get('planAreaUploadTag')
            plan_obj = Route.objects.filter(name=plan_name).all()
            if plan_obj:
                logger.info(f"{plan_name}名称已存在")
                return JsonResponse({'code': 1, 'msg': '该名称已存在', 'data': {}})
            route_plan_dir_path = os.path.join(settings.BASE_DIR, 'static', 'route_plan', plan_name)
            os.makedirs(route_plan_dir_path, exist_ok=True)
            panoramic_point_obj = []
            if plan_area_upload_tag == '0':  # 说明是手动绘制:
                panoramic_point_obj = generate_panoramic_point(plan_area, radius, route_plan_dir_path)
            elif plan_area_upload_tag == '1':  # 说明是矢量:
                path = os.path.join(settings.BASE_DIR, 'static', 'shp', shp_name.split('.')[0])
                if not os.path.exists(path):
                    logger.info('压缩包未找到')
                    return JsonResponse({'code': 0, 'msg': '文件未找到'})
                shp_list = [os.path.join(path, i) for i in os.listdir(path) if i.endswith('.shp')]
                if len(shp_list) == 0:
                    logger.info('压缩包中未找到shp文件')
                    return JsonResponse({'code': 0, 'msg': '文件未找到'})
                else:
                    uuid_value = str(uuid.uuid4())
                    panoramic_point_obj = generate_panoramic_point(shp_list[0], radius, route_plan_dir_path)
            zip_path = route_plan_dir_path + '.zip'
            zip_folder(route_plan_dir_path, zip_path)
            # 存储文件路径以便后续删除
            while True:
                file_id = f"62{random.randint(10000000000000, 99999999999999)}"
                is_exist = BufferFile.objects.filter(file_id=file_id)
                if not is_exist:
                    break
            BufferFile.objects.create(
                file_id=file_id,
                file_name=plan_name + '.zip',
                file_extension='.zip',
                file_path=zip_path,
                owner=username,
                file_type='zip',
                file_size=os.path.getsize(zip_path),
                desc='全景规划'
            )
            logger.info('zip文件生成成功')
            Route.objects.create(
                route_type=plan_type,
                name=plan_name,
                height=int(radius),
                file_id=file_id,
            )
            response_data['data'] = panoramic_point_obj
            response_data['file_id'] = file_id
            # shutil.rmtree(route_plan_dir_path)
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f"全景规划任务接收失败{e}")
            return JsonResponse({'code': '500', 'msg': "{}".format(e), 'data': []})


def get_zipfile_list(request):
    """
    获取已有航线列表
    """
    try:
        if request.method == 'POST':
            para = json.loads(request.body)
            page = para.get('page', 1)
            limit = para.get('limit', 5)
            result_objs = BufferFile.objects.filter(desc='全景规划').order_by('-create_time')
            paginator = Paginator(result_objs, limit)
            results = paginator.page(page)
            data_list = []
            for i in results:
                data_obj = {
                    'file_name': i.file_name,
                    'file_id': i.file_id,
                }
                data_list.append(data_obj)
            return JsonResponse(
                {'code': 0, 'msg': '查询已有航线成功!!!', 'data': data_list, 'total_count': result_objs.count()})
    except Exception as e:
        logger.error("查询已有航线失败，错误信息为{}".format(e))
        return JsonResponse({'code': 500, 'msg': e, 'data': {}})


def modify_panoramic_point(request):
    """
    修改全景点位置，重新生成全景文件
    :param request:
    :return:
    """
    params = json.loads(request.body)
    file_id = str(params.get('file_id'))
    panoramic_point_list = params.get('panoramic_point_list')
    file_obj = BufferFile.objects.get(file_id=file_id)
    if file_obj:
        file_path = file_obj.file_path
        route_plan_dir_path = os.path.join(settings.BASE_DIR, 'static', 'route_plan', file_path.split('.')[0])
        os.makedirs(route_plan_dir_path, exist_ok=True)
        panoramic_point_to_shp(panoramic_point_list, route_plan_dir_path)
        zip_path = route_plan_dir_path + '.zip'
        if os.path.exists(zip_path):
            os.remove(zip_path)
        zip_folder(route_plan_dir_path, zip_path)
        shutil.rmtree(route_plan_dir_path)
        return JsonResponse({'code': 0, 'msg': '修改全景点位置成功!!!'})
    else:
        return JsonResponse({'code': 500, 'msg': '文件不存在!!!'})


# 查看航线或者全景点
def view_plan(request, file_id):
    """
    查看航线或者全景点
    :param request:
    :param file_id: 文件file_id，用于数据库查询
    :return:
    """
    try:
        result_obj = BufferFile.objects.filter(file_id=file_id).first()
        if result_obj:
            route_obj = Route.objects.filter(file_id=file_id).first()
            file_name = result_obj.file_name
            dir_path = result_obj.file_path.split('.')[0]
            if os.path.exists(dir_path):
                shp_path = os.path.join(dir_path, 'result.shp')
                if os.path.exists(shp_path):
                    gdf = gpd.read_file(shp_path)
                    if "ZXDX" not in gdf.columns or "ZXDY" not in gdf.columns:
                        raise ValueError("Shapefile中不存在ZXDX或ZXDY字段！")
                    # 提取ZDX和ZDY字段值，构造列表
                    coordinates = list(zip(gdf["ZXDY"], gdf["ZXDX"]))
                    return JsonResponse({'code': 0, 'msg': '获取成功', 'data': coordinates})
                else:
                    return JsonResponse({'code': 500, 'msg': 'shp文件不存在!!!'})
            else:
                return JsonResponse({'code': 500, 'msg': '文件夹不存在!!!'})
        return JsonResponse({'code': 0, 'msg': '删除成功'})
    except Exception as e:
        return JsonResponse({'code': 500, 'msg': f'{e}'})
