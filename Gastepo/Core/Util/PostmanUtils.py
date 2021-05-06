# -*- coding: utf-8 -*-

import json
import os
import re
import sys

import emoji
import pandas as pd

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Util.CommonUtils import get_alphabet
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class PostmanTools(object):
    """
    Postman操作工具类
    """

    def __init__(self, postman_collection, groups=None):
        """
        初始化生成postman集合文档
        :param postman_collection: Postman集合文档绝对路径
        :param groups: 参数分组(默认为A组), 支持数量定义或名称列表定义
        """
        env = YamlConfig(config=APPLICATION_CONFIG_FILE).get("postman", 2).get("active").get("env")
        sync_url = YamlConfig(config=APPLICATION_CONFIG_FILE).get("postman", 2).get("domain").get(env)
        url_filter = YamlConfig(config=APPLICATION_CONFIG_FILE).get("postman", 2).get("active").get("filter")
        self.url_filter = r".*" if url_filter is None else url_filter
        if sync_url is None:
            logger.warning("[WARNING]：应用配置文件ApplicationConfig中未发现当前激活环境为{}的任何接口匹配地址，请检查！".format(env))
            self.sync_url = None
        else:
            self.sync_url = sync_url
        if os.path.exists(postman_collection):
            with open(file=postman_collection, mode='r', encoding='utf-8') as collection:
                postman_collection_str = emoji.demojize("".join(collection.readlines()))
                self.postman_collection_dict = json.loads(postman_collection_str)
            if groups is None:
                self.groups = ["A"]
            if groups is not None:
                if isinstance(groups, int) and groups > 0:
                    self.groups = [get_alphabet(i) for i in range(groups)]
                elif isinstance(groups, list) and groups != []:
                    self.groups = groups
                else:
                    logger.warning("[WARNING]：当前分组参数groups仅支持大于0的整数值或非空列表类型，请根据需求重新指定！")
                    sys.exit(1)
        else:
            logger.warning('[WARNING]：Postman集合文档"{}"当前并不存在，请指定Postman集合文档合法路径！'.format(postman_collection))
            sys.exit(1)

    def combine_to_total_dict(self, dict_list):
        """
        将字典列表中所有字典合并成一个大字典
        :param dict_list: 字典列表
        :return:
        """
        total_dict = dict()
        for dict_info in dict_list:
            total_dict.update(dict_info)
        if total_dict != {}:
            total_dict = json.dumps(total_dict, indent=1, ensure_ascii=False)
        if total_dict == {}:
            total_dict = ""
        return total_dict

    def if_exists_get_key(self, dict_info, key_info):
        """
        判断字典中是否存在指定键，若存在则取其映射值
        :param dict_info: 字典
        :param key_info: 键名
        :return:
        """
        if dict_info.__contains__(key_info):
            return dict_info[key_info]
        else:
            return []

    def to_dict_str(self, input_str):
        """
        若字符串为空则转换为字典形式字符串
        :param input_str: 字符串
        :return:
        """
        if input_str == "":
            return "{}"
        else:
            return input_str

    def sync_url_with_environment(self, base_url):
        """
        同步应用配置文件中当前激活环境的接口地址
        :param base_url: Postman中当前默认接口地址
        :return:
        """
        if self.sync_url is None:
            return base_url
        else:
            if re.search(self.url_filter, base_url) is not None:
                return self.sync_url
            else:
                return base_url

    @property
    def load_collection(self):
        """
        依据Postman集合文档自动生成接口抓包文档
        :return:
        """
        postman_json_data_groups_df = pd.DataFrame()
        items = self.postman_collection_dict["item"]

        def fetch_env(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 0:
                env_list = re.split(r'[\[|\]]', param_list[0])
                env = env_list[1]
                if env == "":
                    return "default"
                elif str(env).lower() == 'skip':
                    del param_list[0]
                    if param_list.__len__() > 0:
                        env1_list = re.split(r'[\[|\]]', param_list[0])
                        env1 = env1_list[1]
                        if env1 == "":
                            return "default"
                        else:
                            return env1
                    else:
                        return "default"
                else:
                    return env
            else:
                return "default"

        def fetch_level(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 1:
                param_list = [param for param in param_list if str(param).lower() != '[skip]']
                if param_list.__len__() > 1:
                    level_list = re.split(r'[\[|\]]', param_list[1])
                    level = str(level_list[1]).lower()
                    if level in ['blocker', 'critical', 'normal', 'minor', 'trivial']:
                        return level
                    else:
                        return 'normal'
                else:
                    return 'normal'
            else:
                return 'normal'

        def fetch_data_by_mode(item):
            data = ""
            if item["request"]["method"] in ["GET", "DELETE"]:
                data = ""
            if item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                if item["request"].__contains__("body"):
                    data_mode = item["request"]["body"]["mode"]
                    if data_mode == "urlencoded":
                        data = self.combine_to_total_dict([{data["key"]: data["value"]} for data in
                                                           self.if_exists_get_key(item["request"]["body"],
                                                                                  "urlencoded")])
                    if data_mode == "formdata":
                        data = self.combine_to_total_dict([{data["key"]: data["value"]} for data in
                                                           self.if_exists_get_key(item["request"]["body"],
                                                                                  "formdata") if
                                                           data["type"] == "text"])
                    if data_mode == "raw":
                        mode_type = item["request"]["body"]["options"]["raw"]["language"]
                        if mode_type == "json":
                            data = json.loads(
                                item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else "{}")
                            if data == {} and item["request"]["body"]["raw"] == "":
                                data = ""
                        if mode_type == "xml":
                            data = item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else ""
                        if mode_type == "text":
                            data = item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else ""
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data, indent=1, ensure_ascii=False)
            return data

        def fetch_file_for_form(item):
            def combine_to_file_list(file_dict_list):
                files = []
                for file_dict in file_dict_list:
                    file_key = file_dict["key"]
                    file_src = file_dict["src"]
                    if isinstance(file_src, str):
                        files.append((file_key, file_src))
                    if isinstance(file_src, list):
                        if file_src == []:
                            files.append((file_key, "no file"))
                        else:
                            for src in file_src:
                                files.append((file_key, src))
                return files

            files = ""
            if item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                if item["request"].__contains__("body"):
                    data_mode = item["request"]["body"]["mode"]
                    if data_mode == "formdata":
                        files = combine_to_file_list(
                            [file for file in self.if_exists_get_key(item["request"]["body"], "formdata") if
                             file["type"] == "file"])
            if files == []:
                files = ""
            return files

        def fetch_dependency(item):
            event_info = self.if_exists_get_key(item, "event")
            if event_info == []:
                return ""
            else:
                dependency_dict_list = [json.loads(self.to_dict_str("".join(event["script"]["exec"]))) for event in
                                        event_info if
                                        event["listen"] == "prerequest"]
                if dependency_dict_list == [] or dependency_dict_list == [{}]:
                    return ""
                else:
                    dependency_info = json.dumps(dependency_dict_list[0], indent=1, ensure_ascii=False)
                    return dependency_info

        def fetch_assert(item):
            event_info = self.if_exists_get_key(item, "event")
            if event_info == []:
                return ""
            else:
                assert_dict_list = [json.loads(self.to_dict_str("".join(event["script"]["exec"]))) for event in
                                    event_info if
                                    event["listen"] == "test"]
                if assert_dict_list == [] or assert_dict_list == [{}]:
                    return ""
                else:
                    assert_info = json.dumps(assert_dict_list[0], indent=1, ensure_ascii=False)
                    return assert_info

        try:
            for group in self.groups:
                postman_json_data_list = []
                order_count = 1
                for item in items:
                    api_json_dict = dict(
                        Name=item["name"],
                        ID="/" + "/".join(item["request"]["url"]["path"]),
                        Platform=fetch_env(item["name"]),
                        Level=fetch_level(item['name']),
                        Group=group,
                        Order=order_count,
                        Path="",
                        Header=self.combine_to_total_dict(
                            [{header["key"]: header["value"]} for header in
                             self.if_exists_get_key(item["request"], "header")]),
                        Param=self.combine_to_total_dict(
                            [{param["key"]: param["value"]} for param in
                             self.if_exists_get_key(item["request"]["url"], "query")]),
                        Data=fetch_data_by_mode(item),
                        File=fetch_file_for_form(item),
                        Dependency=fetch_dependency(item),
                        Assert=fetch_assert(item)
                    )
                    postman_json_data_list.append(api_json_dict)
                    order_count = order_count + 1
                postman_json_data_df = pd.DataFrame(data=postman_json_data_list)
                postman_json_data_groups_df = postman_json_data_groups_df.append(postman_json_data_df)
            return postman_json_data_groups_df
        except Exception:
            logger.exception("[Exception]：依据Postman集合文档自动生成接口抓包文档过程中发生异常，请检查！")
            sys.exit(1)

    def generate(self, capture_api_file):
        """
        生成接口抓包文档(当前支持Excel文件[xls/xlsx])
        :param capture_api_file: 接口抓包文档路径
        :return:
        """
        logger.info("[Initial]：开始通过Postman集合转换生成Excel接口抓包文档......")
        file_extend = str(os.path.splitext(capture_api_file)[-1]).lower()
        try:
            postman_collection_df = self.load_collection
            if file_extend not in [".xls", ".xlsx"]:
                logger.warning("[WARNING]：根据Postman集合自动生成的接口抓包文档扩展名当前仅支持[xls、xlsx]，请检查！")
                sys.exit(1)
            if file_extend in ['.xls', '.xlsx']:
                postman_collection_df.to_excel(capture_api_file, index=False)
            logger.info('[Done]：根据Postman集合自动生成的{}格式接口抓包文档已完成，路径为"{}".'.format(file_extend, capture_api_file))
        except Exception:
            logger.exception("[Exception]: 根据Postman集合自动生成{}格式接口抓包文档过程中发生异常，请检查！".format(file_extend))
            sys.exit(1)


class DirectPostmanTools(PostmanTools):
    """
    Postman操作工具类(跳过Swagger直接生成测试用例)
    """

    def __init__(self, postman_collection, groups=None):
        """
        初始化生成postman集合文档
        :param postman_collection: Postman集合文档绝对路径
        :param groups: 参数分组(默认为A组), 支持数量定义或名称列表定义
        """
        PostmanTools.__init__(self, postman_collection, groups)

    @property
    def load_collection(self):
        """
        依据Postman集合文档自动生成测试用例
        :return:
        """
        postman_json_data_groups_df = pd.DataFrame()
        items = self.postman_collection_dict["item"]

        def fetch_env(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 0:
                env_list = re.split(r'[\[|\]]', param_list[0])
                env = env_list[1]
                if env == "":
                    return "default"
                elif str(env).lower() == 'skip':
                    del param_list[0]
                    if param_list.__len__() > 0:
                        env1_list = re.split(r'[\[|\]]', param_list[0])
                        env1 = env1_list[1]
                        if env1 == "":
                            return "default"
                        else:
                            return env1
                    else:
                        return "default"
                else:
                    return env
            else:
                return "default"

        def fetch_skip(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 1:
                for param in param_list:
                    skip_list = re.split(r'[\[|\]]', param)
                    skip = skip_list[1]
                    if str(skip).lower() == 'skip':
                        return False
                return True
            else:
                return True

        def fetch_level(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 1:
                param_list = [param for param in param_list if str(param).lower() != '[skip]']
                if param_list.__len__() > 1:
                    level_list = re.split(r'[\[|\]]', param_list[1])
                    level = str(level_list[1]).lower()
                    if level in ['blocker', 'critical', 'normal', 'minor', 'trivial']:
                        return level
                    else:
                        return 'normal'
                else:
                    return 'normal'
            else:
                return 'normal'

        def fetch_scenario(item):
            if item["request"].__contains__("description"):
                if item["request"]["description"] == "":
                    scenario = "Scenario"
                else:
                    scenario = item["request"]["description"]
            else:
                scenario = "Scenario"
            return scenario

        def fetch_data_by_mode(item):
            data = ""
            if item["request"]["method"] in ["GET", "DELETE"]:
                data = ""
            if item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                if item["request"].__contains__("body"):
                    data_mode = item["request"]["body"]["mode"]
                    if data_mode == "urlencoded":
                        data = self.combine_to_total_dict([{data["key"]: data["value"]} for data in
                                                           self.if_exists_get_key(item["request"]["body"],
                                                                                  "urlencoded")])
                    if data_mode == "formdata":
                        data = self.combine_to_total_dict([{data["key"]: data["value"]} for data in
                                                           self.if_exists_get_key(item["request"]["body"],
                                                                                  "formdata") if
                                                           data["type"] == "text"])
                    if data_mode == "raw":
                        mode_type = item["request"]["body"]["options"]["raw"]["language"]
                        if mode_type == "json":
                            data = json.loads(
                                item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else "{}")
                            if data == {} and item["request"]["body"]["raw"] == "":
                                data = ""
                        if mode_type == "xml":
                            data = item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else ""
                        if mode_type == "text":
                            data = item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else ""
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data, indent=1, ensure_ascii=False)
            return data

        def fetch_file_for_form(item):
            def combine_to_file_list(file_dict_list):
                files = []
                for file_dict in file_dict_list:
                    file_key = file_dict["key"]
                    file_src = file_dict["src"]
                    if isinstance(file_src, str):
                        files.append((file_key, file_src))
                    if isinstance(file_src, list):
                        if file_src == []:
                            files.append((file_key, "no file"))
                        else:
                            for src in file_src:
                                files.append((file_key, src))
                return files

            files = ""
            if item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                if item["request"].__contains__("body"):
                    data_mode = item["request"]["body"]["mode"]
                    if data_mode == "formdata":
                        files = combine_to_file_list(
                            [file for file in self.if_exists_get_key(item["request"]["body"], "formdata") if
                             file["type"] == "file"])
            if files == []:
                files = ""
            return files

        def fetch_dependency(item):
            event_info = self.if_exists_get_key(item, "event")
            if event_info == []:
                return ""
            else:
                dependency_dict_list = [json.loads(self.to_dict_str("".join(event["script"]["exec"]))) for event in
                                        event_info if
                                        event["listen"] == "prerequest"]
                if dependency_dict_list == [] or dependency_dict_list == [{}]:
                    return ""
                else:
                    dependency_info = json.dumps(dependency_dict_list[0], indent=1, ensure_ascii=False)
                    return dependency_info

        def fetch_assert(item):
            event_info = self.if_exists_get_key(item, "event")
            if event_info == []:
                return ""
            else:
                assert_dict_list = [json.loads(self.to_dict_str("".join(event["script"]["exec"]))) for event in
                                    event_info if
                                    event["listen"] == "test"]
                if assert_dict_list == [] or assert_dict_list == [{}]:
                    return ""
                else:
                    assert_info = json.dumps(assert_dict_list[0], indent=1, ensure_ascii=False)
                    return assert_info

        def fetch_base_url(item):
            protocol = item["request"]["url"]["protocol"]
            host_path = ".".join(item["request"]["url"]["host"])
            if item["request"]["url"].__contains__("port"):
                port = item["request"]["url"]["port"]
                base_url = protocol + "://" + host_path + ":" + port
            else:
                base_url = protocol + "://" + host_path
            return base_url

        def fetch_consumes(item):
            consumes = "*/*"
            if item["request"]["header"] != []:
                for header in item["request"]["header"]:
                    if header["key"] == "Content-Type":
                        consumes = header["value"]
                        return consumes
                if item["request"]["method"] in ["GET", "DELETE"]:
                    return consumes
                elif item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                    if item["request"].__contains__("body"):
                        data_mode = item["request"]["body"]["mode"]
                        if data_mode == "urlencoded":
                            consumes = "application/x-www-form-urlencoded"
                        if data_mode == "formdata":
                            consumes = "multipart/form-data"
                        if data_mode == "raw":
                            mode_type = item["request"]["body"]["options"]["raw"]["language"]
                            if mode_type == "json":
                                consumes = "application/json"
                            if mode_type == "xml":
                                consumes = "application/xml"
                            if mode_type == "text":
                                consumes = "text/plain"
                        return consumes
                    else:
                        return consumes
                else:
                    return consumes
            else:
                if item["request"]["method"] in ["GET", "DELETE"]:
                    return consumes
                elif item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                    if item["request"].__contains__("body"):
                        data_mode = item["request"]["body"]["mode"]
                        if data_mode == "urlencoded":
                            consumes = "application/x-www-form-urlencoded"
                        if data_mode == "formdata":
                            consumes = "multipart/form-data"
                        if data_mode == "raw":
                            mode_type = item["request"]["body"]["options"]["raw"]["language"]
                            if mode_type == "json":
                                consumes = "application/json"
                            if mode_type == "xml":
                                consumes = "application/xml"
                            if mode_type == "text":
                                consumes = "text/plain"
                        return consumes
                    else:
                        return consumes
                else:
                    return consumes

        try:
            test_id = 1
            for group in self.groups:
                postman_json_data_list = []
                order_count = 1
                for item in items:
                    api_json_dict = dict(
                        ID="TC_" + str(test_id),
                        AID="API_" + str(test_id),
                        Project=self.postman_collection_dict["info"]["name"],
                        Scenario=fetch_scenario(item),
                        Title=item["name"],
                        BaseUrl=self.sync_url_with_environment(fetch_base_url(item)),
                        UrlPath="/" + "/".join(item["request"]["url"]["path"]),
                        Method=item["request"]["method"],
                        Consumes=fetch_consumes(item),
                        Platform=fetch_env(item["name"]),
                        Level=fetch_level(item['name']),
                        Active=fetch_skip(item['name']),
                        Group=group,
                        Order=order_count,
                        RequestPath="",
                        RequestHeader=self.combine_to_total_dict(
                            [{header["key"]: header["value"]} for header in
                             self.if_exists_get_key(item["request"], "header")]),
                        RequestParam=self.combine_to_total_dict(
                            [{param["key"]: param["value"]} for param in
                             self.if_exists_get_key(item["request"]["url"], "query")]),
                        RequestData=fetch_data_by_mode(item),
                        RequestFile=fetch_file_for_form(item),
                        DependencyInfo=fetch_dependency(item),
                        AssertInfo=fetch_assert(item),
                        ActualResponse='',
                        TestDescription='',
                        TestResult='',
                        UpdateTime=''
                    )
                    postman_json_data_list.append(api_json_dict)
                    order_count = order_count + 1
                    test_id = test_id + 1
                postman_json_data_df = pd.DataFrame(data=postman_json_data_list)
                postman_json_data_groups_df = postman_json_data_groups_df.append(postman_json_data_df)
            return postman_json_data_groups_df
        except Exception:
            logger.exception("[Exception]：依据Postman集合文档自动生成接口抓包文档过程中发生异常，请检查！")
            sys.exit(1)


class OrganizePostmanTools(PostmanTools):
    """
    Postman操作工具类(跳过Swagger直接生成测试用例，支持Postman一级分层文件夹)
    """

    def __init__(self, postman_collection, groups=None):
        """
        初始化生成postman集合文档
        :param postman_collection: Postman集合文档绝对路径
        :param groups: 参数分组(默认为A组), 支持数量定义或名称列表定义
        """
        PostmanTools.__init__(self, postman_collection, groups)

    @property
    def load_collection(self):
        """
        依据Postman集合文档自动生成测试用例
        :return:
        """
        postman_json_data_groups_df = pd.DataFrame()
        items = self.postman_collection_dict["item"]
        debug_watcher = None

        def fetch_env(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 0:
                env_list = re.split(r'[\[|\]]', param_list[0])
                env = env_list[1]
                if env == "":
                    return "default"
                elif str(env).lower() == 'skip':
                    del param_list[0]
                    if param_list.__len__() > 0:
                        env1_list = re.split(r'[\[|\]]', param_list[0])
                        env1 = env1_list[1]
                        if env1 == "":
                            return "default"
                        else:
                            return env1
                    else:
                        return "default"
                else:
                    return env
            else:
                return "default"

        def fetch_skip(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 1:
                for param in param_list:
                    skip_list = re.split(r'[\[|\]]', param)
                    skip = skip_list[1]
                    if str(skip).lower() == 'skip':
                        return False
                return True
            else:
                return True

        def fetch_level(item):
            param_list = re.findall(r'\[.*?\]', item)
            if param_list.__len__() > 1:
                param_list = [param for param in param_list if str(param).lower() != '[skip]']
                if param_list.__len__() > 1:
                    level_list = re.split(r'[\[|\]]', param_list[1])
                    level = str(level_list[1]).lower()
                    if level in ['blocker', 'critical', 'normal', 'minor', 'trivial']:
                        return level
                    else:
                        return 'normal'
                else:
                    return 'normal'
            else:
                return 'normal'

        def fetch_data_by_mode(item):
            data = ""
            if item["request"]["method"] in ["GET", "DELETE"]:
                data = ""
            if item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                if item["request"].__contains__("body"):
                    data_mode = item["request"]["body"]["mode"]
                    if data_mode == "urlencoded":
                        data = self.combine_to_total_dict([{data["key"]: data["value"]} for data in
                                                           self.if_exists_get_key(item["request"]["body"],
                                                                                  "urlencoded")])
                    if data_mode == "formdata":
                        data = self.combine_to_total_dict([{data["key"]: data["value"]} for data in
                                                           self.if_exists_get_key(item["request"]["body"],
                                                                                  "formdata") if
                                                           data["type"] == "text"])
                    if data_mode == "raw":
                        mode_type = item["request"]["body"]["options"]["raw"]["language"]
                        if mode_type == "json":
                            data = json.loads(
                                item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else "{}")
                            if data == {} and item["request"]["body"]["raw"] == "":
                                data = ""
                        if mode_type == "xml":
                            data = item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else ""
                        if mode_type == "text":
                            data = item["request"]["body"]["raw"] if item["request"]["body"]["raw"] != "" else ""
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data, indent=1, ensure_ascii=False)
            return data

        def fetch_file_for_form(item):
            def combine_to_file_list(file_dict_list):
                files = []
                for file_dict in file_dict_list:
                    file_key = file_dict["key"]
                    file_src = file_dict["src"]
                    if isinstance(file_src, str):
                        files.append((file_key, file_src))
                    if isinstance(file_src, list):
                        if file_src == []:
                            files.append((file_key, "no file"))
                        else:
                            for src in file_src:
                                files.append((file_key, src))
                return files

            files = ""
            if item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                if item["request"].__contains__("body"):
                    data_mode = item["request"]["body"]["mode"]
                    if data_mode == "formdata":
                        files = combine_to_file_list(
                            [file for file in self.if_exists_get_key(item["request"]["body"], "formdata") if
                             file["type"] == "file"])
            if files == []:
                files = ""
            return files

        def fetch_dependency(item):
            event_info = self.if_exists_get_key(item, "event")
            if event_info == []:
                return ""
            else:
                dependency_dict_list = [json.loads(self.to_dict_str("".join(event["script"]["exec"]))) for event in
                                        event_info if
                                        event["listen"] == "prerequest"]
                if dependency_dict_list == [] or dependency_dict_list == [{}]:
                    return ""
                else:
                    dependency_info = json.dumps(dependency_dict_list[0], indent=1, ensure_ascii=False)
                    return dependency_info

        def fetch_assert(item):
            event_info = self.if_exists_get_key(item, "event")
            if event_info == []:
                return ""
            else:
                assert_dict_list = [json.loads(self.to_dict_str("".join(event["script"]["exec"]))) for event in
                                    event_info if
                                    event["listen"] == "test"]
                if assert_dict_list == [] or assert_dict_list == [{}]:
                    return ""
                else:
                    assert_info = json.dumps(assert_dict_list[0], indent=1, ensure_ascii=False)
                    return assert_info

        def fetch_base_url(item):
            protocol = item["request"]["url"]["protocol"]
            host_path = ".".join(item["request"]["url"]["host"])
            if item["request"]["url"].__contains__("port"):
                port = item["request"]["url"]["port"]
                base_url = protocol + "://" + host_path + ":" + port
            else:
                base_url = protocol + "://" + host_path
            return base_url

        def fetch_consumes(item):
            consumes = "*/*"
            if item["request"]["header"] != []:
                for header in item["request"]["header"]:
                    if header["key"] == "Content-Type":
                        consumes = header["value"]
                        return consumes
                if item["request"]["method"] in ["GET", "DELETE"]:
                    return consumes
                elif item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                    if item["request"].__contains__("body"):
                        data_mode = item["request"]["body"]["mode"]
                        if data_mode == "urlencoded":
                            consumes = "application/x-www-form-urlencoded"
                        if data_mode == "formdata":
                            consumes = "multipart/form-data"
                        if data_mode == "raw":
                            mode_type = item["request"]["body"]["options"]["raw"]["language"]
                            if mode_type == "json":
                                consumes = "application/json"
                            if mode_type == "xml":
                                consumes = "application/xml"
                            if mode_type == "text":
                                consumes = "text/plain"
                        return consumes
                    else:
                        return consumes
                else:
                    return consumes
            else:
                if item["request"]["method"] in ["GET", "DELETE"]:
                    return consumes
                elif item["request"]["method"] in ["POST", "PUT", "PATCH"]:
                    if item["request"].__contains__("body"):
                        data_mode = item["request"]["body"]["mode"]
                        if data_mode == "urlencoded":
                            consumes = "application/x-www-form-urlencoded"
                        if data_mode == "formdata":
                            consumes = "multipart/form-data"
                        if data_mode == "raw":
                            mode_type = item["request"]["body"]["options"]["raw"]["language"]
                            if mode_type == "json":
                                consumes = "application/json"
                            if mode_type == "xml":
                                consumes = "application/xml"
                            if mode_type == "text":
                                consumes = "text/plain"
                        return consumes
                    else:
                        return consumes
                else:
                    return consumes

        try:
            test_id = 1
            for group in self.groups:
                postman_json_data_list = []
                order_count = 1
                for item in items:
                    if item.__contains__("item"):
                        for inner_item in item["item"]:
                            debug_watcher = {"CaseId": "TC_" + str(test_id),
                                             "CaseRoute": str(
                                                 self.postman_collection_dict["info"]["name"]) + " ☞ " + str(
                                                 item["name"]) + " ☞ " + str(
                                                 inner_item[
                                                     "name"]),
                                             "CaseUrl": "/" + "/".join(inner_item["request"]["url"]["path"])}
                            api_json_dict = dict(
                                ID="TC_" + str(test_id),
                                AID="API_" + str(test_id),
                                Project=self.postman_collection_dict["info"]["name"],
                                Scenario=item["name"],
                                Title=inner_item["name"],
                                BaseUrl=self.sync_url_with_environment(fetch_base_url(inner_item)),
                                UrlPath="/" + "/".join(inner_item["request"]["url"]["path"]),
                                Method=inner_item["request"]["method"],
                                Consumes=fetch_consumes(inner_item),
                                Platform=fetch_env(inner_item["name"]),
                                Level=fetch_level(inner_item['name']),
                                Active=fetch_skip(inner_item['name']),
                                Group=group,
                                Order=order_count,
                                RequestPath="",
                                RequestHeader=self.combine_to_total_dict(
                                    [{header["key"]: header["value"]} for header in
                                     self.if_exists_get_key(inner_item["request"], "header")]),
                                RequestParam=self.combine_to_total_dict(
                                    [{param["key"]: param["value"]} for param in
                                     self.if_exists_get_key(inner_item["request"]["url"], "query")]),
                                RequestData=fetch_data_by_mode(inner_item),
                                RequestFile=fetch_file_for_form(inner_item),
                                DependencyInfo=fetch_dependency(inner_item),
                                AssertInfo=fetch_assert(inner_item),
                                ActualResponse='',
                                TestDescription='',
                                TestResult='',
                                UpdateTime=''
                            )
                            postman_json_data_list.append(api_json_dict)
                            order_count = order_count + 1
                            test_id = test_id + 1
                postman_json_data_df = pd.DataFrame(data=postman_json_data_list)
                postman_json_data_groups_df = postman_json_data_groups_df.append(postman_json_data_df)
            return postman_json_data_groups_df
        except Exception:
            logger.exception("[Exception]：依据Postman集合文档自动生成表格测试用例过程中发生异常，Debug监测字典为{}，请检查！".format(debug_watcher))
            sys.exit(1)


class AggregatePostmanTools(object):
    """
    Postman集合聚合类(其会扫描指定用例文件夹下所有的Postman集合文档并聚合生成唯一表格用例)
    """

    def __init__(self, postman_collections_dir):
        """
        初始化Postman集合文档存放的文件夹绝对路径
        :param postman_collections_dir: 文件夹绝对路径
        """
        if os.path.exists(postman_collections_dir):
            self.postman_collections_dir = postman_collections_dir
        else:
            logger.warning('[WARNING]：Postman集合文档存放的文件夹路径"{}"当前并不存在，请指定合法路径！'.format(postman_collections_dir))
            sys.exit(1)

    def postman_collection_colletor(self):
        """
        收集当前文件夹下所有的Postman集合
        :return:
        """
        postman_collection_list = []
        for postman_collection in os.listdir(self.postman_collections_dir):
            if os.path.splitext(postman_collection)[1] == '.json':
                postman_collection_list.append(os.path.join(self.postman_collections_dir, postman_collection))
        return postman_collection_list

    def aggregate_collection(self):
        """
        聚合所有Postman集合文档
        :return:
        """
        try:
            postman_collection_list = self.postman_collection_colletor()
            postman_collection_df = pd.DataFrame()
            for postman_collection in postman_collection_list:
                postman_collection_load_df = OrganizePostmanTools(postman_collection=postman_collection,
                                                                  groups=1).load_collection
                postman_collection_df = pd.concat([postman_collection_df, postman_collection_load_df], axis=0)
            postman_collection_df = postman_collection_df.reset_index(drop=True)
            postman_collection_df_index_list = postman_collection_df.index.values.tolist()
            postman_collection_df.loc[:, 'ID'] = ["TC_" + str(index + 1) for index in postman_collection_df_index_list]
            postman_collection_df.loc[:, 'AID'] = ["API_" + str(index + 1) for index in
                                                   postman_collection_df_index_list]
            postman_collection_df.loc[:, 'Order'] = [index + 1 for index in postman_collection_df_index_list]
            return postman_collection_df
        except Exception:
            logger.exception("[Exception]：聚合Postman集合文档过程中发生异常，请检查！")
            sys.exit(1)

    def generate_testcase(self, testcase):
        """
        将聚合后的Postman集合文档生成表格测试用例(当前支持Excel文件[xls/xlsx])
        :param testcase: 表格测试用例
        :return:
        """
        logger.info("[Initial]：开始将聚合后的Postman集合文档转换生成表格测试用例......")
        file_extend = str(os.path.splitext(testcase)[-1]).lower()
        try:
            postman_collection_df = self.aggregate_collection()
            if file_extend not in [".xls", ".xlsx"]:
                logger.warning("[WARNING]：聚合后的Postman集合文档生成的表格测试用例扩展名当前仅支持[xls、xlsx]，请检查！")
                sys.exit(1)
            if file_extend in ['.xls', '.xlsx']:
                postman_collection_df.to_excel(testcase, index=False)
            logger.info('[Done]：聚合后的Postman集合文档已自动生成{}格式的表格测试用例，路径为"{}".'.format(file_extend, testcase))
        except Exception:
            logger.exception("[Exception]: 将聚合后的Postman集合文档自动生成{}格式的表格测试用例过程中发生异常，请检查！".format(file_extend))
            sys.exit(1)


if __name__ == '__main__':
    from Gastepo.Core.Base.BaseData import TESTCASE_PATH

    AggregatePostmanTools(postman_collections_dir=TESTCASE_PATH).generate_testcase(
        testcase=os.path.join(TESTCASE_PATH, "ApiTestCase_stg.xls"))
