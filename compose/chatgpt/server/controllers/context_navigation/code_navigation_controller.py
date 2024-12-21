#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from flask import Blueprint, request

from common.helpers.application_context import ApplicationContext
from common.helpers.response_helper import Result
from services.context_navigation.code_navigation_service import CodeNavigationService

logger = logging.getLogger(__name__)
code_navigation = Blueprint("code_navigation", __name__)


@code_navigation.route("/cache_context", methods=["POST"])
def cache_context():
    """
    接口功能：用于缓存sdk传递过来的上下文
    返回参数：
    - result: 结果
    ---
    tags:
      - 代码上下文
    responses:
      200:
        res: 结果
    """
    data = request.get_json()
    user = ApplicationContext.get_current()
    data["display_name"] = user.display_name if user and user.display_name else ""
    data["username"] = user.username if user and user.username else ""
    # 这里内容很大，就不打印了；需要估算下字符数，服务于排查异常
    logger.info(f'接收到sdk的初始上下文，请求内容是：{len(str(data))}，用户：{data["username"]}')
    context_uuid = CodeNavigationService.cache_context(data)
    return Result.success(message="获取成功", data=context_uuid)


@code_navigation.route("/get_specified_context", methods=["POST"])
def get_specified_context():
    """
    定义Flask路由/get_specified_context的处理函数，该函数处理POST请求并获取上下文数据
    返回:
        成功获取上下文数据的响应
    ---
    tags:
      - 代码上下文
    responses:
      200:
        res: 结果
    """
    data = request.get_json()
    user = ApplicationContext.get_current()
    username = user.username if user and user.username else ""
    # 1.存储到redis，以这个做key
    chat_id = data.get("chat_id", "")
    logger.info(f"接收到用户获取上下文请求，请求内容是：{data}, 用户：{username}，chat_id：{chat_id}")
    # 2.除了conversation_id，考虑到后续的扩展性，其他原封不动发给sdk，sdk处理这块
    CodeNavigationService.specified_context_request(data, chat_id)
    # 3.等待用户的数据抵达服务端
    data = CodeNavigationService.get_specified_context_content(chat_id)
    logger.info(f"上下文结果：{len(str(data))}，chat_id：{chat_id}")
    return Result.success(data=data)


@code_navigation.route("/specified_context_result", methods=["POST"])
def specified_context_result():
    """
    定义Flask API端点receive_specified_context, 接收并处理客户上下文内容
    处理步骤包括：
        - 从请求中获取JSON数据
        - 获取当前用户信息，用于记录日志
        - 将上下文内容存储到redis中
    接收参数:
        通过POST方法接收指定上下文的JSON数据
    返回:
        使用统一的Result类返回处理的结果
    ---
    tags:
      - 代码上下文
    responses:
      200:
        res: 结果
    """
    data = request.get_json()
    user = ApplicationContext.get_current()
    username = user.username if user and user.username else ""
    # 1.存储到redis，以这个做uuid，加前缀规避对话的chat_id
    chat_id = data.pop("chat_id", "")
    logger.info(f"接收到sdk上下文内容，请求内容长度是：{len(str(data))}, 用户：{username}，chat_id：{chat_id}")
    context = data.pop("context", "")
    CodeNavigationService.cache_specified_context_content(context, chat_id)
    return Result.success()
