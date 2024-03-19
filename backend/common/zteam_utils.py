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


class ZteamLogin(object):
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
            page.goto("https://sso.ztn.cn/cas/login?service=https://zteam.ztn.cn/api/toLogin&locale=zh_CN")
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
    
class ZteamBaseData(ZteamLogin):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.host = "https://zteam.ztn.cn"
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
    def select_bug(self,startTime,endTime):
        """
        查询项目列表
        :return:
        """
        url = f"{self.host}/api/new-report/bug/getData"
        headers = {"Cookie": self.cookie}
        params = {"grain":"month","ratioType":9,"isFilter":True,"startTime":startTime,"endTime":endTime,"headerName":"bug/online","page":{"current":1,"size":1000},"parentRatioType":6}
        result = self.request_data(method="POST", url=url, headers=headers, json=params)
        if not (data := result["data"]["records"]): raise ValueError("没有数据")
        bug_list = [{"bugTitle": i.get("bugTitle"), "bugNumber": i.get("bugNumber"),"workspaceDetail":i.get("workspaceDetail"),} for i in data
                        if i.get("typeId") == "2"]
        return bug_list
    

if __name__ == '__main__':

    a = ZteamBaseData(username="zt23165", password="czh930419881X")
    # result = asyncio.run(a.issue_info("k98e9d"))
    result=a.teration_info_list()
    print(result)