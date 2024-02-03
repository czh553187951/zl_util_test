# -*- coding: utf-8 -*-
import os
import random
import re
import time
import traceback
from asyncio import Semaphore

import httpx
import asyncio
from datetime import datetime
from json import JSONDecodeError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By



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
        cloud_options = {
            'platform': 'ANY',
            'browserName': 'chrome',
            'version': '91',
            'recordVideo': True,
            'build': "build_%s" % time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime()),
            'name': 'test_%s' % time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime()),
            'idleTimeout': 300,
            'screenResolution': '1280x720',
            'testFileNameTemplate': '{platform}_{browser}_{testStatus}_{timestamp}',
        }
        options = ChromeOptions()
        options.set_capability('cloud:options', cloud_options)
        with webdriver.Remote('http://10.100.64.34:4444/wd/hub', options=options) as driver:
            driver.get("https://sso.ztn.cn/cas/login?service=https%3A%2F%2Fpaas.ztn.cn%2Flogin%2F%3Fc_url%"
                       "3Dhttps%3A%2F%2Fdevops.ztn.cn%2F&locale=zh_CN")
            driver.find_element(By.ID, "username").send_keys(self.name)
            driver.find_element(By.ID, "password2").send_keys(self.password)
            driver.find_element(By.NAME, "submit").submit()
            cookies = driver.get_cookies()
            for i in cookies:
                if i.get("name") == "bk_token":
                    cookie_value = f"X-DEVOPS-TENANT-ID=ZTN; bk_token={i.get('value')}"
                    break
        if not cookie_value: raise ValueError("密码错误")
        return cookie_value


