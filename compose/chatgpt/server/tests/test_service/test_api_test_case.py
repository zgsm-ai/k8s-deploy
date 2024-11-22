#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/3/20 14:25
"""
import random
import json
# from tests.mock.mock_api_docs import test_point, tested_api, pre_api_content, post_api_content
# from common.constant import ActionsConstant, GPTModelConstant
# from controllers.completion_helper import async_completion_main
from bot.apiBot import Chatbot
from tests.mock.mock_api_test import RESPONSE_TEXT, NEW_RESPONSE_TEXT, MERGE_RESPONSE_TEXT, \
    RESPONSE_TEXT_1, NEW_RESPONSE_TEXT_1, MERGE_RESPONSE_TEXT_1, MOCK_TEST_POINTS
from services.api_test.api_test_ai_helper import ApiAiHelper


# def test_ask_ai_gen_test_step():
#     ask_data = {
#         "tested_api": tested_api,
#         "pre_api_content": pre_api_content,
#         "post_api_content": post_api_content,
#         "test_point": test_point,
#         "display_name": "范立伟33139",
#         "stream": False,
#         "action": ActionsConstant.API_TEST_SINGLE_CASE,
#         "conversation_id": "",
#         "model": GPTModelConstant.GPT_4
#     }
#     completion = async_completion_main(ask_data)
#     print(completion)


def test_merge_completion_content():
    all_content = Chatbot.merge_completion_content(RESPONSE_TEXT, NEW_RESPONSE_TEXT)
    assert all_content == MERGE_RESPONSE_TEXT

    all_content = Chatbot.merge_completion_content(RESPONSE_TEXT_1, NEW_RESPONSE_TEXT_1)
    assert all_content == MERGE_RESPONSE_TEXT_1


def test_stream_extract_content():
    """测试流式提取测试点"""

    def random_substring_generator(input_string):
        remaining_parts = list(input_string)  # 将字符串转换为字符列表
        while remaining_parts:
            # 随机选择一个剩余的片段的长度
            part_length = random.randint(1, 20)
            # 生成并yield一个随机长度的片段
            part = ''.join(remaining_parts[:part_length])
            yield part
            # 更新剩余的片段
            remaining_parts = remaining_parts[part_length:]

    # 模拟一个流式生成器
    completion = random_substring_generator(MOCK_TEST_POINTS)
    result = []

    # 测试提取方法
    for i in ApiAiHelper.parse_json_list_stream(completion, "test_points"):
        result.append(i)

    test_points = json.loads(MOCK_TEST_POINTS)

    # 提取测试结果对比
    for raw_text, new_text in zip(test_points["test_points"], result):
        assert raw_text == new_text
