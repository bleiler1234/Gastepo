# -*- coding: utf-8 -*-
import sys

sys.path.append("/automation/Gastepo")
import datetime
import random
from typing import Any, List

import pandas as pd
import uvicorn
from bson.objectid import ObjectId
from fastapi import FastAPI, Request, Query, Path
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from Gastepo.Core.Util.DatabaseUtils import MongodbDatabaseTools

"""
描述：自动化测试用例插槽Web服务，如用于对接自定义UI页面编写自动化用例等。
"""
mongo = MongodbDatabaseTools(env='qa', dbname='gastepo',
                             auth_dict={"auth_db": "admin", "auth_username": "root",
                                        "auth_password": "123456"}).db()
# mongo = MongodbDatabaseTools(env='docker', dbname='gastepo').db()

server = FastAPI(title="Slot Server", description="主要提供自动化框架用例插槽接口，如用于对接自定义UI页面编写自动化用例等。",
                 docs_url='/qa/slot/api-docs', redoc_url='/qa/slot/re-docs',
                 openapi_url="/qa/slot/open-api.json")

server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 测试用例数据模型
class TestCaseModel(BaseModel):
    Pid: int
    Project: str
    Sid: int
    Scenario: str
    Tid: int
    Title: str
    BaseUrl: str
    UrlPath: str
    Method: str
    Consumes: str
    Platform: str
    Level: str
    Active: bool
    RequestPath: str
    RequestHeader: str
    RequestParam: str
    RequestData: str
    RequestFile: str
    DependencyInfo: str
    AssertInfo: str


# 测试用例层级模型
class CaseLayerModel(BaseModel):
    pid: int
    pname: str
    sid: int
    sname: str
    tid: int
    case: str


# 响应体模型
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any


class Mock(object):
    @classmethod
    def data(cls):
        def random_int(min=0, max=9, seed=False, string=False):
            if seed is True:
                random.seed()
                value = random.randint(min, max)
                return value if string is False else str(value)
            else:
                value = random.randint(min, max)
                return value if string is False else str(value)

        origin_df = pd.read_excel(
            "/automation/KxhAutoTest/Common/Data/Kxh/ApiTestCase_stg.xls").fillna(
            "")
        origin_df = origin_df[
            ['Project', 'Scenario', 'Title', 'BaseUrl', 'UrlPath', 'Method', 'Consumes', 'Platform', 'Level', 'Active',
             'RequestPath', 'RequestHeader', 'RequestParam', 'RequestData', 'RequestFile', 'DependencyInfo',
             'AssertInfo']]
        total_row = origin_df.shape[0]
        mock_df = pd.DataFrame(origin_df.iloc[random_int(0, total_row - 1), :]).T
        mock_df['Active'] = mock_df["Active"].astype(bool)
        mock_df['Sequence'] = 0
        mock_data = mock_df.to_dict(orient='records')
        return mock_data


# Exception全局异常捕获
@server.exception_handler(Exception)
async def http_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500,
                        content={"code": 999, "msg": "{}".format(exc.__class__.__name__), "info": str(exc)})  # 自定义响应体


# HTTPException请求异常捕获
@server.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=400,
                        content={"code": 998, "msg": "{}".format(exc.__class__.__name__),
                                 "info": str(exc.detail)})  # 自定义响应体


# RequestValidationError默认校验异常捕获
@server.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422,
                        content={"code": 997, "msg": "{}".format(exc.__class__.__name__), "info": str(exc)})  # 自定义响应体


@server.get("/qa/automation/slot/mock", response_model=ResponseModel, response_model_exclude_unset=True,
            tags=["测试数据"],
            summary="Mock测试用例数据", description="根据当前随机种子，随机生成基于康享荟项目的测试用例Mock数据。")
async def mock():
    return jsonable_encoder(dict(code=200, msg="success", data=Mock.data()))


@server.get("/qa/automation/slot/fetchTreeModel", response_model=ResponseModel, response_model_exclude_unset=True,
            tags=["页面数据"],
            summary="测试用例层级目录树渲染数据", description="基于Element页面的测试用例层级目录树渲染数据。")
