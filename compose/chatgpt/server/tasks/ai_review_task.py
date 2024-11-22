#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/7/28 15:14
"""
import datetime
import logging

from billiard.exceptions import SoftTimeLimitExceeded

from controllers.completion_helper import child_process_execute_completion_main
from services.ai_review.ai_review_service import ReviewService
from tasks import celery_app, handle_db

logger = logging.getLogger(__name__)


def ai_review_failure_callback(task_id, exception, args, kwargs, traceback, einfo):
    """review任务执行失败"""
    request_data = kwargs[0]
    request_data['fail_msg'] = exception
    logger.error(f'review任务执行失败 code_task_id: {request_data["code_task_id"]}, {task_id}, {exception}')
    ReviewService.review_done_handler(data=request_data, review_is_success=False)


@celery_app.task(retry_kwargs={'max_retries': 2, 'countdown': 5, 'retry_on_timeout': False},
                 on_failure=ai_review_failure_callback,
                 soft_time_limit=300)
@handle_db
def execute_ai_review(request_data: dict):
    """执行review请求"""
    try:
        logger.info(f'review任务执行 code_task_id: {request_data["code_task_id"]}', )
        request_data['start_time'] = datetime.datetime.now()
        child_process_execute_completion_main(request_data)
        logger.info(f'review任务完成 code_task_id: {request_data["code_task_id"]}')
    except SoftTimeLimitExceeded:
        logger.info(f'review任务超时 code_task_id: {request_data["code_task_id"]}')
        request_data['fail_msg'] = 'celery task timeout'
        ReviewService.review_done_handler(data=request_data, review_is_success=False)
    except Exception as e:
        logger.info(f'review任务异常 {e}')
        request_data['fail_msg'] = str(e)
        ReviewService.review_done_handler(data=request_data, review_is_success=False)

    return True
