# -*- coding: utf-8 -*-
import unittest

from hamcrest import *

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Util.ConfigUtils import YamlConfig


class ConfigUtilsTest(unittest.TestCase):

    def testConfig(self):
        host = YamlConfig(config=APPLICATION_CONFIG_FILE).get("mysql", 1).get("stg").get("host")
        assert_that(host, equal_to("10.9.18.134"))


if __name__ == '__main__':
    unittest.main()
