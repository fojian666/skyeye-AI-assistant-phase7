# -*- coding: utf-8 -*-
"""
@Project :gtus
@File    :consumers.py
@Author  :yhj
@Date    :2026/6/16 15:06
@Desc    :
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class DroneTrackConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "drone_track_group"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("WebSocket 已连接: %s", self.scope.get("path"))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info("WebSocket 已断开, code=%s", close_code)

    # 接收前端消息（不需要可忽略）
    async def receive(self, text_data):
        pass

    # 接收mqtt发来的点位消息，推送到前端
    async def send_drone_point(self, event):
        point_data = event["data"]
        await self.send(text_data=json.dumps(point_data))