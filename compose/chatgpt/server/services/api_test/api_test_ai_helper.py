#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/5/18 15:53
"""
import json
import re
import logging
import uuid

import concurrent.futures

from collections import Counter

from common.constant import (
    ApiTestCaseConstant,
    GPTConstant,
    ActionsConstant,
    GPTModelConstant
)
from controllers.completion_helper import async_completion_main
from services.api_test.api_test_case_task_events_service import ApiTestCaseTaskEventsService

logger = logging.getLogger(__name__)


class ApiAiHelper:

    @staticmethod
    def get_ai_resp(task_id, ask_data, event_type, gen_eoliner_task_id=None):
        event_id = ApiTestCaseTaskEventsService.create(
            api_test_case_task_id=task_id,
            event_type=event_type,
            status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
            data={
                "req_data": ask_data
            },
            gen_eoliner_task_id=gen_eoliner_task_id
        )

        # 这里复用单测is_ut=True逻辑，保留模型获取使用gpt4
        completion = async_completion_main(ask_data)
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
                logger.info(f"{task_id}:{event_id} response_format解析失败：{response_text}")
                re_parse = True
        if re_parse:
            try:
                match = re.search(r'```json(.*?)\n(.*?)```', response_text, re.DOTALL)
                if not match:
                    raise Exception(f"json 正则未匹配到, task_id：{task_id}；{response_text}")
                match_tuple = match.groups()
                if not match_tuple or len(match_tuple) < 2:
                    msg = "获取AI结果失败,未解析到json内容"
                    ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=msg,
                                                               data={"response_text": response_text})
                    raise Exception(f"task_id：{task_id}；{msg}；{response_text}")
                data_obj = json.loads(match_tuple[1])
            except json.JSONDecodeError:
                msg = "获取AI结果失败,解析json失败"
                ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=msg, data={"response_text": response_text})
                raise Exception(f"task_id：{task_id}；{msg}；{response_text}")
        ApiTestCaseTaskEventsService.event_to_done(event_id,
                                                   remark="AI生成完成",
                                                   data={"response_text": response_text, "data_obj": data_obj})
        return data_obj

    @staticmethod
    def get_ai_resp_stream(task_id, ask_data, event_type, gen_eoliner_task_id=None):
        event_id = ApiTestCaseTaskEventsService.create(
            api_test_case_task_id=task_id,
            event_type=event_type,
            status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
            data={
                "req_data": ask_data
            },
            remark="AI正在流式生成",
            gen_eoliner_task_id=gen_eoliner_task_id
        )

        completion = async_completion_main(ask_data)
        return completion, event_id

    @staticmethod
    def get_points_stream(task_id, ask_data):
        """
        请求ai流式获取测试点
        :param task_id: 任务ID
        :param ask_data: 询问AI数据
        :return: 测试点生成器
        """
        logger.info(f'execute_api_testcases_task 开始流式询问AI测试点; task_id: {task_id}')
        completion, event_id = ApiAiHelper. \
            get_ai_resp_stream(task_id, ask_data, ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_TEST_POINTS)

        def partial_event_done(content):
            """
            更新事件状态,位置不能修改, 依赖于上面的event_id
            """
            data = {"response_text": content}
            ApiTestCaseTaskEventsService.event_to_done(event_id, remark="AI流式输出完成", data=data)

        test_points = ApiAiHelper.parse_json_list_stream(completion, "test_points", callback=partial_event_done)
        logger.info(f'execute_api_testcases_task 成功询问AI测试点; task_id: {task_id}')
        return test_points

    @staticmethod
    def parse_json_list_stream(json_input_stream, list_title: str, callback=None):
        """
        解析json流式输出内容,预期数据是一个字典,key是一个标题,value是一个字符串列表，该方法的目的是提取出列表的每一个字符串，yield出来
        例如: {
            "test_points":
            ["测试点1", "测试点2"]
        }
        :param json_input_stream: 流式生成器
        :param list_title: 列表标题
        :param callback: 流式结束后的回调函数
        :return:
        """
        line = []
        all_content = ""
        for chunk in json_input_stream:
            all_content += chunk
            if '\n' in chunk:
                chunk_parts = chunk.split('\n')
                line.append(chunk_parts[0])
                line_str = ''.join(line).strip()
                raw_lines = [line_str] + chunk_parts[1:-1]
                for raw_line in raw_lines:
                    # 匹配以 " 开头，并且以 " 或者 ", 结尾的字符串
                    match = re.search(r'^"(.*?)("|",)$', raw_line)
                    if match:
                        line_str = match.group(1)
                        if line_str != list_title:
                            yield line_str
                # 放回line中
                line = chunk_parts[-1:]
            else:
                line.append(chunk)
        if callback and callable(callback):
            callback(all_content)


class ApiOdgAiHelper:

    @classmethod
    def gen(cls,
            tested_api,
            other_api,
            display_name,
            task_id):
        """
        并发3个线程生成ODG，选取结果相同的
        :param tested_api: 测试API
        :param other_api: 其他API
        :param display_name: 显示用户名称
        :param task_id: 任务ID
        :return: odg依赖图
        """
        results = []
        # 并发3次访问ai，获取所有返回值，取返回值相同的
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交任务并获取 Future 对象
            futures = [
                executor.submit(
                    cls.ask_ai, tested_api, other_api, display_name, task_id
                ) for _ in range(3)
            ]

            # 获取每个线程的执行结果
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

        # 用Counter计算
        counter = Counter(results)
        # 找出出现相同个数最多的元素和出现的次数
        odg_str, count = counter.most_common(1)[0]
        logger.info(f'{task_id}:{display_name} 生成ODG: {odg_str} 出现次数: {count}')
        if count == 1:
            # 如果都不相同, 则取长度最长的
            odg_str = max(results, key=len)

        return odg_str

    @classmethod
    def ask_ai(cls,
               tested_api,
               other_api,
               display_name,
               task_id):
        """
        生成ODG
        :param tested_api: 测试API
        :param other_api: 其他API
        :param display_name: 显示用户名称
        :param task_id: 任务ID
        :return: odg依赖图
        """
        ask_data = {
            "target_api": tested_api,
            "other_api": other_api,
            "display_name": display_name,
            "stream": False,
            "action": ActionsConstant.API_TEST_GEN_ODG,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        data_obj = ApiAiHelper.get_ai_resp(task_id, ask_data,
                                           ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_API_ODG)
        return data_obj.get('odg')
