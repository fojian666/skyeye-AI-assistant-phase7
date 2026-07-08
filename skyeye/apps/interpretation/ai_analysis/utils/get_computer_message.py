import socket
import psutil
import os
import time
import json
from py3nvml import py3nvml
import sys

# Get path
file_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Modify running path
sys.path.insert(0, os.path.dirname(file_path))
import ai_config


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip.replace('.', '-')


def get_formatted_size(size):
    """
    获取总量
    Args:
        size: 总内存大小

    Returns:

    """
    # 定义不同单位的换算关系
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f} {units[index]}"


def get_system_info(path):
    """
    获取系统信息
    @param path:txt文件路径
    @return:节点信息字典类型
    """
    system_info = {}
    try:
        while True:
            # 获取IP地址
            # system_info['node_message'] = '主节点'
            ip_address = get_host_ip()
            system_info['ip_address'] = ip_address

            # 获取CPU信息 - using psutil instead of wmi
            cpu_cores = psutil.cpu_count(logical=True)
            system_info['cpu_info'] = f"-核数{cpu_cores}"

            # 获取GPU信息 - using py3nvml instead of GPUtil
            py3nvml.nvmlInit()
            try:
                device_count = py3nvml.nvmlDeviceGetCount()
                if device_count > 0:
                    handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_name = py3nvml.nvmlDeviceGetName(handle)
                    mem_info = py3nvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_memory = mem_info.total // (1024 * 1024)  # Convert to MiB
                    gpu_memory_free = mem_info.free // (1024 * 1024)  # Convert to MiB
                    system_info['gpu_info'] = f"{gpu_name}-{gpu_memory}MiB"
                    system_info['gpu_free_memory'] = f"{gpu_memory_free}MiB"
                else:
                    system_info['gpu_info'] = "无"
                    system_info['gpu_free_memory'] = "0MiB"
            except Exception as e:
                system_info['gpu_info'] = "无"
                system_info['gpu_free_memory'] = "0MiB"

            # 获取内存信息
            memory_info = psutil.virtual_memory()
            total_memory = memory_info.total
            available_memory = memory_info.available
            memory_usage = memory_info.percent
            formatted_total_memory = get_formatted_size(total_memory)
            system_info['total_memory'] = formatted_total_memory
            system_info['available_memory'] = get_formatted_size(available_memory)
            system_info['used_memory'] = f'{memory_usage}%'

            # 获取CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            system_info['used_cpu'] = f'{cpu_usage}%'

            # 获取GPU使用率
            if 'gpu_info' in system_info and system_info['gpu_info'] != "无":
                try:
                    handle = py3nvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_usage = py3nvml.nvmlDeviceGetUtilizationRates(handle).gpu
                except:
                    gpu_usage = 0
            else:
                gpu_usage = 0
            system_info['used_gpu'] = f'{gpu_usage}%'

            json_data = json.dumps(system_info, ensure_ascii=False)
            print(json_data)
            # 将JSON数据写入新的json文件
            with open(os.path.join(path, '{}.json'.format(ip_address.replace('.', '-'))), "w+",
                      encoding='utf-8') as file:
                file.write(json_data)
                # 刷新缓冲区，确保数据被写入文件
                file.flush()
            # 暂停1秒钟
            time.sleep(10)
    except KeyboardInterrupt:
        print("监控结束")
    finally:
        try:
            # 关闭py3nvml
            py3nvml.nvmlShutdown()
        except Exception as e:
            str(e)

        return system_info


# 测试代码
if __name__ == '__main__':
    system_info_path = os.path.join(ai_config.logger_path, 'system_info')
    if not os.path.exists(system_info_path):
        os.mkdir(system_info_path)
    system_info = get_system_info(os.path.join(ai_config.logger_path, 'system_info'))
    print(system_info)