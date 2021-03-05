# -*- coding: utf-8 -*-

import os
import sys
import time
from collections import Counter

from Gastepo.Core.Base.BaseData import TESTCASE_TITLE_ORDER_ENUM
from Gastepo.Core.Base.CustomException import DotTypeError
from Gastepo.Core.Util.DataFrameUtils import DataframeOperation
from Gastepo.Core.Util.ExcelUtils import ExcelXlsWriter, ExcelXlsxWriter
from Gastepo.Core.Util.LogUtils import logger


class SimpleTestCaseTool(object):
    """
    测试用例自动生成操作类~【单组用例(不支持参数化,用于调试)】
    """

    def __init__(self, swagger_api_file, capture_api_file):
        """
        初始化指定Swagger接口文档和接口抓包文档
        :param swagger_doc_file: Swagger接口文档(Excel文件)
        :param capture_api_file: 接口抓包文档(如Charles、Fiddler或微信开发者工具完成抓包并同步文档)
        """
        if os.path.exists(swagger_api_file):
            if os.path.exists(capture_api_file):
                self.swagger_doc_df = DataframeOperation(test_case_file=swagger_api_file).df.rename(
                    columns={"ID": "AID"})
                self.capture_doc_df = DataframeOperation(test_case_file=capture_api_file).df.rename(
                    columns={"ID": "CID"}).sort_values(by="CID", ascending=True)
                self.case_doc_df = self.swagger_doc_df.loc[
                    self.swagger_doc_df["UrlPath"].isin(
                        [str(i).strip() for i in self.capture_doc_df["CID"].index.values.tolist()])].sort_values(
                    by="UrlPath", ascending=True)
            else:
                logger.warning('[WARNING]：接口抓包文档"{}"当前并不存在，请先完成相关接口抓包操作！'.format(capture_api_file))
                sys.exit(1)
        else:
            logger.warning('[WARNING]：Swagger接口文档"{}"当前并不存在，请先完成接口文档生成操作！'.format(swagger_api_file))
            sys.exit(1)

    @property
    def check_empty_urlpath(self):
        """
        检查Swagger接口文档及接口抓包文档中UrlPath是否全部填充
        :return:
        """
        try:
            if self.swagger_doc_df["UrlPath"].shape[0] == 0 or self.capture_doc_df["CID"].shape[0] == 0:
                logger.warning("[WARNING]：Swagger接口文档或接口抓包文档中UrlPath列当前无任何填充数据，请检查并完全填充相关数据！")
                return False
            if self.swagger_doc_df["UrlPath"].shape[0] != 0 and self.capture_doc_df["CID"].shape[0] != 0:
                logger.info("[Success]：Swagger接口文档及接口抓包文档中UrlPath列完全填充状态检测通过，二者UrlPath列均已填充完全.")
                return True
        except Exception:
            logger.exception("[Exception]：检测Swagger接口文档及接口抓包文档中UrlPath列是否完全填充过程中发生异常，请检查！")
            return False

    @property
    def check_duplicate_urlpath(self):
        """
        检查Swagger接口文档及接口抓包文档中是否存在重复的UrlPath.
        :return:
        """
        pass_flag = False
        try:
            if self.check_empty_urlpath is True:
                swagger_doc_urlpath_veriry = {i: j for i, j in
                                              dict(Counter([str(i).strip() for i in
                                                            self.swagger_doc_df["UrlPath"].values.tolist()])).items() if
                                              j > 1}
                capture_doc_urlpath_veriry = {i: j for i, j in
                                              dict(Counter([str(i).strip() for i in
                                                            self.capture_doc_df["CID"].values.tolist()])).items()
                                              if j > 1}
                if swagger_doc_urlpath_veriry == {} and capture_doc_urlpath_veriry == {}:
                    logger.info("[Success]：Swagger接口文档或接口抓包文档中各自UrlPath列是否存在重复值检测通过，二者各自UrlPath列均无重复值.")
                    return True
                if swagger_doc_urlpath_veriry != {}:
                    logger.warning(
                        '[WARNING]：检测到Swagger接口文档中存在重复的UrlPath，检测结果：{}，请仔细核对并明确需求！'.format(swagger_doc_urlpath_veriry))
                    pass_flag = False
                if capture_doc_urlpath_veriry != {}:
                    logger.warning(
                        '[WARNING]：检测到接口抓包文档中存在重复的UrlPath，检测结果：{}，请仔细核对并明确需求！'.format(capture_doc_urlpath_veriry))
                    pass_flag = False
                return pass_flag
            else:
                logger.warning("[WARNING]：请先正常初始化Swagger接口文档和接口抓包文档！")
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：检测Swagger接口文档或接口抓包文档中各自UrlPath列是否存在重复值过程中发生异常，请检查！")
            return False

    @property
    def check_match_urlpath(self):
        """
        检测Swagger接口文档与接口抓包文档中的UrlPath是否映射匹配
        :return:
        """
        try:
            case_doc_df_count = self.case_doc_df.shape[0]
            capture_doc_df_count = self.capture_doc_df.shape[0]
            if case_doc_df_count == 0:
                logger.warning("[WARNING]：检测到Swagger接口文档中无任何映射匹配的UrlPath，请检查相关接口文档是否符合需求或手动追加！")
                return False
            if case_doc_df_count < capture_doc_df_count:
                swagger_doc_less_set = set([str(i).strip() for i in self.capture_doc_df["CID"].values.tolist()]) - set(
                    [str(i).strip() for i in self.case_doc_df["UrlPath"].values.tolist()])
                logger.warning("[WARNING]：检测到Swagger接口文档中缺少映射匹配的UrlPath，检测结果：{}，请检查相关接口文档是否符合需求或手动追加！".format(
                    swagger_doc_less_set))
                return False
            if case_doc_df_count == capture_doc_df_count:
                logger.info("[Success]：Swagger接口文档与接口抓包文档中UrlPath映射匹配规则检测通过，二者存在数量相等且映射匹配的UrlPath.")
                return True
        except Exception:
            logger.exception("[Exception]：检测Swagger接口文档与接口抓包文档进行UrlPath映射匹配规则过程中发生异常，请检查！")
            return False

    @property
    def load_test_case(self):
        """
        依据swagger接口文档及接口抓包文档生成测试用例
        :return:
        """
        try:
            if self.check_duplicate_urlpath is True:
                if self.check_match_urlpath is True:
                    self.case_doc_df["Platform"] = [str(platform).strip().capitalize() for platform in
                                                    self.capture_doc_df["Platform"].values.tolist()]
                    self.case_doc_df["Level"] = [str(level).strip().upper() for level in
                                                 self.capture_doc_df["Level"].values.tolist()]
                    self.case_doc_df["Active"] = True
                    self.case_doc_df["Group"] = self.capture_doc_df["Group"].values.tolist()
                    self.case_doc_df["Order"] = self.capture_doc_df["Order"].values.tolist()
                    self.case_doc_df["RequestPath"] = self.capture_doc_df["Path"].values.tolist()
                    self.case_doc_df["RequestHeader"] = self.capture_doc_df["Header"].values.tolist()
                    self.case_doc_df["RequestParam"] = self.capture_doc_df["Param"].values.tolist()
                    self.case_doc_df["RequestData"] = self.capture_doc_df["Data"].values.tolist()
                    self.case_doc_df["RequestFile"] = self.capture_doc_df["File"].values.tolist()
                    self.case_doc_df["DependencyInfo"] = self.capture_doc_df["Dependency"].values.tolist()
                    self.case_doc_df["AssertInfo"] = self.capture_doc_df["Assert"].values.tolist()
                    self.case_doc_df = self.case_doc_df.sort_values(by="Order", ascending=True)
                    self.case_doc_df = self.case_doc_df.reset_index(drop=True).reset_index().rename(
                        columns={"index": "ID"})
                    self.case_doc_df["ID"] = self.case_doc_df["ID"].apply(lambda x: "TC_{}".format(x + 1))
                    return self.case_doc_df
                else:
                    logger.warning("[WARNING]：Swagger接口文档与接口抓包文档中UrlPath映射匹配规则检测未通过，请查看相关检测结果！")
                    sys.exit(1)
            else:
                logger.warning("[WARNING]：Swagger接口文档或接口抓包文档中各自UrlPath列是否存在重复值检测未通过，请查看相关检测结果！")
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：依据Swagger接口文档及接口抓包文档自动生成测试用例过程中发生异常，请检查！")
            sys.exit(1)

    def generate(self, test_case_file, sep=r'|', encoding='utf-8'):
        """
        生成测试用例文件(当前支持Excel文件[xls/xlsx]及文本文件[csv/txt])
        :param test_case_file: 测试用例文件路径
        :param sep: 文件分隔符,默认"|"。
        :param encoding: 文件编码格式。
        :return:
        """
        logger.info("[Initial]：开始自动评估测试用例生成条件......")
        file_extend = str(os.path.splitext(test_case_file)[-1]).lower()
        try:
            test_case_df = self.load_test_case
            if file_extend not in [".csv", ".txt", ".xls", ".xlsx"]:
                logger.warning("[WARNING]：自动生成的测试用例文件扩展名当前仅支持[csv、txt、xls、xlsx]，请检查！")
                sys.exit(1)
            if file_extend in ['.xls', '.xlsx']:
                logger.info("[Loading]：开始自动生成{}格式测试用例文件......".format(file_extend))
                test_case_df.to_excel(test_case_file, index=False)
            if file_extend in ['.csv', '.txt']:
                logger.info("[Loading]：开始自动生成{}格式测试用例文件......".format(file_extend))
                test_case_df.to_csv(test_case_file, sep=sep, index=False, header=True,
                                    encoding=encoding)
            logger.info('[Done]：{}格式测试用例文件已经成功自动生成，路径为"{}".'.format(file_extend, test_case_file))
        except Exception:
            logger.exception("[Exception]: {}格式测试用例文件自动生成过程中发生异常，请检查！".format(file_extend))
            sys.exit(1)