async def fetchTreeModel(epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定非空的当前自动化史诗唯一标识epic！"))
    else:
        result = mongo.find(tbname="testcase", filter_json={"Epic": str(epic).strip()},
                            projection_json={"_id": 1, "Pid": 1, "Project": 1, "Sid": 1, "Scenario": 1, "Tid": 1,
                                             "Title": 1},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        origin = []
        df = pd.DataFrame(data=result).drop_duplicates(keep="last").fillna("")
        if df.shape[0] == 0:
            return jsonable_encoder(dict(code=201, msg=f"当前史诗{epic}无任何数据，请先进行初始化！"))
        df["_id"] = df["_id"].astype(str)
        df["Pid"] = df["Pid"].astype(object)
        df["Sid"] = df["Sid"].astype(object)
        df["Tid"] = df["Tid"].astype(object)
        projects_df = df[['Pid', 'Project']].drop_duplicates().reset_index(drop=True).set_index(keys=["Pid"], drop=True)
        projects_index = projects_df.index.values.tolist()
        projects_values = projects_df['Project'].values.tolist()
        projects_dict = dict(zip(projects_index, projects_values))
        for index, project in projects_dict.items():
            origin.append(dict(id=index, label=project, showInput=False, layer=1, children=[]))
        tree_data_list = []
        for origin_dict in origin:
            if origin_dict.get('id') < 0:
                return jsonable_encoder(
                    dict(code=201, msg="检测到非法的一级节点序号（其必须为自然数）",
                         data=dict(pid=origin_dict.get('id'), pname=origin_dict.get('label'))))
            pid_df = df[df["Pid"] == origin_dict.get('id')]
            pid_count = pid_df.shape[0]
            if pid_count == 1:
                tree_data_list.append(dict(layer1_id=int(origin_dict.get('id')),
                                           layer1_label=origin_dict.get('label'),
                                           layer2_id=-1,
                                           layer2_label="",
                                           layer3_data=[]))
            else:
                filter_pid_df = pid_df[pid_df['Sid'] != -1]
                for key1, value1 in filter_pid_df.groupby(by=["Pid", "Project", "Sid", "Scenario"], sort=True):
                    sid_count = value1.shape[0]
                    if sid_count == 1:
                        tree_data_list.append(dict(layer1_id=int(origin_dict.get('id')),
                                                   layer1_label=origin_dict.get('label'),
                                                   layer2_id=int(key1[2]),
                                                   layer2_label=key1[3],
                                                   layer3_data=[]))
                    else:
                        filter_sid_df = value1[value1["Tid"] != -1]
                        tid_df = filter_sid_df.loc[:, ['_id', 'Tid', "Title"]]
                        tid_df['showInput'] = False
                        tid_df['layer'] = 3
                        tid_df = tid_df.reindex(columns=["Tid", "Title", "showInput", "layer", "_id"]).sort_values(
                            by=["Tid"], ascending=True).reset_index(drop=True)
                        tid_data = tid_df.rename(columns={"Tid": "id", "Title": "label", "_id": "case"}).to_dict(
                            orient='records')
                        tree_data_list.append(dict(layer1_id=int(origin_dict.get('id')),
                                                   layer1_label=origin_dict.get('label'),
                                                   layer2_id=int(key1[2]),
                                                   layer2_label=key1[3],
                                                   layer3_data=tid_data))
        for origin_index, origin_dict in enumerate(origin):
            layer2_list = []
            for tree_data in tree_data_list:
                if tree_data['layer1_id'] == origin_dict['id'] and tree_data['layer1_label'] == origin_dict['label']:
                    if tree_data['layer2_id'] < 0:
                        layer2_list = []
                        break
                    else:
                        layer2_list.append(
                            dict(id=int(tree_data['layer2_id']),
                                 label=tree_data['layer2_label'],
                                 showInput=False,
                                 layer=2,
                                 children=tree_data['layer3_data']))

            origin.pop(origin_index)
            origin_dict['children'] = layer2_list
            origin.insert(origin_index, origin_dict)
        return jsonable_encoder(dict(code=200, msg="测试用例层级渲染数据获取成功", data=origin))


@server.get("/qa/automation/slot/fetchLayerData", response_model=ResponseModel, response_model_exclude_unset=True,
            tags=["页面数据"],
            summary="获取测试用例层级信息", description="按测试用例层级获取测试用例层级信息。")
async def fetchLayerData(epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                         pid: int = Query(default=-1, description="测试用例层级项目编号"),
                         sid: int = Query(default=-1, description="测试用例层级场景编号")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    if epic != "" and pid == -1 and sid == -1:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": {"$ne": -1}},
                            projection_json={"_id": 0, "Pid": 1, "Project": 1},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级为空", data=dict(total_count=0, layer_data=result, last_layer=[])))
        df = pd.DataFrame(data=result).drop_duplicates(keep='first').reset_index(drop=True).rename(
            columns={"Pid": "pid", "Project": "project"})
        result = df.to_dict(orient='records')
        last_layer = df.tail(1).to_dict(orient='records')
        return jsonable_encoder(
            dict(code=200, msg="测试用例层级信息获取成功",
                 data=dict(total_count=len(result), layer_data=result, last_layer=last_layer)))
    if epic != "" and pid >= 0 and sid == -1:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": {"$ne": -1}},
                            projection_json={"_id": 0, "Sid": 1, "Scenario": 1},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级为空", data=dict(total_count=len(result), layer_data=result, last_layer=[])))
        df = pd.DataFrame(data=result).drop_duplicates(keep='first').reset_index(drop=True).rename(
            columns={"Sid": "sid", "Scenario": "scenario"})
        result = df.to_dict(orient='records')
        last_layer = df.tail(1).to_dict(orient='records')
        return jsonable_encoder(
            dict(code=200, msg="测试用例层级信息获取成功",
                 data=dict(total_count=len(result), layer_data=result, last_layer=last_layer)))
    if epic != "" and pid >= 0 and sid >= 0:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid, "Tid": {"$ne": -1}},
                            projection_json={"_id": 0, "Tid": 1, "Title": 1},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级为空", data=dict(total_count=len(result), layer_data=result, last_layer=[])))
        df = pd.DataFrame(data=result).drop_duplicates(keep='first').reset_index(drop=True).rename(
            columns={"Tid": "tid", "Title": "title"})
        result = df.to_dict(orient='records')
        last_layer = df.tail(1).to_dict(orient='records')
        return jsonable_encoder(
            dict(code=200, msg="测试用例层级信息获取成功",
                 data=dict(total_count=len(result), layer_data=result, last_layer=last_layer)))
    else:
        return jsonable_encoder(dict(code=101, msg="非法的测试用例层级指定方式，请检查！", data=dict(pid=pid, sid=sid)))


@server.patch("/qa/automation/slot/modifyCaseLayer", response_model=ResponseModel, response_model_exclude_unset=True,
              tags=["页面数据"],
              summary="修改测试用例层级信息", description="根据测试用例标识修改测试用例层级信息（主要是所属场景和组内序号）")
async def modifyCaseLayer(layers: List[CaseLayerModel],
                          epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    else:
        none_update_list = []
        result_flag = True
        for layer in layers:
            layer_dict = layer.dict()
            pid = layer_dict['pid']
            pname = str(layer_dict['pname']).strip()
            sid = layer_dict['sid']
            sname = str(layer_dict['sname']).strip()
            tid = layer_dict['tid']
            case = str(layer_dict['case']).strip()
            update_flag = mongo.update_many(tbname="testcase",
                                            filter_json={"Epic": str(epic).strip(),
                                                         "_id": ObjectId(case)},
                                            update_json={"$set": {"Pid": pid,
                                                                  "Project": pname,
                                                                  "Sid": sid,
                                                                  "Scenario": sname,
                                                                  "Tid": tid,
                                                                  "UpdateTime": str(datetime.datetime.now())}},
                                            upsert=False)
            if update_flag == 0:
                none_update_list.append(dict(pid=pid, pname=pname, sid=sid, sname=sname, tid=tid, case=case))
            result_flag = result_flag and bool(update_flag)

        if result_flag is True:
            return jsonable_encoder(
                dict(code=200, msg="测试用例层级信息全部更新成功"))
        else:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级存在未更新的情况，该测试用例可能并不存在，请检查！",
                     data=none_update_list))


@server.post("/qa/automation/slot/saveCaseData", response_model=ResponseModel, response_model_exclude_unset=True,
             tags=["用例数据"],
             summary="保存测试用例数据", description="保存测试用例数据（新增或修改）。")
async def saveCaseData(testcases: List[TestCaseModel],
                       epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                       opt: int = Query(default=None, description="用例数据操作标识（1-新增，2-修改）")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定非空的当前自动化史诗唯一标识epic！"))
    if opt not in [1, 2]:
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定合法的用例数据操作标识，当前仅支持（1-新增，2-修改）！"))
    if opt == 1:
        for testcase in testcases:
            testcase_dict = testcase.dict()
            testcase_dict["Epic"] = str(epic).strip().upper()
            testcase_dict["CreateTime"] = str(datetime.datetime.now())
            testcase_dict["UpdateTime"] = ""
            pid = testcase_dict['Pid']
            pname = testcase_dict['Project']
            sid = testcase_dict['Sid']
            sname = testcase_dict['Scenario']
            tid = testcase_dict['Tid']
            if pid >= 0 and sid == -1 and tid == -1:
                exist = mongo.find_one(tbname="testcase",
                                       filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": -1, "Tid": -1})
                if exist is not None:
                    return jsonable_encoder(
                        dict(code=201, msg="当前一级节点已存在，不允许重复新增当前一级节点！", data=dict(pid=pid, pname=pname)))
                else:
                    mongo.update_many(tbname="testcase", filter_json={"Epic": str(epic).strip(),
                                                                      "Pid": pid},
                                      update_json={"$set": testcase_dict}, upsert=True)
            elif pid >= 0 and sid >= 0 and tid == -1:
                exist = mongo.find_one(tbname="testcase",
                                       filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid,
                                                    "Tid": -1})
                if exist is not None:
                    return jsonable_encoder(
                        dict(code=201, msg="当前二级节点已存在，不允许重复新增当前二级节点！",
                             data=dict(pid=pid, pname=pname, sid=sid, sname=sname)))
                else:
                    mongo.update_many(tbname="testcase", filter_json={"Epic": str(epic).strip(),
                                                                      "Pid": pid,
                                                                      "Sid": sid},
                                      update_json={"$set": testcase_dict}, upsert=True)
                    # mongo.delete_many(tbname="testcase", delete_json={"Epic": str(epic).strip(),
                    #                                                   "Pid": pid, "Sid": -1})
            elif pid >= 0 and sid >= 0 and tid >= 0:
                mongo.update_many(tbname="testcase", filter_json={"Epic": str(epic).strip(),
                                                                  "Pid": pid,
                                                                  "Sid": sid,
                                                                  "Tid": tid},
                                  update_json={"$set": testcase_dict}, upsert=True)
                # mongo.delete_many(tbname="testcase", delete_json={"Epic": str(epic).strip(),
                #                                                   "Pid": pid, "Sid": sid, "Tid": -1})
            else:
                return jsonable_encoder(dict(code=101, msg="非法测试用例层级序号", data=dict(pid=pid, sid=sid, tid=tid)))
        return jsonable_encoder(
            dict(code=200, msg="测试用例数据保存成功"))
    else:
        for testcase in testcases:
            testcase_dict = testcase.dict()
            testcase_dict["Epic"] = str(epic).strip().upper()
            testcase_dict["UpdateTime"] = str(datetime.datetime.now())
            pid = testcase_dict['Pid']
            pname = testcase_dict['Project']
            sid = testcase_dict['Sid']
            sname = testcase_dict['Scenario']
            tid = testcase_dict['Tid']
            tname = testcase_dict['Title']
            if pid >= 0 and sid == -1 and tid == -1:
                modify_flag = mongo.update_many(tbname="testcase", filter_json={"Epic": str(epic).strip(),
                                                                                "Pid": pid, "Sid": -1, "Tid": -1},
                                                update_json={"$set": testcase_dict}, upsert=False)
                if modify_flag == 0:
                    return jsonable_encoder(
                        dict(code=201,
                             msg="当前一级节点并不存在，修改操作无效！",
                             data=dict(pid=pid, pname=pname)))
            elif pid >= 0 and sid >= 0 and tid == -1:
                modify_flag = mongo.update_many(tbname="testcase", filter_json={"Epic": str(epic).strip(),
                                                                                "Pid": pid, "Sid": sid, "Tid": -1},
                                                update_json={"$set": testcase_dict}, upsert=False)
                if modify_flag == 0:
                    return jsonable_encoder(
                        dict(code=201,
                             msg="当前二级节点并不存在，修改操作无效！",
                             data=dict(pid=pid, pname=pname, sid=sid, sname=sname)))
                # mongo.delete_many(tbname="testcase", delete_json={"Epic": str(epic).strip(),
                #                                                   "Pid": pid, "Sid": -1})
            elif pid >= 0 and sid >= 0 and tid >= 0:
                modify_flag = mongo.update_many(tbname="testcase", filter_json={"Epic": str(epic).strip(),
                                                                                "Pid": pid, "Sid": sid, "Tid": tid},
                                                update_json={"$set": testcase_dict}, upsert=False)
                if modify_flag == 0:
                    return jsonable_encoder(
                        dict(code=201,
                             msg="当前三级节点并不存在，修改操作无效！",
                             data=dict(pid=pid, pname=pname, sid=sid, sname=sname, tid=tid, tname=tname)))
                # mongo.delete_many(tbname="testcase", delete_json={"Epic": str(epic).strip(),
                #                                                   "Pid": pid, "Sid": sid, "Tid": -1})
            else:
                return jsonable_encoder(dict(code=101, msg="非法测试用例层级序号", data=dict(pid=pid, sid=sid, tid=tid)))
        return jsonable_encoder(
            dict(code=200, msg="测试用例数据修改成功"))


@server.get("/qa/automation/slot/loadCaseData", response_model=ResponseModel, response_model_exclude_unset=True,
            tags=["用例数据"],
            summary="获取测试用例数据", description="按测试用例层级获取测试用例数据。")
async def loadCaseData(epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                       pid: int = Query(default=-1, description="测试用例层级项目编号"),
                       sid: int = Query(default=-1, description="测试用例层级场景编号"),
                       tid: int = Query(default=-1, description="测试用例层级用例编号")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    if epic != "" and pid == -1 and sid == -1 and tid == -1:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": {"$ne": -1}, "Sid": {"$ne": -1},
                                         "Tid": {"$ne": -1}},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例加载结果集为空", data=dict(total_count=len(result), case_data=result)))
        return jsonable_encoder(dict(code=200, msg="测试用例数据加载成功", data=dict(total_count=len(result), case_data=result)))
    if epic != "" and pid >= 0 and sid == -1 and tid == -1:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": {"$ne": -1}, "Tid": {"$ne": -1}},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例加载结果集为空", data=dict(total_count=len(result), case_data=result)))
        return jsonable_encoder(dict(code=200, msg="测试用例数据加载成功", data=dict(total_count=len(result), case_data=result)))
    if epic != "" and pid >= 0 and sid >= 0 and tid == -1:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid, "Tid": {"$ne": -1}},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例加载结果集为空", data=dict(total_count=len(result), case_data=result)))
        return jsonable_encoder(dict(code=200, msg="测试用例数据加载成功", data=dict(total_count=len(result), case_data=result)))

    if epic != "" and pid >= 0 and sid >= 0 and tid >= 0:
        result = mongo.find(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid, "Tid": tid},
                            sort_json={"Pid": 1, "Sid": 1, "Tid": 1, "CreateTime": 1})
        if result == []:
            return jsonable_encoder(
                dict(code=201, msg="测试用例加载结果集为空", data=dict(total_count=len(result), case_data=result)))
        return jsonable_encoder(dict(code=200, msg="测试用例数据加载成功", data=dict(total_count=len(result), case_data=result)))
    else:
        return jsonable_encoder(dict(code=101, msg="非法的测试用例层级指定方式，请检查！", data=dict(pid=pid, sid=sid, tid=tid)))


