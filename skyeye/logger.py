# coding=utf-8
'''
    author:yinhaijun
    date:2020-03-13
'''
import os
import logging
import logging.config
import logging.handlers

# 定义日志格式级别
format_dict = {
    1: logging.Formatter("%(message)s"),
    2: logging.Formatter("%(levelname)s - %(message)s"),
    3: logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"),
    4: logging.Formatter("%(asctime)s - %(levelname)s - %(message)s - [%(name)s]"),
    5: logging.Formatter("%(asctime)s - %(levelname)s - %(message)s - [%(name)s:%(lineno)s]")
}
WORK_DIR = os.path.dirname(os.path.abspath(__file__))


class Logger(object):
    def __init__(self, logname, loglevel, logger):
        '''
            指定日志文件路径，日志级别，以及调用文件
            将日志存入到指定的文件中
        '''
        path = os.path.join(WORK_DIR, 'logs')
        filename = os.path.join(path, logname)  # 日志文件名称
        if not os.path.exists(path):
            os.mkdir(path)
        # 创建一个logger
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.DEBUG)
        # 创建一个handler，用于写入日志文件
        fh = logging.FileHandler(filename, 'a+', encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # 定义handler的输出格式
        formatter = format_dict[int(loglevel)]
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # 给logger添加handler
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def getlog(self):
        return self.logger
