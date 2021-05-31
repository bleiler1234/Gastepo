# -*- coding: utf-8 -*-

import json
import os
import sys

import pandas as pd
import requests

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class SwaggerTools(object):
    """
    Swagger爬取工具类
    """

    def __init__(self, swagger_doc_urls, swagger_domain_urls=None):
        """
        初始化Swagger接口文档。
        :param swagger_doc_urls: Swagger接口地址, 必须使用";"分隔。
        :param swagger_domain_urls: Swagger接口域名, 必须使用";"分隔。
        """
        # Swagger接口文档地址列表
        swagger_doc_url_list = [swagger_doc_url.strip() for swagger_doc_url in str(swagger_doc_urls).split(";") if
                                swagger_doc_url != ""]
        self.swagger_protocols = [swagger_doc_url.split(":")[0] for swagger_doc_url in swagger_doc_url_list]
        self.swagger_domain_url_list = [swagger_domain.strip() for swagger_domain in str(swagger_domain_urls).split(";")
                                        if
                                        swagger_domain != ""] if swagger_domain_urls is not None else swagger_domain_urls
        if isinstance(self.swagger_domain_url_list, list):
            if self.swagger_domain_url_list.__len__() < swagger_doc_url_list.__len__():
                logger.warning(
                    "[Warning]：当前配置文件中已有的Swagger替换域名少于Swagger接口文档地址列表，请检查并明确域名替换规则！[当前会默认启用首个域名替换全部Swagger请求域]")
                self.swagger_domain_url_list = [self.swagger_domain_url_list[0] for count in
                                                range(swagger_doc_url_list.__len__())]

        # JSON样式Swagger接口文档列表
        self.swagger_res_dict_list = []
        try:
            session = requests.session()
            for swagger_doc_url in swagger_doc_url_list:
                swagger_res = session.get(url=swagger_doc_url)
                self.swagger_res_dict_list.append(json.loads(swagger_res.text))
        except Exception:
            logger.exception("[Exception]: 请求Swagger过程中发生异常，请检查网络或服务状态！")
            sys.exit(1)

    @property
    def get_swagger_to_dict(self):
        """
        获取Swagger接口文档中可用信息。
        :return: swagger_data_dict_list
        """
        swagger_data_dict_list = []
        try:
            for id, swagger_res_dict in enumerate(self.swagger_res_dict_list):
                api_id_list = []
                api_path_list = []
                api_method_list = []
                api_scenario_list = []
                api_title_list = []
                api_consume_list = []
                swagger_api_name = swagger_res_dict.get("info").get("title")
                swagger_api_host = swagger_res_dict.get("host")
                swagger_api_host = swagger_api_host if swagger_api_host is not None else "ip:port"
                swagger_base_path = swagger_res_dict.get("basePath") if swagger_res_dict.get("basePath") != "/" else ""
                swagger_base_path = swagger_base_path if swagger_base_path is not None else "/basepath"
                swagger_api_urlpath = list(swagger_res_dict.get("paths").keys())
                for current_api_urlpath in swagger_api_urlpath:
                    current_api_methods = list(swagger_res_dict.get("paths").get(current_api_urlpath).keys())
                    for api_id, current_api_method in enumerate(current_api_methods):
                        api_id_list.append("API_{}".format(api_id + 1))
                        api_path_list.append(current_api_urlpath)
                        api_method_list.append(current_api_method)
                        tags = swagger_res_dict["paths"][current_api_urlpath][current_api_method]["tags"]
                        api_scenario_list.append(tags[0] if isinstance(tags, list) else None)
                        api_title_list.append(
                            swagger_res_dict["paths"][current_api_urlpath][current_api_method]["summary"])
                        temp = swagger_res_dict["paths"][current_api_urlpath][current_api_method]
                        consumes = temp["consumes"] if temp.__contains__("consumes") else None
                        api_consume_list.append(consumes[0] if isinstance(consumes, list) else None)
                swagger_data_dict = dict(ID=api_id_list,
                                         Project=swagger_api_name,
                                         Scenario=api_scenario_list,
                                         Title=api_title_list,
                                         BaseUrl="{}://{}".format(self.swagger_protocols[id],
                                                                  swagger_api_host) if self.swagger_domain_url_list is None else
                                         self.swagger_domain_url_list[id],
                                         UrlPath=["{}{}".format(str(swagger_base_path)[:-1], api_path) for api_path in
                                                  api_path_list],
                                         Method=api_method_list,
                                         Consumes=api_consume_list,
                                         Platform="",
                                         Level="Normal",
                                         Active=False,
                                         Group="",
                                         Order="",
                                         RequestPath='',
                                         RequestHeader='',
                                         RequestParam='',
                                         RequestData='',
                                         RequestFile='',
                                         DependencyInfo='',
                                         AssertInfo='',
                                         ActualResponse='',
                                         TestDescription='',
                                         TestResult='',
                                         UpdateTime=''
                                         )
                swagger_data_dict_list.append(swagger_data_dict)
            return swagger_data_dict_list
        except Exception:
            logger.exception("[Exception]: 转换Swagger为数据字典过程中发生异常，请检查！")
            sys.exit(1)

    @property
    def get_swagger_to_dataframe(self):
        """
        通过Swagger字典转换为数据帧。
        :return: swagger_dataframe
        """
        try:
            swagger_df_to_dict_list = []
            swagger_dict_list = self.get_swagger_to_dict
            for swagger_dict in swagger_dict_list:
                swagger_df_to_dict_list.extend(pd.DataFrame(data=swagger_dict).to_dict(orient='records'))
            swagger_dataframe = pd.DataFrame(data=swagger_df_to_dict_list).drop("ID", axis=1).reset_index().rename(
                columns={"index": "ID"})
            swagger_dataframe["ID"] = swagger_dataframe["ID"].apply(lambda x: "API_{}".format(x + 1))
            return swagger_dataframe
        except Exception:
            logger.exception("[Exception]: 转换Swagger为数据帧过程中发生异常，请检查！")
            sys.exit(1)

    def get_swagger_to_excel(self, file_path):
        """
        根据Swagger生成Excel接口文档。
        :param file_path: Excel文件路径。
        :return:
        """
        try:
            if str(os.path.splitext(file_path)[-1]).lower() not in [".xls", ".xlsx"]:
                logger.warning("[WARNING]：生成的Excel文件扩展名必须为xls或xlsx格式，请检查！")
                sys.exit(1)
            logger.info("[Initial]：开始通过Swagger转换生成Excel接口文档......")
            swagger_dataframe = self.get_swagger_to_dataframe
            swagger_dataframe.to_excel(file_path, index=False)
            logger.info('[Done]：已通过Swagger成功转换生成Excel接口文档，路径为"{}".'.format(file_path))
        except Exception:
            logger.exception("[Exception]: 通过Swagger生成Excel接口文档失败，请检查原因！")
            sys.exit(1)

    def get_swagger_to_csv(self, file_path, sep=r',', encoding='utf-8'):
        """
        根据Swagger生成CSV接口文档。
        :param file_path: CSV文件路径。
        :param sep: 文件分隔符,默认","。
        :param encoding: 文件编码格式。
        :return:
        """
        try:
            if str(os.path.splitext(file_path)[-1]).lower() != 'csv':
                logger.warning("[WARNING]：生成的CSV文件扩展名必须为csv格式，请检查！")
                sys.exit(1)
            logger.info("[Initial]：开始通过Swagger转换生成CSV接口文档......")
            swagger_dataframe = self.get_swagger_to_dataframe
            swagger_dataframe.to_csv(file_path, sep=sep, index=False, header=True, encoding=encoding)
            logger.info('[Done]：已通过Swagger成功转换生成CSV接口文档，路径为"{}".'.format(file_path))
        except Exception:
            logger.exception("[Exception]: 通过Swagger生成CSV接口文档失败，请检查原因！")
            sys.exit(1)


