# -*- coding: utf-8 -*-
import time
import httpx
import asyncio
import traceback
from datetime import datetime




class FeiShuPrompt(object):
    base_content = "纵腾自动化测试\n【通知名称】: {task_name}\n【消息类型】: {task_type}\n【通知时间】: {data_time}\n"
    case_content = "【项目名称】: {project_name}\n【执行人】: {user_name}\n【用例总数】: {case_num}\n【成功总数】: {pass_num}" \
                   "\n【跳过总数】: {skipped_num}\n【失败总数】: {fail_nam}\n【成功率】: {pass_percentage}%\n【报告链接】: {report_url}"

    def __init__(self, task_name: str, task_type: str, feishu_user_code: str, send_type: str = 1):
        self.task_name = task_name
        self.task_type = task_type
        self.feishu_user_code = feishu_user_code
        self.send_type = send_type

    async def fei_shu_send(self, all_content):
        feishu_user_code = self.feishu_user_code.split(",")
        for i in feishu_user_code:
            if self.send_type == "1":
                await SystemBasisData().send_data(i, all_content)
            else:
                await SystemBasisData().group_send_data(i, all_content)

    async def fei_shu_send_data(self, batch_code):
        task_type = self.task_type == "1" and "用例套件" or self.task_type == "2" and "脚本套件"
        data_time = time.strftime("%Y-%m-%d %H:%M:%S")
        all_content = self.base_content.format(task_name=self.task_name, task_type=task_type, data_time=data_time)
        select_object = await CaseRunResult.filter(deleted=0, batch_code=batch_code).first()
        if not select_object:
            all_content += "结果: 任务异常，无报告"
            await self.fei_shu_send(all_content)
            return False
        case_num = select_object.case_number
        skipped_num = select_object.skipped_case_number
        fail_nam = select_object.fail_case_number
        pass_num = case_num - skipped_num - fail_nam
        pass_percentage = case_num and round(pass_num * 100/(case_num - skipped_num), 5) or 0
        user_data = await SysUser.filter(user_name=select_object.executor, deleted=0).first()
        user_name = user_data and user_data.real_name or ""
        project_data = await Project.filter(project_code=select_object.project_code, deleted=0).first()
        project_name = project_data and project_data.project_name or ""
        all_content += self.case_content.format(project_name=project_name, user_name=user_name, case_num=case_num,
                                                pass_num=pass_num, skipped_num=0, fail_nam=fail_nam,
                                                pass_percentage=pass_percentage, report_url=select_object.report_path)

        await self.fei_shu_send(all_content)


