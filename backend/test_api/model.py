#!/usr/bin/python3
# -*- coding: utf-8 -*-
from tortoise import Model, fields

class Base_Model():
    id = fields.IntField(pk=True)
    created_time = fields.DatetimeField(auto_now_add=True, description="创建时间")
    modified_time = fields.DatetimeField(auto_now=True, description="修改时间")
    deleted = fields.IntField(default="0", description="是否删除(0：未删除，1：已删除")


class ProjectTable(Base_Model,Model):
    id = fields.IntField(pk=True)
    pno = fields.CharField(null=False,max_length=10, description="项目编号")
    name = fields.CharField(null=False,max_length=10, description="名称")
    address = fields.CharField(null=False,max_length=50, description="项目地址")
    mobile = fields.CharField(null=False,max_length=50, description="联系人电话")

    class Meta:
        table = "project_table"
        table_description = "项目表"
        ordering = ["-created_time"]

class DatasetTable(Base_Model,Model):
    id = fields.IntField(pk=True)
    dataname = fields.CharField(null=False,max_length=10, description="项目编号")
    url = fields.CharField(null=False,max_length=10, description="名称")


    class Meta:
        table = "project_table"
        table_description = "项目表"
        ordering = ["-created_time"]
