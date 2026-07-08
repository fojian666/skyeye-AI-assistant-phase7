import os
import time
import argparse
import numpy as np
import torch.autograd
from skimage import io
from torch.nn import functional as F
from torch.utils.data import DataLoader
from datasets import RS_ST as RS
from models.SSCDl import SSCDl as Net
DATA_NAME = 'ST'
#################################

class PredOptions():
    def __init__(self):
        """Reset the class; indicates the class hasn't been initailized"""
        self.initialized = False
        
    def initialize(self, parser):
        working_path = os.path.dirname(os.path.abspath(__file__))
        parser.add_argument('--pred_batch_size', required=False, default=1, help='prediction batch size')
        parser.add_argument('--test_dir', required=False, default=r'E:\geo_ai_server\c#_test_data\test_mcd', help='directory to test images')
        parser.add_argument('--pred_dir', required=False, default=r'E:\geo_ai_server\c#_test_data\test_mcd', help='directory to output masks')
        # parser.add_argument('--chkpt_path', required=False, default=working_path+'/checkpoints/ST/Fscdnan_OA88.91.pth')
        # parser.add_argument('--chkpt_path', required=False, default=working_path+'/checkpoints/ST/SSCDl_SCLoss_195e_mIoU_Sek_Fscdnan_OA88.pth')
        parser.add_argument('--chkpt_path', required=False, default=working_path+'/checkpoints/ST/Fscd_OA88_52.pth')
        self.initialized = True
        return parser
        
    def gather_options(self):
        if not self.initialized:  # check if it has been initialized
            parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser = self.initialize(parser)
        self.parser = parser
        return parser.parse_args()

    def parse(self):
        self.opt = self.gather_options()
        return self.opt
        
def compare_models(model_1, model_2):
    models_differ = 0
    for key_item_1, key_item_2 in zip(model_1.state_dict().items(), model_2.state_dict().items()):
        if torch.equal(key_item_1[1], key_item_2[1]):
            pass
        else:
            models_differ += 1
            if (key_item_1[0] == key_item_2[0]):
                print('Mismtach found at', key_item_1[0])
            else:
                raise Exception
    if models_differ == 0:
        print('Models match perfectly! :)')        


def start_model(chkpt_path):

    net = Net(3, RS.num_classes).cuda()
    net.load_state_dict(torch.load(chkpt_path) )
    net.eval()
    return net

def main(path_a,path_b):
    begin_time = time.time()
    chk = r'E:\geo_ai_server\gtrs_cs_server\mcd_change_detection\checkpoints\ST\Fscd_OA88_52.pth'
    net = start_model(chk)
    opt = PredOptions().parse()
    out = opt.pred_dir
    # test_set = RS.Data_test(opt.test_dir)
    test_set = RS.Data_test1(path_a,path_b)
    test_loader = DataLoader(test_set, batch_size=1)
    predict(net, test_set, test_loader, out,flip=False, index_map=False, intermediate=False)
    time_use = time.time() - begin_time
    print('Total time: %.2fs'%time_use)

#For models with 3 outputs: 1 change map + 2 semantic maps.
#Parameters: flip->test time augmentation     index_map->"False" means rgb results      intermediate->whether to outputs the intermediate maps
def predict(net, pred_set, pred_loader, pred_dir, flip=False, index_map=False, intermediate=False):
    pred_A_dir_rgb = os.path.join(pred_dir, 'im1_rgb')
    pred_B_dir_rgb = os.path.join(pred_dir, 'im2_rgb')
    if not os.path.exists(pred_A_dir_rgb): os.makedirs(pred_A_dir_rgb)
    if not os.path.exists(pred_B_dir_rgb): os.makedirs(pred_B_dir_rgb)
    # if index_map:
    #     pred_A_dir = os.path.join(pred_dir, 'im1')
    #     pred_B_dir = os.path.join(pred_dir, 'im2')
    #     if not os.path.exists(pred_A_dir): os.makedirs(pred_A_dir)
    #     if not os.path.exists(pred_B_dir): os.makedirs(pred_B_dir)
    # if intermediate:
    #     pred_mA_dir = os.path.join(pred_dir, 'im1_semantic')
    #     pred_mB_dir = os.path.join(pred_dir, 'im2_semantic')
    #     pred_change_dir = os.path.join(pred_dir, 'change')
    #     if not os.path.exists(pred_mA_dir): os.makedirs(pred_mA_dir)
    #     if not os.path.exists(pred_mB_dir): os.makedirs(pred_mB_dir)
    #     if not os.path.exists(pred_change_dir): os.makedirs(pred_change_dir)
    
    for vi, data in enumerate(pred_loader):
        imgs_A, imgs_B = data
        #imgs = torch.cat([imgs_A, imgs_B], 1)
        imgs_A = imgs_A.cuda().float()
        imgs_B = imgs_B.cuda().float()
        mask_name = pred_set.get_mask_name(vi)
        with torch.no_grad(): 
            out_change, outputs_A, outputs_B = net(imgs_A, imgs_B)#,aux
            out_change = F.sigmoid(out_change)
        outputs_A = outputs_A.cpu().detach()
        outputs_B = outputs_B.cpu().detach()
        change_mask = out_change.cpu().detach()>0.5
        change_mask = change_mask.squeeze()
        pred_A = torch.argmax(outputs_A, dim=1).squeeze()
        pred_B = torch.argmax(outputs_B, dim=1).squeeze()
        pred_A = (pred_A*change_mask.long()).numpy()
        pred_B = (pred_B*change_mask.long()).numpy()
        pred_A_path = os.path.join(pred_A_dir_rgb, mask_name)
        pred_B_path = os.path.join(pred_B_dir_rgb, mask_name)
        io.imsave(pred_A_path, RS.Index2Color(pred_A))
        io.imsave(pred_B_path, RS.Index2Color(pred_B))
        print(pred_A_path)
        # if index_map:
        #     pred_A_path = os.path.join(pred_A_dir, mask_name)
        #     pred_B_path = os.path.join(pred_B_dir, mask_name)
        #     io.imsave(pred_A_path, pred_A.astype(np.uint8))
        #     io.imsave(pred_B_path, pred_B.astype(np.uint8))


