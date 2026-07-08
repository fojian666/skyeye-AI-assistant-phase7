# -*- coding: utf-8 -*-
"""
@Project :gtus
@File    :call_big_model.py
@Author  :yhj
@Date    :2026/6/11 16:42
@Desc    :
"""
import base64
import configparser
import json
import os.path
from django.conf import settings
import requests

QUESTIONS = {
    "1": (
        "请仔细分析该全景图，从临时用地恢复（占用耕地）的角度进行判读，给我30字左右描述：临时用地恢复情况如何？土地是否已经复垦？耕地的耕作层是否已经恢复？\n"
    ),
    "2": (
        "请仔细分析该全景图，从山水工程项目（山水林田湖草沙一体化保护和修复）的角度进行判读：，给我30字左右描述：是否满足2026年度完工要求。\n"
    ),
    "3": (
        "请仔细分析该全景图，从建设项目监管的角度进行判读，给我30字左右描述：项目是否已经开工？当前处于哪个建设阶段？（选项：未开工 / 出地面 / 封顶 ），整体评估：请给出该建设项目的综合判断。"
    ),
}


def analyze_by_cate(image_path: str, cate_type: str):
    """按预设类别判读图片"""
    question = QUESTIONS.get(cate_type)
    if question is None:
        raise ValueError(f"未知判读类型: {cate_type}，可选: {list(QUESTIONS.keys())}")
    return call_vl_agent_and_save_desc(image_path, question=question)


def image_to_base64(image_path: str) -> str:
    """本地图片转base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def call_vl_agent_and_save_desc(image_path, question=None):
    """
    1. 根据image_id查询全景图记录
    2. 读取image_path调用多模态智能体
    3. 流式接收所有返回文本拼接完整结果
    4. 更新当前记录desc字段保存判读内容

    :param image_path: 图片路径
    :param question: 自定义提问内容，不传则使用默认问题
    """
    # 默认问题
    if question is None:
        question = "当前全景图中施工工地的进展如何（土地开工，出地面，封顶三者中的哪种）?"

    if not os.path.exists(image_path):
        print("图片路径为空，无法调用识别")
        return '-'

    # 2. 图片转base64
    try:
        base64_img = image_to_base64(image_path)
    except Exception as e:
        print(f"读取图片失败：{str(e)}")
        return None
    config = configparser.ConfigParser()
    # 假设config.ini位于脚本同级目录下
    config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
    other_config = config['other']
    url = other_config['agent_url']
    # 3. 组装智能体请求参数
    headers = {
        "Authorization": "Bearer sk-2baf53ed-e50a-4815-5dae-81e789321d43",
        "Content-Type": "application/json"
    }
    req_data = {
        "model": "qwen35-27b",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_img}"
                        }
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ],
        "stream": True,
        "temperature": 0.1,
        "top_p": 0.01,
        "stop": []
    }

    full_text = []
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(req_data), stream=True, timeout=120)
        if resp.status_code != 200:
            print(f"智能体接口异常，状态码：{resp.status_code}")
            return None

        # 流式逐行解析
        for line in resp.iter_lines():
            if not line:
                continue
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data: "):
                if decoded_line == "data: [DONE]":
                    break
                json_chunk = decoded_line[6:]
                try:
                    chunk_data = json.loads(json_chunk)
                    choices = chunk_data.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_text.append(content)
                except json.JSONDecodeError:
                    continue

    except Exception as e:
        print(f"调用智能体接口异常：{str(e)}")
        return '暂无分析结果'

    # 拼接完整回答文本
    complete_desc = "".join(full_text)
    print("完整判读结果：\n", complete_desc)
    return complete_desc
