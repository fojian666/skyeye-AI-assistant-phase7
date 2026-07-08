# -*- coding: utf-8 -*-
"""
@Project :gtus
@File    :mqtt_drone_sub.py
@Author  :yhj
@Date    :2026/6/16 15:07
@Desc    :
"""

import paho.mqtt.client as mqtt
import json
import redis
import time

# ================= MQTT配置 =================
MQTT_HOST = "2.20.41.1"
MQTT_PORT = 8088
MQTT_USER = "wxzgj"
MQTT_PWD = "wxzgj123"
SUB_TOPIC = "/openapi/362711/1581F8HGX253U00A0645/push"
MQTT_RECONNECT_DELAY = 5  # 连接失败后重试间隔（秒）

# ================= Redis 通道配置（和channels共用） =================
redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0)
CHANNEL_LAYER_CHANNEL = "drone_track_group"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT连接成功，订阅轨迹主题")
        client.subscribe(SUB_TOPIC)
    else:
        print(f"MQTT连接失败 rc={rc}，等待重连...")


def on_disconnect(client, userdata, rc):
    if rc == 0:
        print("MQTT已正常断开")
    else:
        print(f"MQTT连接意外断开 rc={rc}，将自动重连...")

def on_message(client, userdata, msg):
    try:
        res = json.loads(msg.payload.decode("utf-8"))
        data = res.get('data', {})
        lon = data.get("longitude")
        lat = data.get("latitude")
        height = data.get("height")
        timestamp = data.get("timestamp")
        wind_speed = data.get("wind_speed")

        # 过滤空坐标，避免脏数据
        if not all([lon, lat]):
            return

        point_info = {
            "lon": lon,
            "lat": lat,
            "height": height,
            "timestamp": timestamp,
            "wind_speed": wind_speed
        }
        print(f"实时点位 : lon={lon}, lat={lat}, alt={height}")

        # 1. 可选：写入数据库保存历史轨迹
        # DroneTrack.objects.create(**point_info)

        # 2. 通过redis向channels组广播，前端websocket接收
        channel_msg = json.dumps({
            "type": "send_drone_point",
            "data": point_info
        })
        redis_client.publish(f"channels.routing.group.{CHANNEL_LAYER_CHANNEL}", channel_msg)

    except Exception as e:
        print("报文解析异常：", e, msg.payload)

def start_mqtt_listener():
    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PWD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    # 断线后指数退避重连：1s ~ 60s
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=60)

    connected_once = False
    while True:
        try:
            if not connected_once:
                print(f"正在连接 MQTT {MQTT_HOST}:{MQTT_PORT} ...")
                mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
                connected_once = True
            else:
                print(f"正在重新连接 MQTT {MQTT_HOST}:{MQTT_PORT} ...")
                mqtt_client.reconnect()

            print("MQTT订阅进程启动完成，等待无人机数据...")
            mqtt_client.loop_forever()
        except KeyboardInterrupt:
            print("收到退出信号，停止监听")
            try:
                mqtt_client.disconnect()
            except Exception:
                pass
            break
        except Exception as e:
            connected_once = False
            print(f"MQTT连接异常: {e}，{MQTT_RECONNECT_DELAY}秒后重试...")
            time.sleep(MQTT_RECONNECT_DELAY)


if __name__ == "__main__":
    start_mqtt_listener()