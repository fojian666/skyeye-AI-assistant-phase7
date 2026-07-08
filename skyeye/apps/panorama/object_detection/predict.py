import argparse
import time
from io import BytesIO
import os
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO
from flask import Flask, request, jsonify

work_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(work_dir)))
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
app = Flask(__name__)


def start_model():
    model_path = os.path.join(work_dir, 'checkpoints', 'uav_yv11_v20260525_3w_27.pt')
    model = YOLO(model_path)
    return model


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Tensorflow Faster R-CNN demo')
    parser.add_argument('--port', dest='port', type=int, default=8087)
    parser.add_argument('--gpuID', dest='gpuID', type=int, default=0)
    parser.add_argument('--host', dest='host', type=str, default='0.0.0.0')
    parser.add_argument('--device', default='cuda:0', help='Device used for inference')
    args = parser.parse_args()
    return args


@app.route("/detection_web", methods=['post'])
def main():
    global model
    try:
        print('========接收到请求===========')
        response_data = {}
        file_obj = request.files['image']
        filename = request.form.get('filename')
        batch_id = request.form.get('batch_id')
        image_id = request.form.get('image_id')
        file_folder = os.path.join(work_dir, 'static/input_path')
        os.makedirs(file_folder, exist_ok=True)
        file_path = os.path.join(file_folder, filename)
        file_obj.save(file_path)
        results = model.predict(file_path)
        result_dir = os.path.join(work_dir, 'static/resultImg', batch_id, image_id)
        os.makedirs(result_dir, exist_ok=True)
        if len(results) > 0:
            boxes = results[0].boxes
            xyxy = boxes.xyxy.tolist()
            classes = boxes.cls.tolist()
            scores = boxes.conf.tolist()
            result_list = []
            count = 0
            for i in range(len(xyxy)):
                class_id = int(classes[i])
                if class_id not in [2, 6, 7, 8, 9, 17, 18, 20, 23, 24]:
                    save_path = os.path.join(result_dir, filename.split('.')[0] + '_{}.jpg'.format(count))
                    dict_value = {
                        "className": str(number_en_name_dict[class_id]),
                        "score": str(round(scores[i], 2)),
                        "position": [int(i) for i in xyxy[i]],
                        "file_path": f"/static/resultImg/{batch_id}/{image_id}/{filename.split('.')[0]}_{count}.jpg"
                    }
                    result_list.append(dict_value)
                    draw_picture(file_path, dict_value, save_path)
                    count += 1
            response_data['alarms'] = result_list
            response_data['statusCode'] = '200'
            print(result_list)
        return jsonify(response_data)
    except Exception as e:
        print(f"检测报错：{str(e)}")
        return jsonify({'alarms': [], 'statusCode': '500'})


def draw_picture(filePath, dict_value, save_path):
    """
    根据框绘制结果图片
    :param fileName:图片名
    :param response_data:检测结果json
    :return:
    """
    resp = {"result": 0, "alarms": []}
    img = Image.open(filePath)
    draw = ImageDraw.Draw(img)
    position = dict_value["position"]
    china_cls = dict_value["className"]
    draw.rectangle(xy=(position[0], position[1], position[2], position[3]), fill=None,
                   outline=(255, 0, 0), width=3)
    text = china_cls + " " + str(round(float(dict_value["score"]), 2))
    liens = text.split('\n')
    im = Image.new('RGBA', (80, len(liens) * (12 + 4)), (255, 0, 0))
    draw_table = ImageDraw.Draw(im=im)
    draw_table.text(xy=(1, 1), text=text, fill='black',
                    font=ImageFont.truetype(os.path.join(work_dir, 'static/fonts/msyh.ttf'), 12))
    img.paste(im, (position[0], position[1] - 14))
    img_buffer = BytesIO()
    img = img.convert('RGB')
    if filePath.endswith('png') or filePath.endswith('PNG'):
        img.save(img_buffer, format='png')
    else:
        img.save(img_buffer, format='jpeg')
    img = img.convert('RGB')

    img.save(save_path)
    return resp


if __name__ == '__main__':
    args = parse_args()
    host = args.host
    portNum = args.port
    device = args.gpuID
    print("{} 开始启动目标检测模型！".format(time.strftime("%Y-%m-%d %H:%M:%S"), time.localtime()))
    model = start_model()
    app.config['JSON_AS_ASCII'] = False
    app.run(host, port=portNum, debug=True)
