from argparse import ArgumentParser
import sys,os
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(WORK_DIR)
import utils
import torch
from models.basic_model import CDEvaluator
import os
import numpy as np

from datasets.data_utils import CDDataAugmentation
from PIL import Image
import warnings

warnings.filterwarnings("ignore")

def predict_bit_main(A_path,B_path,model,size):
    augm = CDDataAugmentation(
        img_size = size
    )
    # 数据的一些操作
    img = np.asarray(Image.open(A_path).convert('RGB'))
    img_B = np.asarray(Image.open(B_path).convert('RGB'))
    [img, img_B], _ = augm.transform([img, img_B], [], to_tensor=True)
    img_new = img.unsqueeze(0)
    img_B_new = img_B.unsqueeze(0)
    batch = {'A': img_new, 'B': img_B_new, 'name': '1'}
    # 模型的加载
    score_map = model._forward_pass(batch)
    pred = model._save_predictions()
    # result = Image.fromarray(np.uint8(pred))
    # result.save(r'E:\geo_ai_server\c#_test_data\result\test\epoch033.tif')
    return pred

if __name__ == '__main__':
    A_path = r'E:\geo_ai_server\c#_test_data\changebatch\1\epoch033_A.tif'
    B_path = r'E:\geo_ai_server\c#_test_data\changebatch\1\epoch033_B.tif'
    checkpoint_path = r'/change_detection/BIT_CD_master\checkpoints\qinghai_CD_0829\last_ckpt.pt'

    predict_bit_main(A_path,B_path,checkpoint_path)








