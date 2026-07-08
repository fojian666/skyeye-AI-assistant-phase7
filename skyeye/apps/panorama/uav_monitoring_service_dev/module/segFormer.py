from mmseg.apis import init_model, inference_model, show_result_pyplot

import os, random

import cv2 as cv
import numpy as np
from typing import Optional, Union
from apps.uav_monitoring_service_dev.module.target_detection import clip, merge

class SegFormer:
    def __init__(self, img=None, sem_seg=None, model=None):
        self.img = img
        self.masks = []
        self.classes = model.dataset_meta['classes']
        self.palette = model.dataset_meta['palette']
        self.sem_seg = sem_seg
        self.model = model
        self.labels = []
    def get_mask(self):
        num_classes = len(self.classes)
        ids = np.unique(self.sem_seg)[::-1]
        legal_indices = ids < num_classes
        ids = ids[legal_indices]
        labels = np.array(ids, dtype=np.int64)
        colors = [self.palette[label] for label in labels]
        mask = np.zeros_like(self.img, dtype=np.uint8)
        for label, color in zip(labels, colors):
            mask[self.sem_seg[0] == label, :] = color
            m = mask.copy()
            self.masks.append(m)
            self.labels.append(label)
            mask[self.sem_seg[0] == label, :] = [0,0,0]

    def draw_contour(self,label:Optional[int]=-1):
        image = self.img.copy()
        mask_contour = np.zeros_like(self.img, dtype=np.uint8)
        # contours = ()
        if label >= 0:
            for l in self.labels:
                if label == l:
                    mask_contour[self.sem_seg[0]==label,:] =[255,255,255]
                    mask_gray = cv.cvtColor(mask_contour, cv.COLOR_RGB2GRAY)
                    ret, binary = cv.threshold(mask_gray, 127, 255, 0)
                    contour, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
                    cv.drawContours(image, contour, -1, (255, 0, 0), 8)
                    for c in contour:
                        cv.fillPoly(image, [c], color=self.palette[label])
                result = cv.addWeighted(image,0.5,self.img,0.5,gamma=0)
        else:
            for l in self.labels:
                label = l
                mask_contour[self.sem_seg[0] == label, :] = [255, 255, 255]
                mask_gray = cv.cvtColor(mask_contour, cv.COLOR_RGB2GRAY)
                ret, binary = cv.threshold(mask_gray, 127, 255, 0)
                contour, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
                # contours = contours + contour
                mask_contour[self.sem_seg[0] == label, :] = [0,0,0]
                cv.drawContours(image, contour, -1, (255, 0, 0), 5)
                for c in contour:
                    cv.fillPoly(image, [c], color=self.palette[label])
            result = cv.addWeighted(image, 0.5, self.img, 0.5, gamma=0)
        return result

    def write_model_result(self, path):
        images = os.listdir(path)
        imgs = [path + img for img in images if '.JPG' in img]
        names = [img.split('/')[-1] for img in imgs]
        h, w = clip(path, 'JPG')
        for name in names:
            try:
                path_clip = path + 'clip/' + name.split('.')[0] + '/'
                images_clip = os.listdir(path_clip)
                imgs_clip = [path_clip + img_clip for img_clip in images_clip if '.JPG' in img_clip]
                for image_clip in imgs_clip:
                    # image_clip = '../data/IMAGE/test/1.JPG'
                    img = cv.imread(image_clip)
                    result = inference_model(self.model, img)
                    sem_seg = result.pred_sem_seg.cpu().data
                    self.img = img
                    self.sem_seg = sem_seg
                    self.get_mask()
                    result = self.draw_contour(label=8)
                    cv.imwrite(image_clip.replace('.JPG', '.png'), result)
                merge(path_clip, (h, w))
            except Exception as e:
                print(name, e)
                continue

def get_mask(pre,img):
    if len(pre) == 0:
        return
    mask_color = np.zeros_like(img,dtype=np.uint8)
    mask_contour = np.zeros_like(img,dtype=np.uint8)
    contours = ()
    image = img.copy()
    for ann in pre:
        m = ann['segmentation']
        point_coords = ann['point_coords']
        color_mask = [random.randint(0,255),random.randint(0,255),random.randint(0,255)]
        mask_color[m] = color_mask
        mask_contour[m] = [255,255,255]
        mask_gray = cv.cvtColor(mask_contour, cv.COLOR_RGB2GRAY)
        ret, binary = cv.threshold(mask_gray, 127, 255, 0)
        contour, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        contours = contours + contour
        mask_contour[m] = [0,0,0]
    dst = (img*0.4 + mask_color*0.6).astype(np.uint8)
    result = cv.drawContours(dst, contours, -1, (255, 0, 0), 5)
    return result


if __name__ == '__main__':
    config_path = '../configs/segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py'
    checkpoint_path = '../data/model/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth'
    model = init_model(config_path, checkpoint_path, device='cpu')
    paths = ['../data/IMAGE/025_0002/origin/']
    segformer = SegFormer(model=model)
    for path in paths:
        try:
            segformer.write_model_result(path)
        except Exception as e:
            print(path,e)
            continue


    # sam = sam_model_registry["vit_h"](checkpoint='../data/model/sam_vit_h_4b8939.pth')
    # mask_generator = SamAutomaticMaskGenerator(sam)
    # img = cv.imread('../data/IMAGE/test/PANO0015_006.JPG')
    # pre = mask_generator.generate(img)
    # image = get_mask(pre,img)
    # cv.imwrite('../data/IMAGE/test/5.png',image)
