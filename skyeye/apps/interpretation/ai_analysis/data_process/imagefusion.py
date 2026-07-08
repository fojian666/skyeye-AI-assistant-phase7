import os,shutil
import numpy as np
import cv2
from sklearn.decomposition import PCA
from osgeo import gdal,gdalconst
import math

def read_tif_img(file_path):
    dataset = gdal.Open(file_path)
    if dataset == None:
        print(file_path + "文件无法打开")
        return
    im_width = dataset.RasterXSize  # 栅格矩阵的列数
    im_height = dataset.RasterYSize  # 栅格矩阵的行数
    # im_bands = dataset.RasterCount  # 波段数
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    # im_band = im_data[0:im_height, 0:im_width]
    # im_blueBand = im_data[0, 0:im_height, 0:im_width]  # 获取蓝波段
    # im_greenBand = im_data[1, 0:im_height, 0:im_width]  # 获取绿波段
    # im_redBand = im_data[2, 0:im_height, 0:im_width]  # 获取红波段
    # im_nirBand = im_data[3, 0:im_height, 0:im_width]  # 获取近红外波段
    return im_data, im_width, im_height, im_geotrans, im_proj

def read_tif_RGB(file_path):
    '''
    读取多光谱影像
    '''
    dataset = gdal.Open(file_path)
    if dataset == None:
        print(file_path + "文件无法打开")
        return
    im_width = dataset.RasterXSize  # 栅格矩阵的列数
    im_height = dataset.RasterYSize  # 栅格矩阵的行数
    # im_bands = dataset.RasterCount  # 波段数
    im_data = dataset.ReadAsArray(0, 0, im_width, im_height)  # 获取数据
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    im_band = im_data[0:im_height, 0:im_width]
    im_blueBand = im_data[0, 0:im_height, 0:im_width]  # 获取蓝波段
    im_greenBand = im_data[1, 0:im_height, 0:im_width]  # 获取绿波段
    im_redBand = im_data[2, 0:im_height, 0:im_width]  # 获取红波段
    # im_nirBand = im_data[3, 0:im_height, 0:im_width]  # 获取近红外波段
    return im_blueBand, im_greenBand, im_redBand, im_width, im_height, im_geotrans, im_proj

def write_tiff_img(im_data, im_width, im_height, im_bands, im_geotrans, im_proj, path):
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

def Resampling2Images(in_filename, ref_filename, out_filename):
    in_file = gdal.Open(in_filename,gdal.GA_ReadOnly)
    in_band = in_file.GetRasterBand(1)
    in_bands = in_file.RasterCount  # 波段数
    in_Proj = in_file.GetProjection()
    ref_file = gdal.Open(ref_filename, gdal.GA_ReadOnly)
    ref_geoTrans = ref_file.GetGeoTransform()
    ref_Proj = ref_file.GetProjection()
    ref_band = ref_file.GetRasterBand(1)
    x = ref_file.RasterXSize
    y = ref_file.RasterYSize

    driver = gdal.GetDriverByName('GTiff')
    output = driver.Create(out_filename, x, y, in_bands, in_band.DataType)
    output.SetGeoTransform(ref_geoTrans)
    output.SetProjection(ref_Proj)
    options = gdal.WarpOptions(srcSRS = in_Proj,
                        dstSRS = ref_Proj,
                        resampleAlg = gdalconst.GRA_Bilinear,
                        # dstNodata = 0,
                        # srcNodata = 255,
                        )
    gdal.Warp(output, in_filename, options=options)

def gram_schmidt(image1, image2):
    # 将图像转换为灰度并重塑为向量
    vec1 = image1.astype(float).reshape(-1)
    vec2 = image2.astype(float).reshape(-1)

    # 第一步Gram-Schmidt: 正交化第一个向量
    vec1_orth = vec1 - np.dot(vec1, vec2) / np.dot(vec2, vec2) * vec2
    vec1_orth = vec1_orth / np.linalg.norm(vec1_orth)

    # 第二步Gram-Schmidt: 正交化第二个向量
    vec2_orth = image2.astype(float) - np.dot(vec1_orth, vec2) * vec1_orth
    vec2_orth = vec2_orth / np.linalg.norm(vec2_orth)

    # 将正交化后的向量重塑成图像形状并归一化
    image1_orth = vec1_orth.reshape(image1.shape)
    image2_orth = vec2_orth.reshape(image2.shape)

    image1_orth = (image1_orth - image1_orth.min()) / (image1_orth.max() - image1_orth.min()) * 255
    image2_orth = (image2_orth - image2_orth.min()) / (image2_orth.max() - image2_orth.min()) * 255

    return image1_orth, image2_orth


