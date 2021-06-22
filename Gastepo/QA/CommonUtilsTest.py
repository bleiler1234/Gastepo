# -*- coding: utf-8 -*-
import unittest

from hamcrest import *

from Gastepo.Core.Util.CommonUtils import is_number


class CommonUtilsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_is_number(self):
        assert_that(is_number(3), is_(equal_to(True)))

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
