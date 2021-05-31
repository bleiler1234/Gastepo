# -*- coding: utf-8 -*-

import datetime
import random
import re
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, unique
from urllib.parse import urlencode, quote, unquote

from Gastepo.Core.Util.CommonUtils import calc_round


class STATIC_VARIABLE(object):
    """
    静态变量类
    """
    increment_value = 1
    bookmark_dict = {}


@unique
class FUNCTION_ENUM(Enum):
    """
    扩展方法枚举类
    """
    DICT = {"name": "dict", "role": "系统", "description": "字典", "example": "dict(a=1,b=2)"}
    LIST = {"name": "list", "role": "系统", "description": "列表", "example": "list([1,2])"}
    TUPLE = {"name": "tuple", "role": "系统", "description": "元组", "example": "tuple([1,2])"}
    SET = {"name": "set", "role": "系统", "description": "集合", "example": "set([1,2])"}
    LEN = {"name": "len", "role": "系统", "description": "求长度", "example": "len([1,2,3])"}
    MAX = {"name": "max", "role": "系统", "description": "求最大值", "example": "max([1,2,3])"}
    MIN = {"name": "min", "role": "系统", "description": "求最小值", "example": "min([1,2,3])"}
    SUM = {"name": "sum", "role": "系统", "description": "累加求和", "example": "sum([1,2,3])"}
    AVG = {"name": "avg", "role": "系统", "description": "求平均数并支持四舍五入", "example": "avg([1,2,3],2)"}
    POW = {"name": "pow", "role": "系统", "description": "求x的y次幂", "example": "pow(2,3)"}
    ROUND = {"name": "round", "role": "系统", "description": "四舍六入五成双", "example": "round(3.42500,2)"}
    EVAL = {"name": "eval", "role": "系统", "description": "字符串表达式运算", "example": 'eval("2+3")'}
    INT = {"name": "int", "role": "系统", "description": "转换为整数", "example": 'int(2.4)'}
    FLOAT = {"name": "float", "role": "系统", "description": "转换为浮点数", "example": 'float(2)'}
    STR = {"name": "str", "role": "系统", "description": "转换为字符串", "example": 'str(1.4)'}
    REPR = {"name": "repr", "role": "系统", "description": "转换为字符串（解释器模式）", "example": 'repr(1.4)'}
    ORIGIN = {"name": "origin", "role": "框架", "description": "传入什么就返回什么", "example": 'origin("abcde")'}
    SUBSTR = {"name": "substr", "role": "框架", "description": "截取字符串", "example": 'substr("abcde",1,3,1)'}
    COMBINE_STR = {"name": "combine_str", "role": "框架", "description": "合并字符串", "example": 'combine_str("I am ", "yu")'}
    DUPLICATE = {"name": "duplicate", "role": "框架", "description": "集合去重", "example": 'duplicate([1,2,2])'}
    REPLACE = {"name": "replace", "role": "框架", "description": "替换字符串", "example": 'replace("abc","a","d")'}
    FETCH = {"name": "fetch", "role": "框架", "description": "按索引从集合取值", "example": 'fetch([1,2,2],1)'}
    URL_ENCODE = {"name": "url_encode", "role": "框架", "description": "将URL参数进行编码", "example": 'id=1&name=yu'}
    F_QUOTE = {"name": "f_quote", "role": "框架", "description": "将数据进行URLENCODE编码", "example": "%7B%22id%22%3A%201%7D"}
    F_UNQUOTE = {"name": "f_unquote", "role": "框架", "description": "将数据进行URLENCODE解码",
                 "example": "f_unquote('%7B%22id%22%3A%201%7D')"}
    F_MAX = {"name": "f_max", "role": "框架", "description": "求最大值", "example": "f_max(1,2,3)"}
    F_MIN = {"name": "f_min", "role": "框架", "description": "求最小值", "example": "f_min(1,2,3)"}
    S_SUM = {"name": "s_sum", "role": "系统", "description": "累加求和并支持eval", "example": "s_sum(['1','2','3'])"}
    F_SUM = {"name": "f_sum", "role": "框架", "description": "累加求和", "example": "f_sum(1,2,3)"}
    S_AVG = {"name": "s_avg", "role": "系统", "description": "求平均数并支持四舍五入及eval", "example": "s_avg(['1','2','3'],up=2)"}
    F_AVG = {"name": "f_avg", "role": "框架", "description": "求平均数并支持四舍五入", "example": "f_avg(1,2,3,up=2)"}
    LIST_MULTIPLY = {"name": "list_multiply", "role": "框架", "description": "求两个列表间的乘积",
                     "example": "list_multiply([1,2,3],[4,5,6])"}
    F_UUID = {"name": "f_uuid", "role": "框架", "description": "生成uuid随机码", "example": "f_uuid()"}
    NEXT = {"name": "next", "role": "框架", "description": "迭代器", "example": "next(increment)"}
    RANDOM_INT = {"name": "random_int", "role": "框架", "description": "获取随机整数并支持返回字符串形式",
                  "example": "random_int(1,5,True,True)"}
    RANDOM_FLOAT = {"name": "random_float", "role": "框架", "description": "获取随机浮点数并支持四舍五入以及返回字符串形式",
                    "example": "random_float(1,5,True,True,2)"}
    DATE_TIME = {"name": "date_time", "role": "框架", "description": "获取间隔日期时间", "example": "date_time(1,True,0)"}
    SET_BOOKMARK = {"name": "set_bookmark", "role": "框架", "description": "将值存入字典并标记", "example": "set_bookmark('a', 1)"}
    GET_BOOKMARK = {"name": "get_bookmark", "role": "框架", "description": "根据标记从字典取出值", "example": "get_bookmark('a')"}
    SHORT_TIMESTAMP = {"name": "short_timestamp", "role": "框架", "description": "获取当前10位时间戳",
                       "example": "short_timestamp()"}
    LONG_TIMESTAMP = {"name": "long_timestamp", "role": "框架", "description": "获取当前13位时间戳",
                      "example": "long_timestamp()"}
    TO_TIMESTAMP10 = {"name": "to_timestamp10", "role": "框架", "description": "获取指定时间的10位时间戳",
                      "example": "to_timestamp10('2020-12-12 13：34：45')"}
    TO_TIMESTAMP13 = {"name": "to_timestamp13", "role": "框架", "description": "获取指定时间的13位时间戳",
                      "example": "to_timestamp13('2020-12-12 13：34：45')"}
    TIMESTAMP10_TO_NORMAL = {"name": "timestamp10_to_normal", "role": "框架", "description": "10位时间戳转换为指定时间格式",
                             "example": "timestamp10_to_normal(1608011144)"}
    TIMESTAMP_TO_NORMAL = {"name": "timestamp_to_normal", "role": "框架", "description": "13位时间戳转换为指定时间格式",
                           "example": "timestamp_to_normal(1595581242560)"}


