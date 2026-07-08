from pathlib import Path
import os
import sys
import datetime
import configparser
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
# logger_path = os.path.join(BASE_DIR,'logs')

SECRET_KEY = 'django-insecure-7r8#bxz#m^gp&l+r29b5(yrys*in93lp^%zfirczf47x98tawb'

DEBUG = True
# django-celery  配置的部分
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'config.ini'),encoding='utf-8')
config_redis = config['redis']

# Broker配置，使用Redis作为消息中间件
BROKER_URL = config_redis.get('broker_url')
CELERY_BROKER_URL = BROKER_URL

# BACKEND配置，这里使用redis
CELERY_RESULT_BACKEND = config_redis.get('celery_result_backend')

# Broker配置，使用Redis作为消息中间件
CELERY_APP2_BROKER_URL = config_redis.get('celery_app2_broker_url')

# BACKEND配置，这里使用redis
CELERY_APP2_CELERY_RESULT_BACKEND = config_redis.get('celery_app2_celery_result_backend')

# 结果序列化方案
CELERY_RESULT_SERIALIZER = 'json'

# 任务结果过期时间，秒
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24

# 时区配置
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_BROKER_TRANSPORT = 'redis'
# 使用redis作为中间件
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
# 自定义调度类，使用Django的ORM
# 任务结果，使用Django的ORM
CELERY_ACCEPT_CONTENT = ['application/json']
# 设置任务接收的序列化类型
CELERY_TASK_SERIALIZER = 'json'
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'daphne',
    'rest_framework',
    'rest_framework_jwt',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.panorama',
    'apps.model',
    'apps.system',
    'apps.report',
    'apps.resource',
    'apps.interpretation',
    'apps.drone_track',
    'channels',

]

MIDDLEWARE = [
    #'gtus.middleware.LicenseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gtus.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# Channels后端，用redis做通道缓存
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
ASGI_APPLICATION = 'gtus.asgi.application'

WSGI_APPLICATION = 'gtus.wsgi.application'
AUTH_USER_MODEL = 'system.User'  # 替换Django默认用户模型

# 当前的村界数据
SHP_FILE_PATH = os.path.join(BASE_DIR, r'static/shp/ltcj/龙潭村界shp.shp')  # 南京
# SHP_FILE_PATH = os.path.join(BASE_DIR,r'static/shp/jycj/机巢周边村界.shp') # 泰州

# session 设置
# 设置session过期行为和时间：（浏览器关闭即session过期，过期时间设定）
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 七天过期
SESSION_SAVE_EVERY_REQUEST = True  # 每次请求会更新sessions有效期限
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 关闭浏览器，则COOKIE失效
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_NAME = 'gtus_sessionid'  # 自定义会话 Cookie 名称
# SESSION_ENGINE = 'django.contrib.sessions.backends.db'
CORS_ORIGIN_WHITELIST = [
    'http://192.168.60.6:8082',  # 替换为你前端运行的地址和端口
]
config_database = config['database']
# 数据库设置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config_database['database_name'],
        'USER': config_database['database_user'],
        'PASSWORD': config_database['database_password'],
        'HOST': config_database['database_host'],
        'PORT': config_database['database_port'],
        # 添加OPTIONS设置模式
        'OPTIONS': {
            # 指定要使用的schema，多个schema用逗号分隔
            'options': '-c search_path=public'  # 使用默认public schema
            # 如果需要自定义schema，例如使用'my_schema'：
            # 'options': '-c search_path=my_schema'
            # 如果需要多个schema（优先级从左到右）：
            # 'options': '-c search_path=my_schema,public'
        }
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# 设置语言
LANGUAGE_CODE = 'zh-hans'
CORS_ORIGIN_ALLOW_ALL = True  # 允许所有域名跨域(优先选择)
CORS_ALLOW_CREDENTIALS = True  # 允许携带cookie:
# 设置 Access-Control-Allow-Methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
# JWT 配置
JWT_AUTH = {
    # 设置令牌过期时间（默认是 5 分钟，这里改为 2 小时）
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=24),  # 单位可以是 seconds/minutes/hours/days

    # 可选：刷新令牌的过期时间（如果需要支持令牌刷新）
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=7),  # 刷新令牌有效期 1 天

    # 其他可选配置（根据需求添加）
    'JWT_ALGORITHM': 'HS256',  # 加密算法（默认即可）
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',  # 请求头中的前缀（与前端保持一致）
}
CORS_ALLOW_HEADERS = (
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'sessionid',
    'Pragma',
)

# 设置时区
TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_ROOT = os.path.join(BASE_DIR, "static/")

# 航线批处理会在请求体中提交包含上千个地块的 GeoJSON。
# Django 默认仅允许约 2.5 MB，请求体超过该值会在读取 request.body 时失败。
DATA_UPLOAD_MAX_MEMORY_SIZE = 256 * 1024 * 1024  # 256 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB，较大文件自动落临时文件

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EXEPATH = config['other'].get('nona_exe_path')
config_ai_interpretation = config['ai_interpretation']

IP_ADDRESS = config_ai_interpretation.get('ip_address')
SHARED_PATH = config_ai_interpretation.get('share_path')
DATA_PATH = config_ai_interpretation.get('data_path')
LOGGER_PATH = os.path.join(SHARED_PATH,'logs')
