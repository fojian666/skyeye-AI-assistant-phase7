# -*- coding: UTF-8 -*-
import re, json, os
import uuid
from binascii import a2b_hex
from binascii import b2a_hex
import psutil
from datetime import timedelta, datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class Get_license_file(object):
    def __init__(self, mac, date):
        self.mac = mac
        self.date = date
        # self.licensepath = licensepath

    def encrypt(self, content):
        # content length must be a multiple of 16.
        while len(content) % 16:
            content += ' '
        content = content.encode('utf-8')
        # Encrypt content.
        aes = AES.new(b'2021052020210520', AES.MODE_CBC, b'2021052020210520')
        encrypted_content = aes.encrypt(content)
        return (b2a_hex(encrypted_content))

    def gen_license_file(self):
        # license_file = self.licensepath
        sign = self.encrypt('%s#%s' % (self.mac, self.date))
        return self.mac, self.date, str(sign.decode('utf-8'))
        # with open(license_file, 'w') as LF:
        #     LF.write('MAC : %s\n' % (self.mac))
        #     LF.write('Date : %s\n' % (self.date))
        #     sign = self.encrypt('%s#%s' % (self.mac, self.date))
        #     LF.write('Sign : ' + str(sign.decode('utf-8')) + '\n')


class Check_license_file(object):

    def license_check(self, sign, mac, registerdate, interval):
        # license_dic = self.parse_license_file(path)
        sign = self.decrypt(sign)
        sign_list = sign.split('#')
        real_mac = sign_list[0].strip()
        real_date = sign_list[1].strip()
        if (real_mac != mac) or (real_date != registerdate):
            print('*警告*: 许可文件被修改!')
            return False, '*警告*: 许可文件被修改!'
        # 检查MAC和生效日期是否有效.
        if len(sign_list) == 2:
            mac_address = self.get_mac_address()
            if sign_list[0] != mac_address:
                print('*警告*: 无效的主机!')
                return False, '*警告*: 无效的主机!'
            # 当前时间必须在生效日期之前.
            # 将字符串转换为datetime对象
            # 当前日期向前推7天
            interval = interval
            # 如果是今天注册的，那直接七天后是截止期限
            if datetime.now().strftime('%Y%m%d') == sign_list[1].strip():
                return True, "试用许可还有{}天".format(interval)
            else:
                date_format = "%Y%m%d"  # 定义字符串的日期格式
                sign_date = datetime.strptime(sign_list[1].strip(), date_format)
                # 获取7天后的日期
                seven_days_later = sign_date + timedelta(days=interval)
                # 将新的日期格式化回字符串
                new_date_str = seven_days_later.strftime(date_format)
                # 计算两个日期之间的差异
                todaydate = datetime.now().strftime('%Y%m%d')
                if new_date_str < todaydate:
                    print('*警告*: 许可过期了!')
                    return False, '*警告*: 许可过期了!'
                else:
                    # 将字符串转换为datetime对象以便计算
                    today_date_obj = datetime.strptime(todaydate, date_format)
                    # 计算两个日期之间的差异
                    delta = seven_days_later - today_date_obj
                    return True, "试用许可还有{}天".format(delta.days)
        else:
            print('*警告*:许可证文件上的符号设置错误！')
            return False, '*警告*:许可证文件上的符号设置错误！'
            # sys.exit(1)

    def parse_license_file(self, path):
        license_dic = {}
        license_file = path
        with open(license_file, 'r') as LF:
            for line in LF.readlines():
                if re.match('^\s*(\S+)\s*:\s*(\S+)\s*$', line):
                    my_match = re.match('^\s*(\S+)\s*:\s*(\S+)\s*$', line)
                    license_dic[my_match.group(1)] = my_match.group(2)
        return (license_dic)

    def decrypt(self, content):
        aes = AES.new(b'2021052020210520', AES.MODE_CBC, b'2021052020210520')
        decrypted_content = aes.decrypt(a2b_hex(content.encode('utf-8')))
        return (decrypted_content.decode('utf-8'))

    def get_mac_address(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        mac = mac.upper()
        return "-".join([mac[e:e + 2] for e in range(0, 11, 2)])


def get_address():
    # Get all interfaces
    interfaces = psutil.net_if_addrs()
    for interface, addrs in interfaces.items():
        stats = psutil.net_if_stats()[interface]
        if stats.isup:
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    return addr.address
    return None


def registerlicense(username):
    macadress = get_address()
    todaydate = datetime.now().strftime('%Y%m%d')
    mac, date, signtag = Get_license_file(macadress, todaydate).gen_license_file()

    return mac, date, signtag


def checklicense(sign, mac, registerdate, interval, username):
    tag, msg = Check_license_file().license_check(sign, mac, registerdate, interval)
    return tag, msg


def gen_key():
    custom_key_str = "spgtmaphppczybs-20240704"
    custom_key_bytes = custom_key_str.encode()
    if len(custom_key_bytes) > 32:
        custom_key_bytes = custom_key_bytes[:32]  # 截断到最长的AES密钥长度
    elif len(custom_key_bytes) < 32:
        custom_key_bytes += b'\0' * (32 - len(custom_key_bytes))  # 填充到最短的AES密钥长度
    cipher = AES.new(custom_key_bytes, AES.MODE_CBC)
    return cipher, custom_key_bytes


def decryptedfile(file_path):
    with open(file_path, "r") as f:
        encrypted_data_hex = f.readline().strip()  # 读取加密的十六进制字符串
        iv = bytes.fromhex(f.readline().strip())  # 读取IV并转换回字节序列
    encrypted_data = bytes.fromhex(encrypted_data_hex)  # 将十六进制字符串转换回字节序列
    cipher, custom_key_bytes = gen_key()
    cipher_decrypt = AES.new(custom_key_bytes, AES.MODE_CBC, iv)
    decrypted_padded_data = cipher_decrypt.decrypt(encrypted_data)
    decrypted_data = unpad(decrypted_padded_data, AES.block_size).decode()  # 解密并去除填充
    decrypted_trial_data = json.loads(decrypted_data)

    # if  decrypted_trial_data['product_id'] != (os.path.basename(file_path)).split('license.lic')[0]:
    #     return False, "项目名称和许可文件名称检验不一致，禁止访问"
    if decrypted_trial_data['trial_end'] <= datetime.now().isoformat():
        return False, "系统试用许可过期，禁止访问"
    print("仍在许可期内，可继续试用系统{}".format((datetime.fromisoformat(decrypted_trial_data['trial_end']) - datetime.now())))
    return True, "仍在许可期内，可继续试用系统{}".format((datetime.fromisoformat(decrypted_trial_data['trial_end']) - datetime.now()))


if __name__ == '__main__':
    # make license file
    mac = get_address()
    date = datetime.now().strftime('%Y%m%d')
    # Get_license_file(mac, date).gen_license_file()
    # check license file
    # Check_license_file().license_check(r'C:\Users\Administrator\Desktop\asdfLicense')
    # .py文件生成.so文件
    # 'python check_license_file.py build_ext --inplace'
