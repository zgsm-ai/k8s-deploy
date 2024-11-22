#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 刘鹏 z10807
    :更新时间: 2023/4/23 17:12
"""

from flask import Blueprint
from flask import request

from common.helpers.custom_permission import PermissionChecker
from common.helpers.response_helper import Result
from controllers.base import get_request_kwargs, handle_validate
from controllers.completion_helper import completion_main
from services.action.complation_service import V2CompletionService
from services.system.components_map_service import ComponentsMapService

actions = Blueprint('action', __name__)

@actions.route('/completion', methods=['POST'])
@actions.route('/completion/extract_response', methods=['POST'])  # TODO 兼容旧版本路由，后期需要删除
@PermissionChecker.check_plugin_user_permission
def completion():
    """
    补全
    ---
    tags:
      - 补全
    responses:
      200:
        res: 结果
    
    """
    request_data = request.get_json()
    request_data = V2CompletionService.process_params(request_data)  # 处理参数
    request_data["ide"] = request.headers.get('ide', '')
    request_data["ide_version"] = request.headers.get('ide-version', '')
    request_data["ide_real_version"] = request.headers.get('ide-real-version', '')
    request_data["headers"] = request.headers
    return completion_main(request_data)


@actions.route('components_map', methods=['GET'])
def get():
    """
    组件库映射
    查询：get api/v2/components_map
    ---
    tags:
      - 补全
    responses:
      200:
        res: 结果
    
    """
    search_kw = get_request_kwargs()

    query, total = ComponentsMapService.list(**search_kw)
    return Result.success(message='获取成功', data=query, total=total)


@actions.route('components_map', methods=['POST'])
@handle_validate(ComponentsMapService)
def post(fields):
    """
    组件库映射
    新增/更新：post api/v2/components_map
    ---
    tags:
      - 补全
    responses:
      200:
        res: 结果
    """
    kwargs = {
        'team': fields.get('team', ''),
        'defaults': fields
    }
    resp = ComponentsMapService.create_or_update(**kwargs)
    return Result.success(message='提交成功', data=resp)
