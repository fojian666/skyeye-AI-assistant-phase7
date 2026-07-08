from __future__ import absolute_import, unicode_literals
import os
from kombu import Queue
from kombu import Exchange
from celery import Celery, platforms
from django.utils.datetime_safe import datetime
from django.conf import settings
from celery.schedules import crontab
# 获取当前文件夹名，即为该 Django 的项目名

# 设置默认celery命令行的环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtus.settings')


# 实例化 Celery,项目名称
celery_app = Celery('gtus')
celery_app.conf.worker_concurrency = 1
# 解决时区问题
celery_app.now = datetime.now

# 使用 django 的 settings 文件配置 celery
celery_app.config_from_object('django.conf:settings')

# 显式绑定 broker，避免 BROKER_URL 未被 Celery 自动识别
if getattr(settings, 'BROKER_URL', None):
    celery_app.conf.broker_url = settings.BROKER_URL
if getattr(settings, 'CELERY_RESULT_BACKEND', None):
    celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# 从所有应用中加载任务模块tasks.py
celery_app.autodiscover_tasks(settings.INSTALLED_APPS)

# celery -A gtus.celery_config worker -l info
app = celery_app

# 解决celery不能root用户启动的问题
platforms.C_FORCE_ROOT = True


task_queues = (
    Queue('priority_low', exchange=Exchange('priority', type='direct'), routing_key='priority_low'),
    Queue('priority_high', exchange=Exchange('priority', type='direct'), routing_key='priority_high'),
)

# 正确配置 beat_schedule
from datetime import timedelta
celery_app.conf.beat_schedule = {
    'multiply-at-some-time': {
        'task': 'tasks.add',  # 使用完整路径
        'schedule': crontab(minute='*/5'),
        # 'schedule': timedelta(seconds=10),  # 每10秒执行一次
        # 'schedule': crontab(hour=0, minute=0),  # 每天早上 0 点 0 分执行一次
    }
}

# 正确配置任务路由
celery_app.conf.task_routes = {
    'gtus.celery_config.add': {'queue': 'priority_low'},
    'tasks.multiply': {'queue': 'priority_high'},
}



