from collections import Counter
from datetime import datetime, timedelta
import json
import requests

env="uat"           #环境
flowCode="CNETCIS796105553717116929"        #当前环境下的主单号
#需要判断的字段规则，用于生成断言的字段
eq_rules=[
     "taskStatus",
     "length",
     "allocatingOs",
]

#存在不在当前区域任务的规则，如果不需要可以清空数组
notin_rules=[
    "T000000044",
    "T000000045"
]

url="http://gateway."+env+".yunexpress.com/gw/opd-ofp-portal"

class Request:


    #获取不同环境的token
    def get_ofp_token(self):
            header = {"Content-Type": "application/json"}
            payload = {"$AuthenticationType": "PasswordCredential", "Username": "zt23165", "Password": "czh19930419881X",
                    "AuthenticationSource": "SYS"}
            url = 'https://authentication.yunexpress.com/Authentication/Authenticate?resultType='
            res = requests.post(url, json=payload, headers=header)
            return 'Nebula token:' + res.json()['token']

    #查询对应的流程数据
    def get_response_data(self):
            Authorization=self.get_ofp_token()
            header = {"Content-Type": "application/json","Authorization":Authorization}
            body={"startIndex":0,"count":1000,"beginCreateTime":self.get_date_in_utc(30),"flowCode":flowCode,"endCreateTime":self.get_date_in_utc()}
            url2 = url+"/fulfillExcTaskInstance/list"
            res2 = requests.post(url2, headers=header, json=body)
            return json.loads(res2.text)



    def get_date_in_utc(self,days_ago=0):
        # 获取当前UTC时间
        utc_now = datetime.utcnow()

        # 根据输入的天数计算指定日期
        target_date = utc_now - timedelta(days=days_ago)

        # 转换为ISO 8601格式并以Z结尾代表UTC时区，不包含时区偏移信息
        date_in_utc_iso = target_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        return date_in_utc_iso

class TaskResponse:
    def __init__(self, taskInstanceDtos, totalCount):
        self.taskInstanceDtos = taskInstanceDtos
        self.totalCount = totalCount


class TaskInstanceDto:
    def __init__(
        self,
        taskCode,
        flowCode,
        engineTaskCode,
        taskDefCode,
        bizCode,
        allocatingType,
        allocatingTypeName,
        allocatingOs,
        allocatingArea,
        taskTypeCode,
        taskTypeCodeName,
        taskStatus,
        taskStatusName,
        taskInnerStatus,
        resendTaskResultStatus,
        processBy,
        processPosition,
        processPositionName,
        processPositionType,
        callBackResult,
        callBackRemark,
        callBackTime,
        callBackDocument,
        receiveCallBackTime,
        callBackDataJson,
        taskConductorStatus,
        createBy,
        createTime,
        updateBy,
        updateTime,
    ):
        self.taskCode = taskCode
        self.flowCode = flowCode
        self.engineTaskCode = engineTaskCode
        self.taskDefCode = taskDefCode
        self.bizCode = bizCode
        self.allocatingType = allocatingType
        self.allocatingTypeName = allocatingTypeName
        self.allocatingOs = allocatingOs
        self.allocatingArea = allocatingArea
        self.taskTypeCode = taskTypeCode
        self.taskTypeCodeName = taskTypeCodeName
        self.taskStatus = taskStatus
        self.taskStatusName = taskStatusName
        self.taskInnerStatus = taskInnerStatus
        self.resendTaskResultStatus = resendTaskResultStatus
        self.processBy = processBy
        self.processPosition = processPosition
        self.processPositionName = processPositionName
        self.processPositionType = processPositionType
        self.callBackResult = callBackResult
        self.callBackRemark = callBackRemark
        self.callBackTime = callBackTime
        self.callBackDocument = callBackDocument
        self.receiveCallBackTime = receiveCallBackTime
        self.callBackDataJson = callBackDataJson
        self.taskConductorStatus = taskConductorStatus
        self.createBy = createBy
        self.createTime = createTime
        self.updateBy = updateBy
        self.updateTime = updateTime



# 将响应转换为模型对象
response_data =Request().get_response_data()

