# -*- coding: utf-8 -*-
import os,sys,shutil
WORK_DIR =os.path.dirname(os.path.abspath(__file__))
sys.path.append(WORK_DIR)
sys.path.append(os.path.dirname(WORK_DIR))
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2,40).__str__()
from PIL import Image
from PIL import ImageFile
from cloud_coverage import Cloud_Coverage
from resapling import Resampling
from clip_img import is_tif_all_black,clip_image
import apps.interpretation.ai_config as cg

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None
work_dir = cg.PROJECT_PATH
max_single_img_size = cg.max_single_img_size
clip_size = cg.clip_size
logger = cg.logger
img_name_tag = ''

class DataProcessMain():

    def dir_create(self,input_path):
        """
        创建文件
        Args:
            input_path: 创建文件路径

        Returns:

        """
        if not os.path.exists(input_path):
            os.makedirs(input_path)

    def cloud_coverage_proces(self, pre_img_path, next_img_path,mask_threshold):
        """
        Args:
            pre_img_path: 前景影像地址
            next_img_path: 后景影像地址
            mask_threshold：云雪掩膜阈值
        Returns: 前景掩膜数组、后景掩膜数组，空间参考、投影

        """
        #获取云雪覆盖量
        global img_name_tag
        pre_cloud_covrage, pre_mask, im_width, im_height, im_bands, im_geotrans, im_proj = Cloud_Coverage().get_cloud_coverage(pre_img_path,mask_threshold)
        next_cloud_covrage, next_mask, im_width, im_height, im_bands, im_geotrans, im_proj = Cloud_Coverage().get_cloud_coverage(next_img_path,mask_threshold)
        if abs(pre_cloud_covrage - next_cloud_covrage) <= 20:
            logger.info("数据处理:successful,前时影像{}云覆盖量为{}%@{}".format(os.path.splitext(os.path.basename(pre_img_path))[0], round(pre_cloud_covrage, 3),img_name_tag))
            logger.info("数据处理:successful,后时影像{}云覆盖量为{}%@{}".format(os.path.splitext(os.path.basename(next_img_path))[0], round(next_cloud_covrage, 3),img_name_tag))
        else:
            logger.warning("数据处理:warning,前时后时影像云覆盖量差异过大!@{}".format(os.path.splitext(os.path.basename(pre_img_path))[0], os.path.splitext(os.path.basename(next_img_path))[0],img_name_tag))

        return pre_mask, next_mask, im_geotrans, im_proj


    def all_flow(self,folder_name,pre_img_file_path,next_img_file_path,successful_dir,failed_dir,mask_threshold,
                 mask_tif_dir,is_uniform_color,base_progress,sum_progress,status_num_txt_path):
        """
        数据处理总流程
        Args:
            folder_name: 文件夹名字
            pre_img_file_path: 前景文件路径
            next_img_file_path: 后景文件路径
            successful_dir: 成功处理文件存储路径
            failed_dir: 失败存储路径
            mask_threshold: 云雪掩膜阈值
            mask_tif_dir: mask_tif存储路径
            is_uniform_color: 是否匀光匀色
            base_progress: 进度条开始数值
            sum_progress: 进度条结束数值
            status_num_txt_path: 进度写入信息文件
        Returns:

        """
        # 重采样操作
        global img_name_tag
        logger.info("数据处理:开始重采样操作@{}".format(img_name_tag))
        num, pre_img_path, next_img_path = Resampling().start_resampling(pre_img_file_path, next_img_file_path,
                                                                         successful_dir, failed_dir, folder_name)
        # if num == 0:
        #     pass
        # else:
        #     #获取云雪掩膜
        #     pre_mask, next_mask, im_geotrans, im_proj = self.cloud_coverage_proces(pre_img_path, next_img_path,mask_threshold)
        #     update_status_bar(base_progress + sum_progress * 0.5, status_num_txt_path)
        #     all_mask = pre_mask * next_mask
        #     im_height, im_width = all_mask.shape
        #     masktif_path = os.path.join(mask_tif_dir, '{}.tif'.format(folder_name))
        #     read_write_tif.writetiff(all_mask, im_width, im_height, 1, im_geotrans, im_proj, masktif_path)
        #     update_status_bar(base_progress + sum_progress * 0.6, status_num_txt_path)
        #     # 如果确认需要做匀光匀色
        #     if is_uniform_color == '1':
        #         color_detection = Color_Detection()
        #         img_color_flag = color_detection.run_color_contrast(pre_img_path, next_img_path)
        #         image_match = Image_Match()
        #         if not img_color_flag:
        #             logger.info("数据处理:Successful，色彩不一致，进行匹配{}@{}".format(os.path.splitext(os.path.basename(pre_img_file_path))[0],img_name_tag))
        #             # 进行色彩匹配
        #             ref_img_path = next_img_path
        #             out_img_path = os.path.join(os.path.dirname(next_img_path),
        #                                         os.path.basename(pre_img_path).split('.')[0] + '.tif')
        #             image_match.run_histogram_match(pre_img_path, ref_img_path, out_img_path)
        #         logger.info('数据处理:Successful,匀光匀色结束@{}'.format(img_name_tag))
        #     else:
        #         logger.info("数据处理:色彩一致,不进行色彩匹配@{}".format(img_name_tag))
        #     update_status_bar(base_progress + sum_progress * 0.9, status_num_txt_path)

    def start_data_preprocess(self,folder_name,pre_img_file_path,next_img_file_path,successful_dir,failed_dir,
                              mask_tif_dir,mask_threshold,is_uniform_color,base_progress,sum_progress,status_num_txt_path):
        """
        开始数据处理入口函数
        Args:
            folder_name: 文件夹名字
            pre_img_file_path: 前景文件路径
            next_img_file_path: 后景文件路径
            successful_dir: 成功处理文件存储路径
            failed_dir: 失败存储路径
            mask_threshold: 云雪掩膜阈值
            mask_tif_dir: mask_tif存储路径
            is_uniform_color: 是否匀光匀色
            base_progress: 进度条开始数值
            sum_progress: 进度条结束数值
            status_num_txt_path: 进度写入信息文件

        Returns:

        """
        global img_name_tag
        img_name_tag = folder_name
        base_name_path = os.path.dirname(successful_dir)
        img_dataset, band_count, img_cols, img_rows = Resampling().open_img(pre_img_file_path)
        logger.info("数据处理:判断影像大小@{}".format(img_name_tag))
        #判断影像大小，确定是否裁剪
        if img_cols>max_single_img_size or img_rows>max_single_img_size:
            logger.info("数据处理:影像大,执行裁剪@{}".format(img_name_tag))
            clip_img_dir = os.path.join(base_name_path, 'clip_img')
            self.dir_create(clip_img_dir)
            clip_image(pre_img_file_path, next_img_file_path, clip_img_dir, clip_size)
            # update_status_bar(base_progress+sum_progress*0.3,status_num_txt_path)
            file_list_path = os.listdir(clip_img_dir)
            for clip_folder_i in file_list_path:
                folder_path = []
                for file in os.listdir(os.path.join(clip_img_dir,clip_folder_i)):
                    if file.endswith('.tif'):
                        tif_path = os.path.join(clip_img_dir,clip_folder_i, file)
                        #判断影像是否全黑，若全黑，剔除，不参与变化检测
                        if not is_tif_all_black(tif_path):
                            folder_path.append(tif_path)
                if len(folder_path)==2:
                    self.all_flow(clip_folder_i, folder_path[0], folder_path[1], successful_dir,
                                 failed_dir, mask_threshold, mask_tif_dir, is_uniform_color,
                                  base_progress,sum_progress,status_num_txt_path)
            shutil.rmtree(clip_img_dir)
        else:
            self.all_flow(folder_name, pre_img_file_path, next_img_file_path, successful_dir,
                          failed_dir, mask_threshold, mask_tif_dir, is_uniform_color,
                          base_progress,sum_progress,status_num_txt_path)
        if len(os.listdir(failed_dir)) == 0:
            shutil.rmtree(failed_dir)
        logger.info("数据处理:@{}".format(img_name_tag))

