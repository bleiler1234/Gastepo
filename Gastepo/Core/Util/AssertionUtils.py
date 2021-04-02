# -*- coding: utf-8 -*-

import json
import re

from hamcrest import *
from jsonpath import jsonpath

from Base.CustomException import FlakyTestCaseError
from Gastepo.Core.Base.BaseData import MATCHER_TYPE
from Gastepo.Core.Extend.AssertDependencyExtends import *
from Gastepo.Core.Extend.HamcrestCustomExtends import *
from Gastepo.Core.Util.CommonUtils import value_by_type
from Gastepo.Core.Util.LogUtils import logger
from Gastepo.Core.Util.CommonUtils import emoji_to_str


class AssertionTools(object):
    """
    测试结果自动断言操作类
    """

    def __init__(self, test_case_schema, origin_data):
        """
        初始化断言原型数据.
        :param test_case_schema: 测试用例
        :param origin_data: 断言原型数据(dict)
        """
        try:
            if isinstance(test_case_schema, dict) and (isinstance(origin_data, dict) or isinstance(origin_data, list)):
                self.test_case = test_case_schema
                self.origin_data = origin_data
        except Exception:
            logger.exception("测试用例test_case_schema必须用字典方式入参，断言原型origin_data支持字典及列表方式入参！")

    def check_matcher_type(self, matcher_info):
        """
        检测是否支持当前matcher断言器.
        :param matcher_info: matcher断言器
        :return:
        """
        invalid_matchers = []
        matcher_list = re.findall('[^()]+', str(matcher_info))
        for matcher_item in matcher_list:
            find_flag = False
            for matcher_name in MATCHER_TYPE:
                if matcher_item == matcher_name.value.get('type'):
                    find_flag = True
                    break
            if not find_flag:
                invalid_matchers.append(matcher_item)
        return invalid_matchers

    def combine_matcher(self, matcher_expr, params):
        """
        识别并拼接复合matcher断言器，如is_not(has_item).
        :param params: 深度matcher断言器参数
        :return:
        """
        matcher_list = re.findall('[^()]+', str(matcher_expr))
        matchers = matcher_expr.replace(str(matcher_list[-1]), str(matcher_list[-1]) + "(*{args})").format(
            args=params)
        return matchers

    def sample_assert(self, **err_info):
        """
        基础断言检查,仅断言响应码err和响应体errmsg
        :param err_info: 基本响应信息, 如响应码、响应描述等
        :return:
        """
        if err_info == {}:
            logger.warning(
                "[WARNING]：[{}]~[{}]基础断言当前未设置任何检查信息，请首先指定！".format(self.test_case["ID"], self.test_case["Title"]))
            raise FlakyTestCaseError(msg="当前基础断言未设置任何检查信息")
        else:
            logger.info("[Checking]：[{}]~[{}]开启基础断言检查......".format(self.test_case["ID"], self.test_case["Title"]))
            for key, value in err_info.items():
                if self.origin_data.__contains__(str(key)):
                    assert_that(self.origin_data[str(key)], is_(equal_to(value)), "{}不匹配！".format(str(key)))
                else:
                    raise AssertionError('响应报文中未发现关键字"{}"'.format(str(key)))
            logger.info(
                "[End]：[{}]~[{}]基础断言检测合法，断言成功.".format(self.test_case["ID"], self.test_case["Title"]))

    def advance_assert(self, **err_info):
        """
        高级断言检查,支持jsonpath结合hamcrest进行断言
        :param err_info: 基本响应信息, 如响应码、响应描述等
        :return:
        """
        if self.test_case["AssertInfo"] == "":
            logger.warning(
                '[WARNING]：测试用例[{}]~[{}]中未设置任何断言表达式，默认仅启用基础断言！'.format(self.test_case["ID"], self.test_case["Title"]))
            self.sample_assert(**err_info)
        else:
            logger.info("[Checking]：开启高级断言检查......")
            for assert_dict in json.loads(self.test_case["AssertInfo"]):
                match_result = jsonpath(self.origin_data, assert_dict.get("actual"))
                if match_result is False:
                    logger.warning('[WARNING]：jsonpath表达式"{}"当前未匹配到任何合法字串，请检查jsonpath表达式或断言原型数据是否存在问题！'.format(
                        assert_dict.get("actual")))
                expect_vars = assert_dict.get("expect")
                if not isinstance(expect_vars, list):
                    logger.warning(
                        '[WARNING]：断言信息中expect期望值表达式"{}"必须以列表方式指定, 请检查并修改！'.format(assert_dict.get("expect")))
                if expect_vars == []:
                    expect_vars = [""]
                invalid_matchers = self.check_matcher_type(matcher_info=assert_dict.get("matcher"))
                if invalid_matchers != []:
                    raise AssertionError('断言信息中matcher断言器"{}"当前并不支持, 请重新指定！'.format(invalid_matchers))
                else:
                    logger.info("[Injected]：高级断言注入结果为：\n{}".format(
                        json.dumps(dict(actual=match_result,
                                        expect=expect_vars,
                                        matcher=assert_dict.get("matcher"),
                                        alert=assert_dict.get("alert")), ensure_ascii=False, indent=2)))
                    assert_that(match_result,
                                is_(eval(
                                    self.combine_matcher(matcher_expr=assert_dict.get("matcher"), params=expect_vars))),
                                assert_dict.get("alert"))
            logger.info(
                "[End]：[{}]~[{}]高级断言检测合法，断言成功.".format(self.test_case["ID"],
                                                       self.test_case["Title"]))