def origin(param):
    return param


def replace(string, old, new):
    result = str(string).replace(old, new)
    return result


def duplicate(collect):
    if isinstance(collect, list):
        return list(set(collect))
    else:
        return collect


def fetch(collect, index=None):
    if not isinstance(collect, list):
        return collect
    else:
        if index is None:
            return collect
        else:
            if re.match(r'^-?\d*:-?\d*$', str(index)) is None:
                return collect[eval(str(index))]
            else:
                return eval("collect" + "[" + str(index) + "]")


def url_encode(data):
    temp_dict = {"temp": data}
    encode_expr = urlencode(temp_dict)
    encode_str = encode_expr.split(r'=')[-1]
    return encode_str


def f_quote(string, encoding='utf-8'):
    return quote(string=string, encoding=encoding)


def f_unquote(string, encoding='utf-8'):
    return unquote(string=string, encoding=encoding)


def substr(string, start, end, step=1):
    return str(string)[start:end:step]


def combine_str(*args):
    args = [str(i) for i in args]
    return "".join(args)


def f_max(*args):
    return max(args)


def f_min(*args):
    return min(args)


def s_sum(args):
    args = [eval(str(i)) for i in args]
    return sum(args)


def f_sum(*args):
    return sum(args)


def avg(args, up=None):
    total = sum(args)
    length = args.__len__()
    temp_value = float(
        Decimal(str(total / length)).quantize(Decimal("0.00000000000000000000"), ROUND_HALF_UP))
    if str(temp_value).split(r'.')[-1][-3:] == '999':
        avg_value = temp_value + eval('0.' + '0'.center(len(str(temp_value).split(r'.')[-1]) - 1, '0') + '1')
    else:
        avg_value = temp_value
    return calc_round(avg_value, up) if up is not None else avg_value


