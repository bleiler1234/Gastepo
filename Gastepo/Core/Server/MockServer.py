# -*- coding: utf-8 -*-
import json
import os
import secrets
from typing import List, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, Response, Path, Query, Header, Form, File, UploadFile, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import BaseModel

from Gastepo.Core.Util.CommonUtils import json_to_xml, xml_to_json

"""
描述：自动化测试模拟接口Web服务，如Mock测试接口等。
"""
server = FastAPI(title="Mock Server", description="该文档中所有Mock接口主要用于自动化框架的单元测试。",
                 docs_url='/qa/mock/api-docs', redoc_url='/qa/mock/re-docs',
                 openapi_url="/qa/mock/open-api.json")
security = HTTPBasic()


# 请求体模型
class RequestModel(BaseModel):
    id: int
    name: str


# 响应体模型
class ResponseModel(BaseModel):
    code: int
    msg: str
    data: Any


# 敏感接口HTTPBasic账套鉴权
def verify_login_account(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "qa")
    correct_password = secrets.compare_digest(credentials.password, "123456")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Login Account!",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


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


@server.post("/mock/post01", response_model=ResponseModel, tags=["数据依赖"], summary="生产者post01",
             description="其用于生产接口依赖数据，如post02的依赖数据。")
async def post01():
    return jsonable_encoder(dict(code=100, msg="success", data=[dict(id=2, name="mayer")]))


@server.post("/mock/post02", response_model=ResponseModel, tags=["数据依赖"], summary="消费者post02",
             description="请求体为列表形式，其作为消费者并依赖post01中响应体数据。")
async def post02(req: List[RequestModel]):
    return jsonable_encoder(dict(code=100, msg="success", data=req))


@server.get("/mock/get01", response_model=ResponseModel, tags=["数据依赖"], summary="消费者get01",
            description="测试有参及无参场景下的GET请求")
async def get01(id: Optional[int] = Query(default=1)):
    return jsonable_encoder(dict(code=100, msg="success", data=id))


@server.patch("/mock/patch01", response_model=List[ResponseModel], tags=["请求扩展"], summary="PATCH请求",
              description="测试patch接口请求方式")
async def patch01(req: RequestModel):
    return jsonable_encoder([dict(code=100, msg="success", data=req), dict(code=100, msg="success", data=req)])


@server.delete("/mock/delete01", response_model=ResponseModel, tags=["请求扩展"], summary="DELETE请求",
               description="测试delete接口请求方式")
async def delete01(id: Optional[int] = Query(default=1)):
    return jsonable_encoder(dict(code=100, msg="success", data=id))


@server.put("/mock/put01", response_model=ResponseModel, tags=["请求扩展"], summary="PUT请求",
            description="测试put接口请求方式")
async def put01(id: Optional[int] = Query(default=1)):
    return jsonable_encoder(dict(code=100, msg="success", data=id))


@server.get("/mock/path01/{name}/test/{id}", response_model=ResponseModel, tags=["请求扩展"], summary="PATH路径接口",
            description="测试路径参数接口")
async def path01(name: str = Path(default="yzh"), id: int = Path(default=1, ge=1, le=10),
                 group: str = Query(default="A")):
    result = "now {}'s id is equal to {}".format(name, id)
    return jsonable_encoder(dict(code=100, msg="success", data=dict(id=id, group=group, result=result)))


@server.get("/mock/header01", response_model=ResponseModel, tags=["请求扩展"], summary="请求头接口",
            description="测试请求头接口")
async def header01(id: int = Header(default=1, ge=1, le=10)):
    result = "now id is equal to {}".format(id)
    return jsonable_encoder(dict(code=100, msg="success", data=dict(id=id, result=result)))


@server.post("/mock/complex01/{p1}", response_model=ResponseModel, tags=["请求扩展"], summary="所有请求位置接口",
             description="测试包含所有请求位置的接口")
async def complex01(d1: RequestModel, p1: str = Path(default="path1"), h1: str = Header(default="header1"),
                    q1: str = Query(default="param1")):
    return jsonable_encoder(dict(code=100, msg="success", data=dict(p1=p1, h1=h1, q1=q1, d1=d1)))


@server.post('/mock/www-form-urlencode01', response_model=ResponseModel, tags=["请求扩展"],
             summary="www-form-urlencode类型接口")
