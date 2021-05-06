# -*- coding: utf-8 -*-

import os
import sys

import pandas as pd
import pymysql
import redis
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymysql.err import InternalError
from redis import ConnectionError
from redis.exceptions import ResponseError
from sqlalchemy import create_engine

from Gastepo.Core.Base.BaseData import APPLICATION_CONFIG_FILE
from Gastepo.Core.Base.CustomException import DatabaseTypeError, EnvironmentTypeError
from Gastepo.Core.Util.ConfigUtils import YamlConfig
from Gastepo.Core.Util.LogUtils import logger


class GeneralDatabaseTools(object):
    """
    通用数据库工具类，当前支持mysql/redis/mongodb
    """

    def __init__(self, dbtype, env, dbname=None):
        """
        指定数据库类型、所处环境及数据库名称
        :param dbtype: 数据库类型（当前支持mysql/redis/mongodb）
        :param env: 所处环境
        :param dbname: 数据库名称
        """
        try:
            if str(dbtype).lower() not in [r'mysql', r'redis', r'mongodb']:
                raise DatabaseTypeError
            if str(env).lower() not in [r'test', r'stg', r'dev', r'qa']:
                raise EnvironmentTypeError
            else:
                self.dbtype = str(dbtype).lower()
                self.env = str(env).lower()
                self.dbname = dbname
        except DatabaseTypeError:
            logger.warning('[WARNING]：检测到非法或不支持的数据库类型"{}"，当前仅支持[mysql, redis, mongodb]'.format(dbtype))
            sys.exit(1)
        except EnvironmentTypeError:
            logger.warning('[WARNING]：检测到非法或不支持的测试环境"{}"，当前仅支持[test, stg, dev, qa]'.format(env))
            sys.exit(1)

    def create_session(self):
        """
        创建数据库连接会话
        :return session:会话实例
        :return:
        """
        try:
            if self.dbtype == r'mysql':
                mysqlParam = YamlConfig(config=APPLICATION_CONFIG_FILE).get("mysql", 1).get(self.env)
                self.session = pymysql.connect(
                    host=mysqlParam['host'],
                    user=mysqlParam['username'],
                    password=str(mysqlParam['password']),
                    port=mysqlParam['port'],
                    database=str(self.dbname)
                )
                return self.session
            elif self.dbtype == r'redis':
                redisParam = YamlConfig(config=APPLICATION_CONFIG_FILE).get('redis', 1)[self.env]
                pool = redis.ConnectionPool(
                    host=redisParam['host'],
                    port=redisParam['port'],
                    db=self.dbname,
                    decode_responses=True,
                )
                self.session = redis.StrictRedis(connection_pool=pool, charset='utf-8')
                return self.session
            elif self.dbtype == r'mongodb':
                mongoParam = YamlConfig(config=APPLICATION_CONFIG_FILE).get('mongodb', 1)[self.env]
                self.session = MongoClient(host=mongoParam['host'],
                                           port=mongoParam['port'])
                return self.session
            else:
                raise DatabaseTypeError
        except InternalError:
            logger.exception('[Exception]：当前指定的MySQL数据库"{}"并不存在.'.format(self.dbname))
        except DatabaseTypeError:
            logger.exception('[Exception]：数据库类型{}不支持创建连接会话.'.format(self.dbtype.upper()))
        except ConnectionError:
            logger.exception('[Exception]：Redis会话连接错误, 请检查连接会话参数和当前网络状况.')
        except ResponseError:
            logger.exception('[Exception]：Redis数据库索引值"{}"非法, 请输入合法的数据库索引(int类型标识).'.format(self.dbname))
        except Exception:
            logger.exception('[Exception]：创建{}数据库会话实例过程中发生异常，请检查！'.format(self.dbtype.upper()))

    def close_session(self):
        """
        关闭连接会话
        :return:
        """
        try:
            self.session.close()
            logger.exception("[Done]：".format(self.dbtype.upper()))
        except Exception:
            logger.exception("[Exception]：关闭{}会话实例过程中发生异常，请检查！".format(self.dbtype.upper()))