def update_status_bar(num,status_num_txt_path):
    """
    更新进度条进度百分比,写入log
    Args:
        num: 进度百分比

    Returns:

    """
    global STATUS_BAR_PROGRESS
    STATUS_BAR_PROGRESS = num
    with open(status_num_txt_path, 'w+') as f:
        f.write(str(int(STATUS_BAR_PROGRESS)))


if __name__ == '__main__':
    folder_name = 'ledu'
    pre_img_file_path = r'E:\geo_ai_server\c#_test_data\ledu\ledu\LD_2021_clip.tif'
    next_img_file_path = r'E:\geo_ai_server\c#_test_data\ledu\ledu\LD_2022_clip.tif'
    successful_dir = r'E:\geo_ai_server\c#_test_data\result\乐都数据处理\ledu\successful'
    failed_dir = r'E:\geo_ai_server\c#_test_data\result\乐都数据处理\ledu\failed'
    mask_tif_dir = r'E:\geo_ai_server\c#_test_data\result\乐都数据处理\ledu\mask_tif'
    mask_threshold = '0.5'
    is_uniform_color = '1'
    base_progress = 0
    sum_progress = 100
    status_num_txt_path = r'E:\geo_ai_server\gtrs_cs_server\logs\status_num\192-168-60-20_status.txt'
    DataProcessMain().start_data_preprocess(folder_name, pre_img_file_path, next_img_file_path, successful_dir, failed_dir,
                          mask_tif_dir, mask_threshold, is_uniform_color, base_progress, sum_progress,status_num_txt_path)