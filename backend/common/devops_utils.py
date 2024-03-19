# -*- coding: utf-8 -*-
import os
import random
import re
import time
import traceback
from asyncio import Semaphore
import asyncio
import httpx
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import json
from json import JSONDecodeError

import asyncio

import requests



class RequestError(Exception):
    def __init__(self, error_info):
        super().__init__(error_info)
        self.error_info = error_info

    def __str__(self):
        return self.error_info


class DevopsLogin(object):
    def __init__(self, username, password):
        self.name = username
        self.password = password
    @property
    def login_devops(self):
        cookie_value = ""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path="C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1045\\chrome-win\\chrome.exe", headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://sso.ztn.cn/v2/cas/login?locale=zh_CN&service=https%3A%2F%2Fpaas.ztn.cn%2Flogin%2F%3Fc_url%3Dhttps%3A%2F%2Fdevops.ztn.cn%2F")
            page.fill("#username", self.name)
            page.fill("#password2", self.password)
            page.click("#fm1 > input.login_in")
            cookies = page.context.cookies()
            for cookie in cookies:
                if cookie['name'] == "bk_token":
                    cookie_value = f"X-DEVOPS-TENANT-ID=ZTN; bk_token={cookie['value']}"

            if not cookie_value:
                raise ValueError("密码错误")
            
            browser.close()
        return cookie_value

