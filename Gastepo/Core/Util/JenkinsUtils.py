# -*- coding: utf-8 -*-

import re
import sys

from jenkins import Jenkins

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Util.CommonUtils import trans_timestamp
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class JenkinsTools(object):
    """
    Jenkins操作工具类
    """

    def __init__(self, url, username, password):
        """
        初始化Jenkins连接信息
        :param url: Jenkins地址
        :param username: 登录用户名
        :param password: 登录密码
        """
        try:
            self.session = Jenkins(url=url,
                                   username=username,
                                   password=password)
        except Exception:
            logger.exception('初始化Jenkins连接过程中发生异常，请检查!')

    @property
    def get_session(self):
        """
        返回Jenkins会话
        :return:
        """
        return self.session

    def get_job_info(self, job_name):
        """
        获取构建项目信息
        :param job_name: 构建项目名称
        :return:
        """
        try:
            if self.session.job_exists(name=job_name):
                info = self.session.get_job_info(name=job_name)
                return info
            else:
                logger.warning('[WARNING]: Jenkins构建项目"{}"并不存在，请检查!'.format(job_name))
                sys.exit(1)
        except Exception:
            logger.exception('查看Jenkins构建项目"{}"过程中发生异常，请检查!'.format(job_name))

    def get_job_info_by_regex(self, pattern):
        """
        正则表达式方式获取构建项目信息
        :param pattern: 构建项目名称（正则表达式）
        :return:
        """
        try:
            info_regex = self.session.get_job_info_regex(pattern=pattern)
            return info_regex
        except Exception:
            logger.exception('通过正则表达式"{}"查看匹配构建项目过程中发生异常，请检查!'.format(pattern))

    def get_job_build_info(self, job_name, build_number):
        """
        通过构建项目名称及构建任务ID查看构建信息
        :param job_name: 构建项目名称
        :param build_number: 构建ID
        :return:
        """
        try:
            result = self.session.get_build_info(name=job_name, number=build_number)
            return result
        except Exception:
            logger.exception('通过构建项目名称"{}"和构建ID"{}"查看构建信息过程中发生异常，请检查!'.format(
                job_name, build_number))

    def rebase_build_info(self, job_name):
        """
        获取指定项目名称的自定义构建信息
        :param job_name: 构建项目名称
        :return: 构建信息自定义响应体
        """
        response_list = []
        try:
            job_set = self.get_job_info(job_name)
            if job_set['lastBuild'] is not None:
                response_list.append(dict(ActionJob=job_set['displayName'],
                                          LastNumber=job_set['lastBuild']['number'],
                                          Building=
                                          self.get_job_build_info(job_set['displayName'],
                                                                  job_set['lastBuild']['number'])[
                                              'building'],
                                          Result=
                                          self.get_job_build_info(job_set['displayName'],
                                                                  job_set['lastBuild']['number'])[
                                              'result'],
                                          Time=trans_timestamp(
                                              self.get_job_build_info(job_set['displayName'],
                                                                      job_set['lastBuild']['number'])[
                                                  'timestamp'])
                                          )
                                     )
            else:
                response_list.append(dict(ActionJob=job_set['displayName'],
                                          LastBuild="No latest build job info now."))
            return response_list
        except Exception:
            logger.exception('通过构建项目名称"{}"查看其自定义构建信息过程中发生异常，请检查!'.format(job_name))

    def rebase_build_info_by_regex(self, pattern):
        """
        获取匹配正则表达式项目名称的自定义构建信息
        :param pattern: 构建项目名称（正则表达式）
        :return: 构建信息自定义响应体
        """
        response_list = []
        try:
            job_set = self.get_job_info_by_regex(pattern)
            if len(job_set) != 0:
                for i in job_set:
                    if i['lastBuild'] is not None:
                        response_list.append(dict(ActionJob=i['displayName'],
                                                  LastNumber=i['lastBuild']['number'],
                                                  Building=
                                                  self.get_build_info(i['displayName'], i['lastBuild']['number'])[
                                                      'building'],
                                                  Result=
                                                  self.get_build_info(i['displayName'], i['lastBuild']['number'])[
                                                      'result'],
                                                  Time=trans_timestamp(
                                                      self.get_build_info(i['displayName'], i['lastBuild']['number'])[
                                                          'timestamp'])
                                                  ,
                                                  Operator=
                                                  self.get_build_info(i['displayName'], i['lastBuild']['number'])[
                                                      'actions'][0]['causes'][0]['shortDescription']
                                                  )
                                             )
                    else:
                        response_list.append(dict(ActionJob=i['displayName'],
                                                  LastBuild="No latest build job info now."))
            return response_list
        except re.error:
            return "invalid pattern"
        except Exception:
            logger.exception('通过正则表达式"{}"查看匹配项目的自定义构建信息过程中发生异常，请检查!'.format(pattern))

    def stop_job_latest_build(self, job_name):
        """
        停止匹配正则表达式的构建项目的最近构建任务
        :param job_name: 构建项目名称
        :return:
        """
        try:
            lastNumber = self.rebase_build_info(job_name=job_name)[0]['LastNumber']
            self.session.stop_build(name=job_name, number=lastNumber)
        except Exception:
            logger.exception('停止匹配正则表达式"{}"的构建项目的最近构建任务过程中发生异常，请检查!'.format(job_name))


class EnvironmentJenkinsTools(JenkinsTools):
    """
    Jenkins操作工具类(依赖环境配置文件)
    """

    def __init__(self):
        """
        根据环境配置初始化Jenkins连接信息
        """
        env_params = YamlConfig(config=APPLICATION_CONFIG_FILE).get("jenkins")
        url = str(env_params.get("url"))
        username = str(env_params.get("username"))
        password = str(env_params.get("password"))
        JenkinsTools.__init__(self, url=url, username=username, password=password)


if __name__ == '__main__':
    demo = EnvironmentJenkinsTools()

    print(demo.rebase_build_info(job_name="Api_Business_Automation"))
    print(demo.stop_job_latest_build(job_name="Api_Business_Automation"))
