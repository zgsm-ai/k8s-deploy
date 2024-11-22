#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/20 9:24
"""

from flask import Blueprint

from common.helpers.custom_permission import PermissionChecker
from common.helpers.response_helper import Result
from controllers.base import handle_validate, handle_paginate, get_request_kwargs
from services.system.open_api_applications_service import OpenApiApplicationService

open_api_applications = Blueprint('open_api_applications', __name__)
delete_permission_check = PermissionChecker.check_open_api_delete_permission
check_open_api_is_applicant_permission = PermissionChecker.check_open_api_is_applicant_permission


@open_api_applications.route('', methods=['GET'])
@handle_paginate
def get(page, per):
    """
    开放api申请
    查询: get api/open_api_applications
    默认申请时间倒序
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    search_kw = get_request_kwargs()
    if 'ordering' not in search_kw:
        search_kw['ordering'] = '-application_time'
    if 'applicant' in search_kw:
        query, total = OpenApiApplicationService.list(page=page, per=per, **search_kw)
    else:  # 查广场数据时,返回指定state的数据
        query, total = OpenApiApplicationService.get_square_list(page=page, per=per, **search_kw)
    return Result.success(message='获取成功', data=query, total=total)


@open_api_applications.route('', methods=['POST'])
@handle_validate(OpenApiApplicationService)
def post(fields):
    """
    开放api申请
    新增：post api/open_api_applications
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    OpenApiApplicationService.is_valid_date(fields['expiration_time'])
    resp = OpenApiApplicationService.create(**fields)
    return Result.success(message='提交成功', data=resp)


@open_api_applications.route("/<int:mid>", methods=['PUT'])
@check_open_api_is_applicant_permission
@handle_validate(OpenApiApplicationService, methods='update')
def put(mid, fields):
    """
    开放api申请
    更新：put api/open_api_applications/{mid}
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    if fields['app_link'] != '':
        fields['app_link'] = fields['app_link'].strip()
        OpenApiApplicationService.is_valid_app_link(fields['app_link'])
    resp = OpenApiApplicationService.update_by_id(mid, **fields)
    return Result.success(message='更新成功', data=resp)


@open_api_applications.route("/<int:mid>", methods=['DELETE'])
@delete_permission_check
def delete(mid):
    """
    开放api申请
    删除：delete api/open_api_applications/{mid}
    审批未通过、已超期 可删除
    ---
    tags:
      - system
    responses:
      200:
        res: 结果
    """
    OpenApiApplicationService.delete_by_id(mid)
    return Result.success()
