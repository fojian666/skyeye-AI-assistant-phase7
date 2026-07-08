import os
import xml.etree.ElementTree as ET
import time
import xml.dom.minidom as md
import os
import zipfile
import shutil
import math
import uuid
from shapely.geometry import Point
import geopandas as gpd


WPML_NAMESPACE = "http://www.dji.com/wpmz/1.0.6"
DEFAULT_AUTO_FLIGHT_SPEED = 15.0
DEFAULT_TAKE_OFF_SECURITY_HEIGHT = 115.0


def _fmt_number(value, precision=2):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    if number.is_integer():
        return str(int(number))
    return f"{number:.{precision}f}".rstrip('0').rstrip('.')


def _bearing_degrees(start, end):
    if not start or not end:
        return 0.0
    lon1, lat1 = map(math.radians, [float(start[0]), float(start[1])])
    lon2, lat2 = map(math.radians, [float(end[0]), float(end[1])])
    delta_lon = lon2 - lon1
    x = math.sin(delta_lon) * math.cos(lat2)
    y = (
        math.cos(lat1) * math.sin(lat2)
        - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    )
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _waypoint_heading(waypoints, index):
    if not waypoints:
        return 0.0
    if index < len(waypoints) - 1:
        return _bearing_degrees(waypoints[index], waypoints[index + 1])
    if index > 0:
        return _bearing_degrees(waypoints[index - 1], waypoints[index])
    return 0.0


def _add_text(parent, tag, text):
    ET.SubElement(parent, tag).text = str(text)


def _add_mission_config(
    doc,
    waypoints,
    speed_mps=DEFAULT_AUTO_FLIGHT_SPEED,
    take_off_security_height=DEFAULT_TAKE_OFF_SECURITY_HEIGHT,
    take_off_point=None,
):
    mission_config = ET.SubElement(doc, "wpml:missionConfig")
    _add_text(mission_config, "wpml:flyToWaylineMode", "safely")
    _add_text(mission_config, "wpml:finishAction", "goHome")
    _add_text(mission_config, "wpml:exitOnRCLost", "goContinue")
    _add_text(mission_config, "wpml:executeRCLostAction", "goBack")
    _add_text(
        mission_config,
        "wpml:takeOffSecurityHeight",
        _fmt_number(take_off_security_height),
    )
    _add_text(
        mission_config,
        "wpml:globalTransitionalSpeed",
        _fmt_number(speed_mps),
    )
    _add_text(
        mission_config,
        "wpml:globalRTHHeight",
        _fmt_number(take_off_security_height),
    )
    reference_point = take_off_point or (waypoints[0] if waypoints else None)
    if reference_point:
        lon, lat = reference_point
        _add_text(
            mission_config,
            "wpml:takeOffRefPoint",
            f"{lat},{lon},0",
        )

    drone_info = ET.SubElement(mission_config, "wpml:droneInfo")
    _add_text(drone_info, "wpml:droneEnumValue", "100")
    _add_text(drone_info, "wpml:droneSubEnumValue", "1")

    payload_info = ET.SubElement(mission_config, "wpml:payloadInfo")
    _add_text(payload_info, "wpml:payloadEnumValue", "99")
    _add_text(payload_info, "wpml:payloadSubEnumValue", "0")
    _add_text(payload_info, "wpml:payloadPositionIndex", "0")


def _add_folder_header(
    folder,
    flyheight,
    speed_mps=DEFAULT_AUTO_FLIGHT_SPEED,
    take_off_security_height=DEFAULT_TAKE_OFF_SECURITY_HEIGHT,
):
    _add_text(folder, "wpml:templateId", "0")
    _add_text(folder, "wpml:templateType", "waypoint")
    _add_text(folder, "wpml:waylineId", "0")
    _add_text(folder, "wpml:autoFlightSpeed", _fmt_number(speed_mps))
    _add_text(folder, "wpml:executeHeightMode", "relativeToStartPoint")

    coord_param = ET.SubElement(folder, "wpml:waylineCoordinateSysParam")
    _add_text(coord_param, "wpml:coordinateMode", "WGS84")
    _add_text(coord_param, "wpml:heightMode", "relativeToStartPoint")
    _add_text(coord_param, "wpml:globalShootHeight", _fmt_number(flyheight))
    _add_text(coord_param, "wpml:surfaceFollowModeEnable", "1")
    _add_text(coord_param, "wpml:surfaceRelativeHeight", _fmt_number(flyheight))
    _add_text(coord_param, "wpml:positioningType", "GPS")

    _add_text(folder, "wpml:globalHeight", _fmt_number(flyheight))