class MysqlDatabaseTools(object):
    """
    MySQL数据库工具类
    """

    def __init__(self, env, dbname):
        """
        指定所处环境及数据库名称
        :param env: 所处环境
        :param dbname: 数据库名称
        """
        mysqlParam = YamlConfig(config=APPLICATION_CONFIG_FILE).get("mysql", 1).get(env)
        self.mysql_engine = create_engine(
            "mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8".format(mysqlParam['username'], str(mysqlParam['password']),
                                                                 mysqlParam['host'], mysqlParam['port'], dbname))

    @property
    def engine(self):
        """
        返回MySql会话
        :return:
        """
        return self.mysql_engine

    def update_string(self, update_sql):
        """
        更新语句操作
        :param update_sql: 更新SQL
        :return:
        """
        update_result = self.mysql_engine.execute(update_sql)
        return update_result.rowcount

    def delete_string(self, delete_sql):
        """
        删除语句操作
        :param delete_sql: 删除SQL
        :return:
        """
        delete_result = self.mysql_engine.execute(delete_sql)
        return delete_result.rowcount

    def query_string(self, script_str):
        """
        通过sqlalchemy并使用engine方式执行脚本(字符串)并返回结果
        :param script_str: 脚本字符串
        :return:
        """
        try:
            result = self.mysql_engine.execute(script_str).fetchall()
            return result
        except Exception:
            logger.exception("[Exception]：执行MySQL脚本过程中发生异常，请检查！~ 脚本为：【{}】".format(script_str))

    def query_file(self, script_file):
        """
        通过sqlalchemy并使用engine方式执行脚本(文本文件)并返回结果
        :param script_file: 脚本文件
        :return:
        """
        script_string = None
        try:
            if os.path.exists(script_file):
                with open(script_file, mode=r'r', encoding='utf-8') as script:
                    script_string = script.read()
                    result = self.mysql_engine.execute(script_string).fetchall()
                    return result
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.exception('[Exception]：MySQL脚本文件"{}"当前并不存在'.format(script_file))
        except Exception:
            logger.exception("[Exception]：执行MySQL脚本过程中发生异常，请检查！~ 脚本为：【{}】".format(script_string))

    def query_string_df(self, script_str, index_col=None, columns=None, chunksize=None):
        """
        通过sqlalchemy并使用read_sql方式执行脚本(字符串)并返回结果
        :param script_str: 脚本字符串
        :param index_col: 将指定列作为索引
        :param columns: 指定获取列(read_sql_table时候可用)
        :param chunksize: 缓存区大小
        :return:
        """
        try:
            result = pd.read_sql(script_str, con=self.mysql_engine, index_col=index_col, columns=columns,
                                 chunksize=chunksize)
            return result
        except Exception:
            logger.exception("[Exception]：执行MySQL脚本过程中发生异常，请检查！~ 脚本为：【{}】".format(script_str))

    def query_file_df(self, script_file, index_col=None, chunksize=None):
        """
        通过sqlalchemy并使用read_sql_query方式执行脚本文件并返回结果
        :param script_file: 脚本文件
        :param index_col: 将指定列作为索引
        :param chunksize: 缓存区大小
        :return:
        """
        script_string = None
        try:
            if os.path.exists(script_file):
                with open(script_file, mode=r'r', encoding='utf-8') as script:
                    script_string = script.read()
                    result = pd.read_sql_query(script_string, con=self.mysql_engine, index_col=index_col,
                                               chunksize=chunksize)
                    return result
            else:
                raise FileNotFoundError
        except FileNotFoundError:
            logger.exception('[Exception]：MySQL脚本文件"{}"当前并不存在'.format(script_file))
        except Exception:
            logger.exception("[Exception]：执行MySQL脚本过程中发生异常，请检查！~ 脚本为：【{}】".format(script_string))


