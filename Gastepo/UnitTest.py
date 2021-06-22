# -*- coding: utf-8 -*-
import sys

sys.path.append("/Users/mayer/Project/PycharmProjects/MileStone/Automation/Gastepo")

import unittest
from Gastepo.QA.CommonUtilsTest import CommonUtilsTest
from Gastepo.QA.ConfigUtilsTest import ConfigUtilsTest

if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestSuite()
    suite.addTest(CommonUtilsTest)
    suite.addTest(ConfigUtilsTest)
    runner = unittest.TextTestRunner()
    runner.run(suite)
