# -*- coding: utf-8 -*-

import json
import re
import sys

from retrying import retry

from Gastepo.Core.Base.BaseData import ENVIRONMENT_CONFIG_FILE
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.EncryptUtils import encrypt
from Gastepo.Core.Util.LogUtils import logger
from Gastepo.Core.Util.RequestUtils import RequestTool


class ResponseDecrypt(object):
    """
    响应体解密类
    """

    def __init__(self, response_str, key='f2bb2e100c08449290e603a0da2ef0d0'):
        """
        初始化响应体加密字串及key秘钥
        :param response_str: 响应体加密字串
        :param key: 秘钥
        """
        self.response_str = response_str
        self.key = key

    def decrypt(self):
        """
        解密方法
        :return: 解密响应体字串
        """
        try:
            response_hex_str = encrypt.a2b_hex(self.response_str)
            response_base64_str = encrypt.BASE64(response_hex_str).decode('utf-8')
            response_debase64_str = encrypt.BASE64_Decrypt(response_base64_str.encode('utf-8'))
            decrypt_response_str = encrypt.AES_Decrypt1(encrypt_str=response_debase64_str, key=encrypt.add_16(self.key))
            return decrypt_response_str
        except Exception:
            logger.exception("[Exception]：解密接口响应体加密字串过程中发生异常，请检查！")
            sys.exit(1)


class BusinessOperationApiStarter(object):
    """
    XX业务接口自动化测试~启动类
    """

    def __init__(self, project="bus", env="stg"):
        """
        初始化环境信息。
        :param project: 所属项目名称
        :param env: 当前环境名称
        """
        env_params = YamlConfig(config=ENVIRONMENT_CONFIG_FILE).get(project).get(env)
        web_params = env_params.get("doctor_admin")
        self.login_url = web_params.get("login_url")
        self.username = web_params.get("username")
        self.password = web_params.get("password")
        self.validcode = web_params.get("validcode")
        self.env = env
        self.token = None

    @retry(stop_max_attempt_number=2, wait_random_min=2000, wait_random_max=5000)
    def login(self):
        """
        触发登录接口请求并XX业务请求令牌Token值
        :return:
        """
        logger.info('[Start]：开始请求登录XX业务{}环境后台服务...'.format(self.env))
        login_res = RequestTool().post(url=self.login_url,
                                       headers={"Content-Type": "application/json;charset=UTF-8"},
                                       data=json.dumps(
                                           {"username": "{}".format(self.username),
                                            "password": "{}".format(encrypt.MD5(self.password)),
                                            "verificationCode": "{}".format(self.validcode),
                                            "code": "hlwyy",
                                            "userType": 3, "token": ""}),
                                       verify=True)
        response_str = login_res.text.split("\"")[1]
        # response_str = login_res.text
        decrypt_login_res = ResponseDecrypt(response_str=response_str).decrypt()
        decrypt_login_res = re.sub(r"\n|\t|\r|\r\n|\n\r|\x08|\\", "", decrypt_login_res)
        login_res_dict = json.loads(decrypt_login_res)
        if login_res_dict.get("err") == 0 and login_res_dict.get("errmsg") == '操作成功':
            self.token = login_res_dict['data']['token']
            logger.info('[Success]：XX业务{}环境后台服务登录成功, 请求令牌Token值为: {}'.format(self.env, self.token))
            return self
        else:
            logger.warning(
                "[WARNING]：XX业务{}环境后台服务登录失败，接口响应为【{}】，重试登录中...".format(self.env, login_res_dict))
            sys.exit(1)

    @property
    def get_token(self):
        """
        获取请求令牌Token值
        :return:
        """
        if self.token is None:
            logger.warning("[WARNING]：检查到XX业务{}环境后台服务请求令牌Token值为空, 请先登录！".format(self.env))
            sys.exit(1)
        return self.token


if __name__ == '__main__':
    print(BusinessOperationApiStarter().login().get_token)