class SingletonTestCaseTool(object):
    """
    测试用例自动生成操作类~【分组用例(支持参数化,但不支持重复接口调用)】
    """

    def __init__(self, swagger_api_file, capture_api_file):
        """
        初始化指定Swagger接口文档和接口抓包文档
        :param swagger_api_file: Swagger接口文档(Excel文件)
        :param capture_api_file: 接口抓包文档(如Charles、Fiddler或微信开发者工具完成抓包并同步文档)
        """
        if os.path.exists(swagger_api_file):
            if os.path.exists(capture_api_file):
                self.swagger_doc_df = DataframeOperation(test_case_file=swagger_api_file).df.rename(
                    columns={"ID": "AID"})
                self.capture_doc_df = DataframeOperation(test_case_file=capture_api_file).df.rename(
                    columns={"ID": "CID"}).sort_values(by=["Group", "CID"], ascending=True)
                self.capture_doc_cid_check = [str(i).strip() for i in
                                              list(dict(self.capture_doc_df.groupby(["CID"], sort=True).groups).keys())
                                              if i != '']
                self.case_doc_df = self.swagger_doc_df.loc[
                    self.swagger_doc_df["UrlPath"].isin(self.capture_doc_cid_check)].sort_values(
                    by="UrlPath", ascending=True)
            else:
                logger.warning('[WARNING]：接口抓包文档"{}"当前并不存在，请先完成相关接口抓包操作！'.format(capture_api_file))
                sys.exit(1)
        else:
            logger.warning('[WARNING]：Swagger接口文档"{}"当前并不存在，请先完成接口文档生成操作！'.format(swagger_api_file))
            sys.exit(1)

    @property
    def check_exist_urlpath(self):
        """
        检测接口抓包文档在Swagger接口文档中是否存在匹配的UrlPath
        :return:
        """
        try:
            if self.capture_doc_df["CID"].shape[0] == 0 or self.capture_doc_cid_check == []:
                logger.warning("[WARNING]：接口抓包文档中UrlPath当前无任何填充数据，请首先完成接口抓包工作！")
                sys.exit(1)
            if self.case_doc_df["UrlPath"].shape[0] == 0:
                logger.warning("[WARNING]：接口抓包文档中UrlPath在Swagger接口文档中未匹配到任何数据，请检查接口抓包文档和Swagger接口文档是否符合需求！")
                return False
            if self.case_doc_df["UrlPath"].shape[0] != 0 and self.capture_doc_df["CID"].shape[0] != 0:
                logger.info("[Success]：Swagger接口文档及接口抓包文档中UrlPath是否存在匹配数据检测通过，二者UrlPath存在匹配数据.")
                return True
        except Exception:
            logger.exception("[Exception]：检测接口抓包文档中UrlPath在Swagger接口文档中是否存在匹配数据过程中发生异常，请检查！")
            return False

    @property
    def check_duplicate_urlpath(self):
        """
        检测映射接口文档中匹配的UrlPath是否存在重复值
        :return:
        """
        pass_flag = False
        try:
            if self.check_exist_urlpath is True:
                case_doc_urlpath_veriry = {i: j for i, j in
                                           dict(Counter([str(i).strip() for i in
                                                         self.case_doc_df["UrlPath"].values.tolist()])).items() if
                                           j > 1}
                if case_doc_urlpath_veriry == {}:
                    logger.info("[Success]：映射接口文档中匹配的UrlPath是否存在重复值检测通过，其匹配的UrlPath均唯一.")
                    return True
                if case_doc_urlpath_veriry != {}:
                    logger.warning(
                        '[WARNING]：检测到映射接口文档中存在重复的UrlPath，检测结果：{}，请仔细核对并明确需求！'.format(case_doc_urlpath_veriry))
                    pass_flag = False
                return pass_flag
            else:
                logger.error("[Fail]：Swagger接口文档与接口抓包文档进行UrlPath数据匹配检测失败，请仔细检查相关文档数据！")
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：检测映射接口文档中匹配的UrlPath是否存在重复值过程中发生异常，请检查！")
            return False

    @property
    def check_match_urlpath(self):
        """
        检测接口抓包文档与映射接口文档中匹配的UrlPath是否存在一一映射匹配关系
        :return:
        """
        try:
            case_doc_df_count = self.case_doc_df.shape[0]
            capture_doc_df_count = self.capture_doc_cid_check.__len__()
            if case_doc_df_count < capture_doc_df_count:
                swagger_doc_less_set = set([str(i).strip() for i in self.capture_doc_df["CID"].values.tolist()]) - set(
                    [str(i).strip() for i in self.case_doc_df["UrlPath"].values.tolist()])
                logger.warning("[WARNING]：检测到映射接口文档中缺少接口抓包文档中映射匹配的UrlPath，检测结果：{}，请检查相关接口文档是否符合需求或手动追加！".format(
                    swagger_doc_less_set))
                return False
            if case_doc_df_count == capture_doc_df_count:
                logger.info("[Success]：映射接口文档与接口抓包文档中UrlPath一一映射匹配关系检测通过，二者存在一一映射匹配的UrlPath.")
                return True
        except Exception:
            logger.exception("[Exception]：检测映射接口文档与接口抓包文档进行UrlPath一一映射匹配关系过程中发生异常，请检查！")
            return False

    @property
    def load_test_case(self):
        """
        依据swagger接口文档及接口抓包文档自动生成测试用例
        :return:
        """
        test_case_total_df = DataframeOperation.generate_df(data=[])
        try:
            if self.check_duplicate_urlpath is True:
                if self.check_match_urlpath is True:
                    for group_name, group_data in self.capture_doc_df.groupby(["Group"], sort=True):
                        if group_name == "":
                            logger.warning("[WARNING]：检测到未设置任何分组标识的参数组别，需按大写字母(A~Z)区分指定参数分组标识，请先去指定！")
                            sys.exit(1)
                        reset_group_data = group_data.sort_values(by="CID", ascending=True).reset_index(drop=True)
                        if [str(i).strip() for i in reset_group_data["CID"].values.tolist() if i == ""] != []:
                            logger.warning('[WARNING]：检测到当前参数分组"{}"中存在未指定的空白UrlPath，请检查并指定！'.format(
                                group_name if group_name != "" else "N/A"))
                            sys.exit(1)
                        group_urlpath_dict = {i: j for i, j in
                                              dict(Counter([str(i).strip() for i in
                                                            reset_group_data["CID"].values.tolist()])).items() if
                                              j > 1}
                        if group_urlpath_dict != {}:
                            logger.warning(
                                '[WARNING]：参数分组"{}"中检测到重复的UrlPath，检测结果：{}，请确认并修改！'.format(
                                    group_name if group_name != "" else "N/A",
                                    group_urlpath_dict))
                            sys.exit(1)
                        temp_case_doc_df = self.swagger_doc_df.loc[
                            self.swagger_doc_df["UrlPath"].isin(
                                [str(i).strip() for i in reset_group_data["CID"].values.tolist()])].sort_values(
                            by="UrlPath", ascending=True)
                        temp_case_doc_df["Platform"] = [str(platform).strip().capitalize() for platform in
                                                        reset_group_data["Platform"].values.tolist()]
                        temp_case_doc_df["Level"] = [str(level).strip().upper() for level in
                                                     reset_group_data["Level"].values.tolist()]
                        temp_case_doc_df["Active"] = True
                        temp_case_doc_df["Group"] = reset_group_data["Group"].values.tolist()
                        temp_case_doc_df["Order"] = reset_group_data["Order"].values.tolist()
                        temp_case_doc_df["RequestPath"] = reset_group_data["Path"].values.tolist()
                        temp_case_doc_df["RequestHeader"] = reset_group_data["Header"].values.tolist()
                        temp_case_doc_df["RequestParam"] = reset_group_data["Param"].values.tolist()
                        temp_case_doc_df["RequestData"] = reset_group_data["Data"].values.tolist()
                        temp_case_doc_df["RequestFile"] = reset_group_data["File"].values.tolist()
                        temp_case_doc_df["DependencyInfo"] = reset_group_data["Dependency"].values.tolist()
                        temp_case_doc_df["AssertInfo"] = reset_group_data["Assert"].values.tolist()
                        temp_case_doc_df = temp_case_doc_df.sort_values(by=["Order"], ascending=True)
                        test_case_total_df = test_case_total_df.append(temp_case_doc_df)
                    test_case_total_df = test_case_total_df.sort_values(by=["Group", "Order"],
                                                                        ascending=True).reset_index(
                        drop=True).reset_index().rename(
                        columns={"index": "ID"})
                    test_case_total_df["ID"] = test_case_total_df["ID"].apply(lambda x: "TC_{}".format(x + 1))
                    return test_case_total_df
                else:
                    logger.error("[Fail]：映射接口文档与接口抓包文档中UrlPath一一映射匹配关系检测未通过，请查看相关检测结果！")
                    sys.exit(1)
            else:
                logger.error("[Fail]：映射接口文档与接口抓包文档中匹配的UrlPath是否存在重复值检测未通过，请查看相关检测结果！")
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：依据Swagger接口文档及接口抓包文档自动生成测试用例过程中发生异常，请检查！")
            sys.exit(1)

    def generate(self, test_case_file, sep=r'|', encoding='utf-8'):
        """
        生成测试用例文件(当前支持Excel文件[xls/xlsx]及文本文件[csv/txt])
        :param test_case_file: 测试用例文件路径
        :param sep: 文件分隔符,默认"|"。
        :param encoding: 文件编码格式。
        :return:
        """
        logger.info("[Initial]：开始自动评估测试用例生成条件......")
        file_extend = str(os.path.splitext(test_case_file)[-1]).lower()
        try:
            test_case_df = self.load_test_case
            if file_extend not in [".csv", ".txt", ".xls", ".xlsx"]:
                logger.warning("[WARNING]：自动生成的测试用例文件扩展名当前仅支持[csv、txt、xls、xlsx]，请检查！")
                sys.exit(1)
            if file_extend in ['.xls', '.xlsx']:
                logger.info("[Loading]：开始自动生成{}格式测试用例文件......".format(file_extend))
                test_case_df.to_excel(test_case_file, index=False)
            if file_extend in ['.csv', '.txt']:
                logger.info("[Loading]：开始自动生成{}格式测试用例文件......".format(file_extend))
                test_case_df.to_csv(test_case_file, sep=sep, index=False, header=True,
                                    encoding=encoding)
            logger.info('[Done]：{}格式测试用例文件已经成功自动生成，路径为"{}".'.format(file_extend, test_case_file))
        except Exception:
            logger.exception("[Exception]: {}格式测试用例文件自动生成过程中发生异常，请检查！".format(file_extend))
            sys.exit(1)


