import os
import xml.etree.ElementTree as ET
import time
import xml.dom.minidom as md
import os
import zipfile
import shutil
from shapely.geometry import Point
import geopandas as gpd
def create_waylines_kml(waypoints, flyheight, waylinespath):
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
        "xmlns:wpml": "http://www.dji.com/wpmz/1.0.2"
    })
    doc = ET.SubElement(kml, "Document")

    # 添加missionConfig
    mission_config = ET.SubElement(doc, "wpml:missionConfig")
    ET.SubElement(mission_config, "wpml:flyToWaylineMode").text = "safely"
    ET.SubElement(mission_config, "wpml:finishAction").text = "goHome"
    ET.SubElement(mission_config, "wpml:exitOnRCLost").text = "goContinue"
    ET.SubElement(mission_config, "wpml:takeOffSecurityHeight").text = "100"
    ET.SubElement(mission_config, "wpml:globalTransitionalSpeed").text = "12.0"

    # 添加droneInfo
    drone_info = ET.SubElement(mission_config, "wpml:droneInfo")
    ET.SubElement(drone_info, "wpml:droneEnumValue").text = "6"
    ET.SubElement(drone_info, "wpml:droneSubEnumValue").text = "0"

    # 添加payloadInfo
    payload_info = ET.SubElement(mission_config, "wpml:payloadInfo")
    ET.SubElement(payload_info, "wpml:payloadEnumValue").text = ""
    ET.SubElement(payload_info, "wpml:payloadSubEnumValue").text = "0"
    ET.SubElement(payload_info, "wpml:payloadPositionIndex").text = "0"

    # 创建Folder
    folder = ET.SubElement(doc, "Folder")
    ET.SubElement(folder, "wpml:templateId").text = "0"
    ET.SubElement(folder, "wpml:waylineId").text = "0"
    ET.SubElement(folder, "wpml:autoFlightSpeed").text = "12.0"
    ET.SubElement(folder, "wpml:executeHeightMode").text = "relativeToStartPoint"

    # 添加payloadParam
    payload_param = ET.SubElement(folder, "wpml:payloadParam")
    ET.SubElement(payload_param, "wpml:payloadPositionIndex").text = "0"
    ET.SubElement(payload_param, "wpml:imageFormat").text = "wide"

    # 遍历航飞点，创建Placemark
    for i, (lon, lat) in enumerate(waypoints):
        placemark = ET.SubElement(folder, "Placemark")
        point = ET.SubElement(placemark, "Point")
        coordinates = ET.SubElement(point, "coordinates")
        # coordinates.text = f"{lon},{lat},{flyheight}"
        coordinates.text = f"{lon},{lat}"

        # 添加wpml特定元素
        ET.SubElement(placemark, "wpml:index").text = str(i)
        ET.SubElement(placemark, "wpml:executeHeight").text = str(flyheight)
        ET.SubElement(placemark, "wpml:waypointSpeed").text = "12.0"

        # 添加waypointHeadingParam
        waypoint_heading_param = ET.SubElement(placemark, "wpml:waypointHeadingParam")
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingMode").text = "followWayline"
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingAngle").text = "0"
        ET.SubElement(waypoint_heading_param, "wpml:waypointHeadingPathMode").text = "followBadArc"

        # 添加waypointTurnParam
        waypoint_turn_param = ET.SubElement(placemark, "wpml:waypointTurnParam")
        ET.SubElement(waypoint_turn_param, "wpml:waypointTurnMode").text = "toPointAndStopWithContinuityCurvature"
        ET.SubElement(waypoint_turn_param, "wpml:waypointTurnDampingDist").text = "0"

        # 添加useStraightLine
        ET.SubElement(placemark, "wpml:useStraightLine").text = "0"

        # 添加actionGroup
        action_group = ET.SubElement(placemark, "wpml:actionGroup")
        ET.SubElement(action_group, "wpml:actionGroupId").text = str(i)
        ET.SubElement(action_group, "wpml:actionGroupStartIndex").text = str(i)
        ET.SubElement(action_group, "wpml:actionGroupEndIndex").text = str(i)
        ET.SubElement(action_group, "wpml:actionGroupMode").text = "sequence"

        # 添加actionTrigger
        action_trigger = ET.SubElement(action_group, "wpml:actionTrigger")
        ET.SubElement(action_trigger, "wpml:actionTriggerType").text = "reachPoint"
        ET.SubElement(action_trigger, "wpml:actionTriggerParam").text = "-90"

        # 添加action
        action = ET.SubElement(action_group, "wpml:action")
        ET.SubElement(action, "wpml:actionId").text = "0"
        ET.SubElement(action, "wpml:actionActuatorFunc").text = "takePhoto"
        action_actuator_func_param = ET.SubElement(action, "wpml:actionActuatorFuncParam")
        ET.SubElement(action_actuator_func_param, "wpml:payloadPositionIndex").text = "0"
        ET.SubElement(action_actuator_func_param, "wpml:fileSuffix").text = "yuzhucg"

        # 添加gimbalRotate action
        gimbal_action = ET.SubElement(action_group, "wpml:action")
        ET.SubElement(gimbal_action, "wpml:actionId").text = "1"
        ET.SubElement(gimbal_action, "wpml:actionActuatorFunc").text = "gimbalRotate"
        gimbal_actuator_func_param = ET.SubElement(gimbal_action, "wpml:actionActuatorFuncParam")
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalHeadingYawBase").text = "aircraft"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalRotateMode").text = "absoluteAngle"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalPitchRotateEnable").text = "1"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalPitchRotateAngle").text = "-90"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalRollRotateEnable").text = "0"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalRollRotateAngle").text = "0"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalYawRotateEnable").text = "0"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalYawRotateAngle").text = "0"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalRotateTimeEnable").text = "0"
        ET.SubElement(gimbal_actuator_func_param, "wpml:gimbalRotateTime").text = "0"
        ET.SubElement(gimbal_actuator_func_param, "wpml:payloadPositionIndex").text = "0"

    tree = ET.ElementTree(kml)
    # 格式化XML文档
    xmlstr = ET.tostring(kml, encoding='utf-8')
    dom = md.parseString(xmlstr)
    formatted_xml = dom.toprettyxml(indent='  ')

    # 保存XML文档
    with open(waylinespath, 'w') as f:
        f.write(formatted_xml)


