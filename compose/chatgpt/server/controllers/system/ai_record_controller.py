#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/20 14:55
"""
from flask import Blueprint

from common.helpers.response_helper import Result
from controllers.base import handle_paginate, get_request_kwargs, handle_validate
from services.system.ai_record_service import AIRecordActionService

ai_record = Blueprint('ai_record', __name__)


@ai_record.route('actions', methods=['GET'])
@handle_paginate
def get(page, per):
    """
    动作记录
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    # prompt: 模糊查询
    # display_name: 模糊查询
    # start_time/end_time：范围查询
    search_kw = get_request_kwargs()

    # 默认时间倒序
    if 'ordering' not in search_kw:
        search_kw['ordering'] = '-created_at'
    query, total = AIRecordActionService.list(page=page, per=per, **search_kw)
    return Result.success(message='获取成功', data=query, total=total)


@ai_record.route("/actions", methods=['post'])
@handle_validate(AIRecordActionService)
def post(fields):
    """
    根据 response_id 更新记录数据
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    resp = AIRecordActionService.update_by_response_id(**fields)
    return Result.success(message='更新成功', data=resp)


@ai_record.route('/departments', methods=['GET'])
def get_departments():
    """
    部门列表
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    query = AIRecordActionService.dept_list()
    return Result.success(message='获取成功', data=query)