class DevopsBaseData(DevopsLogin):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.host = "https://devops.ztn.cn"
        self.divmod_number = 15
        self.cookie = super().login_devops

    def request_data(self, method, url, headers, params=None, json=None, project_code=None, number=5):
        try:
            limits = httpx.Limits(max_connections=200, max_keepalive_connections=150)
            with httpx.AsyncClient(timeout=40, verify=False, limits=limits, follow_redirects=True) as client:
                response = client.request(method=method, url=url, headers=headers, params=params, json=json,
                                                timeout=40)
            if response.status_code == 401:
                if number < 0: raise ValueError("认证失败")
                self.cookie = super().login_devops
                headers = {
                    "Cookie": project_code and f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}" or self.cookie}
                return self.request_data(method, url, headers, params, json, project_code=project_code,
                                               number=number - 1)
            elif response.status_code == 429:
                asyncio.sleep(random.randint(3, 7))
                if number < 0: raise ValueError("请求次数太多")
                return self.request_data(method, url, headers, params, json, project_code=project_code,
                                               number=number - 1)
            return response.json()
        except JSONDecodeError:
            raise ValueError("JSONDecodeError")
        except Exception as E:
            raise ValueError(str(traceback.format_exc()))

    @property
    def select_project(self):
        """
        查询项目列表
        :return:
        """
        url = f"{self.host}/ms/projectmanager/api/user/project/cw/select"
        headers = {"Cookie": self.cookie}
        params = {"showTree": False}
        result = self.request_data(method="GET", url=url, headers=headers, params=params)
        if not (data := result.get("data")): raise ValueError("没有项目数据")
        project_list = [{"project_code": i.get("projectCode"), "project_name": i.get("projectName")} for i in data
                        if i.get("typeId") == "2"]
        return project_list

    def select_case_task(self, project_code):
        """
        查询测试任务
        :param project_code: 项目code
        :return:
        """
        url = f"{self.host}/ms/ctest/api/user/task/page?num=1&size=200"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {"keyword": ""}
        result = self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        records = (result.get("data") or {}).get("records")
        if not records: return []
        return records

    def select_case(self, project_code, case_task_id, base_filter, page=1, page_size=5):
        """
        查询测试用例
        :param project_code: 项目code
        :param case_task_id: 测试任务id
        :param base_filter: 查询参数
        :param page: 查询页数
        :param page_size: 查询个数
        :return:
        """
        url = f"{self.host}/ms/ctest/api/user/case_design/case/query"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {
            "keyword": "",
            "filter": {
                "baseFilter": base_filter,
                "customFilter": []
            },
            "page": page,
            "pageSize": page_size,
            "sortField": "createTime",
            "sortType": "DESC",
            "taskId": case_task_id,
            "group": ""
        }
        result = self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        return result

    def select_stage(self, project_code, case_task_id):
        """
        查询测试阶段数据
        :param project_code: 项目code
        :param case_task_id: 测试任务id
        :return:
        """
        url = f"{self.host}/ms/ctest/api/user/case_exec/round/list/{case_task_id}"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {
            "keyWord": "",
            "filter": {
                "baseFilter": [],
                "customFilter": [],
                "defaultFilter": ""
            },
            "sortField": "round_create_time",
            "sortType": "DESC",
            "taskId": case_task_id
        }
        result = self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        stage_list = result.get("data")
        if not stage_list: return []
        return stage_list

    def select_stage_bug(self, project_code, stage_id):
        """
        查询阶段bug
        stage_id: 阶段id
        """
        url = f"{self.host}/ms/ctest/api/user/case_exec/round/bug/page/{stage_id}/"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        params = {
            "page": 1,
            "pageSize": 200,
        }
        result = self.request_data(method="GET", url=url, headers=headers, params=params)
        return [i.get("id") for i in result.get("data").get("records")]

    def select_run_case(self, project_code, case_task_id, stage_id, base_filter, page=1, page_size=5):
        """
        查询测试用例
        :param project_code: 项目code
        :param case_task_id: 测试任务id
        :param stage_id: 阶段id
        :param base_filter: 查询参数
        :param page: 查询页数
        :param page_size: 查询个数
        :return:
        """
        url = f"{self.host}/ms/ctest/api/user/case_exec/round/detail/case_page/{stage_id}"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {
            "keyword": "",
            "filter": {
                "baseFilter": base_filter,
                "customFilter": [],
                "defaultFilter": ""
            },
            "page": page,
            "pageSize": page_size,
            "sortField": "createTime",
            "sortType": "DESC",
            "taskId": case_task_id,
            "group": "",
            "roundId": stage_id
        }
        return self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)

    def select_review_sheet(self, project_code, page=1):
        """
        查询评审单
        :param project_code: 项目code
        :param page: 查询页数
        :return:
        """
        url = f"{self.host}/ms/platform/api/user/review/sheet/getList"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {
            "name": "",
            "description": "",
            "startDateTime": "",
            "endDateTime": "",
            "projectFlowId": "",
            "firstNode": [],
            "publish": "",
            "fileIds": [],
            "other": False,
            "projectCode": project_code,
            "reviewObject": "",
            "creator": "",
            "reviewUsers": [],
            "timeRange": [
                "",
                ""
            ],
            "status": [],
            "reviewIssueList": [],
            "title": "",
            "listType": "all",
            "sort": "",
            "sortName": "",
            "page": page,
            "size": 100,
            "pending": "",
            "isOperator": False
        }
        result = self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        data_list = []
        for i in result.get("data").get("records"):
            if title_data := re.findall(r"【(.*?)】", i.get("title")):
                data_list.append(title_data[0])
        return {"count": result.get("data").get("count"), "data": data_list}

    def select_iteration_bug_id(self, project_code, display_value="测试缺陷"):
        url = f"{self.host}/ms/vteam/api/user/issue_field_value/{project_code}/option/modelTypeId"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        params = {"all": True, "classify": ""}
        result = self.request_data(method="GET", url=url, headers=headers, project_code=project_code,
                                         params=params)
        data = result.get("data") or []
        return [i.get("value") for i in data if i.get("displayValue") == display_value]

    def select_iteration(self, project_code, iteration_id, display_value="测试缺陷", model_type: int = 1):
        url = f"{self.host}/ms/vteam/api/user/issue/{project_code}/version_iteration/ITERATION/{iteration_id}?remember=true&viewMode=TABLE"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = [{"name": "modelTypeId", "value": self.select_iteration_bug_id(project_code, display_value)}]
        result = self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        data = result.get("data").get("records")
        if model_type == 1:
            return {"bug_num": len(data),
                    "id_value": {i.get("property").get("id").get("value"): i.get("property").get("number").get("value")
                                 for i in data if
                                 i.get("property").get("state").get("displayValue") not in ["已作废", "已暂停",
                                                                                            "已拒绝"]}}
        else:
            return [i.get("property") for i in data]


    def issue_info(self, project_code: str):
        """查询需求信息"""
        url = f"{self.host}/ms/vteam/api/user/issue/{project_code}/table/DEMAND"
        payload=[{"name":"exclude","value":[]}]
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        res = requests.post(url, json=payload, headers=headers)
        result=res.json()
        if not result.get("data"):
            return False
        return result.get("data").get("property")
    
    def teration_info(self, project_code: str):
        """查询迭代信息"""
        url = f"{self.host}/ms/vteam/api/user/issue_sprint/{project_code}/flat?state=ACTIVE,NOT_STARTED"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        res = requests.get(url,  headers=headers)
        result=res.json()
        if not result.get("data"):
            return False
        return result.get("data").get("content")


    def star_project_list(self):
        """查询迭代信息"""
        url = f"{self.host}/projectmanager/api/user/project/cw/selectByType?showTree=false&haveUser=false"
        headers = {"Cookie": f"{self.cookie}"}
        res = requests.get(url,  headers=headers)
        result=res.json()
        star_project_list=[]
        for i in result.get("data"):
            if i.get("star") == True:
                star_project_list.append(i.get("projectCode"))
        return star_project_list

    def teration_info_list(self):
        """查询收藏项目的迭代信息"""
        teration_list = []
        
        project_codes = self.star_project_list()  # 获取star_project_list方法返回的projectCode列表
        for project_code in project_codes:
            teration_info_result = self.teration_info(project_code)  # 调用teration_info方法获取迭代信息
            teration_list.extend(teration_info_result)
        
        # return json.dumps(teration_list,ensure_ascii=False)
        return teration_list


    



if __name__ == '__main__':

    a = DevopsBaseData(username="zt23165", password="czh930419881X")
    # result = asyncio.run(a.issue_info("k98e9d"))
    result=a.teration_info_list()
    print(result)
    # a = DevopsTestCase(username="zt20283", password="Huxin!23", start_date="2023-07-01", end_date="2023-07-31")
    # a = CheckTestCase(username="zt20257", password="900713hb@")
    # a = DevopsGroupData(project_id="t196b9", user_id="zt21255")
    # c = (time.time() * 1000)
    # print(asyncio.run(a.create_issue_data("zt20862", "bead345cef634cc19a8f7501c6d86e37", "dddddd")))
    # print((time.time() * 1000) - c)