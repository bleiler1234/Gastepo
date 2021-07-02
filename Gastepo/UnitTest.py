# -*- coding: utf-8 -*-
import sys

sys.path.append("/Users/mayer/Project/PycharmProjects/MileStone/Automation/Gastepo")

import unittest
from Gastepo.Core.Base.BaseData import QA_PATH

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(start_dir=QA_PATH, pattern="*Test.py")
    runner = unittest.TextTestRunner()
    runner.run(suite)
