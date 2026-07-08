# _*_ coding: utf-8 _*_
# @Time : 2024/8/9 13:18 
# @Author : xxx 
# @Version：V 0.1
# @File : test2.py
# @desc :
import os

import cv2

from ultralytics import YOLO
work_dir = os.path.dirname(os.path.abspath(__file__))
#from moviepy.editor import VideoFileClip

def crop_video(input_video_path, output_video_path, start_time, duration):
    # 加载视频文件
    video = VideoFileClip(input_video_path)

    # 从视频中裁剪出指定的时间段
    cropped_video = video.subclip(start_time, start_time + duration)

    # 将裁剪后的视频保存到新文件
    cropped_video.write_videofile(output_video_path)

    # 关闭视频文件
    video.close()
def detect_objects_in_video(input_video_path, output_video_path,):
    # 加载模型
    model_path = os.path.join(work_dir, 'checkpoints', 'hyst_yolov8_best.pt')
    model = YOLO(model_path)

    # 打开输入视频文件
    cap = cv2.VideoCapture(input_video_path)

    # 获取视频的帧率
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 获取视频的宽度和高度
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 创建 VideoWriter 对象来保存输出视频
    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 使用 YOLOv8 模型进行检测
        results = model(frame)[0]

        # 将结果画在帧上
        annotated_frame = results.plot()

        # 将帧写入输出视频
        out.write(annotated_frame)

        # 显示帧（可选）
        cv2.imshow('YOLOv8 Inference', annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 释放资源
    cap.release()
    out.release()
    cv2.destroyAllWindows()
if __name__ == '__main__':
    input_video_path = r'G:\东A20240703 (1).MP4'  # 输入视频文件路径
    output_video_path = r'G:\cropped_video.mp4'  # 输出视频文件路径
    start_time = 30  # 开始时间，单位秒
    duration = 60  # 持续时间，单位秒
    detect_objects_in_video(r'G:\cropped_video.MP4', r'G:\result.mp4')
    #crop_video(input_video_path, output_video_path, start_time, duration)