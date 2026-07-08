"""按飞机起降点服务半径筛选可完整覆盖的地块。"""

import math

from geopy.distance import geodesic
from shapely.geometry import shape

AIRCRAFT_PARCEL_RANGE_KM = 6.0
BOUNDARY_SAMPLE_INTERVAL_KM = 0.1


def _coord_lon_lat(coord):
    """兼容二维/三维坐标，统一取前两维作为经度、纬度。"""
    return float(coord[0]), float(coord[1])


def _interpolate_ring_coords(coords, interval_km=BOUNDARY_SAMPLE_INTERVAL_KM):
    """沿边界加密采样，避免仅一个近端顶点命中就错误保留整个大地块。"""
    result = []
    coord_list = list(coords)
    for start, end in zip(coord_list, coord_list[1:]):
        start_lon, start_lat = _coord_lon_lat(start)
        end_lon, end_lat = _coord_lon_lat(end)
        segment_km = geodesic(
            (start_lat, start_lon),
            (end_lat, end_lon),
        ).kilometers
        steps = max(1, math.ceil(segment_km / interval_km))
        for step in range(steps):
            ratio = step / steps
            result.append((
                start_lon + (end_lon - start_lon) * ratio,
                start_lat + (end_lat - start_lat) * ratio,
            ))
    if coord_list:
        result.append(_coord_lon_lat(coord_list[-1]))
    return result


def _geometry_sample_points(geometry):
    geom = shape(geometry)
    if geom.is_empty:
        return []
    coords = []
    if geom.geom_type == 'Polygon':
        coords.extend(_interpolate_ring_coords(geom.exterior.coords))
        for interior in geom.interiors:
            coords.extend(_interpolate_ring_coords(interior.coords))
    elif geom.geom_type == 'MultiPolygon':
        for polygon in geom.geoms:
            coords.extend(_interpolate_ring_coords(polygon.exterior.coords))
            for interior in polygon.interiors:
                coords.extend(_interpolate_ring_coords(interior.coords))
    else:
        coords.extend(geom.coords)
    return coords


def parcel_max_distance_km_to_aircraft(geometry, aircraft):
    """返回一个地块全部边界采样点到指定机巢的最大距离。"""
    sample_points = _geometry_sample_points(geometry)
    if not sample_points:
        return float('inf')
    aircraft_location = (
        float(aircraft['latitude']),
        float(aircraft['longitude']),
    )
    return max(
        geodesic(
            (float(latitude), float(longitude)),
            aircraft_location,
        ).kilometers
        for longitude, latitude in map(_coord_lon_lat, sample_points)
    )


def eligible_aircraft_for_geometry(
    geometry,
    aircraft_list,
    radius_km=AIRCRAFT_PARCEL_RANGE_KM,
):
    """返回能够独立完整覆盖该地块的机巢及其最大边界距离。"""
    return [
        (aircraft, max_distance_km)
        for aircraft in aircraft_list
        for max_distance_km in [
            parcel_max_distance_km_to_aircraft(geometry, aircraft)
        ]
        if max_distance_km <= radius_km
    ]


def filter_features_by_aircraft_range(
    features,
    aircraft_list,
    radius_km=AIRCRAFT_PARCEL_RANGE_KM,
    progress_callback=None,
):
    if not aircraft_list:
        raise ValueError('请先上传机巢点位')
    if not features:
        raise ValueError('没有可筛选的地块')

    kept = []
    excluded = []
    total = len(features)
    for index, feature in enumerate(features, start=1):
        eligible_aircraft = eligible_aircraft_for_geometry(
            feature['geometry'],
            aircraft_list,
            radius_km=radius_km,
        )
        if eligible_aircraft:
            kept.append(feature)
        else:
            excluded.append(feature)
        if progress_callback:
            progress_callback(index, total)
    return kept, excluded


def build_filtered_geojson_from_features(
    features,
    aircraft_list,
    radius_km=AIRCRAFT_PARCEL_RANGE_KM,
    crs=None,
):
    kept, excluded = filter_features_by_aircraft_range(features, aircraft_list, radius_km)
    if not kept:
        raise ValueError(
            f'{radius_km:g} km 范围内没有有效地块，共 {len(features)} 个地块均被剔除'
        )

    filtered_geojson = {
        'type': 'FeatureCollection',
        'features': kept,
    }
    if crs:
        filtered_geojson['crs'] = crs

    return {
        'geojson': filtered_geojson,
        'summary': {
            'totalParcelCount': len(features),
            'parcelCount': len(kept),
            'excludedParcelCount': len(excluded),
            'aircraftCount': len(aircraft_list),
            'rangeKm': radius_km,
        },
    }
