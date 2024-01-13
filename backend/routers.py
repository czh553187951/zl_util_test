#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from test_api.urls import router as test_router


RESPONSES = {404: {"description": "Not found"}}

ALLRouter = [
    {"router": test_router, "prefix": "/test_api", "tags": ['测试'], "responses": RESPONSES}
]