def _add_folder_global_parameters(folder):
    """补齐真实可飞航线包中的全局负载与航点控制参数。"""
    payload_param = ET.SubElement(folder, "wpml:payloadParam")
    _add_text(payload_param, "wpml:payloadPositionIndex", "0")
    _add_text(payload_param, "wpml:focusMode", "firstPoint")
    _add_text(payload_param, "wpml:meteringMode", "average")
    _add_text(payload_param, "wpml:returnMode", "singleReturnFirst")
    _add_text(payload_param, "wpml:samplingRate", "240000")
    _add_text(payload_param, "wpml:scanningMode", "repetitive")
    # 这里沿用已验证可执飞 KMZ 的拼写，与动作参数中的 visable 保持一致。
    _add_text(payload_param, "wpml:imageFormat", "visable")

    _add_text(
        folder,
        "wpml:globalWaypointTurnMode",
        "toPointAndStopWithDiscontinuityCurvature",
    )
    _add_text(folder, "wpml:globalUseStraightLine", "1")
    _add_text(folder, "wpml:gimbalPitchMode", "manual")
    heading_param = ET.SubElement(
        folder,
        "wpml:globalWaypointHeadingParam",
    )
    _add_text(heading_param, "wpml:waypointHeadingMode", "followWayline")


def _add_waypoint_actions(placemark, index, heading):
    action_group = ET.SubElement(placemark, "wpml:actionGroup")
    _add_text(action_group, "wpml:actionGroupId", index)
    _add_text(action_group, "wpml:actionGroupStartIndex", index)
    _add_text(action_group, "wpml:actionGroupEndIndex", index)
    _add_text(action_group, "wpml:actionGroupMode", "sequence")
    action_trigger = ET.SubElement(action_group, "wpml:actionTrigger")
    _add_text(action_trigger, "wpml:actionTriggerType", "reachPoint")

    heading_text = _fmt_number(heading, precision=1)

    yaw_action = ET.SubElement(action_group, "wpml:action")
    _add_text(yaw_action, "wpml:actionActuatorFunc", "rotateYaw")
    yaw_param = ET.SubElement(yaw_action, "wpml:actionActuatorFuncParam")
    _add_text(yaw_param, "wpml:aircraftHeading", heading_text)
    _add_text(yaw_param, "wpml:aircraftPathMode", "clockwise")
    _add_text(yaw_action, "wpml:actionId", "0")

    gimbal_action = ET.SubElement(action_group, "wpml:action")
    _add_text(gimbal_action, "wpml:actionActuatorFunc", "gimbalRotate")
    gimbal_param = ET.SubElement(gimbal_action, "wpml:actionActuatorFuncParam")
    _add_text(gimbal_param, "wpml:payloadPositionIndex", "0")
    _add_text(gimbal_param, "wpml:gimbalHeadingYawBase", "aircraft")
    _add_text(gimbal_param, "wpml:gimbalRotateMode", "absoluteAngle")
    _add_text(gimbal_param, "wpml:gimbalPitchRotateEnable", "1")
    _add_text(gimbal_param, "wpml:gimbalPitchRotateAngle", "-90")
    _add_text(gimbal_param, "wpml:gimbalRollRotateEnable", "0")
    _add_text(gimbal_param, "wpml:gimbalRollRotateAngle", "0")
    _add_text(gimbal_param, "wpml:gimbalYawRotateEnable", "0")
    _add_text(gimbal_param, "wpml:gimbalYawRotateAngle", "0")
    _add_text(gimbal_param, "wpml:gimbalRotateTimeEnable", "0")
    _add_text(gimbal_param, "wpml:gimbalRotateTime", "2")
    _add_text(gimbal_action, "wpml:actionId", "1")

    photo_action = ET.SubElement(action_group, "wpml:action")
    _add_text(photo_action, "wpml:actionActuatorFunc", "orientedShoot")
    photo_param = ET.SubElement(photo_action, "wpml:actionActuatorFuncParam")
    _add_text(photo_param, "wpml:gimbalPitchRotateAngle", "-90")
    _add_text(photo_param, "wpml:gimbalRollRotateAngle", "0")
    _add_text(photo_param, "wpml:gimbalYawRotateAngle", heading_text)
    _add_text(photo_param, "wpml:focusX", "0")
    _add_text(photo_param, "wpml:focusY", "0")
    _add_text(photo_param, "wpml:focusRegionWidth", "0")
    _add_text(photo_param, "wpml:focusRegionHeight", "0")
    _add_text(photo_param, "wpml:focalLength", "24")
    _add_text(photo_param, "wpml:aircraftHeading", heading_text)
    _add_text(photo_param, "wpml:accurateFrameValid", "0")
    _add_text(photo_param, "wpml:payloadPositionIndex", "0")
    _add_text(photo_param, "wpml:payloadLensIndex", "visable")
    _add_text(photo_param, "wpml:useGlobalPayloadLensIndex", "0")
    _add_text(photo_param, "wpml:targetAngle", "0")
    _add_text(photo_param, "wpml:actionUUID", str(uuid.uuid4()))
    _add_text(photo_param, "wpml:imageWidth", "0")
    _add_text(photo_param, "wpml:imageHeight", "0")
    _add_text(photo_param, "wpml:AFPos", "0")
    _add_text(photo_param, "wpml:gimbalPort", "0")
    _add_text(photo_param, "wpml:orientedCameraType", "99")
    _add_text(photo_param, "wpml:orientedFilePath", str(uuid.uuid4()))
    ET.SubElement(photo_param, "wpml:orientedFileMD5")
    _add_text(photo_param, "wpml:orientedFileSize", "0")
    ET.SubElement(photo_param, "wpml:orientedFileSuffix")
    _add_text(photo_param, "wpml:orientedPhotoMode", "normalPhoto")
    _add_text(photo_action, "wpml:actionId", "2")