class AdvanceTestCaseTool(object):
    """
    测试用例自动生成操作类~【分组用例(支持参数化,同时支持重复接口调用)】
    """

    def __init__(self, swagger_api_file, capture_api_file):
        """
        初始化指定Swagger接口文档和接口抓包文档
        :param swagger_api_file: Swagger接口文档(Excel文件)
        :param capture_api_file: 接口抓包文档(如Charles、Fiddler或微信开发者工具完成抓包并同步文档)
        """
        if os.path.exists(swagger_api_file):
            if os.path.exists(capture_api_file):
                self.swagger_doc_df = DataframeOperation(test_case_file=swagger_api_file).df.rename(
                    columns={"ID": "AID"})
                self.capture_doc_df = DataframeOperation(test_case_file=capture_api_file).df.rename(
                    columns={"ID": "CID"}).sort_values(by=["Group", "CID"], ascending=True)
                self.capture_doc_cid_check = [str(i).strip() for i in
                                              list(dict(self.capture_doc_df.groupby(["CID"], sort=True).groups).keys())
                                              if i != '']
                self.case_doc_df = self.swagger_doc_df.loc[
                    self.swagger_doc_df["UrlPath"].isin(self.capture_doc_cid_check)].sort_values(
                    by="UrlPath", ascending=True)
            else:
                logger.warning('[WARNING]：接口抓包文档"{}"当前并不存在，请先完成相关接口抓包操作！'.format(capture_api_file))
                sys.exit(1)
        else:
            logger.warning('[WARNING]：Swagger接口文档"{}"当前并不存在，请先完成接口文档生成操作！'.format(swagger_api_file))
            sys.exit(1)

    @property
    def check_exist_urlpath(self):
        """
        检测接口抓包文档在Swagger接口文档中是否存在匹配的UrlPath
        :return:
        """
        try:
            if self.capture_doc_df["CID"].shape[0] == 0 or self.capture_doc_cid_check == []:
                logger.warning("[WARNING]：接口抓包文档中UrlPath当前无任何填充数据，请首先完成接口抓包工作！")
                sys.exit(1)
            if self.case_doc_df["UrlPath"].shape[0] == 0:
                logger.warning("[WARNING]：接口抓包文档中UrlPath在Swagger接口文档中未匹配到任何数据，请检查接口抓包文档和Swagger接口文档是否符合需求！")
                return False
            if self.case_doc_df["UrlPath"].shape[0] != 0 and self.capture_doc_df["CID"].shape[0] != 0:
                logger.info("[Success]：Swagger接口文档及接口抓包文档中UrlPath是否存在匹配数据检测通过，二者UrlPath存在匹配数据.")
                return True
        except Exception:
            logger.exception("[Exception]：检测接口抓包文档中UrlPath在Swagger接口文档中是否存在匹配数据过程中发生异常，请检查！")
            return False

    @property
    def check_duplicate_urlpath(self):
        """
        检测映射接口文档中匹配的UrlPath是否存在重复值
        :return:
        """
        pass_flag = False
        try:
            if self.check_exist_urlpath is True:
                case_doc_urlpath_veriry = {i: j for i, j in
                                           dict(Counter([str(i).strip() for i in
                                                         self.case_doc_df["UrlPath"].values.tolist()])).items() if
                                           j > 1}
                if case_doc_urlpath_veriry == {}:
                    logger.info("[Success]：映射接口文档中匹配的UrlPath是否存在重复值检测通过，其匹配的UrlPath均唯一.")
                    return True
                if case_doc_urlpath_veriry != {}:
                    logger.warning(
                        '[WARNING]：检测到映射接口文档中存在重复的UrlPath，检测结果：{}，请仔细核对并明确需求！'.format(case_doc_urlpath_veriry))
                    pass_flag = False
                return pass_flag
            else:
                logger.error("[Fail]：Swagger接口文档与接口抓包文档进行UrlPath数据匹配检测失败，请仔细检查相关文档数据！")
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：检测映射接口文档中匹配的UrlPath是否存在重复值过程中发生异常，请检查！")
            return False

    @property
    def check_match_urlpath(self):
        """
        检测接口抓包文档与映射接口文档中匹配的UrlPath是否存在一一映射匹配关系
        :return:
        """
        try:
            case_doc_df_count = self.case_doc_df.shape[0]
            capture_doc_df_count = self.capture_doc_cid_check.__len__()
            if case_doc_df_count < capture_doc_df_count:
                swagger_doc_less_set = set([str(i).strip() for i in self.capture_doc_df["CID"].values.tolist()]) - set(
                    [str(i).strip() for i in self.case_doc_df["UrlPath"].values.tolist()])
                logger.warning("[WARNING]：检测到映射接口文档中缺少接口抓包文档中映射匹配的UrlPath，检测结果：{}，请检查相关接口文档是否符合需求或手动追加！".format(
                    swagger_doc_less_set))
                return False
            if case_doc_df_count == capture_doc_df_count:
                logger.info("[Success]：映射接口文档与接口抓包文档中UrlPath一一映射匹配关系检测通过，二者存在一一映射匹配的UrlPath.")
                return True
        except Exception:
            logger.exception("[Exception]：检测映射接口文档与接口抓包文档进行UrlPath一一映射匹配关系过程中发生异常，请检查！")
            return False

    @property
    def load_test_case(self):
        """
        依据swagger接口文档及接口抓包文档自动生成测试用例
        :return:
        """
        test_case_total_df = DataframeOperation.generate_df(data=[])
        try:
            if self.check_duplicate_urlpath is True:
                if self.check_match_urlpath is True:
                    for group_name, group_data in self.capture_doc_df.groupby(["Group"], sort=True):
                        if group_name == "":
                            logger.warning("[WARNING]：检测到未设置任何分组标识的参数组别，需按大写字母(A~Z)区分指定参数分组标识，请先去指定！")
                            sys.exit(1)
                        reset_group_data = group_data.sort_values(by="CID", ascending=True).reset_index(drop=True)
                        if [str(i).strip() for i in reset_group_data["CID"].values.tolist() if i == ""] != []:
                            logger.warning('[WARNING]：检测到当前参数分组"{}"中存在未指定的空白UrlPath，请检查并指定！'.format(
                                group_name if group_name != "" else "N/A"))
                            sys.exit(1)

                        temp_case_doc_df = self.swagger_doc_df.loc[
                            self.swagger_doc_df["UrlPath"].isin(
                                [str(i).strip() for i in reset_group_data["CID"].values.tolist()])].sort_values(
                            by="UrlPath", ascending=True)
                        group_cid_total_df = DataframeOperation.generate_df(data=[])
                        for cid in set(group_data["CID"].values.tolist()):
                            cid_df = group_data[group_data["CID"] == cid]
                            cid_df.loc[:, "Project"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "Project"].values.tolist()
                            cid_df.loc[:, "Scenario"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "Scenario"].values.tolist()
                            cid_df.loc[:, "Title"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "Title"].values.tolist()
                            cid_df.loc[:, "BaseUrl"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "BaseUrl"].values.tolist()
                            cid_df.loc[:, "Method"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "Method"].values.tolist()
                            cid_df.loc[:, "Consumes"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "Consumes"].values.tolist()
                            cid_df.loc[:, "Active"] = True
                            cid_df.loc[:, "AID"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "AID"].values.tolist()
                            cid_df.loc[:, "ActualResponse"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "ActualResponse"].values.tolist()
                            cid_df.loc[:, "TestDescription"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "TestDescription"].values.tolist()
                            cid_df.loc[:, "TestResult"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "TestResult"].values.tolist()
                            cid_df.loc[:, "UpdateTime"] = temp_case_doc_df[temp_case_doc_df["UrlPath"] == cid][
                                "UpdateTime"].values.tolist()
                            group_cid_total_df = group_cid_total_df.append(cid_df)
                        test_case_total_df = test_case_total_df.append(group_cid_total_df)
                    test_case_total_df = test_case_total_df.rename(
                        columns={"CID": "UrlPath", "Path": "RequestPath", "Header": "RequestHeader",
                                 "Param": "RequestParam", "Data": "RequestData", "File": "RequestFile",
                                 "Dependency": "DependencyInfo",
                                 "Assert": "AssertInfo"})
                    test_case_total_df = test_case_total_df.reindex(
                        columns=["AID", "Project", "Scenario", "Title", "BaseUrl", "UrlPath", "Method", "Consumes",
                                 "Platform", "Level", "Active", "Group", "Order", "RequestPath", "RequestHeader",
                                 "RequestParam", "RequestData", "RequestFile", "DependencyInfo", "AssertInfo",
                                 "ActualResponse",
                                 "TestDescription",
                                 "TestResult",
                                 "UpdateTime"])
                    test_case_total_df = test_case_total_df.sort_values(by=["Group", "Order"],
                                                                        ascending=True).reset_index(
                        drop=True).reset_index().rename(
                        columns={"index": "ID"})
                    test_case_total_df["ID"] = test_case_total_df["ID"].apply(lambda x: "TC_{}".format(x + 1))
                    return test_case_total_df

                else:
                    logger.error("[Fail]：映射接口文档与接口抓包文档中UrlPath一一映射匹配关系检测未通过，请查看相关检测结果！")
                    sys.exit(1)
            else:
                logger.error("[Fail]：映射接口文档与接口抓包文档中匹配的UrlPath是否存在重复值检测未通过，请查看相关检测结果！")
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：依据Swagger接口文档及接口抓包文档自动生成测试用例过程中发生异常，请检查！")
            sys.exit(1)

    def generate(self, test_case_file, sep=r'|', encoding='utf-8'):
        """
        生成测试用例文件(当前支持Excel文件[xls/xlsx]及文本文件[csv/txt])
        :param test_case_file: 测试用例文件路径
        :param sep: 文件分隔符,默认"|"。
        :param encoding: 文件编码格式。
        :return:
        """
        logger.info("[Initial]：开始自动评估测试用例生成条件......")
        file_extend = str(os.path.splitext(test_case_file)[-1]).lower()
        try:
            test_case_df = self.load_test_case
            if file_extend not in [".csv", ".txt", ".xls", ".xlsx"]:
                logger.warning("[WARNING]：自动生成的测试用例文件扩展名当前仅支持[csv、txt、xls、xlsx]，请检查！")
                sys.exit(1)
            if file_extend in ['.xls', '.xlsx']:
                logger.info("[Loading]：开始自动生成{}格式测试用例文件......".format(file_extend))
                test_case_df.to_excel(test_case_file, index=False)
            if file_extend in ['.csv', '.txt']:
                logger.info("[Loading]：开始自动生成{}格式测试用例文件......".format(file_extend))
                test_case_df.to_csv(test_case_file, sep=sep, index=False, header=True,
                                    encoding=encoding)
            logger.info('[Done]：{}格式测试用例文件已经成功自动生成，路径为"{}".'.format(file_extend, test_case_file))
        except Exception:
            logger.exception("[Exception]: {}格式测试用例文件自动生成过程中发生异常，请检查！".format(file_extend))
            sys.exit(1)


