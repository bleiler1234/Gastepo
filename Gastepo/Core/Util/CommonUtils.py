# -*- coding: utf-8 -*-
# Author:yuzhonghua

import calendar
import datetime
import json
import os
import random
import re
import socket
import string
import subprocess
import sys
import time
from collections import OrderedDict

import emoji
import xmltodict

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Base.CustomException import SystemOSTypeError
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


def random_str(length):
    """
    生成指定长度的随机字符串.
    :param length: 指定长度.
    :return:
    """
    str_list = random.sample(string.digits + string.ascii_letters, length)
    random_str = ''.join(str_list).lower()
    return random_str


def calc_round(n, m=0):
    """
    四舍五入精度
    :param n: 浮点数
    :param m: 进位数
    :return:
    """
    if m == 0:
        return int(n + 0.5)
    temp_list = str(n).split('.')
    if temp_list.__len__() != 1:
        temp = temp_list[1][:m]
        n = str(int(n * 10 ** m + 0.5))
        n = n.rjust(temp.__len__(), '0')
    else:
        n = str(int(n * 10 ** m + 0.5))
    m *= -1
    n = '{}.{}'.format(n[:m], n[m:])
    return float(n)


def time_spent(func):
    """
    运行耗时装饰器.
    :return:
    """

    def wrapper(*args, **kw):
        start_time = time.time()
        result = func(*args, **kw)
        logger.info('被装饰方法{}总共运行耗时{}秒.'.format(func.__name__, round(time.time() - start_time, 2)))
        return result

    return wrapper