def _add_panoramic_action(placemark, index):
    """添加与真实可飞全景 KMZ 一致的 360° 全景拍摄动作。"""
    action_group = ET.SubElement(placemark, "wpml:actionGroup")
    _add_text(action_group, "wpml:actionGroupId", index)
    _add_text(action_group, "wpml:actionGroupStartIndex", index)
    _add_text(action_group, "wpml:actionGroupEndIndex", index)
    _add_text(action_group, "wpml:actionGroupMode", "sequence")
    action_trigger = ET.SubElement(action_group, "wpml:actionTrigger")
    _add_text(action_trigger, "wpml:actionTriggerType", "reachPoint")

    pano_action = ET.SubElement(action_group, "wpml:action")
    _add_text(pano_action, "wpml:actionActuatorFunc", "panoShot")
    pano_param = ET.SubElement(pano_action, "wpml:actionActuatorFuncParam")
    _add_text(pano_param, "wpml:payloadPositionIndex", "0")
    _add_text(pano_param, "wpml:payloadLensIndex", "visable,ir")
    _add_text(pano_param, "wpml:useGlobalPayloadLensIndex", "1")
    _add_text(pano_param, "wpml:panoShotSubMode", "panoShot_360")
    _add_text(pano_action, "wpml:actionId", "0")