def s_avg(args, up=None):
    total = s_sum(args)
    length = args.__len__()
    temp_value = float(
        Decimal(str(total / length)).quantize(Decimal("0.00000000000000000000"), ROUND_HALF_UP))
    if str(temp_value).split(r'.')[-1][-3:] == '999':
        avg_value = temp_value + eval('0.' + '0'.center(len(str(temp_value).split(r'.')[-1]) - 1, '0') + '1')
    else:
        avg_value = temp_value
    return calc_round(avg_value, up) if up is not None else avg_value


def f_avg(*args, up=None):
    total = sum(args)
    length = args.__len__()
    temp_value = float(
        Decimal(str(total / length)).quantize(Decimal("0.00000000000000000000"), ROUND_HALF_UP))
    if str(temp_value).split(r'.')[-1][-3:] == '999':
        avg_value = temp_value + eval('0.' + '0'.center(len(str(temp_value).split(r'.')[-1]) - 1, '0') + '1')
    else:
        avg_value = temp_value
    return calc_round(avg_value, up) if up is not None else avg_value


def list_multiply(a, b):
    if isinstance(a, list) and isinstance(b, list):
        if a.__len__() == b.__len__():
            return list(map(lambda x, y: x * y, a, b))
        else:
            return "all list length must be equal!"
    else:
        return "params must be all list type!"


def f_uuid():
    """
    生成uuid随机码
    :return:
    """
    return uuid.uuid4()


def increment_iter():
    while True:
        yield STATIC_VARIABLE.increment_value
        STATIC_VARIABLE.increment_value = STATIC_VARIABLE.increment_value + 1


increment = increment_iter()


def random_int(min=0, max=9, seed=False, string=False):
    """
    获取随机整数
    :param min: 最小值(默认0)
    :param max: 最大值(默认9)
    :param seed: 随机种子
    :param string: 是否输出字符串形式
    :return:
    """
    if seed is True:
        random.seed()
        value = random.randint(min, max)
        return value if string is False else str(value)
    else:
        value = random.randint(min, max)
        return value if string is False else str(value)


def random_float(min=0, max=9, seed=False, string=False, up=None):
    """
    获取随机浮点数
    :param min: 最小值(默认0)
    :param max: 最大值(默认9)
    :param seed: 随机种子
    :param string: 是否输出字符串形式
    :param up: 四舍五入保留的小数位(默认为None，不保留)
    :return:
    """
    if seed is True:
        random.seed()
        float_value = random.uniform(min, max)
        value = calc_round(float_value, up) if up is not None else float_value
        return value if string is False else str(value)
    else:
        float_value = random.uniform(min, max)
        value = calc_round(float_value, up) if up is not None else float_value
        return value if string is False else str(value)


def short_timestamp():
    """
    获取当前10位时间戳
    :return:
    """
    return int(time.time())


def long_timestamp():
    """
    获取当前13位时间戳
    :return:
    """
    return int(round(time.time() * 1000))


def to_timestamp10(date_str, format_string="%Y-%m-%d %H:%M:%S"):
    """
    时间字符串转换为10位时间戳
    :param date_str:
    :param format_string:
    :return:
    """
    time_array = time.strptime(str(date_str), format_string)
    time_stamp10 = int(time.mktime(time_array))
    return time_stamp10


