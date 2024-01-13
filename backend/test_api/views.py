#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from test_api.model import ProjectTable
from test_api.response_code import TestResponseCode


class TestObject(object):
    @staticmethod
    async def create_data(param_data):
        select_result=ProjectTable.filter(pno=param_data.get("pno"),deleted="0")
        if await select_result.exists():return TestResponseCode.CreateError
        await ProjectTable.create(**param_data)
        return TestResponseCode.SUCCESS

    @staticmethod
    async def query_list():
        project_list = []
        projectlist=await ProjectTable.filter(deleted="0").all();
        if projectlist:
            for project in projectlist:
                data={
                    "id":project.id,
                    "pno": project.pno,
                    "name": project.name,
                    "address": project.address,
                    "mobile": project.mobile
                }
                project_list.append(data)
        return {"message": "success", "code": 100000, "data": project_list}

    @staticmethod
    async def query_data(param_data):
        project_list = []
        param=param_data.get("pno")
        if param is None or param.strip() == '':
            projectlist=await ProjectTable.filter(deleted="0").all();
            if projectlist:
                for project in projectlist:
                    data={
                            "id":project.id,
                            "pno": project.pno,
                            "name": project.name,
                            "address": project.address,
                            "mobile": project.mobile
                    }
                    project_list.append(data)

            return {"message": "success", "code": 100000, "data": project_list}
        if not param_data.get("pno") is None:
            project_list = []
            projectlist = await ProjectTable.filter(pno=param_data.get("pno"),deleted="0").all();
            for project in projectlist:
                data = {
                    "id": project.id,
                    "pno": project.pno,
                    "name": project.name,
                    "address": project.address,
                    "mobile": project.mobile
                }
                project_list.append(data)
            return {"message": "success", "code": 100000, "data": project_list}

    @staticmethod
    async def update_data(param_data):
        select_result = ProjectTable.filter(pno=param_data.get("pno"),deleted="0")
        if not await select_result.exists(): return TestResponseCode.NotfoundError
        await select_result.update(**param_data)
        return TestResponseCode.SUCCESS

    @staticmethod
    async def delete_data(param_data):
        select_result = ProjectTable.filter(pno=param_data.get("pno"),deleted="0")
        if not await select_result.exists(): return TestResponseCode.deleteError
        await select_result.update(deleted=1)
        return TestResponseCode.SUCCESS

