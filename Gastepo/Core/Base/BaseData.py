# -*- coding: utf-8 -*-

import os
from enum import Enum, unique

# ------------ 项目本地路径 -----------
BASE_PATH = os.path.split(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))[0]

# ------------ 配置文件路径 -----------
CONFIG_PATH = os.path.join(BASE_PATH, 'Config')
APPLICATION_CONFIG_FILE = os.path.join(BASE_PATH, 'Config', 'ApplicationConfig.yml')
ENVIRONMENT_CONFIG_FILE = os.path.join(BASE_PATH, 'Config', 'EnvironmentConfig.yml')

# ------------ 资源文件路径 -----------
RESOURCE_PATH = os.path.join(BASE_PATH, 'Resource')

# ------------ 在线服务路径 -----------
SERVER_PATH = os.path.join(BASE_PATH, 'Core', "Server")

# ------------ 测试用例路径 -----------
TESTCASE_PATH = os.path.join(BASE_PATH, 'TestSuite', 'TestCase')

# ------------ 单元测试路径 -----------
QA_PATH = os.path.join(BASE_PATH, 'QA')

# ------------ 运行输出路径 -----------
OUTPUT_PATH = os.path.join(BASE_PATH, 'Output')

# ------------ 测试结果路径 -----------
RESULT_PATH = os.path.join(OUTPUT_PATH, "Result")

# ------------ 测试报告路径 -----------
REPORT_PATH = os.path.join(OUTPUT_PATH, "Report")

# ------------ 接口录制路径 -----------
RECORD_PATH = os.path.join(OUTPUT_PATH, "Record")

# ------------ 框架日志路径 -----------
LOG_PATH = os.path.join(OUTPUT_PATH, 'Log')


@unique
class TESTCASE_TITLE_ORDER_ENUM(Enum):
    """
    测试用例标题序号枚举类.
    """
    ID = 0
    AID = 1
    Project = 2
    Scenario = 3
    Title = 4
    BaseUrl = 5
    UrlPath = 6
    Method = 7
    Consumes = 8
    Platform = 9
    Level = 10
    Active = 11
    Group = 12
    Order = 13
    RequestPath = 14
    RequestHeader = 15
    RequestParam = 16
    RequestData = 17
    RequestFile = 18
    DependencyInfo = 19
    AssertInfo = 20
    ActualResponse = 21
    TestDescription = 22
    TestResult = 23
    UpdateTime = 24


@unique
class MATCHER_TYPE(Enum):
    """
    当前支持的常用Hamcrest断言器枚举类.
    """
    HAS_ENTRY = {"type": "has_entry", "description": "字典是否包含某个键值对"}
    HAS_ENTRIES = {"type": "has_entries", "description": "字典是否包含某些键值对"}
    HAS_KEY = {"type": "has_key", "description": "字典是否包含指定键"}
    HAS_VALUE = {"type": "has_value", "description": "字典是否包含指定值"}
    IS_IN = {"type": "is_in", "description": "是否存在于指定序列中"}
    EMPTY = {"type": "empty", "description": "断言项是否为空(不用入参)"}
    HAS_ITEM = {"type": "has_item", "description": "序列是否包含某个值"}
    HAS_ITEMS = {"type": "has_items", "description": "序列是否包含某些值"}
    CONTAINS_INANYORDER = {"type": "contains_inanyorder", "description": "完全匹配指定序列且忽略元素顺序(赋值元素)"}
    INANYORDER_CONTAINS = {"type": "inanyorder_contains", "description": "完全匹配指定序列且忽略元素顺序(赋值序列)"}
    CONTAINS = {"type": "contains", "description": "请使用contains_exactly"}
    CONTAINS_EXACTLY = {"type": "contains_exactly", "description": "完全匹配指定序列且顺序一致(赋值元素)"}
    EXACTLY_CONTAINS = {"type": "exactly_contains", "description": "完全匹配指定序列且顺序一致(赋值序列)"}
    IS_CONTAINS = {"type": "is_contains", "description": "全序列是否包含子序列"}
    CONTAINS_IN = {"type": "contains_in", "description": "子序列是否存在于全序列中"}
    ONLY_CONTAINS = {"type": "only_contains", "description": "必须至少包含待断言序列中所有元素(赋值元素)"}
    CONTAINS_ONLY = {"type": "contains_only", "description": "必须至少包含待断言序列中所有元素(赋值序列)"}
    NOT_CONTAINS = {"type": "not_contains", "description": "全序列应不包含指定的子序列"}
    MATCH_EQUALITY = {"type": "match_equality", "description": "这是什么鬼？"}
    MATCHES_REGEXP = {"type": "matches_regexp", "description": "正则匹配"}
    CLOSE_TO = {"type": "close_to", "description": "测试浮点值接近给定的值"}
    GREATER_THAN = {"type": "greater_than", "description": "大于"}
    GREATER_THAN_OR_EQUAL_TO = {"type": "greater_than_or_equal_to", "description": "大于等于"}
    LESS_THAN = {"type": "less_than", "description": "小于"}
    LESS_THAN_OR_EQUAL_TO = {"type": "less_than_or_equal_to", "description": "小于等于"}
    HAS_LENGTH = {"type": "has_length", "description": "检查指定长度数值是否等同于待断言项长度"}
    HAS_PROPERTY = {"type": "has_property", "description": "对象是否存在某个属性"}
    HAS_PROPERTIES = {"type": "has_properties", "description": "对象是否存在某些属性"}
    HAS_STRING = {"type": "has_string", "description": "字符串是否完全一致"}
    EQUAL_TO_IGNORING_CASE = {"type": "equal_to_ignoring_case", "description": "字符串是否相同(忽略大小写)"}
    EQUAL_TO_IGNORING_WHITESPACE = {"type": "equal_to_ignoring_whitespace", "description": "字符串是否相同(忽略左右空格)"}
    CONTAINS_STRING = {"type": "contains_string", "description": "是否包含指定子字符串"}
    ENDS_WITH = {"type": "ends_with", "description": "必须以指定子字符串结尾"}
    STARTS_WITH = {"type": "starts_with", "description": "必须以指定子字符串开始"}
    STRING_CONTAINS_IN_ORDER = {"type": "string_contains_in_order", "description": "是否包含子字符串(忽略字符顺序)"}
    ALL_OF = {"type": "all_of", "description": "断言子项均需全部匹配成功"}
    ANY_OF = {"type": "any_of", "description": "断言子项之一匹配成功即可"}
    IS_ = {"type": "is_", "description": "语法糖"}
    IS_NOT = {"type": "is_not", "description": "断言取反"}
    EQUAL_TO = {"type": "equal_to", "description": "数值相等断言"}
    INSTANCE_OF = {"type": "instance_of", "description": "断言数据类型"}
