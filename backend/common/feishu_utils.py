# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import tracemalloc
import httpx
from dateutil import parser
import asyncio
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../../')
from backend.settings import FEISHUAPPID, FEISHUAPPSECRET

from backend.common.devops_utils import DevopsBaseData


# sys.path.append(r"总路径也就是例子中all目录的路径")




class FeiShuOpenApi(object):
    def __init__(self):
        self.host = "https://open.feishu.cn/open-apis"
        self.authorization = None
        self.app_token = None

    @staticmethod
    def request_data(method, url, headers, params=None, json=None):
        limits = httpx.Limits(max_connections=200, max_keepalive_connections=150)
        with httpx.Client(timeout=40, verify=False, limits=limits, follow_redirects=True) as client:
            response = client.request(method=method, url=url, headers=headers, params=params, json=json, timeout=40)
            # print(url)
            # print(json)
            # print("这是响应！！！！！！！！！！！！！！！！！！！！！！")
            # print(response.text)
            try:
                result = response.json()
                if result.get("code") != 0:
                    raise ValueError(f"请求错误: {response.status_code}, {result.get('msg')}")
                return result
            except ValueError as E:
                raise ValueError(str(E))
            except Exception as E:
                raise ValueError(f"请求异常: {str(E)}")

    @property
    def tenant_access_token(self):
        url = f"{self.host}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        json = {
            "app_id": FEISHUAPPID,
            "app_secret": FEISHUAPPSECRET
        }
        result = self.request_data(method="POST", url=url, headers=headers, json=json)
        access_token = result.get("tenant_access_token")
        return f"Bearer {access_token}"

    def spaces_node(self, token_node):
        """
        获取知识空间节点信息
        :param token_node: 文档的节点token
        :return:
        """
        url = f"{self.host}/wiki/v2/spaces/get_node"
        headers = {"Authorization": self.authorization, "Content-Type": "application/json; charset=utf-8"}
        params = {
            "token": token_node
        }
        result = self.request_data(method="GET", url=url, headers=headers, params=params)
        obj_token = result.get("data").get("node").get("obj_token")
        return obj_token

    def select_tables(self, table_id):
        """
        多维表格查询记录
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        url = f"{self.host}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        headers = {"Authorization": self.authorization, "Content-Type": "application/json; charset=utf-8"}
        params = {"page_size": 500}
        result = self.request_data(method="GET", url=url, headers=headers, params=params)
        items_data = result.get("data").get("items") or []
        total_data = result.get("data").get("total") or 0
        return {"items_data": items_data, "total_data": total_data}

    def create_tables(self, table_id, records_data):
        """
        多维表格新增记录
        :param table_id: 多维表格数据表的唯一标识符
        :param records_data: 本次请求将要新增的记录列表
        :return:
        """
        url = f"{self.host}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        headers = {"Authorization": self.authorization, "Content-Type": "application/json; charset=utf-8"}
        json = {
            "fields": records_data
        }
        self.request_data(method="POST", url=url, headers=headers, json=json)
        return True

    def batch_create_tables(self, table_id, records_data):
        """
        多维表格批量新增记录
        :param table_id: 多维表格数据表的唯一标识符
        :param records_data: 本次请求将要新增的记录列表
        :return:
        """
        if not records_data: return True
        url = f"{self.host}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/batch_create"
        headers = {"Authorization": self.authorization, "Content-Type": "application/json; charset=utf-8"}
        json = {
            "records": records_data
        }
        self.request_data(method="POST", url=url, headers=headers, json=json)
        return True

    def batch_delete_tables(self, table_id, records_data):
        """
        多维表格批量删除记录
        :param table_id: 多维表格数据表的唯一标识符
        :param records_data: 删除的多条记录id列表
        :return:
        """
        url = f"{self.host}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/batch_delete"
        headers = {"Authorization": self.authorization, "Content-Type": "application/json; charset=utf-8"}
        json = {
            "records": records_data
        }
        self.request_data(method="POST", url=url, headers=headers, json=json)
        return True


    def convert_to_milliseconds(self,timestamp):
        dt = parser.parse(timestamp)
        milliseconds = int(dt.timestamp() * 1000)
        return milliseconds
    
    def convert_to_state(self,state):
        if state == "ACTIVE":
            state_chinese = "开发中"
        elif state == "COMPLETE":
            state_chinese = "已完成"
        elif state == "NOT_STARTED":
            state_chinese = "未开始"
        elif state == "SUSPEND":
            state_chinese = "挂起"
        elif state == "ABORTED":
            state_chinese = "已终止"
        return state_chinese
    
    

class FeiShuBase(FeiShuOpenApi):
    def login_app_token(self, app_token):
        """
        获取认证和多维表格的唯一标识符
        :param app_token: 多维表格中url中id
        :return:
        """
        self.authorization = self.tenant_access_token
        self.app_token = self.spaces_node(app_token)
        return True

    def delete_data(self, table_id):
        """
        查询多维表格及删除数据
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        result = self.select_tables(table_id)
        total_data = result.get("total_data")
        records_data = [i.get("record_id") for i in result.get("items_data")]
        records_data and self.batch_delete_tables(table_id, records_data)
        if total_data > 500:
            return self.delete_data(table_id)
        return True

    def login_delete_create(self, table_app_token, table_id, create_list):
        """
        登录删除
        :param table_app_token: 多维表格中url中id
        :param table_id: 多维表格数据表的唯一标识符
        :param create_list: 批量插入数据
        :return:
        """
        if not create_list: return True
        self.login_app_token(table_app_token)
        self.delete_data(table_id)
        self.batch_create_tables(table_id, create_list)


    
    
