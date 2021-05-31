# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse

import requests
from retrying import retry

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE, RESOURCE_PATH
from Gastepo.Core.Util.CommonUtils import get_ip, capture_image, face_bed
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class DingTools(object):
    """
    钉钉机器人消息提醒工具类
    """

    def __init__(self):
        """
        从应用配置文件获取钉钉请求token及签名secret
        """
        self.token = YamlConfig(config=APPLICATION_CONFIG_FILE).get("ding")["token"]
        self.secret = YamlConfig(config=APPLICATION_CONFIG_FILE).get("ding")["secret"]
        self.timestamp = str(round(time.time() * 1000))

    @property
    def get_sign(self):
        """
        生成钉钉机器人签名字串
        :return:
        """
        try:
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(self.timestamp, self.secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            return sign
        except Exception:
            logger.exception("[Exception]：生成钉钉机器人签名字串过程中发生异常，请检查！")

    @retry(stop_max_attempt_number=2, wait_random_min=2000, wait_random_max=5000)
    def send(self, message):
        """
        发送钉钉机器人消息提醒
        :param message: 消息提醒
        :return:
        """
        try:
            if not isinstance(message, dict):
                logger.warning("[WARNING]：参数message必须以字典形式入参，请检查！")
                sys.exit(1)
            if not message.__contains__('msgtype'):
                logger.warning("[WARNING]：消息体message必须包含消息类型msgtype，请检查！")
                sys.exit(1)
            if message.get('msgtype') not in ['text', 'link', 'markdown', 'actionCard', 'feedCard']:
                logger.warning('[WARNING]：检测到非法消息类型"{}"，当前仅支持text、link、markdown、actionCard、feedCard，请重新指定！'.format(
                    message.get('msgtype')))
                sys.exit(1)
            url = "https://oapi.dingtalk.com/robot/send?access_token={}&timestamp={}&sign={}".format(self.token,
                                                                                                     self.timestamp,
                                                                                                     self.get_sign)
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=json.dumps(message))
            result = response.json()
            if result.get("errcode") == 0 and result.get("errmsg") == 'ok':
                logger.info("[Done]：钉钉机器人消息提醒成功.")
            else:
                logger.warning("[WARNING]：钉钉机器人消息提醒失败，接口响应为【{}】，开始重试...".format(result))
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：发送钉钉机器人消息提醒过程中发生异常，请检查！")
            sys.exit(1)


class EnvironmentDingTools(DingTools):
    """
    钉钉机器人消息提醒工具类(依赖环境配置文件)
    """

    def __init__(self, ding_notify_file, preview_mode=False):
        """
        从应用配置文件获取钉钉请求token及签名secret
        :param ding_notify_file: 钉钉消息模板文件
        :param preview_mode: 测试报告截图预览
        """
        try:
            DingTools.__init__(self)
            if not os.path.exists(ding_notify_file):
                raise FileNotFoundError
            with open(file=ding_notify_file, mode=r'r', encoding='utf-8') as ding_file:
                if preview_mode is False:
                    self.ding = json.loads(ding_file.read().replace("ip_address", get_ip())
                                           .replace("![Allure](report_url)", ">      🐾🐾🐾 ~ {}".format(get_ip())))
                else:
                    self.ding = json.loads(ding_file.read()
                                           .replace("ip_address", get_ip())
                                           .replace("report_url", face_bed(pic=capture_image(width=1440,
                                                                                             height=797,
                                                                                             url="http://localhost:5000/allure",
                                                                                             sleep=10,
                                                                                             pic=os.path.join(
                                                                                                 RESOURCE_PATH,
                                                                                                 "Allure",
                                                                                                 "Allure.png")
                                                                                             ),
                                                                           alias="Allure.png")
                                                    )
                                           )
            self.token = YamlConfig(config=APPLICATION_CONFIG_FILE).get("ding")["token"]
            self.secret = YamlConfig(config=APPLICATION_CONFIG_FILE).get("ding")["secret"]
            self.timestamp = str(round(time.time() * 1000))
        except FileNotFoundError:
            logger.warning('[WARNING]：钉钉消息通知模板文件"{}"当前并不存在，请检查！'.format(ding_notify_file))
            sys.exit(1)

    @property
    def get_sign(self):
        """
        生成钉钉机器人签名字串
        :return:
        """
        try:
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(self.timestamp, self.secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            return sign
        except Exception:
            logger.exception("[Exception]：生成钉钉机器人签名字串过程中发生异常，请检查！")

    def generate_msg(self, msgtype):
        """
        构造钉钉机器人消息体
        :param msgtype: 消息提醒类型（当前仅支持Text/Link/MarkDown/ActionCard/FeedCard）
        :return:
        """
        try:
            if msgtype == 'text':
                return json.dumps(self.ding.get('text'))
            if msgtype == 'link':
                return json.dumps(self.ding.get('link'))
            if msgtype == 'markdown':
                return json.dumps(self.ding.get('markdown'))
            if msgtype == 'actionCard':
                return json.dumps(self.ding.get('actionCard'))
            if msgtype == 'feedCard':
                return json.dumps(self.ding.get('feedCard'))
        except Exception:
            logger.warning("[WARNING]：构造钉钉机器人消息体过程中发生异常，请检查！")

    @retry(stop_max_attempt_number=2, wait_random_min=2000, wait_random_max=5000)
    def send(self, msgtype):
        """
        发送钉钉机器人消息提醒
        :param msgtype: 消息提醒类型
        :return:
        """
        try:
            if msgtype not in ['text', 'link', 'markdown', 'actionCard', 'feedCard']:
                logger.warning(
                    '[WARNING]：检测到非法消息类型"{}"，当前仅支持text、link、markdown、actionCard、feedCard，请重新指定！'.format(msgtype))
                sys.exit(1)
            url = "https://oapi.dingtalk.com/robot/send?access_token={}&timestamp={}&sign={}".format(self.token,
                                                                                                     self.timestamp,
                                                                                                     self.get_sign)
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=self.generate_msg(msgtype))
            result = response.json()
            if result.get("errcode") == 0 and result.get("errmsg") == 'ok':
                logger.info("[Done]：钉钉机器人消息提醒成功.")
            else:
                logger.warning("[WARNING]：钉钉机器人消息提醒失败，接口响应为【{}】，开始重试...".format(result))
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：发送钉钉机器人消息提醒过程中发生异常，请检查！")
            sys.exit(1)


