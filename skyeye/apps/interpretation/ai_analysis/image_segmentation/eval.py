# -*- coding: utf-8 -*-
import os
import cv2
import numpy as np
from sklearn.metrics import confusion_matrix


class IOUMetric:
    """
    Class to calculate mean-iou using fast_hist method
    """

    def __init__(self, num_classes):
        self.num_classes = num_classes
        self.hist = np.zeros((num_classes, num_classes))

    def _fast_hist(self, label_pred, label_true):
        mask = (label_true >= 0) & (label_true < self.num_classes)
        hist = np.bincount(
            self.num_classes * label_true[mask].astype(int) +
            label_pred[mask], minlength=self.num_classes ** 2).reshape(self.num_classes, self.num_classes)
        return hist

    def evaluate(self, predictions, gts):
        for lp, lt in zip(predictions, gts):
            assert len(lp.flatten()) == len(lt.flatten())
            self.hist += self._fast_hist(lp.flatten(), lt.flatten())
        # miou
        iou = np.diag(self.hist) / (self.hist.sum(axis=1) + self.hist.sum(axis=0) - np.diag(self.hist))
        miou = np.nanmean(iou)
        # mean acc
        acc = np.diag(self.hist).sum() / self.hist.sum()
        # acc_cls = np.nanmean(np.diag(self.hist) / self.hist.sum(axis=1))
        acc_cls = np.diag(self.hist) / self.hist.sum(axis=1)
        freq = self.hist.sum(axis=1) / self.hist.sum()
        fwavacc = (freq[freq > 0] * iou[freq > 0]).sum()
        return acc, acc_cls, iou, miou, fwavacc


if __name__ == '__main__':
    # label_path = r'G:/BaiduNetdiskDownload/archive/deepglobe-road-dataset/test_label/'
    label_path = r'F:/multi_model_merge/data/single_classfication/build/val/masks/'
    predict_path = 'F:/multi_model_merge/code/DeepGlobe-Road-Extraction-Challenge-master/submits/build/'
    pres = os.listdir(predict_path)
    labels = []
    confusion = np.zeros((2, 2))
    predicts = []
    for im in pres:
        if im[-4:] == '.tif':
            label_name = im.split('.')[0].replace('mask', '') + '.png'
            lab_path = os.path.join(label_path, label_name)
            pre_path = os.path.join(predict_path, im)
            label = cv2.imread(lab_path)
            label = label[:, :, 2]
            pre = cv2.imread(pre_path, 0)
            label[label > 0] = 1
            pre[pre > 0] = 1
            labels.append(label)
            predicts.append(pre)
            confuse = confusion_matrix(label.flatten(), pre.flatten())
            confusion += confuse
    el = IOUMetric(2)
    acc, acc_cls, iou, miou, fwavacc = el.evaluate(predicts, labels)
    # 1)计算矩阵每一行的数据和；
    row_sums = np.sum(confusion, axis=1)
    col_sums = np.sum(confusion, axis=0)
    # 2）计算矩阵每一行的数据所站该行数据总和的比例；
    err_matrix_row = confusion / row_sums
    err_matrix_col = confusion / col_sums
    precision = confusion[1][1] / (confusion[0][1] + confusion[1][1])
    recall = confusion[1][1] / (confusion[1][0] + confusion[1][1])
    accuracy = (confusion[0][0] + confusion[1][1]) / confusion.sum()
    f1_score = 2 * precision * recall / (precision + recall)
    print('precision: ', precision)
    print('class_recall: ', recall)
    print('accuracy: ', accuracy)
    print('f1_score: ', f1_score)
    print('acc: ', acc)
    print('acc_cls: ', acc_cls)
    print('iou: ', iou)
    print('miou: ', miou)
    print('fwavacc: ', fwavacc)
    print('confusion', confusion)
    print('err_matrix_row', err_matrix_row)
    print('err_matrix_col', err_matrix_col)


    # pres = os.listdir(predict_path)
    # init = np.zeros((2, 2))
    # tn_sum, fp_sum, fn_sum, tp_sum = 0, 0, 0, 0
    # l1, l2 = 0, 0
    # l3 = 0
    # for im in pres:
    #     # try:
    #     # label_name = im.split('.')[0].replace('mask', '') + '.png'
    #     lb_path = os.path.join(label_path, im.split('.')[0].replace('mask', '') + '.png')
    #     pre_path = os.path.join(predict_path, im)
    #     lb = cv2.imread(lb_path, 0)
    #     # print(np.max(lb), np.min(lb), 'lb')
    #     pre = cv2.imread(pre_path, 0)
    #     # print(np.max(pre), np.min(pre), 'pre')
    #     lb[lb > 0] = 1
    #     pre[pre > 0] = 1
    #     l1 += len(pre[pre == 1])
    #     l3 += len(lb[lb == 1])
    #     temp = lb
    #     temp[temp == 0] = 100
    #     l2 += len(pre[pre == temp])
    #     temp[temp == 100] = 0
    #     lb = lb.flatten()
    #     pre = pre.flatten()
    #     # print(lb.shape, pre.shape)
    #     confuse = confusion_matrix(lb, pre)
    #     init += confuse
    #     # if len(confuse) == 2:
    #     #     init += confuse
    #     # elif len(confuse) == 1:
    #     #     init[0][0] += confuse[0][0]
    #     # print(confuse)
    #     # tn, fp, fn, tp = confusion_matrix(lb, pre).ravel()
    #     # tn_sum += tn
    #     # fp_sum += fp
    #     # fn_sum += fn
    #     # tp_sum += tp
    #
    #     # except:
    #     #     print('error')
    # # print(tn_sum, fp_sum, fn_sum, tp_sum)
    # # TP = init[1][1]
    # # FN = init[1][0]
    # # FP = init[0][1]
    # # TN = init[0][0]
    # print(l2 / l1)
    # print(l2 / l3)
    # # po = (TP + TN) / (TP + FP + TN + FN)
    # # pe = (501 * (TP + FP) + 501 * (FN + TN)) / (501 * 501)  # 60为单类样本的个数，120为总样本数量
    # # Kappa = (po - pe) / (1 - pe)
    # # 1)计算矩阵每一行的数据和；
    # row_sums = np.sum(init, axis=1)
    # # 2）计算矩阵每一行的数据所站该行数据总和的比例；
    # err_matrix = init / row_sums
    # print(err_matrix)
    #
    # precision = init[1][1] / (init[0][1] + init[1][1])
    # recall = init[1][1] / (init[1][0] + init[1][1])
    # accuracy = (init[0][0] + init[1][1]) / init.sum()
    # f1_score = 2 * precision * recall / (precision + recall)
    # print('precision: ', precision)
    # print('class_recall: ', recall)
    # print('accuracy: ', accuracy)
    # print('f1_score: ', f1_score)
    # # print('oa', po)