def run_gram_schmidt(image1_path, image2_path):
    # 读取图像
    image1 = cv2.imread('image1.jpg', cv2.IMREAD_GRAYSCALE)
    image2 = cv2.imread('image2.jpg', cv2.IMREAD_GRAYSCALE)

    # 执行Gram-Schmidt融合
    image1_orth, image2_orth = gram_schmidt(image1, image2)

    # 展示正交化后的图像
    cv2.imshow('Orthogonalized Image 1', image1_orth)
    cv2.imshow('Orthogonalized Image 2', image2_orth)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def get_gray_cumulative_prop(gray):
    """获取图像的累积分布直方图，即就P{X<=x}的概率
        - 大X表示随机变量
        - 小x表示取值边界
    """
    cum_gray = []
    sum_prop = 0.
    for i in gray:
        sum_prop += i
        cum_gray.append(sum_prop)  # 累计概率求和
    return cum_gray

def histogram_match(img_pix, ref_pix):
    """运行图像直方图匹配"""
    img_his = cv2.calcHist([img_pix], [0], None, [256], [0, 256])  # 2.获取图像的灰度直方图
    img_his = (img_his / (img_pix.shape[0] * img_pix.shape[1])).flatten()
    ref_his = cv2.calcHist([ref_pix], [0], None, [256], [0, 256])
    ref_his = (ref_his / (ref_pix.shape[0] * ref_pix.shape[1])).flatten()
    cul_img_his = get_gray_cumulative_prop(img_his)  # 3.获取图像的累积分布函数
    cul_ref_his = get_gray_cumulative_prop(ref_his)

    # 寻找像素映射（累积概率，就进原则）
    new_index = []
    for each_gray in cul_img_his:
        # 求出原直方图每一个灰度级累计概率在指定直方图上的灰度索引
        diff = list(abs(np.array(cul_ref_his - each_gray)))
        closest_index = diff.index(min(diff))  # 索引代表对应填充的灰度级
        new_index.append(closest_index)

    new_index = np.array(new_index)
    # 填充像素
    height, width = img_pix.shape
    new_img_pix = np.zeros((height, width), dtype=np.uint8)
    for h in range(height):
        new_img_pix[h, :] = new_index[img_pix[h, :]]
    return new_img_pix


def RGB2HIS(image):
    image = np.float32(image)
    R = image[0]
    G = image[1]
    B = image[2]
    I = (R+G+B)/3

    min_value = np.min(image, axis=0)
    S = 1-3*min_value/(R+G+B)
    S[I == 0] = 0
    numerator = 1/2*((R-G)+(R-B))
    denominator = pow(((R-G)*(R-G)+(R-B)*(G-B)), 1/2)
    denominator = np.where(denominator != 0, denominator, 1)  # 用1替换零，或者采取其他适当措施
    theta = np.arccos(numerator / denominator)

    # theta = math.acos(numerator/denominator)
    theta = np.degrees(theta)
    H = np.where(G<B, 360-theta, theta)

    return H, I, S

def HIS2RGB(H, I, S):
    H = np.float32(H)
    I = np.float32(I)
    S = np.float32(S)

    H = np.radians(H)
    mask_1 = np.where(H<120, 1, 0)
    mask_2 = np.where(np.logical_and(H>=120, H < 240), 1, 0)
    mask_3 = np.where(H>=240, 1, 0)
    B1 = (I*(1-S))*mask_1
    R1 = (I*(1+(S*np.cos(H)/np.cos(60-H))))*mask_1
    G1 = (3*I-(B1+R1))*mask_1

    R2 = (I*(1-S))*mask_2
    G2 = (I*(1+S*np.cos(H-120)/np.cos(180-H)))*mask_2
    B2 = (3*I-(R2+G2))*mask_2

    G3 = (I*(1-S))*mask_3
    B3 = (I*(1+S*np.cos(H-240)/np.cos(300-H)))*mask_3
    R3 = (3*I-(G3+B3))*mask_3

    R = R1+R2+R3
    G = G1+G2+G3
    B = B1+B2+B3
    return R, G, B


