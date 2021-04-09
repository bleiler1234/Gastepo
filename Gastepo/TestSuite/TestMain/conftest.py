# -*- coding: utf-8 -*-

import os

import pytest

from Gastepo.Core.Base.BaseData import RESOURCE_PATH
from Gastepo.Core.Util.AllureUtils import AllureTools
from Gastepo.Core.Util.DingUtils import EnvironmentDingTools
from Gastepo.Core.Util.LogUtils import logger


def pytest_sessionstart():
    """
    【开启自动化测试会话】
    :return:
    """
    pass


@pytest.fixture(name="自动化测试全局跟踪", scope="session", autouse=True)
def auto_test_trance():
    """
    【自动化测试全局跟踪】~ 用于重置Allure测试报告信息、跟踪自动化测试用例执行情况等。
    :return:
    """
    logger.info("☞【开始重置环境】")
    # 初始化Allure报告
    AllureTools.initial_allure()
    logger.info("☞【执行测试用例】")
    yield
    logger.info("[Bingo]：E2E接口自动化测试执行完毕.")


def pytest_sessionfinish():
    """
    【终止自动化测试会话】~ 用于测试报告、邮件通知、钉钉提醒等。
    :return:
    """
    logger.info("☞【同步测试结果】")
    AllureTools.generate_report()
    # Email().send("E2E接口自动化测试完成，请查阅报告。")
    EnvironmentDingTools(ding_notify_file=os.path.join(RESOURCE_PATH, "Ding", "DingNotifyTemplate.json"),
                         preview_mode=True).send(msgtype='markdown')
    logger.info("O(∩_∩)O【自动化测试全部完成】")
