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
