import cv2
from osgeo import gdal,osr,ogr
import numpy as np
import math
import os
import glob
import exifread

class Aerial2Orthophoto:
    def __init__(self):
        self.cx = None
        self.cy = None
        self.f = None
        self.k1 = None
        self.k2 = None
        self.k3 = None
        self.p1 = None
        self.p2 = None
        self.undistorted_image = None
        self.IMGfile = None
        self.image_height = None
        self.image_width = None
        self.lat=None
        self.lon=None
        self.alt=None
        self.camera_x=None
        self.camera_y=None
        self.camera_z=None
        self.omega=None
        self.phi=None
        self.kappa=None
        self.rotation_matrix = None
        self.image_corners_min_x = None
        self.image_corners_max_x = None
        self.image_corners_min_y = None
        self.image_corners_max_y = None
        self.output_image = None

    def llh2ecef(self, lat, lon, alt):
        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)  # WGS84坐标系的EPSG代码为4326
        bj1954 = osr.SpatialReference()
        bj1954.ImportFromEPSG(4549)  # WGS84坐标系的EPSG代码为4326
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lat, lon)
        # 创建转换对象
        transform = osr.CoordinateTransformation(wgs84, bj1954)
        point.Transform(transform)
        return [point.GetY(), point.GetX(), alt]

    def ReadIMGfile(self, filePath):
        b = b"\x3c\x2f\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x3e"
        a = b"\x3c\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x20"

        # aa = ["\x3c\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x20"]
        # bb = ["\x3c\x2f\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x3e"]

        img = open(filePath, 'rb')
        # bytearray() 方法返回一个新字节数组
        data = bytearray()
        # 标识符,
        flag = False

        for i in img.readlines():
            # 按行读取二进制信息，标签成对出现
            if a in i:
                flag = True
            if flag:
                # 把第i行数据复制到新数组中
                data += i
            if b in i:
                break
        if len(data) > 0:
            data = str(data.decode('ascii'))
            # filter()函数用于过滤序列，过滤掉不符合条件的元素，返回符合条件的元素组成新列表。
            # filter(function,iterable) ,function -- 判断函数。iterable -- 可迭代对象
            # python允许用lambda关键字创造匿名函数。
            # 在 lambda 关键字之后、冒号左边为参数列表，可不带参数，也可有多个参数。若有多个参数，则参数间用逗号隔开，冒号右边为 lambda 表达式的返回值。
            # left--->right
            # judge condition 'drone-dji:' in x
            lines = list(filter(lambda x: 'drone-dji:' in x, data.split("\n")))
            dj_data_dict = {}
            for d in lines:
                # remove 'drone-dji:'
                d = d.strip()[10:]
                # k is name
                # v is value
                k, v = d.split("=")
                dj_data_dict[k] = v

        # lat = float(dj_data_dict['GpsLatitude'].split('"')[1])
        # lon = float(dj_data_dict['GpsLongitude'].split('"')[1])
        #alt = float(dj_data_dict['RelativeAltitude'].split('"')[1])
        alt = float(dj_data_dict['AbsoluteAltitude'].split('"')[1])
        h = float(dj_data_dict['FlightYawDegree'].split('"')[1])
        p = float(dj_data_dict['FlightPitchDegree'].split('"')[1])
        r = float(dj_data_dict['FlightRollDegree'].split('"')[1])
        # DewarpData = dj_data_dict['DewarpData'].split('"')[1].split(';')[1].split(',')
        # DewarpData = np.array([3600, 3600, , 0, 0])
        # self.innerfx = float(DewarpData[0])
        # self.innerfy = float(DewarpData[1])
        # self.cx = float(DewarpData[2])
        # self.cy = float(DewarpData[3])
        # self.k1 = float(DewarpData[4])
        # self.k2 = float(DewarpData[5])
        # self.k3 = float(DewarpData[8])
        # self.p1 = float(DewarpData[6])
        # self.p2 = float(DewarpData[7])
        with open(filePath, 'rb') as f:
            tags = exifread.process_file(f)

        self.cx = float(str(tags['EXIF ExifImageWidth'])) / 2
        self.cy = float(str(tags['EXIF ExifImageLength'])) / 2
        DewarpData = np.array([3600, 3600, 0, 0, 0, 0, 0])
        self.innerfx = float(DewarpData[0])
        self.innerfy = float(DewarpData[1])
        self.k1 = float(DewarpData[2])
        self.k2 = float(DewarpData[3])
        self.k3 = float(DewarpData[4])
        self.p1 = float(DewarpData[5])
        self.p2 = float(DewarpData[6])
        latitude_info = str(tags['GPS GPSLatitude']).replace("[", "").replace("]", '').split(",")
        longitude_info = str(tags['GPS GPSLongitude']).replace("[", "").replace("]", '').split(",")
        lat = float(latitude_info[0]) + float(latitude_info[1]) / 60 + eval(latitude_info[2]) / 3600
        lon = float(longitude_info[0]) + float(longitude_info[1]) / 60 + eval(longitude_info[2]) / 3600

        self.f = float(str(tags['EXIF FocalLengthIn35mmFilm']))*1000

        heading = math.radians(h)
        pitch = math.radians(p)
        roll = math.radians(r)

        pos_x, pos_y, pos_z = self.llh2ecef(lat, lon, alt)
        self.camera_x = pos_x
        self.camera_y = pos_y
        self.camera_z = pos_z
        self.omega = pitch
        self.phi = roll
        self.kappa = heading
        self.rotation_matrix = cv2.Rodrigues(np.array([self.omega, self.phi, self.kappa]))[0]
        self.IMGfile = cv2.imread(filePath)
        print('获取参数如下：')
        print('35mm等效焦距：', self.f/1000)
        print('cx偏移量：', self.cx)
        print('cy偏移量：', self.cy)
        print('k1：', self.k1)
        print('k2：', self.k2)
        print('p1：', self.p1)
        print('p2：', self.p2)
        print('k1：', self.k1)
        print('相机经纬度坐标：', (lon, lat, alt))
        print('相机CSCS2000坐标：', (pos_x, pos_y, pos_z))
        print('外方位元素(heading,pitch,roll)：', (heading, pitch, roll))

    def distortionRectifying(self):
        """
        TODO: 影像去畸变
        """
        self.image_height, self.image_width = self.IMGfile.shape[:2]
        cx = self.image_width/2+self.cx
        cy = self.image_height/2+self.cy

        self.distortion_coefficients = np.array([[self.k1, self.k2, self.p1, self.p2, self.k3]])
        self.camera_matrix = np.array([[self.innerfx, 0, cx], [0, self.innerfy, cy], [0, 0, 1]])

        undistorted_image = cv2.undistort(self.IMGfile, self.camera_matrix, self.distortion_coefficients)
        self.image_height, self.image_width = undistorted_image.shape[:2]

        self.undistorted_image=undistorted_image

    def CacularConer(self):
        fx = self.f / 1000
        fy = self.f / 1000
        cx = self.image_width/2+self.cx
        cy = self.image_height/2+self.cy
        image_corners = np.array(
            [[0, 0], [0, self.image_height - 1], [self.image_width - 1, 0], [self.image_width - 1, self.image_height - 1]])
        image_corners_camera = np.zeros_like(image_corners, dtype=np.float64)
        for i in range(4):
            x_cam = (image_corners[i, 0] - cx) / fx
            y_cam = (image_corners[i, 1] - cy) / fy
            z_cam = - self.f / 1000
            image_corners_cameraX,image_corners_cameraY,image_corners_cameraZ = self.GetGround_coords(x_cam,y_cam,z_cam)
            image_corners_camera[i, 0] = image_corners_cameraX
            image_corners_camera[i, 1] = image_corners_cameraY

        self.image_corners_min_x, self.image_corners_max_x = np.min(image_corners_camera[:, 0]), np.max(
            image_corners_camera[:, 0])
        self.image_corners_min_y, self.image_corners_max_y = np.min(image_corners_camera[:, 1]), np.max(
            image_corners_camera[:, 1])

    def GetGround_coords(self, x_cam, y_cam, z_cam):

        ground_coords = np.dot(self.rotation_matrix, np.array([x_cam, y_cam, z_cam]))
        return (ground_coords[0] + self.camera_x,-ground_coords[1] + self.camera_y, self.camera_z-ground_coords[2])

    def Orthophoto(self):
        fx = self.f / 1000
        fy = self.f / 1000
        self.output_image = np.zeros((int(self.image_height), int(self.image_width), 3), dtype=np.uint8)
        cx = self.image_width/2+self.cx
        cy = self.image_height/2+self.cy
        # 循环遍历每个像素
        for i in range(self.image_height):
            for j in range(self.image_width):
                # 计算像素在相机坐标系中的坐标
                x_cam = (j - cx) / fx
                y_cam = (i - cy) / fy
                z_cam = -self.f/1000

                # 旋转相机坐标系到地面坐标系
                image_corners_cameraX, image_corners_cameraY,image_corners_cameraZ = self.GetGround_coords(x_cam, y_cam, z_cam)

                ground_x = image_corners_cameraX
                ground_y = image_corners_cameraY

                # 计算像素在输出影像中的位置
                output_x = int((ground_x - self.image_corners_min_x) / (self.image_corners_max_x - self.image_corners_min_x) * (
                            self.image_width - 1)) - 1
                output_y = int((ground_y - self.image_corners_min_y) / (self.image_corners_max_y - self.image_corners_min_y) * (
                            self.image_height - 1)) - 1
                if output_x < 0 or output_y < 0:
                    continue
                if output_x >= self.image_width or output_y >= self.image_height:
                    continue
                self.output_image[output_y, output_x] = self.undistorted_image[i, j]

    def Orthophoto2(self):
        self.output_image = np.zeros((int(self.image_height), int(self.image_width), 3), dtype=np.uint8)
        # 创建第一个影像中所有像元的行坐标和列坐标数组
        rows1, cols1 = np.meshgrid(np.arange(self.output_image.shape[0]), np.arange(self.output_image.shape[1]), indexing='ij')
        # 创建第二个影像中所有像元的行坐标和列坐标数组
        rows2, cols2 = np.meshgrid(np.arange(self.undistorted_image.shape[0]), np.arange(self.undistorted_image.shape[1]), indexing='ij')
        rows_mapped, cols_mapped = self.coordsmapping_func(rows1, cols1)

        rows_mapped[rows_mapped < 0] = 0
        rows_mapped[rows_mapped >= self.image_width] = self.image_width-1
        cols_mapped[cols_mapped < 0] = 0
        cols_mapped[cols_mapped >= self.image_height] = self.image_height-1

        # 对第一个影像进行赋值
        self.output_image[cols_mapped, rows_mapped ] = self.undistorted_image[rows2, cols2]

    def OutPutfile(self,outPutName):
        pixel_size_x = (self.image_corners_max_x - self.image_corners_min_x) / self.image_width
        pixel_size_y = (self.image_corners_max_y - self.image_corners_min_y) / self.image_height
        geotransform = (self.image_corners_min_x - pixel_size_x / 2, pixel_size_x, 0, self.image_corners_min_y + pixel_size_y / 2, 0,pixel_size_y)
        bj1954 = osr.SpatialReference()
        bj1954.ImportFromEPSG(4326)  # WGS84坐标系的EPSG代码为4326
        driver = gdal.GetDriverByName('GTiff')
        output_dataset = driver.Create(outPutName, self.image_width, self.image_height, 3, gdal.GDT_Float32)
        output_dataset.SetProjection(bj1954.ExportToWkt())
        output_dataset.SetGeoTransform(geotransform)
        output_dataset.GetRasterBand(1).WriteArray(self.output_image[:, :, 2])
        output_dataset.GetRasterBand(2).WriteArray(self.output_image[:, :, 1])
        output_dataset.GetRasterBand(3).WriteArray(self.output_image[:, :, 0])
        output_dataset.FlushCache()

    def location(self, points):
        pixel_size_x = (self.image_corners_max_x - self.image_corners_min_x) / self.image_width
        pixel_size_y = (self.image_corners_max_y - self.image_corners_min_y) / self.image_height
        geotransform = (self.image_corners_min_x - pixel_size_x / 2,
                        pixel_size_x, 0,
                        self.image_corners_min_y + pixel_size_y / 2,
                        0,
                        pixel_size_y)
        return np.column_stack([geotransform[0] + points[:, 0] * geotransform[1], geotransform[3] - points[:, 1] * geotransform[5]])


    def coordsmapping_func(self, i, j):
        fx = self.f / 1000
        fy = self.f / 1000
        cx = self.image_width/2+self.cx
        cy = self.image_height/2+self.cy
        x_cam = (j.flatten() - cx) / fx
        y_cam = (i.flatten() - cy) / fy
        z_cam = np.zeros_like(x_cam)
        z_cam[:] = -self.f / 1000

        image_corners_cameraX, image_corners_cameraY, image_corners_cameraZ = self.GetGround_coords(x_cam, y_cam, z_cam)
        ground_x = image_corners_cameraX
        ground_y = image_corners_cameraY
        output_x = ((ground_x - self.image_corners_min_x) / (self.image_corners_max_x - self.image_corners_min_x) * (
                self.image_width)).astype(int).reshape((self.image_height, self.image_width))
        output_y = ((ground_y - self.image_corners_min_y) / (self.image_corners_max_y - self.image_corners_min_y) * (
                self.image_height)).astype(int).reshape((self.image_height, self.image_width))

        return (output_x, output_y)

if __name__ =='__main__':
    folder_path = r'D:\mgr\software\COLMAP-3.8-windows-cuda\bev_image'
    Orthophoto = Aerial2Orthophoto()
    # 遍历文件夹中的所有 JPG 图片
    for file_path in glob.glob(os.path.join(folder_path, '*.JPG')):
        print('---------------------------')
        print('正在处理：'+file_path)
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        Orthophoto.ReadIMGfile(file_path)
        Orthophoto.distortionRectifying()
        Orthophoto.CacularConer()
        Orthophoto.Orthophoto2()
        Orthophoto.OutPutfile(folder_path+'\\'+file_name+'.tif')
        print('处理完成，文件存储在：'+folder_path+'\\'+file_name+'.tif')
