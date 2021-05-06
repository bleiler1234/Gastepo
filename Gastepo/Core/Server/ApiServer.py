# -*- coding: utf-8 -*-

import json
import re
from typing import Any, List, Optional

import uvicorn
from fastapi import FastAPI, Request, Query, Body
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from hamcrest import *
from pydantic import BaseModel, Field

from Gastepo.Core.Base.BaseData import MATCHER_TYPE
from Gastepo.Core.Extend.AssertDependencyExtends import *
from Gastepo.Core.Extend.HamcrestCustomExtends import *
from Gastepo.Core.Util.AssertionUtils import AdvanceAssertionTools
from Gastepo.Core.Util.CommonUtils import emoji_to_str

"""
描述：自动化测试扩展功能Web服务，如在线断言调试器等。
"""
server = FastAPI(title="Automation", description="主要通过接口方式在线使用自动化测试相关功能扩展, 如在线断言调试等。",
                 docs_url='/qa/debug/api-docs', redoc_url='/qa/debug/re-docs',
                 openapi_url="/qa/debug/open-api.json")


# 断言Schema模型
class AssertSchemaModel(BaseModel):
    actual: Any = Field(title="实际结果", example="$.err")
    expect: list = Field(title="预期结果", example=[[0, 1]])
    matcher: str = Field(title="匹配器", example="is_in")
    alert: str = Field(title="警告提示", example="value is not in list.")
    multi: Optional[bool] = Field(title="JsonPath列表结果开关", example=False)


# 测试结果模型
class TestResultModel(BaseModel):
    actual_data: Any = Field(title="Actual结果", example=[4])
    expect_data: Any = Field(title="Expect结果", example=[[0, 1]])
    debug_result: str = Field(title="测试结论", example="断言失败")
    fail_reason: str = Field(title="失败原因", example="\nExpected: one of (<0>, <1>)\n     but: was <4>\n", default="")


# 响应体模型
class ResponseBodyModel(BaseModel):
    code: int = Field(title="响应码", example=100)
    msg: str = Field(title="响应体", example="success")
    assert_schema: List[AssertSchemaModel]
    assert_result: TestResultModel


# 请求体模型
class RequestBodyModel(BaseModel):
    pass


# 响应样例
REQUEST_BODY_EXAMPLE = {
    "data": {
        "diagnosisInfoId": 5384,
        "payRecordId": 5014,
        "appId": 725
    },
    "err": 0,
    "errmsg": "操作成功"
}


# 识别并拼接复合断言器
def combine_matcher(matcher_expr, params):
    matcher_list = re.findall('[^()]+', str(matcher_expr))
    matchers = matcher_expr.replace(str(matcher_list[-1]), str(matcher_list[-1]) + "(*{args})").format(
        args=params)
    return matchers


# actual实际数据类型转换器
def analyze_expr(origin_expr):
    if re.match(r"((^\{.*\}$)|(^\[.*\]$)|(^\(.*\)$))", str(origin_expr)):
        return eval(origin_expr)
    else:
        return origin_expr


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


@server.post("/debug/assert", tags=["调试器"], summary="高级断言调试器",
             description="主要针对自动化测试断言Schema进行在线调试；当前支持常量、JsonPath表达式、类SpEL表达式、接口依赖表达式及函数依赖表达式。",
             response_model=ResponseBodyModel, response_model_exclude_unset=True, response_description="断言调试结果的接口响应")