class AdvanceAssertionTools(AssertionTools):
    """
    测试结果自动断言高级操作类 ~ 支持依赖数据处理
    """

    def __init__(self, test_case_schema, origin_data, realtime_dependency):
        """
        初始化断言原型数据.
        :param test_case_schema: 测试用例
        :param origin_data: 断言原型数据(dict)
        :param realtime_dependency: 测试依赖
        """
        AssertionTools.__init__(self, test_case_schema=test_case_schema, origin_data=origin_data)
        try:
            if isinstance(test_case_schema, dict) and (
                    isinstance(origin_data, dict) or isinstance(origin_data, list)) and isinstance(realtime_dependency,
                                                                                                   dict):
                self.test_case = test_case_schema
                self.origin_data = origin_data
                self.realtime_dependency = realtime_dependency
        except Exception:
            logger.exception("测试用例test_case_schema及测试依赖realtime_dependency必须用字典方式入参，断言原型origin_data支持字典及列表方式入参！")

    def schema_dependency(self, actual, multi, expr_key, expr_value):
        """
        高级断言接口依赖处理
        :param actual: 实际数据(用于开启是否将预期数据类型转换为实际结果数据类型(actual：开启；None：关闭))
        :param multi: JsonPath列表结果(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
        :param expr_key: 接口依赖Url
        :param expr_value: jsonpath表达式
        :return:
        """
        url = str(expr_key).strip()
        depend_jsonpath_expression = str(expr_value).strip()
        if self.realtime_dependency.__contains__(url):
            depend_jsonpath_value = jsonpath(self.realtime_dependency.get(url),
                                             depend_jsonpath_expression)
            if depend_jsonpath_value is False:
                logger.warning(
                    '[WARNING]：【高级断言接口依赖】依赖接口"{}"响应数据的jsonPath表达式"{}"未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！'.format(
                        url,
                        depend_jsonpath_expression))
                return False
            else:
                if multi is False:
                    depend_jsonpath_value = self.sync_type_with_actual(actual, depend_jsonpath_value[0])
                else:
                    depend_jsonpath_value = self.sync_type_with_actual(actual, depend_jsonpath_value)
                logger.info(
                    '[Dependency]：【高级断言接口依赖】高级断言完成一次依赖接口"{}"的响应体期望数据替换，jsonPath表达式为"{}"，获取期望值为{}.'.format(
                        url, depend_jsonpath_expression, depend_jsonpath_value))
                return depend_jsonpath_value
        else:
            logger.warning('[WARNING]：【高级断言接口依赖】当前接口响应缓存字典中不存在高级断言依赖接口"{}"的任何响应数据！'.format(url))

    def schema_function(self, actual, multi, expr_key, expr_value):
        """
        高级断言函数依赖处理
        :param actual: 实际数据(用于开启是否将预期数据类型转换为实际结果数据类型(actual：开启；None：关闭))
        :param multi: JsonPath列表结果(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
        :param expr_key: 函数接口表达式
        :param expr_value: 函数入参dict
        :return:
        """
        function_expr = expr_key[2:-1]
        function_name = function_expr.split("(")[0]
        if str(function_name).upper() in list(FUNCTION_ENUM.__members__.keys()):
            param_expr = re.search(r'\(.*\)$', function_expr)
            if param_expr:
                param_list = [i.strip() for i in re.split(r'[(|)|,]', param_expr.group()) if i != ""]
                if isinstance(expr_value, dict):
                    param_value_list = []
                    for param in param_list:
                        if expr_value.__contains__(param):
                            param_value_list.append(self.expr_identity(expr_value[param], multi=multi))
                        else:
                            logger.warning(
                                '[WARNING]：【高级断言函数依赖】当前接口预期表达式中依赖函数"{}"的参数"{}"不存在于赋值字典中，请检查！'.format(
                                    function_name, param))
                            break
                    if param_value_list.__len__() == param_list.__len__():
                        eval_expr = function_name + tuple(param_value_list).__str__()
                        eval_expr_value = eval(eval_expr)
                        logger.info(
                            '[Dependency]：【高级断言函数依赖】高级断言完成一次依赖函数"{}"的返回值期望数据替换，依赖函数表达式为"{}"，获取期望值为{}.'.format(
                                function_name, eval_expr, eval_expr_value))
                        eval_expr_value = self.sync_type_with_actual(actual, eval_expr_value)
                        return eval_expr_value
                    else:
                        logger.warning(
                            '[WARNING]：【高级断言函数依赖】当前接口预期表达式中依赖函数"{}"由于参数赋值存在缺失，将忽略此函数依赖！'.format(
                                function_name))
                else:
                    logger.warning(
                        '[WARNING]：【高级断言函数依赖】当前接口预期表达式中调用的依赖函数"{}"传值入参形式必须为字典结构，请检查！'.format(
                            function_name))
            else:
                logger.warning(
                    '[WARNING]：【高级断言函数依赖】当前接口预期表达式中调用的依赖函数"{}"调用方式存在错误，请检查其是否合法！'.format(
                        function_name))
        else:
            logger.warning(
                '[WARNING]：【高级断言函数依赖】当前接口预期表达式中指定的依赖函数"{}"暂未支持，请检查或追加！'.format(function_name))

    def expr_identity(self, param_expr, fetch_actual=False, multi=False):
        """
        解析数据依赖表达式并求值
        :param param_expr: 数据依赖表达式
        :param fetch_actual: 当前是否正在识别actual实际结果(True: 当前识别actual)
        :param multi: JsonPath列表结果(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
        :return:
        """
        if re.match(r'^\$\..*', str(param_expr)):
            value = jsonpath(self.origin_data, param_expr)
            if fetch_actual is True:
                result = value if value is not False else False
            else:
                if multi is True:
                    result = value if value is not False else False
                else:
                    result = value[0] if value is not False else False
            if result is False:
                if fetch_actual is False:
                    logger.warning('[WARNING]：【高级断言数据依赖】数据依赖jsonpath表达式"{}"当前未匹配到任何值，请检查！'.format(param_expr))
                else:
                    logger.warning('[WARNING]：高级断言中获取actual实际数据的jsonpath表达式"{}"当前未匹配到任何值，请检查！'.format(param_expr))
            return result
        elif re.match(r'^\$\{.*\}$', str(param_expr)):
            expr = param_expr[2:-1]
            result = eval(expr)
            if result is None:
                if fetch_actual is False:
                    logger.warning('[WARNING]：【高级断言数据依赖】数据依赖求值表达式"{}"当前所求值为None，请检查！'.format(param_expr))
                else:
                    logger.warning('[WARNING]：高级断言中获取actual实际数据的求值表达式"{}"当前所求值为None，请检查！'.format(param_expr))
            return result
        elif isinstance(param_expr, dict):
            # if fetch_actual is True:
            #     actual_value_list = []
            #     for key, value in param_expr.items():
            #         if re.match(r'^/{1}.+', key):
            #             actual_value_list.append(self.schema_dependency(actual=None, expr_key=key, expr_value=value))
            #         elif re.match(r'^\$\{.*\}$', key):
            #             actual_value_list.append(self.schema_function(actual=None, expr_key=key, expr_value=value))
            #         else:
            #             pass
            #     return actual_value_list
            # else:
            for key, value in param_expr.items():
                if re.match(r'^/{1}.+', key):
                    return self.schema_dependency(actual=None, multi=multi, expr_key=key, expr_value=value)
                elif re.match(r'^\$\{.*\}$', key):
                    return self.schema_function(actual=None, multi=multi, expr_key=key, expr_value=value)
                else:
                    pass
            logger.warning(
                '[WARNING]：【高级断言数据依赖】数据依赖字典表达式{}当前未匹配到任何字典规则(字典规则当前支持接口依赖及函数依赖)，请检查！'.format(param_expr))
        else:
            return param_expr

    def sync_type_with_actual(self, actual, sync_value):
        """
        将预期值类型同步为实际值类型
        :param actual: 实际值
        :param sync_value: 预期值
        :return:
        """
        if actual is not None and actual is not False:
            if isinstance(actual, list):
                if isinstance(sync_value, list):
                    result = []
                    for value in sync_value:
                        temp = value_by_type(actual[0], value)
                        result.append(temp)
                    return result
                else:
                    result = value_by_type(actual[0], sync_value)
                    return result
            else:
                if isinstance(sync_value, list):
                    result = []
                    for value in sync_value:
                        temp = value_by_type(actual, value)
                        result.append(temp)
                    return result
                else:
                    result = value_by_type(actual, sync_value)
                    return result
        else:
            result = sync_value
            return result

    def check_expect(self, expect, actual, multi):
        """
        检查期望数据类型并返回处理结果, 扩展支持接口依赖及函数依赖的期望值
        :param actual: 实际数据(用于开启是否将预期数据类型转换为实际结果数据类型(actual：开启；None：关闭))
        :param multi: JsonPath列表结果(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
        :param expect: 期望数据
        :return:
        """
        realtime_expect = []
        if isinstance(expect, list) and expect.__len__() != 0:
            expect_data = expect[0]
            if isinstance(expect_data, dict):
                for expr_key, expr_value in expect_data.items():
                    if re.match(r'^/{1}.+', expr_key):
                        realtime_expect.append(
                            self.schema_dependency(actual=actual, multi=multi, expr_key=expr_key,
                                                   expr_value=expr_value))
                    elif re.match(r'^\$\{.*\}$', expr_key):
                        realtime_expect.append(
                            self.schema_function(actual=actual, multi=multi, expr_key=expr_key, expr_value=expr_value))
                    else:
                        pass
                return realtime_expect
            elif re.match(r'^\$\..*', str(expect_data)):
                value = jsonpath(self.origin_data, expect_data)
                if multi is True:
                    result = self.sync_type_with_actual(actual=actual,
                                                        sync_value=value if value is not False else False)
                else:
                    result = self.sync_type_with_actual(actual=actual,
                                                        sync_value=value[0] if value is not False else False)
                return [result]
            elif re.match(r'^\$\{.*\}$', str(expect_data)):
                expr = expect_data[2:-1]
                result = self.sync_type_with_actual(actual=actual, sync_value=eval(expr))
                return [result]
            else:
                expect = self.sync_type_with_actual(actual=actual, sync_value=expect)
                return expect
        else:
            logger.warning('[WARNING]：断言信息中expect期望值表达式"{}"必须以列表方式指定且不能为空, 请检查并修改！'.format(expect))
            return expect

    def sample_assert(self, **err_info):
        """
        基础断言检查,仅断言响应码err和响应体errmsg
        :param err_info: 基本响应信息, 如响应码、响应描述等
        :return:
        """
        if err_info == {}:
            logger.warning(
                "[WARNING]：[{}]~[{}]基础断言当前未设置任何检查信息，请首先指定！".format(self.test_case["ID"], self.test_case["Title"]))
            raise FlakyTestCaseError(msg="当前基础断言未设置任何检查信息")
        else:
            logger.info("[Checking]：[{}]~[{}]开启基础断言检查......".format(self.test_case["ID"], self.test_case["Title"]))
            for key, value in err_info.items():
                if self.origin_data.__contains__(str(key)):
                    assert_that(self.origin_data[str(key)], is_(equal_to(value)), "{}不匹配！".format(str(key)))
                else:
                    raise AssertionError('响应报文中未发现关键字"{}"'.format(str(key)))
            logger.info(
                "[End]：[{}]~[{}]基础断言检测合法，断言成功.".format(self.test_case["ID"], self.test_case["Title"]))

    def advance_assert(self, **err_info):
        """
        高级断言检查,支持jsonpath结合hamcrest进行断言
        :param err_info: 基本响应信息, 如响应码、响应描述等
        :return:
        """
        if self.test_case["AssertInfo"] == "":
            logger.warning(
                '[WARNING]：测试用例[{}]~[{}]中未设置任何断言表达式，默认仅启用基础断言！'.format(self.test_case["ID"], self.test_case["Title"]))
            self.sample_assert(**err_info)
        else:
            logger.info("[Checking]：开启高级断言检查......")
            for assert_dict in json.loads(self.test_case["AssertInfo"]):
                if assert_dict.__contains__("multi"):
                    multi_flag = True if assert_dict.get("multi") is True else False
                else:
                    multi_flag = False
                assert_dict["multi"] = multi_flag
                match_result = emoji_to_str(self.expr_identity(assert_dict.get("actual"), fetch_actual=True, multi=multi_flag))
                expect_vars = emoji_to_str(self.check_expect(actual=None, multi=multi_flag, expect=assert_dict.get("expect")))
                if expect_vars == []:
                    expect_vars = [""]
                invalid_matchers = self.check_matcher_type(matcher_info=assert_dict.get("matcher"))
                if invalid_matchers != []:
                    raise AssertionError('断言信息中matcher断言器"{}"当前并不支持, 请重新指定！'.format(invalid_matchers))
                else:
                    logger.info("[Injected]：高级断言注入结果为：\n{}".format(
                        json.dumps(dict(actual=match_result,
                                        expect=expect_vars,
                                        matcher=assert_dict.get("matcher"),
                                        alert=assert_dict.get("alert"),
                                        multi=assert_dict.get("multi")), ensure_ascii=False, indent=2)))
                    assert_that(match_result,
                                is_(eval(
                                    self.combine_matcher(matcher_expr=assert_dict.get("matcher"), params=expect_vars))),
                                assert_dict.get("alert"))
            logger.info(
                "[End]：[{}]~[{}]高级断言检测合法，断言成功.".format(self.test_case["ID"],
                                                       self.test_case["Title"]))


if __name__ == '__main__':
    def combine_matcher(matcher_expr, params):
        matcher_list = re.findall('[^()]+', str(matcher_expr))
        matchers = matcher_expr.replace(str(matcher_list[-1]), str(matcher_list[-1]) + "(*{args})").format(
            args=params)
        return matchers


    data = {
        "data": {
            "diagnosisInfoId": 5384,
            "payRecordId": 5014,
            "appId": 725
        },
        "err": "0",
        "errmsg": "操作成功"
    }

    assert_schema = [
        {
            "actual": "$.err",
            "expect": [["0", "1"]],
            "matcher": "is_not(contains_in)",
            "alert": "当前仅断言历史诊号，请查看响应体是否为新诊号！"
        }
    ]
    test_index = assert_schema[0]
    match_data = jsonpath(data, test_index.get("actual"))
    print("JsonPath匹配数据为：{}".format(match_data))
    item = test_index.get("expect")
    assert_result = assert_that(match_data, is_(eval(combine_matcher(test_index.get("matcher"), item))))
    print("Assert断言结果为：{}".format("通过" if assert_result is None else assert_result))
