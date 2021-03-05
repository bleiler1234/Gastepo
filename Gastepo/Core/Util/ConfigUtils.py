# -*- coding: utf-8 -*-
# Author:yuzhonghua

import os
from configparser import RawConfigParser

import yaml


class _YamlReader(object):
    '''
    YAML读取模块
    '''

    def __init__(self, yaml):
        '''
        获取yaml文件
        :param yaml:配置文件
        '''
        if os.path.exists(yaml):
            self.yaml = yaml
        else:
            raise FileNotFoundError('此路径下未发现该YAML配置文件！~ {}'.format(yaml))
        self._data = None

    @property
    def data(self):
        '''
        加载所有yaml配置文件并返回数据
        :return: _data
        '''
        if not self._data:
            with open(self.yaml, 'rb') as f:
                self._data = list(yaml.safe_load_all(f))
        return self._data


class YamlConfig(object):
    '''
    YAML文件配置类
    '''

    def __init__(self, config):
        '''
        获取yaml配置文件信息
        '''
        self.config = _YamlReader(config).data

    def get(self, element, index=0):
        '''
        返回yaml内指定的element
        :param element: 指定element
        :param index: ---模块
        :return: 返回指定element
        '''
        return self.config[index].get(element)


class IniConfig(object):
    '''
    INI文件配置类
    '''

    def __init__(self, config):
        '''
        初始化并载入ini配置文件
        :param config:
        '''
        if os.path.exists(config):
            self.config = RawConfigParser()
            self.config.read(config)
        else:
            raise FileNotFoundError('此路径下未发现该INI配置文件! ~ {}'.format(config))

    def get(self, section, option):
        '''
        获取ini文件内配置信息
        :param section:
        :param option:
        :return: 返回ini配置信息
        '''

        return self.config.get(section, option)


if __name__ == '__main__':
    from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE

    print(YamlConfig(config=APPLICATION_CONFIG_FILE).get("mysql", 1).get("stg").get("host"))