async def assert_debuger(request: Request,
                         request_body: RequestBodyModel = Body(default={}, example=REQUEST_BODY_EXAMPLE),
                         actual: str = Query(title="实际结果",
                                             description='如通过JsonPath表达式获取响应数据, "$.data[0].name"',
                                             default="$"),
                         expect: str = Query(title="预期结果", description='预期结果必须以列表形式指定, 如["${1+2}"]。',
                                             default="[]", regex=r'^\[.*\]$'),
                         matcher: str = Query(title="匹配器", description="请指定Hamcrest匹配器, 如has_items等。",
                                              default="has_items"),
                         alert: Optional[str] = Query(title="错误提示", description="若断言错误, 则提示此警告信息。",
                                                      default="assert failure"),
                         multi: Optional[bool] = Query(title="JsonPath列表结果开关",
                                                       description="若True则为开启状态，那么所有JsonPath结果均为列表形式。", default=False)):
    # 获取响应体
    request_body = await request.json()

    # 生成断言表达式
    assert_schema = []
    assert_dict = dict(actual=analyze_expr(actual),
                       expect=eval(expect),
                       matcher=matcher,
                       alert=alert,
                       multi=multi)
    assert_schema.append(assert_dict)
    fetch_schema = assert_schema[0]

    # 初始化断言器
    # todo: realtime_dependency可以使用离线录制数据，需提供上传接口并需要开启schema_url的debug模式。
    asserter = AdvanceAssertionTools(test_case_schema={}, origin_data=request_body,
                                     realtime_dependency={})

    # 调试断言Schema
    actual_data = emoji_to_str(asserter.analysis_actual(param_expr=fetch_schema.get("actual"),
                                                        origin_data=request_body,
                                                        function_mode=False,
                                                        multi=fetch_schema.get("multi")))
    print("当前Assert Schema为：\n{}".format(json.dumps(assert_schema, indent=2, ensure_ascii=False)))
    print("actual匹配数据为：{}".format(actual_data))
    if isinstance(fetch_schema.get("expect"), list) and fetch_schema.get("expect").__len__() != 0:
        expect_data = emoji_to_str([asserter.analysis_expect(param_expr=fetch_schema.get("expect")[0],
                                                             origin_data=request_body,
                                                             multi=fetch_schema.get("multi"))])
    else:
        print('[WARNING]：高级断言中expect数据依赖表达式"{}"必须以列表方式指定且不能为空, 请检查并修改！'.format(fetch_schema.get("expect")))
        expect_data = emoji_to_str(["" if fetch_schema.get("expect") == [] else fetch_schema.get("expect")])

    print("expect期望数据为：{}".format(expect_data))
    now_matcher = fetch_schema.get("matcher")
    print("matcher断言器为：{}".format(now_matcher))
    now_alert = fetch_schema.get("alert")
    print("alert默认提示为：{}".format(now_alert))
    multi_flag = fetch_schema.get("multi")
    print("multi开关状态为：{}".format(multi_flag))
    print("*".center(100, "*"))
    try:
        assert_that(actual=actual_data,
                    matcher=eval(combine_matcher(matcher_expr=fetch_schema.get("matcher"), params=expect_data)),
                    reason=now_alert)
        print("{} ☞【Assert断言通过】".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        print("*".center(100, "*"))
        return jsonable_encoder(dict(code=100, msg="assert success", assert_schema=[assert_dict],
                                     assert_result=dict(actual_data=actual_data, expect_data=expect_data,
                                                        debug_result="断言通过")))
    except AssertionError as e:
        print("{} ☞【Assert断言失败】，原因为：{}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), e))
        print("*".center(100, "*"))
        return jsonable_encoder(dict(code=101, msg="assert failure", assert_schema=[assert_dict],
                                     assert_result=dict(actual_data=actual_data, expect_data=expect_data,
                                                        debug_result="断言失败",
                                                        fail_reason=str(e))))


@server.get("/assert/dependency/functions", tags=["相关"], summary="高级断言依赖函数", description="显示当前高级断言支持的所有依赖函数。")
async def dependency_functions(
        role: Optional[str] = Query(default="全部", description="显示指定类别下的所有依赖函数。", regex=r'^全部$|^系统$|^框架$|^业务$')):
    dependency_functions_list = []
    if role == "全部":
        for dependency_function_info in FUNCTION_ENUM.__members__.values():
            dependency_functions_list.append(dependency_function_info.value)

        return jsonable_encoder(dependency_functions_list)
    else:
        for dependency_function_info in FUNCTION_ENUM.__members__.values():
            if dependency_function_info.value["role"] == role:
                dependency_functions_list.append(dependency_function_info.value)
        return jsonable_encoder(dependency_functions_list)


@server.get("/assert/matcher/hamcrest", tags=["相关"], summary="高级断言Hamcrest匹配器", description="显示当前高级断言支持的常用Hamcrest匹配器。")
async def matcher_hamcrest():
    matcher_hamcrest_list = []
    for matcher_hamcrest_info in MATCHER_TYPE.__members__.values():
        matcher_hamcrest_list.append(matcher_hamcrest_info.value)

    return jsonable_encoder(matcher_hamcrest_list)


# 启动服务
if __name__ == '__main__':
    uvicorn.run(app="ApiServer:server", host="0.0.0.0", port=5001, debug=True, reload=True)
