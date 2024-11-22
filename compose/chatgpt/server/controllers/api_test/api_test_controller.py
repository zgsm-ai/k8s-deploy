#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/24 10:50
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : api_test_controller.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : API测试生成相关接口定义文档

import logging

from flask import Blueprint, request, Response

from common.helpers.application_context import ApplicationContext
from services.api_test.api_test_case_service import ApiTestCaseService
from services.api_test.api_test_service import ApiTestService
from common.helpers.response_helper import Result
from common.validation.base_validation import ApiTestRequestModel, ApiTestCaseTaskRequestModel, VersionRequestModel
from pydantic import ValidationError
from common.constant import ApiTestCaseConstant

logger = logging.getLogger(__name__)
api_test = Blueprint("api_test", __name__)


@api_test.route("/is_latest_version", methods=["POST"])
def is_latest_version():
    """
        接口功能：判断eolinker端插件是否为最新版本
        request body:
        {
            current_version: 插件端本地记录的版本号
        }
        response body:
        {
        "message": "是最新版本/不是最新版本",
        "data":{
            is_latest: True/False
        },
        "success": True/False
        }
    ---
    tags:
      - 测试用例
    responses:
      200:
        res: 结果
    """
    logging.info(f"{request.method} {request.path}")
    kw = request.get_json()
    try:
        request_model = VersionRequestModel(**kw)
    except ValidationError as e:
        return Result.fail(message=f"参数不满足规范：{e}")

    is_latest = ApiTestService.is_latest_version(request_model.current_version)
    return Result.success(data={"is_latest": is_latest})


@api_test.route("/testcases", methods=["POST"])
def generate_testcases():
    """
    接口功能：生成测试点或者测试用例
    request body:
    {
        api_info:{}, # 接口详细信息，具体参考eolinker平台/v2/api_studio/management/api/api_info接口的返回信息
        api_platform: "eolinker", # 平台信息，eolinker、奇林(kylin)和swagger
        testcase_type: "pytest", # 测试用例类型，pytest、eolinker和奇林
        stream: True, # 是否开启流式
        action: "",  # 动作，可选: generateApiTestPoint、generateApiTestSet
        test_points: [""]  # 测试点列表，generateApiTestSet 时需要
    }
    response body:
    流式返回text/plain格式，内容为
    test_point+testcase
    非流式返回json：
    {
    "message": "",
    "data":{
        id: "xxxx", # 响应id
        testpoint: "", # 测试点
        testcase: "" # 测试用例
    },
    "success": True/False
    }
    ---
    tags:
      - 测试用例
    responses:
      200:
        res: 结果
    """
    kw = request.get_json()
    authorization = request.headers.get("Authorization", None)
    kw['authorization'] = authorization
    try:
        request_model = ApiTestRequestModel(**kw)
    except ValidationError as e:
        return Result.fail(message=f"参数不满足规范：{e}")
    user = ApplicationContext.get_current()
    display_name = user.display_name if user and user.display_name else ""
    data = ApiTestService.generate_testcases(request_model,
                                             origin=request.headers.get('Origin'),
                                             display_name=display_name)
    if not data:
        return Result.fail(message="生成测试点失败")
    if kw.get("stream") is True:
        return Response(data, mimetype="text/plain")
    return Result.success(data=data)


@api_test.route("/api_test_case_task", methods=["POST"])
def api_test_case_task():
    """
    接口功能：生成测试用例并 创建eolink自动化测试用例
    spaceKey   工作空间key
    projectHashKey   项目哈希key
    ---
    tags:
      - 测试用例
    responses:
      200:
        res: 结果
    """

    kw = request.get_json()
    authorization = request.headers.get("Authorization", None)
    kw['authorization'] = authorization

    try:
        req_model = ApiTestCaseTaskRequestModel(**kw)
    except ValidationError as e:
        return Result.fail(message=f"参数不满足规范：{e}")
    user = ApplicationContext.get_current()
    display_name = user.display_name if user and user.display_name else ""

    data = ApiTestCaseService.api_test_case_task(req_model,
                                                 display_name=display_name,
                                                 origin=request.headers.get('Origin'))
    if not data:
        return Result.fail(message="请求生成自动化测试用例任务失败")
    if data.get("status") == "fail":
        return Result.fail(message=data.get("msg"))
    return Result.success(data=data)


@api_test.route("/stop_api_test_case_task", methods=["POST"])
def stop_api_test_case_task():
    """
    接口功能：中止生成测试用例任务
    ---
    tags:
      - 测试用例
    responses:
      200:
        res: 结果
    """
    user = ApplicationContext.get_current()
    kw = request.args.to_dict()
    test_case_stage = kw.get("test_case_stage", ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST)

    display_name = user.display_name if user and user.display_name else ""
    data = ApiTestCaseService.stop_api_test_case_task(display_name, test_case_stage)
    if not data:
        return Result.fail(message="中止任务失败")
    return Result.success(data=data)


@api_test.route("/get_run_task_by_user", methods=["GET", "POST"])
def get_detail_task_by_user():
    """
    接口功能：根据用户查询当前任务详情
    ---
    tags:
      - 测试用例
    responses:
      200:
        res: 结果
    """
    user = ApplicationContext.get_current()
    display_name = user.display_name if user and user.display_name else ""

    kw = request.args.to_dict()
    task_id = kw.get("task_id")
    test_case_stage = kw.get("test_case_stage", ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST)

    data = ApiTestCaseService.get_run_detail_task_by_user(display_name, task_id, test_case_stage)
    return Result.success(data=data)


@api_test.route("/parse_testcase_latest_update_time", methods=["POST"])
def parse_testcase_latest_update_time():
    """
    接口功能：解析测试用例列表中更新时间最新的时间点
    body:
        api_relation_test_case_list :  [
            {
            caseName: string;
            caseID: number;
            projectHashKey?: string;
            isSelected: boolean;
            }
        ]
        space_id: string;
    ---
    tags:
      - 测试用例
    responses:
      200:
        res: 结果
    """
    api_relation_test_case_list = request.get_json().get("api_relation_test_case_list")
    space_id = request.get_json().get("space_id")
    origin = request.headers.get("Origin")
    authorization = request.headers.get("Authorization")
    data = ApiTestCaseService.parse_testcase_latest_update_time(api_relation_test_case_list, space_id, origin,
                                                                authorization)
    if not data:
        return Result.fail(message="解析用例最后更新时间失败")
    return Result.success(data=data)
