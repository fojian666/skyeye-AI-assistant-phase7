# your_app/middleware.py

import os
from django.http import HttpResponseForbidden
from django.conf import settings
# 这里导入你已有的 RSA 验证函数
from utils_tools import verify_license

# 你的授权文件路径（根目录）
LICENSE_FILE = os.path.join(settings.BASE_DIR, "license.lic")
print(LICENSE_FILE)

class LicenseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. 检查文件是否存在
        if not os.path.exists(LICENSE_FILE):
            return HttpResponseForbidden("授权文件不存在")

        # 2. 读取 license
        try:
            with open(LICENSE_FILE, 'r', encoding='utf-8') as f:
                license_str = f.read().strip()
        except Exception as e:
            return HttpResponseForbidden("授权文件读取失败")

        # 3. 调用你现有的 RSA 验证
        valid, msg = verify_license.verify_license(license_str)
        if not valid:
            return HttpResponseForbidden(f"授权无效：{msg}")

        # 验证通过，继续访问
        response = self.get_response(request)
        return response