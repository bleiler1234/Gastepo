# -*- coding: utf-8 -*-

import json
from urllib.parse import urljoin

import requests
from jsonpath import jsonpath

from Gastepo.Core.Base.CustomException import InvalidConsumesError
from Gastepo.Core.Extend.AssertDependencyExtends import *
from Gastepo.Core.Util.CommonUtils import param_to_dict, value_by_type, xml_to_json, json_to_xml
from Gastepo.Core.Util.LogUtils import logger

# 全局Session
GLOBAL_SESSION = requests.session()


class RequestTool(object):
    """
    HTTP(S)请求工具类
    """

    def __init__(self, global_session=False):
        """
        初始化Http请求Session
        :param global_session: 是否开启全局Session(默认False)
        """
        self.session = GLOBAL_SESSION if global_session is True else requests.session()

    @property
    def get_session(self):
        """
        获取请求session
        :return:
        """
        return self.session

    def request(self, url, method, headers=None, cookies=None, auth=None, params=None, data=None, json=None):
        """
        封装request的主要请求参数。
        :param url: 请求URL（必填）
        :param method: 请求方法（必填）
        :param headers: 请求头
        :param cookies: 请求Cookie
        :param auth: 认证信息, 如HTTPBasicAuth('user', 'passwd')
        :param params: 请求参数
        :param data: 请求体, dict时默认application/json
        :param json: 请求体Json
        :return:
        """
        try:
            response = self.session.request(url=url,
                                            method=method,
                                            headers=headers,
                                            cookies=cookies,
                                            auth=auth,
                                            params=params,
                                            data=data,
                                            json=json)
            return response
        except Exception:
            logger.exception('[Exception]：请求"{}"时发生异常！'.format(url))

    def get(self, url, **kwargs):
        """
        封装get请求。
        :param url: 请求URL（必填）
        :param kwargs: 请求字典
        :return:
        """
        try:
            response = self.session.get(url=url, **kwargs)
            return response
        except Exception:
            logger.exception('[Exception]：请求"{}"时发生异常！'.format(url))

    def post(self, url, data=None, json=None, **kwargs):
        """
        封装post请求。
        :param url: 请求URL（必填）
        :param data: 请求体, dict时默认application/json
        :param json: 请求体Json
        :param kwargs: 请求字典
        :return:
        """
        try:
            response = self.session.post(url=url, data=data, json=json, **kwargs)
            return response
        except Exception:
            logger.exception('[Exception]：请求"{}"时发生异常！'.format(url))

    def put(self, url, data=None, **kwargs):
        """
        封装put请求。
        :param url: 请求URL（必填）
        :param data: 请求体, dict时默认application/json
        :param kwargs: 请求字典
        :return:
        """
        try:
            response = self.session.put(url=url, data=data, **kwargs)
            return response
        except Exception:
            logger.exception('[Exception]：请求"{}"时发生异常！'.format(url))

    def patch(self, url, data=None, **kwargs):
        """
        封装patch请求。
        :param url: 请求URL（必填）
        :param data: 请求体, dict时默认application/json
        :param kwargs: 请求字典
        :return:
        """
        try:
            response = self.session.patch(url=url, data=data, **kwargs)
            return response
        except Exception:
            logger.exception('[Exception]：请求"{}"时发生异常！'.format(url))

    def delete(self, url, **kwargs):
        """
        封装delete请求。
        :param url: 请求URL（必填）
        :param kwargs: 请求字典
        :return:
        """
        try:
            response = self.session.delete(url=url, **kwargs)
            return response
        except Exception:
            logger.exception('[Exception]：请求"{}"时发生异常！'.format(url))


class SimpleTestCaseRequestTool(RequestTool):
    """
    测试用例HTTP(S)请求工具类 ~ 不支持请求扩展及接口依赖。
    """

    def __init__(self, test_case_schema=None, global_session=False):
        """
        初始化测试用例请求工具类
        :param test_case_schema: 测试用例
        :param global_session: 是否开启全局Session(默认False)
        """
        RequestTool.__init__(self, global_session=global_session)
        if isinstance(test_case_schema, dict):
            self.test_case = test_case_schema
        else:
            logger.exception("测试用例参数test_case_schema必须用字典方式入参！")

    def mapping_header(self, headers):
        """
        转换请求头RequestHeader
        :param headers: 请求头RequestHeader
        :return: dict
        """
        try:
            if headers == "":
                return {}
            else:
                return json.loads(self.test_case["RequestHeader"])
        except Exception:
            logger.exception("转换请求头RequestHeader过程中发生异常，请检查！")

    def mapping_data(self, consumes):
        """
        根据Consumes支持的请求头匹配请求body
        :param consumes: 请求头类型
        :return: 请求body
        """
        consume = str(consumes).lower()
        try:
            if consume not in ["application/x-www-form-urlencoded", "application/json", "*/*"]:
                raise InvalidConsumesError
            if consume == "application/x-www-form-urlencoded":
                return urlencode(json.loads(self.test_case["RequestData"]))
            if consume == "application/json" or consume == "*/*":
                return self.test_case["RequestData"]
        except InvalidConsumesError:
            logger.exception('当前暂时不支持请求头"{}"类型的数据解析！'.format(consume))

    def joint_header(self):
        """
        扩展请求头信息
        :return: headers
        """
        try:
            headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
            headers.update(self.mapping_header(self.test_case["RequestHeader"]))
            return headers
        except Exception:
            logger.exception("扩展请求头过程中发生异常，请检查！")

    def dispatch_request(self):
        """
        请求转换器。
        :return:
        """
        response = None
        request_method = str(self.test_case["Method"]).lower()
        try:
            if request_method == 'get':
                response = self.send_get()
            if request_method == 'post':
                response = self.send_post()
            if request_method == "put":
                response = self.send_put()
            if request_method == "patch":
                response = self.send_patch()
            if request_method == "delete":
                response = self.send_delete()
            return response
        except Exception:
            logger.exception('[Exception]：发送{}接口请求过程中发生异常！'.format(request_method.upper()))

    def send_delete(self):
        """
        发送DELETE请求(读取TestCase中字段值)
        :return:
        """
        try:
            main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
            query_string = urlencode(json.loads(self.test_case["RequestParam"]))
            response = self.delete(
                url=(main_url + "?" + query_string) if query_string != "" else main_url,
                headers=self.joint_header()
            )
            return response
        except Exception:
            logger.exception('[Exception]：发送DELETE接口请求过程中发生异常！')

    def send_patch(self):
        """
        发送PATCH请求(读取TestCase中字段值)
        :return:
        """
        response = None
        query_patch = self.test_case["RequestParam"]
        try:
            if query_patch == "":
                response = self.patch(
                    url=urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]),
                    headers=self.joint_header(),
                    data=self.mapping_data(self.test_case["Consumes"]))
            if query_patch != "":
                main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
                query_string = urlencode(json.loads(self.test_case["RequestParam"]))
                response = self.patch(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(),
                    data=self.mapping_data(self.test_case["Consumes"]))
            return response
        except Exception:
            logger.exception('[Exception]：发送PATCH接口请求过程中发生异常！')

    def send_put(self):
        """
        发送PUT请求(读取TestCase中字段值)
        :return:
        """
        response = None
        query_put = self.test_case["RequestParam"]
        try:
            if query_put == "":
                response = self.put(
                    url=urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]),
                    headers=self.joint_header(),
                    data=self.mapping_data(self.test_case["Consumes"]))
            if query_put != "":
                main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
                query_string = urlencode(json.loads(self.test_case["RequestParam"]))
                response = self.put(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(),
                    data=self.mapping_data(self.test_case["Consumes"]))
            return response
        except Exception:
            logger.exception('[Exception]：发送PUT接口请求过程中发生异常！')

    def send_post(self):
        """
        发送POST请求(读取TestCase中字段值)
        :return:
        """
        response = None
        query_post = self.test_case["RequestParam"]
        try:
            if query_post == "":
                response = self.post(
                    url=urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]),
                    headers=self.joint_header(),
                    data=self.mapping_data(self.test_case["Consumes"]))
            if query_post != "":
                main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
                query_string = urlencode(json.loads(self.test_case["RequestParam"]))
                response = self.post(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(),
                    data=self.mapping_data(self.test_case["Consumes"]))
            return response
        except Exception:
            logger.exception('[Exception]：发送POST接口请求过程中发生异常！')

    def send_get(self):
        """
        发送GET请求(读取TestCase中字段值)
        :return:
        """
        try:
            main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
            query_string = urlencode(json.loads(self.test_case["RequestParam"]))
            response = self.get(
                url=(main_url + "?" + query_string) if query_string != "" else main_url,
                headers=self.joint_header()
            )
            return response
        except Exception:
            logger.exception('[Exception]：发送GET接口请求过程中发生异常！')


