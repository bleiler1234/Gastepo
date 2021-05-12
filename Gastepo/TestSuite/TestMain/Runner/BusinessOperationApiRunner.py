# -*- coding: utf-8 -*-

import datetime
import json
import os
import re

import allure
import pytest
from allure_commons.types import LinkType

from Gastepo.Core.Base.BaseData import TESTCASE_PATH, RECORD_PATH
from Gastepo.Core.Util.AssertionUtils import AdvanceAssertionTools
from Gastepo.Core.Util.CommonUtils import force_to_json, unicode_to_normal, runner_config, param_to_dict, body_to_dict
from Gastepo.Core.Util.DataFrameUtils import DataframeOperation
from Gastepo.Core.Util.LogUtils import logger
from Gastepo.Core.Util.PostmanUtils import AggregatePostmanTools
from Gastepo.Core.Util.RequestUtils import SuperTestCaseRequestTool
from Gastepo.Core.Util.TestCaseUtils import UpdateTestCaseTool

logger.info("☞【生成测试用例】")

# 生成测试用例
AggregatePostmanTools(postman_collections_dir=TESTCASE_PATH).generate_testcase(
    testcase=os.path.join(TESTCASE_PATH, "ApiTestCase_stg.xls"))

# 测试用例路径
TEST_CASE = os.path.join(TESTCASE_PATH, "ApiTestCase_stg.xls")

# 测试运行筛选
RUN = runner_config()