class FeiShuOpenApi(object):
    def __init__(self):
        self.host = "https://open.feishu.cn/open-apis"
        self.authorization = None
        self.app_token = None

    @staticmethod
    async def request_data(method, url, headers, params=None, json=None):
        limits = httpx.Limits(max_connections=200, max_keepalive_connections=150)
        async with httpx.AsyncClient(timeout=40, verify=False, limits=limits, follow_redirects=True) as client:
            response = await client.request(method=method, url=url, headers=headers, params=params, json=json, timeout=40)
        try:
            result = response.json()
            if result.get("code") != 0:
                raise ValueError(f"请求错误: {response.status_code}, {result.get('msg')}")
            return result
        except ValueError as E:
            raise ValueError(f"{str(E)}")
        except Exception as E:
            raise ValueError(f"请求异常: {str(E)}")

    @property
    async def tenant_access_token(self):
        url = f"{self.host}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        json = {
            "app_id": FEISHUAPPID,
            "app_secret": FEISHUAPPSECRET
        }
        result = await self.request_data(method="POST", url=url, headers=headers, json=json)
        access_token = result.get("tenant_access_token")
        return f"Bearer {access_token}"

    async def spaces_node(self, token_node):
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
        result = await self.request_data(method="GET", url=url, headers=headers, params=params)
        obj_token = result.get("data").get("node").get("obj_token")
        return obj_token

    async def select_tables(self, table_id):
        """
        多维表格查询记录
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        url = f"{self.host}/bitable/v1/apps/{self.app_token}/tables/{table_id}/records"
        headers = {"Authorization": self.authorization, "Content-Type": "application/json; charset=utf-8"}
        params = {"page_size": 500}
        result = await self.request_data(method="GET", url=url, headers=headers, params=params)
        items_data = result.get("data").get("items") or []
        total_data = result.get("data").get("total") or 0
        return {"items_data": items_data, "total_data": total_data}

    async def create_tables(self, table_id, records_data):
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
        await self.request_data(method="POST", url=url, headers=headers, json=json)
        return True

    async def batch_create_tables(self, table_id, records_data):
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
        await self.request_data(method="POST", url=url, headers=headers, json=json)
        return True

    async def batch_delete_tables(self, table_id, records_data):
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
        await self.request_data(method="POST", url=url, headers=headers, json=json)
        return True


class FeiShuBase(FeiShuOpenApi):
    async def login_app_token(self, app_token):
        """
        获取认证和多维表格的唯一标识符
        :param app_token: 多维表格中url中id
        :return:
        """
        self.authorization = await self.tenant_access_token
        self.app_token = await self.spaces_node(app_token)
        return True

    async def delete_data(self, table_id):
        """
        查询多维表格及删除数据
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        result = await self.select_tables(table_id)
        total_data = result.get("total_data")
        records_data = [i.get("record_id") for i in result.get("items_data")]
        records_data and await self.batch_delete_tables(table_id, records_data)
        if total_data > 500:
            return await self.delete_data(table_id)
        return True

    async def login_delete_create(self, table_app_token, table_id, create_list):
        """
        登录删除
        :param table_app_token: 多维表格中url中id
        :param table_id: 多维表格数据表的唯一标识符
        :param create_list: 批量插入数据
        :return:
        """
        if not create_list: return True
        await self.login_app_token(table_app_token)
        await self.delete_data(table_id)
        await self.batch_create_tables(table_id, create_list)


class FeiShuCaseCheck(FeiShuBase):
    def __init__(self, table_app_token):
        super().__init__()
        self.table_app_token = table_app_token

    async def create_data(self, table_id, username, password):
        try:
            create_list = []
            check_data = await CheckTestCase(username=username, password=password).check_all_case
            logs.warning(f"用户{username}: 检查异常数据{len(check_data)}")
            for i in check_data:
                new_dict = {
                    "项目名称": i.get("project_name"),
                    "测试任务名称": i.get("task_name"),
                    "用例未关联需求": ",".join(i.get("demand_data")),
                    "用例不符合规范（步骤/预期）": ",".join(i.get("step_expected")),
                    "轮次存在用例未执行": ",".join(i.get("no_exec")),
                    "轮次未包含【其它】": i.get("display_value") and "是" or "否",
                    "缺陷未关联用例": ",".join(i.get("bug_data")),
                    "需求未关联用例": ",".join(i.get("issue_data")),
                    "迭代未关联评审单": i.get("review_status") and "是" or "否",
                    "测试任务创建时间": i.get("task_create_time") and datetime.fromisoformat(i.get("task_create_time")).timestamp() * 1000 or 0,
                    "测试任务负责人": ",".join(i.get("task_principal_name")),
                }
                create_list.append({"fields": new_dict})
            await self.delete_data(table_id)
            await self.batch_create_tables(table_id, create_list)
            url_str = f"https://ztn.feishu.cn/wiki/{self.table_app_token}?table={table_id}"
            content = f"devops用例检查\n【异常数量】: {len(create_list)}\n【链接】: {url_str}"
            create_list and await SystemBasisData().send_data(username, content)
        except Exception as E:
            logs.error(f"devops同步异常: {str(traceback.format_exc())}")
        return True

    async def select_config(self,  table_id):
        """
        查询配置表数据
        :param table_id: 多维表格数据表的唯一标识符
        :return:
        """
        await self.login_app_token(self.table_app_token)
        result = await self.select_tables(table_id)
        for i in result.get("items_data"):
            usr_id = i.get("fields").get("usr_id").lower()
            password = i.get("fields").get("pwd")
            table_id = i.get("fields").get("table_id")
            status = i.get("fields").get("status")
            if usr_id and password and table_id and status == "1":
                await self.create_data(**{"username": usr_id, "password": password, "table_id": table_id})
                await asyncio.sleep(10)
        return True


