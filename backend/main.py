#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

from settings import system_logs, logs, connect_db
from routers import ALLRouter


class Main(object):
    @staticmethod
    async def start_event():
        await connect_db()
        await system_logs('服务启动')

    @staticmethod
    async def shutdown_event():
        await system_logs('服务停止')

    @classmethod
    def create_app(cls):
        app = FastAPI(debug=False, title='test', description='test', version='v1.0.0', docs_url='/docs', redoc_url='/redocs',
                      on_startup=[cls.start_event],   on_shutdown=[cls.shutdown_event])

        origins = ["*"]
        app.add_middleware(  # 在应用上添加中间件
            CORSMiddleware,  # 内置中间件类
            allow_origins=origins,  # 参数1 可用域列表
            allow_credentials=True,  # 参数2 允许cookie， 是
            allow_methods=["*"],  # 参数3 允许的方法， 全部
            allow_headers=["*"],  # 参数4 允许的Header，全部
        )

        [app.include_router(**router) for router in ALLRouter]

        @app.exception_handler(RequestValidationError)
        async def request_error(request: Request, exc):
            """
            处理异常
            :param request:
            :param exc:
            :return:
            """
            content = {"code": 300000, "data": "", "message": jsonable_encoder(exc.errors())}
            return JSONResponse(content=content, status_code=200)

        @app.middleware("http")
        async def middleware_request(request: Request, call_next):
            """
            中间件
            :param request:
            :param call_next:
            :return:
            """
            start_time = time.time()
            response = None
            try:

                response = await call_next(request)
            except Exception as E:
                logs.info(f"异常: {str(E)}")
                response = JSONResponse(content={"message": "异常", "code": 100000, "data": str(E)}, status_code=200)
            finally:
                process_time = time.time() - start_time
                logs.info(f"请求时间: {process_time}")
                return response
        return app




