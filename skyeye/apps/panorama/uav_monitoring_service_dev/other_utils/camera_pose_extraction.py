
import numpy as np
import cv2 as cv

# file = r'../data/camera_info/images.txt'
# with open(file, 'rb') as f:
#     lines = f.readlines()
#     for i in range(len(lines)):
#         if i % 2 == 0 and i != 0 and i != 2:
#             idx, q1, q2, q3, q4, t1, t2, t3, camera_id, image_name = lines[i].decode().split(" ")
#             # 绝对位姿
#             absolute_pose = pycolmap.qvec_to_rotmat(np.array([q1, q2, q3, q4], dtype=np.float32))



m1 = np.array([[0.55625008, -0.74093524,  0.37629884],
               [0.75433293,  0.64017705,  0.14544817],
               [-0.34866555,  0.20294905,  0.91501039]])
t1 = np.array(['-0.19732434512860389', '1.7963297578684325', '-2.0041171871697627'], dtype=np.float32)
m2 = np.array([[0.57282356, -0.73174545,  0.36935319],
               [0.81868833,  0.53289862, -0.21393568],
               [-0.04028135, 0.42493254,  0.90432834]])
t2 = np.array(['-0.17295149769803864', '0.54452498887448708', '-1.5405647689220499'], dtype=np.float32)

relative_r = np.dot(m1, np.linalg.inv(m2))

K = np.array([[2626.1882085897741, 0, 2016],
              [0, 2626.1882085897741, 1512],
              [0, 0, 1]])

# 构建一个 3 * 3 的矩阵
transform_matrix = np.dot(K, np.dot(relative_r, np.linalg.inv(K)))
# extra_matrix = np.array()

# 转换
img1 = cv.imread(r'D:\mgr\GTMap\CameraLocalization\data\panorama\100_0770\DJI_0708.JPG')
img2 = cv.imread(r'D:\mgr\GTMap\CameraLocalization\data\panorama\100_0770\DJI_0707.JPG')
warp_img = cv.warpPerspective(img1, transform_matrix, (4032, 3024))

