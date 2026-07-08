import cv2,math
from osgeo import gdal
import os
import numpy as np
# kernel_size必须是正奇数
blur_method = 'mean_blur'  #均值滤波
# blur_method = 'median_blur'  #中值滤波
# blur_method = 'gaussian_blur'  #高斯滤波
# blur_method = 'low_pass_filter'  #低通滤波
# blur_method = 'high_pass_filter'  #高通滤波
# blur_method = 'band_pass_filter'  #带通滤波
def read_tiff(file_path):
    """
   读取图像
   :param file_path: 输入图像路径
   :return im_data: 要写入的图像数据
   :return im_width: 图像宽
   :return im_height: 图像高
   :return im_geotrans: 坐标信息
   :return im_proj: 投影信息
   """
    dataset = gdal.Open(file_path)
    if dataset == None:
        print(file_path + "文件无法打开")
        return
    im_width = dataset.RasterXSize  # 栅格矩阵的列数
    im_height = dataset.RasterYSize  # 栅格矩阵的行数
    im_bands = dataset.RasterCount  # 波段数
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    # im_band = im_data[0:im_height, 0:im_width]
    # im_blueBand = im_data[0, 0:im_height, 0:im_width]  # 获取蓝波段
    # im_greenBand = im_data[1, 0:im_height, 0:im_width]  # 获取绿波段
    # im_redBand = im_data[2, 0:im_height, 0:im_width]  # 获取红波段
    # im_nirBand = im_data[3, 0:im_height, 0:im_width]  # 获取近红外波段
    return im_data, im_width, im_height, im_bands, im_geotrans, im_proj

def write_tiff_img(im_data, im_width, im_height, im_bands, im_geotrans, im_proj, path):
    """
   写入图像
   :param im_data: 要写入的图像数据
   :param im_width: 图像宽
   :param im_height: 图像高
   :param im_bands: 要写入的图像波段数
   :param im_geotrans: 坐标信息
   :param im_proj: 投影信息
   :param path: 保存路径
   :return: 0
   """
    if 'int8' in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif 'int16' in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    if len(im_data.shape) == 3:
        im_bands, im_height, im_width = im_data.shape
    elif len(im_data.shape) == 2:
        im_data = np.array([im_data])
    else:
        im_bands, (im_height, im_width) = 1, im_data.shape
        # 创建文件
    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(path, im_width, im_height, im_bands, datatype)
    if (dataset != None):
        dataset.SetGeoTransform(im_geotrans)  # 写入仿射变换参数
        dataset.SetProjection(im_proj)  # 写入投影
    for i in range(im_bands):
        dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
    del dataset
    print('file_writing process is finished')

def salt_pepper(image, salt, pepper):
    """
    添加椒盐噪声的图像
    :param image: 输入图像
    :param salt: 盐比例
    :param pepper: 椒比例
    :return: 添加了椒盐噪声的图像
    """
    height = image.shape[0]
    width = image.shape[1]
    pertotal = salt + pepper  # 总噪声占比
    noise_image = image.copy()
    noise_num = int(pertotal * height * width)
    for i in range(noise_num):
        rows = np.random.randint(0, height - 1)
        cols = np.random.randint(0, width - 1)
        if (np.random.randint(0, 100) < salt * 100):
            noise_image[rows][cols] = 255
        else:
            noise_image[rows][cols] = 0
    return noise_image


def low_pass_filtering(image, radius):
    """
    低通滤波函数
    :param image: 输入图像
    :param radius: 半径
    :return: 滤波结果
    """
    # 对图像进行傅里叶变换，fft是一个三维数组，fft[:, :, 0]为实数部分，fft[:, :, 1]为虚数部分
    fft = cv2.dft(np.float32(image), flags=cv2.DFT_COMPLEX_OUTPUT)
    # 对fft进行中心化，生成的dshift仍然是一个三维数组
    dshift = np.fft.fftshift(fft)

    # 得到中心像素
    rows, cols = image.shape[:2]
    mid_row, mid_col = int(rows / 2), int(cols / 2)

    # 构建掩模，256位，两个通道
    mask = np.zeros((rows, cols, 2), np.float32)
    mask[mid_row - radius:mid_row + radius, mid_col - radius:mid_col + radius] = 1

    # 给傅里叶变换结果乘掩模
    fft_filtering = dshift * mask
    # 傅里叶逆变换
    ishift = np.fft.ifftshift(fft_filtering)
    image_filtering = cv2.idft(ishift)
    image_filtering = cv2.magnitude(image_filtering[:, :, 0], image_filtering[:, :, 1])
    # 对逆变换结果进行归一化（一般对图像处理的最后一步都要进行归一化，特殊情况除外）
    cv2.normalize(image_filtering, image_filtering, 0, 1, cv2.NORM_MINMAX)
    return image_filtering


