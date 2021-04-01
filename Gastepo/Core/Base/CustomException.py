# -*- coding: utf-8 -*-

class SheetTypeError(Exception):
    '''
    EXCEL中无当前指定的Sheet标识类型（Sheet标识仅支持int和str类型）
    '''

    def __init__(self):
        Exception.__init__(self)


class ConfigTypeError(Exception):
    '''
    配置类工厂无法生产当前配置文件类型的配置类
    '''

    def __init__(self):
        Exception.__init__(self)


class DotTypeError(Exception):
    '''
    非法文件扩展名异常
    '''

    def __init__(self):
        Exception.__init__(self)


class SystemOSTypeError(Exception):
    '''
    非法或不支持的操作系统OS
    '''

    def __init__(self):
        Exception.__init__(self)


class DatabaseTypeError(Exception):
    '''
    非法或不支持的数据库类型
    '''

    def __init__(self):
        Exception.__init__(self)


class InvalidConsumesError(Exception):
    '''
    非法或不支持的请求头类型
    '''

    def __init__(self):
        Exception.__init__(self)


class EnvironmentTypeError(Exception):
    '''
    非法或不支持的测试环境
    '''

    def __init__(self):
        Exception.__init__(self)


class FlakyTestCaseError(Exception):
    '''
    弱势或不稳定的测试用例
    '''

    def __init__(self, msg):
        Exception.__init__(self, msg)