def create_templete_kml(templatepath):
    """
    创建一个templete.kml文件
    :param templatepath: templete.km地址
    :return:
    """
    # 创建根元素
    kml = ET.Element("kml", {
        "xmlns": "http://www.opengis.net/kml/2.2",
        "xmlns:wpml": "http://www.dji.com/wpmz/1.0.2"
    })
    doc = ET.SubElement(kml, "Document")

    # 添加missionConfig
    ET.SubElement(doc, "wpml:author").text = 'author'

    ET.SubElement(doc, "wpml:createTime").text = "".format(time.time())
    ET.SubElement(doc, "wpml:updateTime").text = "".format(time.time())

    # 添加missionConfig
    mission_config = ET.SubElement(doc, "wpml:missionConfig")
    ET.SubElement(mission_config, "wpml:flyToWaylineMode").text = "safely"
    ET.SubElement(mission_config, "wpml:finishAction").text = "goHome"
    ET.SubElement(mission_config, "wpml:exitOnRCLost").text = "goContinue"
    ET.SubElement(mission_config, "wpml:globalTransitionalSpeed").text = "6.0"

    # 添加droneInfo
    drone_info = ET.SubElement(mission_config, "wpml:droneInfo")
    ET.SubElement(drone_info, "wpml:droneEnumValue").text = "68"
    ET.SubElement(drone_info, "wpml:droneSubEnumValue").text = "0"
    tree = ET.ElementTree(kml)
    # 格式化XML文档
    xmlstr = ET.tostring(kml, encoding='utf-8')
    dom = md.parseString(xmlstr)
    formatted_xml = dom.toprettyxml(indent='  ')

    # 保存XML文档
    with open(templatepath, 'w') as f:
        f.write(formatted_xml)

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
    if os.path.exists(new_filepath):
        os.remove(new_filepath)
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

def generate_kmz(out_path, waypoints_list, altitude):
    """
    生成kmz文件
    :param out_path: 输出文件夹路径
    :param waypoints: 航点列表
    :param altitude: 飞行高度
    :return:
    """
    waypoints = []
    for i in waypoints_list:
        waypoints.append([i[1],i[0]])
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    zip_filename = os.path.join(os.path.dirname(out_path), os.path.basename(out_path) + '.zip')
    wpmz_path = os.path.join(out_path, 'wpmz')
    if not os.path.exists(wpmz_path):
        os.mkdir(wpmz_path)
    # 创建KML文件
    waylines_path = os.path.join(wpmz_path, 'waylines.wpml')
    template_path = os.path.join(wpmz_path, 'template.xml')
    create_waylines_kml(waypoints, altitude, waylines_path)  # 创建waylinesKML文件
    create_templete_kml(template_path) # 创建templateKML文件
    zip_wpmz_path = os.path.join(os.path.dirname(wpmz_path), os.path.basename(wpmz_path) + '.zip')
    zip_folder(wpmz_path,zip_wpmz_path)  #压缩wpmz文件夹
    change_file_extension(zip_wpmz_path, 'kmz') # 修改zip文件后缀为kmz
    shutil.rmtree(wpmz_path)
    generate_shp(os.path.join(out_path,'result.shp'),waypoints)
    zip_folder(out_path, zip_filename)  # 创建zip文件
    shutil.rmtree(out_path)
    return zip_filename




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