class FeiShuAutoCaseCoverRate(FeiShuBase):
    def __init__(self, table_app_token):
        super().__init__()
        self.table_app_token = table_app_token

    async def create_data(self, table_id):
        create_list = []
        await db_init()
        auto_object = AutoCreateCase(role="3")
        system_result = await auto_object.system_data
        project_result = await asyncio.gather(*[auto_object.project_data(system_code=i.get("project_code"))
                                                for i in system_result])
        for i, k in zip(system_result, project_result):
            for j in k:
                new_dict = {
                    "小队": i.get("project_name"),
                    "系统": j.get("project_name"),
                    "达标接口数": j.get("conform_api"),
                    "未标接口数(5.1前)": j.get("unfinished_api"),
                    "5.1后未达标用例接口数": j.get("part_no_case_api")
                }
                create_list.append({"fields": new_dict})
        await self.login_delete_create(self.table_app_token, table_id, create_list)
        return True


class FeiShuScenarioData(FeiShuBase):

    async def scenario_case_run_time(self, table_id):
        create_list = []
        await db_init()
        date_result = await RunRecordsService(start_date="2023-08-01", end_date="2023-08-31").run_case_time
        for i in date_result:
            new_dict = {
                "场景id": int(i.get("case_code")),
                "场景名称": i.get("scenario_case_name"),
                "创建人": i.get("real_name"),
                "平均执行时间(秒)": int(i.get("avg_data")),
                "成功率": float(i.get("success_rate")),
                "运行次数": i.get("run_number"),
                "最后执行时间": i.get("latest_time")
            }
            create_list.append({"fields": new_dict})
        await self.login_delete_create("wikcnQBauab5VB5tlD0b6b9JBkg", table_id, create_list)
        return True

    async def production_case_run_time(self, records_data):
        """
        造数用例运行数量及时间
        :param records_data: 数据
        :return:
        """
        await self.login_app_token("Gy1EwH5L5iaMBHkrBsVcUhvdnfe")
        new_data = {
            "造数ID": records_data.get("case_id"),
            "造数名称": records_data.get("case_name"),
            "造数数量": records_data.get("run_number"),
            "造数时长": records_data.get("use_time"),
            "造数步骤数": records_data.get("step_number"),
            "创建人": records_data.get("created_by"),
        }
        await self.create_tables("tbli9lzensOUe6FK", new_data)


class FeiShuTimeTaskData(FeiShuBase):
    async def time_task_run_data(self, records_data):
        """
        套件定时任务执行数据
        :param records_data: 数据
        :return:
        """
        await self.login_app_token("HFxhwpP4yixBprkdPaZcImPjn5d")
        for i in records_data:
            new_data = {
                "系统名称": i.get("system_data"),
                "项目名称": i.get("project_name"),
                "套件ID": str(i.get("set_id")),
                "用例总数": i.get("case_number"),
                "失败用例总数": i.get("fail_num"),
                "跳过用例数": i.get("skipped_num") or 0,
                "类型": i.get("set_type")
            }
            await self.create_tables("tblLHT6DTBkpmRoM", new_data)
        return True


if __name__ == "__main__":
    asyncio.run(FeiShuCaseCheck(table_app_token="UXU7w6zT5i0NTukc6f8cydc6nvg").select_config(table_id="tblgTPzpt16oBypG"))
    # asyncio.run(FeiShuScenarioData().scenario_case_run_time("tblZNYNUtE9Jr2kH"))
    # asyncio.run(FeiShuCaseCheck(table_app_token="UXU7w6zT5i0NTukc6f8cydc6nvg").select_config(table_id="tblgTPzpt16oBypG"))
    # asyncio.run(FeiShuAutoCaseCoverRate(table_app_token="Amu5wE37Oi8tMakOMkScOYlYnqg").create_data(
    #     table_id="tblVShPkL9W6b61b"))
