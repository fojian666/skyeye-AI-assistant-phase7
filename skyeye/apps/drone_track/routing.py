# -*- coding: utf-8 -*-
"""
@Project :gtus
@File    :routing.py
@Author  :yhj
@Date    :2026/6/16 15:05
@Desc    :
"""
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/drone/track/", consumers.DroneTrackConsumer.as_asgi()),
]