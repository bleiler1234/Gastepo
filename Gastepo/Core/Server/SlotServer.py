# -*- coding: utf-8 -*-
import sys

sys.path.append("/automation/Gastepo")
import random
from typing import Any

import pandas as pd
import uvicorn
from fastapi import FastAPI, Request, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from bson.objectid import ObjectId
from Gastepo.Core.Util.DatabaseUtils import MongodbDatabaseTools

"""
描述：自动化测试用例插槽Web服务，如用于对接自定义UI页面编写自动化用例等。
"""
session = MongodbDatabaseTools(env='qa', dbname='gastepo',
                               auth_dict={"auth_db": "admin", "auth_username": "root",
                                          "auth_password": "123456"})
mongo = session.db()

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


# 请求体模型
class RequestModel(BaseModel):
    id: int
    name: str


# 响应体模型
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any


def random_int(min=0, max=9, seed=False, string=False):
    if seed is True:
        random.seed()
        value = random.randint(min, max)
        return value if string is False else str(value)
    else:
        value = random.randint(min, max)
        return value if string is False else str(value)


def mock_data(query_id):
    origin_df = pd.read_excel(
        "/automation/KxhAutoTest/Common/Data/Kxh/ApiTestCase_stg.xls").fillna(
        "")
    origin_df = origin_df[
        ['Project', 'Scenario', 'Title', 'BaseUrl', 'UrlPath', 'Method', 'Consumes', 'Platform', 'Level', 'Active',
         'RequestPath', 'RequestHeader', 'RequestParam', 'RequestData', 'RequestFile', 'DependencyInfo', 'AssertInfo']]
    total_row = origin_df.shape[0]
    mock_df = pd.DataFrame(origin_df.iloc[random_int(0, total_row - 1), :]).T
    mock_df['Active'] = mock_df["Active"].astype(bool)
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


@server.get("/qa/automation/slot/getTreeMetadata", response_model=ResponseModel, tags=["元数据"], summary="页面目录树")
async def getTreeMetaData():
    data = mongo.find_one(tbname="metadata",
                          filter_json={"_id": ObjectId("6093896b2ab1710a65c3e1b5")},
                          projection_json={"_id": 0})
    if data is not None:
        return jsonable_encoder(dict(code=200, msg="success", data=[data]))
    else:
        return jsonable_encoder(dict(code=201, msg="empty result", data=[]))


@server.get("/qa/automation/slot/getCaseData", response_model=ResponseModel, tags=["用例数据（Mock）"], summary="根据用例数据标识获取测试用例数据")
async def getCaseData(query_id: str = Query(default="", description="文档库中用例数据标识，其是测试用例数据的唯一标识")):
    if query_id == "":
        return jsonable_encoder(dict(code=100, msg="invalid request param", data="请指定非空的用例数据标识query_id！"))
    else:
        return jsonable_encoder(dict(code=200, msg="success", data=mock_data(query_id=query_id)))


# 启动服务
if __name__ == '__main__':
    uvicorn.run(app="SlotServer:server", host="10.6.0.116", port=12010, debug=True, reload=True)
