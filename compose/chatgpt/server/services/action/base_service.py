#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 陈烜 42766
    :更新时间: 2023/3/24 14:12
"""
import logging
import re
import json

from common.utils.util import mock_stream_content
from config import conf
from common.constant import GPTModelConstant, ActionsConstant
from bot.apiBot import Chatbot as apiBot
from bot.cache import get_redis
from typing import Dict, List
from dataclasses import dataclass, asdict
from services.agents.agent_data_classes import ChatRequestData

from services.system.configuration_service import ConfigurationService

logger = logging.getLogger(__name__)

def stream_error_response(func):
    """
    控制流式错误响应
    """

    def wrapper(*args, **kwargs):
        self_ = args[0]  # 类实例
        stream = args[2].stream
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if stream:
                self_.mock_stream = True
                self_.resp_headers['mock_stream'] = 1
                return mock_stream_content(str(e))
            raise e

    return wrapper

class ChatbotOptions:
    """
    对话设置
    """
    def __init__(self, data: Dict[str, any] = None):
        if not data:
            data = {}
        # self.raw_data = data
        # 请求配置
        self.stream: bool = data.get('stream', False)
        # 指定LLM生成数据的选项参数
        self.temperature: int = data.get('temperature', 0)
        # 本轮对话使用的模型：GPTModelConstant.GPT_TURBO
        self.model: str = data.get('model', '')
        # 是否保留上下文
        self.context_association: bool = data.get('context_association', True)
        # 自定义预置
        systems = data.get("systems", list())
        if isinstance(systems, str):
            systems = [systems]
        self.systems: List[str] = systems

class ActionStrategy:
    name = "base"

    def __init__(self):
        self.resp_headers = {}

    @staticmethod
    def format_prompt_string(string):
        return '{{' + str(string) + '}}'

    def get_prompt_template(self, attribute_key: str = '') -> str:
        """
        default_prompt_template: 兼容同一Action类有多prompt场景
        """
        attribute_key = attribute_key if attribute_key else self.name
        prompt_template = ConfigurationService.get_prompt_template(attribute_key=attribute_key)
        return prompt_template

    @staticmethod
    def check_prompt(prompt):
        pass

    @staticmethod
    def get_default_options():
        return ChatbotOptions()

    def get_model(self, options: ChatbotOptions = None):
        return options.model or ConfigurationService.get_model_ide_normal(self.name)

    def get_api_key(self, options: ChatbotOptions = None):
        return conf.get("openai_api_key")

    def get_systems(self, data: ChatRequestData = None, options: ChatbotOptions = None):
        options = options or self.get_default_options()
        return options.systems

    def get_conversation_db(self, options: ChatbotOptions = None):
        return get_redis(conf)

    def make_chatbot(self, data: ChatRequestData = None, options: ChatbotOptions = None):
        return apiBot(redis=self.get_conversation_db(options),
                      model=self.get_model(options),
                      systems=self.get_systems(data, options))

    def ask(self, data: ChatRequestData, options: ChatbotOptions = None):
        options = options or self.get_default_options()
        chatbot = self.make_chatbot(data, options)
        conversation_id = self.get_conversation_id(data)

        self.check_prompt(data.prompt)
        logger.info(f"ask(): prompt: {data.prompt}")
        logger.info(f"ask(): data: {json.dumps(data.__dict__)}")
        logger.info(f"ask(): options: {json.dumps(options.__dict__)}")
        if options.stream:
            func = chatbot.ask_stream
        else:
            func = chatbot.ask
        return func(data.prompt,
                    temperature=options.temperature,
                    conversation_id=conversation_id,
                    context_association=options.context_association,
                    request_data=data.to_dict())

    def make_result(self, data: ChatRequestData, options: ChatbotOptions = None):
        return self.ask(data, options=options)

    def get_conversation_id(self, data: ChatRequestData):
        return data.conversation_id

    def get_prompt(self, data: ChatRequestData):
        return data.prompt


def process_code_retract(request_data, code):
    if not code:
        return code
    try:
        source_first_line = next((v for v in request_data.code.splitlines() if v.strip()), '')  # 输入代码非空首行
        if '\t' in source_first_line:
            return code  # 输入代码含制表符，不做缩进处理
        source_strip_count = len(source_first_line) - len(source_first_line.lstrip())  # 空格数
        first_line = next((v for v in code.splitlines() if v.strip()), '')
        res_strip_count = len(first_line) - len(first_line.lstrip())
        offset = source_strip_count - res_strip_count
        new_code = None
        if offset > 0:
            new_code = '\n'.join(list(map(lambda line: ' ' * offset + line, code.splitlines())))
        elif offset < 0:
            new_code = '\n'.join(list(
                map(lambda line: line[-offset:] if line.startswith(' ' * -offset) else line,
                    code.splitlines())))

        if new_code is not None:
            if code.endswith('\n') and not new_code.endswith('\n'):
                new_code += '\n'
            return new_code
    except Exception as e:
        logger.error('缩进处理异常', e)
    return code


# 处理返回代码缩进
def process_retract(func):
    def inner(*args, **kwargs):
        res = func(*args, **kwargs)
        try:
            response_content = res['choices'][0]['message']['content']
            data = args[1]
            if data.code and response_content:
                match = re.search(r'```(.*?)\n(.*?)```', response_content, re.DOTALL)
                match_tuple = match.groups()
                if len(match_tuple) == 2:
                    code = match_tuple[1]
                    new_code = process_code_retract(data, code)
                    if new_code != code:
                        if code.endswith('\n') and not new_code.endswith('\n'):
                            new_code += '\n'
                        res['choices'][0]['message']['content'] = response_content.replace(code, new_code)
        except Exception as e:
            logger.error('缩进处理异常', e)
        return res

    return inner
