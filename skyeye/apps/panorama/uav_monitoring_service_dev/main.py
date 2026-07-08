import os.path
import sys
import numpy as np
from pyproj import Transformer

work_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, work_dir)
module_dir = os.path.join(work_dir, 'module')
sys.path.insert(0, module_dir)

from module.device_module import DJCameraDeviceInitializer, get_image_paths
from module.map_module import UAVMap
from module.stitching_module import AutoPanoramaStitcher
from other_utils.Orthophoto_Class import Aerial2Orthophoto
from module.ai_module import KeyPointsDetector, LightGlueMatcher
LOFTR_MODEL_PATH = os.path.join(work_dir, 'checkpoints', 'model.ckpt')  # loftr 模型文件路径


def main(panorama_input_dir, panorama_save_dir, panorama_pkl_path, map_path, patch_info_path):
    """
    TODO： 生成全景图
    """
    # 初始化不同组件模块
    map_uav = UAVMap(map_path, None, patch_info_path, proj_code=32650)  # map
    detector = KeyPointsDetector(LOFTR_MODEL_PATH)  # ai
    matcher = LightGlueMatcher()
    stitcher = AutoPanoramaStitcher(detector="sift", nfeatures=8000)  # stitcher
    files = np.array(
        [os.path.join(panorama_input_dir, file) for file in os.listdir(panorama_input_dir) if '.JPG' in file])
    uav_initializer = DJCameraDeviceInitializer(files, map_uav, detector, matcher, stitcher,
                                                calibration_dir=os.path.join(work_dir, 'data', 'calibration_info'),
                                                patch_dir=os.path.join(work_dir, 'data', 'cultivate_mask'),
                                                stitch_dir=os.path.join(work_dir, 'data', 'stitching', 'info'),
                                                layers_dir=panorama_save_dir,
                                                tif_dir=os.path.join(work_dir, 'data', 'TIF'))
    # 初始化相机信息
    if panorama_pkl_path is not None:
        # 如果config里面存在初始化好的标定信息, 直接加载
        uav_initializer.load_camera_info(panorama_pkl_path)
    else:
        # 初始化当前全景图片信息
        uav_initializer.init_camera()
        # 生成邻接权重图
        uav_initializer.generate_camera_graph()
        # bev视角相机标定
        uav_initializer.calibration()
        # 其他视角相机标定
        uav_initializer.calibration_other_camera_from_graph()
        # 相机信息保存
        uav_initializer.camera_info_save()

    # # # 全景图层生成
    #uav_initializer.origin_panorama_generation()
    # 目标检测图层生成
    alarms,result_alarms = uav_initializer.detection_panorama_generation()
    # 耕地图层生成
    #uav_initializer.cultivate_panorama_generation()
    return result_alarms



def single_img_location(image_file: str, detection_info: list):
    """
    TODO: 单张图像的定位, 坐标系4326
    detection_info = [{'class':, 'position':, 'prob':,}]
    """
    try:
        # 初始化定位器
        Orthophoto = Aerial2Orthophoto()
        Orthophoto.ReadIMGfile(image_file)   # 不同机型读取方式有些许不同
        Orthophoto.distortionRectifying()
        Orthophoto.CacularConer()
        Orthophoto.Orthophoto2()
        res_info = []
        for i in range(len(detection_info)):
            info = detection_info[i]
            points = np.array([info['position'][0]])
            world_points = Orthophoto.location(points)
            transformer = Transformer.from_crs("epsg:{}".format(4549), "epsg:{}".format(4326))    # 平面转经纬度
            lat, lon = transformer.transform(world_points[:, 1], world_points[:, 0])
            info['location'] = [lon[0], lat[0]]
            res_info.append(info)
        return res_info
    except Exception as e:
        print(e)
        for j in range(i, len(detection_info)):
            info = detection_info[j]
            info['location'] = [118.60622, 32.50423]
            res_info.append(info)
        return res_info


if __name__ == '__main__':
    input_panorama_dir = r'./data/panorama/3'  # 全景图文件夹
    save_panorama_dir = r'data/layers'  # 保存三个图层的文件夹
    panorama_pkl_path = r'data/calibration_info/3.pkl'  # 全景图标定文件路径
    map_path = r'G:\R36T2017.tif'  # 正射影像信息
    patch_info_path = r'data/shp/DLTB.shp'  # 图斑信息
    main(input_panorama_dir, save_panorama_dir, panorama_pkl_path, map_path, patch_info_path)