class CustomDingTools(object):
    """
    钉钉机器人消息提醒工具类(自定义钉钉验签及群组别名)
    """

    def __init__(self, token, secret, alias):
        """
        :param token 钉钉令牌
        :param secret 钉钉秘钥
        :param alias 推送群组别名
        """
        self.token = token
        self.secret = secret
        self.alias = alias
        self.timestamp = str(round(time.time() * 1000))

    @property
    def get_sign(self):
        """
        生成钉钉机器人签名字串
        :return:
        """
        try:
            secret_enc = self.secret.encode('utf-8')
            string_to_sign = '{}\n{}'.format(self.timestamp, self.secret)
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            return sign
        except Exception:
            logger.exception("[Exception]：『{}』生成钉钉机器人签名字串过程中发生异常，请检查！".format(self.alias))

    @retry(stop_max_attempt_number=2, wait_random_min=2000, wait_random_max=5000)
    def send(self, message):
        """
        发送钉钉机器人消息提醒
        :param message: 消息提醒
        :return:
        """
        try:
            if not isinstance(message, dict):
                logger.warning("[WARNING]：参数message必须以字典形式入参，请检查！")
                sys.exit(1)
            if not message.__contains__('msgtype'):
                logger.warning("[WARNING]：消息体message必须包含消息类型msgtype，请检查！")
                sys.exit(1)
            if message.get('msgtype') not in ['text', 'link', 'markdown', 'actionCard', 'feedCard']:
                logger.warning('[WARNING]：检测到非法消息类型"{}"，当前仅支持text、link、markdown、actionCard、feedCard，请重新指定！'.format(
                    message.get('msgtype')))
                sys.exit(1)
            url = "https://oapi.dingtalk.com/robot/send?access_token={}&timestamp={}&sign={}".format(self.token,
                                                                                                     self.timestamp,
                                                                                                     self.get_sign)
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=json.dumps(message))
            result = response.json()
            if result.get("errcode") == 0 and result.get("errmsg") == 'ok':
                logger.info("[Done]：『{}』钉钉机器人消息提醒成功.".format(self.alias))
            else:
                logger.warning("[WARNING]：『{}』钉钉机器人消息提醒失败，接口响应为【{}】，开始重试...".format(self.alias, result))
                sys.exit(1)
        except Exception:
            logger.exception("[Exception]：『{}』发送钉钉机器人消息提醒过程中发生异常，请检查！".format(self.alias))
            sys.exit(1)


if __name__ == '__main__':
    from Gastepo.Core.Base.BaseData import RESOURCE_PATH

    ding = EnvironmentDingTools(ding_notify_file=os.path.join(RESOURCE_PATH, "Ding", "DingNotifyTemplate.json"))
    ding.send("markdown")
