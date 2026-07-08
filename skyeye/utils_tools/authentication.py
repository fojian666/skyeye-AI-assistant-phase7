# _*_ coding: utf-8 _*_
# @Time : 2024/9/27 18:04 
# @Author : xxx 
# @Version：V 0.1
# @File : authentication.py
# @desc :
# authentication.py
import jwt
from system.models import User
from rest_framework import exceptions
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.settings import api_settings


jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class JsonAuthentication(JSONWebTokenAuthentication):

    def authenticate_credentials(self, payload):
        username = payload['username']
        if not username:
            msg = 'Invalid payload.'
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get(username=username)
        except Exception:
            msg = 'Invalid signature.'
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = 'User account is disabled.'
            raise exceptions.AuthenticationFailed(msg)
        return user

    def authenticate(self, request):

        # 若前端无token则获取切割后的列表索引1会报索引错误，则用try包围
        try:
            jwt_value = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        except IndexError:
            jwt_value = None

        # # 验证签名，验证是否过期
        try:
            payload = jwt_decode_handler(jwt_value)  # 得到载荷
            # 取当前用户，拿到user对象，每登录一个人就要去数据库查一次
            # 这个也要重写，因为它找的是auth的user表，我们是去自己表中查
            user = self.authenticate_credentials(payload)
        except jwt.ExpiredSignature:
            msg = 'token过期'
            raise exceptions.AuthenticationFailed(msg)
        except jwt.DecodeError:
            msg = '签名错误'
            raise exceptions.AuthenticationFailed(msg)
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('错误')

        return (user, jwt_value)

