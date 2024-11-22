#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/6/6 14:39
"""
import logging

from flask import Blueprint

from common.constant import AIReviewConstant
from common.exception.exceptions import FieldValidateError
from common.helpers.response_helper import Result
from controllers.base import handle_validate, get_request_kwargs
from services.ai_review.ai_review_task_record_service import AIReviewTaskRecordService
from services.ai_review.ai_review_main import ReviewMainService
from services.ai_review.ai_review_service import ReviewService

logger = logging.getLogger(__name__)
review = Blueprint('review', __name__)


@review.route('/poll', methods=['GET'])
def get_poll():
    """
    轮询
    ---
    tags:
      - 代码review
    responses:
      200:
        result: 结果
    """
    search_kw = get_request_kwargs()
    ids_str = search_kw.get('ids', '')
    if not ids_str:
        raise FieldValidateError('ids为必传参数')

    resp = ReviewService.get_poll(search_kw)
    return Result.success(message='获取成功', data=resp)


@review.route('/tasks/<int:mid>', methods=['PUT'])
@handle_validate(AIReviewTaskRecordService, methods='update')
def update_task(mid, fields):
    """
    更新任务
    ---
    tags:
      - 代码review
    responses:
      200:
        result: 结果
    """
    resp = AIReviewTaskRecordService.update_flag(mid, **fields)
    return Result.success(message='更新成功', data=resp)


@review.route('', methods=['POST'])
@handle_validate(ReviewService)
def ai_review(fields):
    """
    review任务
    ---
    tags:
      - 代码review
    responses:
      200:
        result: 结果
    """
    fields['language'] = fields.get('language').lower()
    if fields.get('review_type') == AIReviewConstant.ReviewType.MANUAL:
        return ReviewMainService.run_manual_review(fields)
    else:
        resp = ReviewMainService.run_auto_review(fields)
        return Result.success(message='成功', data=resp)
