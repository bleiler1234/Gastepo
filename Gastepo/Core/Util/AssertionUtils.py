# -*- coding: utf-8 -*-

import json

from hamcrest import *
from jsonpath import jsonpath

from Gastepo.Core.Base.BaseData import MATCHER_TYPE
from Gastepo.Core.Base.CustomException import FlakyTestCaseError
from Gastepo.Core.Extend.AssertDependencyExtends import *
from Gastepo.Core.Extend.HamcrestCustomExtends import *
from Gastepo.Core.Util.CommonUtils import emoji_to_str, value_by_type, url_identity

from Gastepo.Core.Util.LogUtils import logger


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

    def schema_url(self, expr_key, expr_value, actual_mode, function_mode, multi):
        """
         高级断言接口依赖处理
         :param expr_key: 接口依赖地址
         :param expr_value: 接口依赖Schema
         :param actual_mode: actual识别模式开关
         :param function_mode: 函数依赖表达式取值模式开关
         :param multi: JsonPath取值模式开关(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
         :return:
         """
        url = str(expr_key).strip()
        now = str(self.test_case["Method"]).strip().upper() + " " + str(self.test_case["UrlPath"]).strip()
        if self.realtime_dependency.__contains__(url):
            if isinstance(expr_value, str):
                depend_jsonpath_expression = str(expr_value).strip()
                depend_jsonpath_value = jsonpath(self.realtime_dependency[url]['response']['data'],
                                                 depend_jsonpath_expression)
                if function_mode:
                    if multi:
                        result = depend_jsonpath_value if depend_jsonpath_value is not False else False
                    else:
                        result = depend_jsonpath_value[0] if depend_jsonpath_value is not False else False
                else:
                    result = depend_jsonpath_value if depend_jsonpath_value is not False else False
                if result is False:
                    if url == now:
                        if actual_mode:
                            logger.warning(
                                '[WARNING]：【高级断言自身依赖】高级断言actual中通过jsonpath表达式"{}"直接获取自身接口响应数据时未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！！'.format(
                                    depend_jsonpath_expression))
                        else:
                            logger.warning(
                                '[WARNING]：【高级断言自身依赖】高级断言expect中通过jsonpath表达式"{}"直接获取自身接口响应数据时未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！！'.format(
                                    depend_jsonpath_expression))
                    else:
                        if actual_mode:
                            logger.warning(
                                '[WARNING]：【高级断言接口依赖】高级断言actual中通过jsonpath表达式"{}"直接获取依赖接口"{}"响应数据时未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！！'.format(
                                    depend_jsonpath_expression, url))
                        else:
                            logger.warning(
                                '[WARNING]：【高级断言接口依赖】高级断言expect中通过jsonpath表达式"{}"直接获取依赖接口"{}"响应数据时未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！！'.format(
                                    depend_jsonpath_expression, url))
                return result
            elif isinstance(expr_value, dict) and expr_value != dict():
                if set(list(expr_value.keys())) <= {"request", "response"}:
                    if expr_value.__contains__("request"):
                        if isinstance(expr_value["request"], dict) and expr_value["request"] != dict():
                            if set(list(expr_value["request"].keys())) <= {"path", "header", "param", "data"}:
                                if expr_value["request"].__contains__("path"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["request"]["path"],
                                        origin_data=self.realtime_dependency[url]["request"]["path"],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["request"]["path"],
                                        origin_data=
                                        self.realtime_dependency[url]["request"][
                                            "path"],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口请求路径的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口请求路径的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"请求路径的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"请求路径的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                elif expr_value["request"].__contains__("header"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["request"]["header"],
                                        origin_data=self.realtime_dependency[url]["request"][
                                            "header"],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["request"]["header"],
                                        origin_data=
                                        self.realtime_dependency[url]["request"][
                                            "header"],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口请求头的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口请求头的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"请求头的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"请求头的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                elif expr_value["request"].__contains__("param"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["request"]["param"],
                                        origin_data=self.realtime_dependency[url]["request"]["param"],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["request"]["param"],
                                        origin_data=
                                        self.realtime_dependency[url]["request"][
                                            "param"],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口请求参数的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口请求参数的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"请求参数的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"请求参数的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                elif expr_value["request"].__contains__("data"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["request"]["data"],
                                        origin_data=self.realtime_dependency[url]["request"]["data"],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["request"]["data"],
                                        origin_data=
                                        self.realtime_dependency[url]["request"][
                                            "data"],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口请求体的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口请求体的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"请求体的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"请求体的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                else:
                                    pass
                            else:
                                if url == now:
                                    if actual_mode:
                                        logger.warning(
                                            '[WARNING]：【高级断言自身依赖】高级断言actual中获取自身接口请求信息的request表达式字典当前仅支持path、header、param、data，请检查！')
                                    else:
                                        logger.warning(
                                            '[WARNING]：【高级断言自身依赖】高级断言expect中获取自身接口请求信息的request表达式字典当前仅支持path、header、param、data，请检查！')
                                else:
                                    if actual_mode:
                                        logger.warning(
                                            '[WARNING]：【高级断言接口依赖】高级断言actual中获取依赖接口"{}"请求信息的request表达式字典当前仅支持path、header、param、data，请检查！'.format(
                                                url))
                                    else:
                                        logger.warning(
                                            '[WARNING]：【高级断言接口依赖】高级断言expect中获取依赖接口"{}"请求信息的request表达式字典当前仅支持path、header、param、data，请检查！'.format(
                                                url))
                                return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
                        else:
                            if url == now:
                                if actual_mode:
                                    logger.warning(
                                        '[WARNING]：【高级断言自身依赖】高级断言actual中获取自身接口请求信息的request表达式类型必须为字典形式且不能为空，请检查！')
                                else:
                                    logger.warning(
                                        '[WARNING]：【高级断言自身依赖】高级断言expect中获取自身接口请求信息的request表达式类型必须为字典形式且不能为空，请检查！')
                            else:
                                if actual_mode:
                                    logger.warning(
                                        '[WARNING]：【高级断言接口依赖】高级断言actual中获取依赖接口"{}"请求信息的request表达式类型必须为字典形式且不能为空，请检查！'.format(
                                            url))
                                else:
                                    logger.warning(
                                        '[WARNING]：【高级断言接口依赖】高级断言expect中获取依赖接口"{}"请求信息的request表达式类型必须为字典形式且不能为空，请检查！'.format(
                                            url))
                            return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
                    elif expr_value.__contains__("response"):
                        if isinstance(expr_value["response"], dict) and expr_value["response"] != dict():
                            if set(list(expr_value["response"].keys())) <= {"header", "data", "status_code"}:
                                if expr_value["response"].__contains__("status_code"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["response"]["status_code"],
                                        origin_data=self.realtime_dependency[url],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["response"]["status_code"],
                                        origin_data=self.realtime_dependency[url],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口响应状态码的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口响应状态码的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"响应状态码的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"响应状态码的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                elif expr_value["response"].__contains__("header"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["response"]["header"],
                                        origin_data=self.realtime_dependency[url]["response"][
                                            "header"],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["response"]["header"],
                                        origin_data=
                                        self.realtime_dependency[url]["response"][
                                            "header"],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口响应头的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口响应头的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"响应头的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"响应头的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                elif expr_value["response"].__contains__("data"):
                                    return_value = self.analysis_actual(
                                        param_expr=expr_value["response"]["data"],
                                        origin_data=self.realtime_dependency[url]["response"]["data"],
                                        function_mode=function_mode,
                                        multi=multi
                                    ) if actual_mode else self.analysis_expect(
                                        param_expr=expr_value["response"]["data"],
                                        origin_data=
                                        self.realtime_dependency[url]["response"][
                                            "data"],
                                        function_mode=function_mode,
                                        multi=multi)
                                    if url == now:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言actual中完成一次自身接口响应体的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言自身依赖】高级断言expect中完成一次自身接口响应体的期望数据替换，获取期望值为{}.'.format(
                                                    return_value))
                                    else:
                                        if actual_mode:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言actual中完成一次依赖接口"{}"响应体的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                        else:
                                            logger.info(
                                                '[Dependency]：【高级断言接口依赖】高级断言expect中完成一次依赖接口"{}"响应体的期望数据替换，获取期望值为{}.'.format(
                                                    url, return_value))
                                    return return_value
                                else:
                                    pass
                            else:
                                if url == now:
                                    if actual_mode:
                                        logger.warning(
                                            '[WARNING]：【高级断言自身依赖】高级断言actual中获取自身接口响应信息的response表达式字典当前仅支持status_code、header、data，请检查！')
                                    else:
                                        logger.warning(
                                            '[WARNING]：【高级断言自身依赖】高级断言expect中获取自身接口响应信息的response表达式字典当前仅支持status_code、header、data，请检查！')
                                else:
                                    if actual_mode:
                                        logger.warning(
                                            '[WARNING]：【高级断言接口依赖】高级断言actual中获取依赖接口"{}"响应信息的response表达式字典当前仅支持status_code、header、data，请检查！'.format(
                                                url))
                                    else:
                                        logger.warning(
                                            '[WARNING]：【高级断言接口依赖】高级断言expect中获取依赖接口"{}"响应信息的response表达式字典当前仅支持status_code、header、data，请检查！'.format(
                                                url))
                                return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
                        else:
                            if url == now:
                                if actual_mode:
                                    logger.warning(
                                        '[WARNING]：【高级断言自身依赖】高级断言actual中获取自身接口响应信息的response表达式类型必须为字典形式且不能为空，请检查！')
                                else:
                                    logger.warning(
                                        '[WARNING]：【高级断言自身依赖】高级断言expect中获取自身接口响应信息的response表达式类型必须为字典形式且不能为空，请检查！')
                            else:
                                if actual_mode:
                                    logger.warning(
                                        '[WARNING]：【高级断言接口依赖】高级断言actual中获取依赖接口"{}"响应信息的response表达式类型必须为字典形式且不能为空，请检查！'.format(
                                            url))
                                else:
                                    logger.warning(
                                        '[WARNING]：【高级断言接口依赖】高级断言expect中获取依赖接口"{}"响应信息的response表达式类型必须为字典形式且不能为空，请检查！'.format(
                                            url))
                            return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
                    else:
                        pass
                else:
                    if url == now:
                        if actual_mode:
                            logger.warning(
                                '[WARNING]：【高级断言自身依赖】高级断言actual中自身接口的字典表达式键名必须为request或response，请检查！')
                        else:
                            logger.warning(
                                '[WARNING]：【高级断言自身依赖】高级断言expect中自身接口的字典表达式键名必须为request或response，请检查！')
                    else:
                        if actual_mode:
                            logger.warning(
                                '[WARNING]：【高级断言接口依赖】高级断言actual中依赖接口"{}"的字典表达式键名必须为request或response，请检查！'.format(url))
                        else:
                            logger.warning(
                                '[WARNING]：【高级断言接口依赖】高级断言expect中依赖接口"{}"的字典表达式键名必须为request或response，请检查！'.format(url))
                    return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
            else:
                if url == now:
                    if actual_mode:
                        logger.warning('[WARNING]：【高级断言自身依赖】高级断言actual中自身接口未匹配到任何合法赋值规则，请指定str或非空dict形式的赋值规则！')
                    else:
                        logger.warning('[WARNING]：【高级断言自身依赖】高级断言expect中自身接口未匹配到任何合法赋值规则，请指定str或非空dict形式的赋值规则！')
                else:
                    if actual_mode:
                        logger.warning(
                            '[WARNING]：【高级断言接口依赖】高级断言actual中依赖接口"{}"未匹配到任何合法赋值规则，请指定str或非空dict形式的赋值规则！'.format(url))
                    else:
                        logger.warning(
                            '[WARNING]：【高级断言接口依赖】高级断言expect中依赖接口"{}"未匹配到任何合法赋值规则，请指定str或非空dict形式的赋值规则！'.format(url))
                return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
        else:
            logger.warning('[WARNING]：【高级断言接口依赖】当前接口信息缓存字典中不存在当前自身接口"{}"的任何接口信息！'.format(url))
            return "Missing Dependency Url" if actual_mode else ["Missing Dependency Url"]

    def schema_function(self, expr_key, expr_value, actual_mode, multi):
        """
        高级断言函数依赖处理
        :param expr_key: 函数名称标识符
        :param expr_value: 函数依赖Schema
        :param actual_mode: actual识别模式开关
        :param multi: JsonPath取值模式开关(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
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
                            param_value_list.append(
                                self.analysis_actual(param_expr=expr_value[param], origin_data=self.origin_data,
                                                     function_mode=True, multi=multi) if actual_mode else
                                self.analysis_expect(param_expr=expr_value[param], origin_data=self.origin_data,
                                                     function_mode=True, multi=multi))
                        else:
                            if actual_mode:
                                logger.warning(
                                    '[WARNING]：【高级断言函数依赖】高级断言actual中依赖函数"{}"的参数"{}"不存在于赋值字典中，请检查！'.format(
                                        function_name, param))
                            else:
                                logger.warning(
                                    '[WARNING]：【高级断言函数依赖】高级断言expect中依赖函数"{}"的参数"{}"不存在于赋值字典中，请检查！'.format(
                                        function_name, param))
                            break
                    if param_value_list.__len__() == param_list.__len__():
                        eval_expr = function_name + tuple(param_value_list).__str__()
                        eval_expr_value = eval(eval_expr)
                        if actual_mode:
                            logger.info(
                                '[Dependency]：【高级断言函数依赖】高级断言actual中完成一次依赖函数"{}"的返回值期望数据替换，依赖函数表达式为"{}"，获取期望值为{}.'.format(
                                    function_name, eval_expr, eval_expr_value))
                        else:
                            logger.info(
                                '[Dependency]：【高级断言函数依赖】高级断言expect中完成一次依赖函数"{}"的返回值期望数据替换，依赖函数表达式为"{}"，获取期望值为{}.'.format(
                                    function_name, eval_expr, eval_expr_value))
                        return eval_expr_value
                    else:
                        if actual_mode:
                            logger.warning(
                                '[WARNING]：【高级断言函数依赖】高级断言actual中依赖函数"{}"由于参数赋值存在缺失，将忽略此函数依赖！'.format(
                                    function_name))
                        else:
                            logger.warning(
                                '[WARNING]：【高级断言函数依赖】高级断言expect中依赖函数"{}"由于参数赋值存在缺失，将忽略此函数依赖！'.format(
                                    function_name))
                        return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
                else:
                    if actual_mode:
                        logger.warning(
                            '[WARNING]：【高级断言函数依赖】高级断言actual中依赖函数"{}"的传值入参形式必须为字典结构，请检查！'.format(
                                function_name))
                    else:
                        logger.warning(
                            '[WARNING]：【高级断言函数依赖】高级断言expect中依赖函数"{}"的传值入参形式必须为字典结构，请检查！'.format(
                                function_name))
                    return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
            else:
                if actual_mode:
                    logger.warning(
                        '[WARNING]：【高级断言函数依赖】高级断言actual中依赖函数"{}"的函数调用方式存在错误，请检查其是否合法！'.format(
                            function_name))
                else:
                    logger.warning(
                        '[WARNING]：【高级断言函数依赖】高级断言expect中依赖函数"{}"的函数调用方式存在错误，请检查其是否合法！'.format(
                            function_name))
                return "Catching Dependency Fail" if actual_mode else ["Catching Dependency Fail"]
        else:
            if actual_mode:
                logger.warning(
                    '[WARNING]：【高级断言函数依赖】高级断言actual中依赖函数"{}"暂未支持，请检查或追加！'.format(function_name))
            else:
                logger.warning(
                    '[WARNING]：【高级断言函数依赖】高级断言expect中依赖函数"{}"暂未支持，请检查或追加！'.format(function_name))
            return "Missing Dependency Function" if actual_mode else ["Missing Dependency Function"]

    def analysis_actual(self, param_expr, origin_data, function_mode=False, multi=False):
        """
        actual数据依赖解析处理
        :param param_expr: 数据依赖表达式
        :param origin_data: 待取值字典（仅jsonpath模式时使用）
        :param function_mode: 函数依赖表达式取值模式开关
        :param multi: JsonPath取值模式开关(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
        :return:
        """
        if not function_mode:
            if re.match(r'^\$\..*', str(param_expr)):
                value = jsonpath(origin_data, param_expr)
                result = value if value is not False else False
                if result is False:
                    logger.warning('[WARNING]：高级断言actual中获取数据的jsonpath表达式"{}"当前未匹配到任何值，请检查！'.format(param_expr))
                return result
            elif re.match(r'^\$\{.*\}$', str(param_expr)):
                expr = param_expr[2:-1]
                result = eval(expr)
                if result is None:
                    logger.warning('[WARNING]：高级断言actual中获取数据的类SpEL表达式"{}"当前所求值为None，请检查！'.format(param_expr))
                return result
            elif isinstance(param_expr, dict):
                for key, value in param_expr.items():
                    if re.match(r'(^self$)', key):
                        return self.schema_url(expr_key=str(self.test_case["Method"]).strip().upper() + " " + str(
                            self.test_case["UrlPath"]).strip(),
                                               expr_value=value, actual_mode=True,
                                               function_mode=function_mode, multi=multi)
                    elif url_identity(url=key, simple=False) != "Unrecognized Url":
                        return self.schema_url(expr_key=key, expr_value=value, actual_mode=True,
                                               function_mode=function_mode, multi=multi)
                    elif re.match(r'^\$\{.*\}$', key):
                        return self.schema_function(expr_key=key, expr_value=value, actual_mode=True, multi=multi)
                    else:
                        pass
                logger.warning(
                    '[WARNING]：【高级断言数据依赖】高级断言actual中指定的字典形式表达式"{}"当前未匹配到任何已有字典规则(当前字典规则支持自身接口依赖、外部接口依赖及注册函数依赖)，请检查！'.format(
                        param_expr))
                return "Invalid Dictionary Schema"
            else:
                return param_expr
        else:
            if re.match(r'^\$\..*', str(param_expr)):
                value = jsonpath(origin_data, param_expr)
                if multi:
                    result = value if value is not False else False
                else:
                    result = value[0] if value is not False else False
                if result is False:
                    logger.warning('[WARNING]：高级断言actual中获取数据的jsonpath表达式"{}"当前未匹配到任何值，请检查！'.format(param_expr))
                return result
            elif re.match(r'^\$\{.*\}$', str(param_expr)):
                expr = param_expr[2:-1]
                result = eval(expr)
                if result is None:
                    logger.warning('[WARNING]：高级断言actual中获取数据的类SpEL表达式"{}"当前所求值为None，请检查！'.format(param_expr))
                return result
            elif isinstance(param_expr, dict):
                for key, value in param_expr.items():
                    if re.match(r'(^self$)', key):
                        return self.schema_url(expr_key=str(self.test_case["Method"]).strip().upper() + " " + str(
                            self.test_case["UrlPath"]).strip(),
                                               expr_value=value, actual_mode=True,
                                               function_mode=True, multi=multi)
                    elif url_identity(url=key, simple=False) != "Unrecognized Url":
                        return self.schema_url(expr_key=key, expr_value=value, actual_mode=True,
                                               function_mode=True, multi=multi)
                    elif re.match(r'^\$\{.*\}$', key):
                        return self.schema_function(expr_key=key, expr_value=value, actual_mode=True, multi=multi)
                    else:
                        pass
                logger.warning(
                    '[WARNING]：【高级断言数据依赖】高级断言actual中指定的字典形式表达式"{}"当前未匹配到任何已有字典规则(当前字典规则支持自身接口依赖、外部接口依赖及注册函数依赖)，请检查！'.format(
                        param_expr))
                return "Invalid Dictionary Schema"
            else:
                return param_expr

    def analysis_expect(self, param_expr, origin_data, function_mode=False, multi=False):
        """
        expect数据依赖解析处理
        :param param_expr: 数据依赖表达式
        :param origin_data: 待取值字典（仅jsonpath模式时使用）
        :param function_mode: 函数依赖表达式取值模式开关（expect依赖表达式暂时不启用）
        :param multi: JsonPath取值模式开关(False：仅获取JsonPath列表结果首个值 True：获取整个JsonPath列表结果)
        :return:
        """
        if re.match(r'^\$\..*', str(param_expr)):
            value = jsonpath(origin_data, param_expr)
            if multi:
                result = value if value is not False else False
            else:
                result = value[0] if value is not False else False
            if result is False:
                logger.warning('[WARNING]：高级断言expect中获取数据的jsonpath表达式"{}"当前未匹配到任何值，请检查！'.format(param_expr))
            return result
        elif re.match(r'^\$\{.*\}$', str(param_expr)):
            expr = param_expr[2:-1]
            result = eval(expr)
            if result is None:
                logger.warning('[WARNING]：高级断言expect中获取数据的类SpEL表达式"{}"当前所求值为None，请检查！'.format(param_expr))
            return result
        elif isinstance(param_expr, dict):
            for key, value in param_expr.items():
                if re.match(r'(^self$)', key):
                    return self.schema_url(expr_key=str(self.test_case["Method"]).strip().upper() + " " + str(
                        self.test_case["UrlPath"]).strip(),
                                           expr_value=value, actual_mode=False,
                                           function_mode=True, multi=multi)
                elif url_identity(url=key, simple=False) != "Unrecognized Url":
                    return self.schema_url(expr_key=key, expr_value=value, actual_mode=False,
                                           function_mode=True, multi=multi)
                elif re.match(r'^\$\{.*\}$', key):
                    return self.schema_function(expr_key=key, expr_value=value, actual_mode=False, multi=multi)
                else:
                    pass
            logger.warning(
                '[WARNING]：【高级断言数据依赖】高级断言expect中指定的字典形式表达式"{}"当前未匹配到任何已有字典规则(当前字典规则支持自身接口依赖、外部接口依赖及注册函数依赖)，请检查！'.format(
                    param_expr))
            return ["Invalid Dictionary Schema"]
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
            for key, value in {emoji_to_str(x): emoji_to_str(y) for x, y in err_info.items()}.items():
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
        expect_vars = None
        if self.test_case["AssertInfo"] == "":
            logger.warning(
                '[WARNING]：测试用例[{}]~[{}]中未设置任何断言表达式，默认仅启用基础断言！'.format(self.test_case["ID"], self.test_case["Title"]))
            self.sample_assert(**err_info)
        else:
            for assert_dict in json.loads(self.test_case["AssertInfo"]):
                logger.info("[Checking]：开启高级断言检测......")
                if assert_dict.__contains__("multi"):
                    multi_flag = True if assert_dict.get("multi") is True else False
                else:
                    multi_flag = False
                assert_dict["multi"] = multi_flag
                match_result = emoji_to_str(
                    self.analysis_actual(param_expr=assert_dict.get("actual"), origin_data=self.origin_data,
                                         multi=multi_flag))
                if isinstance(assert_dict.get("expect"), list) and assert_dict.get("expect").__len__() != 0:
                    expect_vars = emoji_to_str(
                        [self.analysis_expect(param_expr=assert_dict.get("expect")[0], origin_data=self.origin_data,
                                              multi=multi_flag)])
                else:
                    logger.warning(
                        '[WARNING]：高级断言中expect数据依赖表达式"{}"必须以列表方式指定且不能为空, 请检查并修改！'.format(assert_dict.get("expect")))
                    expect_vars = emoji_to_str(["" if assert_dict.get("expect") == [] else assert_dict.get("expect")])
                if expect_vars == []:
                    expect_vars = [""]
                if assert_dict.get("matcher") == "instance_of":
                    expect_vars = [eval(expr) for expr in expect_vars]
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
                    logger.info("[Pass]：当前高级断言检测通过.")
            logger.info(
                "[Success]：[{}]~[{}]全部高级断言检测完毕，所有高级断言均运行通过.".format(self.test_case["ID"],
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