class EnvironmentSwaggerTools(SwaggerTools):
    """
    Swagger爬取工具类(依赖环境配置文件)
    """

    def __init__(self, env, domain=True):
        """
        根据环境配置初始化Swagger接口文档。
        :param env: 项目环境
        :param domain: 域名替换开关(默认开启)
        """
        env_params = YamlConfig(config=APPLICATION_CONFIG_FILE).get("swagger", 2).get(env)
        swagger_doc_urls = env_params.get("swagger_docs")
        if domain is True:
            domain_urls = env_params.get("domain_urls")
            SwaggerTools.__init__(self, swagger_doc_urls=swagger_doc_urls, swagger_domain_urls=domain_urls)
        else:
            SwaggerTools.__init__(self, swagger_doc_urls=swagger_doc_urls)

    def get_swagger_to_excel(self, file_path):
        """
        根据Swagger生成Excel接口文档。
        :param file_path: Excel文件路径。
        :return:
        """
        try:
            if str(os.path.splitext(file_path)[-1]).lower() not in [".xls", ".xlsx"]:
                logger.warning("[WARNING]：生成的Excel文件扩展名必须为xls或xlsx格式，请检查！")
                sys.exit(1)
            logger.info("[Initial]：开始通过Swagger转换生成Excel接口文档[依赖环境配置]......")
            swagger_dataframe = self.get_swagger_to_dataframe
            swagger_dataframe.to_excel(file_path, index=False)
            logger.info('[Done]：已通过Swagger成功转换生成Excel接口文档，路径为"{}".'.format(file_path))
        except Exception:
            logger.exception("[Exception]: 通过Swagger生成Excel接口文档失败，请检查原因！")
            sys.exit(1)

    def get_swagger_to_csv(self, file_path, sep=r',', encoding='utf-8'):
        """
        根据Swagger生成CSV接口文档。
        :param file_path: CSV文件路径。
        :param sep: 文件分隔符,默认","。
        :param encoding: 文件编码格式。
        :return:
        """
        try:
            if str(os.path.splitext(file_path)[-1]).lower() != 'csv':
                logger.warning("[WARNING]：生成的CSV文件扩展名必须为csv格式，请检查！")
                sys.exit(1)
            logger.info("[Initial]：开始通过Swagger转换生成CSV接口文档[依赖环境配置]......")
            swagger_dataframe = self.get_swagger_to_dataframe
            swagger_dataframe.to_csv(file_path, sep=sep, index=False, header=True, encoding=encoding)
            logger.info('[Done]：已通过Swagger成功转换生成CSV接口文档，路径为"{}".'.format(file_path))
        except Exception:
            logger.exception("[Exception]: 通过Swagger生成CSV接口文档失败，请检查原因！")
            sys.exit(1)


if __name__ == '__main__':
    from Gastepo.Core.Base.BaseData import TESTCASE_PATH

    EnvironmentSwaggerTools(env="stg", domain=True).get_swagger_to_excel(
        os.path.join(TESTCASE_PATH, "SwaggerApiDocs_stg.xls"))
