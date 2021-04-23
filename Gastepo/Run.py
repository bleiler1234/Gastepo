# -*- coding: utf-8 -*-

import os
from threading import Thread

import pytest

from Gastepo.Core.Base.BaseData import SERVER_PATH
from Gastepo.Core.Util.CommonUtils import pipe_command


def main():
    Thread(
        target=pipe_command,
        name="ServerThread",
        args=("python3 {}".format(os.path.join(SERVER_PATH, "MainServer.py")),),
        daemon=False
    ).start()
    pytest.main()


# 自动化测试启动器
if __name__ == '__main__':
    main()
