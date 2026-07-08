import json
import base64
import uuid
from datetime import datetime
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
import os

work_dir = os.path.dirname(os.path.abspath(__file__))


def get_current_mac():
    import netifaces
    """获取默认网卡的MAC地址（可根据需求调整）"""
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET]
    interface = default_gateway[1]
    addrs = netifaces.ifaddresses(interface)
    mac = addrs[netifaces.AF_LINK][0]['addr']
    return mac.upper()  # 统一转为大写，便于比较


def get_mac_address():
    """
    获取本机MAC地址（纯Python，无任何第三方依赖）
    不需要netifaces，不需要VC++，打包绝对安全
    """
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[i:i + 2] for i in range(0, 12, 2)]).upper()


def verify_license(serial_string):
    public_key_path = os.path.join(os.path.dirname(work_dir), 'public.pem')
    license_data = json.loads(serial_string)
    info = license_data["info"]
    signature = base64.b64decode(license_data["signature"])

    # 重新计算签名验证
    message = json.dumps(info, separators=(',', ':'), sort_keys=True).encode('utf-8')
    with open(public_key_path, 'rb') as f:
        key = RSA.import_key(f.read())
    h = SHA256.new(message)
    pkcs1_15.new(key).verify(h, signature)

    # 验证日期
    today = datetime.now().date()
    start = datetime.strptime(info["start"], "%Y-%m-%d").date()
    end = datetime.strptime(info["end"], "%Y-%m-%d").date()
    if today < start or today > end:
        return False, f"License period is from {start} to {end}"

    # 验证MAC地址
    current_mac = get_mac_address()
    licensed_mac = info["mac"].upper()  # 统一转为大写比较
    if current_mac != licensed_mac:
        return False, f"MAC mismatch: licensed {licensed_mac}, current {current_mac}"

    return True, info


if __name__ == '__main__':
    json_value = '{"info":{"mac":"40:C2:BA:59:94:C8","region":"南京","start":"2025-01-01","end":"2026-03-03"},"signature":"MR53wyHOp/YkAKHjnK5hf30B9/sQcWDH8YHbGdGm2b+Vk5mpKXXHz8MGRJzGIR78X7+Y0HL1334ZKZSAZJUiXtChfyqWsX0cwKFjOOhQ+ZH5pKJcOUQzURJsuk/NtlQ84LZldojtnULUz+/T+RwUwgINX5x7M/zhWrzt+LR5ib6eM8SB5lSNS90SFBZKhIciPWfpeqm8ZL5fo4BBtkiIKZfAresouKktU+SRqNP/W8zsqIf1f9SbDyM6Q5nXP8fJzdprr1wJ9RcetEQ22B1dBy5AqZgbmdBYDb6WkaKk7Y11DL5OeFqi0186vf+ogiwZu1V4MJwUlllcMGwpd0+a9w=="}'

    result = verify_license(json_value)
    print(result)