#For models that directly produce 2 SCD maps.
#Parameters: flip->test time augmentation     index_map->"False" means rgb results
def predict_direct(net, pred_set, pred_loader, pred_dir, flip=False, index_map=False,):
    pred_A_dir_rgb = os.path.join(pred_dir, 'im1_rgb')
    pred_B_dir_rgb = os.path.join(pred_dir, 'im2_rgb')
    if not os.path.exists(pred_A_dir_rgb): os.makedirs(pred_A_dir_rgb)
    if not os.path.exists(pred_B_dir_rgb): os.makedirs(pred_B_dir_rgb)
    if index_map:
        pred_A_dir = os.path.join(pred_dir, 'im1')
        pred_B_dir = os.path.join(pred_dir, 'im2')
        if not os.path.exists(pred_A_dir): os.makedirs(pred_A_dir)
        if not os.path.exists(pred_B_dir): os.makedirs(pred_B_dir)
    
    for vi, data in enumerate(pred_loader):
        imgs_A, imgs_B = data
        #imgs = torch.cat([imgs_A, imgs_B], 1)
        imgs_A = imgs_A.cuda().float()
        imgs_B = imgs_B.cuda().float()
        mask_name = pred_set.get_mask_name(vi)
        with torch.no_grad(): 
            outputs_A, outputs_B = net(imgs_A, imgs_B)#,aux
        if flip:
            outputs_A = F.softmax(outputs_A, dim=1)
            outputs_B = F.softmax(outputs_B, dim=1)
            
            imgs_A_v = torch.flip(imgs_A, [2])
            imgs_B_v = torch.flip(imgs_B, [2])
            outputs_A_v, outputs_B_v = net(imgs_A_v, imgs_B_v)
            outputs_A_v = torch.flip(outputs_A_v, [2])
            outputs_B_v = torch.flip(outputs_B_v, [2])
            outputs_A += F.softmax(outputs_A_v, dim=1)
            outputs_B += F.softmax(outputs_B_v, dim=1)
            
            imgs_A_h = torch.flip(imgs_A, [3])
            imgs_B_h = torch.flip(imgs_B, [3])
            outputs_A_h, outputs_B_h = net(imgs_A_h, imgs_B_h)
            outputs_A_h = torch.flip(outputs_A_h, [3])
            outputs_B_h = torch.flip(outputs_B_h, [3])
            outputs_A += F.softmax(outputs_A_h, dim=1)
            outputs_B += F.softmax(outputs_B_h, dim=1)
            
            imgs_A_hv = torch.flip(imgs_A, [2,3])
            imgs_B_hv = torch.flip(imgs_B, [2,3])
            outputs_A_hv, outputs_B_hv = net(imgs_A_hv, imgs_B_hv)
            outputs_A_hv = torch.flip(outputs_A_hv, [2,3])
            outputs_B_hv = torch.flip(outputs_B_hv, [2,3])
            outputs_A += F.softmax(outputs_A_hv, dim=1)
            outputs_B += F.softmax(outputs_B_hv, dim=1)
            
        outputs_A = outputs_A.cpu().detach()
        outputs_B = outputs_B.cpu().detach()
        pred_A = torch.argmax(outputs_A, dim=1)
        pred_B = torch.argmax(outputs_B, dim=1)
        pred_A = pred_A.squeeze().numpy().astype(np.uint8)
        pred_B = pred_B.squeeze().numpy().astype(np.uint8)
        
        pred_A_path = os.path.join(pred_A_dir_rgb, mask_name)
        pred_B_path = os.path.join(pred_B_dir_rgb, mask_name)
        io.imsave(pred_A_path, RS.Index2Color(pred_A))
        io.imsave(pred_B_path, RS.Index2Color(pred_B))
        print(pred_A_path)
        if index_map:
            pred_A_path = os.path.join(pred_A_dir, mask_name)
            pred_B_path = os.path.join(pred_B_dir, mask_name)
            io.imsave(pred_A_path, pred_A.astype(np.uint8))
            io.imsave(pred_B_path, pred_B.astype(np.uint8))
        '''
        change_path = os.path.join(pred_dir, 'change', mask_name)
        io.imsave(change_path, (change_mask*255).astype(np.uint8))'''


if __name__ == '__main__':
    # main()
    # output_path = r'E:\geo_ai_server\c#_test_data\test_mcd'
    # img_pre = r'E:\geo_ai_server\c#_test_data\test_mcd\im1\c2020_Clip_7168_8192_13312_14336.tif'
    # img_next = r'E:\geo_ai_server\c#_test_data\test_mcd\im2\c2020_Clip_7168_8192_13312_14336.tif'
    # mask_name = r'c2020_Clip_7168_8192_13312_14336.tif'
    # predict1(output_path, img_pre, img_next, mask_name)
    path_a = r'E:\geo_ai_server\c#_test_data\test_mcd\im1'
    path_b = r'E:\geo_ai_server\c#_test_data\test_mcd\im2'
    main(path_a, path_b)