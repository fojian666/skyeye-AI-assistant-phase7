"""This module implements an abstract base class (ABC) 'BaseDataset' for datasets.
它还包括常见的转换函数（例如，get_transform、__scale_width），稍后可以在子类中使用。
"""
import random
import numpy as np
import torch.utils.data as data
from PIL import Image, ImageFilter
import torchvision.transforms as transforms
from abc import ABC, abstractmethod
import math


class BaseDataset(data.Dataset, ABC):
    """
    此类是数据集的抽象基类（ABC）。
    """

    def __init__(self, opt):
        """初始化类；保存类中的选项
        """
        self.opt = opt
        self.root = opt.dataroot

    @staticmethod
    def modify_commandline_options(parser, is_train):
        """添加新的数据集特定选项，并重写现有选项的默认值.
        """
        return parser

    @abstractmethod
    def __len__(self):
        """返回数据集中的图像总数."""
        return 0

    @abstractmethod
    def __getitem__(self, index):
        """返回数据点及其元数据信息.

        参数:
            index - - 用于数据索引的随机整数
        返回:
            一个有他们名字的数据字典。它通常包含数据本身及其元数据信息。
        """
        pass


def get_params(opt, size, test=False):
    w, h = size
    new_h = h
    new_w = w
    angle = 0
    if opt.preprocess == 'resize_and_crop':
        new_h = new_w = opt.load_size
    if 'rotate' in opt.preprocess and test is False:
        angle = random.uniform(0, opt.angle)
        new_w = int(new_w * math.cos(angle * math.pi / 180) \
                    + new_h * math.sin(angle * math.pi / 180))
        new_h = int(new_h * math.cos(angle * math.pi / 180) \
                    + new_w * math.sin(angle * math.pi / 180))
        new_w = min(new_w, new_h)
        new_h = min(new_w, new_h)
    x = random.randint(0, np.maximum(0, new_w - opt.crop_size))
    y = random.randint(0, np.maximum(0, new_h - opt.crop_size))
    flip = random.random() > 0.5  # left-right
    return {'crop_pos': (x, y), 'flip': flip, 'angle': angle}


def get_transform(opt, params=None, grayscale=False, method=Image.BICUBIC,
                  convert=True, normalize=True, test=False):
    transform_list = []
    if grayscale:
        transform_list.append(transforms.Grayscale(1))
    if 'resize' in opt.preprocess:
        osize = [opt.load_size, opt.load_size]
        transform_list.append(transforms.Resize(osize, method))
    #  gaussian blur
    if 'blur' in opt.preprocess:
        transform_list.append(transforms.Lambda(lambda img: __blur(img)))

    if 'rotate' in opt.preprocess and test == False:
        if params is None:
            transform_list.append(transforms.RandomRotation(5))
        else:
            degree = params['angle']
            transform_list.append(transforms.Lambda(lambda img: __rotate(img, degree)))

    if 'crop' in opt.preprocess:
        if params is None:
            transform_list.append(transforms.RandomCrop(opt.crop_size))
        else:
            transform_list.append(transforms.Lambda(lambda img: __crop(img, params['crop_pos'],
                                                                       opt.crop_size)))

    if not opt.no_flip:
        if params is None:
            transform_list.append(transforms.RandomHorizontalFlip())
        elif params['flip']:
            transform_list.append(transforms.Lambda(lambda img: __flip(img, params['flip'])))
    if convert:
        transform_list += [transforms.ToTensor()]
    if normalize:
        transform_list += [transforms.Normalize((0.5, 0.5, 0.5),
                                                (0.5, 0.5, 0.5))]
    return transforms.Compose(transform_list)


def __blur(img):
    if img.mode == 'RGB':
        img = img.filter(ImageFilter.GaussianBlur(radius=random.random()))
    return img


def __rotate(img, degree):
    if img.mode == 'RGB':
        # set img padding == 128
        img2 = img.convert('RGBA')
        rot = img2.rotate(degree, expand=1)
        fff = Image.new('RGBA', rot.size, (128,) * 4)  # 灰色
        out = Image.composite(rot, fff, rot)
        img = out.convert(img.mode)
        return img
    else:
        # set label padding == 0
        img2 = img.convert('RGBA')
        rot = img2.rotate(degree, expand=1)
        # a white image same size as rotated image
        fff = Image.new('RGBA', rot.size, (255,) * 4)
        # create a composite image using the alpha layer of rot as a mask
        out = Image.composite(rot, fff, rot)
        img = out.convert(img.mode)
        return img


def __crop(img, pos, size):
    ow, oh = img.size
    x1, y1 = pos
    tw = th = size
    # only 图像尺寸大于截取尺寸才截取，否则要padding
    if (ow > tw and oh > th):
        return img.crop((x1, y1, x1 + tw, y1 + th))

    size = [size, size]
    if img.mode == 'RGB':
        new_image = Image.new('RGB', size, (128, 128, 128))
        new_image.paste(img, (int((1 + size[1] - img.size[0]) / 2),
                              int((1 + size[0] - img.size[1]) / 2)))

        return new_image
    else:
        new_image = Image.new(img.mode, size, 255)
        # upper left corner
        new_image.paste(img, (int((1 + size[1] - img.size[0]) / 2),
                              int((1 + size[0] - img.size[1]) / 2)))
        return new_image


def __flip(img, flip):
    if flip:
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    return img


def __print_size_warning(ow, oh, w, h):
    """Print warning information about image size(only print once)"""
    if not hasattr(__print_size_warning, 'has_printed'):
        print("The image size needs to be a multiple of 4. "
              "The loaded image size was (%d, %d), so it was adjusted to "
              "(%d, %d). This adjustment will be done to all images "
              "whose sizes are not multiples of 4" % (ow, oh, w, h))
        __print_size_warning.has_printed = True
