#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/19 14:18
"""

from flask import Blueprint

from common.helpers.application_context import ApplicationContext
from common.helpers.custom_permission import PermissionChecker
from common.helpers.custom_throttle import limiter
from controllers.base import handle_validate
from controllers.completion_helper import completion_main
from services.action.complation_service import CompletionService

actions_v3 = Blueprint('actions_v3', __name__)
permission_check = PermissionChecker.check_open_api_permission


@actions_v3.route('/completion', methods=['POST'])
@limiter.limit('40 per minute', key_func=ApplicationContext.get_current_app_id)
@permission_check
@handle_validate(CompletionService)
def completion(fields):
    """
    补全
    ---
    tags:
      - 补全
    responses:
      200:
        res: 结果
    
    """
    return completion_main(fields)