class UpdateTestCaseTool(object):
    """
    测试用例自动更新操作类~【更新接口请求体、响应结果及断言结果等】
    """

    def __init__(self, test_case):
        """
        初始化测试用例文件, 准备同步更新结果.
        :param test_case: 测试用例文件绝对路径.
        """
        file_extension = os.path.splitext(str(test_case))[-1]
        try:
            if not os.path.exists(test_case):
                raise FileNotFoundError
            if file_extension == "":
                logger.exception("未检测到包含用例文件扩展名的合法路径，请仔细检查！")
            if str(file_extension).lower() == '.xls':
                self.writer = ExcelXlsWriter(excel_path=test_case, sheet=0)
            elif str(file_extension).lower() == '.xlsx':
                self.writer = ExcelXlsxWriter(excel_path=test_case, sheet=0)
            else:
                raise DotTypeError
        except DotTypeError:
            logger.exception(
                '非法文件扩展名"{}", 当前仅支持xls、xlsx用例文件扩展名.'.format(file_extension))
        except FileNotFoundError:
            logger.exception('当前用例文件"{}"并不存在，请检查路径！'.format(test_case))
        except Exception:
            logger.exception("初始化用例DataFrame过程中发生异常，请检查！")

    def testcase_result_clear(self):
        """
        清除测试用例文件上次运行的结果记录.
        :return:
        """
        # 清除上次更新时间
        self.writer.write_column(TESTCASE_TITLE_ORDER_ENUM.UpdateTime.value, "")
        # 清除上次测试结果
        self.writer.write_column(TESTCASE_TITLE_ORDER_ENUM.TestResult.value, "")
        # 清除上次测试描述
        self.writer.write_column(TESTCASE_TITLE_ORDER_ENUM.TestDescription.value, "")
        # 清除上次请求结果
        self.writer.write_column(TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value, "").save()
        logger.info("[Done]：EXCEL用例文件已完成结果重置.")

    def testcase_request_info(self, row_count, actual_header, actual_param, actual_data):
        """
        保存当前接口请求的所有数据.
        :param row_count: 测试用例所在行号
        :param actual_header: 实际请求头
        :param actual_param: 实际请求参数
        :param actual_data: 实际请求体
        :return:
        """
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.RequestHeader.value, actual_header, style="black")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.RequestParam.value, actual_param, style="black")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.RequestData.value, actual_data, style="black")

    def testcase_result_pass(self, row_count, write_msg, pass_flag="PASS"):
        """
        标记当前测试用例执行结果为成功.
        :param row_count: 测试用例所在行号
        :param write_msg: 用例响应结果
        :param pass_flag: 通过标记(默认PASS)
        :return:
        """
        if str(write_msg).__len__() >= 32767:
            self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value,
                              "【自动化跟踪】响应字符总长度({})超过单元格最高字符限制(32767)".format(str(write_msg).__len__()),
                              style="orange")
        else:
            self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value, "{}".format(write_msg),
                              style="black")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.TestResult.value, "{}".format(pass_flag), style="green")
        update_time = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.UpdateTime.value,
                          update_time,
                          style="gray")
        return dict(mark=pass_flag, reason="", time=update_time)

    def testcase_result_fail(self, row_count, write_msg, fail_reason, fail_flag="FAIL"):
        """
        标记当前测试用例执行结果为失败.
        :param row_count: 测试用例所在行号
        :param write_msg: 用例响应结果
        :param fail_reason: 失败原因描述
        :param fail_flag: 失败标记(默认FAIL)
        :return:
        """
        if str(write_msg).__len__() >= 32767:
            self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value,
                              "【自动化跟踪】响应字符总长度({})超过单元格最高字符限制(32767)".format(str(write_msg).__len__()),
                              style="orange")
        else:
            self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value, "{}".format(write_msg),
                              style="orange")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.TestDescription.value, "{}".format(fail_reason),
                          style="orange")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.TestResult.value, "{}".format(fail_flag), style="red")
        update_time = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.UpdateTime.value,
                          update_time,
                          style="gray")
        return dict(mark=fail_flag, reason=fail_reason, time=update_time)

    def testcase_result_xfail(self, row_count, write_msg, xfail_reason, xfail_flag="XFAIL"):
        """
        标记当前测试用例执行结果为预期失败.
        :param row_count: 测试用例所在行号
        :param write_msg: 用例响应结果
        :param xfail_reason: 预期失败原因描述
        :param xfail_flag: 预期失败标记(默认XFAIL)
        :return:
        """
        if str(write_msg).__len__() >= 32767:
            self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value,
                              "【自动化跟踪】响应字符总长度({})超过单元格最高字符限制(32767)".format(str(write_msg).__len__()),
                              style="orange")
        else:
            self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.ActualResponse.value, "{}".format(write_msg),
                              style="orange")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.TestDescription.value, "{}".format(xfail_reason),
                          style="orange")
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.TestResult.value, "{}".format(xfail_flag),
                          style="boldorange")
        update_time = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        self.writer.write(row_count, TESTCASE_TITLE_ORDER_ENUM.UpdateTime.value,
                          update_time,
                          style="gray")
        return dict(mark=xfail_flag, reason=xfail_reason, time=update_time)

    def save_testcase_result(self):
        """
        保存更新结果后的测试用例.
        :return:
        """
        self.writer.save()


if __name__ == '__main__':
    from Gastepo.Core.Base.BaseData import TESTCASE_PATH

    testcase = AdvanceTestCaseTool(swagger_api_file=os.path.join(TESTCASE_PATH, "SwaggerApiDocs_stg.xls"),
                                   capture_api_file=os.path.join(TESTCASE_PATH, "ApiCaptureDocs_stg.xls"))
    testcase.generate(test_case_file=os.path.join(TESTCASE_PATH, "ApiTestCase_stg.xls"))
    testcase.generate(test_case_file=os.path.join(TESTCASE_PATH, "ApiTestCase_stg.xlsx"))