@server.patch("/qa/automation/slot/updateCaseProject/{epic}/{pid}", response_model=ResponseModel,
              response_model_exclude_unset=True,
              tags=["用例数据"],
              summary="修改测试用例项目信息", description="修改自动化史诗下指定项目编号的项目信息。")
async def updateCaseProject(epic: str = Path(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                            pid: int = Path(default=-1, description="测试用例层级项目编号"),
                            pname: str = Query(default="", description="更改后的项目名称")
                            ):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    if pid < 0:
        return jsonable_encoder(dict(code=100, msg="检测到非法的一级节点序号（其必须为自然数）"))
    if pname == "":
        return jsonable_encoder(dict(code=100, msg="测试用例层级项目名称不允许更改为空！"))
    if epic != "" and pid >= 0 and pname != "":
        update_flag = mongo.update_many(tbname="testcase",
                                        filter_json={"Epic": str(epic).strip(), "Pid": pid},
                                        update_json={"$set": {"Project": pname}},
                                        upsert=False)
        if update_flag != 0:
            return jsonable_encoder(
                dict(code=200, msg="测试用例层级项目名称更新成功"))
        else:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级项目名称无任何更新，指定项目编号的数据可能并不存在或未做任何修改，请检查！"))


@server.patch("/qa/automation/slot/updateCaseScenario/{epic}/{pid}/{sid}", response_model=ResponseModel,
              response_model_exclude_unset=True,
              tags=["用例数据"],
              summary="修改测试用例场景信息", description="修改自动化史诗下指定场景编号的场景信息。")
async def updateCaseScenario(epic: str = Path(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                             pid: int = Path(default=-1, description="测试用例层级项目编号"),
                             sid: int = Path(default=-1, description="测试用例层级场景编号"),
                             sname: str = Query(default="", description="更改后的场景名称")
                             ):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    if pid < 0:
        return jsonable_encoder(dict(code=100, msg="检测到非法的一级节点序号（其必须为自然数）"))
    if sid < 0:
        return jsonable_encoder(dict(code=100, msg="检测到非法的二级节点序号（其必须为自然数）"))
    if sname == "":
        return jsonable_encoder(dict(code=100, msg="测试用例层级场景名称不允许更改为空！"))
    if epic != "" and pid >= 0 and sid >= 0 and sname != "":
        update_flag = mongo.update_many(tbname="testcase",
                                        filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid},
                                        update_json={"$set": {"Scenario": sname}},
                                        upsert=False)
        if update_flag != 0:
            return jsonable_encoder(
                dict(code=200, msg="测试用例层级场景名称更新成功"))
        else:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级场景名称无任何更新，指定场景编号的数据可能并不存在或未做任何修改，请检查！"))


@server.patch("/qa/automation/slot/updateCaseTitle/{epic}/{pid}/{sid}/{tid}", response_model=ResponseModel,
              response_model_exclude_unset=True,
              tags=["用例数据"],
              summary="修改测试用例名称信息", description="修改自动化史诗下指定用例编号的名称信息。")
async def updateCaseTitle(epic: str = Path(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                          pid: int = Path(default=-1, description="测试用例层级项目编号"),
                          sid: int = Path(default=-1, description="测试用例层级场景编号"),
                          tid: int = Path(default=-1, description="测试用例层级用例编号"),
                          tname: str = Query(default="", description="更改后的用例名称")
                          ):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    if pid < 0:
        return jsonable_encoder(dict(code=100, msg="检测到非法的一级节点序号（其必须为自然数）"))
    if sid < 0:
        return jsonable_encoder(dict(code=100, msg="检测到非法的二级节点序号（其必须为自然数）"))
    if tid < 0:
        return jsonable_encoder(dict(code=100, msg="检测到非法的三级节点序号（其必须为自然数）"))
    if tname == "":
        return jsonable_encoder(dict(code=100, msg="测试用例层级场景名称不允许更改为空！"))
    if epic != "" and pid >= 0 and sid >= 0 and tid >= 0 and tname != "":
        update_flag = mongo.update_many(tbname="testcase",
                                        filter_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid, "Tid": tid},
                                        update_json={"$set": {"Title": tname}},
                                        upsert=False)
        if update_flag != 0:
            return jsonable_encoder(
                dict(code=200, msg="测试用例层级用例名称更新成功"))
        else:
            return jsonable_encoder(
                dict(code=201, msg="测试用例层级用例名称无任何更新，指定用例编号的数据可能并不存在或未做任何修改，请检查！"))


@server.delete("/qa/automation/slot/removeCaseData", response_model=ResponseModel, response_model_exclude_unset=True,
               tags=["用例数据"],
               summary="删除测试用例数据", description="按测试用例层级获取测试用例数据。")
async def removeCaseData(epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                         pid: int = Query(default=-1, description="测试用例层级项目编号"),
                         sid: int = Query(default=-1, description="测试用例层级场景编号"),
                         tid: int = Query(default=-1, description="测试用例层级用例编号")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="请首先指当前自动化史诗唯一标识epic！"))
    if epic != "" and pid == -1 and sid == -1 and tid == -1:
        count = mongo.delete_many(tbname="testcase",
                                  delete_json={"Epic": str(epic).strip()})
        if count == 0:
            return jsonable_encoder(
                dict(code=201, msg="当前暂无结果集，删除操作无效！"))
        return jsonable_encoder(dict(code=200, msg="测试用例数据删除成功", data=dict(delete_count=count)))
    if epic != "" and pid >= 0 and sid == -1 and tid == -1:
        count = mongo.delete_many(tbname="testcase",
                                  delete_json={"Epic": str(epic).strip(), "Pid": pid})
        if count == 0:
            return jsonable_encoder(
                dict(code=201, msg="当前暂无结果集，删除操作无效！"))
        return jsonable_encoder(dict(code=200, msg="测试用例数据删除成功", data=dict(delete_count=count)))
    if epic != "" and pid >= 0 and sid >= 0 and tid == -1:
        count = mongo.delete_many(tbname="testcase",
                                  delete_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid})
        if count == 0:
            return jsonable_encoder(
                dict(code=201, msg="当前暂无结果集，删除操作无效！"))
        return jsonable_encoder(dict(code=200, msg="测试用例数据删除成功", data=dict(delete_count=count)))

    if epic != "" and pid >= 0 and sid >= 0 and tid >= 0:
        count = mongo.delete_many(tbname="testcase",
                                  delete_json={"Epic": str(epic).strip(), "Pid": pid, "Sid": sid, "Tid": tid})
        if count == 0:
            return jsonable_encoder(
                dict(code=201, msg="当前暂无结果集，删除操作无效！"))
        return jsonable_encoder(dict(code=200, msg="测试用例数据删除成功", data=dict(delete_count=count)))
    else:
        return jsonable_encoder(dict(code=101, msg="非法的测试用例层级指定方式，请检查！", data=dict(pid=pid, sid=sid, tid=tid)))


