# -*- coding: utf-8 -*-
import sys

sys.path.append("/Users/mayer/Project/PycharmProjects/MileStone/Automation/Gastepo")

import unittest

from hamcrest import *

from Gastepo.Core.Util.CommonUtils import is_number


class CommonUtilsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("set up class")

    def setUp(self):
        print("set up")

    def test_is_number(self):
        assert_that(is_number(3), is_(equal_to(True)))
        print("test done")

    def tearDown(self):
        print("tear down")

    @classmethod
    def tearDownClass(cls):
        print("tear down class")


if __name__ == '__main__':
    unittest.main()
