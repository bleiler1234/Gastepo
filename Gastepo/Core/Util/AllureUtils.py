# -*- coding: utf-8 -*-

import os
import shutil
import time
from subprocess import CalledProcessError

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Base.BaseData import RESULT_PATH, REPORT_PATH, RESOURCE_PATH
from Gastepo.Core.Util.CommonUtils import run_command
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger

ALLURE_RESULT = RESULT_PATH
ALLURE_REPORT = REPORT_PATH
CHECK_COUNT = YamlConfig(config=APPLICATION_CONFIG_FILE).get("allure", 2).get("check_count")

class AllureTools(object):
    """
    Allure测试报告操作类
    """

    @classmethod
    def check_result(cls, check_count=CHECK_COUNT):
        """
        检查Allure测试结果json文件是否生成。
        :param check_count: 检测次数。
        :return:
        """
        check_result = None
        for count in range(check_count):
            if os.listdir(ALLURE_RESULT) == list() and count < check_count:
                if count == check_count - 1:
                    logger.warning("仍未检测到Allure测试结果json文件，已达检测次数上限({})，停止检测。".format(check_count))
                    check_result = False
                    break
                logger.info("未检测到Allure测试结果json文件，可能正在生成......")
                time.sleep(2)
                continue
            if os.listdir(ALLURE_RESULT) != list():
                logger.info("[Success]：已检测到Allure测试结果json文件.")
                check_result = True
                break
        return check_result

    @classmethod
    def generate_report(cls):
        """
        根据json结果文件自动生成Allure测试报告。
        """
        try:
            if cls.check_result() is True:
                command = "allure generate {0} -o {1} --clean".format(ALLURE_RESULT, ALLURE_REPORT)
                time.sleep(1)
                logger.info('开始执行Allure测试报告生成命令："{}"'.format(command))
                run_command(command)
                logger.info("[Done]：已经成功生成Allure测试报告.")
            else:
                logger.warning("[Warning]：由于未检测到Allure测试结果json文件，停止生成Allure测试报告！")
        except CalledProcessError:
            logger.exception("[Exception]：Allure测试报告生成命令执行失败！")
        except Exception:
            logger.exception("[Exception]：生成Allure测试报告过程中发生异常，请检查！")

    @classmethod
    def clear_result(cls):
        """
        清空Allure测试结果json文件。
        """
        try:
            if os.listdir(ALLURE_RESULT) != list():
                time.sleep(1)
                shutil.rmtree(ALLURE_RESULT)
                os.mkdir(ALLURE_RESULT)
                logger.info("[Success]：已经成功清空Allure历史测试结果.")
            else:
                logger.info("当前暂无Allure历史测试结果，无需清除操作！")
        except Exception:
            logger.exception("[Exception]：清空Allure历史测试结果过程中发生异常，请检查！")

    @classmethod
    def sync_history(cls):
        """
        追加Allure历史追溯信息
        :return:
        """
        ALLURE_REPORT_HISTORY = os.path.join(ALLURE_REPORT, "history")
        ALLURE_RESULT_HISTORY = os.path.join(ALLURE_RESULT, "history")
        try:
            if os.path.exists(ALLURE_RESULT_HISTORY):
                raise FileExistsError
            if os.path.exists(ALLURE_REPORT_HISTORY):
                time.sleep(1)
                shutil.copytree(ALLURE_REPORT_HISTORY, ALLURE_RESULT_HISTORY)
                logger.info("[Success]：已经成功同步Allure历史追溯信息.")
            else:
                logger.warning('[WARNING]：Allure历史追溯信息"{}"当前并不存在，无法完成同步！'.format(ALLURE_REPORT_HISTORY))
        except FileExistsError:
            logger.exception('[Exception]：已同步Allure历史追溯信息至"{}"，无需再次同步！'.format(ALLURE_RESULT_HISTORY))
        except Exception:
            logger.exception("[Exception]：同步Allure历史追溯信息过程中发生异常，请检查！")

    @classmethod
    def sync_environment(cls):
        """
        同步Allure环境信息文件
        :return:
        """
        ENVIRONMENT_INFO = os.path.join(RESOURCE_PATH, "Allure", "environment.properties")
        try:
            if os.path.exists(ENVIRONMENT_INFO):
                time.sleep(1)
                shutil.copyfile(ENVIRONMENT_INFO, os.path.join(ALLURE_RESULT, "environment.properties"))
                logger.info("[Success]：已经成功同步Allure环境信息文件.")
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.exception('[Exception]：Allure环境信息文件"{}"并不存在，无法同步，请检查！'.format(ENVIRONMENT_INFO))
        except Exception:
            logger.exception("[Exception]：同步Allure环境信息文件过程中发生异常，请检查！")

    @classmethod
    def sync_categories(cls):
        """
        同步Allure测试分类文件
        :return:
        """
        CATEGORIES_INFO = os.path.join(RESOURCE_PATH, "Allure", "categories.json")
        try:
            if os.path.exists(CATEGORIES_INFO):
                time.sleep(1)
                shutil.copyfile(CATEGORIES_INFO, os.path.join(ALLURE_RESULT, "categories.json"))
                logger.info("[Success]：已经成功同步Allure测试分类文件.")
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.exception('[Exception]：Allure测试分类文件"{}"并不存在，无法同步，请检查！'.format(CATEGORIES_INFO))
        except Exception:
            logger.exception("[Exception]：同步Allure测试分类文件过程中发生异常，请检查！")

    @classmethod
    def initial_allure(cls):
        """
        初始化Allure
        :return:
        """
        try:
            logger.info('[Initial]：开始初始化Allure......')
            cls.clear_result()
            if os.path.exists(ALLURE_REPORT):
                cls.sync_history()
            cls.sync_environment()
            cls.sync_categories()
            logger.info("[Done]：已经成功初始化Allure.")
        except Exception:
            logger.exception("[Exception]：初始化Allure过程中发生异常，请检查！")


if __name__ == '__main__':
    AllureTools.generate_report()
