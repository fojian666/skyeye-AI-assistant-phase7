from __future__ import absolute_import, unicode_literals
import os
from kombu import Queue
from kombu import Exchange
from celery import Celery, platforms
from django.utils.datetime_safe import datetime
from django.conf import settings
# 获取当前文件夹名，即为该 Django 的项目名

# 设置默认celery命令行的环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtus.settings')


# 实例化 Celery,项目名称
celery_app = Celery('gtus')
celery_app.conf.worker_concurrency = 1
# 解决时区问题
celery_app.now = datetime.now

# 使用 django 的 settings 文件配置 celery
celery_app.config_from_object('django.conf:settings', namespace='CELERY_APP2')


# 从所有应用中加载任务模块tasks.py
celery_app.autodiscover_tasks(settings.INSTALLED_APPS)

# 解决celery不能root用户启动的问题
platforms.C_FORCE_ROOT = True


task_queues = (
    Queue('priority_low', exchange=Exchange('priority', type='direct'), routing_key='priority_low'),
    Queue('priority_high', exchange=Exchange('priority', type='direct'), routing_key='priority_high'),
)

#celery -A tasks worker -l info -P eventlet