@server.get("/qa/automation/slot/getSingleCase", response_model=ResponseModel, response_model_exclude_unset=True,
            tags=["用例数据"],
            summary="根据用例数据标识获取测试用例数据", description="根据用例数据标识获取测试用例数据。")
async def getSingleCase(epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                        case_id: str = Query(default="", description="当前自动化项目用例数据唯一标识，如5ff2c39364efd65eed78597e")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定非空的当前自动化史诗唯一标识epic！"))
    if case_id == "":
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定非空的测试用例数据唯一标识case_id！"))
    result = mongo.find_one(tbname="testcase",
                            filter_json={"Epic": str(epic).strip(), "_id": ObjectId(str(case_id).strip())})
    if result is None:
        return jsonable_encoder(
            dict(code=201, msg="测试用例查询结果集为空"))
    else:
        return jsonable_encoder(
            dict(code=200, msg="测试用例数据查询成功",
                 data=result))


@server.delete("/qa/automation/slot/deleteSingleCase", response_model=ResponseModel, response_model_exclude_unset=True,
               tags=["用例数据"],
               summary="根据用例数据标识删除测试用例数据", description="根据用例数据标识删除测试用例数据。")
async def deleteSingleCase(epic: str = Query(default="", description="当前自动化史诗唯一标识，如KXHNEW"),
                           case_id: str = Query(default="", description="当前自动化项目用例数据唯一标识，如5ff2c39364efd65eed78597e")):
    if epic == "":
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定非空的当前自动化史诗唯一标识epic！"))
    if case_id == "":
        return jsonable_encoder(dict(code=100, msg="非法请求参数", data="请指定非空的测试用例数据唯一标识case_id！"))
    delete_flag = mongo.delete_many(tbname="testcase",
                                    delete_json={"Epic": str(epic).strip(),
                                                 "_id": ObjectId(str(case_id).strip())})
    if delete_flag != 0:
        return jsonable_encoder(
            dict(code=200, msg="测试用例数据删除成功"))
    else:
        return jsonable_encoder(
            dict(code=201, msg="测试用例数据删除无效，可能该用例并不存在！", data=dict(epic=epic, case_id=case_id)))


server.mount("/test-plus",
             app=StaticFiles(directory="/automation/Gastepo/Template/dist",
                             html=True), name="test-plus")

# 启动服务
if __name__ == '__main__':
    uvicorn.run(app="SlotServer:server", host="10.6.0.116", port=12010, debug=True, reload=True)
    # uvicorn.run(app="SlotServer:server", host="localhost", port=12010, debug=True, reload=True)
