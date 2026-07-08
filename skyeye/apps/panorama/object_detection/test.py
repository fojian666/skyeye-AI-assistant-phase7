import argparse
import time
import os
from PIL import Image
from ultralytics import YOLO

work_dir = os.path.dirname(os.path.abspath(__file__))
number_en_name_dict = {
    0: '搅拌车',
    1: '堆砖',
    2: '施工人员',
    3: '在建砖房',
    4: '推土车',
    5: '板房棚房',
    6: '大巴车',
    7: '彩钢瓦',
    8: '水泥管',
    9: '塔吊',
    10: '防尘网',
    11: '围挡',
    12: '起重机',
    13: '物料提升机',
    14: '搅拌机',
    15: '堆土',
    16: '打桩机',
    17: '铁塔',
    18: '钢筋',
    19: '翻土机',
    20: '小轿车',
    21: '脚手架',
    22: '烟雾',
    23: '压路车',
    24: '运输车',
    25: '翻斗车',
    26: '挖掘机',
}

# 需要保留的类别
KEEP_CLASSES = [0,1, 3, 4, 5, 11, 15, 18, 14, 19, 21, 23, 25, 26]


def start_model():
    model_path = os.path.join(work_dir, 'checkpoints', 'UAV_yolov8l_best_14k_1129.pt')
    model = YOLO(model_path)
    return model


def parse_args():
    parser = argparse.ArgumentParser(description='YOLO批量检测并生成VOC XML标注')
    parser.add_argument('--input_dir', default=r'E:\image', type=str, help='输入图片文件夹路径')
    parser.add_argument('--device', default='cuda:0', help='推理设备')
    args = parser.parse_args()
    return args


def create_voc_xml(image_path, boxes, classes, scores, save_xml_path):
    """生成标准VOC格式XML（只保留有效目标）"""
    img = Image.open(image_path)
    width, height = img.size
    filename = os.path.basename(image_path)
    folder_name = os.path.basename(os.path.dirname(image_path))

    xml_content = f"""<annotation>
    <folder>{folder_name}</folder>
    <filename>{filename}</filename>
    <path>{image_path}</path>
    <source>
        <database>Unknown</database>
    </source>
    <size>
        <width>{width}</width>
        <height>{height}</height>
        <depth>3</depth>
    </size>
    <segmented>0</segmented>"""

    # 只保留需要的类别
    valid_objects = []
    for box, cls_id, conf in zip(boxes, classes, scores):
        cls_id = int(cls_id)
        if cls_id not in KEEP_CLASSES:
            continue
        xmin, ymin, xmax, ymax = map(int, box)
        class_name = number_en_name_dict[cls_id]
        obj = f"""
    <object>
        <name>{class_name}</name>
        <pose>Unspecified</pose>
        <truncated>0</truncated>
        <difficult>0</difficult>
        <confidence>{conf:.2f}</confidence>
        <bndbox>
            <xmin>{xmin}</xmin>
            <ymin>{ymin}</ymin>
            <xmax>{xmax}</xmax>
            <ymax>{ymax}</ymax>
        </bndbox>
    </object>"""
        valid_objects.append(obj)

    # 如果没有有效目标，返回空
    if not valid_objects:
        return False

    # 拼接并写入XML
    xml_content += "".join(valid_objects)
    xml_content += "\n</annotation>"

    with open(save_xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    return True


def batch_detect(input_dir, model):
    img_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    img_files = [f for f in os.listdir(input_dir) if f.lower().endswith(img_formats)]

    if not img_files:
        print("文件夹中没有找到图片！")
        return

    print(f"共找到 {len(img_files)} 张图片，开始检测...")
    parent_dir = os.path.dirname(input_dir)
    xml_dir = os.path.join(parent_dir, 'xml')
    os.makedirs(xml_dir, exist_ok=True)

    for idx, img_name in enumerate(img_files):
        img_path = os.path.join(input_dir, img_name)
        print(f"[{idx + 1}/{len(img_files)}] 处理: {img_name}")

        # 推理
        results = model.predict(img_path, verbose=False)
        if len(results) == 0:
            os.remove(img_path)
            print(f"❌ 无检测结果，已删除图片: {img_name}")
            continue

        # 获取检测结果
        boxes = results[0].boxes.xyxy.tolist()
        classes = results[0].boxes.cls.tolist()
        scores = results[0].boxes.conf.tolist()

        # XML 保存路径
        xml_name = os.path.splitext(img_name)[0] + '.xml'
        xml_path = os.path.join(xml_dir, xml_name)
        is_need = False
        for box, cls_id, conf in zip(boxes, classes, scores):
            cls_id = int(cls_id)
            if cls_id in KEEP_CLASSES:
                is_need = True
                continue
        # 生成 XML，同时判断是否有有效目标
        if is_need:
            success = create_voc_xml(img_path, boxes, classes, scores, xml_path)
        else:
            # 没有需要的类别 → 删除图片，不生成XML
            if os.path.exists(img_path):
                os.remove(img_path)
            print(f"❌ 无指定类别目标，已删除图片: {img_name}")

    print("\n🎉 全部处理完成！")


if __name__ == '__main__':
    args = parse_args()
    print("{} 开始启动目标检测模型！".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    model = start_model()
    batch_detect(args.input_dir, model)