# 创建模型对象
task_instances = []
for task_data in response_data["taskInstanceDtos"]:
    task_instance = TaskInstanceDto(
        taskCode=task_data["taskCode"],
        flowCode=task_data["flowCode"],
        engineTaskCode=task_data["engineTaskCode"],
        taskDefCode=task_data["taskDefCode"],
        bizCode=task_data["bizCode"],
        allocatingType=task_data["allocatingType"],
        allocatingTypeName=task_data["allocatingTypeName"],
        allocatingOs=task_data["allocatingOs"],
        allocatingArea=task_data["allocatingArea"],
        taskTypeCode=task_data["taskTypeCode"],
        taskTypeCodeName=task_data["taskTypeCodeName"],
        taskStatus=task_data["taskStatus"],
        taskStatusName=task_data["taskStatusName"],
        taskInnerStatus=task_data["taskInnerStatus"],
        resendTaskResultStatus=task_data["resendTaskResultStatus"],
        processBy=task_data["processBy"],
        processPosition=task_data["processPosition"],
        processPositionName=task_data["processPositionName"],
        processPositionType=task_data["processPositionType"],
        callBackResult=task_data["callBackResult"],
        callBackRemark=task_data["callBackRemark"],
        callBackTime=task_data["callBackTime"],
        callBackDocument=task_data["callBackDocument"],
        receiveCallBackTime=task_data["receiveCallBackTime"],
        callBackDataJson=task_data["callBackDataJson"],
        taskConductorStatus=task_data["taskConductorStatus"],
        createBy=task_data["createBy"],
        createTime=task_data["createTime"],
        updateBy=task_data["updateBy"],
        updateTime=task_data["updateTime"],
    )
    task_instances.append(task_instance)

task_response = TaskResponse(
    taskInstanceDtos=task_instances,
    totalCount=response_data["totalCount"]
)   

def get_notin_env(env):
    if env == "sit":
        return "SIT"
    elif env == "uat":
        return "UAT"
    else:
        return "ALL"
def get_notin_value(env):
    if env == "sit":
        return "US"
    elif env == "uat":
        return "CN"
    else:
        return ""


def generate_jms_path_expressions(task_response):
    expressions = []
    
    for rule in eq_rules:
        if rule == "length":
            task_type_counts = Counter(task_instance.taskTypeCode for task_instance in task_response.taskInstanceDtos)
            for task_type_code, count in task_type_counts.items():
                expression = {
                    "field_env": "ALL",
                    "params_type": "assert",
                    "field_key": "length(taskInstanceDtos[?taskTypeCode=='{}'])".format(task_type_code),
                    "field_value": count,
                    "and_or": "and",
                    "asserts_type": "eq",
                    "checked": True
                }
                expressions.append(expression)
        else:
            task_type_counts = Counter(task_instance.taskTypeCode for task_instance in task_response.taskInstanceDtos)
            for task_instance in task_response.taskInstanceDtos:
                if rule == "taskStatus" and task_instance.allocatingArea == "EU":
                    continue  
                elif rule == "taskStatus" and getattr(task_instance, rule) == "SEND_FAIL":
                    continue  
                elif task_type_counts[task_instance.taskTypeCode] == 3 and task_instance.taskTypeCode not in notin_rules:
                    if rule == "taskStatus" and task_instance.allocatingArea == "EU":
                        continue 
                    else:
                        expression = {
                            "field_env": "ALL",
                            "params_type": "assert",
                            "field_key": "taskInstanceDtos[?taskTypeCode=='{}'&&allocatingArea=='{}'&&allocatingOs=='{}'].{}|[0]".format(
                                task_instance.taskTypeCode, task_instance.allocatingArea,task_instance.allocatingOs, rule),
                            "field_value": getattr(task_instance, rule),
                            "and_or": "and",
                            "asserts_type": "eq",
                            "checked": True
                        }
                        expressions.append(expression)
                elif task_instance.taskTypeCode not in notin_rules:
                    expression = {
                        "field_env": "ALL",
                        "params_type": "assert",
                        "field_key": "jmespath@taskInstanceDtos[?taskTypeCode=='{}'&&allocatingArea=='${{gl_env_OFP}}'&&allocatingOs=='{}'].{}|[0]".format(
                            task_instance.taskTypeCode,task_instance.allocatingOs, rule),
                        "field_value": getattr(task_instance, rule),
                        "and_or": "and",
                        "asserts_type": "eq",
                        "checked": True
                    }
                    expressions.append(expression)
    
    for rule1 in notin_rules:
        if any(task_instance.taskTypeCode == rule1 for task_instance in task_response.taskInstanceDtos):
            expression = {
                "field_env": get_notin_env(env),
                "params_type": "assert",
                "field_key": "taskInstanceDtos[?taskTypeCode== '{}'].allocatingArea|[0]".format(rule1),
                "field_value": get_notin_value(env),
                "and_or": "and",
                "asserts_type": "not_in",
                "checked": True
            }
            expressions.append(expression)
    
    json_result = json.dumps(expressions, indent=4)  # 转换为 JSON 字符串
    
    output_file="output.json"
    with open(output_file, 'w') as file:
        file.write(json_result)
    
    print(f"Expressions written to file: {output_file}")
    return expressions
expressions = generate_jms_path_expressions(task_response)
print(expressions)

