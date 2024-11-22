#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/24 15:02
"""
import logging
from pydantic import ValidationError
from flask import Blueprint, request

from common.helpers.response_helper import Result
from services.ai_e2e.manual_case import ManualCase
from services.ai_e2e.ai_e2e_case_task import AiE2ECaseTaskService

logger = logging.getLogger(__name__)
e2e_case_task = Blueprint('e2e_case_task', __name__)


@e2e_case_task.route('/generate', methods=['POST'])
def e2e_case_task_post():
    """
    端到端测试案例生成
    ---
    tags:
      - 端到端测试案例
    responses:
      200:
        result: 结果
    """
    logging.info(f"{request.method} {request.path}")
    kw = request.get_json()
    try:
        manual_case = ManualCase(**kw)
        res = AiE2ECaseTaskService.start_generate_case(manual_case)
        return Result.stream_response(res)
    except ValidationError as e:
        return Result.fail(message=f"参数不满足规范：{e}")


@e2e_case_task.route('/<int:task_id>/accept', methods=['POST'])
def e2e_case_task_accept(task_id: int):
    """
    端到端测试案例被接受
    ---
    tags:
      - 端到端测试案例
    responses:
      200:
        result: 结果
    """
    kw = request.get_json()
    try:
        accept_content = kw.get('accept_content')
        accept_type = kw.get('accept_type')
        if not accept_content or not accept_type:
            return Result.fail(message="参数不满足规范")
        res = AiE2ECaseTaskService.accept(task_id, accept_type, accept_content)
        return Result.success(res)
    except ValidationError as e:
        return Result.fail(message=f"参数不满足规范：{e}")
