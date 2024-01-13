#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from enum import Enum
from typing import Any, Optional, Union
from pydantic import BaseModel, Field, root_validator


class Project(BaseModel):
    pno: str = Field(title="项目编号")
    name: str = Field(title="名称")
    address: str = Field(title="地址")
    mobile:str = Field(title="联系人号码")

    @root_validator(pre=True)
    def check_data(cls, value):
        if not value.get("pno"): raise ValueError("请填项目编号")
        if not value.get("name"): raise ValueError("请填名称")
        if not value.get("address"): raise ValueError("请填地址")
        if not value.get("mobile"): raise ValueError("请填联系人号码")
        return value

class Response(BaseModel):
    message: str = Field(title="信息")
    code: int = Field(title="业务code")
    data: Any = Field(title="数据")

class CreateResponse(Response):
    data: Optional[str]

class DeleteProject(BaseModel):
    pno: Union[str, list]

    @root_validator(pre=True)
    def check_data(cls, value):
        if not value.get("pno"): raise ValueError("请输入编号")
        return value

class queryResponse(BaseModel):
    pno: Union[str, None]

class Input(BaseModel):
    url: str
    method: str
    params: dict = None
    headers: dict = None

    class Config:
        schema_extra = {
            "example": {
                "url": "http://gateway.sit.yunexpress.com/gw/opd-ofp-receive/orderTaskGenerationRule/list",
                "method": "POST",
                "params": {"apiId": "593"},
                "headers": {
                "Content-Type": "application/json",
                "Authorization": "Nebula token:bfc9c6cdba3e41f1979cb6e1b288f1d9",
                "Accept-Language": "zh_cn"
                }
            }
        }