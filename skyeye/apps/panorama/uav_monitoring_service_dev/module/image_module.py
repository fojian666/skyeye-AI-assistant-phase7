import cv2 as cv
import numpy as np
import os
from itertools import product
import networkx as nx
from tqdm import tqdm
from module.ai_module import KeyPointsDetector


class PTZCaptureImagesInfo:
    """
    摄像头抓拍图片信息类， 包含抓拍图片存放文件夹, PTZ, 抓拍时间, 邻接图片
    """

    def __init__(self):
        self.capture_dir = None
        self.capture_scheme = {}  # {'zoom': capture_matrix}
        self.adjacent_graphs = {}  # {'zoom': graphs}
        self.fov = {}  # {'ptz':[left_bound_point, right_bound_point]}
        self.detector = KeyPointsDetector()

    def generate_img_capture_info(self, pan_step, tilt_step, zoom):
        """
        生成指定焦距下抓拍图片方案和邻接图
        :param  pan_step: p值间隔
        :param  tilt_step: t值间隔
        :param  zoom: zoom设置
        :return:
        """
        # 生成需要抓拍图片的pan, tilt, zoom信息
        capture_pan = np.arange(7.8, 360, pan_step)
        capture_tilt = np.arange(270.4, 360, tilt_step)

        max_row = len(capture_pan)
        max_col = len(capture_tilt)

        capture_ptzs = np.array([("_".join(list(info)) + '_' + str(zoom)).replace('.0', '') for info in
                                product(capture_pan.astype(np.str), capture_tilt.astype(np.str))])

        # 生成邻接信息, 并生成networkx graph类
        capture_matrix = np.zeros((len(capture_pan), len(capture_tilt)))
        capture_matrix_row_idx, capture_matrix_col_idx = np.where(capture_matrix == 0)

        adjacent_up_idx = np.column_stack([capture_matrix_row_idx, capture_matrix_col_idx + 1])  # 上邻接图片索引
        adjacent_up_idx[adjacent_up_idx[:, -1] == max_col] = [-1, -1]  # 修改最后一张图片和第一张图片相邻接

        adjacent_down_idx = np.column_stack([capture_matrix_row_idx, capture_matrix_col_idx - 1])  # 下邻接图片索引
        adjacent_down_idx[adjacent_down_idx[:, -1] == -1] = [-1, -1]  # 修改最后一张图片和第一张图片相邻接

        adjacent_right_idx = np.column_stack([capture_matrix_row_idx + 1, capture_matrix_col_idx])  # 右邻接图片索引
        adjacent_right_idx[adjacent_right_idx[:, 0] == max_row, 0] = 0  # 修改最后一张图片和第一张图片相邻接

        adjacent_left_idx = np.column_stack([capture_matrix_row_idx - 1, capture_matrix_col_idx])  # 左邻接图片索引
        adjacent_left_idx[adjacent_left_idx[:, 0] == -1, 0] = max_row - 1  # 修改最后一张图片和第一张图片相邻接

        #  生成邻接矩阵
        adjacent_matrix = np.zeros((max_row * max_col, max_row * max_col))
        for i in range(max_col * max_row):
            # 计算与当前图片邻接的图片编号
            if i % max_col == 0:
                adjacent_matrix[[i, i, i], [adjacent_right_idx[i][0] * max_col + adjacent_right_idx[i][1],
                                            adjacent_left_idx[i][0] * max_col + adjacent_left_idx[i][1],
                                            adjacent_up_idx[i][0] * max_col + adjacent_up_idx[i][1],
                                            ]] = 1

            elif i % max_col == max_col - 1:
                adjacent_matrix[[i, i, i], [adjacent_right_idx[i][0] * max_col + adjacent_right_idx[i][1],
                                            adjacent_left_idx[i][0] * max_col + adjacent_left_idx[i][1],
                                            adjacent_down_idx[i][0] * max_col + adjacent_down_idx[i][1]
                                            ]] = 1

            else:
                adjacent_matrix[[i, i, i, i], [adjacent_right_idx[i][0] * max_col + adjacent_right_idx[i][1],
                                               adjacent_left_idx[i][0] * max_col + adjacent_left_idx[i][1],
                                               adjacent_up_idx[i][0] * max_col + adjacent_up_idx[i][1],
                                               adjacent_down_idx[i][0] * max_col + adjacent_down_idx[i][1]
                                               ]] = 1

        #  生成图
        G = nx.from_numpy_matrix(adjacent_matrix)
        node_labels = {i: capture_ptzs[i] for i in range(len(capture_ptzs))}
        nx.set_node_attributes(G, node_labels, 'label')
        # nx.draw(G, pos=nx.spring_layout(G), node_size=5)
        # plt.show()

        self.capture_scheme[zoom] = capture_ptzs
        self.adjacent_graphs[zoom] = G

    def graph_connecting(self, base_plane_list):
        """
        根据标定平面信息，将不同焦距下的图连接起来
        :return:
        """
        pass

    def img_loading(self, ptz_list):
        """
        加载抓拍图片
        :return: [image]
        """
        img_info = []
        for ptz in ptz_list:
            img = cv.imdecode(np.fromfile(os.path.join(self.capture_dir, ptz + '.png'),
                                          dtype=np.uint8), cv.IMREAD_COLOR)
            img_info.append(img)

        return img_info

    def img_matching_from_adjacent_matrix(self, zoom):
        """
        TODO: 根据邻接矩阵生成图片间的匹配信息
        :return:
        """

        adjacent_matrix = nx.adjacency_matrix(self.adjacent_graphs[zoom]).todense()
        node_labels = nx.get_node_attributes(self.adjacent_graphs[zoom], 'label')
        for idx, ptz in tqdm(node_labels.items(), desc='Adjacent Image KeyPoints Generating'):
            # 1. 寻找每一个节点及其相邻的其他节点
            adjacent_index = np.where(adjacent_matrix[idx] == 1)[1]
            candidate_ptz_list = [node_labels[idx] for idx in adjacent_index]
            candidate_ptz_list.append(ptz)
            # 2. 加载对应候选图片并进行
            candidate_image = self.img_loading(candidate_ptz_list)
            self.detector.generating_matching_points(candidate_image[-1], candidate_image[:-1],
                                                     ptz, candidate_ptz_list[:-1])


            pass

    def get_keypoints(self, image1, image2):
        pass


if __name__ == '__main__':
    img_infos = PTZCaptureImagesInfo('./')
    img_infos.generate_img_capture_info(10, 5, 1)






