import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import get_user_model

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

User = get_user_model()  # 获取用户模型

class LoginSerializer(serializers.ModelSerializer):
    '''登录序列化器'''

    # 设置自定义的反序列化字段usr，pwd
    username = serializers.CharField(write_only=True)  # 重写 username , 否则会它会认为你想存数据
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # 全局钩子
    def validate(self, attrs):
        # username mobile 都可能是登录账户
        username = attrs.get('username')
        password = attrs.get('password')
        if re.match('^1[0-9]\d{9}$', username):  # 手机号正则
            user = User.objects.filter(mobile=username).first()
        else:  # 用户名登录
            user = User.objects.filter(username=username).first()
        if user and user.check_password(password):  # 如果登录成功,生成token
            payload = jwt_payload_handler(user)  # 通过user拿到payload
            token = jwt_encode_handler(payload)  # 通过payload拿到token
            # 视图类和序列化类之间通过context这个字典来传递数据
            self.context['token'] = token
            self.context['username'] = user.username
            self.context['user_id'] = user.id
            self.context['role']=user.role
            self.context['county']=user.county
            return attrs
        else:
            raise ValidationError("账户或密码错误")
