#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import traceback

from billiard.exceptions import SoftTimeLimitExceeded

from common.constant import ApiTestCaseConstant
from tasks import celery_app, handle_db

logger = logging.getLogger(__name__)


def execute_api_testcases_task_fail_callback(task_id, exception, args, kwargs, traceback, einfo):
    """执行API测试用例任务执行失败"""
    request_data = kwargs[0]
    display_name = request_data['display_name']
    logger.info(f"execute_api_testcases_task异常退出 display_name: {request_data['display_name']}; "
                f"task_id: {request_data['task_id']}, celery_task_id: {task_id}; error: {exception}")
    from services.api_test.api_test_case_service import ApiTestCaseService
    ApiTestCaseService.fail_task(display_name, request_data['task_id'], remark="任务异常终止",
                                 req_data={"error": str(exception)})


def execute_api_test_eolinker_case_task_fail_callback(task_id, exception, args, kwargs, traceback, einfo):
    """执行API测试用例任务执行失败"""
    request_data = kwargs[0]
    display_name = request_data['display_name']
    logger.info(f"execute_api_test_eolinker_case_task_async异常退出 display_name: {request_data['display_name']}; "
                f"gen_eoliner_task_id: {request_data['gen_eoliner_task_id']}, "
                f"celery_task_id: {task_id}; error: {exception}")
    from services.api_test.api_test_case_service import ApiTestEolinkerCaseTaskService
    ApiTestEolinkerCaseTaskService.fail_task(display_name, request_data['gen_eoliner_task_id'], remark="任务异常终止",
                                             req_data={"error": str(exception)})


@celery_app.task(queue=ApiTestCaseConstant.CELERY_API_CASE_QUEUE,
                 retry_kwargs={'max_retries': 2, 'countdown': 5, 'retry_on_timeout': False},
                 on_failure=execute_api_testcases_task_fail_callback,
                 soft_time_limit=ApiTestCaseConstant.TASK_TIMEOUT)
@handle_db
def execute_api_testcases_task_async(request_data: dict):
    from services.api_test.api_test_case_service import ApiTestCaseService
    from services.api_test.api_test_case_task_executor import TaskExecuteManager
    display_name = request_data['display_name']
    task_id = request_data['task_id']
    try:
        TaskExecuteManager.execute_gen_api_testcases_task(request_data)
    except SoftTimeLimitExceeded:
        logger.info(f'execute_api_testcases_task超时 display_name: {display_name}; task_id: {task_id}')
        ApiTestCaseService.stop_task(display_name, task_id, remark="任务超时")
    except Exception as e:
        logger.info(f'execute_api_testcases_task异常 display_name: {display_name}; task_id: {task_id}, error: {e}')
        ApiTestCaseService.fail_task(display_name, task_id, remark="任务异常",
                                     req_data={"error": str(traceback.format_exc())})


@celery_app.task(queue=ApiTestCaseConstant.CELERY_EOLINKER_CASE_QUEUE,
                 retry_kwargs={'max_retries': 2, 'countdown': 5, 'retry_on_timeout': False},
                 on_failure=execute_api_test_eolinker_case_task_fail_callback,
                 soft_time_limit=ApiTestCaseConstant.TASK_TIMEOUT)
@handle_db
def execute_api_test_eolinker_case_task_async(request_data: dict):
    from services.api_test.api_test_case_service import ApiTestEolinkerCaseTaskService
    from services.api_test.api_test_case_task_executor import TaskExecuteManager
    display_name = request_data['display_name']
    gen_eoliner_task_id = request_data['gen_eoliner_task_id']
    try:
        TaskExecuteManager.execute_gen_case_to_eolinker(request_data)
    except SoftTimeLimitExceeded:
        logger.info(f'api_test_eolinker_case_task超时 display_name: {display_name}; '
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}')
        ApiTestEolinkerCaseTaskService.stop_task(display_name, gen_eoliner_task_id, remark="任务超时")
    except Exception as e:
        logger.info(f'api_test_eolinker_case_task异常 display_name: {display_name}; '
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}, error: {traceback.format_exc()}')
        ApiTestEolinkerCaseTaskService.fail_task(display_name, gen_eoliner_task_id,
                                                 remark="任务异常", req_data={"error": str(e)})


