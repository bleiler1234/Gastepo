# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import TimedRotatingFileHandler

import colorlog

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Base.BaseData import LOG_PATH
from Gastepo.Core.Util.ConfigUtils import YamlConfig


class LogUtils(object):
    '''
    日志记录模块
    '''

    def __init__(self, logger_name='GastepoAutoTest', config=APPLICATION_CONFIG_FILE):
        '''
        通过logging模块配置控制台和间隔文件log
        :param logger_name: 日志名称
        '''
        c = YamlConfig(config=config).get('log')
        self.color = str(c.get("logcolor")).capitalize()
        self.logger = logging.getLogger(logger_name)
        logging.root.setLevel(logging.NOTSET)
        self.log_file_name = c.get('logname') if c and c.get('logname') else 'GastepoAutoTest.log'
        self.when_auto = c.get('when') if c and c.get('when') else 'D'
        self.backup_count = c.get('backup') if c and c.get('backup') else 5
        self.console_output_level = c.get('console_level') if c and c.get('console_level') else 'DEBUG'
        self.file_output_level = c.get('file_level') if c and c.get('file_level') else 'INFO'
        pattern = c.get('pattern') if c and c.get(
            'pattern') else '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
        if self.color == "True":
            LOG_COLORS_CONFIG = {
                'DEBUG': 'white',
                'INFO': 'black',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
            self.formatter = colorlog.ColoredFormatter('%(log_color)s{}'.format(pattern), log_colors=LOG_COLORS_CONFIG)
        else:
            self.formatter = logging.Formatter(pattern)

    def getLogger(self):
        '''
        创建控制台日志和间隔文件日志handler
        :return: 返回一个logger日志对象
        '''
        if not self.logger.handlers:
            if self.color == "True":
                console_handler = colorlog.StreamHandler()
            else:
                console_handler = logging.StreamHandler()
            console_handler.setFormatter(self.formatter)
            console_handler.setLevel(self.console_output_level)
            self.logger.addHandler(console_handler)
            file_handler = TimedRotatingFileHandler(filename=os.path.join(LOG_PATH, self.log_file_name),
                                                    when=self.when_auto,
                                                    interval=1,
                                                    backupCount=self.backup_count,
                                                    delay=True,
                                                    encoding='utf-8'
                                                    )
            file_handler.setFormatter(self.formatter)
            file_handler.setLevel(self.file_output_level)
            self.logger.addHandler(file_handler)
        return self.logger


logger = LogUtils().getLogger()
