# -*- coding: utf-8 -*-

import os

import pandas as pd

from Gastepo.Core.Base.CustomException import DotTypeError
from Gastepo.Core.Util.LogUtils import logger


class DataframeOperation(object):
    """
    测试用例数据操作类
    注意：str时结果为Series系列；list时结果为DataFrame数据帧.
    """

    def __init__(self, test_case_file):
        """
        初始化用例文件DataFrame。
        :param test_case_file: 用例文件绝对路径
        """
        file_extension = os.path.splitext(str(test_case_file))[-1]
        try:
            if not os.path.exists(test_case_file):
                raise FileNotFoundError
            if file_extension == "":
                logger.exception("未检测到包含用例文件扩展名的合法路径，请仔细检查！")
            if str(file_extension).lower() in ['.xls', '.xlsx']:
                self.test_case_df = pd.read_excel(test_case_file).set_index("ID",
                                                                            drop=False).fillna(
                    "")
            elif str(file_extension).lower() in ['.csv', '.txt']:
                self.test_case_df = pd.read_csv(test_case_file, sep=r',').set_index("ID",
                                                                                    drop=False).fillna(
                    "")
            else:
                raise DotTypeError
        except DotTypeError:
            logger.exception(
                '非法文件扩展名"{}", 当前仅支持xls、xlsx、csv、txt用例文件扩展名.'.format(file_extension))
        except FileNotFoundError:
            logger.exception('当前用例文件"{}"并不存在，请检查路径！'.format(test_case_file))
        except Exception:
            logger.exception("初始化用例DataFrame过程中发生异常，请检查！")

    @property
    def T(self):
        """
        用例文件DataFrame矩阵转置。
        :return:
        """
        return self.test_case_df.stack().unstack(0)

    @property
    def df(self):
        """
        获取test_case_dataframe。
        :return:
        """
        return self.test_case_df

    def get_all_data(self, check_active=False):
        """
        获取全部数据。
        :param check_active: 校验开关(True:仅获取Active=True的用例 False:获取全部用例)
        :return:
        """
        if check_active is False:
            return self.test_case_df
        else:
            return self.test_case_df[self.test_case_df["Active"] == True]

    def get_group_data(self, id=[], group=[], order=[], check_active=False):
        """
        获取分组修饰的数据。
        :param id: 用例编号列表，如["TC_1", "TC_2"], 开启id参数后，分组group及序号order不生效。
        :param group: 分组名称列表，如["A", "B"]
        :param order: 用例顺序列表，如[1, 2]
        :param check_active: 校验开关
        :return:
        """
        if not isinstance(id, list):
            logger.warning('[WARNING]：用例编号参数id必须以列表方式入参，如["TC_1","TC_2"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(group, list):
            logger.warning('[WARNING]：测试分组参数group必须以列表方式入参，如["A","B"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(order, list):
            logger.warning('[WARNING]：用例顺序参数order必须以列表方式入参，如[1,2]方式！')
            import sys
            sys.exit(1)
        if id != [] and check_active is False:
            return self.test_case_df[self.test_case_df["ID"].isin(id)]
        if id != [] and check_active is True:
            return self.test_case_df[(self.test_case_df["Active"] == True) & (self.test_case_df["ID"].isin(id))]
        if id == [] and group == [] and order == [] and check_active is False:
            return self.get_all_data(check_active=False)
        if id == [] and group == [] and order == [] and check_active is True:
            return self.get_all_data(check_active=True)
        if id == [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Group"].isin(group)]
        if id == [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[(self.test_case_df["Active"] == True) & (self.test_case_df["Group"].isin(group))]
        if id == [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[self.test_case_df["Order"].isin(order)]
        if id == [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[(self.test_case_df["Active"] == True) & (self.test_case_df["Order"].isin(order))]
        if id == [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Group"].isin(group)) & (self.test_case_df["Order"].isin(order))]
        if id == [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]

    def get_descriptor_data(self, scenario=[], platform=[], level=[], check_active=False):
        """
        获取描述符修饰的数据。
        :param scenario: 场景名称，如["测试场景"]
        :param platform: 场景平台，如["患者H5"]
        :param level: 用例级别，如["blocker"]
        :param check_active: 校验开关
        :return:
        """
        if not isinstance(scenario, list):
            logger.warning('[WARNING]：场景名称参数scenario必须以列表方式入参，如["测试场景"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(platform, list):
            logger.warning('[WARNING]：场景平台参数platform必须以列表方式入参，如["患者H5"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(level, list):
            logger.warning('[WARNING]：用例级别参数Level必须以列表方式入参，如["blocker"]方式！')
            import sys
            sys.exit(1)
        if scenario == [] and platform == [] and level == [] and check_active is False:
            return self.get_all_data(check_active=False)
        if scenario == [] and platform == [] and level == [] and check_active is True:
            return self.get_all_data(check_active=True)
        if scenario != [] and platform == [] and level == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Scenario"].isin(scenario)]
        if scenario != [] and platform == [] and level == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario))]
        if scenario == [] and platform == [] and level != [] and check_active is False:
            return self.test_case_df[self.test_case_df["Level"].isin(level)]
        if scenario == [] and platform == [] and level != [] and check_active is True:
            return self.test_case_df[(self.test_case_df["Active"] == True) & (self.test_case_df["Level"].isin(level))]
        if scenario == [] and platform != [] and level == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Platfrom"].isin(platform)]
        if scenario == [] and platform != [] and level == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform))]
        if scenario != [] and level != [] and platform == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Level"].isin(level))]
        if scenario != [] and level != [] and platform == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Level"].isin(level))]
        if scenario != [] and platform != [] and level == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform))]
        if scenario != [] and platform != [] and level == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform))]
        if scenario == [] and platform != [] and level != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Level"].isin(level))]
        if scenario == [] and platform != [] and level != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level))]
        if scenario != [] and platform != [] and level != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level))]
        if scenario != [] and platform != [] and level != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level))]

    def get_entire_data(self, id=[], scenario=[], platform=[], level=[], group=[], order=[], check_active=False):
        """
        获取全量修饰的数据。
        :param id: 用例编号列表，如["TC_1", "TC_2"], 开启id参数后，分组group及序号order不生效。
        :param scenario: 场景名称，如["测试场景"]
        :param platform: 场景平台，如["患者H5"]
        :param level: 用例级别，如["blocker"]
        :param group: 分组名称列表，如["A", "B"]
        :param order: 用例顺序列表，如[1, 2]
        :param check_active: 校验开关
        :return:
        """
        if not isinstance(id, list):
            logger.warning('[WARNING]：用例编号参数id必须以列表方式入参，如["TC_1","TC_2"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(scenario, list):
            logger.warning('[WARNING]：场景名称参数scenario必须以列表方式入参，如["测试场景"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(platform, list):
            logger.warning('[WARNING]：场景平台参数platform必须以列表方式入参，如["患者H5"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(level, list):
            logger.warning('[WARNING]：用例级别参数Level必须以列表方式入参，如["blocker"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(group, list):
            logger.warning('[WARNING]：测试分组参数group必须以列表方式入参，如["A","B"]方式！')
            import sys
            sys.exit(1)
        if not isinstance(order, list):
            logger.warning('[WARNING]：用例顺序参数order必须以列表方式入参，如[1,2]方式！')
            import sys
            sys.exit(1)
        if id != [] and check_active is False:
            return self.test_case_df[self.test_case_df["ID"].isin(id)]
        if id != [] and check_active is True:
            return self.test_case_df[(self.test_case_df["Active"] == True) & (self.test_case_df["ID"].isin(id))]
        if id == [] and scenario == [] and platform == [] and level == [] and group == [] and order == [] and check_active is False:
            return self.get_all_data(check_active=False)
        if id == [] and scenario == [] and platform == [] and level == [] and group == [] and order == [] and check_active is True:
            return self.get_all_data(check_active=True)
        if id == [] and scenario != [] and platform == [] and level == [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Scenario"].isin(scenario)]
        if id == [] and scenario != [] and platform == [] and level == [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario))]
        if id == [] and scenario == [] and platform != [] and level == [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Platform"].isin(platform)]
        if id == [] and scenario == [] and platform != [] and level == [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform))]
        if id == [] and scenario == [] and platform == [] and level != [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Level"].isin(level)]
        if id == [] and scenario == [] and platform == [] and level != [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Level"].isin(level))]
        if id == [] and scenario == [] and platform == [] and level == [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[self.test_case_df["Group"].isin(group)]
        if id == [] and scenario == [] and platform == [] and level == [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform == [] and level == [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[self.test_case_df["Order"].isin(order)]
        if id == [] and scenario == [] and platform == [] and level == [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level == [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform))]
        if id == [] and scenario != [] and platform != [] and level == [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform))]
        if id == [] and scenario != [] and platform == [] and level != [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Level"].isin(level))]
        if id == [] and scenario != [] and platform == [] and level != [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Level"].isin(level))]
        if id == [] and scenario != [] and platform == [] and level == [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform == [] and level == [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform == [] and level == [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level == [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level != [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Level"].isin(level))]
        if id == [] and scenario == [] and platform != [] and level != [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level))]
        if id == [] and scenario == [] and platform != [] and level == [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform != [] and level == [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform != [] and level == [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level == [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform == [] and level != [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Level"].isin(level)) & (self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform == [] and level != [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform == [] and level != [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Level"].isin(level)) & (self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform == [] and level != [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform == [] and level == [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Group"].isin(group)) & (self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform == [] and level == [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level != [] and group == [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level))]
        if id == [] and scenario != [] and platform != [] and level != [] and group == [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level))]
        if id == [] and scenario != [] and platform != [] and level == [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform != [] and level == [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform != [] and level == [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level == [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level != [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform != [] and level != [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario == [] and platform != [] and level != [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level != [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform == [] and level != [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Level"].isin(level)) & (self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform == [] and level != [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level != [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform == [] and level != [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform == [] and level != [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level != [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level == [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level == [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level == [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level == [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level != [] and group != [] and order == [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform != [] and level != [] and group != [] and order == [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group))]
        if id == [] and scenario != [] and platform != [] and level != [] and group == [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level != [] and group == [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level == [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level == [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level != [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform == [] and level != [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level != [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Platform"].isin(platform)) & (self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario == [] and platform != [] and level != [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level != [] and group != [] and order != [] and check_active is False:
            return self.test_case_df[
                (self.test_case_df["Scenario"].isin(scenario)) & (self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]
        if id == [] and scenario != [] and platform != [] and level != [] and group != [] and order != [] and check_active is True:
            return self.test_case_df[
                (self.test_case_df["Active"] == True) & (self.test_case_df["Scenario"].isin(scenario)) & (
                    self.test_case_df["Platform"].isin(platform)) & (
                    self.test_case_df["Level"].isin(level)) & (
                    self.test_case_df["Group"].isin(group)) & (
                    self.test_case_df["Order"].isin(order))]

    def get_all_data_to_dict(self, check_active=False, orient="records"):
        """
        获取全部数据并转换成字典。
        :param check_active: 校验开关(True:仅获取Active=True的用例 False:获取全部用例)
        :return:
        """
        return self.get_all_data(check_active=check_active).to_dict(orient=orient)

    def get_group_data_to_dict(self, id=[], group=[], order=[], check_active=False, orient="records"):
        """
        获取分组修饰的数据并转换成字典。
        :param id: 用例编号列表，如["TC_1", "TC_2"]
        :param group: 分组名称列表，如["A", "B"]
        :param order: 用例顺序列表，如[1, 2]
        :param check_active: 校验开关
        :return:
        """
        return self.get_group_data(id=id, group=group, order=order, check_active=check_active).to_dict(orient=orient)

    def get_descriptor_data_to_dict(self, scenario=[], platform=[], level=[], check_active=False, orient="records"):
        """
        获取描述符修饰的数据并转换成字典。
        :param scenario: 场景名称，如["测试场景"]
        :param platform: 场景平台，如["患者H5"]
        :param level: 用例级别，如["blocker"]
        :param check_active: 校验开关
        :return:
        """
        return self.get_descriptor_data(scenario=scenario, platform=platform, level=level,
                                        check_active=check_active).to_dict(
            orient=orient)

    def get_entire_data_to_dict(self, id=[], scenario=[], platform=[], level=[], group=[], order=[], check_active=False,
                                orient="records"):
        """
        获取全量修饰的数据并转换成字典。
        :param id: 用例编号列表，如["TC_1", "TC_2"], 开启id参数后，分组group及序号order不生效。
        :param scenario: 场景名称，如["测试场景"]
        :param platform: 场景平台，如["患者H5"]
        :param level: 用例级别，如["blocker"]
        :param group: 分组名称列表，如["A", "B"]
        :param order: 用例顺序列表，如[1, 2]
        :param check_active: 校验开关
        :return:
        """
        return self.get_entire_data(id=id, scenario=scenario, platform=platform, level=level, group=group, order=order,
                                    check_active=check_active).to_dict(orient=orient)

    def set_cell_data(self, indexs, columns, values):
        """
        设置单元格数据。
        :param indexs: 索引（str或list）
        :param columns: 列名（str或list）
        :param values: 赋值（str或list）
        :return:
        """
        self.test_case_df.loc[indexs, columns] = values

    def get_cell_data(self, indexs, columns):
        """
        获取单元格数据。
        :param indexs: 索引（str或list）
        :param columns: 列名（str或list）
        :return:
        """
        return self.test_case_df.loc[indexs, columns]

    def get_row_data(self, indexs):
        """
        获取整行数据。
        :param indexs: 索引（str或list）
        :return:
        """
        return self.test_case_df.loc[indexs, :]

    def set_column_data(self, columns, values):
        """
        设置整列数据。
        :param columns: 列名（str或list）
        :param values: 赋值（str或list）
        :return:
        """
        self.test_case_df.loc[:, columns] = values

    def get_column_data(self, columns):
        """
        获取整列数据。
        :param columns: 列名（str或list）
        :return:
        """
        return self.test_case_df.loc[:, columns]

    @classmethod
    def generate_df(cls, data=None, index=None, columns=None, dtype=None, copy=False):
        """
        通过工具生成DataFrame实例。
        :param data: 数据
        :param index: 索引
        :param columns: 列名
        :param dtype: 类型
        :param copy: 复制
        :return:
        """
        return pd.DataFrame(data=data, index=index, columns=columns, dtype=dtype, copy=copy)


if __name__ == '__main__':
    from Gastepo.Core.Base.BaseData import TESTCASE_PATH

    session = DataframeOperation(os.path.join(TESTCASE_PATH, "ApiTestCase_stg.xls"))
    # print(session.get_group_data(check_active=False, id=["TC_1", "TC_2"], group=["A", "B"], order=[1, 2, 3])[
    #           ["ID", "AID", "Active", "Group", "Order"]])
    # print(session.get_descriptor_data(scenario=['血糖管理'], platform=["患者H5"], level=['critical'], check_active=True)[
    #           ['ID', "Scenario", "Platform", "Level", "Active"]])
    print(session.get_entire_data(scenario=['血糖管理'], platform=["BMS端"], level=['critical'], group=['A'], order=[41],
                                  check_active=True)[
              ['ID', "Scenario", "Platform", "Level", "Group", "Order", "Active"]])
    # a = session.get_all_data()[["ID", "AID", "Active", "TestResult"]]
    # print(a[a["Active"] == False])
    # a["Active"] = a["Active"].map(lambda x: str(x).lower())
    # print(session.get_column_data(columns=["ID","BaseUrl", "UrlPath", "Method"]))
    # session.set_cell_data(["TC_1", "TC_3"], ["BaseUrl", "Active"], ["j", "a"])
    # print(session.get_cell_data(["TC_1", "TC_2"], ["BaseUrl", "Active"]))
    # print(session.get_row_data(indexs=["TC_433"]))
    # print(session.get_column_data(columns=["BaseUrl"]).to_dict("records"))
    # print(session.get_column_data(columns=["BaseUrl"]).to_json(orient="records"))