class SingletonTestCaseRequestTool(RequestTool):
    """
    测试用例HTTP(S)请求工具类 ~ 支持请求扩展，但不支持接口依赖。
    描述：该工具类支持header/param/data请求扩展，但不支持接口依赖。
    """

    def __init__(self, test_case_schema=None, global_session=False):
        """
        初始化测试用例请求工具类
        :param test_case_schema: 测试用例
        :param global_session: 是否开启全局Session(默认False)
        """
        RequestTool.__init__(self, global_session=global_session)
        if isinstance(test_case_schema, dict):
            self.test_case = test_case_schema
        else:
            logger.exception("参数test_case_schema必须用字典方式入参！")

    def mapping_header(self, headers):
        """
        转换请求头RequestHeader
        :param headers: 请求头RequestHeader
        :return: dict
        """
        try:
            if headers == "":
                return {}
            else:
                return json.loads(self.test_case["RequestHeader"])
        except Exception:
            logger.exception("转换请求头RequestHeader过程中发生异常，请检查！")

    def mapping_data(self, data):
        """
        转换请求体RequestData
        :param data: 请求体RequestData
        :return: dict
        """
        try:
            if data == "":
                return {}
            else:
                return json.loads(self.test_case["RequestData"])
        except Exception:
            logger.exception("转换请求体RequestData过程中发生异常，请检查！")

    def joint_header(self, **kw):
        """
        扩展请求头信息
        :param kw: 额外请求头信息，字典Update注意键相同，后边会覆盖前边
        :return: headers
        """
        try:
            if kw == {}:
                headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
                headers.update(self.mapping_header(self.test_case["RequestHeader"]))
                return headers
            if kw != {} and kw.__contains__("header"):
                headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
                headers.update(self.mapping_header(self.test_case["RequestHeader"]))
                headers.update(kw.get("header"))
                return headers
            else:
                logger.warning('[WARNING]：请求头kw当前仅支持"header={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求头过程中发生异常，请检查！")

    def joint_param(self, **kw):
        """
        扩展请求参数信息
        :param kw: 额外请求参数信息
        :return: param
        """
        try:
            if self.test_case["RequestParam"] == "":
                self.test_case["RequestParam"] = "{}"
            if str(self.test_case["RequestParam"]).__contains__("="):
                self.test_case["RequestParam"] = json.dumps(param_to_dict(self.test_case["RequestParam"]))
            if kw == {}:
                param = urlencode(json.loads(self.test_case["RequestParam"]))
                return param
            if kw != {} and kw.__contains__("param"):
                param_dict = json.loads(self.test_case["RequestParam"])
                param_dict.update(kw.get("param"))
                param = urlencode(param_dict)
                return param
            else:
                logger.warning('[WARNING]：请求参数kw当前仅支持"param={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求参数过程中发生异常，请检查！")

    def joint_data(self, consumes, **kw):
        """
        扩展请求体信息
        :param consumes: 请求头类型
        :param kw: 额外请求体信息
        :return: data
        """
        consume = str(consumes).lower()
        try:
            if consume not in ["application/x-www-form-urlencoded", "application/json", "*/*"]:
                raise InvalidConsumesError
            if consume == "application/x-www-form-urlencoded":
                if kw == {}:
                    request_data = urlencode(self.mapping_data(self.test_case["RequestData"]))
                    return request_data
                if kw != {} and kw.__contains__("data"):
                    data_dict = self.mapping_data(self.test_case["RequestData"])
                    data_dict.update(kw.get("data"))
                    data = urlencode(data_dict)
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/json" or consume == "*/*":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    data = json.dumps(request_data)
                    if self.test_case["RequestData"] == "" and data == "{}":
                        data = ""
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    if isinstance(request_data, dict):
                        request_data.update(kw.get("data"))
                        data = json.dumps(request_data)
                        if self.test_case["RequestData"] == "" and data == "{}":
                            data = ""
                        return data
                    if isinstance(request_data, list):
                        logger.warning('[WARNING]：当前请求体为列表形式，不支持kw形式的请求体外部参数扩展！')
                        data = json.dumps(request_data)
                        return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
        except InvalidConsumesError:
            logger.exception('当前暂时不支持请求头"{}"类型的数据解析！'.format(consume))
        except Exception:
            logger.exception("扩展请求体过程中发生异常，请检查！")

    def dispatch_request(self, **others):
        """
        请求转换器。
        :param others: 额外信息,传参形式必须包含{"header":{},"data":{},"param":{}}
        :return:
        """
        response = None
        request_method = str(self.test_case["Method"]).lower()
        try:
            if request_method == 'get':
                response = self.send_get(**others)
            if request_method == 'post':
                response = self.send_post(**others)
            if request_method == "put":
                response = self.send_put(**others)
            if request_method == "patch":
                response = self.send_patch(**others)
            if request_method == "delete":
                response = self.send_delete(**others)
            return response
        except Exception:
            logger.exception('[Exception]：发送{}接口请求过程中发生异常！'.format(request_method.upper()))

    def send_delete(self, **kw):
        """
        发送DELETE请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        try:
            main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
            query_string = self.joint_param(**kw)
            response = self.delete(
                url=(main_url + "?" + query_string) if query_string != "" else main_url,
                headers=self.joint_header(**kw)
            )
            return response
        except Exception:
            logger.exception('[Exception]：发送DELETE接口请求过程中发生异常！')

    def send_patch(self, **kw):
        """
        发送PATCH请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        response = None
        query_patch = self.test_case["RequestParam"]
        try:
            if query_patch == "":
                response = self.patch(
                    url=urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]),
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw))
            if query_patch != "":
                main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
                query_string = self.joint_param(**kw)
                response = self.patch(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw))
            return response
        except Exception:
            logger.exception('[Exception]：发送PATCH接口请求过程中发生异常！')

    def send_put(self, **kw):
        """
        发送PUT请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        response = None
        query_put = self.test_case["RequestParam"]
        try:
            if query_put == "":
                response = self.put(
                    url=urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]),
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw))
            if query_put != "":
                main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
                query_string = self.joint_param(**kw)
                response = self.put(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw))
            return response
        except Exception:
            logger.exception('[Exception]：发送PUT接口请求过程中发生异常！')

    def send_post(self, **kw):
        """
        发送POST请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        response = None
        query_post = self.test_case["RequestParam"]
        try:
            if query_post == "":
                response = self.post(
                    url=urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]),
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw))
            if query_post != "":
                main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
                query_string = self.joint_param(**kw)
                response = self.post(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw))
            return response
        except Exception:
            logger.exception('[Exception]：发送POST接口请求过程中发生异常！')

    def send_get(self, **kw):
        """
        发送GET请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        try:
            main_url = urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"])
            query_string = self.joint_param(**kw)
            response = self.get(
                url=(main_url + "?" + query_string) if query_string != "" else main_url,
                headers=self.joint_header(**kw)
            )
            return response
        except Exception:
            logger.exception('[Exception]：发送GET接口请求过程中发生异常！')


class AdvanceTestCaseRequestTool(RequestTool):
    """
    测试用例HTTP(S)请求工具类 ~ 支持请求扩展及接口依赖。
    描述：该工具类支持path/header/param/data请求扩展，同时支持接口依赖。
    """

    def __init__(self, test_case_schema=None, realtime_dependency=None, global_session=False):
        """
        初始化测试用例请求工具类
        :param test_case_schema: 测试用例
        :param realtime_dependency: 测试依赖
        :param global_session: 是否开启全局Session(默认False)
        """
        RequestTool.__init__(self, global_session=global_session)
        if isinstance(test_case_schema, dict) and isinstance(realtime_dependency, dict):
            self.test_case = test_case_schema
            self.realtime_dependency = realtime_dependency
            self.dependency_fail_info_dict = {}
            self.request_dict = dict(paths="", headers="", params="", datas="")
        else:
            logger.exception("所有参数均必须用字典方式入参！")

    def mapping_path(self, paths):
        """
        转换请求路径RequestPath
        :param paths: 请求路径RequestPath
        :return: dict
        """
        try:
            if paths == "":
                return {}
            else:
                return json.loads(self.test_case["RequestPath"])
        except Exception:
            logger.exception("转换请求路径RequestPath过程中发生异常，请检查！")

    def mapping_header(self, headers):
        """
        转换请求头RequestHeader
        :param headers: 请求头RequestHeader
        :return: dict
        """
        try:
            if headers == "":
                return {}
            else:
                return json.loads(self.test_case["RequestHeader"])
        except Exception:
            logger.exception("转换请求头RequestHeader过程中发生异常，请检查！")

    def mapping_param(self, params):
        """
        转换请求参数RequestParam
        :param params: 请求参数RequestParam
        :return: dict
        """
        try:
            if params == "":
                return {}
            elif str(self.test_case["RequestParam"]).__contains__("="):
                return param_to_dict(self.test_case["RequestParam"])
            else:
                return json.loads(self.test_case["RequestParam"])
        except Exception:
            logger.exception("转换请求参数RequestParam过程中发生异常，请检查！")

    def mapping_data(self, data):
        """
        转换请求体RequestData
        :param data: 请求体RequestData
        :return: dict
        """
        try:
            if data == "":
                return {}
            else:
                if self.test_case['Consumes'] == "application/xml":
                    return json.loads(xml_to_json(self.test_case["RequestData"]))
                else:
                    return json.loads(self.test_case["RequestData"])
        except Exception:
            logger.exception("转换请求体RequestData过程中发生异常，请检查！")

    def mapping_dependency(self, path=False, header=False, param=False, data=False):
        """
        转换请求依赖项DependencyInfo ~ 接口响应依赖方式
        :param path: 开启请求路径依赖
        :param header: 开启请求头依赖
        :param param: 开启请求参数依赖
        :param data: 开启请求体依赖
        :return: dict
        """
        try:
            if self.test_case["DependencyInfo"] == "":
                return {}
            if self.test_case["DependencyInfo"] != "" and path is True:
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                request_path = self.mapping_path(self.test_case["RequestPath"])
                for url, depend in dependency_dict.items():
                    if depend["to_path"] != {}:
                        for req_dict_expression, res_jsonpath_expression in depend["to_path"].items():
                            req_dict_value = str(req_dict_expression).replace("$", "request_path")
                            if self.realtime_dependency.__contains__(url):
                                res_jsonpath_value = jsonpath(self.realtime_dependency.get(url),
                                                              res_jsonpath_expression)
                                if res_jsonpath_value is False:
                                    logger.warning(
                                        '[WARNING]：【请求路径数据依赖】依赖接口"{}"响应数据的jsonPath表达式"{}"未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！'.format(
                                            url,
                                            res_jsonpath_expression))
                                    self.dependency_fail_info_dict[
                                        'to_path'] = '请求路径存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                                else:
                                    # 因为总是使用字符串替换路径参数变量，所以无需使用value_by_type同步类型。
                                    res_jsonpath_value = res_jsonpath_value[0]
                                    if isinstance(res_jsonpath_value, str):
                                        res_jsonpath_value = "".join(["'", res_jsonpath_value, "'"])
                                    exec_expression = "".join([req_dict_value, "=", str(res_jsonpath_value)])
                                    exec(exec_expression)
                                    logger.info(
                                        '[Dependency]：【请求路径数据依赖】当前接口"{}"的请求路径完成一次依赖接口"{}"的响应数据替换，替换表达式为"{}"'.format(
                                            self.test_case["UrlPath"], url,
                                            exec_expression))
                            else:
                                logger.warning('[WARNING]：当前接口响应缓存字典中不存在依赖接口"{}"的任何响应数据！'.format(url))
                                self.dependency_fail_info_dict[
                                    'to_path'] = '请求路径存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                return request_path
            elif self.test_case["DependencyInfo"] != "" and header is True:
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                request_header = self.mapping_header(self.test_case["RequestHeader"])
                for url, depend in dependency_dict.items():
                    if depend["to_header"] != {}:
                        for req_dict_expression, res_jsonpath_expression in depend["to_header"].items():
                            req_dict_value = str(req_dict_expression).replace("$", "request_header")
                            if self.realtime_dependency.__contains__(url):
                                res_jsonpath_value = jsonpath(self.realtime_dependency.get(url),
                                                              res_jsonpath_expression)
                                if res_jsonpath_value is False:
                                    logger.warning(
                                        '[WARNING]：【请求头数据依赖】依赖接口"{}"响应数据的jsonPath表达式"{}"未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！'.format(
                                            url,
                                            res_jsonpath_expression))
                                    self.dependency_fail_info_dict[
                                        'to_header'] = '请求头存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                                else:
                                    res_jsonpath_value = value_by_type(eval(req_dict_value), res_jsonpath_value[0])
                                    if isinstance(res_jsonpath_value, str):
                                        res_jsonpath_value = "".join(["'", res_jsonpath_value, "'"])
                                    exec_expression = "".join([req_dict_value, "=", str(res_jsonpath_value)])
                                    exec(exec_expression)
                                    logger.info(
                                        '[Dependency]：【请求头数据依赖】当前接口"{}"的请求头完成一次依赖接口"{}"的响应数据替换，替换表达式为"{}"'.format(
                                            self.test_case["UrlPath"], url,
                                            exec_expression))
                            else:
                                logger.warning('[WARNING]：当前接口响应缓存字典中不存在依赖接口"{}"的任何响应数据！'.format(url))
                                self.dependency_fail_info_dict[
                                    'to_header'] = '请求头存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                return request_header
            elif self.test_case["DependencyInfo"] != "" and param is True:
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                request_param = self.mapping_param(self.test_case["RequestParam"])
                for url, depend in dependency_dict.items():
                    if depend["to_param"] != {}:
                        for req_dict_expression, res_jsonpath_expression in depend["to_param"].items():
                            req_dict_value = str(req_dict_expression).replace("$", "request_param")
                            if self.realtime_dependency.__contains__(url):
                                res_jsonpath_value = jsonpath(self.realtime_dependency.get(url),
                                                              res_jsonpath_expression)
                                if res_jsonpath_value is False:
                                    logger.warning(
                                        '[WARNING]：【请求参数数据依赖】依赖接口"{}"响应数据的jsonPath表达式"{}"未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！'.format(
                                            url,
                                            res_jsonpath_expression))
                                    self.dependency_fail_info_dict[
                                        'to_param'] = '请求参数存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                                else:
                                    res_jsonpath_value = value_by_type(eval(req_dict_value), res_jsonpath_value[0])
                                    if isinstance(res_jsonpath_value, str):
                                        res_jsonpath_value = "".join(["'", res_jsonpath_value, "'"])
                                    exec_expression = "".join([req_dict_value, "=", str(res_jsonpath_value)])
                                    exec(exec_expression)
                                    logger.info(
                                        '[Dependency]：【请求参数数据依赖】当前接口"{}"的请求参数完成一次依赖接口"{}"的响应数据替换，替换表达式为"{}"'.format(
                                            self.test_case["UrlPath"], url,
                                            exec_expression))
                            else:
                                logger.warning('[WARNING]：当前接口响应缓存字典中不存在依赖接口"{}"的任何响应数据！'.format(url))
                                self.dependency_fail_info_dict[
                                    'to_param'] = '请求参数存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                return request_param
            elif self.test_case["DependencyInfo"] != "" and data is True:
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                request_data = self.mapping_data(self.test_case["RequestData"])
                for url, depend in dependency_dict.items():
                    if depend["to_data"] != {}:
                        for req_dict_expression, res_jsonpath_expression in depend["to_data"].items():
                            req_dict_value = str(req_dict_expression).replace("$", "request_data")
                            if self.realtime_dependency.__contains__(url):
                                res_jsonpath_value = jsonpath(self.realtime_dependency.get(url),
                                                              res_jsonpath_expression)
                                if res_jsonpath_value is False:
                                    logger.warning(
                                        '[WARNING]：【请求体数据依赖】依赖接口"{}"响应数据的jsonPath表达式"{}"未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！'.format(
                                            url,
                                            res_jsonpath_expression))
                                    self.dependency_fail_info_dict[
                                        'to_data'] = '请求体存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                                else:
                                    res_jsonpath_value = value_by_type(eval(req_dict_value), res_jsonpath_value[0])
                                    if isinstance(res_jsonpath_value, str):
                                        res_jsonpath_value = "".join(["'", res_jsonpath_value, "'"])
                                    exec_expression = "".join([req_dict_value, "=", str(res_jsonpath_value)])
                                    exec(exec_expression)
                                    logger.info(
                                        '[Dependency]：【请求体数据依赖】当前接口"{}"的请求体完成一次依赖接口"{}"的响应数据替换，替换表达式为"{}"'.format(
                                            self.test_case["UrlPath"], url,
                                            exec_expression))
                            else:
                                logger.warning('[WARNING]：当前接口响应缓存字典中不存在依赖接口"{}"的任何响应数据！'.format(url))
                                self.dependency_fail_info_dict['to_data'] = '请求体存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
                return request_data
            else:
                logger.warning("[WARNING]：当前接口请求存在依赖数据但未被使用，请检查是否开启相关数据依赖开关！")
        except Exception:
            logger.exception("转换依赖项DependencyInfo过程中发生异常，请检查！")

    def joint_path(self, **kw):
        """
        扩展请求路径信息
        :param kw: 额外请求路径信息，字典Update注意键相同，后边会覆盖前边
        :return: paths
        """
        try:
            if kw == {}:
                paths = self.mapping_path(self.test_case["RequestPath"])
                paths.update(self.mapping_dependency(path=True))
                self.request_dict["paths"] = paths
                return paths
            if kw != {} and kw.__contains__("path"):
                paths = self.mapping_path(self.test_case["RequestPath"])
                paths.update(self.mapping_dependency(path=True))
                paths.update(kw.get("path"))
                self.request_dict["paths"] = paths
                return paths
            else:
                logger.warning('[WARNING]：请求路径kw当前仅支持"path={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求路径过程中发生异常，请检查！")

    def joint_header(self, **kw):
        """
        扩展请求头信息
        :param kw: 额外请求头信息，字典Update注意键相同，后边会覆盖前边
        :return: headers
        """
        try:
            if kw == {}:
                headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
                headers.update(self.mapping_header(self.test_case["RequestHeader"]))
                headers.update(self.mapping_dependency(header=True))
                self.request_dict["headers"] = headers.copy()
                if self.test_case["Consumes"] == "multipart/form-data":
                    headers.pop("Content-Type")
                return headers
            if kw != {} and kw.__contains__("header"):
                headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
                headers.update(self.mapping_header(self.test_case["RequestHeader"]))
                headers.update(self.mapping_dependency(header=True))
                headers.update(kw.get("header"))
                self.request_dict["headers"] = headers.copy()
                if self.test_case["Consumes"] == "multipart/form-data":
                    headers.pop("Content-Type")
                return headers
            else:
                logger.warning('[WARNING]：请求头kw当前仅支持"header={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求头过程中发生异常，请检查！")

    def joint_param(self, **kw):
        """
        扩展请求参数信息
        :param kw: 额外请求参数信息
        :return: param
        """
        try:
            if kw == {}:
                request_param = self.mapping_param(self.test_case["RequestParam"])
                request_param.update(self.mapping_dependency(param=True))
                param = urlencode(request_param)
                self.request_dict["params"] = param
                return param
            if kw != {} and kw.__contains__("param"):
                request_param = self.mapping_param(self.test_case["RequestParam"])
                request_param.update(self.mapping_dependency(param=True))
                request_param.update(kw.get("param"))
                param = urlencode(request_param)
                self.request_dict["params"] = param
                return param
            else:
                logger.warning('[WARNING]：请求参数kw当前仅支持"param={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求参数过程中发生异常，请检查！")

    def joint_data(self, consumes, **kw):
        """
        扩展请求体信息
        :param consumes: 请求头类型
        :param kw: 额外请求体信息
        :return: data
        """
        consume = str(consumes).lower()
        try:
            if consume not in ["multipart/form-data", "application/x-www-form-urlencoded", "application/xml",
                               "application/json", "*/*"]:
                raise InvalidConsumesError
            if consume == "multipart/form-data":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependency(data=True))
                    data = request_data
                    self.request_dict["datas"] = data
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependency(data=True))
                    request_data.update(kw.get("data"))
                    data = request_data
                    self.request_dict["datas"] = data
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/x-www-form-urlencoded":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependency(data=True))
                    data = urlencode(request_data)
                    self.request_dict["datas"] = data
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependency(data=True))
                    request_data.update(kw.get("data"))
                    data = urlencode(request_data)
                    self.request_dict["datas"] = data
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/xml":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependency(data=True))
                    data = json_to_xml(request_data)
                    self.request_dict["datas"] = data
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependency(data=True))
                    request_data.update(kw.get("data"))
                    data = json_to_xml(request_data)
                    self.request_dict["datas"] = data
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/json" or consume == "*/*":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    if isinstance(request_data, dict):
                        request_data.update(self.mapping_dependency(data=True))
                        data = json.dumps(request_data)
                        if self.test_case["RequestData"] == "" and data == "{}":
                            data = ""
                        self.request_dict["datas"] = data
                        return data
                    if isinstance(request_data, list):
                        mapping_data = self.mapping_dependency(data=True)
                        if mapping_data == {}:
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        elif isinstance(mapping_data, list):
                            for index in range(request_data.__len__()):
                                request_data[index].update(mapping_data[index])
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        else:
                            logger.warning('[WARNING]：当前列表形式请求体依赖数据更新失败，将跳过依赖数据替换，请检查失败原因！')
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    if isinstance(request_data, dict):
                        request_data.update(self.mapping_dependency(data=True))
                        request_data.update(kw.get("data"))
                        data = json.dumps(request_data)
                        if self.test_case["RequestData"] == "" and data == "{}":
                            data = ""
                        self.request_dict["datas"] = data
                        return data
                    if isinstance(request_data, list):
                        logger.warning('[WARNING]：当前请求体为列表形式，不支持kw形式的请求体外部参数扩展！')
                        mapping_data = self.mapping_dependency(data=True)
                        if mapping_data == {}:
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        elif isinstance(mapping_data, list):
                            for index in range(request_data.__len__()):
                                request_data[index].update(mapping_data[index])
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        else:
                            logger.warning('[WARNING]：当前列表形式请求体依赖数据更新失败，将跳过依赖数据替换，请检查失败原因！')
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
        except InvalidConsumesError:
            logger.exception('当前暂时不支持请求头"{}"类型的数据解析！'.format(consume))
        except Exception:
            logger.exception("扩展请求体过程中发生异常，请检查！")

    def joint_file(self, consumes):
        """
        扩展请求文件信息（仅针对multipart/form-data）
        :param consumes: 请求头类型
        :return: files
        """
        consume = str(consumes).lower()
        try:
            if consume != "multipart/form-data":
                return None
            else:
                files = [(file[0], open(file[1], 'rb')) for file in eval(self.test_case["RequestFile"])]
                return files
        except Exception:
            logger.exception("扩展请求文件过程中发生异常，请检查！")

    def dispatch_request(self, **others):
        """
        请求转换器。
        :param others: 额外信息,传参形式必须包含{"header":{},"data":{},"param":{}}
        :return:
        """
        response = None
        request_method = str(self.test_case["Method"]).lower()
        try:
            if request_method == 'get':
                response = self.send_get(**others)
            if request_method == 'post':
                response = self.send_post(**others)
            if request_method == "put":
                response = self.send_put(**others)
            if request_method == "patch":
                response = self.send_patch(**others)
            if request_method == "delete":
                response = self.send_delete(**others)
            return response
        except Exception:
            logger.exception('[Exception]：发送{}接口请求过程中发生异常！'.format(request_method.upper()))

    def send_delete(self, **kw):
        """
        发送DELETE请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        try:
            main_url = self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw)
            query_string = self.joint_param(**kw)
            response = self.delete(
                url=(main_url + "?" + query_string) if query_string != "" else main_url,
                headers=self.joint_header(**kw)
            )
            return response
        except Exception:
            logger.exception('[Exception]：发送DELETE接口请求过程中发生异常！')

    def send_patch(self, **kw):
        """
        发送PATCH请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        response = None
        query_patch = self.test_case["RequestParam"]
        try:
            if query_patch == "":
                response = self.patch(
                    url=self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw),
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw),
                    files=self.joint_file(self.test_case["Consumes"]))
            if query_patch != "":
                main_url = self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw)
                query_string = self.joint_param(**kw)
                response = self.patch(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw),
                    files=self.joint_file(self.test_case["Consumes"]))
            return response
        except Exception:
            logger.exception('[Exception]：发送PATCH接口请求过程中发生异常！')

    def send_put(self, **kw):
        """
        发送PUT请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        response = None
        query_put = self.test_case["RequestParam"]
        try:
            if query_put == "":
                response = self.put(
                    url=self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw),
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw),
                    files=self.joint_file(self.test_case["Consumes"]))
            if query_put != "":
                main_url = self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw)
                query_string = self.joint_param(**kw)
                response = self.put(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw),
                    files=self.joint_file(self.test_case["Consumes"]))
            return response
        except Exception:
            logger.exception('[Exception]：发送PUT接口请求过程中发生异常！')

    def send_post(self, **kw):
        """
        发送POST请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        response = None
        query_post = self.test_case["RequestParam"]
        try:
            if query_post == "":
                response = self.post(
                    url=self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw),
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw),
                    files=self.joint_file(self.test_case["Consumes"]))
            if query_post != "":
                main_url = self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw)
                query_string = self.joint_param(**kw)
                response = self.post(
                    url=(main_url + "?" + query_string) if query_string != "" else main_url,
                    headers=self.joint_header(**kw),
                    data=self.joint_data(self.test_case["Consumes"], **kw),
                    files=self.joint_file(self.test_case["Consumes"]))
            return response
        except Exception:
            logger.exception('[Exception]：发送POST接口请求过程中发生异常！')

    def send_get(self, **kw):
        """
        发送GET请求(读取TestCase中字段值)
        :param kw: 额外信息
        :return:
        """
        try:
            main_url = self.url_identity(urljoin(self.test_case["BaseUrl"], self.test_case["UrlPath"]), **kw)
            query_string = self.joint_param(**kw)
            response = self.get(
                url=(main_url + "?" + query_string) if query_string != "" else main_url,
                headers=self.joint_header(**kw)
            )
            return response
        except Exception:
            logger.exception('[Exception]：发送GET接口请求过程中发生异常！')

    def url_identity(self, url, **kw):
        """
        识别并替换请求url中的路径参数
        :param url: 请求url
        :param kw: 额外请求路径信息，字典Update注意键相同，后边会覆盖前边
        :return: paths
        """
        try:
            url_path_vars = re.findall(r"\{(\S+?)\}", str(url))
            if url_path_vars == []:
                return url
            else:
                paths = self.joint_path(**kw)
                url_path_vars_set = set(url_path_vars)
                path_key_set = set(list(paths.keys()))
                verify_path_vars_set = url_path_vars_set - path_key_set
                if verify_path_vars_set == set():
                    for path_var in url_path_vars_set:
                        url = url.replace("{" + str(path_var) + "}", str(paths.get(path_var)))
                    return url
                else:
                    logger.warning(
                        '[WARNING]：当前接口RequestPath中缺少必要的请求路径参数赋值信息，缺少项为{}'.format(list(verify_path_vars_set)))
        except Exception:
            logger.warning('[WARNING]：识别并替换请求路径参数过程中发生异常，请检查！')

    @property
    def check_dependency_fail_info_dict(self):
        """
        检查数据依赖失败信息字典
        :return:
        """
        if self.dependency_fail_info_dict == {}:
            return False
        else:
            return True

    @property
    def fetch_request_dict(self):
        """
        获取请求信息字典数据
        :return:
        """
        return self.request_dict


class SuperTestCaseRequestTool(AdvanceTestCaseRequestTool):
    """
    测试用例HTTP(S)请求工具类 ~ 支持请求扩展及多种依赖，如常量、类SpEL表达式、接口依赖及函数依赖表达式。
    描述：该工具类支持path/header/param/data请求扩展，同时支持以上形式数据依赖。
    """

    def __init__(self, test_case_schema=None, realtime_dependency=None, global_session=False):
        """
        初始化测试用例请求工具类
        :param test_case_schema: 测试用例
        :param realtime_dependency: 测试依赖
        :param global_session: 是否开启全局Session(默认False)
        """
        AdvanceTestCaseRequestTool.__init__(self, test_case_schema=test_case_schema,
                                            realtime_dependency=realtime_dependency,
                                            global_session=global_session)

    def mapping_dependencies(self, path=False, header=False, param=False, data=False):
        """
        转换请求依赖项DependencyInfo ~ 支持常量、类SpEL表达式、接口依赖表达式、函数依赖表达式
        :param path: 开启请求路径依赖
        :param header: 开启请求头依赖
        :param param: 开启请求参数依赖
        :param data: 开启请求体依赖
        :return: dict
        """
        try:
            if self.test_case["DependencyInfo"] == "":
                return {}
            if self.test_case["DependencyInfo"] != "" and path is True:
                request_path = self.mapping_path(self.test_case["RequestPath"])
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                to_path_dict = dependency_dict.get("to_path")
                if to_path_dict != {}:
                    for req_dict_expression, dependency_expression in to_path_dict.items():
                        req_dict_value = str(req_dict_expression).replace("$", "request_path")
                        expression_value = self.expr_identity(param_expr=dependency_expression, maintainer="请求路径")
                        if expression_value not in ["Missing Dependency Url", "JsonPath Value is False"]:
                            # 因为总是使用字符串替换路径参数变量，所以无需使用value_by_type同步类型。
                            if isinstance(expression_value, str):
                                expression_value = "".join(["'", expression_value, "'"])
                            exec_expression = "".join([req_dict_value, "=", str(expression_value)])
                            exec(exec_expression)
                            logger.info(
                                '[Success]：【请求路径数据依赖】当前接口"{}"的请求路径完成一次数据依赖替换，替换表达式为"{}"'.format(
                                    self.test_case["UrlPath"], exec_expression))
                        else:
                            continue
                return request_path
            elif self.test_case["DependencyInfo"] != "" and header is True:
                request_header = self.mapping_header(self.test_case["RequestHeader"])
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                to_header_dict = dependency_dict.get("to_header")
                if to_header_dict != {}:
                    for req_dict_expression, dependency_expression in to_header_dict.items():
                        req_dict_value = str(req_dict_expression).replace("$", "request_header")
                        expression_value = self.expr_identity(param_expr=dependency_expression, maintainer="请求头")
                        if expression_value not in ["Missing Dependency Url", "JsonPath Value is False"]:
                            expression_value = value_by_type(eval(req_dict_value), expression_value)
                            if isinstance(expression_value, str):
                                expression_value = "".join(["'", expression_value, "'"])
                            exec_expression = "".join([req_dict_value, "=", str(expression_value)])
                            exec(exec_expression)
                            logger.info(
                                '[Success]：【请求头数据依赖】当前接口"{}"的请求头完成一次数据依赖替换，替换表达式为"{}"'.format(
                                    self.test_case["UrlPath"], exec_expression))
                        else:
                            continue
                return request_header
            elif self.test_case["DependencyInfo"] != "" and param is True:
                request_param = self.mapping_param(self.test_case["RequestParam"])
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                to_param_dict = dependency_dict.get("to_param")
                if to_param_dict != {}:
                    for req_dict_expression, dependency_expression in to_param_dict.items():
                        req_dict_value = str(req_dict_expression).replace("$", "request_param")
                        expression_value = self.expr_identity(param_expr=dependency_expression, maintainer="请求参数")
                        if expression_value not in ["Missing Dependency Url", "JsonPath Value is False"]:
                            expression_value = value_by_type(eval(req_dict_value), expression_value)
                            if isinstance(expression_value, str):
                                expression_value = "".join(["'", expression_value, "'"])
                            exec_expression = "".join([req_dict_value, "=", str(expression_value)])
                            exec(exec_expression)
                            logger.info(
                                '[Success]：【请求参数数据依赖】当前接口"{}"的请求参数完成一次数据依赖替换，替换表达式为"{}"'.format(
                                    self.test_case["UrlPath"], exec_expression))
                        else:
                            continue
                return request_param
            elif self.test_case["DependencyInfo"] != "" and data is True:
                request_data = self.mapping_data(self.test_case["RequestData"])
                dependency_dict = json.loads(self.test_case["DependencyInfo"])[0]
                to_data_dict = dependency_dict.get("to_data")
                if to_data_dict != {}:
                    for req_dict_expression, dependency_expression in to_data_dict.items():
                        req_dict_value = str(req_dict_expression).replace("$", "request_data")
                        expression_value = self.expr_identity(param_expr=dependency_expression, maintainer="请求体")
                        if expression_value not in ["Missing Dependency Url", "JsonPath Value is False"]:
                            expression_value = value_by_type(eval(req_dict_value), expression_value)
                            if isinstance(expression_value, str):
                                expression_value = "".join(["'", expression_value, "'"])
                            exec_expression = "".join([req_dict_value, "=", str(expression_value)])
                            exec(exec_expression)
                            logger.info(
                                '[Success]：【请求体数据依赖】当前接口"{}"的请求体完成一次数据依赖替换，替换表达式为"{}"'.format(
                                    self.test_case["UrlPath"], exec_expression))
                        else:
                            continue
                return request_data
            else:
                logger.warning("[WARNING]：当前接口请求存在依赖数据但未被使用，请检查是否开启相关数据依赖开关！")
        except Exception:
            logger.exception("转换依赖项DependencyInfo过程中发生异常，请检查！")

    def joint_path(self, **kw):
        """
        扩展请求路径信息
        :param kw: 额外请求路径信息，字典Update注意键相同，后边会覆盖前边
        :return: paths
        """
        try:
            if kw == {}:
                paths = self.mapping_path(self.test_case["RequestPath"])
                paths.update(self.mapping_dependencies(path=True))
                self.request_dict["paths"] = paths
                return paths
            if kw != {} and kw.__contains__("path"):
                paths = self.mapping_path(self.test_case["RequestPath"])
                paths.update(self.mapping_dependencies(path=True))
                paths.update(kw.get("path"))
                self.request_dict["paths"] = paths
                return paths
            else:
                logger.warning('[WARNING]：请求路径kw当前仅支持"path={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求路径过程中发生异常，请检查！")

    def joint_header(self, **kw):
        """
        扩展请求头信息
        :param kw: 额外请求头信息，字典Update注意键相同，后边会覆盖前边
        :return: headers
        """
        try:
            if kw == {}:
                headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
                headers.update(self.mapping_header(self.test_case["RequestHeader"]))
                headers.update(self.mapping_dependencies(header=True))
                self.request_dict["headers"] = headers.copy()
                if self.test_case["Consumes"] == "multipart/form-data":
                    headers.pop("Content-Type")
                return headers
            if kw != {} and kw.__contains__("header"):
                headers = {"Content-Type": "{};charset=UTF-8".format(self.test_case["Consumes"])}
                headers.update(self.mapping_header(self.test_case["RequestHeader"]))
                headers.update(self.mapping_dependencies(header=True))
                headers.update(kw.get("header"))
                self.request_dict["headers"] = headers.copy()
                if self.test_case["Consumes"] == "multipart/form-data":
                    headers.pop("Content-Type")
                return headers
            else:
                logger.warning('[WARNING]：请求头kw当前仅支持"header={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求头过程中发生异常，请检查！")

    def joint_param(self, **kw):
        """
        扩展请求参数信息
        :param kw: 额外请求参数信息
        :return: param
        """
        try:
            if kw == {}:
                request_param = self.mapping_param(self.test_case["RequestParam"])
                request_param.update(self.mapping_dependencies(param=True))
                param = urlencode(request_param)
                self.request_dict["params"] = param
                return param
            if kw != {} and kw.__contains__("param"):
                request_param = self.mapping_param(self.test_case["RequestParam"])
                request_param.update(self.mapping_dependencies(param=True))
                request_param.update(kw.get("param"))
                param = urlencode(request_param)
                self.request_dict["params"] = param
                return param
            else:
                logger.warning('[WARNING]：请求参数kw当前仅支持"param={}"形式键值传递！')
        except Exception:
            logger.exception("扩展请求参数过程中发生异常，请检查！")

    def joint_data(self, consumes, **kw):
        """
        扩展请求体信息
        :param consumes: 请求头类型
        :param kw: 额外请求体信息
        :return: data
        """
        consume = str(consumes).lower()
        try:
            if consume not in ["multipart/form-data", "application/x-www-form-urlencoded", "application/xml",
                               "application/json", "*/*"]:
                raise InvalidConsumesError
            if consume == "multipart/form-data":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependencies(data=True))
                    data = request_data
                    self.request_dict["datas"] = data
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependencies(data=True))
                    request_data.update(kw.get("data"))
                    data = request_data
                    self.request_dict["datas"] = data
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/x-www-form-urlencoded":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependencies(data=True))
                    data = urlencode(request_data)
                    self.request_dict["datas"] = data
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependencies(data=True))
                    request_data.update(kw.get("data"))
                    data = urlencode(request_data)
                    self.request_dict["datas"] = data
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/xml":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependencies(data=True))
                    data = json_to_xml(request_data)
                    self.request_dict["datas"] = data
                    return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    request_data.update(self.mapping_dependencies(data=True))
                    request_data.update(kw.get("data"))
                    data = json_to_xml(request_data)
                    self.request_dict["datas"] = data
                    return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
            if consume == "application/json" or consume == "*/*":
                if kw == {}:
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    if isinstance(request_data, dict):
                        request_data.update(self.mapping_dependencies(data=True))
                        data = json.dumps(request_data)
                        if self.test_case["RequestData"] == "" and data == "{}":
                            data = ""
                        self.request_dict["datas"] = data
                        return data
                    if isinstance(request_data, list):
                        mapping_data = self.mapping_dependencies(data=True)
                        if mapping_data == {}:
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        elif isinstance(mapping_data, list):
                            for index in range(request_data.__len__()):
                                request_data[index].update(mapping_data[index])
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        else:
                            logger.warning('[WARNING]：当前列表形式请求体依赖数据更新失败，将跳过依赖数据替换，请检查失败原因！')
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                if kw != {} and kw.__contains__("data"):
                    request_data = self.mapping_data(self.test_case["RequestData"])
                    if isinstance(request_data, dict):
                        request_data.update(self.mapping_dependencies(data=True))
                        request_data.update(kw.get("data"))
                        data = json.dumps(request_data)
                        if self.test_case["RequestData"] == "" and data == "{}":
                            data = ""
                        self.request_dict["datas"] = data
                        return data
                    if isinstance(request_data, list):
                        logger.warning('[WARNING]：当前请求体为列表形式，不支持kw形式的请求体外部参数扩展！')
                        mapping_data = self.mapping_dependencies(data=True)
                        if mapping_data == {}:
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        elif isinstance(mapping_data, list):
                            for index in range(request_data.__len__()):
                                request_data[index].update(mapping_data[index])
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                        else:
                            logger.warning('[WARNING]：当前列表形式请求体依赖数据更新失败，将跳过依赖数据替换，请检查失败原因！')
                            data = json.dumps(request_data)
                            self.request_dict["datas"] = data
                            return data
                else:
                    logger.warning('[WARNING]：请求体kw当前仅支持"data={}"形式键值传递！')
        except InvalidConsumesError:
            logger.exception('当前暂时不支持请求头"{}"类型的数据解析！'.format(consume))
        except Exception:
            logger.exception("扩展请求体过程中发生异常，请检查！")

    def expr_identity(self, param_expr, maintainer):
        """
        解析数据依赖表达式并求值
        :param param_expr: 数据依赖表达式
        :param maintainer: 调用者名称
        :return:
        """
        if re.match(r'^\$\{.*\}$', str(param_expr)):
            expr = param_expr[2:-1]
            result = eval(expr)
            if result is None:
                logger.warning('[WARNING]：【{}数据依赖】数据依赖求值表达式"{}"当前所求值为None，请检查！'.format(maintainer, param_expr))
                self.dependency_fail_identity(maintainer)
            return result
        elif isinstance(param_expr, dict):
            for key, value in param_expr.items():
                if re.match(r'^/{1}.+', key):
                    return self.schema_dependency(maintainer=maintainer, expr_key=key, expr_value=value)
                elif re.match(r'^\$\{.*\}$', key):
                    return self.schema_function(maintainer=maintainer, expr_key=key, expr_value=value)
                else:
                    pass
            logger.warning(
                '[WARNING]：【{}数据依赖】数据依赖字典表达式{}当前未匹配到任何字典规则(字典规则当前支持接口依赖及函数依赖)，请检查！'.format(maintainer, param_expr))
            self.dependency_fail_identity(maintainer)
        else:
            return param_expr

    def schema_dependency(self, maintainer, expr_key, expr_value):
        """
        接口依赖处理
        :param maintainer: 调用者名称
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
                    '[WARNING]：【{}接口依赖】依赖接口"{}"响应数据的jsonPath表达式"{}"未匹配到任何值，请检查依赖接口响应或jsonPath表达式是否正确！'.format(
                        maintainer,
                        url,
                        depend_jsonpath_expression))
                self.dependency_fail_identity(maintainer)
                return "JsonPath Value is False"
            else:
                depend_jsonpath_value = depend_jsonpath_value[0]
                logger.info(
                    '[Dependency]：【{}接口依赖】{}完成一次依赖接口"{}"的响应体期望数据替换，jsonPath表达式为"{}"，获取期望值为{}.'.format(
                        maintainer, maintainer, url, depend_jsonpath_expression, depend_jsonpath_value))
                return depend_jsonpath_value
        else:
            logger.warning('[WARNING]：【{}接口依赖】当前接口响应缓存字典中不存在依赖接口"{}"的任何响应数据！'.format(maintainer, url))
            self.dependency_fail_identity(maintainer)
            return "Missing Dependency Url"

    def schema_function(self, maintainer, expr_key, expr_value):
        """
        函数依赖处理
        :param maintainer: 调用者名称
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
                            param_value_list.append(self.expr_identity(expr_value[param], maintainer))
                        else:
                            logger.warning(
                                '[WARNING]：【{}函数依赖】当前接口预期表达式中依赖函数"{}"的参数"{}"不存在于赋值字典中，请检查！'.format(maintainer,
                                                                                                   function_name,
                                                                                                   param))
                            self.dependency_fail_identity(maintainer)
                            break
                    if param_value_list.__len__() == param_list.__len__():
                        eval_expr = function_name + tuple(param_value_list).__str__()
                        eval_expr_value = eval(eval_expr)
                        logger.info(
                            '[Dependency]：【{}函数依赖】{}完成一次依赖函数"{}"的返回值期望数据替换，依赖函数表达式为"{}"，获取期望值为{}.'.format(
                                maintainer, maintainer, function_name, eval_expr, eval_expr_value))
                        return eval_expr_value
                    else:
                        logger.warning(
                            '[WARNING]：【{}函数依赖】当前接口预期表达式中依赖函数"{}"由于参数赋值存在缺失，将忽略此函数依赖！'.format(
                                maintainer, function_name))
                        self.dependency_fail_identity(maintainer)
                else:
                    logger.warning(
                        '[WARNING]：【{}函数依赖】当前接口预期表达式中调用的依赖函数"{}"传值入参形式必须为字典结构，请检查！'.format(maintainer, function_name))
                    self.dependency_fail_identity(maintainer)
            else:
                logger.warning(
                    '[WARNING]：【{}函数依赖】当前接口预期表达式中调用的依赖函数"{}"调用方式存在错误，请检查其是否合法！'.format(maintainer, function_name))
                self.dependency_fail_identity(maintainer)
        else:
            logger.warning(
                '[WARNING]：【{}函数依赖】当前接口预期表达式中指定的依赖函数"{}"暂未支持，请检查或追加！'.format(maintainer, function_name))
            self.dependency_fail_identity(maintainer)

    def dependency_fail_identity(self, maintainer):
        """
        识别数据依赖失败信息
        :param maintainer: 调用者名称
        :return:
        """
        if maintainer == "请求路径":
            self.dependency_fail_info_dict[
                'to_path'] = '请求路径存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
        elif maintainer == "请求头":
            self.dependency_fail_info_dict[
                'to_header'] = '请求头存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
        elif maintainer == "请求参数":
            self.dependency_fail_info_dict[
                'to_param'] = '请求参数存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
        elif maintainer == "请求体":
            self.dependency_fail_info_dict[
                'to_data'] = '请求体存在依赖数据未正常获取的情况，测试用例预期失败并自动跳过，具体请见log信息！'
        else:
            logger.warning('[WARNING]：当前不支持调用者"{}"的数据依赖失败信息识别，请检查！'.format(maintainer))