class FeiShuTestData(FeiShuBase):
    def __init__(self, table_app_token):
        super().__init__()
        self.table_app_token = table_app_token


    def query_data(self,  table_id):
        """
        查询表数据
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        self.login_app_token(self.table_app_token)
        result = self.select_tables(table_id)
        # return json.dumps(result,ensure_ascii=False)
        return result

        
    def add_data(self, table_id):
        """
        插入表数据
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        self.login_app_token(self.table_app_token)
        devops = DevopsBaseData(username="zt23165", password="czh930419881X")
        check_data = devops.teration_info_list()
        create_list = []
        feishutable = self.query_data(table_id)
        for i in check_data:
            found_match = False  # 布尔变量，用于标记是否找到匹配的迭代名称
            for feishudata in feishutable['items_data']:
                if i.get("title") == feishudata['fields']['迭代名称']['text']:
                    found_match = True
                    break
            else:
                if not found_match:
                    print(i.get("state"))
                    new_dict = {
                        "计划提测时间": self.convert_to_milliseconds(i.get("testStartDate")),
                        "计划转验时间": self.convert_to_milliseconds(i.get("testEndDate")),
                        "迭代名称": {"text": i.get("title"), "link": f"https://devops.ztn.cn/console/vteam/{i.get('projectId')}/iteration/overview?id={i.get('id')}"},
                        "迭代完成时间": self.convert_to_milliseconds(i.get("endDate")),
                        "迭代开始时间": self.convert_to_milliseconds(i.get("startDate")),
                        "迭代状态": self.convert_to_state(i.get("state")),
                    }
                    create_list.append({"fields": new_dict})
                    
        self.batch_create_tables(table_id, create_list)
        return True

if __name__ == "__main__":
    a=FeiShuTestData(table_app_token="G1YXwnVffidPimkG2X4cebtJnfh").add_data(table_id="tbleCErolm5pqcJR")
    # print(json.dumps(a, ensure_ascii=False))
    # print(os.path.dirname(os.path.abspath()))
    # asyncio.run(FeiShuScenarioData().scenario_case_run_time("tblZNYNUtE9Jr2kH"))
    # asyncio.run(FeiShuCaseCheck(table_app_token="UXU7w6zT5i0NTukc6f8cydc6nvg").select_config(table_id="tblgTPzpt16oBypG"))
    # asyncio.run(FeiShuAutoCaseCoverRate(table_app_token="Amu5wE37Oi8tMakOMkScOYlYnqg").create_data(
    #     table_id="tblVShPkL9W6b61b"))
