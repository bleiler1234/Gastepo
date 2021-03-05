# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
from binascii import b2a_hex, a2b_hex

import rsa
from Crypto.Cipher import AES, DES


class Encrypt(object):
    '''
    加密/解密工具类
    '''

    def __init__(self):
        '''
        初始化时默认生成RSA加密公钥和解密私钥（均为private类型）
        '''
        self.__pubkey, self.__prikey = rsa.newkeys(256)

    def a2b_hex(self, string):
        """
        16进制转字符串
        :param string: 字符串
        :return:
        """
        return a2b_hex(string)

    def b2a_hex(self, string):
        """
        字符串转16进制
        :param string: 字符串
        :return:
        """
        return b2a_hex(string)

    def add_16(self, par):
        """
        16位补数
        :param par: 初始字符串
        :return:
        """
        par = par.encode('utf-8')
        while len(par) % 16 != 0:
            par += b'\x00'
        return par

    def MD5(self, string, key=None):
        '''
        MD5校验
        :param string:初始字符串
        :param key:校验码
        :return:
        '''
        temp = hashlib.md5()
        if key is None:
            temp.update(string.encode())
        else:
            temp.update((string + key).encode())
        result = temp.hexdigest()
        return result

    def SHA1(self, string, key=None):
        '''
        SHA1校验
        :param string: 初始字符串
        :param key: 校验码
        :return:
        '''
        temp = hashlib.sha1()
        if key is None:
            temp.update(string.encode())
        else:
            temp.update((string + key).encode())
        result = temp.hexdigest()
        return result

    def SHA256(self, string, key=None):
        '''
        SHA256校验
        :param string: 初始字符串
        :param key: 校验码
        :return:
        '''
        temp = hashlib.sha256()
        if key is None:
            temp.update(string.encode())
        else:
            temp.update((string + key).encode())
        result = temp.hexdigest()
        return result

    def HMAC(self, string, key, msg):
        '''
        HMAC加密
        :param string: 初始字符串（必须encode，通过指定b或encode()转换）
        :param key: 加密key（必须为bytes，通过指定b或encode()转换）
        :param msg: 加密消息（必须encode，通过指定b或encode()转换）
        :return:
        '''
        temp = hmac.new(key=key.encode(), msg=msg.encode())
        temp.update(string.encode())
        result = temp.hexdigest()
        return result

    def BASE64(self, string):
        '''
        BASE64加密
        :param string:初始字符串
        :return:
        '''
        result = base64.encodebytes(string)
        return result

    def BASE64_Decrypt(self, encrypt_str):
        '''
        BASE64解密
        :param encrypt_str: base64加密字符串
        :return:
        '''
        result = base64.decodebytes(encrypt_str)
        return result

    def AES(self, string, key):
        '''
        AES对称加密
        :param string: 初始字符串
        :param key: 加密秘钥（16位,必须为bytes），如 b'luckincoffeetest'（或'luckincoffeetest'.encode()）
        :return:
        '''
        cryptor = AES.new(key, AES.MODE_ECB, key)
        length = 16
        count = len(string)
        add = length - (count % length)
        string = string + ('\0' * add)
        ciphertext = cryptor.encrypt(string)
        result = b2a_hex(ciphertext)
        return result

    def AES_Decrypt(self, encrypt_str, key):
        '''
        AES对称解密
        :param encrypt_str: AES加密字符串
        :param key: 解密秘钥，与加密秘钥相同
        :return:
        '''
        cryptor = AES.new(key, AES.MODE_ECB, key)
        plain_text = cryptor.decrypt(a2b_hex(encrypt_str))
        result = plain_text.rstrip(b'\0').decode()
        return result

    def AES_Decrypt1(self, encrypt_str, key):
        '''
        AES对称解密
        :param encrypt_str: AES加密字符串
        :param key: 解密秘钥，与加密秘钥相同
        :return:
        '''
        cryptor = AES.new(key, AES.MODE_ECB)
        plain_text = cryptor.decrypt(encrypt_str)
        result = plain_text.decode('utf-8').strip('\0').strip('\u0005')
        return result

    def DES(self, string, key):
        '''
        DES对称加密
        :param string: 初始字符串
        :param key: 加密秘钥（8位,必须为bytes），如 b'lkcoffee'（或'lkcoffee'.encode()）
        :return:
        '''
        cryptor = DES.new(key, DES.MODE_ECB)
        length = 8
        count = len(string)
        add = length - (count % length)
        string = string + ('\0' * add)
        ciphertext = cryptor.encrypt(string)
        result = b2a_hex(ciphertext)
        return result

    def DES_Decrypt(self, encrypt_str, key):
        '''
        DES对称解密
        :param encrypt_str: DES加密字符串
        :param key: 解密秘钥，与加密秘钥相同
        :return:
        '''
        cryptor = DES.new(key, DES.MODE_ECB)
        plain_text = cryptor.decrypt(a2b_hex(encrypt_str))
        result = plain_text.rstrip(b'\0').decode()
        return result

    def RSA(self, string):
        '''
        RSA非对称加密（公钥加密）
        :param string: 初始字符串
        :return:
        '''
        ciphertext = rsa.encrypt(string.encode(), self.__pubkey)
        result = b2a_hex(ciphertext)
        return result

    def RSA_Decrypt(self, encrypt_str):
        '''
        RSA非对称解密（私钥解密）
        :param encrypt_str: RSA加密字符串
        :return:
        '''
        plain_text = rsa.decrypt(a2b_hex(encrypt_str), self.__prikey)
        result = plain_text.decode()
        return result

    def get_rsa_pubkey(self):
        '''
        获取RSA加密公钥.
        :return:
        '''
        return self.__pubkey

    def get_rda_prikey(self):
        '''
        获取RSA解密私钥.
        :return:
        '''
        return self.__prikey


encrypt = Encrypt()
