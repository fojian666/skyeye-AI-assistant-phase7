try:
    import gdal,osr
except:
    from osgeo import gdal,osr
import ai_config as cg
from math import *

def get_squeeze_split_region_info(image_path, block_size, overlap_size=(100, 100)):
    """
    获取缩略图分区信息
        Args:
            image_path: 原始影像路径
            block_size: 影像切分单元
            overlap_size: 缩略图输出路径

        Returns:
            split_info: 全分区信息
            overlap_col_info: 列(竖）重叠带坐标信息
            overlap_row_info: 行（横）重叠带分区信息
            index_info: split_info索引信息
            rate: 实际影像与缩略图缩放比例
            split_col_count: 分割列数
            split_row_count: 分割行数

    """
    # 读取图片信息
    image_dataset = gdal.Open(image_path)
    h = image_dataset.RasterYSize
    w = image_dataset.RasterXSize
    # 计算压缩比例，取压缩单元与最短边之比
    if h < w:
        rate = cg.SQUEEZE_UNIT / h
    else:
        rate = cg.SQUEEZE_UNIT / w

    srs = osr.SpatialReference()
    srs.ImportFromWkt(image_dataset.GetProjection())
    # 计算重叠行数
    overlap_row = 1 + ceil((image_dataset.RasterYSize - block_size) / (block_size - overlap_size[1]))
    # 计算重叠列数
    overlap_col = 1 + ceil((image_dataset.RasterXSize - block_size) / (block_size - overlap_size[0]))

    # 分幅行列数
    split_col_count = ceil(overlap_col / cg.SPLIT_UNIT)
    split_row_count = ceil(overlap_row / cg.SPLIT_UNIT)

    # 切割边缘长宽张数
    left_col = overlap_col % cg.SPLIT_UNIT
    if left_col == 0:
        left_col = cg.SPLIT_UNIT
    left_row = overlap_row % cg.SPLIT_UNIT
    if left_row == 0:
        left_row = cg.SPLIT_UNIT
    # 记录每个小图分区的起点坐标、终点坐标
    split_info = {}
    # 记录每个小图重叠带的起点坐标、终点坐标
    overlap_col_info = {}  # 竖着的重叠带
    overlap_row_info = {}  # 横着的重叠带
    # 记录每个分区的索引号
    index_info = {}
    # block_size和overlap_size在小图的长度
    split_block_size = rate * block_size

    index = 1
    # 计算每个分区的小图起终点坐标
    for col in range(split_col_count):
        offset_x = col * cg.SPLIT_UNIT * split_block_size
        for row in range(split_row_count):
            offset_y = row * cg.SPLIT_UNIT * split_block_size
            split_info[str(col) + "_" + str(row)] = {}
            index_info[index] = str(col) + "_" + str(row)
            start_x = offset_x
            start_y = offset_y
            if col >= split_col_count - 1:
                end_x = start_x + left_col * split_block_size
            else:
                end_x = start_x + cg.SPLIT_UNIT * split_block_size
            if row >= split_row_count - 1:
                end_y = start_y + left_row * split_block_size
            else:
                end_y = start_y + cg.SPLIT_UNIT * split_block_size

            split_info[str(col) + "_" + str(row)]["start"] = (start_x, start_y)
            split_info[str(col) + "_" + str(row)]["end"] = (end_x, end_y)
            index += 1

    # 计算每个分区的小图起终点坐标
    col_index = 1
    row_index = 1
    for col in range(split_col_count):
        for row in range(split_row_count):
            if col < split_col_count - 1:
                # "_col_"代表竖着的重叠带
                overlap_col_info[str(col) + "_" + str(row)] = {}
                overlap_col_info[str(col) + "_" + str(row)]["start"] = split_info[str(col + 1) + "_" + str(row)]["start"]
                overlap_col_info[str(col) + "_" + str(row)]["end"] = split_info[str(col) + "_" + str(row)]["end"]
                overlap_col_info[str(col) + "_" + str(row)]["no"] = col_index
                col_index += 1
            if row < split_row_count - 1:
                # "_row_"代表横着的重叠带
                overlap_row_info[str(col) + "_" + str(row)] = {}
                overlap_row_info[str(col) + "_" + str(row)]["start"] = split_info[str(col) + "_" + str(row + 1)]["start"]
                overlap_row_info[str(col) + "_" + str(row)]["end"] = split_info[str(col) + "_" + str(row)]["end"]
                overlap_row_info[str(col) + "_" + str(row)]["no"] = row_index
                row_index += 1

    return split_info, overlap_col_info, overlap_row_info, index_info, rate, split_col_count, split_row_count


def is_two_image_size_same(img1, img2):
    # 判断两张图size是否相同
    # 读取图片1信息
    image_dataset = gdal.Open(img1)
    h1 = image_dataset.RasterYSize
    w1 = image_dataset.RasterXSize
    # 读取图片2信息
    image_dataset2 = gdal.Open(img2)
    h2 = image_dataset2.RasterYSize
    w2 = image_dataset2.RasterXSize

    if h1 != h2 or w1 != w2:
        return False
    else:
        return True

