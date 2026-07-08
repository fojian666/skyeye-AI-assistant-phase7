# Copyright (c) OpenMMLab. All rights reserved.
from argparse import ArgumentParser
import os
import numpy as np
import sys,os
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,WORK_DIR)
#sys.path.append(WORK_DIR+"//mmseg")
from PIL import Image
from mmseg.apis import inference_segmentor, init_segmentor, show_result_pyplot
# from mmseg.core.evaluation import get_palette
# import argparse


def predict_result(img,model):
    # args = set_change_predict_param()
    model = model
    img_root =img
    if os.path.isfile(img_root):
        result = inference_segmentor(model, img_root)[0]
        return result
    elif os.path.isdir(img_root):
        for file in os.listdir(img_root):
            if file.endswith('.tif') or file.endswith('.png') or file.endswith('.jpg'):
                file_path = os.path.join(img_root, file)
                result = inference_segmentor(model, file_path)[0]
                return result
    else:
        print('the input path is neither a file nor a file folder, please check the input')



if __name__ == '__main__':
    # main()
    img_path = r'E:\geo_ai_server\c#_test_data\changebatch\1\epoch033_A.tif'
    config_path = r'E:\geo_ai_server\gtrs_cs_server\image_segmentation\mmsegmentation\checkpoints\qh_forest_2m_256\segformer_mit-b5_512x512_160k_ade20k.py'
    checkpoint = r'E:\geo_ai_server\gtrs_cs_server\image_segmentation\iter_175000.pth'