def high_pass_filtering(image, radius):
    """
    高通滤波函数
    :param image: 输入图像
    :param radius: 半径
    :return: 滤波结果
    """
    # 对图像进行傅里叶变换，fft是一个三维数组，fft[:, :, 0]为实数部分，fft[:, :, 1]为虚数部分
    fft = cv2.dft(np.float32(image), flags=cv2.DFT_COMPLEX_OUTPUT)
    # 对fft进行中心化，生成的dshift仍然是一个三维数组
    dshift = np.fft.fftshift(fft)

    # 得到中心像素
    rows, cols = image.shape[:2]
    mid_row, mid_col = int(rows / 2), int(cols / 2)

    # 构建ButterWorth高通滤波掩模

    mask = np.ones((rows, cols, 2), np.float32)
    mask[mid_row - radius:mid_row + radius, mid_col - radius:mid_col + radius] = 0
    # 给傅里叶变换结果乘掩模
    fft_filtering = dshift * mask
    # 傅里叶逆变换
    ishift = np.fft.ifftshift(fft_filtering)
    image_filtering = cv2.idft(ishift)
    image_filtering = cv2.magnitude(image_filtering[:, :, 0], image_filtering[:, :, 1])
    # 对逆变换结果进行归一化（一般对图像处理的最后一步都要进行归一化，特殊情况除外）
    cv2.normalize(image_filtering, image_filtering, 0, 1, cv2.NORM_MINMAX)
    return image_filtering


def band_pass_filter(image, radius, w, n=1):
    """
    带通滤波函数
    :param image: 输入图像
    :param radius: 带中心到频率平面原点的距离
    :param w: 带宽
    :param n: 阶数
    :return: 滤波结果
    """
    # 对图像进行傅里叶变换，fft是一个三维数组，fft[:, :, 0]为实数部分，fft[:, :, 1]为虚数部分
    fft = cv2.dft(np.float32(image), flags=cv2.DFT_COMPLEX_OUTPUT)
    # 对fft进行中心化，生成的dshift仍然是一个三维数组
    dshift = np.fft.fftshift(fft)

    # 得到中心像素
    rows, cols = image.shape[:2]
    mid_row, mid_col = int(rows / 2), int(cols / 2)

    # 构建掩模，256位，两个通道
    # mask = np.zeros((rows, cols, 2), np.float32)
    # d = np.sqrt(np.square(np.arange(rows)[:, np.newaxis] - mid_row) + np.square(np.arange(cols) - mid_col))
    #
    # mask = np.where(np.logical_and(radius - w / 2 < d, d < radius + w / 2), 1, 0)
    # mask = np.expand_dims(mask, axis=-1)
    # mask = np.concatenate((mask, mask), axis=-1).astype(np.float32)
    mask = np.ones((rows, cols, 2), np.uint8)
    for i in range(0, rows):
        for j in range(0, cols):
            d = math.sqrt(pow(i - mid_row, 2) + pow(j - mid_col, 2))  # 计算(i, j)到中心点的距离
            if radius - w / 2 < d < radius + w / 2:
                mask[i, j, 0] = mask[i, j, 1] = 0
            else:
                mask[i, j, 0] = mask[i, j, 1] = 1


    # 给傅里叶变换结果乘掩模
    fft_filtering = dshift * np.float32(mask)
    # 傅里叶逆变换
    ishift = np.fft.ifftshift(fft_filtering)
    image_filtering = cv2.idft(ishift)
    image_filtering = cv2.magnitude(image_filtering[:, :, 0], image_filtering[:, :, 1])
    # 对逆变换结果进行归一化（一般对图像处理的最后一步都要进行归一化，特殊情况除外）
    cv2.normalize(image_filtering, image_filtering, 0, 1, cv2.NORM_MINMAX)
    return image_filtering