class MongodbDatabaseTools(object):
    """
    MongoDB数据库工具类
    """

    def __init__(self, env, dbname, auth_dict=None):
        """
        指定所处环境及数据库名称
        :param env: 所处环境
        :param dbname: 数据库名称
        :param auth_dict: 授权字典，样例格式为{"auth_db":"admin", "auth_username":"root", "auth_password":"123456"}
        """
        mongodbParam = YamlConfig(config=APPLICATION_CONFIG_FILE).get("mongodb", 1).get(env)
        self.mongodb = MongoClient(host=mongodbParam['host'],
                                   port=mongodbParam['port'])
        if not mongodbParam.__contains__("auth") and auth_dict is None:
            logger.warning("请在应用配置文件中指定MongoDB授权信息，或者通过auth_dict字典进行指定！")
            sys.exit(1)
        if auth_dict is not None:
            if isinstance(auth_dict, dict):
                auth_db = auth_dict.get("auth_db")
                auth_username = auth_dict.get("auth_username")
                auth_password = str(auth_dict.get("auth_password"))
                auth = eval("self.mongodb.{}".format(auth_db))
                auth.authenticate(auth_username, auth_password)
                self.db_client = eval("self.mongodb.{}".format(dbname))
            else:
                logger.warning("auth_dict授权信息必须为字典形式，请检查！")
                sys.exit(1)
        if auth_dict is None and mongodbParam.__contains__("auth"):
            mongodbAuth = mongodbParam.get("auth")
            auth_db = mongodbAuth.get("db")
            auth_username = mongodbAuth.get("username")
            auth_password = str(mongodbAuth.get("password"))
            auth = eval("self.mongodb.{}".format(auth_db))
            auth.authenticate(auth_username, auth_password)
            self.db_client = eval("self.mongodb.{}".format(dbname))

    def db(self, dbname=None):
        """
        获取MongoDB数据库会话
        :param dbname: 数据库名称
        :return:
        """
        if dbname is None:
            return self.DbClient(db_client=self.db_client)
        else:
            db_client = eval("self.mongodb.{}".format(dbname))
            return self.DbClient(db_client=db_client)

    @property
    def mongo(self):
        """
        获取MongoDB实例
        :return:
        """
        return self.mongodb

    class DbClient:
        """
        MongoDB数据库操作
        """

        def __init__(self, db_client):
            """
            初始化MongoDB数据库实例
            :param db_client: MongoDB数据库实例
            """
            self.db_client = db_client

        @property
        def client(self):
            """
            获取MongoDB数据库实例
            :return:
            """
            return self.db_client

        def drop(self, tbname):
            """
            删除指定表
            :param tbname: MongoDB表名
            :return:
            """
            tb = eval("self.db_client.{}".format(tbname))
            drop = tb.drop()
            return drop

        def insert_one(self, tbname, insert_json):
            """
            单条数据插入
            :param tbname: MongoDB表名
            :param insert_json: 单条插入json, 最好指定_id否则可能重复插入
            :return: 插入数据id
            """
            tb = eval("self.db_client.{}".format(tbname))
            insert = tb.insert_one(insert_json)
            return insert.inserted_id

        def insert_many(self, tbname, insert_json_list):
            """
            批量数据插入
            :param tbname: MongoDB表名
            :param insert_json_list: 批量插入json列表，最好指定_id否则可能重复插入
            :return: 插入数据id列表
            """
            tb = eval("self.db_client.{}".format(tbname))
            insert = tb.insert_many(insert_json_list)
            return insert.inserted_ids

        def delete_one(self, tbname, delete_json):
            """
            删除匹配到的第一条数据
            :param tbname: MongoDB表名
            :param delete_json: 删除数据json
            :return: 删除数据id
            """
            tb = eval("self.db_client.{}".format(tbname))
            delete = tb.delete_one(delete_json)
            return delete.deleted_count

        def delete_many(self, tbname, delete_json):
            """
            删除多条数据
            :param tbname: MongoDB表名
            :param delete_json: 删除数据json，若为{}则删除集合全部数据
            :return: 删除数据id
            """
            tb = eval("self.db_client.{}".format(tbname))
            delete = tb.delete_many(delete_json)
            return delete.deleted_count

        def update_one(self, tbname, filter_json, update_json, upsert=False):
            """
            更新匹配到的第一条数据
            :param tbname: MongoDB表名
            :param filter_json: 过滤json
            :param update_json: 更新json
            :param upsert: 更新插入开关
            :return:
            """
            tb = eval("self.db_client.{}".format(tbname))
            update = tb.update_one(filter=filter_json, update=update_json, upsert=upsert)
            return update.modified_count

        def update_many(self, tbname, filter_json, update_json, upsert=False):
            """
            更新多条数据
            :param tbname: MongoDB表名
            :param filter_json: 过滤json
            :param update_json: 更新json
            :param upsert: 更新插入开关
            :return:
            """
            tb = eval("self.db_client.{}".format(tbname))
            update = tb.update_many(filter=filter_json, update=update_json, upsert=upsert)
            return update.modified_count

        def find_one(self, tbname, filter_json=None, projection_json=None, sort_json={}, skip=0, limit=0):
            """
            查询匹配到的第一条数据
            :param tbname: MongoDB表名
            :param filter_json: 过滤json
            :param projection_json: 显示json
            :param sort_json: 排序json
            :param skip: 跳过行数
            :param limit: 限制行数
            :return:
            """
            tb = eval("self.db_client.{}".format(tbname))
            return tb.find_one(filter=filter_json, projection=projection_json, sort=list(sort_json.items()), skip=skip,
                               limit=limit)

        def find(self, tbname, filter_json=None, projection_json=None, sort_json={}, skip=0, limit=0):
            """
            查询多条数据
            :param tbname: MongoDB表名
            :param filter_json: 过滤json
            :param projection_json: 显示json
            :param sort_json: 排序json
            :param skip: 跳过行数
            :param limit: 限制行数
            :return:
            """
            result = []
            tb = eval("self.db_client.{}".format(tbname))
            items = tb.find(filter=filter_json, projection=projection_json, sort=list(sort_json.items()), skip=skip,
                            limit=limit)
            for item in items:
                result.append(item)
            return result