def create_waylines_kml(
    waypoints,
    flyheight,
    waylinespath,
    photo_waypoint_indexes=None,
    speed_mps=DEFAULT_AUTO_FLIGHT_SPEED,
    take_off_security_height=DEFAULT_TAKE_OFF_SECURITY_HEIGHT,
    take_off_point=None,
    capture_mode='overview',
):
    """
    创建waylines.kml文件
    :param waypoints: 航点列表
    :param flyheight: 飞行高度
    :param waylinespath: waylines.kml文件存储路径
    :return:
    """
    # 创建根元素
    kml = ET.Element("kml", {
        "xmlns": "http://www.opengis.net/kml/2.2",
        "xmlns:wpml": WPML_NAMESPACE
    })
    doc = ET.SubElement(kml, "Document")

    _add_mission_config(
        doc,
        waypoints,
        speed_mps=speed_mps,
        take_off_security_height=take_off_security_height,
        take_off_point=take_off_point,
    )

    # 创建Folder
    folder = ET.SubElement(doc, "Folder")
    _add_folder_header(
        folder,
        flyheight,
        speed_mps=speed_mps,
        take_off_security_height=take_off_security_height,
    )

    photo_waypoint_indexes = (
        set(range(len(waypoints)))
        if photo_waypoint_indexes is None
        else set(photo_waypoint_indexes)
    )

    # 遍历航飞点，创建Placemark
    for i, (lon, lat) in enumerate(waypoints):
        placemark = ET.SubElement(folder, "Placemark")
        point = ET.SubElement(placemark, "Point")
        coordinates = ET.SubElement(point, "coordinates")
        # coordinates.text = f"{lon},{lat},{flyheight}"
        coordinates.text = f"{lon},{lat}"

        # 添加wpml特定元素
        heading = _waypoint_heading(waypoints, i)
        ET.SubElement(placemark, "wpml:isRisky").text = "0"
        ET.SubElement(placemark, "wpml:index").text = str(i)
        ET.SubElement(placemark, "wpml:height").text = _fmt_number(flyheight)
        ET.SubElement(placemark, "wpml:executeHeight").text = _fmt_number(flyheight)
        ET.SubElement(placemark, "wpml:ellipsoidHeight").text = _fmt_number(flyheight)
        ET.SubElement(placemark, "wpml:useGlobalHeight").text = "1"
        ET.SubElement(placemark, "wpml:useGlobalSpeed").text = "1"
        ET.SubElement(placemark, "wpml:waypointSpeed").text = _fmt_number(speed_mps)
        ET.SubElement(placemark, "wpml:useGlobalHeadingParam").text = "1"
        ET.SubElement(placemark, "wpml:useGlobalTurnParam").text = "1"

        # 添加waypointHeadingParam
        waypoint_heading_param = ET.SubElement(placemark, "wpml:waypointHeadingParam")
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingMode").text = "followWayline"
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingAngle").text = "0"
        ET.SubElement(waypoint_heading_param, "wpml:waypointPoiPoint").text = "0.000000,0.000000,0.000000"
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingAngleEnable").text = "0"
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingPathMode").text = "followBadArc"
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingPoiIndex").text = "0"

        # 添加waypointTurnParam
        waypoint_turn_param = ET.SubElement(placemark, "wpml:waypointTurnParam")
        ET.SubElement(waypoint_turn_param, "wpml:waypointTurnMode").text = "toPointAndStopWithDiscontinuityCurvature"
        # 已验证任务中，普通任务点使用 10m 转弯缓冲，航线末点使用 0m。
        damping_distance = (
            0
            if i == len(waypoints) - 1 or (capture_mode == 'panorama' and i == 0)
            else 10
        )
        ET.SubElement(waypoint_turn_param, "wpml:waypointTurnDampingDist").text = _fmt_number(
            damping_distance
        )

        # 添加useStraightLine
        ET.SubElement(placemark, "wpml:useStraightLine").text = "1"

        waypoint_gimbal_heading_param = ET.SubElement(placemark, "wpml:waypointGimbalHeadingParam")
        ET.SubElement(waypoint_gimbal_heading_param, "wpml:waypointGimbalPitchAngle").text = "0"
        ET.SubElement(waypoint_gimbal_heading_param, "wpml:waypointGimbalYawAngle").text = "0"
        ET.SubElement(placemark, "wpml:waypointWorkType").text = "0"

        if i not in photo_waypoint_indexes:
            continue

        # 仅目标网格中心点添加正射拍照动作；起降点不拍照。
        if capture_mode == 'panorama':
            _add_panoramic_action(placemark, i)
        else:
            _add_waypoint_actions(placemark, i, heading)

    _add_folder_global_parameters(folder)

    # 与已验证可导入文件保持一致：紧凑 XML，且根节点前不写 XML 声明。
    # 个别执飞端并非使用通用 XML 解析器，会对声明头和包结构做严格匹配。
    ET.ElementTree(kml).write(
        waylinespath,
        encoding='utf-8',
        xml_declaration=False,
    )


def create_templete_kml(
    templatepath,
    waypoints=None,
    flyheight=120,
    photo_waypoint_indexes=None,
    speed_mps=DEFAULT_AUTO_FLIGHT_SPEED,
    take_off_security_height=DEFAULT_TAKE_OFF_SECURITY_HEIGHT,
    take_off_point=None,
    capture_mode='overview',
):
    """
    创建一个templete.kml文件
    :param templatepath: templete.km地址
    :return:
    """
    # 大疆机场航线包中 template.kml 与 waylines.wpml 均使用完整 WPML
    # 任务结构。这里直接生成同构内容，避免旧版极简 template.xml
    # 在真实设备/平台侧被判为不完整任务。
    create_waylines_kml(
        waypoints or [],
        flyheight,
        templatepath,
        photo_waypoint_indexes=photo_waypoint_indexes,
        speed_mps=speed_mps,
        take_off_security_height=take_off_security_height,
        take_off_point=take_off_point,
        capture_mode=capture_mode,
    )

def zip_folder(folder_path, zip_filename):
    """
    压缩文件
    :param folder_path: 压缩文件夹
    :param zip_filename: 压缩文件地址
    :return:
    """
    # 创建ZIP文件
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 创建文件夹路径
                file_path = os.path.join(root, file)
                # 创建ZIP内的相对路径
                arcname = os.path.relpath(file_path, os.path.join(folder_path, ''))
                # 添加文件到ZIP
                zipf.write(file_path, arcname)


