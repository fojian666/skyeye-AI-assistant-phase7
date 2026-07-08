import numpy as np
from .change_detection.models import create_model
import os,shutil,sys
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK_DIR)
sys.path.append(WORK_DIR+"//image_segmentation//mmsegmentation")
sys.path.append(WORK_DIR+"//change_detection//bit_master")
import torch.nn.functional as F
from functools import partial
from PIL import Image
import apps.interpretation.ai_config as cg
import geopandas as gpd
import pandas as pd
from .change_detection.allflow import change_predict
from .change_detection.allflow_bit import change_predict_bit
from .image_segmentation import predict_dlinknet
from .change_detection.allflow2 import change_detection_dlinknet
from .change_detection.allflow2_mmsegmentation import change_detection_mmseg
from .image_segmentation.predict_dlinknet import get_dinknet
from .image_segmentation.mmsegmentation.mmseg.apis import init_segmentor
# from get_computer_message import get_host_ip
from .utils.common import create_text_file,update_status_bar,create_ori_path
from .image_segmentation import predict_mmsegmentation
from .change_detection.bit_master import utils
from .change_detection.bit_master.models.basic_model import CDEvaluator
# from .mcd_change_detection.models.SSCDl import SSCDl as Net
# from .mcd_change_detection.predict_multi_change_detection import mcdchange_predict
import torch
try:
    import gdal, osr
except:
    from osgeo import gdal, osr

# 静态文件路径设置
nonlinearity = partial(F.relu, inplace=True)
# 设置pillow读取破损图片时跳过去
Image.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
logger = cg.logger
num_classes = cg.num_classes

class WorkerParams(object):
    """
    定义变化检测的参数
    """
    def __init__(self):
        self.prev_path = ''
        self.next_path = ''
        self.output_path = ''
        self.input_path = ''
        self.name = ""
        self.gpu_id = '0'
        self.checkpoints_dir = r"D:\Code\GT_Offline\model\change_detection"
        self.model = 'CDFA'
        self.input_nc = 3
        self.output_nc = 3
        self.arch = 'mynet3'
        self.f_c = 64
        self.n_class = 2
        self.SA_mode = 'PAM'
        self.dataset_mode = 'changedetection'
        self.val_dataset_mode = 'changedetection'
        self.split = 'train',
        self.ds = '1'
        self.angle = 0
        self.istest = False
        self.serial_batches = ''
        self.num_threads = 0
        self.batch_size = 16
        self.load_size = 512
        self.crop_size = 512
        self.max_dataset_size = float("inf")
        self.preprocess = 'none1'
        self.no_flip = True
        self.display_winsize = 256
        self.epoch = "20_F1_1_0.78956"
        self.load_iter = 0
        self.verbose = 'store_true'
        self.phase = 'test'
        self.isTrain = False
        self.num_test = np.inf
        self.pixel = 1
        self.fragment = "1"
        self.region_path = "0"
        self.region_field = "0"
        self.building_regular = 0
        self.way = ''
        self.gpu_ids = [0]

class WorkerParamsBIT(object):
    """
    定义BIT变化检测的参数
    """
    def __init__(self):
        self.project_name = 'qinghai_CD_0829'
        self.gpu_ids = '0'
        self.num_workers = 0
        self.dataset = "CDDataset_predict"
        self.data_name = 'LEVIR_predict'
        self.batch_size = 1
        self.split = 'val'
        self.img_size = 256
        self.n_class = 2
        self.net_G = 'base_transformer_pos_s4_dd8_dedim8'