if __name__ == '__main__':
    # print(MysqlDatabaseTools("test", "test").query_file_df("select name from userinfo where id in (1,2)"))
    session = MongodbDatabaseTools(env='qa', dbname='test_mongo',
                                   auth_dict={"auth_db": "admin", "auth_username": "root",
                                              "auth_password": "123456"})
    db = session.db(dbname="test_mongo")
    # print(db.insert_one(tbname='test_mongo', insert_json={"_id":1, "name": "a1", "club": "c1"}))
    # print(db.insert_many(tbname='test_mongo', insert_json_list=[{"_id": 2, "name": "a2", "club": "c2"},
    #                                                             {"_id": 3, "name": "a3", "club": "c3"}]))
    # print(
    #     db.update_one(tbname="test_mongo", filter_json={"name": {"$regex": "^a"}},
    #                    update_json={"$set": {"club": "cu"}}))
    # print(
    #     db.update_many(tbname="test_mongo", filter_json={"name": {"$regex": "^a"}},
    #                    update_json={"$set": {"club": "cu"}}))
    # print(db.update_one(tbname="test_mongo", filter_json={"_id": "id1"},
    #                     update_json={"$set": {"name": "Mayer", "club": "Merida"}}, upsert=True))
    # print(db.delete_one(tbname="test_mongo", delete_json={"name": {"$regex":"^a"}}))
    # print(db.delete_many(tbname="test_mongo", delete_json={"name": {"$regex": "^a"}}))
    # print(db.find_one(tbname="test_mongo", filter_json={"_id": ObjectId("5ff2c39364efd65eed78597e")}))
    # print(db.find(tbname="test_mongo", filter_json={"name": {"$regex": "s"}}, projection_json={"_id": 1, "name": 1},
    #               sort_json={"_id": -1}))