class DevopsBaseData(DevopsLogin):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.host = "https://devops.ztn.cn"
        self.divmod_number = 15
        self.cookie = super().login_devops

    async def request_data(self, method, url, headers, params=None, json=None, project_code=None, number=5):
        try:
            limits = httpx.Limits(max_connections=200, max_keepalive_connections=150)
            async with httpx.AsyncClient(timeout=40, verify=False, limits=limits, follow_redirects=True) as client:
                response = await client.request(method=method, url=url, headers=headers, params=params, json=json,
                                                timeout=40)
            if response.status_code == 401:
                if number < 0: raise ValueError("认证失败")
                self.cookie = super().login_devops
                headers = {
                    "Cookie": project_code and f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}" or self.cookie}
                return await self.request_data(method, url, headers, params, json, project_code=project_code,
                                               number=number - 1)
            elif response.status_code == 429:
                await asyncio.sleep(random.randint(3, 7))
                logs.warning(f"请求次数太多{number}次")
                if number < 0: raise ValueError("请求次数太多")
                return await self.request_data(method, url, headers, params, json, project_code=project_code,
                                               number=number - 1)
            return response.json()
        except JSONDecodeError:
            logs.warning(f"url: {url}, method: {method}, params: {params}, json: {json}, response: {response.text}")
            raise ValueError("JSONDecodeError")
        except Exception as E:
            logs.warning(f"url: {url}, method: {method}, params: {params}, json: {json}")
            raise ValueError(str(traceback.format_exc()))

    @property
    async def select_project(self):
        """
        查询项目列表
        :return:
        """
        url = f"{self.host}/ms/projectmanager/api/user/project/cw/select"
        headers = {"Cookie": self.cookie}
        params = {"showTree": False}
        result = await self.request_data(method="GET", url=url, headers=headers, params=params)
        if not (data := result.get("data")): raise ValueError("没有项目数据")
        project_list = [{"project_code": i.get("projectCode"), "project_name": i.get("projectName")} for i in data
                        if i.get("typeId") == "2"]
        return project_list

    async def select_case_task(self, project_code):
        """
        查询测试任务
        :param project_code: 项目code
        :return:
        """
        url = f"{self.host}/ms/ctest/api/user/task/page?num=1&size=200"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {"keyword": ""}
        result = await self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        records = (result.get("data") or {}).get("records")
        if not records: return []
        return records

    async def select_case(self, project_code, case_task_id, base_filter, page=1, page_size=5):
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
        result = await self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        return result

    async def select_stage(self, project_code, case_task_id):
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
        result = await self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        stage_list = result.get("data")
        if not stage_list: return []
        return stage_list

    async def select_stage_bug(self, project_code, stage_id):
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
        result = await self.request_data(method="GET", url=url, headers=headers, params=params)
        return [i.get("id") for i in result.get("data").get("records")]

    async def select_run_case(self, project_code, case_task_id, stage_id, base_filter, page=1, page_size=5):
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
        return await self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)

    async def select_review_sheet(self, project_code, page=1):
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
        result = await self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        data_list = []
        for i in result.get("data").get("records"):
            if title_data := re.findall(r"【(.*?)】", i.get("title")):
                data_list.append(title_data[0])
        return {"count": result.get("data").get("count"), "data": data_list}

    async def select_iteration_bug_id(self, project_code, display_value="测试缺陷"):
        url = f"{self.host}/ms/vteam/api/user/issue_field_value/{project_code}/option/modelTypeId"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        params = {"all": True, "classify": ""}
        result = await self.request_data(method="GET", url=url, headers=headers, project_code=project_code,
                                         params=params)
        data = result.get("data") or []
        return [i.get("value") for i in data if i.get("displayValue") == display_value]

    async def select_iteration(self, project_code, iteration_id, display_value="测试缺陷", model_type: int = 1):
        url = f"{self.host}/ms/vteam/api/user/issue/{project_code}/version_iteration/ITERATION/{iteration_id}?remember=true&viewMode=TABLE"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = [{"name": "modelTypeId", "value": await self.select_iteration_bug_id(project_code, display_value)}]
        result = await self.request_data(method="POST", url=url, headers=headers, project_code=project_code, json=json)
        data = result.get("data").get("records")
        if model_type == 1:
            return {"bug_num": len(data),
                    "id_value": {i.get("property").get("id").get("value"): i.get("property").get("number").get("value")
                                 for i in data if
                                 i.get("property").get("state").get("displayValue") not in ["已作废", "已暂停",
                                                                                            "已拒绝"]}}
        else:
            return [i.get("property") for i in data]

    async def issue_log(self, project_code: str, model_id: str) -> list:
        """获取工作项操作日志"""
        url = f"{self.host}/ms/vteam/api/user/issue_log/{project_code}/{model_id}"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        result = await self.request_data(method="GET", url=url, headers=headers, project_code=project_code)
        return result.get("data")

    async def test_order(self, project_code: str, interation_id: str):
        """获取提测单列表"""
        url = f"{self.host}/ms/vteam/api/user/test/{project_code}/all?num=1&size=200"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        json = {"result": [], "createUser": [], "createTime": [], "principal": [], "objId": [interation_id],
                "search": ""}
        result = await self.request_data(method="POST", url=url, headers=headers, json=json,
                                         project_code=project_code)
        return result.get("data").get("content")

    async def issue_demand(self, project_code: str, model_id: str) -> dict or bool:
        """跨项目上级需求"""
        url = f"{self.host}/ms/vteam/api/user/issue_demand/{project_code}/{model_id}"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        result = await self.request_data(method="GET", url=url, headers=headers,
                                         project_code=project_code)
        if not result.get("data"):
            return False
        return result.get("data").get("property")

    async def issue_info(self, project_code: str, model_id: str) -> dict or bool:
        """查询需求信息"""
        url = f"{self.host}/ms/vteam/api/user/issue/{project_code}/{model_id}"
        headers = {"Cookie": f"{self.cookie};X-DEVOPS-PROJECT-ID={project_code}"}
        result = await self.request_data(method="GET", url=url, headers=headers,
                                         project_code=project_code)
        if not result.get("data"):
            return False
        return result.get("data").get("property")