@allure.epic("E2E接口自动化测试")
@allure.description("主要进行端到端接口自动化测试.")
class TestBusinessOperationApi(object):
    """
    接口自动化测试~执行类
    """

    def setup_class(self):
        """
        测试用例初始化，如用例结果重置、获取请求token等
        :return:
        """
        # 接口信息缓存字典
        self.REALTIME_API_DICT = {}
        self.ender = UpdateTestCaseTool(test_case=TEST_CASE)
        # 清空测试用例历史执行信息
        self.ender.testcase_result_clear()
        self.ender.save_testcase_result()
        # with allure.step("开始获取XX业务Web端请求Token值"):
        #     self.web_token = BusinessOperationApiStarter().login().get_token

    @pytest.mark.parametrize('test_case',
                             DataframeOperation(TEST_CASE).get_entire_data_to_dict(id=RUN.get("id"),
                                                                                   scenario=RUN.get("scenario"),
                                                                                   platform=RUN.get("platform"),
                                                                                   level=RUN.get("level"),
                                                                                   group=RUN.get("group"),
                                                                                   order=RUN.get("order"),
                                                                                   check_active=RUN.get("active")),
                             indirect=False)
    @allure.step('执行测试用例')
    def test_case_runner(self, test_case):
        """
        测试用例执行器
        :param test_case: 测试用例字典数据
        :return:
        """

        def get_token(platform):
            if platform == "Web":
                return self.web_token

        # 获取测试用例所在行号
        test_case_count = int(re.split(r"[_]+", test_case["ID"])[-1])

        # 动态设定Allure测试报告参数
        allure.dynamic.feature(test_case["Project"])
        allure.dynamic.story(test_case['Scenario'])
        allure.dynamic.title(test_case['Title'])
        allure.dynamic.tag(test_case["Platform"])
        allure.dynamic.tag(
            str(test_case["Group"]) + "_" + str(test_case["Order"]) + " ~ " + "[" + test_case["ID"] + "]")
        allure.dynamic.severity(test_case['Level'])
        allure.dynamic.link("{}".format("http://10.9.18.133:8087/swagger-ui.html"), link_type=LinkType.ISSUE,
                            name="[请查阅]：Swagger接口文档")

        # 接口信息收集
        with allure.step("接口信息收集"):
            allure.attach(
                json.dumps(json.loads(test_case["DependencyInfo"] if test_case["DependencyInfo"] != "" else "{}"),
                           indent=1,
                           ensure_ascii=False), name="接口依赖",
                attachment_type=allure.attachment_type.JSON, extension="json")

        # 接口请求发送
        with allure.step("接口请求发送"):
            logger.info("[Begin]：开始执行接口测试用例[{}][{}_{}][{}] ~ [{}]......".format(test_case["ID"], test_case["Group"],
                                                                                test_case["Order"],
                                                                                test_case["Platform"],
                                                                                test_case["Title"]))
            token = get_token(test_case["Platform"])
            session = SuperTestCaseRequestTool(test_case, self.REALTIME_API_DICT, global_session=True)
            response = session.dispatch_request(path={}, header={}, param={}, data={})
            headers = session.fetch_request_dict.get("headers")
            paths = session.fetch_request_dict.get("paths")
            params = session.fetch_request_dict.get("params")
            datas = session.fetch_request_dict.get("datas")

            # 接口信息缓存字典数据注入
            IDENTITY_URL = str(test_case["Method"]).strip().upper() + " " + str(test_case["UrlPath"]).strip()
            self.REALTIME_API_DICT[IDENTITY_URL] = dict(request=dict(path={}, header={}, param={}, data={}),
                                                        response=dict(header={}, data={}))
            self.REALTIME_API_DICT[IDENTITY_URL]["request"]["path"] = {} if paths == "" else paths
            self.REALTIME_API_DICT[IDENTITY_URL]["request"]["header"] = headers
            self.REALTIME_API_DICT[IDENTITY_URL]["request"]["param"] = param_to_dict(params)
            self.REALTIME_API_DICT[IDENTITY_URL]["request"]["data"] = body_to_dict(headers["Content-Type"],
                                                                                   datas)
            self.REALTIME_API_DICT[IDENTITY_URL]["response"]["header"] = force_to_json(
                json.dumps(dict(response.headers.items()), ensure_ascii=False))
            self.REALTIME_API_DICT[IDENTITY_URL]["response"]["data"] = force_to_json(response.text)
            self.REALTIME_API_DICT[IDENTITY_URL]["status_code"] = response.status_code
            self.REALTIME_API_DICT[IDENTITY_URL]["trace_time"] = str(datetime.datetime.now())
            logger.info(
                "接口请求详细日志如下☞：\n 【请求URL】：{}\n 【请求方法】：{}\n 【请求头部】：{}\n 【请求数据】：{}\n 【响应结果】：{}".format(response.request.url,
                                                                                                   response.request.method,
                                                                                                   headers,
                                                                                                   unicode_to_normal(
                                                                                                       response.request.body),
                                                                                                   json.dumps(
                                                                                                       force_to_json(
                                                                                                           response.text),
                                                                                                       ensure_ascii=False,
                                                                                                       indent=2)))
            allure.dynamic.description_html(
                """
                <font color="gray">请求路径：</font>{}<br/>
                <font color="gray">请求方法：</font>{}<br/>
                <font color="gray">请求头部：</font>{}<br/>
                <font color="gray">请求参数：</font>{}<br/>
                <font color="gray">请求数据：</font>{}
                """.format(response.request.url if response.request.url != "" else "N/A",
                           response.request.method if response.request.method != "" else "N/A",
                           headers if headers != "" else "N/A",
                           params if params != "" else "N/A",
                           unicode_to_normal(
                               response.request.body) if response.request.body != "" and response.request.body is not None else "N/A"))
            allure.attach(json.dumps(force_to_json(json.dumps(dict(response.headers.items()), ensure_ascii=False)),
                                     indent=1, ensure_ascii=False), name="响应头部",
                          attachment_type=allure.attachment_type.JSON, extension="json")
            allure.attach(json.dumps(force_to_json(response.text), indent=1, ensure_ascii=False), name="响应结果",
                          attachment_type=allure.attachment_type.JSON, extension="json")

            # # 保存上次接口请求信息
            # self.ender.testcase_request_info(row_count=test_case_count,
            #                                  actual_header=json.dumps(headers, indent=1,
            #                                                           ensure_ascii=False) if headers != "" else "",
            #                                  actual_param=params if params != "" else "",
            #                                  actual_data=unicode_to_normal(
            #                                      response.request.body) if response.request.body != "" and response.request.body is not None else "")

        try:
            # 接口结果断言匹配
            with allure.step("测试响应断言"):
                allure.attach(
                    json.dumps(json.loads(test_case["AssertInfo"] if test_case["AssertInfo"] != "" else "{}"), indent=1,
                               ensure_ascii=False),
                    name="断言信息", attachment_type=allure.attachment_type.JSON,
                    extension="json")
                AdvanceAssertionTools(test_case_schema=test_case, origin_data=force_to_json(response.text),
                                      realtime_dependency=self.REALTIME_API_DICT).advance_assert()
            # 标记测试结果为成功(pass)
            with allure.step("测试结果标记"):
                result = self.ender.testcase_result_pass(row_count=test_case_count,
                                                         write_msg=json.dumps(force_to_json(response.text),
                                                                              ensure_ascii=False, indent=1),
                                                         pass_flag="PASS")
                allure.attach(json.dumps(result, indent=1, ensure_ascii=False), name="测试结果",
                              attachment_type=allure.attachment_type.JSON, extension="json")
        except AssertionError as reason:
            # 标记测试结果为失败(xfail或fail)
            with allure.step("测试结果标记"):
                if session.check_dependency_fail_info_dict is True:
                    logger.error(
                        "[Assertion]：[{}]~[{}]依赖数据缺失情况下的断言检测预期失败，失败原因为【{}】.".format(test_case["ID"], test_case["Title"],
                                                                                    str(reason)))
                    logger.critical(
                        "[End]：[{}]~[{}]依赖数据存在缺失情况，缺失原因为【{}】！".format(test_case["ID"], test_case["Title"],
                                                                      json.dumps(
                                                                          session.dependency_fail_info_dict,
                                                                          indent=1, ensure_ascii=False)))
                    result = self.ender.testcase_result_xfail(row_count=test_case_count,
                                                              write_msg=json.dumps(force_to_json(response.text),
                                                                                   ensure_ascii=False, indent=1),
                                                              xfail_reason=str(reason), xfail_flag="XFAIL")
                    allure.attach(json.dumps(result, indent=1, ensure_ascii=False), name="测试结果",
                                  attachment_type=allure.attachment_type.JSON, extension="json")
                    pytest.xfail(reason=json.dumps(session.dependency_fail_info_dict, indent=1, ensure_ascii=False))
                else:
                    logger.critical(
                        "[End]：[{}]~[{}]断言检测存在失败情况，失败原因为【{}】，测试用例断言失败.".format(test_case["ID"], test_case["Title"],
                                                                               str(reason)))
                    result = self.ender.testcase_result_fail(row_count=test_case_count,
                                                             write_msg=json.dumps(force_to_json(response.text),
                                                                                  ensure_ascii=False, indent=1),
                                                             fail_reason=str(reason), fail_flag="FAIL")
                    allure.attach(json.dumps(result, indent=1, ensure_ascii=False), name="测试结果",
                                  attachment_type=allure.attachment_type.JSON, extension="json")
                    pytest.fail(msg=str(reason))

    def teardown_class(self):
        """
        测试用例结束操作
        :return:
        """
        with open(file=os.path.join(RECORD_PATH, "ApiRecordDocs.json"), mode=r'w', encoding='utf-8') as record:
            record.write(json.dumps(self.REALTIME_API_DICT, ensure_ascii=False, indent=2))
            logger.info("[Record]：接口信息实时录制已完成并保存成功.")
        # 删除接口信息缓存字典
        del self.REALTIME_API_DICT
        # 保存更新后的测试用例
        self.ender.save_testcase_result()
        logger.info("[Done]：EXCEL测试用例文件已同步更新执行结果并保存.")
