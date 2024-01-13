#!/usr/bin/python3
# -*- coding: UTF-8 -*-


class TestResponseCode(object):
    SUCCESS = {"message": "请求成功", "code": 100000, "data": ""}
    CreateError = {"message": "数据已存在", "code": 100001, "data": ""}
    NotfoundError={"message": "数据不存在", "code": 100002, "data": ""}
    deleteError={"message": "数据已被删除", "code": 100003, "data": ""}