if __name__ == '__main__':
    from Gastepo.Core.Util.DataFrameUtils import DataframeOperation
    from Gastepo.Core.Util.CommonUtils import force_to_json, unicode_to_normal

    df = DataframeOperation(
        test_case_file="/Users/mayer/project/PycharmProjects/Gastepo/TestSuite/TestCase/ApiTestCase_stg.xls")
    test_case = df.get_entire_data_to_dict(id=['TC_1', 'TC_2', 'TC_4'], check_active=True)

    response_dict = {}
    for case in test_case:
        session = SuperTestCaseRequestTool(case, response_dict)
        response = session.dispatch_request(header={}, param={}, data={})
        headers = session.fetch_request_dict.get("headers")
        params = session.fetch_request_dict.get("params")
        response_dict[case["UrlPath"]] = force_to_json(
            xml_to_json(response.text) if case["Consumes"] == "application/xml" else response.text)
        print('开始请求{}用例接口"{}"'.format(case["ID"], case["UrlPath"]))
        print("请求方法：{}; 请求路径：{}; 请求头：{}; 请求体：{}; 响应结果：{}".format(response.request.method,
                                                                 response.request.url,
                                                                 headers,
                                                                 unicode_to_normal(response.request.body),
                                                                 response.text if case[
                                                                                      "Consumes"] == "application/xml" else force_to_json(
                                                                     response.text)
                                                                 )
              )
    print("done".center(100, "*"))