def trans_timestamp(timeNum):
    """
    13位时间戳转换为指定时间格式.
    :param timeNum: 13 format timestamp string, such as 1573120029224
    :return: output such as 2019-11-07 17:47:09
    """
    timeStamp = float(timeNum / 1000)
    timeArray = time.localtime(timeStamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime


def date_timedelta(date_str):
    """
    获取指定日期的星期、季度、月份、年份分布
    :param date_str: 字符串格式 '2020-08-21'
    :return:
    """
    result = {}
    struct_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    # 获取当前月第一天和最后一天
    _, monthRange = calendar.monthrange(struct_date.year, struct_date.month)
    firstDay_month = datetime.date(year=struct_date.year, month=struct_date.month, day=1).strftime("%Y-%m-%d")
    lastDay_month = datetime.date(year=struct_date.year, month=struct_date.month, day=monthRange).strftime("%Y-%m-%d")

    # 获取当前年份第一天和最后一天
    _, last_month_of_days = calendar.monthrange(struct_date.year, 12)
    first_day_year = datetime.date(year=struct_date.year, month=1, day=1).strftime("%Y-%m-%d")
    last_day_year = datetime.date(year=struct_date.year, month=12, day=last_month_of_days).strftime("%Y-%m-%d")

    # 获取当前周第一天和最后一天
    this_week_start = (struct_date - datetime.timedelta(days=struct_date.weekday())).strftime("%Y-%m-%d")
    this_week_end = (struct_date + datetime.timedelta(days=6 - struct_date.weekday())).strftime("%Y-%m-%d")

    # 获取本季度第一天和最后一天
    month = struct_date.month
    if month in [1, 2, 3]:
        this_quarter_start = datetime.date(struct_date.year, 1, 1).strftime("%Y-%m-%d")
        this_quarter_end = (datetime.date(struct_date.year, 4, 1) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif month in [4, 5, 6]:
        this_quarter_start = datetime.date(struct_date.year, 4, 1).strftime("%Y-%m-%d")
        this_quarter_end = (datetime.date(struct_date.year, 7, 1) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif month in [7, 8, 9]:
        this_quarter_start = datetime.date(struct_date.year, 7, 1).strftime("%Y-%m-%d")
        this_quarter_end = (datetime.date(struct_date.year, 10, 1) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        this_quarter_start = datetime.date(struct_date.year, 10, 1).strftime("%Y-%m-%d")
        this_quarter_end = (datetime.date(struct_date.year + 1, 1, 1) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    result.update({
        'year': {'first_day': first_day_year, 'last_day': last_day_year},
        'month': {'first_day': firstDay_month, 'last_day': lastDay_month},
        'quarter': {'first_day': this_quarter_start, 'last_day': this_quarter_end},
        'week': {'first_day': this_week_start, 'last_day': this_week_end}, })
    return result


def execute_command(command):
    """
    执行终端命令.
    :param command: 字符串形式命令(根据系统识别命令方式)
    :return:
    """
    if os.name == 'posix':
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    elif os.name == 'nt':
        windows_command = ['cmd', '/c']
        command_detail_list = re.split(r"[ ]+", command)
        windows_command.extend(command_detail_list)
        subprocess.run(windows_command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    else:
        raise SystemOSTypeError


def unicode_to_normal(origin_str):
    """
    将中文unicode字符(如"\u6d4b")转换为正常中文
    :param origin_str: 中文unicode字符
    :return:
    """
    result_str = str(origin_str).encode("utf-8").decode("unicode-escape")
    return result_str


def param_to_dict(request_param):
    """
    转换请求参数为dict形式, 如a=1&b=2转换为{"a":1, "b":2}
    :param request_param: 请求参数
    :return: dict
    """
    param_zip_list = [tuple([i.strip() for i in re.split(r"[=]+", param.strip())]) for param in
                      re.split(r"[&]+", request_param)]
    param_dict = dict(param_zip_list)
    return param_dict


def xml_to_json(xml_str):
    """
    XML字符串转换为JSON字符串
    :param xml_str: XML字符串
    :return:
    """
    xml_str = re.split(pattern=r'<\?[\s\S]*\?>', string=str(xml_str).strip(), maxsplit=1)[-1]
    xml_parse = xmltodict.parse(xml_str)
    json_str = json.dumps(xml_parse, indent=1)
    return json_str


def json_to_xml(json_dict):
    """
    JSON字典转换为XML字符串
    :param json_dict: json字典
    :return:
    """
    xml_str = xmltodict.unparse(json_dict, pretty=1)
    return xml_str


def emoji_to_str(origin):
    """
    将Emoji表情转换为字符窜
    :param origin:
    :return:
    """
    if isinstance(origin, str):
        return emoji.demojize(origin)
    elif isinstance(origin, list):
        return list(map(lambda x: emoji_to_str(x), origin))
    elif isinstance(origin, tuple):
        return tuple(map(lambda x: emoji_to_str(x), origin))
    elif isinstance(origin, set):
        return set(map(lambda x: emoji_to_str(x), origin))
    elif isinstance(origin, dict):
        keys = list(map(lambda x: emoji_to_str(x), list(origin.keys())))
        values = list(map(lambda x: emoji_to_str(x), list(origin.values())))
        return dict(zip(keys, values))
    else:
        return origin


def get_alphabet(number):
    """
    将数字转换为大写字母
    :param number: 大于等于0的整数
    :return: 大写字母，如A或CW等
    """
    factor, moder = divmod(number, 26)
    modChar = chr(moder + 65)
    if factor != 0:
        modChar = get_alphabet(factor - 1) + modChar
    return modChar


def get_ip():
    """
    获取本机IP地址
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def update_run_environment(env="Test"):
    """
    更新environment.properties中环境值
    :param env: 默认STG
    :return:
    """
    from Gastepo.Core.Base.BaseData import RESOURCE_PATH
    ENVIRONMENT_FILE = os.path.join(RESOURCE_PATH, "Allure", "environment.properties")
    with open(ENVIRONMENT_FILE, mode=r'r+', encoding='utf-8') as env_ops:
        env_text = env_ops.read()
        env_str = env_text.split(r"=")[-1]
        env_info = env_text.replace(env_str, str(env).upper())
        env_ops.seek(0)
        env_ops.truncate()
        env_ops.write(env_info)


def get_run_environment():
    """
    获取environment.properties中环境值
    :return:
    """
    from Gastepo.Core.Base.BaseData import RESOURCE_PATH
    ENVIRONMENT_FILE = os.path.join(RESOURCE_PATH, "Allure", "environment.properties")
    with open(ENVIRONMENT_FILE, mode=r'r', encoding='utf-8') as env_ops:
        env_text = env_ops.read()
        env_str = env_text.split(r"=")[-1]
        return env_str


def value_by_type(dest_value, test_value):
    """
    转换测试值为目标值类型的数据
    :param dest_value: 目标值
    :param test_value: 测试值
    :return:
    """
    if isinstance(test_value, type(dest_value)):
        return test_value
    else:
        type_str = str(type(dest_value)).split(r"'")[1]
        test_value = eval(type_str)(test_value)
        return test_value


def func_by_eval(func_expr):
    """
    eval方式解析函数表达式并求值
    :param func_expr: 函数表达式，如"${func(a, b)}"
    :return:
    """
    if re.match(r'^\$\{.*\}$', str(func_expr)):
        expr = func_expr[2:-1]
        return eval(expr)
    else:
        return func_expr


def force_to_json(origin):
    """
    json字串转换为字典
    :param origin: 输入字符串
    :return:
    """
    if re.match(r"(^\{[\s\S]*\}$)|(^\[\{[\s\S]*\}\]$|\[\])", str(origin)):
        return json.loads(emoji.demojize(json.dumps(json.loads(emoji.demojize(str(origin))), ensure_ascii=False)))
    else:
        if isinstance(origin, str):
            origin = emoji.demojize(origin)
        return {"qa": origin}


def sortDict(pyload, reverse=False):
    """
    字典深层递归排序
    :param pyload: 待排序字典
    :param reverse: 排序规则(默认升序)
    :return: 排序后OrderedDict字典
    """
    item = 'p.items()'
    if type(pyload).__name__ == 'list':
        p = sorted(pyload, reverse=reverse)
        item = 'enumerate(p)'
    if type(pyload).__name__ == 'dict':
        p = OrderedDict(sorted(pyload.items(), key=lambda a: a[0], reverse=reverse))
    for k, v in eval(item):
        if type(v).__name__ == 'list':
            if not v or (v is None):
                p.pop(k)
            else:
                p[k] = list(sortDict(sorted(v, reverse=reverse), reverse=reverse))
        elif type(v).__name__ == 'dict':
            if not v or (v is None):
                p.pop(k)
            else:
                p[k] = dict(sortDict(v, reverse=reverse))
            return p
        else:
            if v is None:
                p.pop(k)
    return p


def runner_config():
    """
    自动化测试配置运行筛选器
    :return:
    """
    must_list = ['id', 'scenario', 'platform', 'level', 'group', 'order', 'active']
    runner_config_dict = {}
    check_flag = False
    config_dict = YamlConfig(config=APPLICATION_CONFIG_FILE).get('runner', 2)
    if config_dict is None:
        return dict(id=[], scenario=[], platform=[], level=[], group=[], order=[], active=True)
    else:
        for key, value in config_dict.items():
            if key not in must_list:
                continue
            else:
                check_flag = True
                if key == "id":
                    runner_config_dict["id"] = [i for i in str(value).split(",") if i != ""] if config_dict[
                        "id"] else []
                elif key == "scenario":
                    runner_config_dict["scenario"] = [i for i in str(value).split(",") if i != ""] if config_dict[
                        "scenario"] else []
                elif key == "platform":
                    runner_config_dict["platform"] = [i for i in str(value).split(",") if i != ""] if config_dict[
                        "platform"] else []
                elif key == "level":
                    runner_config_dict["level"] = [i for i in str(value).split(",") if i != ""] if config_dict[
                        "level"] else []
                elif key == "group":
                    runner_config_dict["group"] = [i for i in str(value).split(",") if i != ""] if config_dict[
                        "group"] else []
                elif key == "order":
                    runner_config_dict["order"] = [int(i) for i in str(value).split(",") if i != ""] if config_dict[
                        "order"] else []
                elif key == "active":
                    runner_config_dict["active"] = config_dict["active"] if config_dict["active"] is not None else True
                else:
                    pass

        if check_flag is False:
            return dict(id=[], scenario=[], platform=[], level=[], group=[], order=[], active=True)
        if runner_config_dict.__len__() < must_list.__len__():
            less_key = list(set(must_list) - set(list(runner_config_dict.keys())))
            less_value = [[] for i in range(less_key.__len__())]
            less_dict = dict(zip(less_key, less_value))
            if less_dict.__contains__("active"):
                less_dict["active"] = True
            runner_config_dict.update(less_dict)
            return runner_config_dict
        return runner_config_dict


def runner_argv():
    """
    自动化测试参数运行筛选器
    :return:
    """
    argvs = sys.argv
    must_list = ['--id', '--scenario', '--platform', '--level', '--group', '--order', '--active']
    runner_config_dict = {}
    check_flag = False
    if argvs.__len__() == 1:
        return runner_config()
    elif argvs.__len__() > 1:
        for argv in sys.argv[1:]:
            argv_key = str(argv).split(r"=")[0]
            argv_value = str(argv).split(r"=")[1]
            if argv_key not in must_list:
                continue
            else:
                check_flag = True
                if argv_key == "--id":
                    runner_config_dict["id"] = [i.strip() for i in argv_value.split(",") if i != ""]
                elif argv_key == "--scenario":
                    runner_config_dict["scenario"] = [i.strip() for i in argv_value.split(",") if i != ""]
                elif argv_key == "--platform":
                    runner_config_dict["platform"] = [i.strip() for i in argv_value.split(",") if i != ""]
                elif argv_key == "--level":
                    runner_config_dict["level"] = [i.strip() for i in argv_value.split(",") if i != ""]
                elif argv_key == "--group":
                    runner_config_dict["group"] = [i.strip() for i in argv_value.split(",") if i != ""]
                elif argv_key == "--order":
                    runner_config_dict["order"] = [int(i.strip()) for i in argv_value.split(",") if i != ""]
                elif argv_key == "--active":
                    if str(argv_value) in ['0', 'false', 'False', 'FALSE']:
                        argv_value = False
                    elif str(argv_value) in ['1', 'true', 'True', 'TRUE']:
                        argv_value = True
                    else:
                        argv_value = True
                    runner_config_dict["active"] = argv_value
                else:
                    pass
        if check_flag is False:
            return runner_config()
        if runner_config_dict.__len__() < must_list.__len__():
            less_key = list(set([i[2:] for i in must_list]) - set(list(runner_config_dict.keys())))
            less_value = [[] for i in range(less_key.__len__())]
            less_dict = dict(zip(less_key, less_value))
            if less_dict.__contains__("active"):
                less_dict["active"] = True
            runner_config_dict.update(less_dict)
            return runner_config_dict
        return runner_config_dict
    else:
        pass


if __name__ == '__main__':
    pass