@celery_app.task(queue=ApiTestCaseConstant.CELERY_API_CASE_QUEUE,
                 retry_kwargs={'max_retries': 2, 'countdown': 5, 'retry_on_timeout': False},
                 on_failure=execute_api_testcases_task_fail_callback,
                 soft_time_limit=ApiTestCaseConstant.TASK_TIMEOUT)
@handle_db
def execute_api_management_testcases_task_async(request_data: dict):
    from services.api_test.api_test_case_service import ApiTestCaseService
    from services.api_test.api_test_case_task_executor import TaskExecuteManager
    display_name = request_data['display_name']
    task_id = request_data['task_id']
    try:
        TaskExecuteManager.execute_gen_api_management_testcases_task(request_data)
    except SoftTimeLimitExceeded:
        logger.info(f'execute_gen_api_management_testcases_task超时 display_name: {display_name}; task_id: {task_id}')
        ApiTestCaseService.stop_task(display_name, task_id, remark="任务超时")
    except Exception as e:
        logger.info(
            f'execute_gen_api_management_testcases_task异常 display_name: {display_name}; task_id: {task_id}, error: {e}')
        ApiTestCaseService.fail_task(display_name, task_id, remark="任务异常",
                                     req_data={"error": str(traceback.format_exc())})


@celery_app.task(queue=ApiTestCaseConstant.CELERY_EOLINKER_CASE_QUEUE,
                 retry_kwargs={'max_retries': 2, 'countdown': 5, 'retry_on_timeout': False},
                 on_failure=execute_api_test_eolinker_case_task_fail_callback,
                 soft_time_limit=ApiTestCaseConstant.TASK_TIMEOUT)
@handle_db
def execute_api_management_test_eolinker_case_task_async(request_data: dict):
    from services.api_test.api_test_case_service import ApiTestEolinkerCaseTaskService
    from services.api_test.api_test_case_task_executor import TaskExecuteManager
    display_name = request_data['display_name']
    gen_eoliner_task_id = request_data['gen_eoliner_task_id']
    try:
        TaskExecuteManager.execute_gen_management_case_to_eolinker(request_data)
    except SoftTimeLimitExceeded:
        logger.info(f'execute_gen_management_case_to_eolinker超时 display_name: {display_name}; '
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}')
        ApiTestEolinkerCaseTaskService.stop_task(display_name, gen_eoliner_task_id, remark="任务超时")
    except Exception as e:
        logger.info(f'execute_gen_management_case_to_eolinker异常 display_name: {display_name}; '
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}, error: {traceback.format_exc()}')
        ApiTestEolinkerCaseTaskService.fail_task(display_name, gen_eoliner_task_id,
                                                 remark="任务异常", req_data={"error": str(e)})


@celery_app.task(queue=ApiTestCaseConstant.CELERY_EOLINKER_CASE_QUEUE,
                 retry_kwargs={'max_retries': 2, 'countdown': 5, 'retry_on_timeout': False},
                 on_failure=execute_api_test_eolinker_case_task_fail_callback,
                 soft_time_limit=ApiTestCaseConstant.TASK_TIMEOUT)
@handle_db
def execute_modify_exist_case_async(request_data: dict):
    from services.api_test.api_test_case_service import ApiTestEolinkerCaseTaskService
    from services.api_test.api_test_case_task_executor import TaskExecuteManager
    display_name = request_data['display_name']
    gen_eoliner_task_id = request_data['gen_eoliner_task_id']
    try:
        TaskExecuteManager.execute_modify_exist_case(request_data)
    except SoftTimeLimitExceeded:
        logger.info(f'api_test_modify_case_task超时 display_name: {display_name}; '
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}')
        ApiTestEolinkerCaseTaskService.stop_task(display_name, gen_eoliner_task_id, remark="任务超时")
    except Exception as e:
        logger.info(f'aapi_test_modify_case_task异常 display_name: {display_name}; '
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}, error: {traceback.format_exc()}')
        ApiTestEolinkerCaseTaskService.fail_task(display_name, gen_eoliner_task_id,
                                                 remark="任务异常", req_data={"error": str(e)})


@celery_app.task()
@handle_db
def check_api_test_eolinker_case_task():
    # 检查非终态非排队并且更新时间距离现在大于20分钟的任务
    # 改成中止状态
    from services.api_test.api_test_case_service import ApiTestEolinkerCaseTaskService
    ApiTestEolinkerCaseTaskService.check_task()