def to_timestamp13(date_str, format_string="%Y-%m-%d %H:%M:%S"):
    """
    时间字符串转换为13位时间戳
    :param date_str:
    :param format_string:
    :return:
    """
    time_array = time.strptime(str(date_str), format_string)
    time_stamp13 = int(time.mktime(time_array)) * 1000
    return time_stamp13


def timestamp10_to_normal(time_stamp, format_string="%Y-%m-%d %H:%M:%S"):
    """
    10位时间戳转换为指定时间格式.
    :param time_stamp:
    :param format_string:
    :return:
    """
    time_array = time.localtime(time_stamp)
    str_date = time.strftime(format_string, time_array)
    return str_date


def timestamp_to_normal(time_stamp, format_string="%Y-%m-%d %H:%M:%S"):
    """
    13位时间戳转换为指定时间格式.
    :param time_stamp:
    :param format_string:
    :return:
    """
    stamp = float(time_stamp / 1000)
    time_array = time.localtime(stamp)
    str_date = time.strftime(format_string, time_array)
    return str_date


def date_time(today=0, time_flag=True, time_type=None, start_date=None, start_time="hhmmss"):
    """
    获取日期及时间
    :param today: 日期间隔，默认今天
    :param time_flag: 是否显示时间，默认显示
    :param time_type: 时间显示格式标识
    :param start_date: 手动开始日期，格式为"2018-08-21";若设置则会固定时间（一直为00:00:00）
    :param start_time: 手动开始时间，格式为"000000"
    :return:
    """
    if start_date is None:
        start_date_time = datetime.datetime.now()
    else:
        start_date_time = datetime.datetime(*map(int, str(start_date).strip().split(r'-')))
    if time_flag is True:
        if time_type == 0:
            return (start_date_time + datetime.timedelta(days=today)).strftime('%Y/%m/%d %H:%M:%S')
        elif time_type == 1:
            return (start_date_time + datetime.timedelta(days=today)).strftime('%Y%m%d%H%M%S')
        elif time_type == 2:
            return str((start_date_time + datetime.timedelta(days=today)).strftime('%Y%m%d')) + "000000"
        elif time_type == 3:
            return str((start_date_time + datetime.timedelta(days=today)).strftime('%Y%m%d')) + "235959"
        elif time_type == 4:
            return str((start_date_time + datetime.timedelta(days=today)).strftime('%Y%m%d')) + str(start_time)
        elif time_type == 5:
            return str((start_date_time + datetime.timedelta(days=today)).strftime('%Y/%m/%d')) + str(start_time)
        elif time_type == 6:
            return str((start_date_time + datetime.timedelta(days=today)).strftime('%Y-%m-%d')) + str(start_time)
        else:
            return (start_date_time + datetime.timedelta(days=today)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        if time_type == 0:
            return (start_date_time + datetime.timedelta(days=today)).strftime('%Y/%m/%d')
        elif time_type == 1:
            return (start_date_time + datetime.timedelta(days=today)).strftime('%Y%m%d')
        else:
            return (start_date_time + datetime.timedelta(days=today)).strftime('%Y-%m-%d')


def set_bookmark(flag, value):
    STATIC_VARIABLE.bookmark_dict.update({str(flag): value})
    return STATIC_VARIABLE.bookmark_dict.get(str(flag))


def get_bookmark(flag):
    return STATIC_VARIABLE.bookmark_dict.get(str(flag))


if __name__ == '__main__':
    a = [
        "5.43",
        "9.87",
        "5.43",
        "5.43",
        "9.87",
        "5.43",
        "5.43",
        "9.87",
        "5.43",
        "8.76"
    ]
    b = [
        "66.79",
        "66.79",
        "66.79",
        "66.79",
        "66.79",
        "66.78",
        "65.66",
        "65.66",
        "70",
        "65.66",
        "65.66",
        "65.66",
        "70",
        "65.66",
        "70",
        "65.65",
        "65"
    ]
    print(s_avg(a, 2))
    print(s_avg(b, 2))
    print(next(increment))
    print(next(increment))
