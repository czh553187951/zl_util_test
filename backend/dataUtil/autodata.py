import requests
import json

class AutoTestLogin(object):
    def __init__(self, username, password):
        self.name = username
        self.password = password

    @property
    def get_auto_token(self):
        header = {"Content-Type": "application/json"}
        payload = {"username": self.name, "password": self.password}
        url = 'http://autotest.sit.yunexpress.com/prod-api/login'
        res = requests.post(url, json=payload, headers=header)
        return 'Bearer ' + res.json()['token']





a = AutoTestLogin('zt23165', 'zt@123456789')
token = a.get_auto_token
print(token)