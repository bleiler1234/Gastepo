# -*- coding: utf-8 -*-
# Author: yuzhonghua

import os
import re
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPException
from socket import gaierror, error

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Base.BaseData import RESOURCE_PATH
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class Email(object):
    '''
    邮件发送模块
    '''

    emailParam = YamlConfig(config=APPLICATION_CONFIG_FILE).get('email')

    def __init__(self,
                 server=emailParam['server'],
                 port=emailParam['port'],
                 user=emailParam['user'],
                 password=emailParam['password'],
                 title=emailParam['title'],
                 sender=emailParam['sender'],
                 receiver=emailParam['receiver'],
                 ):
        '''
        初始化Email参数
        :param server:  邮件服务器ip或域名
        :param port: 邮件服务器端口号
        :param user: 登录账户
        :param password: 登录密码
        :param title: 邮件标题
        :param sender: 发送邮箱
        :param receiver: 接收邮箱
        '''
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.title = title
        self.sender = 'Automation' + '<' + sender + '>'
        self.receiver = receiver
        self.message = None
        self.files = None
        self.msg = MIMEMultipart('related')
        self.msg['From'] = Header(self.sender, 'utf-8')
        self.msg['To'] = Header(self.receiver, 'utf-8')
        self.msg['Subject'] = Header(self.title, 'utf-8')

    def createSession(self):
        '''
        建立SMTP邮件服务连接
        '''
        try:
            self.smtpObj = smtplib.SMTP()
            self.smtpObj.connect(self.server,
                                 self.port)
            # 若开启SSL，则关闭TLS
            # self.smtpObj.starttls()
            self.smtpObj.login(self.user,
                               self.password)
            return self.smtpObj
        except SMTPConnectError:
            logger.exception('邮件SMTPConnectError连接错误, 请检查网络以及邮件配置.')
        except SMTPAuthenticationError:
            logger.exception('邮件SMTPAuthenticationError认证错误, 请检查邮件登录账套.')
        except SMTPException:
            logger.exception('触发SMTPException异常, 当前无适配邮件认证方式, 请确认当前开启的验证方式(SSL或TSL).')

    def checkAtType(self, attype):
        '''
        校验附件类型并自动添加
        :param attype:附件类型
        :return:
        '''
        if isinstance(attype, list):
            for af in attype:
                self.attachFile(af)
        if isinstance(attype, str):
            self.attachFile(attype)

    def attachFile(self, file):
        '''
        构造附件扩展，仅MIMEBase支持中文附件
        :param file: 附件文件
        '''
        # with open(file, 'rb') as f:
        #     att = MIMEText(f.read(), 'plait', 'utf-8')
        # att["Content-Type"] = 'application/octet-stream'
        # filename = re.split(r'[\\|/]', file)[-1]
        # att["Content-Disposition"] = 'attachment; filename={}'.format(filename)
        # self.msg.attach(att)
        # logger.info('邮件已添加附件 {}'.format(filename))
        att = MIMEBase('application', 'octet-stream')
        with open(file, 'rb') as f:
            att.set_payload(f.read())
        filename = re.split(r'[\\|/]', file)[-1]
        att.add_header('Content-Disposition', 'attachment', filename=('gbk', '', filename))
        encoders.encode_base64(att)
        self.msg.attach(att)
        logger.info('邮件已添加附件 {}'.format(filename))

    def attachImage(self, path=os.path.join(RESOURCE_PATH, "Allure")):
        '''
        构造附图扩展
        :param path: 图片路径
        '''
        with open(os.path.join(path, 'Allure.png'), 'rb') as f:
            attimg = MIMEImage(f.read())
        attimg.add_header('Content-ID', '<image1>')
        return attimg

    def attachHtml(self, href="http://10.16.168.70:5000/allure", desc="API功能自动化测试报告"):
        """
        构造文本扩展
        :param href: 链接地址
        :param desc: 链接描述
        :return:
        """
        if self.image_flag:
            img_str = '<p><img src="cid:image1"></p>'
            message = \
                '''
                <h4>Dear All:</h4><br/><p>{}</p>
                <p>【<font size="3" color="gray"><b>测试报告</b></font>】：点击<a href="{}">{}</a>进行查看.</p><br/>
                {}
                '''.format(self.message, href, desc, img_str)
        else:
            message = \
                '''
                <h4>Dear All:</h4><br/><p>{}</p>
                <p>【<font size="3" color="gray"><b>测试报告</b></font>】：点击<a href="{}">{}</a>进行查看.</p><br/>
                '''.format(self.message, href, desc)

        msgalter = MIMEMultipart('alternative')
        msgalter.attach(MIMEText(message, _subtype='html', _charset='utf-8'))
        return msgalter

    def build_all_msg(self):
        '''
        添加所有邮件数据
        '''
        self.msg.attach(self.attachHtml())
        self.msg.attach(self.attachImage())
        return self.msg

    def build_html_msg(self):
        """
        添加文本邮件信息
        :return:
        """
        self.msg.attach(self.attachHtml())
        return self.msg

    def build_image_msg(self):
        """
        添加图片邮件信息
        :return:
        """
        self.msg.attach(self.attachImage())
        return self.msg

    def send(self, message='FYI', image_flag=False, *filepath):
        '''
        触发邮件发送
        :param message: 邮件文本信息
        :param image_flag: 是否发送图片
        :param filepath: 邮件附件元组
        :return:
        '''
        self.message = message
        self.image_flag = image_flag
        for p in filepath:
            if os.path.isdir(p):
                self.files = list()
                for f in os.listdir(p):
                    self.files.append(os.path.join(p, f))
                self.checkAtType(self.files)
            elif os.path.isfile(p):
                self.files = p
                self.checkAtType(self.files)
            else:
                self.files = p
                filename = re.split(r'[\\|/]', str(p))[-1]
                logger.warning('注意! 邮件附件"{0}"的路径"{1}"可能无效, 附件无法上传.'.
                               format(filename, p))
        try:
            logger.info("开始发送测试结果邮件......")
            session = self.createSession()
            session.sendmail(self.sender,
                             self.receiver.split(';'),
                             self.build_all_msg().as_string() if self.image_flag else self.build_html_msg().as_string()
                             )
        except (gaierror and error):
            logger.exception('邮件发送失败! ~ 无法连接到SMTP服务器, 请检查网络以及邮件配置.')
        else:
            logger.info('[Done]：{0}邮件发送成功! 收件人：{1}.'.format(self.title, self.receiver))
            session.quit()
            session.close()


if __name__ == '__main__':
    email = Email()
    email.send("这是一封Demo邮件，请查阅！", image_flag=False)