def match_image_value(pan_image, mul_image):
    # data_type = pan_image.dtype
    pan_image = np.float32(pan_image)
    mul_image = np.float32(mul_image)
    max_pan = np.max(pan_image)
    max_mul = np.max(mul_image)
    min_pan = np.min(pan_image)
    min_mul = np.min(mul_image)
    A = (max_mul-min_mul)/(max_pan-min_pan)
    B = (max_pan*min_mul-min_pan*max_mul)/(max_pan-min_pan)

    new_img = np.zeros_like(pan_image)

    height = pan_image.shape[0]
    width = pan_image.shape[1]
    for h in range(height):
        new_img[h, :] = pan_image[h, :]*A+B

    return np.uint8(new_img)

def TwoPercentLinearGray(gray, maxout, minout):
    '''
    对单波段灰度影像进行2%线性拉伸
    '''
    high_value = np.percentile(gray, 98)#取得98%直方图处对应灰度
    low_value = np.percentile(gray, 2)#同理
    truncated_gray = np.clip(gray, a_min=low_value, a_max=high_value)
    processed_gray = ((truncated_gray - low_value)/(high_value - low_value)) * (maxout - minout)#线性拉伸嘛
    return np.uint8(processed_gray)

def TwoPercentLinearRGB(image, max_out=255, min_out=0):
    '''
    对红绿蓝三波段影像进行2%线性拉伸
    '''
    r = image[0]
    g = image[1]
    b = image[2]
    r_p = TwoPercentLinearGray(r, max_out, min_out)
    g_p = TwoPercentLinearGray(g, max_out, min_out)
    b_p = TwoPercentLinearGray(b, max_out, min_out)
    # result = cv2.merge((b_p, g_p, r_p))#合并处理后的三个波段
    image[0] = r_p
    image[1] = g_p
    image[2] = b_p

    return np.uint8(image)

def his_image_fusion(mul_img_path, pan_img_path, save_fusion_path):
    '''
    利用HIS融合方法，首先获取全色波段和多光谱数据，然后对多光谱数据进行重采样，使二者分辨率保持一致
    然后对全色波段和多光谱数据进行变换，将其数值转换到0-255，为了更好的融合效果，进行2%线性拉伸，
    将多光谱进行HIS变换，然后将全色波段替换多光谱的I分量，最终再组合起来，保存
    '''
    rsmp_mul_path = os.path.join(os.path.dirname(save_fusion_path), 'rsmp.tif')
    Resampling2Images(mul_img_path, pan_img_path, rsmp_mul_path)
    B_band, G_band, R_band, mul_width, mul_height, mul_geotrans, mul_proj = read_tif_RGB(rsmp_mul_path)
    pan_img, pan_width, pan_height, pan_geotrans, pan_proj = read_tif_img(pan_img_path)
    mul_img_new = np.zeros((3,mul_height,mul_width))

    mul_img_new[0] = R_band
    mul_img_new[1] = G_band
    mul_img_new[2] = B_band

    mul_img = np.float32(mul_img_new)
    pan_img = np.float32(pan_img)
    min_mul = np.min(mul_img)
    max_mul = np.max(mul_img)
    min_pan = np.min(pan_img)
    max_pan = np.max(pan_img)
    mul_img = np.uint8((mul_img - min_mul)/(max_mul - min_mul)*255)
    pan_img = np.uint8((pan_img - min_pan)/(max_pan - min_pan)*255)
    mul_img = TwoPercentLinearRGB(mul_img)
    pan_img = TwoPercentLinearGray(pan_img, 255, 0)

    mul_img = mul_img.transpose(1, 2, 0)

    h_mul, i_mul, s_mul = cv2.split(cv2.cvtColor(mul_img, cv2.COLOR_BGR2HLS))

    fused_img_hsv = cv2.merge([h_mul, pan_img, s_mul])
    fused_img_rgb = cv2.cvtColor(fused_img_hsv, cv2.COLOR_HLS2BGR)
    fused_img_rgb = np.uint8((fused_img_rgb.transpose(2, 0, 1)))

    write_tiff_img(fused_img_rgb, pan_width, pan_height, 3, pan_geotrans, pan_proj, save_fusion_path)
    os.remove(rsmp_mul_path)




if __name__ == '__main__':
    mul_img_path = r'D:\data\example_data\example_data\original\SV1-01_20171021_L2A0000192762_1109170051408_01\SV1-01_20171021_L2A0000192762_1109170051408_01-MUX.tiff'
    pan_img_path = r'D:\data\example_data\example_data\original\SV1-01_20171021_L2A0000192762_1109170051408_01\SV1-01_20171021_L2A0000192762_1109170051408_01-PAN.tiff'
    save_fusion_path = r'D:\data\example_data\example_data\original\his_fusion.tif'
    his_image_fusion(mul_img_path, pan_img_path, save_fusion_path)