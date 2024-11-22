#!/usr/bin/env python
# -*- coding: utf-8 -*-
import concurrent.futures
import datetime
import logging
import os
import uuid

from celery.app.control import Control
from celery.result import AsyncResult

from common.constant import ApiTestCaseConstant, ActionsConstant, GPTModelConstant, GPTConstant
from common.validation.base_validation import ApiTestCaseTaskRequestModel, ApiTestRequestModel
from dao.system.api_test_case_dao import ApiTestCaseTaskDao, ApiTestEolinkerCaseTaskDao
from lib.cache import BaseCache
from lib.cache.lock import parameter_lock
from services.api_test.api_test_ai_helper import ApiAiHelper
from services.api_test.api_test_case_task_events_service import ApiTestCaseTaskEventsService
from services.base_service import BaseService
from tasks import celery_app
from tasks.api_test_case_task import execute_api_testcases_task_async, execute_api_management_testcases_task_async
from third_platform.eolinker.api_studio_manager import ApiStudioManager, ApiStudioHelper

logger = logging.getLogger(__name__)


class ApiTestCaseService(BaseService):
    """
    API测试用例相关服务
    """
    dao = ApiTestCaseTaskDao
    LOCK_API_TEST_CASE_TASK_DISPLAY_NAME = "lock:api_test_case_task:display_name"

    @classmethod
    @parameter_lock(key="display_name", blocking=False, prefix_key=LOCK_API_TEST_CASE_TASK_DISPLAY_NAME,
                    lock_exist_return={"status": "fail", "msg": "有请求正在处理中，请稍后重试！"})
    def api_test_case_task(cls, req_model: ApiTestCaseTaskRequestModel, display_name, origin=None):
        """
        生成API测试用例任务
        :param req_model: 请求数据
        :param display_name: 请求用户
        :param origin:
        :return:
        """
        # 如果用户任务锁存在，直接返回
        if cls.check_task_lock(display_name):
            return {"status": "fail", "msg": "有任务正在处理中，请稍后重试！"}

        req_data = req_model.model_dump()
        req_data["origin"] = origin
        req_data["display_name"] = display_name

        # 在此处解析修改用例的数量，优化进度显示效果
        api_list = req_data.get('api_list', [])
        total_case_modify = 0
        for api in api_list:
            api_relation_testcase_list = api.get('api_relation_testcase_list', [])
            if api.get('current_history').get('id') == api.get('old_history').get('id'):
                continue
            for api_relation_testcase in api_relation_testcase_list:
                if api_relation_testcase.get('is_selected', False):
                    total_case_modify += 1
        req_data["total_case_modify"] = total_case_modify

        # 创建数据库数据
        obj = cls.create(
            display_name=display_name,
            status=ApiTestCaseConstant.ApiTestCaseTaskStatus.PENDING,
            req_data=req_data,
        )
        task_id = obj.id
        req_data["task_id"] = task_id
        # 加用户任务锁
        cls._add_task_lock(display_name, task_id)
        api_test_sync = os.environ.get("API_TEST_SYNC")
        if api_test_sync:
            # 同步调用，不使用异步任务，调试的时候才用，防止循环导包
            from services.api_test.api_test_case_task_executor import TaskExecuteManager
            TaskExecuteManager.execute_gen_api_testcases_task(req_data)
            # 获取任务ID
            celery_task_id = str("fffffffffffffff")
        else:
            # 创建异步任务
            result = execute_api_testcases_task_async.delay(req_data)
            # 获取任务ID
            celery_task_id = str(result.id)
        # 将celery任务id添加到数据库
        cls.update_by_id(
            task_id,
            celery_task_id=celery_task_id,
        )

        return {"status": "success", "task_id": task_id, "celery_task_id": celery_task_id}

    @classmethod
    def api_management_test_case_task(cls, req_model: ApiTestRequestModel, display_name, origin=None):
        """
        生成API测试用例任务，对应API管理平台的用例任务
        :param req_model: 请求数据
        :param display_name: 请求用户
        :param origin:
        :return:
        """
        req_data = req_model.model_dump()
        req_data["origin"] = origin
        req_data["display_name"] = display_name
        # 创建数据库数据
        obj = cls.create(
            display_name=display_name,
            status=ApiTestCaseConstant.ApiTestCaseTaskStatus.PENDING,
            req_data=req_data,
            test_case_stage=ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT,
        )
        task_id = obj.id
        req_data["task_id"] = task_id
        api_test_sync = os.environ.get("API_TEST_SYNC")
        if api_test_sync:
            from services.api_test.api_test_case_task_executor import TaskExecuteManager
            TaskExecuteManager.execute_gen_api_management_testcases_task(req_data)
            # 获取任务ID
            celery_task_id = str("fffffffffffffff")
        else:
            # 创建异步任务
            result = execute_api_management_testcases_task_async.delay(req_data)
            # 获取任务ID
            celery_task_id = str(result.id)
        # 将celery任务id添加到数据库
        cls.update_by_id(
            task_id,
            celery_task_id=celery_task_id,
        )

        return {"status": "success", "task_id": task_id, "celery_task_id": celery_task_id}

    @classmethod
    def start_task(cls, task_id, **kwargs):
        """
        任务开始
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        cls.update_by_id_json(task_id, status=ApiTestCaseConstant.ApiTestCaseTaskStatus.STARTED, **kwargs)

    @classmethod
    def stop_task(cls, display_name, task_id, **kwargs):
        """
        任务结束
        :param display_name: 请求用户
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        stop_result = cls.update_by_id_json(task_id, status=ApiTestCaseConstant.ApiTestCaseTaskStatus.REVOKED, **kwargs)
        ApiTestCaseTaskEventsService.change_status_by_task_id(task_id,
                                                              ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.REVOKED)
        # api管理页面没有任务锁，直接返回
        if stop_result and ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT == stop_result.test_case_stage:
            return

        # 释放锁
        cls._release_task_lock(display_name, task_id)

    @classmethod
    def fail_task(cls, display_name, task_id, **kwargs):
        """
        任务失败
        :param display_name: 用户
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        fail_result = cls.update_by_id_json(task_id, status=ApiTestCaseConstant.ApiTestCaseTaskStatus.FAILURE, **kwargs)
        ApiTestCaseTaskEventsService.change_status_by_task_id(task_id,
                                                              ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.FAILURE)
        # api管理页面没有任务锁，直接返回
        if fail_result and ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT == fail_result.test_case_stage:
            return
        # 释放锁
        cls._release_task_lock(display_name, task_id)

    @classmethod
    def success_task(cls, display_name, task_id, **kwargs):
        """
        任务成功
        :param display_name: 用户
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        succ_result = cls.update_by_id_json(task_id, status=ApiTestCaseConstant.ApiTestCaseTaskStatus.SUCCESS, **kwargs)
        ApiTestCaseTaskEventsService.change_status_by_task_id(task_id,
                                                              ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.SUCCESS)
        # api管理页面没有任务锁，直接返回
        if succ_result and ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT == succ_result.test_case_stage:
            return
        # 释放锁
        cls._release_task_lock(display_name, task_id)

    @classmethod
    def update_by_id_json(cls, mid, **kwargs):
        logging.info(f"更新{cls.dao.model.__name__},id:{mid},kwargs:{kwargs}")
        # 更新前， 检查是否存在该资源
        _obj = cls.get_by_id(mid)
        if "req_data" in kwargs:
            data = kwargs.pop("req_data")
            old_data = _obj.req_data
            old_data.update(data)
            kwargs["req_data"] = old_data

        cls.dao.update_by_id(mid, **kwargs)
        result = cls.get_by_id(mid)
        return result

    @classmethod
    def _task_lock_is_exist(cls, display_name):
        """判断锁是否存在，如果存在返回值, 如果不存在返回None"""
        task_lock_key = ApiTestCaseConstant.LOCK_API_TESTCASES_TASK_KEY.format(display_name=display_name)
        cache = BaseCache()
        res = cache.get(task_lock_key)
        logger.info(f"_task_lock_is_exist:{display_name}:{cache.connection},res:{res}")
        return res if res else None

    @classmethod
    def check_task_lock(cls, display_name):
        """
        校验用户任务锁是否锁定，锁定返回True, 未锁定返回False
        也可用于判断用户当前是否有任务在进行中
        """
        redis_value = cls._task_lock_is_exist(display_name=display_name)

        # 查询数据库表数据
        query, total = cls.get_run_task_by_user(display_name)

        if not redis_value and not query:
            is_exist = False
        # 如果有锁但是任务没了，释放锁
        elif redis_value and not query:
            logger.warning(f"用户任务锁存在但是任务已结束，释放锁, display_name: {display_name}, task_id:{redis_value}")
            cls._release_task_lock(display_name, task_id=redis_value)
            is_exist = False
        # 如果锁没了但是任务存在
        elif not redis_value and query and total == 1:
            logger.warning(f"用户任务锁异常丢失，加锁, display_name: {display_name}, task_id:{query[0].id}")
            cls._add_task_lock(display_name, task_id=query[0].id)
            is_exist = True
        else:
            is_exist = True
        if is_exist:
            celery_task_id = query[0].celery_task_id
            try:
                async_result = AsyncResult(celery_task_id, app=celery_app)
                final_state = async_result.state
            except AttributeError:
                final_state = ApiTestCaseConstant.ApiTestCaseTaskStatus.FAILURE

            if final_state in [ApiTestCaseConstant.ApiTestCaseTaskStatus.SUCCESS,
                               ApiTestCaseConstant.ApiTestCaseTaskStatus.FAILURE,
                               ApiTestCaseConstant.ApiTestCaseTaskStatus.REVOKED]:
                cls._release_task_lock(display_name, task_id=query[0].id)
                if final_state == ApiTestCaseConstant.ApiTestCaseTaskStatus.SUCCESS:
                    cls.success_task(display_name, task_id=query[0].id)
                elif final_state == ApiTestCaseConstant.ApiTestCaseTaskStatus.FAILURE:
                    cls.fail_task(display_name, task_id=query[0].id)
                else:
                    cls.stop_task(display_name, task_id=query[0].id)
                is_exist = False

        return is_exist

    @classmethod
    def _add_task_lock(cls, display_name, task_id):
        """添加锁: 如果已存在，添加失败，False；不存在，添加成功，返回True"""
        task_lock_key = ApiTestCaseConstant.LOCK_API_TESTCASES_TASK_KEY.format(display_name=display_name)
        cache = BaseCache()
        lock = cache.set(
            task_lock_key,
            task_id,
            nx=True
        )
        logger.info(f"_add_task_lock_lock:{display_name}:{cache.connection},lock:{lock}")
        return True if lock else False

    @classmethod
    def _release_task_lock(cls, display_name, task_id):
        """释放锁: 存在，释放, 不存在，定时任务已释放"""
        task_lock_key = ApiTestCaseConstant.LOCK_API_TESTCASES_TASK_KEY.format(display_name=display_name)
        cache = BaseCache()
        ret = cache.delete(task_lock_key)
        logger.info(f"释放用户任务锁, display_name:{display_name}:{cache.connection}, task_id:{task_id}, 返回:{ret}")
        return ret

    @classmethod
    def stop_api_test_case_task(cls, display_name, test_case_stage=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST):
        """
        停止API测试用例任务
        :param display_name: 请求用户
        :param test_case_stage: 用例阶段，用于区分api management和automated_test页面用例
        :return:
        """
        # 获取控制实例
        control = Control(app=celery_app)
        # 查询数据库表数据
        query, total = cls.get_run_task_by_user(display_name, test_case_stage)
        for item in query:
            celery_task_id = item.celery_task_id
            # 撤销任务
            control.revoke(celery_task_id, terminate=True, signal='SIGKILL')
            ApiTestEolinkerCaseTaskService.stop_all_by_api_test_case_task_id(display_name, item.id)
        cls._release_task_lock(display_name, None)
        return True

    @classmethod
    def get_run_task_by_user(cls, display_name, test_case_stage=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST):
        """
        根据用户查询当前运行中的任务
        :param display_name: 请求用户
        :param test_case_stage: 用例阶段，用于区分api management和automated_test页面用例
        :return:
        """
        query, total = cls.list(
            display_name=display_name,
            test_case_stage=test_case_stage,
            status=[ApiTestCaseConstant.ApiTestCaseTaskStatus.STARTED,
                    ApiTestCaseConstant.ApiTestCaseTaskStatus.PENDING],
            deleted=False,
            sort_by="id",
            sort_to="desc"
        )
        return query, total

    @classmethod
    def get_run_detail_task_by_user(cls, display_name, task_id=None,
                                    test_case_stage=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST):
        """
        根据用户查询当前运行中的任务详情
        :param display_name: 请求用户
        :param task_id: 任务ID
        :param test_case_stage: 用例阶段，用于区分api management和automated_test页面用例
        :return:
        """
        if not task_id:
            query, total = cls.get_run_task_by_user(display_name, test_case_stage)
            task_obj = query[0] if query else None
        else:
            task_obj = cls.get_by_id(task_id)

        if not task_obj:
            return None

        query, _ = ApiTestCaseTaskEventsService.list(api_test_case_task_id=task_obj.id,
                                                     include_fields=["id", "event_type", "status",
                                                                     "remark", "created_at", "update_at"],
                                                     sort_by="id",
                                                     sort_to="desc")
        task_data = task_obj.to_dict_with_status_display()
        total_status_real = 0
        if test_case_stage == ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT and \
                task_data.get("req_data", {"test_points": []}).get("test_points"):
            total_status_real = len(task_data.get("req_data", {"test_points": []}).get("test_points"))

        task_data["events"] = [i.to_dict_with_status_display() for i in query]

        ask_ai_test_points_status = cls.get_ask_ai_test_points_status(task_data["events"])
        task_data["eolinker_case_task_process"], task_data["title_msg"] = cls.get_title_msg(
            api_test_case_task_id=task_obj.id,
            events=task_data["events"],
            ask_ai_test_points_status=ask_ai_test_points_status,
            total_status_real=total_status_real)

        return task_data

    @classmethod
    def get_case_info(cls, params):
        return ApiStudioManager.get_case_info(params.get("space_id"), params.get("caseItem")['projectHashKey'],
                                              case_id=params.get("caseItem")['caseID'],
                                              authorization=params.get("authorization"), origin=params.get("origin"))

    @classmethod
    def parse_testcase_latest_update_time(cls, api_relation_test_case_list, space_id, origin, authorization):
        """
        根据关联用例列表信息解析最新更新时间
        :param api_relation_test_case_list: 关联列表信息
        :param space_id: 空间ID
        :param origin: 请求来源
        :param authorization: 请求头认证信息
        :return:
        """
        if not api_relation_test_case_list:
            return {"latest_update_time": ""}
        all_response_data = []
        latest_update_time = ''

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(cls.get_case_info,
                                       {"space_id": space_id, "caseItem": caseItem, "authorization": authorization,
                                        "origin": origin}) for caseItem in api_relation_test_case_list]
            for future in concurrent.futures.as_completed(futures):
                resp = future.result()
                all_response_data.append(resp)

        # allResponseData = [result.json() for result in results]
        for response_data in all_response_data:
            if response_data.get('statusCode') and response_data.get('statusCode') == '000000':
                single_case_list = response_data.get('singleCaseList')
                for single_case in single_case_list:
                    if single_case.get('latestTestTime'):
                        if not latest_update_time:
                            latest_update_time = single_case.get('updateTime')
                        else:
                            update_date_time = datetime.datetime.strptime(single_case.get('updateTime'),
                                                                          '%Y-%m-%d %H:%M:%S')
                            latest_update_date_time = datetime.datetime.strptime(latest_update_time,
                                                                                 '%Y-%m-%d %H:%M:%S')
                            if update_date_time > latest_update_date_time:
                                latest_update_time = single_case.get('updateTime')

        logging.info(f"latest_update_time :{latest_update_time}")
        return {"latest_update_time": latest_update_time}

    @classmethod
    def get_ask_ai_test_points_status(cls, events):
        """
        获取问答测试点状态
        :param events: 事件列表
        :return: 问答测试点状态
        """
        ask_ai_test_points_status = ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED
        for event in events:
            if event.get("event_type") == ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_TEST_POINTS:
                ask_ai_test_points_status = event.get("status")
                break
        return ask_ai_test_points_status

    @classmethod
    def get_title_msg(cls, api_test_case_task_id, events, ask_ai_test_points_status,
                      total_status_real=0):
        """
        获取标题信息，包含进度和状态
        :param api_test_case_task_id: 任务ID
        :param events: 事件列表
        :param ask_ai_test_points_status: 问答测试点状态
        :param total_status_real: 真实的状态数量，非流式测试点类型选用
        :return: 标题信息
        """
        eolinker_case_task_process = 0
        # 新生成用例数目，缺省为20
        total_status = 20

        # 生成/修改测试用例任务（子任务）
        query_eolinker_case, total_eolinker_case = ApiTestEolinkerCaseTaskService.list(
            api_test_case_task_id=api_test_case_task_id,
            include_fields=["id", "status"],
            sort_by="id",
            sort_to="desc")

        # api管理页面测试点是手动勾选（非流式），总任务数是固定的，这里可以使用真实进度
        if total_status_real > 0 and total_eolinker_case > 0:
            total_status = total_status_real
        # 父任务
        query_api_test, total_api_test = ApiTestCaseService.list(id=api_test_case_task_id,
                                                                 include_fields=["id", "status", "req_data"],
                                                                 sort_by="id",
                                                                 sort_to="desc")

        finish_api_test_task = []
        total_case_modify = 0
        for item in query_api_test:
            req = item.get_req_data()
            total_case_modify += req.get('total_case_modify', 0)
            if item.is_final_status:
                finish_api_test_task.append(item)

        total_status += total_case_modify

        # 子任务任务数量为 0，两种情况：还没开始生成/生成完为空
        if not total_eolinker_case:
            if total_api_test == len(finish_api_test_task):
                title_msg = "生成测试用例完毕，本次无新增用例"
            else:
                events_display = []
                # 不需要展示的列表
                not_title_msg_events = [ApiTestCaseConstant.ApiTestCaseTaskEventsType.API_TEST_CASE_REPEAT_VERIFIED]
                for event in events:
                    if event.get('event_type_display') not in not_title_msg_events:
                        events_display.append(f"{event.get('event_type_display')}，{event.get('status_display')}")
                title_msg = '\n'.join(events_display)
        else:
            # 由于测试点流式输出，这里的total_status可能会发生变化，这里先给个
            finish_task = [i for i in query_eolinker_case if i.is_final_status]
            if ask_ai_test_points_status in ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FINAL_STATUS \
                    and len(finish_task) == total_eolinker_case:
                # 测试点为终态且完成任务和总任务相同时说明任务完成
                eolinker_case_task_process = 100
            else:
                eolinker_case_task_process = int(len(finish_task) / total_status * 100) if len(
                    finish_task) < total_status else 99
            title_msg = f"生成测试用例进度：{eolinker_case_task_process}%"

        return eolinker_case_task_process, title_msg

    @classmethod
    def add_param_name_to_step_params(cls, param_list, step_params_list):
        """
        递归填充参数列表的param_name(参数说明)到步骤参数中，兼容不同childList存在相同paramKey问题
        :param param_list: 参数列表
        :param step_params_list: 步骤参数列表
        """
        # 创建一个字典，用于存储paramKey和paramName的对应关系，以及paramKey的路径
        param_key_to_name = {}

        # 递归函数，用于填充param_key_to_name字典
        def fill_param_key_to_name(sub_param_list, parent_path=""):
            for param in sub_param_list:
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('paramKey')}" if parent_path else param.get('paramKey')
                if param.get('paramName'):
                    param_key_to_name[current_path] = param.get('paramName')
                # 递归检查子参数
                if 'childList' in param:
                    fill_param_key_to_name(param['childList'], current_path)

        # 递归函数，用于在step_params中添加param_name
        def add_param_name_to_step_params_recursion(sub_step_params_list, parent_path=""):
            for param in sub_step_params_list:
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('param_key')}" if parent_path else param.get('param_key')
                # 如果param_key的路径在param_key_to_name中，添加param_name
                if current_path in param_key_to_name:
                    param['param_name'] = param_key_to_name[current_path]
                # 递归检查子参数
                if 'child_list' in param:
                    add_param_name_to_step_params_recursion(param['child_list'], current_path)

        # 填充param_key_to_name字典
        fill_param_key_to_name(param_list)
        # 在step_params中添加param_name
        add_param_name_to_step_params_recursion(step_params_list)

    @classmethod
    def test_point_is_repeated(cls, api_test_case_task_id, exist_test_point, new_point, display_name=""):
        """
        校验新增测试点是否和老测试点重复
        :param api_test_case_task_id: 测试任务id， api_test_case_task_id
        :param exist_test_point: 存在测试点列表
        :param new_point: 新测试点
        :param display_name: 请求用户
        return boolean
        """
        ask_data = {
            "exist_case": exist_test_point,
            "new_case": new_point,
            "display_name": display_name,
            "stream": False,
            "action": ActionsConstant.API_TEST_CASE_REPEAT_VERIFIED,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        data_obj = ApiAiHelper.get_ai_resp(api_test_case_task_id, ask_data,
                                           ApiTestCaseConstant.ApiTestCaseTaskEventsType.API_TEST_CASE_REPEAT_VERIFIED)
        return data_obj.get("similarly_status")

    @classmethod
    def api_test_point_is_test_param_type_error(cls, test_point, api_id):
        """
        校验测试点是否属于参数类型异常测试
        :param test_point: 测试点描述
        :param api_id: api_id, 这里方便和步骤关联
        return boolean
        """
        ask_data = {
            "test_point": test_point,
            "stream": False,
            "action": ActionsConstant.API_TEST_PARAM_TYPE_ERROR_VERIFIED,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        data_obj = ApiAiHelper.get_ai_resp(api_id, ask_data,
                                           ApiTestCaseConstant.ApiTestCaseTaskEventsType.API_TEST_CASE_REPEAT_VERIFIED)
        return data_obj.get("is_param_type_error_test")

    @staticmethod
    def is_newest_case(api_list, case_info):
        """
        判断是否为最新用例，如果case_info中所有步骤更新时间均比api的更新时间新，则任务用例已更新，不需要再进行更新
        :param api_list: 包含API历史数据的API列表
        :param case_info: 用例信息，用例步骤中包含更新时间
        :return: bool
        """
        is_newest = True
        for api in api_list:
            api_id = api.get('api_id')
            api_project_id = api.get('project_id')
            api_update_time = api.get('current_history', {}).get("update_time")
            for single_case in case_info.get("singleCaseList"):
                single_case_api_id = single_case.get("apiID")
                single_case_api_project_id = single_case.get("apiProjectHashKey")
                single_case_update_time = single_case.get("updateTime")
                if api_id and single_case_api_id and api_id == single_case_api_id and \
                        api_project_id and single_case_api_project_id and api_project_id == single_case_api_project_id \
                        and api_update_time and single_case_update_time \
                        and datetime.datetime.strptime(api_update_time, "%Y-%m-%d %H:%M:%S") > \
                        datetime.datetime.strptime(single_case_update_time, "%Y-%m-%d %H:%M:%S"):
                    is_newest = False
                    break
        return is_newest

    @staticmethod
    def get_case_steps_info(space_id, project_id, case_id, authorization, origin):
        """
        获取测试步骤详情，测试步骤会被组装成dict格式
        :param space_id: 空间 id
        :param project_id: 项目 id
        :param case_id: 测试步骤所属的用例 id
        :param authorization: 鉴权 key
        :param origin:
        :return: 一个元组，包含了 (test_steps_dict, conn_id_list, resp_case_steps)
        其中，test_steps_dict 为解析出的测试步骤。conn_id_list 为该用例所包含的测试步骤序号列表, resp_case_steps 为未处理的第三方接口
        返回内容。
        """

        resp_case_steps = ApiStudioManager.get_case_info(space_id, project_id, case_id=case_id,
                                                         authorization=authorization,
                                                         origin=origin)

        conn_id_list = []
        test_steps_title_list = []
        for single_case in resp_case_steps["singleCaseList"]:
            conn_id_list.append(single_case["connID"])
            test_steps_title_list.append({
                "api_id": single_case["apiID"],
                "step_name": single_case["apiName"]
            })

        test_point = resp_case_steps["caseName"]
        test_steps = []

        api_key = ApiStudioHelper.get_space_api_key(space_id, authorization, origin)

        for conn_id in conn_id_list:
            resp_step_info = ApiStudioManager.get_step_info(space_id, project_id, case_id, conn_id, origin, api_key)
            test_steps.append(ApiTestCaseService.construct_case_data(resp_step_info))

        test_steps_dict = {
            "test_point": test_point,
            "test_steps_title": test_steps_title_list,
            "test_steps": test_steps
        }

        return test_steps_dict, conn_id_list, resp_case_steps

    @staticmethod
    def construct_case_data(raw_data: dict) -> dict:
        construct_result = {}
        raw_case_data = raw_data["single_case_info"]["case_data"]
        construct_result["conn_id"] = raw_data["single_case_info"]["conn_id"]
        construct_result["api_url"] = raw_case_data["url"]
        construct_result["api_id"] = raw_data["single_case_info"]["api_id"]

        case_data = {"url": raw_case_data["url"],
                     "step_type": "api_request",
                     "headers": raw_case_data["headers"],
                     "url_param": raw_case_data["url_param"],
                     "restful_param": raw_case_data["restful_param"],
                     "params": raw_case_data["params"]}

        construct_result["case_data"] = case_data
        construct_result["status_code_verification"] = raw_data["single_case_info"]["status_code_verification"]
        construct_result["response_result_verification"] = raw_data["single_case_info"]["response_result_verification"]

        return construct_result


class ApiTestEolinkerCaseTaskService(BaseService):
    dao = ApiTestEolinkerCaseTaskDao
    LOCK_TEST_CASE_TASK_ID = "lock:api_test_case_task_id"
    TASK_TIMEOUT = 20

    @classmethod
    def check_task(cls):
        # 检查非终态非排队并且更新时间距离现在大于20分钟的任务
        # 改成中止状态
        now = datetime.datetime.now()
        minutes_ago = now - datetime.timedelta(minutes=cls.TASK_TIMEOUT)
        conditions = (cls.dao.model.update_at < minutes_ago,)
        result, total = cls.list(status=ApiTestCaseConstant.ApiTestCaseTaskStatus.STARTED, conditions=conditions)
        index = 1
        logger.info("开始兜底检查,数量：0")
        for item in result:
            logger.info(f"兜底进度： {index} / {total}")
            cls.stop_task(item.display_name, item.id, remark="兜底中止")
            index += 1
        logger.info("兜底完成")

    @classmethod
    def start_task(cls, task_id, **kwargs):
        """
        任务开始
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        cls.update_by_id_json(task_id, status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.STARTED, **kwargs)

    @classmethod
    def stop_task(cls, display_name, gen_eoliner_task_id, check_status=True, **kwargs):
        """
        任务结束
        :param display_name: 请求用户
        :param gen_eoliner_task_id: 任务ID
        :param check_status: 是否检查所有任务状态,并更新父任务状态
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        obj = cls.update_by_id_json(gen_eoliner_task_id,
                                    status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.REVOKED,
                                    **kwargs)
        if check_status:
            cls.judge_is_all_is_done(display_name, obj.api_test_case_task_id)

    @classmethod
    def fail_task(cls, display_name, gen_eoliner_task_id, check_status=True, **kwargs):
        """
        任务失败
        :param display_name: 请求用户
        :param gen_eoliner_task_id: 任务ID
        :param check_status: 是否检查所有任务状态,并更新父任务状态
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        obj = cls.update_by_id_json(gen_eoliner_task_id,
                                    status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FAILURE,
                                    **kwargs)
        if check_status:
            cls.judge_is_all_is_done(display_name, obj.api_test_case_task_id)

    @classmethod
    def success_task(cls, display_name, gen_eoliner_task_id, check_status=True, **kwargs):
        """
        任务成功
        :param display_name: 请求用户
        :param gen_eoliner_task_id: 任务ID
        :param check_status: 是否检查所有任务状态,并更新父任务状态
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        obj = cls.update_by_id_json(gen_eoliner_task_id,
                                    status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.SUCCESS,
                                    **kwargs)
        if check_status:
            cls.judge_is_all_is_done(display_name, obj.api_test_case_task_id)

    @classmethod
    def stop_all_by_api_test_case_task_id(cls, display_name, api_test_case_task_id):
        """
        根据 api_test_case_task_id 停止所有子任务
        :param display_name: 请求用户
        :param api_test_case_task_id: 任务ID
        :return:
        """
        result, _ = cls.list(api_test_case_task_id=api_test_case_task_id, is_need_total=False)
        for task in result:
            if task.status not in ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FINAL_STATUS:
                cls.stop_task(display_name, task.id, check_status=False)
        ApiTestCaseService.stop_task(display_name, api_test_case_task_id)

    @classmethod
    @parameter_lock(index=2, prefix_key=LOCK_TEST_CASE_TASK_ID)
    def judge_is_all_is_done(cls, display_name, api_test_case_task_id):
        """
        判断所有子任务状态，然后更新父任务状态
        :param display_name: 请求用户
        :param api_test_case_task_id: 任务ID
        :return:
        """
        result, _ = cls.list(api_test_case_task_id=api_test_case_task_id, is_need_total=False)
        success_list = []
        status = ""
        result = list(result)
        is_break = False
        for task in result:
            if task.status == ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.PENDING:
                # 如果有排队中的,则查询是否任务是否存在celery中,直接退出,不更新父任务状态
                is_break = True
                break
            elif task.status == ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.STARTED:
                # 如果有started的，则直接退出,不更新父任务状态
                is_break = True
                break
            elif task.status == ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.REVOKED:
                # 如果有中止的，则父任务为中止
                status = ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.REVOKED
            elif task.status == ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FAILURE:
                # 如果有失败的，并且当前状态不是中止，父状态为失败
                if status != ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.REVOKED:
                    status = ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FAILURE
            elif task.status == ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.SUCCESS:
                # 如果全是成功，父状态为成功
                success_list.append(task)
        if len(success_list) == len(result):
            status = ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.SUCCESS
        if not is_break:
            # 不是中途break出来的才更新父任务状态
            update_func_map = {
                ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FAILURE:
                    ApiTestCaseService.fail_task,
                ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.SUCCESS:
                    ApiTestCaseService.success_task,
                ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.REVOKED:
                    ApiTestCaseService.stop_task
            }
            if status in update_func_map:
                func = update_func_map.get(status)
                func(display_name, api_test_case_task_id)

    @classmethod
    def update_by_id_json(cls, mid, **kwargs):
        logging.info(f"更新{cls.dao.model.__name__},id:{mid},kwargs:{kwargs}")
        # 更新前， 检查是否存在该资源
        _obj = cls.get_by_id(mid)
        if "req_data" in kwargs:
            data = kwargs.pop("req_data")
            old_data = _obj.req_data
            old_data.update(data)
            kwargs["req_data"] = old_data

        cls.dao.update_by_id(mid, **kwargs)
        result = cls.get_by_id(mid)
        return result
