#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import platform
import arrow
from pathlib import Path
from loguru import logger
from tortoise import Tortoise

now = arrow.now()
current_date = now.format('YYYY-MM-DD')
FILE_NAME = f"{current_date}.log"
if platform.system() == "Windows" or platform.system() == "Darwin":
    LOG_FILENAME = os.path.join(Path().resolve(), "logs", FILE_NAME)
else:
    LOG_FILENAME = f"/home/www/logs/{FILE_NAME}"
LOG_LEVEL = "INFO"
logs = logger


async def system_logs(msg=''):
    logger.add(
        LOG_FILENAME,
        format="{time} {level} {message}",
        level=LOG_LEVEL,
        rotation="00:00",  # rotation='500 MB' 日志超出500M自动分割日志文件（{time}.log/rotation='00:00' 定时自动生成）
        retention='30 days',  # 设置日志保留时长
        compression='zip',  # 设置日志压缩格式
    )
    logs.info(f'=== {msg} ===')


async def connect_db():
    connect_conf = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    'host': "localhost",
                    'port': "3306",
                    'user': "root",
                    'password': "admin",
                    'database': "test",
                    'minsize': 1,
                    'maxsize': 5,
                    'charset': 'utf8mb4'
                },
            }
        },
        "timezone": "Asia/Shanghai",
        "apps": {
            "zt_auto_test": {
                "models": [
                    "test_api.model",
                ],
                "default_connection": "default"
            },

        },
    }
    await Tortoise.close_connections()
    await Tortoise.init(connect_conf)
    # await Tortoise.generate_schemas()
