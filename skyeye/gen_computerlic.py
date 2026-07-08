import json
from datetime import timedelta, datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import ast

def gen_key():
    custom_key_str = "spgtmaphppczybs-20240704"
    custom_key_bytes = custom_key_str.encode()
    if len(custom_key_bytes) > 32:
        custom_key_bytes = custom_key_bytes[:32]  # 截断到最长的AES密钥长度
    elif len(custom_key_bytes) < 32:
        custom_key_bytes += b'\0' * (32 - len(custom_key_bytes))  # 填充到最短的AES密钥长度
    cipher = AES.new(custom_key_bytes, AES.MODE_CBC)
    return cipher, custom_key_bytes

def Encryptedstr(jsontry, file_path):
    cipher, custom_key_bytes = gen_key()
    padded_data = pad(jsontry.encode(), AES.block_size)  # 填充到AES块大小
    encrypted_data = cipher.encrypt(padded_data)
    encrypted_hex = encrypted_data.hex()  # 转换为十六进制字符串
    iv = cipher.iv.hex()  # 将IV转换为十六进制字符串

    # 将加密的十六进制字符串和IV写入文件
    with open(file_path, "w") as f:
        f.write(encrypted_hex + '\n' + iv)  # 将加密数据和IV写入文件

def Decryptedstr(file_path):
    with open(file_path, "r") as f:
        encrypted_data_hex = f.readline().strip()  # 读取加密的十六进制字符串
        iv = bytes.fromhex(f.readline().strip())  # 读取IV并转换回字节序列

    encrypted_data = bytes.fromhex(encrypted_data_hex)  # 将十六进制字符串转换回字节序列
    cipher, custom_key_bytes = gen_key()
    cipher_decrypt = AES.new(custom_key_bytes, AES.MODE_CBC, iv)

    decrypted_padded_data = cipher_decrypt.decrypt(encrypted_data)
    decrypted_data = unpad(decrypted_padded_data, AES.block_size).decode()  # 解密并去除填充

    return decrypted_data

# 准备试用数据
trial_data = {
    "product_id": "bsjy01",
    "trial_start": datetime.now().isoformat(),
    "trial_end": (datetime.now() + timedelta(days=150)).isoformat(),
}

license_file_path = "license.lic"
trial_json = json.dumps(trial_data)

# 加密JSON字符串
Encryptedstr(trial_json, license_file_path)

# 解密数据
# decrypted_data = Decryptedstr(license_file_path)
#
# # 将解密后的数据（JSON字符串）转换回字典
# decrypted_trial_data = json.loads(decrypted_data)
# if  decrypted_trial_data['trial_end'] <= datetime.now().isoformat():
#     print("试用许可过期")