#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/23 16:29
"""
import logging
import time
from multiprocessing import Process

from flask import request, g, Response, make_response, jsonify

from bot.bot_util import get_chat_model
from common.constant import GPTConstant
from common.helpers.application_context import ApplicationContext
from common.utils.util import process_code_just
from services.action import ChatbotOptions, get_action_strategy
from services.agents.agent_data_classes import ChatRequestData, make_cls_with_dict

logger = logging.getLogger(__name__)


def get_beta_keys():
    # beta 功能开关
    beta_keys = request.cookies.get('beta_keys', '')
    # 返回一个列表，逗号分隔，支持多种 beta 功能启用
    # 例如：gpt-4,custom-prompt
    return beta_keys.split(",")

def get_request_data(data, user):
    data['path'] = request.path
    data['user_agent'] = request.headers.get("User-Agent")
    data['host'] = request.headers.get("Host")
    data['display_name'] = user.display_name

    # V3版本处理
    data['app_id'] = ApplicationContext.get_current_app_id()
    if data['app_id'] and data.get('system_prompt'):
        data['systems'] = data.pop('system_prompt')

    # review处理
    if data.get('review_type'):
        data['ide'] = request.headers.get('ide', '')
        data['ide_version'] = request.headers.get('ide-version', '')
        data['ide_real_version'] = request.headers.get('ide-real-version', '')
    return make_cls_with_dict(ChatRequestData, data)


def get_chatbot_options(data, user, is_ut: bool = False):
    if "context_association" not in data.keys():
        data["context_association"] = data.get("association", True)
    action = data.get('action', 'chat')  # v3接口不传action，默认chat
    data['model'] = get_chat_model(action=action, request_data=data, is_ut=is_ut)
    return ChatbotOptions(data)


def completion_main(request_data, is_ut: bool = False):
    user = g.current_user  # g对象直接获取当前用户信息
    data = get_request_data(request_data, user)
    options = get_chatbot_options(request_data, user, is_ut)
    strategy = get_action_strategy(data.action)
    result = strategy.make_result(data, options)

    if is_ut:
        return result

    # TODO: 这里可以简化下
    if options.stream:
        resp = Response(result, mimetype='text/plain')
        resp.headers.update(strategy.resp_headers)
        return resp
    else:
        # 若要求只返回代码，对其处理
        if request_data.get('code_only', False):
            result = process_code_just(result)
        resp = make_response(jsonify(result))
        resp.headers.update(strategy.resp_headers)
        return resp


def request_data_process(data: dict, user: dict) -> dict:
    """
    考虑异步执行gpt请求，不能使用请求上下文、传参需要可序列化，
    数据处理放至此，并返回dict类型
    """
    data['path'] = request.path
    data['user_agent'] = request.headers.get("User-Agent")
    data['host'] = request.headers.get("Host")
    data['display_name'] = user.get('display_name', '')

    data['ide'] = request.headers.get('ide', '')
    data['ide_version'] = request.headers.get('ide-version', '')
    data['ide_real_version'] = request.headers.get('ide-real-version', '')

    # 是否开启会话上下文，需与conversation_id结合使用
    if 'context_association' not in data.keys():
        data['context_association'] = data.get('association', True)

    # 选择模型
    action = data.get('action')
    data['model'] = get_chat_model(action=action, request_data=data)
    return data


# AIReview使用，避免异步内无法使用上下文
def async_completion_main(request_data: dict):
    data = make_cls_with_dict(ChatRequestData, request_data)
    options = ChatbotOptions(request_data)
    strategy = get_action_strategy(data.action)
    result = strategy.make_result(data, options)
    return result


# 子进程执行，控制超时时间
def child_process_execute_completion_main(request_data):
    task_process = Process(target=async_completion_main, args=(request_data,))
    task_process.start()
    cost_time = 0
    while task_process.is_alive():
        cost_time += 1
        if cost_time > GPTConstant.TIMEOUT:
            task_process.terminate()
            raise Exception(f'request gpt timeout {GPTConstant.TIMEOUT}s')
        time.sleep(1)


def get_request_ide_data(data, user) -> dict:
    """
    获取IDE插件传输的数据
    """
    data['user_agent'] = request.headers.get("User-Agent")
    data['host'] = request.headers.get("Host")
    data['host_ip'] = request.headers.get("host-ip", "")
    data['ide'] = request.headers.get('ide', '')
    data['ide_version'] = request.headers.get('ide-version', '')
    data['ide_real_version'] = request.headers.get('ide-real-version', '')
    data["path"] = request.url or "/chat_agent"
    data['username'] = user.username
    data['display_name'] = user.display_name
    return data
