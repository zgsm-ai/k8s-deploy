#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/19 14:18
"""
import json
import logging

from flask import Blueprint, Response
from flask import request

from common.constant import ActionsConstant
from controllers.base import handle_validate
from services.ai_e2e.ai_e2e_case_task import AiE2ECaseTaskService
from services.dify_chat import DifyChatBot
from services.agents.agent_data_classes import ChatRequestData, make_cls_with_dict
from services.agents.context_helper import ContextHelper
from services.action.complation_service import CompletionService, UserGiveFeedbacks
from services.system.configuration_service import ConfigurationService
from common.helpers.application_context import ApplicationContext
from controllers.completion_helper import get_request_ide_data
from controllers.response_helper import Result

actions_v4 = Blueprint('actions_v4', __name__)


@actions_v4.route('/completion', methods=['POST'])
@handle_validate(CompletionService)
def completion(fields):
    """
    实现补全
    ---
    tags:
      - 补全
    responses:
      200:
        result: 流
    """
    conv_id = fields.pop("conversation_id")
    query = fields.pop("prompt")
    chatbot = DifyChatBot(conv_id)
    request_data = make_cls_with_dict(ChatRequestData, fields)
    result = chatbot.chat_stream(request_data, **fields)
    return Response(result, mimetype='text/event-stream', headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    })


@actions_v4.route('/chat_agent', methods=['POST'])
def chat_agent():
    """
    对话
    ---
    tags:
      - 补全
    responses:
      200:
        result: 流
    """
    fields = request.get_json()
    request_data = fields.copy()
    conv_id = fields.pop("conversation_id")
    action = fields.pop('action')
    code = fields.pop("code", "")
    username = ApplicationContext.get_current()
    if username:
        fields["user"] = username.display_name
        request_data = get_request_ide_data(request_data, username)
    logging.info(f"接收到chat_agent，action: {action}, conv_id: {conv_id}, username: {fields.get('user')}")
    chat_agent = DifyChatBot(conv_id)
    result = chat_agent.dispatch_execution_agent(code, action, request_data, **fields)
    return Response(result, mimetype='text/event-stream', headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    })

@actions_v4.route('/zhuge_ads', methods=['GET'])
def get_ads():
    """
    对话
    ---
    tags:
      - 补全
    responses:
      200:
        ads: 列表
    """
    return ConfigurationService.get_zhuge_ads()


@actions_v4.route('/give_like', methods=['POST'])
@handle_validate(UserGiveFeedbacks)
def give_like(fields):
    """
    用户点赞接口,同时处理dify和es平台
    注意:快捷指令没有点赞功能，因此无message_id
    ---
    tags:
      - 补全
    responses:
      200:
        result: 流
    
    """
    es_id = fields.pop("conversation_id")
    name = fields.pop("agent_name")
    username = ApplicationContext.get_current()
    if username:
        fields["user"] = username.display_name

    action = fields.pop("action", "chat")
    if action == ActionsConstant.E2E_CASE_GEN:
        res, status = AiE2ECaseTaskService.user_give_likes(es_id, **fields)
    else:
        user_agent = DifyChatBot(es_id)
        res, status = user_agent.user_give_likes(name, es_id, **fields)
    return Response(json.dumps(res), status=status, mimetype='application/json', headers={
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    })


@actions_v4.route('/user_feedbacks', methods=['POST'])
def user_feedbacks():
    """
    用户反馈
    ---
    tags:
      - 补全
    responses:
      200:
        res: 结果
    
    """
    try:
        status = 200
        request_data = request.get_json()
        if not request_data:
            res, status = {"error": "Invalid input: JSON data is required"}, 403
        es_id = request_data.get("conversation_id")
        accept_num = request_data.get("accept_num") or 0
        # 新增用户交互行为，兼容旧版本，不做字段校验
        behavior = request_data.get("behavior", "")
        if not es_id or not isinstance(es_id, str):
            res, status = {"error": "Invalid input: 'conversation_id' must be a non-empty string"}, 403
        if not isinstance(accept_num, int):
            res, status = {"error": "Invalid input: 'accept_num' must be an integer"}, 403

        action = request_data.get("action")
        if action == ActionsConstant.E2E_CASE_GEN:
            res = AiE2ECaseTaskService.user_give_feedbacks(es_id, accept_num, behavior,
                                                           request_data.get("code"))
        else:
            user_feedback = DifyChatBot(es_id)
            res = user_feedback.user_give_feedbacks(es_id, accept_num, behavior)
        return Response(json.dumps(res), status=status, mimetype='application/json', headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        })
    except Exception as e:
        return Response(json.dumps({"error": {e}}), status=500, mimetype='application/json', headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        })


@actions_v4.route('/agent/context', methods=['POST'])
def update_context():
    """
    更新用户上下文
    ---
    tags:
      - 补全
    responses:
      200:
        res: 结果
    
    """
    method = request.args.get("method")
    data = request.get_json()
    key = data.get("key")
    value = data.get("value", {})
    if not key:
        return Result.fail(message="key is required.")
    if method and method.upper() == "GET":
        return Result.success(data=ContextHelper.get_env_context(key))
    else:
        ContextHelper.update_env_context(key, value)
        return Result.success(message="update success")
