# -*- coding: utf-8 -*-

import datetime
import json
import sys
from datetime import timedelta

import requests
from jsonpath import jsonpath

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class ElkSupport(object):
    """
    ELK DSL查询功能类
    """

    def __init__(self, username="qa", password="123456"):
        """
        初始化并登录ELK
        :param username: Kibana账户
        :param password: Kibana密码
        """
        self._session = requests.session()
        login_res = self._session.post(url='http://esk.qa.com/api/security/v1/login',
                                       data=json.dumps({"username": str(username), "password": str(password)},
                                                       ensure_ascii=False),
                                       headers={"kbn-xsrf": ""})
        if login_res.status_code in [200, 204]:
            self.cookies_str = '&'.join([str(i) + "=" + str(j) for i, j in login_res.cookies.get_dict().items()])
        else:
            logger.error("【ELK】登录失败，异常响应信息为：{}".format(login_res.json()))
            sys.exit(1)

    def dsl_search(self, es_index, es_dsl):
        """
        ELK DSL查询
        :param es_index: ES索引
        :param es_dsl: ES查询语句
        :return:
        """
        if not isinstance(es_dsl, dict):
            logger.exception("【ELK】DSL查询语句类型错误，请用字典形式指定！")
        else:
            es_res = self._session.post(
                url='http://esk.qa.com/api/console/proxy?path={}%2F_search%3Ftrack_total_hits%3Dtrue&method=POST'
                    .format(str(es_index)),
                data=json.dumps(es_dsl, ensure_ascii=False),
                headers={"kbn-xsrf": "", "Cookie": "{}".format(self.cookies_str), 'Content-Type': 'application/json'})
            if es_res.status_code == 200:
                return es_res
            else:
                logger.error(
                    "【ELK】查询失败，执行的DSL语句为：\n{}\n\n异常响应信息如下：\n{}".format(json.dumps(es_dsl, ensure_ascii=False, indent=2),
                                                                       json.dumps(es_res.json(), ensure_ascii=False,
                                                                                  indent=2)))
                sys.exit(1)

    def page_frequency(self, es_index, es_dsl):
        """
        计算ELK查询分页频次（size:10000条）
        :param es_index: ES索引
        :param es_dsl: ES查询语句
        :return:
        """
        es_res = self.dsl_search(es_index, es_dsl)
        if es_res:
            hits_count_list = jsonpath(es_res.json(), "$.hits.total.value")
            if hits_count_list:
                hits_count = hits_count_list[0]
                if hits_count == 0:
                    logger.warning("【ELK】DSL查询结果为空，请知悉！")
                    sys.exit(1)
                logger.info("【ELK】DSL查询匹配结果总量为：{}".format(hits_count))
                pages = divmod(hits_count, 10000)
                total_page = pages[0]
                leave_page = pages[1]
                if total_page == 0:
                    logger.info("【ELK】已计算数据采集预期DSL分页频次为：1")
                    return dict(count=hits_count, frequency=1, total_page=1, leave_page=0)
                elif total_page > 0 and leave_page == 0:
                    logger.info("【ELK】已计算数据采集预期DSL分页频次为：{}".format(total_page))
                    return dict(count=hits_count, frequency=total_page, total_page=total_page, leave_page=0)
                elif total_page > 0 and leave_page > 0:
                    logger.info("【ELK】已计算数据采集预期DSL分页频次为：{}".format(total_page + 1))
                    return dict(count=hits_count, frequency=total_page + 1, total_page=total_page, leave_page=1)
                else:
                    logger.warning("【ELK】未成功计算预期DSL分页频次，请检查！")
                    sys.exit(1)
            else:
                logger.error("【ELK】查询匹配结果总量获取失败，请检查查询结果或JsonPath表达式是否合法！")
                sys.exit(1)
        else:
            logger.warning("【ELK】由于DSL查询失败，导致结果总量未能获取！")
            sys.exit(1)

    def time_frequency(self, start, end):
        """
        计算ELK查询时间分片（hour:1小时）
        :param start: 开始时间
        :param end: 结束时间
        :return:
        """

        def str_to_format(datetime_str):
            temp_datetime = str(datetime_str).split(r"T")
            temp_date = temp_datetime[0]
            temp_time = temp_datetime[1].split(r".")[0]
            format_datetime = " ".join([temp_date, temp_time])
            return format_datetime

        def dt_to_format(dt):
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        start_datetime = datetime.datetime.strptime(str_to_format(start), "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.datetime.strptime(str_to_format(end), "%Y-%m-%d %H:%M:%S")
        interval_days = (end_datetime - start_datetime).days
        interval_hours = int((end_datetime - start_datetime).seconds / 3600)
        total_hours = interval_days * 24 + interval_hours
        logger.info("【ELK】起止时间共相差{}天{}小时，则数据采集预期DSL时间分片总数为：{}".format(interval_days, interval_hours, total_hours))
        hours_interval_list = []
        for hours in range(1, total_hours + 1):
            hours_interval_list.append(
                dict(start=dt_to_format(start_datetime), end=dt_to_format(start_datetime + timedelta(hours=1))))
            start_datetime = start_datetime + timedelta(hours=1)
        return hours_interval_list


class EnvironmentELkTools(ElkSupport):
    """
    ELK操作工具类(依赖环境配置文件)
    """

    def __init__(self):
        """
        根据环境配置初始化ELK连接信息
        """
        env_params = YamlConfig(config=APPLICATION_CONFIG_FILE).get("elk")
        username = str(env_params.get("username"))
        password = str(env_params.get("password"))
        ElkSupport.__init__(self, username=username, password=password)