def _write_dji_kmz(kmz_filename, waylines_path, template_path):
    """按已验证可导入的 DJI KMZ 目录、顺序和存储方式写包。"""
    with zipfile.ZipFile(kmz_filename, 'w', compression=zipfile.ZIP_STORED) as zipf:
        # 可用样例中存在显式目录项；部分执飞端的导入器会直接检查它。
        directory_info = zipfile.ZipInfo('wpmz/')
        directory_info.create_system = 0
        directory_info.external_attr = 0x10
        zipf.writestr(directory_info, b'')
        # 文件顺序同可用样例：航线文件在前，模板文件在后，均不压缩。
        zipf.write(
            waylines_path,
            'wpmz/waylines.wpml',
            compress_type=zipfile.ZIP_STORED,
        )
        zipf.write(
            template_path,
            'wpmz/template.kml',
            compress_type=zipfile.ZIP_STORED,
        )


def change_file_extension(src_filename, new_extension):
    """
    更改文件后缀
    :param src_filename: 原始文件名
    :param new_extension: 新后缀
    """
    # 获取文件的目录和原始文件名（不包括后缀）
    directory, filename = os.path.split(src_filename)
    # 分割文件名和原始后缀
    file_root, file_ext = os.path.splitext(filename)

    # 构造新的文件名
    new_filename = f"{file_root}.{new_extension}"
    # 构造完整的新文件路径
    new_filepath = os.path.join(directory, new_filename)
    # 重命名文件
    os.rename(src_filename, new_filepath)
    return new_filepath

def generate_shp(out_path,waypoints):
    points = [Point(coord) for coord  in waypoints]
    # 创建 GeoDataFrame
    point_gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")  # 使用 WGS84 坐标系
    point_gdf['ZXDX'] = point_gdf['geometry'].x
    point_gdf['ZXDY'] = point_gdf['geometry'].y
    # 保存为 SHP 文件
    point_gdf.to_file(out_path)

def generate_kmz(
    out_path,
    waypoints_list,
    altitude,
    photo_waypoint_indexes=None,
    speed_mps=DEFAULT_AUTO_FLIGHT_SPEED,
    take_off_security_height=DEFAULT_TAKE_OFF_SECURITY_HEIGHT,
    take_off_point=None,
    capture_mode='overview',
):
    """
    生成kmz文件
    :param out_path: 输出文件夹路径
    :param waypoints: 航点列表
    :param altitude: 飞行高度
    :return:
    """
    waypoints = [
        [float(point[0]), float(point[1])]
        for point in waypoints_list
    ]
    normalized_take_off_point = None
    if take_off_point is not None:
        normalized_take_off_point = [
            float(take_off_point[0]),
            float(take_off_point[1]),
        ]
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    kmz_filename = os.path.join(os.path.dirname(out_path), os.path.basename(out_path) + '.kmz')
    if os.path.exists(kmz_filename):
        os.remove(kmz_filename)
    wpmz_path = os.path.join(out_path, 'wpmz')
    if not os.path.exists(wpmz_path):
        os.mkdir(wpmz_path)
    # 创建KML文件
    waylines_path = os.path.join(wpmz_path, 'waylines.wpml')
    template_path = os.path.join(wpmz_path, 'template.kml')
    create_waylines_kml(
        waypoints,
        altitude,
        waylines_path,
        photo_waypoint_indexes=photo_waypoint_indexes,
        speed_mps=speed_mps,
        take_off_security_height=take_off_security_height,
        take_off_point=normalized_take_off_point,
        capture_mode=capture_mode,
    )
    # 两份真实可飞任务中的 template.kml 与 waylines.wpml 完全相同。
    # 直接复制可避免分别生成随机 actionUUID 后产生无意义差异。
    shutil.copyfile(waylines_path, template_path)
    _write_dji_kmz(kmz_filename, waylines_path, template_path)
    generate_shp(os.path.join(out_path,'result.shp'),waypoints)
    # shutil.rmtree(out_path)


if __name__ == '__main__':
    # 示例航飞点列表和飞行高度
    # waypoints = [
    #     (118.64513397216798, 32.05406272757821),
    #     (118.60942840576173, 32.002835495405165),
    #     (118.60942840572273, 32.002835494405165),
    #     (118.63342840576173, 32.0033835495405165)
    # ]
    # altitude = 100  # 飞行高度
    # out_path = r'E:\02Gitcode\gtus\static\route_plan\d\1.shp'
    # # generate_kmz(out_path)
    # generate_shp(out_path, waypoints)

    pass
