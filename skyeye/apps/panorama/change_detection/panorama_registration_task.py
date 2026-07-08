# @Time : 2025/1/16 15:51
# @Description : 📷
import os
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import torch
import torch.nn.functional as F
from PIL import Image, ImageEnhance
import random
from lightglue.utils import load_image, rbd
from transformers import AutoImageProcessor, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

random.seed(2025)
PROJECT_DIR = os.path.abspath(os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)), os.pardir))
# os.environ['PREFECT_API_URL'] = 'http://192.168.60.81:8739/api'


def list_frames_sorted(directory, file_extension=".png", sorted_idx=-1, filter=False):
    """
    列出指定目录中按顺序排列的所有帧文件。

    :param directory: 帧文件所在目录
    :param file_extension: 帧文件的扩展名（默认为".png"）
    :return: 按顺序排列的帧文件列表
    """
    # 列出目录中的所有文件
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(file_extension)]

    # 使用sorted()对文件进行排序，确保按数字顺序排列
    if filter:
        # 筛选并排序，确保按行号排序
        # 筛选并排序，按行号和列号排序
        sorted_files = sorted(
            [
                file for file in files
                if int(os.path.basename(file).split('_')[0]) >= 8  # 筛选行号 >= 6
            ],
            key=lambda x: (
                int(os.path.basename(x).split('_')[0]),  # 按行号排序
                int(os.path.basename(x).split('_')[1].split('.')[0])  # 按列号排序
            )
        )
    else:
        sorted_files = sorted(files, key=lambda x: int(x.split('_')[sorted_idx].split('.')[0]))

    return sorted_files