async def www_form_urlencode01(id: int = Form(media_type="application/x-www-form-urlencoded", default=None, ge=1,
                                              le=10),
                               name: str = Form(media_type="application/x-www-form-urlencoded", default=None,
                                                regex=r'^test.*')):
    return jsonable_encoder(dict(code=100, msg="success", data={"id": id, "name": name}))


@server.post('/mock/form-data01', response_model=ResponseModel, tags=["请求扩展"], summary="multipart/form-data类型接口")
async def form_data01(id: int = Form(media_type="multipart/form-data", default=None, ge=1, le=10),
                      name: str = Form(media_type="multipart/form-data", default=None, regex=r'^test.*'),
                      files: List[UploadFile] = File(...)):
    return jsonable_encoder(dict(code=100, msg="success",
                                 data=dict(id=id,
                                           name=name,
                                           file={"filename": [file.filename for file in files],
                                                 "filetype": [file.content_type for file in files]}
                                           )
                                 )
                            )


@server.get(path="/mock/get_xml01", tags=["请求扩展"], summary="XML报文的GET接口")
async def get_xml01():
    data = {"history": {"id": 1, "name": "Mayer",
                        "battle": [{"order": "o1", "location": "Japan"}, {"order": "o2", "location": "Korean"}]}}
    return Response(content=json_to_xml(data), media_type="application/xml")


class XmlBody:
    def __init__(self, model_class):
        self.model_class = model_class

    async def __call__(self, request: Request):
        if request.headers.get("Content-Type") == "application/xml":
            print("yes")
            data = await request.body()
            return data.decode('utf-8')
        else:
            print("No")
            data = await request.json()
            return data


@server.post(path="/mock/post_xml01", tags=["请求扩展"], summary="XML报文的POST接口")
async def post_xml01(request: Request, data: Any = Depends(XmlBody(Any))):
    if request.headers.get("Content-Type") == "application/xml":
        result = {"convert": True}
        result.update(json.loads(xml_to_json(data)))
        xml_result = json_to_xml(dict(result=result))
        return Response(content=xml_result, media_type="application/xml")
    else:
        result = {"convert": False}
        result.update(data)
        json_result = dict(result=result)
    return jsonable_encoder(json_result)


@server.post('/mock/upload', response_model=ResponseModel, tags=["请求扩展"], summary="模拟上传接口")
async def upload(files: List[UploadFile] = File(...)):
    fail_upload = []
    for file in files:
        if file.filename == "":
            return dict(code=998, msg="invalid", data="请首先指定文件")
        file_contents = await file.read()
        upload_file = "/temp/{}".format(file.filename)  # 注意待创建文件的上层文件夹upload必须首先存在
        with open(file=upload_file, mode='wb') as f:
            f.write(file_contents)
        if not os.path.exists(upload_file):
            fail_upload.append(upload_file)
    if fail_upload == []:
        return dict(code=100, msg="success", data="全部写入成功")
    else:
        return dict(code=999, msg="failure", data=fail_upload)


@server.get("/mock/download/{filename}", tags=["请求扩展"], summary="模拟下载接口")
async def download(filename: str):
    file_path = os.path.join("/temp/{}".format(filename))
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        return dict(code=999, msg="failure", data="/temp/{} is not exist".format(filename))


@server.get("/mock/stream/{filename}", response_model=ResponseModel, tags=["请求扩展"], summary="模拟文件下载流")
async def stream(filename: str):
    file_path = os.path.join("/temp/{}".format(filename))
    if os.path.exists(file_path):
        with open(file_path, mode=r'r', encoding='utf-8') as f:
            return dict(code=100, msg="success", data=f.read())
    else:
        return dict(code=999, msg="failure", data="/temp/{} is not exist".format(filename))


@server.get("/mock/auth01", response_model=ResponseModel, tags=["请求扩展"], summary="模拟鉴权接口",
            dependencies=[Depends(verify_login_account)])
async def auth01():
    return jsonable_encoder(dict(code=100, msg="success", data="auth pass"))


# 启动服务
if __name__ == '__main__':
    uvicorn.run(app="MockServer:server", host="0.0.0.0", port=5002, debug=True, reload=True)