class CheckTestCase(DevopsBaseData):

    async def select_case_task(self, project_code, **kwargs):
        """
        查询测试任务
        :param project_code: 项目code
        :param kwargs: 项目名称
        :return:
        """
        result = await super().select_case_task(project_code)
        return [{"project_name": kwargs.get("project_name"), "title_name": i.get("title"), "case_task_id": i.get("id"),
                 "iteration_id": i.get("testContent").get("content"), "task_principal_name": i.get("principalName"),
                 "task_create_time": i.get("createTime"), "project_code": project_code,
                 "iteration_name": i.get("testContent").get("testContentDesc")} for i in result
                if i.get("stateDesc") != '已完成' and i.get("testContent").get("type") == "ITERATION"]

    async def select_stage(self, project_code, case_task_id, **kwargs):
        """
        查询测试阶段数据
        :param project_code: 项目code
        :param case_task_id: 测试任务id
        :return:
        """
        tag = True
        no_exec, stage_id_list, stage_bug = [], [], []
        result = await super().select_stage(project_code, case_task_id)
        for i in result:
            stage_id_list.append(i.get("id"))
            data_result = i.get("result")
            no_exec_num = data_result.get("noExec").get("total")
            no_exec_num and no_exec.append(i.get("name"))
            if [True for k in (i.get("customField") or []) if k.get("displayValue") == "其他"] and tag:
                tag = False
        stage_result = stage_id_list and await asyncio.gather(*[self.select_stage_bug(project_code, stage_id)
                                                                for stage_id in stage_id_list]) or []
        [stage_bug.extend(i) for i in stage_result]
        iteration_issue_bug = await self.select_iteration(project_code, kwargs.get("iteration_id"))
        issue_bug = iteration_issue_bug.get("id_value")
        diff_bug = list(set(issue_bug).difference(set(stage_bug)))
        return {"no_exec": no_exec, "display_value": tag, "bug_data": [issue_bug.get(i) for i in diff_bug]}

    async def select_case(self, project_code, case_task_id, page=1, **kwargs):
        """
        查询测试用例
        :param project_code: 项目code
        :param case_task_id: 测试任务id
        :param page: 查询页数
        :return:
        """
        step_expected, demand_data, issue_id = [], [], []
        result = await super().select_case(project_code, case_task_id, base_filter=[], page=page, page_size=200)
        records_data = result.get("data").get("page").get("records")
        count = result.get("data").get("page").get("count")
        for i in records_data:
            test_step = i.get("testStep")
            expected_result = i.get("expectedResult")
            demand_id = i.get("demandId")
            if not test_step or not expected_result:
                step_expected.append(i.get("num"))
            if not demand_id and i.get("sourceCode") == "NEW":
                demand_data.append(i.get("num"))
            demand_id and demand_id not in issue_id and issue_id.append(demand_id)
        return {"step_expected": step_expected, "demand_data": demand_data, "count": count, "issue_id": issue_id}

    async def select_review_sheet(self, project_code, page=1):
        """
        查询评审单
        :param project_code: 项目code
        :param page: 查询页数
        :return:
        """
        result = await super().select_review_sheet(project_code, page=page)
        review_number = result.get("count")
        review_list = result.get("data")
        if review_number <= 100:
            return {project_code: review_list}
        divmod_num = divmod(review_number, 100)
        run_number = divmod_num[1] > 0 and divmod_num[0] + 1 or divmod_num[0]
        task_list = [{"project_code": project_code, "page": i + 1} for i in range(1, run_number)]
        for start in range(0, run_number, self.divmod_number):
            end = min(start + self.divmod_number, run_number)
            task_result = await asyncio.gather(*[super().select_review_sheet(**i) for i in task_list[start: end]])
            [review_list.extend(i.get("data")) for i in task_result]
        return {project_code: review_list}

    async def loop_case_task(self, project_code, case_task_id, iteration_id):
        """
        事件循环查询用例
        :param project_code: 项目code
        :param case_task_id: 测试任务id
        :param iteration_id: 迭代id
        :return:
        """
        iteration_issue = await self.select_iteration(project_code, iteration_id, display_value="软件需求")
        issue_list = iteration_issue.get("id_value")
        new_dict = {"project_code": project_code, "case_task_id": case_task_id}
        result = await self.select_case(**new_dict)
        case_number = result.get("count")
        step_expected = result.get("step_expected")
        demand_data = result.get("demand_data")
        issue_id_list = result.get("issue_id")
        if case_number <= 200:
            issue_data = list(set(issue_list).difference(set(issue_id_list)))
            return {"step_expected": step_expected, "demand_data": demand_data, "case_number": case_number,
                    "issue_data": [issue_list.get(i) for i in issue_data]}
        divmod_num = divmod(case_number, 200)
        run_number = divmod_num[1] > 0 and divmod_num[0] + 1 or divmod_num[0]
        task_list = [new_dict | {"page": i + 1} for i in range(1, run_number)]
        for start in range(0, run_number, self.divmod_number):
            end = min(start + self.divmod_number, run_number)
            task_result = await asyncio.gather(*[self.select_case(**i) for i in task_list[start: end]])
            [(step_expected.extend(i.get("step_expected")), demand_data.extend(i.get("demand_data")),
              issue_id_list.extend(i.get("issue_id"))) for i in task_result]
        issue_data = list(set(issue_list).difference(set(issue_id_list)))
        return {"step_expected": step_expected, "demand_data": demand_data,
                "issue_data": [issue_list.get(i) for i in issue_data], "case_number": case_number}

    async def loop_case_data(self, task_dict):
        """
        事件循环查询用例、执行数据、迭代bug数
        :param task_dict: 参数
        :return:
        """
        project_code = task_dict.get("project_code")
        new_data = {"task_name": task_dict.get("title_name"), "project_name": task_dict.get("project_name"),
                    "task_principal_name": task_dict.get("task_principal_name"), "project_code": project_code,
                    "task_create_time": task_dict.get("task_create_time"),
                    "iteration_name": task_dict.get("iteration_name")}
        case_task_id = task_dict.get("case_task_id")
        iteration_id = task_dict.get("iteration_id")
        result = await asyncio.gather(*[self.select_stage(project_code, case_task_id, iteration_id=iteration_id),
                                        self.loop_case_task(project_code, case_task_id, iteration_id)])
        [new_data.update(i) for i in result]
        return new_data

    @property
    async def select_all_task(self):
        task_result_list = []
        review_dict = {}
        project_list = await self.select_project
        run_number = len(project_list)
        for start in range(0, run_number, self.divmod_number):
            end = min(start + self.divmod_number, run_number)
            task_result = await asyncio.gather(*[self.select_case_task(**i) for i in project_list[start: end]])
            [task_result_list.extend(i) for i in task_result]
            review_result = await asyncio.gather(
                *[self.select_review_sheet(i.get("project_code")) for i in project_list[start: end]])
            [review_dict.update(i) for i in review_result]
        return {"task_result_list": task_result_list, "review_dict": review_dict}

    @property
    async def check_all_case(self):
        """
        检查用例数据
        :return:
        """
        data_list = []
        task_list = await self.select_all_task
        task_result_list = task_list.get("task_result_list")
        review_dict = task_list.get("review_dict")
        run_number = len(task_result_list)
        for start in range(0, run_number, self.divmod_number):
            end = min(start + self.divmod_number, run_number)
            result = await asyncio.gather(*[self.loop_case_data(i) for i in task_result_list[start: end]])
            for i in result:
                review_status = i.get("iteration_name") not in review_dict.get(
                    i.get("project_code")) and True or False if i.get("case_number") else False
                if i.get("no_exec") or i.get("display_value") or i.get("bug_data") \
                        or i.get("step_expected") or i.get("demand_data") or i.get("issue_data") or review_status:
                    i |= {"review_status": review_status}
                    data_list.append(i)
        return data_list



if __name__ == "__main__":
    # a = DevopsTestCase(username="zt20283", password="Huxin!23", start_date="2023-07-01", end_date="2023-07-31")
    # a = CheckTestCase(username="zt20257", password="900713hb@")
    # a = DevopsGroupData(project_id="t196b9", user_id="zt21255")
    # c = (time.time() * 1000)
    # print(asyncio.run(a.create_issue_data("zt20862", "bead345cef634cc19a8f7501c6d86e37", "dddddd")))
    # print((time.time() * 1000) - c)
    a = DevOpsIterationData()
    print(asyncio.run(a.async_get_iterations_demand_data()))
