#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/24 14:37
"""
import base64
import logging
import re
import traceback

from typing import Iterator, Callable
from functools import partial

from tenacity import (
    retry,
    stop_after_attempt,
    RetryError
)

from dao.ai_e2e.ai_e2e_case_task_dao import AiE2ECaseTaskDao, AiE2ECaseTaskEventsDao
from services.ai_e2e.robot_parser import E2ERobotParser
from services.base_service import BaseService
from services.ai_e2e.manual_case import ManualCase
from services.ai_e2e.ai_req_helper import AiResultHandle
from common.exception.exceptions import ManualCaseError
from common.constant import AiE2ECaseConstant
from common.utils.util import random_completion_id
from services.ai_e2e.e2e_context import CaseContextAssembly
from services.ai_e2e.chunk_helper import ChunkHelper
from services.system.configuration_service import ConfigurationService
from third_platform.es.chat_messages.prompt_es_service import prompt_es_service
from third_platform.tp.tp_manager import TpManager

logger = logging.getLogger(__name__)


class AiE2ECaseTaskService(BaseService):
    AGENT_NAME = "E2E自动化用例助手"
    AGENT_ID = "e2e_case_assistant"

    # 检查用例阶段
    NODE_CHECK_CASE = AiE2ECaseConstant.NODE_CHECK_CASE

    # 手工用例步骤和期望结果识别
    NODE_IDENTIFY_RELATIONSHIPS = AiE2ECaseConstant.NODE_IDENTIFY_RELATIONSHIPS

    # 手工步骤意图提取
    NODE_INTENT_EXTRACT = AiE2ECaseConstant.NODE_INTENT_EXTRACT

    # 检查上下文阶段
    NODE_KNOWLEDGE_SEEKER = AiE2ECaseConstant.NODE_KNOWLEDGE_SEEKER

    # 检查过滤结果
    NODE_RAG_FILTER = AiE2ECaseConstant.NODE_RAG_FILTER

    # 检查过滤结果
    NODE_GEN_CASE = AiE2ECaseConstant.NODE_GEN_CASE

    dao = AiE2ECaseTaskDao

    prefix = "TP-"

    @classmethod
    def check_input(cls, user_input: str):
        """
        校验输入参数
        """
        if not user_input:
            return False, {"msg": "输入字符串不能为空"}
        # 切割前缀
        if not user_input.startswith(cls.prefix):
            return False, {"msg": "输入字符串格式不匹配"}

        user_input = user_input[len(cls.prefix):]

        # base64解码
        decoded_str = base64.b64decode(user_input.encode('utf-8')).decode('utf-8')
        # 解析json
        input_data = eval(decoded_str)
        project_id = input_data.get("project_id")
        case_id = input_data.get("case_id")
        version_id = input_data.get("version_id")
        product_name = input_data.get("product_name")
        if not project_id or not case_id or not version_id or not product_name:
            return False, {"msg": "输入字符串格式不匹配"}
        return True, input_data

    @classmethod
    def make_result_by_ide(cls, data):
        user_input = data.get("prompt", "")
        result, input_data = cls.check_input(user_input)
        if not result:
            logger.error(f"E2E参数校验未通过：{user_input}， error: {input_data.get('msg')}")
            yield ChunkHelper.dify_error(
                data=input_data.get("msg"),
            )
        project_id = input_data.get("project_id")
        case_id = input_data.get("case_id")
        version_id = input_data.get("version_id")
        product_name = input_data.get("product_name")

        try:
            case_info = TpManager.get_case_info(case_id, project_id, version_id)
            case_info["display_name"] = data["username"] or ""
            case_info["case_id"] = case_info["id"]
            case_info["case_name"] = case_info["name"] or ""
            case_info["case_pre_step"] = case_info["doc_pre"] or ""
            case_info["case_step"] = case_info["doc_step"] or ""
            case_info["case_expect"] = case_info["doc_except"] or ""
            case_info["case_post_step"] = case_info["doc_post"] or ""
            case_info["case_remark"] = case_info["doc"] or ""
            case_info["case_level"] = case_info["priority"] or ""
            case_info["product_id"] = project_id
            case_info["product_name"] = product_name

            dir_code = case_info.get("parent_code")
            case_path_info = TpManager.get_case_path(case_id, project_id, version_id, dir_code)
            case_info["case_module"] = case_path_info["path"]
        except Exception as e:
            logger.error(f"E2E获取用例信息异常，"
                         f"project_id:{project_id}, case_id:{case_id}, version_id:{version_id}, error: {e}")
            yield ChunkHelper.dify_error(
                data=f"获取用例信息异常，错误信息：{e}",
            )
            return

        try:
            manual_case = ManualCase(**case_info)
        except Exception as e:
            logger.error(f"E2E初始化参数异常，{e}")
            yield ChunkHelper.dify_error(
                data="获取用例的信息缺少关键信息",
            )
            return
        # full_data = ""
        res = cls.start_generate_case(manual_case, data.get("conversation_id", ""))
        for chunk_data in res:
            if chunk_data:
                yield chunk_data
        # yield {"event": "sf_tokens", "total_answer": full_data}

    @classmethod
    def start_generate_case(cls, manual_case: ManualCase, conv_id: str = "") -> Iterator:
        """
        生成e2e自动化用例的主入口
        @param manual_case: 输入数据结构
        @param conv_id:
        @return: 流式输出生成器
        """
        es_id = conv_id
        if not conv_id:
            es_id = random_completion_id(AiE2ECaseConstant.ES_ID_TITLE)
        task = cls.create(
            display_name=manual_case.display_name,
            case_code=manual_case.case_code,
            case_id=manual_case.case_id,
            case_name=manual_case.case_name,
            case_pre_step=manual_case.case_pre_step,
            case_step=manual_case.case_step,
            case_expect=manual_case.case_expect,
            case_post_step=manual_case.case_post_step,
            case_level=manual_case.case_level,
            case_module=manual_case.case_module,
            product_id=manual_case.product_id,
            product_name=manual_case.product_name,
            case_remark=manual_case.case_remark,
            status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
            es_id=es_id
        )
        task_id = task.id
        event = None
        node = None
        try:
            yield ChunkHelper.workflow_started_chunk(cls.AGENT_NAME, cls.AGENT_ID, "开始执行")
            # 1. 校验用例内容是否需要生成
            yield ChunkHelper.node_started_chunk(
                data="*洞察：精准理解用例意图",
                **cls.NODE_INTENT_EXTRACT
            )
            event = AiE2ECaseTaskEventsService.create(
                ai_e2e_case_task_id=task_id,
                status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
                event_type=cls.NODE_CHECK_CASE["node_id"],
            )
            node = cls.NODE_CHECK_CASE
            # yield ChunkHelper.node_started_chunk(
            #     data="开始用例检查",
            #     **cls.NODE_CHECK_CASE
            # )
            event_callback = partial(cls.event_callback, event.id)
            cls.check_case(task_id, manual_case, event_callback)
            # yield ChunkHelper.node_finished_chunk(
            #     data="用例检查结束",
            #     **cls.NODE_CHECK_CASE
            # )
            AiE2ECaseTaskEventsService.success_task(event.id)

            # 2.手工用例步骤和期望结果关系识别
            node = cls.NODE_IDENTIFY_RELATIONSHIPS
            event = AiE2ECaseTaskEventsService.create(
                ai_e2e_case_task_id=task_id,
                status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
                event_type=cls.NODE_IDENTIFY_RELATIONSHIPS["node_id"],
            )
            # yield ChunkHelper.node_started_chunk(
            #     data="开始用例步骤和期望结果关系识别",
            #     **cls.NODE_IDENTIFY_RELATIONSHIPS
            # )
            event_callback = partial(cls.event_callback, event.id)
            cls.identify_relationships(task_id, manual_case, event_callback)
            # yield ChunkHelper.node_finished_chunk(
            #     data="用例步骤和期望结果关系识别结束",
            #     **cls.NODE_IDENTIFY_RELATIONSHIPS
            # )
            AiE2ECaseTaskEventsService.success_task(event.id)

            # 3. 手工用例步骤意图提取
            node = cls.NODE_INTENT_EXTRACT
            event = AiE2ECaseTaskEventsService.create(
                ai_e2e_case_task_id=task_id,
                status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
                event_type=cls.NODE_INTENT_EXTRACT["node_id"],
            )

            event_callback = partial(cls.event_callback, event.id)
            cls.extract_intent(task_id, manual_case, event_callback)
            AiE2ECaseTaskEventsService.success_task(event.id)
            yield ChunkHelper.node_finished_chunk(
                data="*洞察：精准理解用例意图",
                **cls.NODE_INTENT_EXTRACT
            )

            # 4. 单步骤检索相关步骤和关键字
            yield ChunkHelper.node_started_chunk(
                data="*识破：挑选自动化关键字",
                **cls.NODE_KNOWLEDGE_SEEKER
            )
            event = AiE2ECaseTaskEventsService.create(
                ai_e2e_case_task_id=task_id,
                status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
                event_type=cls.NODE_KNOWLEDGE_SEEKER["node_id"],
            )
            event_callback = partial(cls.event_callback, event.id)

            node = cls.NODE_KNOWLEDGE_SEEKER
            cca = CaseContextAssembly(manual_case, task_id)
            (test_case,
             associated_keywords,
             associated_steps,
             associated_cli,
             associated_api,
             associated_graph) = cca.context_assembly(event_callback)

            AiE2ECaseTaskEventsService.success_task(event.id)
            yield ChunkHelper.node_finished_chunk(
                data="*识破：挑选自动化关键字",
                **cls.NODE_KNOWLEDGE_SEEKER
            )
            # 5. 检索汇总，重排，过滤
            # event = AiE2ECaseTaskEventsService.create(
            #     ai_e2e_case_task_id=task_id,
            #     status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
            #     event_type=cls.NODE_RAG_FILTER["node_id"],
            # )
            # node = cls.NODE_RAG_FILTER
            # yield ChunkHelper.node_started_chunk(
            #     data="开始过滤结果",
            #     **cls.NODE_RAG_FILTER
            # )
            # # 待实现
            # yield ChunkHelper.node_finished_chunk(
            #     data="过滤结果结束",
            #     **cls.NODE_RAG_FILTER
            # )
            # AiE2ECaseTaskEventsService.success_task(event.id)

            # 5. 生成用例
            yield ChunkHelper.node_started_chunk(
                data="*乘胜追击：根据关键字，组装自动化用例",
                **cls.NODE_GEN_CASE
            )
            event = AiE2ECaseTaskEventsService.create(
                ai_e2e_case_task_id=task_id,
                status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED,
                event_type=cls.NODE_GEN_CASE["node_id"],
            )
            node = cls.NODE_GEN_CASE

            event_callback = partial(cls.event_callback, event.id)
            res = AiResultHandle.gen_e2e_case(
                task_id,
                manual_case,
                associated_keywords,
                associated_steps,
                associated_cli,
                associated_api,
                associated_graph,
                event_callback,
                es_id=es_id,
                display_name=manual_case.display_name
            )
            for chunk in res:
                if chunk.get("status") == "done":
                    after_handle_content = chunk.get("after_handle_content", "")
                    # 提取完整代码段
                    pattern = r'```(.*?)\n(.*?)```'
                    match = re.search(pattern, after_handle_content, re.DOTALL)
                    if match:
                        full_code = match.groups()[1]
                    else:
                        full_code = after_handle_content
                    template_data = E2ERobotParser(
                        full_code,
                        associated_api,
                        associated_cli,
                        associated_keywords
                    ).get_template_data()
                    yield ChunkHelper.node_diff_chunk(
                        data=template_data,
                        language="robot",
                        title=manual_case.case_name,
                        **cls.NODE_GEN_CASE
                    )
                    continue
                yield ChunkHelper.message_chunk(data=chunk.get("data", ""), task_id=task_id, **cls.NODE_GEN_CASE)

            AiE2ECaseTaskEventsService.success_task(event.id)
            yield ChunkHelper.node_finished_chunk(
                data="*乘胜追击：根据关键字，组装自动化用例",
                **cls.NODE_GEN_CASE
            )
            yield ChunkHelper.workflow_finished_chunk(cls.AGENT_NAME, cls.AGENT_ID, "执行结束")
            AiE2ECaseTaskService.success_task(task_id)
        except Exception as err:
            try:
                err_info = f"生成e2e用例失败，task: {task_id}, 堆栈： {traceback.format_exc()}"
                if isinstance(err, ManualCaseError):
                    err_data = f"手工用例意图识别失败[用例ID({manual_case.case_code})]：\n" + str(err)
                    # yield ChunkHelper.dify_error(
                    #     data=err_data
                    # )
                    if node:
                        yield ChunkHelper.node_fail_chunk(
                            data=err_data,
                            **node
                        )
                else:
                    err_data = "悟空受伤啦：" + str(err)
                    yield ChunkHelper.dify_error(
                        data=err_data
                    )
                    logger.error(err_info)
                if event:
                    AiE2ECaseTaskEventsService.fail_task(event.id, remark=err_info)
                yield ChunkHelper.workflow_fail_chunk(cls.AGENT_NAME, cls.AGENT_ID, err_data)
                AiE2ECaseTaskService.fail_task(task_id, remark=err_info)
            except Exception:
                err_info = f"生成e2e用例失败，task: {task_id}, 堆栈： {traceback.format_exc()}"
                logger.error(err_info)
                yield ChunkHelper.workflow_fail_chunk(cls.AGENT_NAME, cls.AGENT_ID, "AI生成失败，请稍后重试")
                AiE2ECaseTaskService.fail_task(task_id, remark=err_info)

    @classmethod
    def event_callback(cls, event_id: int, **kwargs):
        AiE2ECaseTaskEventsService.update_by_id_json(event_id, data=kwargs)

    @classmethod
    def identify_relationships(cls, task_id: int, manual_case: ManualCase, callback: Callable = None):
        try:
            cls._identify_relationships(task_id, manual_case, callback)
        except RetryError:
            raise ManualCaseError("手工用例步骤和期望结果关系识别失败，请完善步骤和期望结果的关系")

    @classmethod
    @retry(stop=stop_after_attempt(2))
    def _identify_relationships(cls, task_id: int, manual_case: ManualCase, callback: Callable = None):
        # result 为 二维数组，step 和 expect 对应关系的下标为一组，不存在expect的结果为 ""
        result = AiResultHandle.identify_relationships(task_id, manual_case, callback)
        manual_case.set_step_map_expect(result)

    @classmethod
    def check_case(cls, task_id: int, manual_case: ManualCase, callback: Callable = None):
        """
        检查用例内容是否完整
        @param callback: 回调函数，用来记录过程数据
        @param task_id: 任务id
        @param manual_case: 手工用例
        @return:
        """
        # 直接检查字符长度
        manual_case.check_step()
        is_check, min_score = ConfigurationService.get_check_e2e_case_config()
        if is_check:
            # ai检测内容是否完善
            score, section = AiResultHandle.check_case(task_id, manual_case, callback)
            if score < min_score:
                # 评分小于阈值，则报错
                msg = ""
                pre_score = section.get("pre", "")
                step_score = section.get("step", "")
                expect_score = section.get("expect", "")
                post_score = section.get("post", "")
                if pre_score < min_score:
                    msg += f'{section.get("pre_assess", "")}\n'
                if step_score < min_score:
                    msg += f'{section.get("step_assess", "")}\n'
                if expect_score < min_score:
                    msg += f'{section.get("expect_assess", "")}\n'
                if post_score < min_score:
                    msg += f'{section.get("post_assess", "")}\n'
                if not msg:
                    logger.error(f"用例评分: {section}")
                    msg = "用例内容描述不清晰，请完善用户信息"
                raise ManualCaseError(f"{msg}")

    @classmethod
    def extract_intent(cls, task_id: int, manual_case: ManualCase, callback: Callable = None):
        """
        提取手工用例步骤意图
        @param callback: 回调函数，用来记录过程数据
        @param task_id: 任务id
        @param manual_case: 手工用例
        @return:
        """
        step_desc = manual_case.convert_to_step_dict()
        # 提取手工用例步骤意图
        result = AiResultHandle.extract_intent(task_id, step_desc, callback, display_name=manual_case.display_name)
        # 将生成的结果按步骤进行缓存
        cache = {}
        for step_id, intent_list in result.items():
            if step_id in step_desc and isinstance(intent_list, list):
                cache[step_id] = []
                for intent in intent_list:
                    # intent_str = f"{intent.get('operate', '')}{intent.get('entity', '')}"
                    cache[step_id].append(intent)
        manual_case.set_case_intent_cache(cache)

    @classmethod
    def start_task(cls, task_id: int, **kwargs):
        """
        任务开始
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED, **kwargs)

    @classmethod
    def stop_task(cls, task_id: int, **kwargs):
        """
        中止任务
        :param task_id: 任务ID
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.REVOKED, **kwargs)

    @classmethod
    def fail_task(cls, task_id: int, **kwargs):
        """
        任务失败
        :param task_id: 任务ID
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.FAILURE, **kwargs)

    @classmethod
    def success_task(cls, task_id: int, **kwargs):
        """
        任务成功
        :param task_id: 任务ID
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.SUCCESS, **kwargs)

    @classmethod
    def accept(cls, task_id: int, accept_type: str, accept_content: str):
        """
        接受生成结果
        :param task_id: 任务id
        :param accept_type: 接受类型
        :param accept_content: 接受内容
        :return:
        """
        # 更新任务状态
        accept_num = len(accept_content.splitlines())
        task = cls.update_by_id(
            task_id, accept_type=accept_type,
            accept_content=accept_content,
            accept_num=accept_num,
        )
        # 更新es
        prompt_es_service.update_by_id(task.es_id, {
            "is_accept": True,
            "accept_num": accept_num,
            "code": accept_content
        })

    @staticmethod
    def user_give_likes(es_id: str, **fields):
        """
        用户点赞处理，更新es平台
        es_id:es平台对应的id
        """
        # 更新es平台的字段
        # 更新es
        prompt_es_service.update_by_id(es_id, {'feedbacks': fields.get('rating', '')})
        return {"es_status": "The es platform is updated successfully!"}, 200

    @classmethod
    def user_give_feedbacks(cls, es_id: str, accept_num: int, behavior: str, accept_content: str):
        """
        处理用户采纳结果,用户每一次的交互行为都要记录下来
        es_id:es平台id
        accept_num:用户采纳行数
        """
        try:
            # 如果是查看变更，且没有接受行，不更新实际数据
            if behavior == "diff" and accept_num <= 0:
                return {"es_status": "Successful"}

            # 更新任务状态
            task_query, _ = cls.list(es_id=es_id, is_need_total=False)
            if task_query:
                # 如果没有旧的数据大，则不更新
                old_accept_num = task_query[0].accept_num or 0
                if old_accept_num > accept_num:
                    return {"es_status": "Successful"}
                cls.update_by_id(
                    task_query[0].id, accept_type=behavior,
                    accept_content=accept_content,
                    accept_num=accept_num,
                )
            # 更新es
            prompt_es_service.update_by_id(es_id, {
                "is_accept": True,
                "accept_type": behavior,
                "accept_num": accept_num,
                "accept_content": accept_content
            })
            return {"es_status": "Successful"}
        except Exception as err:
            logger.error(f"es更新ide_data数据失败，失败日志： {str(err)}")
            return {"es_status": "Failed"}


class AiE2ECaseTaskEventsService(BaseService):
    dao = AiE2ECaseTaskEventsDao

    @classmethod
    def update_by_id_json(cls, mid, **kwargs):
        # logging.info(f"更新{cls.dao.model.__name__},id:{mid},kwargs:{kwargs}")
        # 更新前， 检查是否存在该资源
        _obj = cls.get_by_id(mid)
        if "data" in kwargs:
            data = kwargs.pop("data")
            old_data = _obj.data
            old_data.update(data)
            kwargs["data"] = old_data

        cls.dao.update_by_id(mid, **kwargs)
        result = cls.get_by_id(mid)
        return result

    @classmethod
    def start_task(cls, task_id, **kwargs):
        """
        任务开始
        :param task_id: 任务ID
        :param kwargs: 其他同步需要修改的参数
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.STARTED, **kwargs)

    @classmethod
    def stop_task(cls, task_id, **kwargs):
        """
        中止任务
        :param task_id: 任务ID
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.REVOKED, **kwargs)

    @classmethod
    def fail_task(cls, task_id, **kwargs):
        """
        任务失败
        :param task_id: 任务ID
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.FAILURE, **kwargs)

    @classmethod
    def success_task(cls, task_id, **kwargs):
        """
        任务成功
        :param task_id: 任务ID
        :return:
        """
        # 更新任务状态
        cls.update_by_id(task_id, status=AiE2ECaseConstant.AiE2ECaseTaskStatus.SUCCESS, **kwargs)
