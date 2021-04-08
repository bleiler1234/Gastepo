# -*- coding: utf-8 -*-

from datetime import timedelta

from flask import Flask, redirect

from Gastepo.Core.Base.BaseData import REPORT_PATH

"""
描述：自动化测试主要功能Web服务，如在线阅览测试报告等。
"""
server = Flask(__name__,
               template_folder=REPORT_PATH,
               static_folder=REPORT_PATH,
               static_url_path='/')
server.config['JSON_AS_ASCII'] = False
server.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(seconds=1)


@server.route('/allure')
def allure():
    return redirect(location='index.html')


# 启动服务
if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
