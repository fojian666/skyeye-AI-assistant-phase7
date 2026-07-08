# Copyright (c) OpenMMLab. All rights reserved.
from argparse import ArgumentParser
import os
import numpy as np
import sys,os
WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
from mmseg.apis import inference_segmentor, init_segmentor, show_result_pyplot
from mmseg.core.evaluation import get_palette
import argparse
import time
def main1111():
    parser = ArgumentParser()
    parser.add_argument('--img',default=r'E:\geo_ai_server\c#_test_data\1', help='Image file')
    parser.add_argument('--config', default=r'E:\geo_ai_server\gtrs_cs_server\image_segmentation\mmsegmentation\checkpoints\qh_forest_2m_256\segformer_mit-b5_512x512_160k_ade20k.py', help='Config file')
    parser.add_argument('--checkpoint', default=r'E:\geo_ai_server\gtrs_cs_server\model\iter_175000.pth', help='Checkpoint file')
    parser.add_argument('--out_file', default=r'E:\00_CW\07_QHMM\pred\1results.tif', help='Path to output file')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--palette',
        default='cityscapes',
        help='Color palette used for segmentation map')
    parser.add_argument(
        '--opacity',
        type=float,
        default=0.5,
        help='Opacity of painted segmentation map. In (0, 1] range.')
    args = parser.parse_args()

    # build the model from a config file and a checkpoint file
    model = init_segmentor(args.config, args.checkpoint, device=args.device)
    # test a single image
    # result = inference_segmentor(model, args.img)

    img_root = args.img
    save_root = args.out_file
    if os.path.isfile(img_root):
        result = inference_segmentor(model, img_root)[0]
        # print(result.pred_sem_seg.data)
        # result = result.cpu()
        # result = np.array(result.pred_sem_seg.data)[0]
        result = Image.fromarray(np.uint8(result))
        result.save(save_root)
    elif os.path.isdir(img_root):
        for file in os.listdir(img_root):
            if file.endswith('.tif') or file.endswith('.png') or file.endswith('.jpg'):
                file_path = os.path.join(img_root, file)
                result_path = os.path.join(save_root, file)
                result = inference_segmentor(model, file_path)[0]
                # print(result.pred_sem_seg.data)
                # result = result.cpu()
                # result = np.array(result.pred_sem_seg.data)[0]
                result = Image.fromarray(np.uint8(result))
                result.save(result_path)
    else:
        print('the input path is neither a file nor a file folder, please check the input')

    # show the results
    # show_result_pyplot(
    #     model,
    #     args.img,
    #     result,
    #     get_palette(args.palette),
    #     opacity=args.opacity,
    #     out_file=args.out_file)

def main():
    # parser = ArgumentParser()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('img', help='Image file')
    parser.add_argument('config', help='Config file')
    parser.add_argument('checkpoint', help='Checkpoint file')
    parser.add_argument('--out-file', default=None, help='Path to output file')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--palette',
        default='cityscapes',
        help='Color palette used for segmentation map')
    parser.add_argument(
        '--opacity',
        type=float,
        default=0.5,
        help='Opacity of painted segmentation map. In (0, 1] range.')
    args = parser.parse_args()
    # build the model from a config file and a checkpoint file
    model = init_segmentor(args.config, args.checkpoint, device=args.device)
    # test a single image
    result = inference_segmentor(model, args.img)
    # show the results
    show_result_pyplot(
        model,
        args.img,
        result,
        get_palette(args.palette),
        opacity=args.opacity,
        out_file=args.out_file)

def set_change_predict_param():
    """
    设置变化检测预测参数
    Returns:
        opt：变化检测预测参数
    """
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--img', default=r'E:\00_CW\07_QHMM\QHMM_mixed_256_2m_voc\VOCdevkit\VOC2012\JPEGImages\00000002.tif', help='Image file')
        parser.add_argument('--config', default=r'D:\Code\mmsegmentation-v0.30.0\checkpoints\qh_forest_2m_256\segformer_mit-b5_512x512_160k_ade20k.py',help='Config file')
        parser.add_argument('--checkpoint', default=r'D:\Code\mmsegmentation_v111\mmsegmentation-main\checkpoints\iter_175000.pth', help='Checkpoint file')
        parser.add_argument('--out-file', default=None, help='Path to output file')
        parser.add_argument(
            '--device', default='cuda:0', help='Device used for inference')
        parser.add_argument(
            '--palette',
            default='cityscapes',
            help='Color palette used for segmentation map')
        parser.add_argument(
            '--opacity',
            type=float,
            default=0.5,
            help='Opacity of painted segmentation map. In (0, 1] range.')
        args = parser.parse_args()
        return args
    except Exception as e:
        print("set_change_predict_param:", e)


def predict_result(img,config,checkpoint):
    args = set_change_predict_param()
    # build the model from a config file and a checkpoint file
    model = init_segmentor(config, checkpoint, device=args.device)
    # test a single image
    # result = inference_segmentor(model, args.img)
    img_root =img
    # save_root = r'E:\geo_ai_server\c#_test_data\result\4'
    save_root = r'E:\\1.tif'
    if os.path.isfile(img_root):
        result = inference_segmentor(model, img_root)[0]
        result = Image.fromarray(np.uint8(result))
        result.save(save_root)
        return result
    elif os.path.isdir(img_root):
        for file in os.listdir(img_root):
            if file.endswith('.tif') or file.endswith('.png') or file.endswith('.jpg'):
                file_path = os.path.join(img_root, file)
                result_path = os.path.join(save_root, file.replace('.jpg','.tif'))
                result = inference_segmentor(model, file_path)[0]
                result = Image.fromarray(np.uint8(result))
                result.save(result_path)
                # return result
    else:
        print('the input path is neither a file nor a file folder, please check the input')


def all_main(img_path, config_path, checkpoint):
    args = set_change_predict_param()
    # 更新关键参数
    args.img = img_path
    args.config = config_path
    args.checkpoint = checkpoint
    result = predict_result(args.img,args.config,args.checkpoint)
    time.sleep(20)
    print(result)


if __name__ == '__main__':
    # main()
    # img_path = r'E:\1.jpg'
    img_path = r'E:\geo_ai_server\c#_test_data\changebatch\1\epoch033_A.tif'
    config_path = r'E:\geo_ai_server\gtrs_cs_server\image_segmentation\mmsegmentation\checkpoints\qh_forest_2m_256\segformer_mit-b5_512x512_160k_ade20k.py'
    checkpoint = r'E:\code\target_identification\ai_detection\road\demo\segformer_mit-b3_1024x1960_15k_HYST_ROAD_pascal_context_zxx_remote_iter_120000.pth'
    all_main(img_path, config_path, checkpoint)