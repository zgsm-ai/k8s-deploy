#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 18212
@Date    : 2023/11/07
"""
import logging

from flask import Blueprint, request, Response
from services.ai_ut.ut_service import UTService
from common.helpers.application_context import ApplicationContext
from common.helpers.response_helper import Result
from third_platform.es.chat_messages.ut_test_es_service import ut_case_es_service

logger = logging.getLogger(__name__)
ut_case = Blueprint("ut_case", __name__)


@ut_case.route("/check_ut_button", methods=["GET"])
def check_ut_button():
    """
    接口功能：校验单测使用功能
    ---
    tags:
      - 单元测试
    responses:
      200:
        result: 权限校验结果
    """
    user = ApplicationContext.get_current()
    data = UTService.check_ut_button(user)
    return Result.success(message="获取成功", data=data)


@ut_case.route("/plugin_min_version", methods=["GET"])
def plugin_min_version():
    """
    接口功能：获取单侧插件最小版本
    ---
    tags:
      - 单元测试
    responses:
      200:
        res: 结果
    """
    data = UTService.get_plugin_min_version()
    return Result.success(message="获取成功", data=data)


@ut_case.route("/config", methods=["GET"])
def get_ai_test_config():
    """
    接口功能：获取配置模板接口
    ---
    tags:
      - 单元测试
    responses:
      200:
        model: 模型名称
        language: '支持的语言和测试框架 {c++:{suffix:[.cpp], frame:"gtest"}...}'
        point_template: 测试点模板
        case_template: 用例模板
        req_timeout: 请求超时时间
        req_times: 请求次数
        token_length: '{input_length:1500, all_length:3000}'
        max_point: 最大测试点数
    """
    data = UTService.get_ai_test_config()
    return Result.success(message="获取成功", data=data)


@ut_case.route("/testcases", methods=["GET"])
def generate_testcases():
    """
    接口功能：生成测试用例 或者测试点
    ---
    tags:
      - 单元测试
    responses:
      200:
        model_res: 生成的测试点或者测试用例结果
    """
    # parameters:
    #   parameters: '包含最大新令牌数的字典，例如 {"max_new_tokens": 3000}'
    #   inputs: 包含生成测试用例所需信息的字符串
    #   stre1am: 布尔值，表示是否使用流式API
    #   type: 区分测试点/测试用例
    #   timestamp: 时间戳
    # 请求的参数示例：
    # {
    #     "parameters": {"max_new_tokens": 3000},
    #     "inputs": "<s>[INST] <<SYS>>\n\nPlease help me generate a whole c test..."
    #     "stream": true,
    #     "type": "test_case",
    #     "timestamp": 20231019145399
    # }
    user = ApplicationContext.get_current()
    kw = request.get_json()

    res, data = UTService.generate_testcases(kw, user)
    if not res:
        return Result.fail(message=data)
    if kw.get("stream") is True:
        return Response(data, mimetype="text/plain")
    return Result.success(data=data)

@ut_case.route("/report/case", methods=["POST"])
def upload_ut_data():
    """
    接口功能：上传用例汇总的数据
    ---
    tags:
      - 单元测试
    responses:
      200:
        result: 流
    """
    # parameters:
    #   timestamp: 时间戳，格式为 '%Y%m%d%H%M%S'
    #   duration: 耗时（单位：秒）
    #   test_path: 单元测试路径
    #   file_count: 总文件数
    #   cur_file_count: 当前文件数
    #   cur_method_count: 当前方法数
    #   generated_case_count: 生成的测试用例数
    # 请求的参数示例：
    # {
    #     "timestamp": 20201013142244,
    #     "duration": 2,
    #     "test_path": "/usr3/code",
    #     "file_count": 4,
    #     "cur_file_count": 3,
    #     "cur_method_count": 5,
    #     "generated_case_count": 22
    # }
    user = ApplicationContext.get_current()
    data = request.get_json()
    data["display_name"] = user.display_name if user and user.display_name else ""
    data["username"] = user.username if user and user.username else ""
    ut_case_es_service.insert_code_completion(data)
    return Result.success(message="上报成功")