class PanoramaImageCropper:
    """
    全景图像切割器
    """
    def __init__(self,
                 panorama_img_path: str,
                 crop_start_row_idx: int = 2500):
        self.panorama_img_path = panorama_img_path
        self.crop_start_row_idx = crop_start_row_idx   # start row idx for panorama image cropping

    # @task
    def crop_image_no_padding(self, output_dir, crop_size=(512, 512), exploit='jpg', verbose=False):
        """
        按照指定大小裁切图像并保存，舍弃不足裁切大小的部分。

        Args:
            image_path (str): 输入图像路径。
            output_dir (str): 裁切后图像保存目录。
            crop_size (tuple): 裁切图像大小，默认(512, 512)。
            exploit
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 读取图像
        image = cv2.imread(self.panorama_img_path)
        if image is None:
            raise ValueError("图像无法加载，请检查路径！")

        img_height, img_width, _ = image.shape
        crop_height, crop_width = crop_size

        # 计算裁切顶点
        start_points = [
            (row, col)
            for row in range(0, img_height - crop_height + 1, crop_height)
            for col in range(0, img_width - crop_width + 1, crop_width)
        ]

        # 单循环裁切
        # 可视化裁剪区域
        vis_image = image.copy()
        for row, col in start_points:
            # 裁切图像
            crop_img = image[row:row + crop_height, col:col + crop_width]
            if verbose:
                cv2.rectangle(vis_image, (col, row), (col + crop_width, row + crop_height), (0, 0, 255), 8)

            # 保存裁切后的图像，命名方式为 row_col.jpg
            output_filename = f"{row // crop_height}_{col // crop_width}.{exploit}"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, crop_img)

        # 显示图像
        if verbose:
            plt.figure(figsize=(12, 8))
            plt.imshow(cv2.cvtColor(vis_image, cv2.COLOR_BGR2RGB))
            plt.title("Crop Region Visualization")
            plt.axis('off')
            plt.show()

        print(f"图像裁切完成，结果保存在：{output_dir}")
        return True


class PanoramaImageMatcher:
    """
       两期全景影像配对
       """

    def __init__(self,
                 base_image_dir: str,
                 registration_image_dir: str,
                 processor: AutoImageProcessor,
                 model: AutoModel,
                 file_extension: str = '.jpeg',
                 sorted_idx: int = -1,
                 ):
        self.base_image_dir = base_image_dir
        self.registration_image_dir = registration_image_dir
        self.processor = processor
        self.model = model

    def get_image_embedding(self, model, processor, images):
        """获取图像的嵌入向量"""
        with torch.no_grad():
            # 将图像转换为张量并进行预处理
            inputs = processor(images=images, return_tensors="pt").to(model.device)
            outputs = model(**inputs)
            # print(outputs.feature_maps)
            embedding = F.normalize(outputs.last_hidden_state[:, 1:].max(dim=1)[0], dim=-1, p=2)  # 获取嵌入
            return embedding

    def augment_image(self, image):
        """
        图像增强
        :param image:
        :return:
        """
        # 随机调整亮度
        enhancer = ImageEnhance.Brightness(image)
        brightness_factor = random.uniform(0.8, 1.2)  # 控制亮度的范围
        image = enhancer.enhance(brightness_factor)

        # 随机调整对比度
        enhancer = ImageEnhance.Contrast(image)
        contrast_factor = random.uniform(0.8, 1.2)  # 控制对比度的范围
        image = enhancer.enhance(contrast_factor)

        # 随机调整色彩
        enhancer = ImageEnhance.Color(image)
        color_factor = random.uniform(0.8, 1.2)  # 控制色彩的范围
        image = enhancer.enhance(color_factor)

        return image

    def preprocess_embeddings(self, image_files, model, processor, aug=False, batch_size=32, size=(512, 512)):
        """
        计算并将所有图像嵌入保存到单个文件中。
        :param image_files: DINOv2模型
        :param model: DINOv2模型
        :param processor: DINOv2模型
        :param aug: DINOv2模型
        :param batch_size: DINOv2模型
        :param size: DINOv2模型
        """

        all_embeddings = []  # 存储所有嵌入

        # 分批次处理
        for i in tqdm(range(0, len(image_files), batch_size), total=len(image_files) // batch_size):
            # 取出当前 batch 的图像文件
            batch_files = image_files[i:i + batch_size]
            batch_images = []

            for image_file in batch_files:
                try:
                    # 加载图像
                    image = Image.open(image_file)
                    resized_img = image.resize(size, resample=Image.LANCZOS)
                    if aug:
                        resized_img = self.augment_image(resized_img)  # 假设 `augment_image` 已定义

                    batch_images.append(np.array(resized_img))  # 转换成 NumPy 数组并加入 batch
                except Exception as e:
                    print(f"无法读取图像: {image_file}, 错误: {e}")
                    continue

            # 计算嵌入
            embeddings = self.get_image_embedding(model, processor, batch_images)
            all_embeddings.append(embeddings.detach().cpu())  # 将嵌入转为numpy并存储

        return torch.cat(all_embeddings, dim=0)

    # @task
    def pipeline_matching_top_k(self, top_k=3, similarity_threshold=0.9, verbose=False):
        """
        基于相似度矩阵，找到每张 base 图像对应的相似度大于阈值的 top-k registration 图像。
        :param top_k: 每张 base 图像要匹配的 registration 图像数量
        :param similarity_threshold: 相似度阈值
        :return: 匹配的 base 索引和 registration 索引对的列表
        """
        # logger = get_run_logger()
        # 1. load images
        base_frame_paths = list_frames_sorted(self.base_image_dir, '.jpg')  # 替换为实际的base帧路径
        target_frame_paths = list_frames_sorted(self.registration_image_dir, '.jpg')  # 替换为实际的待配准帧路径]
        # 2.获取image embedding并保存(多线程)
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交多线程任务
            # logger.info('原始图像嵌入计算')
            future_base = executor.submit(self.preprocess_embeddings, base_frame_paths, self.model, self.processor)
            future_target = executor.submit(self.preprocess_embeddings, target_frame_paths, self.model, self.processor)
            # 获取结果
            base_embeddings_no_aug = future_base.result()
            target_embeddings_no_aug = future_target.result()
        # 图像增强， 提高配对准确率，减少配对图片，提高速度
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交多线程任务
            # logger.info('增强图像嵌入计算')
            future_base = executor.submit(self.preprocess_embeddings, base_frame_paths, self.model, self.processor, True)
            future_target = executor.submit(self.preprocess_embeddings, target_frame_paths, self.model, self.processor, True)
            # 获取结果
            base_embeddings_aug = future_base.result()
            target_embeddings_aug = future_target.result()

        base_embeddings = (base_embeddings_no_aug + base_embeddings_aug) / 2
        target_embeddings = (target_embeddings_no_aug + target_embeddings_aug) / 2
        # 计算相似矩阵
        similarity_matrix = cosine_similarity(base_embeddings, target_embeddings)

        N_base, N_reg = similarity_matrix.shape
        matches = []

        for base_idx in range(N_base):
            # 获取当前 base 图像与所有 registration 图像的相似度
            similarities = similarity_matrix[base_idx]

            # 过滤掉低于阈值的相似度
            valid_indices = np.where(similarities >= similarity_threshold)[0]
            valid_similarities = similarities[valid_indices]

            # 使用 argsort 获取从小到大的索引，然后取倒数前 top_k 个
            if len(valid_similarities) > 0:
                top_k_indices = valid_indices[np.argsort(valid_similarities)[-top_k:][::-1]].tolist()  # 降序排列
            else:
                top_k_indices = None

            # 记录匹配的索引对
            matches.append((base_idx, top_k_indices))

            # print(
            #     f"base {base_idx} 匹配的相似度大于 {similarity_threshold} 的 top-{top_k} registration 索引: {top_k_indices}")

        # 可视化前 6 对匹配（只展示第一个 top_k 的配对）
        if verbose:
            # 参数：最多显示 6 组、每组显示前 top_k 张配对图
            num_groups_to_show = 6
            k_per_group = top_k

            # 收集图像对用于展示
            vis_images = []  # 每行为一组 [base_img, reg_img1, reg_img2, ..., reg_img_k]
            count = 0

            for base_idx, top_k_indices in matches:
                if top_k_indices is None or len(top_k_indices) == 0:
                    continue

                base_img = cv2.imread(base_frame_paths[base_idx])
                if base_img is None:
                    continue

                base_img = cv2.resize(base_img, (256, 256))
                row_imgs = [base_img]

                for reg_idx in top_k_indices[:k_per_group]:
                    reg_img = cv2.imread(target_frame_paths[reg_idx])
                    if reg_img is None:
                        continue
                    reg_img = cv2.resize(reg_img, (256, 256))
                    row_imgs.append(reg_img)

                if len(row_imgs) == k_per_group + 1:
                    vis_images.append(row_imgs)
                    count += 1

                if count >= num_groups_to_show:
                    break

            # 绘图
            fig, axs = plt.subplots(num_groups_to_show, k_per_group + 1,
                                    figsize=(4 * (k_per_group + 1), 4 * num_groups_to_show))

            for i, row_imgs in enumerate(vis_images):
                for j, img in enumerate(row_imgs):
                    ax = axs[i][j] if num_groups_to_show > 1 else axs[j]
                    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    if j == 0:
                        ax.set_title(f"Base {i}", fontsize=12)
                    else:
                        ax.set_title(f"Reg {j}", fontsize=12)
                    ax.axis('off')

            plt.tight_layout()
            plt.show()

        return matches


class PanoramaImageRegistrator:
    """
    全景图像配准器
    """

    def __init__(self,
                 kp_extractor,
                 kp_matcher):
        self.kp_extractor = kp_extractor
        self.kp_matcher = kp_matcher

    # Function to process each match block
    def process_match_block(self, block_matches, base_img_files, target_img_files, logger=None, crop_size=(512, 512)):
        local_key_points_pair = {'pre': [], 'last': []}
        for base_idx, target_idx_list in block_matches:
            if target_idx_list is None:
                continue
            inliers_number = []
            res_match_info = []
            for target_idx in target_idx_list:
                # base_points, target_points = self.get_keypoint_position_KF(base_img_files[base_idx],
                #                                                         target_img_files[target_idx])
                base_points, target_points = self.get_keypoint_position_lg(base_img_files[base_idx],
                                                                        target_img_files[target_idx])

                if len(base_points) < 4 or len(target_points) < 4:
                    # logger.info(f"匹配点不足，跳过索引对 {base_idx}, {target_idx}")
                    continue

                H, inliers = cv2.findHomography(np.array(target_points), np.array(base_points), cv2.USAC_MAGSAC, 4,
                                                0.999, 100000)

                if np.sum(inliers) < 15:
                    # logger.info(f"未能计算单应性矩阵，跳过索引对 {base_idx}, {target_idx}")
                    continue
                inliers_number.append(np.sum(inliers))

                origin_filename = base_img_files[base_idx].replace('\\', '/').split('/')[-1]
                # print(origin_filename)
                pre_row, pre_col = map(int, origin_filename.split('.')[0].split('_'))

                last_filename = target_img_files[target_idx].replace('\\', '/').split('/')[-1]
                last_row, last_col = map(int, last_filename.split('.')[0].split('_'))

                pre_points = list(np.array(base_points).reshape(-1, 2)[inliers.flatten() == 1] + np.array(
                    [pre_col * crop_size[0], pre_row * crop_size[1]]))
                last_points = list(np.array(target_points).reshape(-1, 2)[inliers.flatten() == 1] + np.array(
                    [last_col * crop_size[0], last_row * crop_size[1]]))
                res_match_info.append([pre_points, last_points])

            if len(inliers_number) > 0:
                local_key_points_pair['pre'].extend(res_match_info[np.argmax(inliers_number)][0])
                local_key_points_pair['last'].extend(res_match_info[np.argmax(inliers_number)][1])

        return local_key_points_pair

    # @task
    def generate_all_keypoints(self, base_img_dir, target_img_dir, matches, crop_size=(1024, 1024), num_workers=6):
        # logger = get_run_logger()

        base_img_files = list_frames_sorted(base_img_dir, '.jpg')  # 替换为实际的base帧路径
        target_img_files = list_frames_sorted(target_img_dir, '.jpg')  # 替换为实际的待配准帧路径]

        key_points_pair = {'pre': [],
                           'last': []}
        # Divide matches into chunks for parallel processing
        chunk_size = len(matches) // num_workers
        match_chunks = [matches[i:i + chunk_size] for i in range(0, len(matches), chunk_size)]

        # # Use ThreadPoolExecutor to process chunks in parallel
        # with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        #     futures = [executor.submit(self.process_match_block, chunk, base_img_files, target_img_files, None, crop_size) for chunk in match_chunks]
        #     for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
        #         result = future.result()
        #         key_points_pair['pre'].extend(result['pre'])
        #         key_points_pair['last'].extend(result['last'])
        for chunk in tqdm(match_chunks):
            result = self.process_match_block(chunk, base_img_files, target_img_files, None, crop_size)
            key_points_pair['pre'].extend(result['pre'])
            key_points_pair['last'].extend(result['last'])

        return key_points_pair

    def get_keypoint_position_KF(self, fname1, fname2):
        """
        根据给定的图像文件获取它们的关键点位置，使用特征点匹配器。

        :param matcher: 特征点匹配器（如 LoFTR）
        :param fname1: 基准图像文件名
        :param fname2: 目标图像文件名
        :return: 匹配的基准图像和目标图像的关键点 [(x, y), ...]
        """
        image0 = load_image(fname1).cuda()
        image1 = load_image(fname2).cuda()
        # extract local features
        feats0 = self.kp_extractor.extract(image0)  # auto-resize the image, disable with resize=None
        feats1 = self.kp_extractor.extract(image1)

        # match the features
        matches01 = self.kp_matcher({'image0': feats0, 'image1': feats1})
        feats0, feats1, matches01 = [rbd(x) for x in [feats0, feats1, matches01]]  # remove batch dimension
        matches = matches01['matches']  # indices with shape (K,2)
        mkpts0 = feats0['keypoints'][matches[..., 0]]  # coordinates in image #0, shape (K,2)
        mkpts1 = feats1['keypoints'][matches[..., 1]]  # coordinates in image #1, shape (K,2)

        # # 使用 LoFTR 获取关键点
        # with torch.inference_mode():
        #     inp = torch.cat([img1, img2], dim=0)
        #     features1, features2 = self.kp_extractor(inp, num_features, pad_if_not_divisible=True)
        #     kps1, descs1 = features1.keypoints, features1.descriptors
        #     kps2, descs2 = features2.keypoints, features2.descriptors
        #     lafs1 = KF.laf_from_center_scale_ori(kps1[None], torch.ones(1, len(kps1), 1, 1, device='cuda:0'))
        #     lafs2 = KF.laf_from_center_scale_ori(kps2[None], torch.ones(1, len(kps2), 1, 1, device='cuda:0'))
        #     dists, idxs = self.kp_matcher(descs1, descs2, lafs1, lafs2, hw1=hw1, hw2=hw2)
        #
        # mkpts0, mkpts1 = self.get_matching_keypoints(kps1, kps2, idxs)

        return mkpts0.cpu().numpy(), mkpts1.cpu().numpy()

    def get_keypoint_position_lg(self, fname1, fname2):
        """
               根据给定的图像文件获取它们的关键点位置，使用特征点匹配器。

               :param matcher: 特征点匹配器（如 LoFTR）
               :param fname1: 基准图像文件名
               :param fname2: 目标图像文件名
               :return: 匹配的基准图像和目标图像的关键点 [(x, y), ...]
               """
        # img1 = K.io.load_image(fname1, K.io.ImageLoadType.RGB32)[None, ...].to('cuda:0')
        # img2 = K.io.load_image(fname2, K.io.ImageLoadType.RGB32)[None, ...].to('cuda:0')

        # load each image as a torch.Tensor on GPU with shape (3,H,W), normalized in [0,1]
        image0 = load_image(fname1).cuda()
        image1 = load_image(fname2).cuda()
        # print(image0.shape)
        # print(image1.shape)

        # # print(img1.shape)
        # num_features = 2048

        # extract local features
        feats0 = self.kp_extractor.extract(image0)  # auto-resize the image, disable with resize=None
        feats1 = self.kp_extractor.extract(image1)
        # print(f"desc0.shape: {feats0['descriptors'].shape}")
        # match the features
        matches01 = self.kp_matcher({'image0': feats0, 'image1': feats1})
        feats0, feats1, matches01 = [rbd(x) for x in [feats0, feats1, matches01]]  # remove batch dimension
        matches = matches01['matches']  # indices with shape (K,2)
        mkpts0 = feats0['keypoints'][matches[..., 0]]  # coordinates in image #0, shape (K,2)
        mkpts1 = feats1['keypoints'][matches[..., 1]]  # coordinates in image #1, shape (K,2)

        return mkpts0.cpu().numpy(), mkpts1.cpu().numpy()

    def get_matching_keypoints(self, kp1, kp2, idxs):
        mkpts1 = kp1[idxs[:, 0]]
        mkpts2 = kp2[idxs[:, 1]]
        return mkpts1, mkpts2

