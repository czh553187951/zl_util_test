#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from fastapi import APIRouter

from test_api.schema import Project, CreateResponse, queryResponse, Input, DeleteProject
from test_api.views import TestObject

router = APIRouter()

@router.get(path="/queryall", summary="查询列表")
async def query_api():
    return await TestObject.query_list()

@router.post(path="/query", summary="查询列表")
async def query_api(request_data:queryResponse):
    return await TestObject.query_data(request_data.dict())

@router.post(path="/addproject", summary="添加接口", response_model=CreateResponse)
async def create_api(request_data: Project):
    return await TestObject.create_data(request_data.dict())


@router.post(path="/updateproject", summary="修改接口", response_model=CreateResponse)
async def create_api(request_data: Project):
    return await TestObject.update_data(request_data.dict())


@router.post(path="/deleteproject", summary="删除接口", response_model=CreateResponse)
async def del_api(request_data:DeleteProject):
    return await TestObject.delete_data(request_data.dict())

@router.post(path="/uploadfile/", summary="上传", response_model=queryResponse)
async def create_api(request_data: Input):
    return await TestObject.query_score_data(request_data.dict())

@router.post(path="/compare",summary="json对比"):
async def compare(request_data):
    return await TestObject.update_data(request_data.dict())

#
# @app.post("/uploadfile/")
# async def upload_excel_file(file: UploadFile = File(...)):
#     try:
#         contents = await file.read()
#         filename = file.filename
#         with open(filename, "wb") as file_object:
#             file_object.write(contents)
#         return JSONResponse(content={"message": "File uploaded successfully"})
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
#
# @app.post("/modifyfile/")
# async def modify_excel_file(file: UploadFile = File(...)):
#     try:
#         contents = await file.read()
#         wb = load_workbook(filename=file.filename)
#         sheet = wb.active
#         sheet["A1"] = "Modified Value"
#         wb.save(file.filename)
#         return JSONResponse(content={"message": "File modified successfully"})
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
#
#
# @app.post("/requestapi/")
# async def my_api(request: Request, data: Input):
#     try:
#         url = data.url
#         method = data.method.upper()
#         params = data.params
#         headers = data.headers
#         response = requests.request(method=method, url=url, json=params, headers=headers)
#         return response.json()
#     except Exception as e:
#         return {"error": "Invalid input data", "details": str(e)}
