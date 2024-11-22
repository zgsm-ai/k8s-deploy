#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/25 11:39
"""
import logging
import json
import re
import uuid

from typing import Tuple, Callable, Generator

from common.constant import (
    GPTConstant,
    ActionsConstant,
    GPTModelConstant
)
from controllers.completion_helper import async_completion_main
from services.ai_e2e.manual_case import ManualCase
from services.ai_e2e.result_handle import RobotResultHandle

logger = logging.getLogger(__name__)


class E2eAiHelper:
    @staticmethod
    def get_ai_resp(task_id: int, ask_data: dict):
        stream = ask_data.get("stream", False)
        completion = async_completion_main(ask_data)
        if stream:
            # 流式直接返回
            return completion
        response_text = completion['choices'][0].get('message', {}).get('content', '')
        # 是否用正则解析
        re_parse = True
        data_obj = {}
        if ask_data.get("response_format") == GPTConstant.RESPONSE_JSON_OBJECT:
            try:
                data_obj = json.loads(response_text)
                # 如果指定了response_format并且解析成功，则不用后续的正则解析
                re_parse = False
            except json.JSONDecodeError:
                logger.info(f"{task_id} response_format解析失败：{response_text}")
                re_parse = True
        if re_parse:
            try:
                match = re.search(r'```json(.*?)\n(.*?)```', response_text, re.DOTALL)
                if not match:
                    raise Exception(f"json 正则未匹配到, task_id：{task_id}；{response_text}")
                match_tuple = match.groups()
                if not match_tuple or len(match_tuple) < 2:
                    msg = "获取AI结果失败,未解析到json内容"
                    raise Exception(f"task_id：{task_id}；{msg}；{response_text}")
                data_obj = json.loads(match_tuple[1])
            except json.JSONDecodeError:
                msg = "获取AI结果失败,解析json失败"
                raise Exception(f"task_id：{task_id}；{msg}；{response_text}")
        return data_obj

    @classmethod
    def gen_e2e_case(cls,
                     task_id: int,
                     test_case: str,
                     associated_keywords: list,
                     associated_steps: list,
                     associated_cli: list,
                     associated_api: list,
                     associated_graph: list,
                     **kwargs
                     ):
        """
        生成e2e
        @param task_id: 任务ID
        @param test_case: 测试用例markdown
        @param associated_keywords: 关联的关键字
        @param associated_steps: 关联的步骤
        @param associated_cli: 关联的cli
        @param associated_api: 关联的api
        @param associated_graph: 用例步骤的关联信息
        @return:
        """
        ask_data = {
            "test_case": test_case,
            "associated_keywords": associated_keywords,
            "associated_steps": associated_steps,
            "associated_cli": associated_cli,
            "associated_api": associated_api,
            "associated_graph": associated_graph,
            "stream": True,
            "action": ActionsConstant.E2E_CASE_GEN,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            # "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        display_name = kwargs.get("display_name")
        if display_name:
            ask_data.update({"display_name": display_name})
        es_id = kwargs.get("es_id")
        if es_id:
            ask_data["extra_kwargs"] = {"id": es_id}
        data = E2eAiHelper.get_ai_resp(task_id, ask_data)
        return data


class AiResultHandle:

    @classmethod
    def gen_e2e_case(cls,
                     task_id: int,
                     manual_case: ManualCase,
                     associated_keywords: list,
                     associated_steps: list,
                     associated_cli: list,
                     associated_api: list,
                     associated_graph: list,
                     callback: Callable = None,
                     **kwargs
                     ):
        """
        生成e2e
        @param task_id: 任务ID
        @param manual_case: manual_case对象
        @param associated_keywords: 关联的关键字
        @param associated_steps: 关联的步骤
        @param associated_cli: 关联的cli
        @param associated_api: 关联的api
        @param associated_graph: 用例步骤的关联信息
        @param callback: 回调函数
        @return:
        """
        full_response = ''  # 完整响应
        full_code = ''  # 完整代码

        def gen_result() -> Generator:
            res = E2eAiHelper.gen_e2e_case(
                task_id,
                manual_case.format_markdown(),
                associated_keywords,
                associated_steps,
                associated_cli,
                associated_api,
                associated_graph,
                **kwargs
            )
            nonlocal full_response
            nonlocal full_code
            # is_block_code = False  # 是代码时再流式返回
            # content_temp = ''  # 暂存代码块标记 ``` （为兼容 ```分开返回场景）
            for content in res:
                full_response += content
                # 对接诸葛不需要单独将md格式数据拿出来，可在生成完后一次处理，先注释
                # if full_code and is_block_code is False:
                #     # 已返回过代码块
                #     continue
                # elif content in ['`', '``', '```']:
                #     # 暂存，先不返回
                #     content_temp += content
                #     continue
                #
                # elif is_block_code is False and re.search(r'^```(.+)\n', full_response):  # 代码块开始
                #     is_block_code = True
                #     # 把第一个换行前面的内容去除后返回
                #     temp = "\n".join(full_response.split("\n")[1:])
                #     full_code += temp
                #     content_temp = ''
                #     yield temp
                #     continue
                # elif is_block_code and re.search(r'```(\n)*$', full_response):
                #     # 代码块结束, 如果没有输出完，则切割后输出
                #     temp = content_temp + content
                #     code = temp.rsplit("```")[0]
                #     full_code += code
                #     content_temp = ""
                #     yield code
                #     is_block_code = False
                #
                # if is_block_code:
                #     if content_temp:
                #         # 此时不是作为代码块结束符，故返回
                #         content = content_temp + content
                #         content_temp = ''
                #     full_code += content
                # yield content
                yield content

            # 提取完整代码段
            pattern = r'```(.*?)\n(.*?)```'
            match = re.search(pattern, full_response, re.DOTALL)
            if match:
                full_code = match.groups()[1]
            else:
                full_code = ""

            # if not full_code and full_response:
            #     # 如果没有提取出代码, 但是原始信息有内容, 则把原始内容返回
            #     yield full_response

        # 替换字符处理
        obj = RobotResultHandle(gen_result(), manual_case)
        after_handle_content = ""
        for chunk in obj.handle():
            after_handle_content += chunk
            yield {"data": chunk, "status": "ongoing"}

        yield {
            "full_code": full_code,
            "full_response": full_response,
            "after_handle_content": after_handle_content,
            "status": "done"
        }

        if callback:
            callback(full_code=full_code, full_response=full_response, after_handle_content=after_handle_content)

    @classmethod
    def check_case(cls, task_id: int, manual_case: ManualCase, callback: Callable = None) -> Tuple[bool, dict]:
        """
        检查手工用例
        @param callback: 回调函数
        @param task_id:
        @param manual_case:
        @return: 用例评分以及每个部分的评分和评价
        {
            "score": 10,
            "section": {
                "pre_assess": "",
                "pre": 10,
                "step_assess": "",
                "step": 10,
                "expect_assess": "",
                "expect": 10,
                "post_assess": "",
                "post": 10
            }
        }
        """
        ask_data = {
            "test_case": manual_case.format_markdown(only_step=True),
            "stream": False,
            "action": ActionsConstant.E2E_MANUAL_CASE_CHECK,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        data_obj = E2eAiHelper.get_ai_resp(task_id, ask_data)
        if callback:
            callback(ask_data=ask_data, res=data_obj)
        return data_obj['score'], data_obj['section']

    @classmethod
    def identify_relationships(cls, task_id: int, manual_case: ManualCase, callback: Callable = None, **kwargs) -> list:
        """
        识别手工用例步骤和对应的期望结果
        @param callback: 回调函数
        @param task_id:
        @param manual_case:
        @return: 二维数组，step 和 expect 对应关系的下标为一组，不存在expect的结果为 "-"
        """
        ask_data = {
            "step_desc": manual_case.steps_list,
            "expect_result": manual_case.expect_list,
            "stream": False,
            "action": ActionsConstant.E2E_IDENTIFY_RELATIONSHIPS,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        display_name = kwargs.get("display_name")
        if display_name:
            ask_data.update({"display_name": display_name})
        data_obj = E2eAiHelper.get_ai_resp(task_id, ask_data)
        if callback:
            callback(ask_data=ask_data, res=data_obj)
        return data_obj["result"]

    @classmethod
    def extract_intent(cls, task_id: int, step_desc: dict, callback: Callable = None, **kwargs) -> dict:
        """
        提取用例的步骤操作
        @param callback: 回调函数
        @param task_id:
        @param step_desc: 步骤描述字典
        @return: 结果
        """
        ask_data = {
            "step_desc": step_desc,
            "stream": False,
            "action": ActionsConstant.E2E_STEP_INTENT_EXTRACT,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        display_name = kwargs.get("display_name")
        if display_name:
            ask_data.update({"display_name": display_name})
        data_obj = E2eAiHelper.get_ai_resp(task_id, ask_data)
        if callback:
            callback(ask_data=ask_data, res=data_obj)
        return data_obj