def bandstop_filter(image, radius, w, n=1):
    """
    带通滤波函数
    :param image: 输入图像
    :param radius: 带中心到频率平面原点的距离
    :param w: 带宽
    :param n: 阶数
    :return: 滤波结果
    """
    # 对图像进行傅里叶变换，fft是一个三维数组，fft[:, :, 0]为实数部分，fft[:, :, 1]为虚数部分
    fft = cv2.dft(np.float32(image), flags=cv2.DFT_COMPLEX_OUTPUT)
    # 对fft进行中心化，生成的dshift仍然是一个三维数组
    dshift = np.fft.fftshift(fft)

    # 得到中心像素
    rows, cols = image.shape[:2]
    mid_row, mid_col = int(rows / 2), int(cols / 2)

    # 构建掩模，256位，两个通道
    mask = np.zeros((rows, cols, 2), np.float32)
    for i in range(0, rows):
        for j in range(0, cols):
            # 计算(i, j)到中心点的距离
            d = math.sqrt(pow(i - mid_row, 2) + pow(j - mid_col, 2))
            if radius - w / 2 < d < radius + w / 2:
                mask[i, j, 0] = mask[i, j, 1] = 0
            else:
                mask[i, j, 0] = mask[i, j, 1] = 1

    # 给傅里叶变换结果乘掩模
    fft_filtering = dshift * np.float32(mask)
    # 傅里叶逆变换
    ishift = np.fft.ifftshift(fft_filtering)
    image_filtering = cv2.idft(ishift)
    image_filtering = cv2.magnitude(image_filtering[:, :, 0], image_filtering[:, :, 1])
    # 对逆变换结果进行归一化（一般对图像处理的最后一步都要进行归一化，特殊情况除外）
    cv2.normalize(image_filtering, image_filtering, 0, 1, cv2.NORM_MINMAX)
    return image_filtering

def image_filter(image, radius, filter_method):
    """
     频率域滤波函数
     :param image: 输入图像(2维图像）
     :param kernel_size: 滤波核的大小
     :param blur_method: 滤波方式
     :return: 滤波结果
     """
    if filter_method == 'low_pass_filter':
        filtered_image = low_pass_filtering(image, radius)
    elif filter_method == 'high_pass_filter':
        filtered_image = high_pass_filtering(image, radius)
    elif filter_method == 'band_pass_filter':
        filtered_image = band_pass_filter(image, radius, radius)

    return filtered_image

def image_blur(image, kernel_size, blur_method):
    """
     空间域滤波函数
     :param image: 输入图像
     :param kernel_size: 滤波核的大小
     :param blur_method: 滤波方式
     :return: 滤波结果
     """
    if blur_method == 'mean_blur':
        blurred_image = cv2.blur(image, (kernel_size,kernel_size))
    elif blur_method == 'median_blur':
        blurred_image = cv2.medianBlur(image, kernel_size)
    elif blur_method == 'gaussian_blur':
        blurred_image = cv2.GaussianBlur(image, (kernel_size,kernel_size), 0)
    else:
        print('没有相应的滤波函数')
        blurred_image = 0
    return blurred_image



def normalize_image(image):
    """
    归一化函数
     :param image: 输入图像
     :return: 归一化结果
    """
    image = np.float32(image)
    normalized_image = (image - np.min(image)) / (np.max(image) - np.min(image))
    # 如果需要，可以将归一化后的图像转换为8位无符号整数
    normalized_image_uint8 = (normalized_image * 255).astype(np.uint8)
    return normalized_image_uint8

def enhancefun(file_path,save_path,is_auto_revise_data_flag,is_normalize_data_flag,kernel_size,filter_method):
    im_data, im_width, im_height, im_bands, im_geotrans, im_proj = read_tiff(file_path)
    if im_bands > 3 and is_auto_revise_data_flag == False:
        print('输入数据不是红绿蓝三波段影像，请手动修改数据！')
        data_band_require_flag = False
    elif im_bands > 3 and is_auto_revise_data_flag == True:
        print('输入数据不是红绿蓝三波段影像，将自动保留前3个波段，并将其设定为蓝、绿、红波段！')
        im_data = im_data[0:3]
        data_band_require_flag = True
    else:
        data_band_require_flag = True
    if data_band_require_flag == True:
        if 'int8' not in im_data.dtype.name and is_normalize_data_flag == False:
            print('输入数据不是8bit数据，请手动修改数据格式！')
            data_type_require_flag = False
        elif 'int8' not in im_data.dtype.name and is_normalize_data_flag == True:
            print('输入数据不是8bit数据，将自动修改为8bit数据，并对数据进行归一化处理！')
            im_data = normalize_image(im_data)
            data_type_require_flag = True
        else:
            data_type_require_flag = True
    if data_band_require_flag == True and data_band_require_flag == True:
        if filter_method.split('_')[-1] == 'filter':
            filter_image = np.float32(np.zeros_like(im_data))
            for i in range(3):
                filter_image[i] = image_filter(im_data[i], kernel_size, filter_method)
            write_tiff_img(filter_image, im_width, im_height, 3, im_geotrans, im_proj, save_path)
        else:
            im_data = np.transpose(im_data, (1, 2, 0))
            filter_image = image_blur(im_data, kernel_size, filter_method)
            filter_image = np.transpose(filter_image, (2, 0, 1))
            write_tiff_img(filter_image, im_width, im_height, 3, im_geotrans, im_proj, save_path)