class BasicModel():
    def __init__(self):
        self.change_model = None
        self.img_seg_model = None
        self.opt = WorkerParams()
        self.change_model_path = ''
        self.img_seg_model_path = ''
        self.mmseg_model = None
        self.mmseg_model_path = ''
        self.bit_change_detection_model = None
        self.bit_change_detection_model_path = ''
        self.bisrnet_model = None
        self.bisrnet_model_path = ''

    def start_model(self,model_path):
        """
        启动变化检测模型
        @param opt: 模型参数
        @param model_path:模型地址
        @return:
        """
        self.change_model_path = model_path
        print(model_path+">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        checkpoint_path = os.path.dirname(os.path.dirname(model_path))  # checkpoints文件夹路径
        epoch_name = os.path.basename(model_path).replace("_net_A.pth", "").replace(
            "_net_F.pth", "")  # 模型epoch名称
        model_name = os.path.basename(os.path.dirname(model_path))  # 模型名称，即存放模型文件的上级目录名
        self.opt.checkpoints_dir = checkpoint_path
        self.opt.epoch = epoch_name
        self.opt.name = model_name
        self.change_model = create_model(self.opt)
        self.change_model.setup(self.opt)
        # 模型验证
        self.change_model.eval()

    def get_dinknet_model(self,model_path):
        """
        启动影像分割dinknet模型
        Args:
            model_path: 模型路径
        Returns:
        """
        self.img_seg_model_path = model_path
        self.img_seg_model = get_dinknet(model_path)

    def start_mmseg_model(self,model_path,config_path):
        """
        启动segformer模型
        Args:
            model_path: 模型路径
            model_name: 模型名称
        """
        self.mmseg_model_path = model_path
        # configpy = cg.MMSEG_CONFIGPY[model_name]
        configpy = config_path
        self.mmseg_model = init_segmentor(configpy, model_path, device='cuda:0')


    def start_bit_model(self,model_path):
        """
        启动BIT模型
        Args:
            model_path: 模型路径
        """

        self.bit_change_detection_model_path = model_path
        opt = WorkerParamsBIT()
        utils.get_device(opt)
        device = torch.device("cuda:%s" % opt.gpu_ids[0]
                              if torch.cuda.is_available() and len(opt.gpu_ids) > 0
                              else "cpu")
        # 模型的加载
        model = CDEvaluator(opt)
        model.load_checkpoint(model_path)
        model.eval()
        self.bit_change_detection_model = model

    def start_bisrnet_model(self, model_path):
        """
        启动BiSRNET模型
        Args:
            model_path: 模型路径
        """
        self.bisrnet_model_path = model_path
        net = Net(3, num_classes).cuda()
        net.load_state_dict(torch.load(model_path))
        net.eval()
        # return net
        self.bisrnet_model = net

    def judge_change_detection_model(self):
        """
        判断当前变化检测模型是否已经启动
        """
        return True if self.change_model else False

    def get_change_detection_model(self):
        """
        得到变化检测模型
        """
        return self.change_model,self.change_model_path

    def judge_image_segmentation_model(self):
        """
        判断影像分割模型是否启动
        """
        return True if self.img_seg_model else False

    def get_image_segmentation_model(self):
        """
        得到影像分割模型
        """
        return self.img_seg_model,self.img_seg_model_path

    def judge_mmseg_model(self):
        """
        判断segformer影像分割模型是否启动
        """
        return True if self.mmseg_model else False

    def get_mmseg_model(self):
        """
        得到segformer影像分割模型
        """
        return self.mmseg_model,self.mmseg_model_path

    def judge_bit_model(self):
        """
        判断bit模型是否启动
        """
        return True if self.bit_change_detection_model else False

    def get_bit_model(self):
        """
        得到bit模型
        """
        return self.bit_change_detection_model,self.bit_change_detection_model_path

    def judge_bisrnet_model(self):
        """
        判断当前bisrnet变化检测模型是否已经启动
        """
        return True if self.bisrnet_model else False

    def get_bisrnet_model(self):
        """
        得到bisrnet变化检测模型
        """
        return self.bisrnet_model, self.bisrnet_model_path

# 获取参数，预起模型
basicmodel = BasicModel()
def change_detection_start_model(model_path):
    """
    启动变化检测模型
    :param model_path:模型路径
    :return:模型
    """
    model_change_detection, change_model_path = basicmodel.get_change_detection_model()
    if not model_change_detection:
        print(">>>>>>>>>>>>>>>>>>>>>>>>变化检测模型没有启动，正在启动模型<<<<<<<<<<<<<<<<<")
        basicmodel.start_model(model_path)
        model_change_detection, change_model_path = basicmodel.get_change_detection_model()
        print(change_model_path)
    else:
        model_change_detection, change_model_path = basicmodel.get_change_detection_model()
        if change_model_path != model_path:
            print(">>>>>>>>>>>>>>>>>>>>>>>>变化检测检测模型不一致，正在重新启动模型<<<<<<<<<<<<<<<<<")
            basicmodel.start_model(model_path)
        print(">>>>>>>>>>>>>>>>>>>>>>>>变化检测模型已经启动<<<<<<<<<<<<<<<<<")
        model_change_detection, change_model_path = basicmodel.get_change_detection_model()
        print(change_model_path)
    return model_change_detection

def image_segmentation_start_model(model_path):
    """
    启动影像分割模型 DLinkNet
    :param model_path:模型路径
    :return:模型
    """
    model_segmentation_predict, img_seg_model_path = basicmodel.get_image_segmentation_model()
    # 获取参数，预起模型
    if not model_segmentation_predict:
        print(">>>>>>>>>>>>>>>>>>>>>>>>影像分割模型没有启动，正在启动模型<<<<<<<<<<<<<<<<<")
        basicmodel.get_dinknet_model(model_path)
        model_segmentation_predict, img_seg_model_path = basicmodel.get_image_segmentation_model()
    else:
        model_segmentation_predict, img_seg_model_path = basicmodel.get_image_segmentation_model()
        if img_seg_model_path != model_path:
            print(">>>>>>>>>>>>>>>>>>>>>>>>影像分割检测模型不一致，正在重新启动模型<<<<<<<<<<<<<<<<<")
            basicmodel.get_dinknet_model(model_path)
        print(">>>>>>>>>>>>>>>>>>>>>>>>影像分割模型已经启动<<<<<<<<<<<<<<<<<")
        model_segmentation_predict, img_seg_model_path = basicmodel.get_image_segmentation_model()
    print(img_seg_model_path)
    return model_segmentation_predict

def mmseg_segmentation_start_model(model_path,config_path):
    """
    启动影像分割模型 MMSEG
    :param model_path:模型路径
    :param config_path:配置文件路径
    :return:模型
    """
    model_mmseg_predict, mmseg_model_path = basicmodel.get_mmseg_model()
    # 获取参数，预起模型
    if not model_mmseg_predict:
        print(">>>>>>>>>>>>>>>>>>>>>>>>MMSEG分割模型没有启动，正在启动模型<<<<<<<<<<<<<<<<<")
        basicmodel.start_mmseg_model(model_path,config_path)
        model_mmseg_predict, mmseg_model_path = basicmodel.get_mmseg_model()
    else:
        model_mmseg_predict, mmseg_model_path = basicmodel.get_mmseg_model()
        if mmseg_model_path != model_path:
            print(">>>>>>>>>>>>>>>>>>>>>>>>MMSEG分割检测模型不一致，正在重新启动模型<<<<<<<<<<<<<<<<<")
            basicmodel.start_mmseg_model(model_path,config_path)
        print(">>>>>>>>>>>>>>>>>>>>>>>>MMSEG分割模型已经启动<<<<<<<<<<<<<<<<<")
        model_mmseg_predict, mmseg_model_path = basicmodel.get_mmseg_model()
    print(mmseg_model_path)
    return model_mmseg_predict

def bit_start_model(model_path):
    """
    启动BIT模型
    :param model_path:模型路径
    :return:模型
    """
    bit_model_predict, bit_model_path = basicmodel.get_bit_model()
    # 获取参数，预起模型
    if not bit_model_predict:
        print(">>>>>>>>>>>>>>>>>>>>>>>>BIT模型没有启动，正在启动模型<<<<<<<<<<<<<<<<<")
        basicmodel.start_bit_model(model_path)
        bit_model_predict, bit_model_path = basicmodel.get_bit_model()
    else:
        bit_model_predict, bit_model_path = basicmodel.get_bit_model()
        if bit_model_path != model_path:
            print(">>>>>>>>>>>>>>>>>>>>>>>>BIT模型不一致，正在重新启动模型<<<<<<<<<<<<<<<<<")
            basicmodel.start_mmseg_model(model_path)
        print(">>>>>>>>>>>>>>>>>>>>>>>>BIT模型已经启动<<<<<<<<<<<<<<<<<")
        bit_model_predict, bit_model_path = basicmodel.get_bit_model()
    print(bit_model_path)
    return bit_model_predict

def bisrnet_start_model(model_path):
    """
    启动BiSRNet模型
    :param model_path:模型路径
    :return:模型
    """
    bisrnet_model_predict, bisrnet_model_path = basicmodel.get_bisrnet_model()
    # 获取参数，预起模型
    if not bisrnet_model_predict:
        print(">>>>>>>>>>>>>>>>>>>>>>>>BiSRNet模型没有启动，正在启动模型<<<<<<<<<<<<<<<<<")
        basicmodel.start_bisrnet_model(model_path)
        bisrnet_model_predict, bisrnet_model_path = basicmodel.get_bisrnet_model()
    else:
        bisrnet_model_predict, bisrnet_model_path = basicmodel.get_bisrnet_model()
        if bisrnet_model_path != model_path:
            print(">>>>>>>>>>>>>>>>>>>>>>>>BiSRNet模型不一致，正在重新启动模型<<<<<<<<<<<<<<<<<")
            basicmodel.start_bisrnet_model(model_path)
        print(">>>>>>>>>>>>>>>>>>>>>>>>BiSRNet模型已经启动<<<<<<<<<<<<<<<<<")
        bisrnet_model_predict, bisrnet_model_path = basicmodel.get_bisrnet_model()
    print(bisrnet_model_path)
    return bisrnet_model_predict


def image_segmentation_predict_main(input_path, output_path, fragment, building_regular,
                                    model_path, status_num_txt_path,model_name,config_path,model_network):
    """
    影像分割处理路由
    @param input_path: 目标检测待检测影像路径
    @param output_path: 输出路径
    @param fragment: 碎斑阈值
    @param building_regular: 是否规则化
    @param model_path: 选择的模型路径
    @param status_num_txt_path: 进度更新文件路径
    @param model_name:模型名称
    @param config_path:配置文件路径
    @param model_network:模型网络
    """
    # 模型路径
    image_name = os.path.splitext(os.path.basename(input_path))[0]
    # 结果状态
    result_status = True
    try:
        print(model_name,model_path)
        temp_out_path = os.path.join(output_path, image_name)
        create_ori_path(temp_out_path)
        if model_network == 'DLinkNet':
            model_segmentation_predict = image_segmentation_start_model(model_path)
            predict_dlinknet.segmentation_predict(input_path, temp_out_path, model_path, image_name, fragment,
                                                  building_regular, model_segmentation_predict,0,90,status_num_txt_path)
        elif model_network == 'Segformer':
            model_segmentation_predict = mmseg_segmentation_start_model(model_path,config_path)
            predict_mmsegmentation.segmentation_predict(input_path, temp_out_path, model_path, image_name, fragment,
                                                        building_regular, model_segmentation_predict,0, 100,status_num_txt_path)
        logger.info("结束:@{}".format(image_name))
        #清除显存
        torch.cuda.empty_cache()
    except Exception as e:
        # 结果状态
        result_status = False
        logger.error("结束:影像分割处理路由报错，报错内容{}@{}".format(e,image_name))
    update_status_bar(100, status_num_txt_path)

    return result_status

def image_seg_er_predict_main(prev_path, next_path, output_path, fragment, building_regular,
                              model_path, status_num_txt_path,
                              folder_name,config_path,model_network):
    """
    基于影像分割擦除的变化检测路由
    @param prev_path: 前景影像路径
    @param next_path: 后景影像路径
    @param output_path: 输出路径
    @param fragment: 碎斑阈值
    @param building_regular:是否规则化
    @param model_path：模型路径
    @param status_num_txt_path：进度更新文件路径
    @param folder_name:文件夹名字，主要是在日志结尾处添加文件夹名字,确定当前处理的区域名称，更新节点信息
    @param config_path:配置文件路径
    @param model_network:模型网络名称
    """
    # status_num_txt_path = ip_connect_log(log_path)
    try:
        prev_name = os.path.splitext(os.path.basename(prev_path))[0]
        next_name = os.path.splitext(os.path.basename(next_path))[0]
        if model_network == 'DLinkNet':
            model_segmentation_predict = image_segmentation_start_model(model_path)
            change_detection_dlinknet(prev_path, next_path, output_path, model_path,prev_name,next_name,
                                      fragment, building_regular,
                                      model_segmentation_predict,0, 90, status_num_txt_path, folder_name)
        elif model_network == 'Segformer':
            model_segmentation_predict = mmseg_segmentation_start_model(model_path, config_path)
            change_detection_mmseg(prev_path, next_path, output_path, model_path, prev_name,
                                   next_name, fragment, building_regular,
                                   model_segmentation_predict,0, 90, status_num_txt_path,folder_name)
        #清除显存
        torch.cuda.empty_cache()
        logger.info("结束:@{}".format(folder_name))
    except Exception as e:
        logger.error("结束:基于影像分割擦除的变化检测路由报错，报错内容{}@{}".format(e,folder_name))
    update_status_bar(100, status_num_txt_path)
    return True

def change_detection_one_step_main(model_path, successful_dir, change_detection_dir_i, bar_interval, fragment,
                                   building_regular, is_add_radio,
                                   probability_threshold, status_num_txt_path, folder_name, model_network):
    """
    变化检测一键通中变化检测部分
    Args:
        model_path: 模型地址
        successful_dir: 数据处理成功文件夹
        change_detection_dir_i: 变化检测结果存储文件夹
        bar_interval: 进度条更新检测
        fragment: 碎斑阈值
        building_regular:是否规则化
        is_add_radio: 是否添加概率
        probability_threshold: 概率阈值
        status_num_txt_path: 进度条更新文件
        folder_name: 文件夹名字，主要是在日志结尾处添加文件夹名字,确定当前处理的区域名称，更新节点信息
        model_network: 模型网络
    Returns:

    """
    print(model_path, successful_dir, change_detection_dir_i, bar_interval, fragment,
                                   building_regular, is_add_radio,
                                   probability_threshold, status_num_txt_path, folder_name, model_network)
    input_list = []
    for index, file_dir_name in enumerate(os.listdir(successful_dir)):
        folder_path = []
        for file in os.listdir(os.path.join(successful_dir, file_dir_name)):
            if file.endswith('.tif'):
                folder_path.append(file)
        data_pred_prev_path = os.path.join(successful_dir, file_dir_name, folder_path[0])
        data_pred_next_path = os.path.join(successful_dir, file_dir_name, folder_path[1])
        solo_change_detection_result_path = os.path.join(change_detection_dir_i, file_dir_name)
        create_ori_path(solo_change_detection_result_path)
        # 计算进度条的各个阶段百分比以及初始数值
        base_progress, sum_progress = (30 + index * bar_interval), bar_interval
        if model_network == 'STANet':
            model_change_detection = change_detection_start_model(model_path)
            change_predict(data_pred_prev_path, data_pred_next_path, solo_change_detection_result_path, fragment,
                           building_regular, model_change_detection, is_add_radio,
                           probability_threshold,base_progress, sum_progress, status_num_txt_path, folder_name)
        elif model_network == 'BIT':
            model_change_detection = bit_start_model(model_path)
            opt = WorkerParamsBIT()
            img_size = opt.img_size
            change_predict_bit(data_pred_prev_path, data_pred_next_path, solo_change_detection_result_path, fragment,
                           building_regular, model_change_detection,base_progress, sum_progress, status_num_txt_path,
                               folder_name,img_size)
        else:
            bisrnet_model = bisrnet_start_model(model_path)
            result_path = mcdchange_predict(data_pred_prev_path, data_pred_next_path, solo_change_detection_result_path, fragment,
                              building_regular,bisrnet_model, base_progress, sum_progress, status_num_txt_path,folder_name)
            # input_list.append(result_path)
            input_list.extend(result_path)
        update_status_bar(30 + (index + 1) * bar_interval, status_num_txt_path)
    if model_network == 'MCD':
        output_path = os.path.join(change_detection_dir_i,'merge_{}.shp'.format(folder_name))
        merge_shp(input_list, output_path)
    logger.info("结束:@{}".format(folder_name))

def merge_shp(input_list,output_path):
    """
    利用gpd实现shp的合并
    Args:
        input_list: 需要合并的数据列表
        output_path: 输出文件路径
    """
    gdf_list = []
    for i_file in input_list:
        gdf_list.append(gpd.read_file(i_file))
    merged_shapefile = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
    merged_shapefile.to_file(output_path)

def image_erasure_one_step_main(prev_path, next_path, output_path,
                                model_path, fragment, building_regular,
                                status_num_txt_path, bar_interval, folder_name, model_name,model_network):
    """
    基于影像分割擦除
    Args:
        prev_path: 前景地址
        next_path: 后景地址
        output_path:结果输出路径
        model_path: 模型路径
        pixel: 分辨率
        fragment: 碎斑阈值
        region_field: 行政区字段
        building_regular: 是否规则化
        is_add_radio:是否添加概率
        probability_threshold:概率阈值
        status_num_txt_path:进度文件路径
        bar_interval:进度间隔
        folder_name:文件夹名字
        model_name:模型名称
    """
    base_progress, sum_progress =0, bar_interval
    if model_network == 'DLinkNet':
        model_segmentation_predict = image_segmentation_start_model(model_path)
        change_detection_dlinknet(prev_path, next_path, output_path, model_path,
                                  os.path.splitext(os.path.basename(prev_path))[0],
                                  os.path.splitext(os.path.basename(next_path))[0],
                                  fragment, building_regular,
                                  model_segmentation_predict,
                                  base_progress, sum_progress, status_num_txt_path, folder_name)
    elif model_network == 'Segformer':
        model_segmentation_predict = mmseg_segmentation_start_model(model_path, model_name)
        change_detection_mmseg(prev_path, next_path, output_path, model_path,
                               os.path.splitext(os.path.basename(prev_path))[0],
                               os.path.splitext(os.path.basename(next_path))[0],
                               fragment, building_regular,
                               model_segmentation_predict,
                               base_progress, sum_progress, status_num_txt_path, folder_name)
