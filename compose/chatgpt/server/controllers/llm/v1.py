#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from functools import wraps

from flask import request, Response, Blueprint, stream_with_context

from common.exception.exceptions import AuthFailError
from common.utils.date_util import DateUtil
from common.utils.util import generate_uuid
from services.llm.llm_service import LLMService
from services.system.application_service import ApplicationService

v1 = Blueprint('v1', __name__)


def check_application_key(func):
    """application_key合法性"""

    @wraps(func)
    def inner(*args, **kwargs):
        api_key = ""
        if "api-key" in request.headers:
            api_key = request.headers.get('api-key')
        elif "Authorization" in request.headers:
            authorization = request.headers.get('Authorization')
            if authorization.startswith("Bearer "):
                api_key = authorization.replace("Bearer ", "")
        if not api_key:
            raise AuthFailError('header lack api-key')

        application = ApplicationService.dao.get_by_application_key(api_key)
        if not application:
            raise AuthFailError('api-key invalid')
        request.json['application_name'] = application.application_name
        request.json['application_key'] = application.application_key
        conversation_id = request.headers.get('conversation-id')
        if not conversation_id:
            conversation_id = generate_uuid()
        request.json['conversation_id'] = conversation_id
        request.json['request_id'] = generate_uuid()

        return func(*args, **kwargs)

    return inner


@v1.route('/chat/completions', methods=['POST'])
@check_application_key
def chat_completion():
    """
    补全
    ---
    tags:
      - LLM
    responses:
      200:
        res: 结果
    """
    kw = request.json
    logging.info(f'received request, request_id:{kw.get("request_id")}, now_time:{DateUtil.get_now_yyyymmddhhmmss()}')
    result = LLMService.chat_completion(**kw)
    if kw.get("stream"):
        resp = Response(stream_with_context(result), mimetype='text/event-stream', headers={
            "Content-Type": "text/event-stream",
        })
    else:
        resp = Response(result, mimetype='application/json')

    resp.headers['conversation-id'] = kw.get("conversation_id")
    resp.headers['request_id'] = kw.get("request_id")
    logging.info(f'end request, request_id:{kw.get("request_id")}, now_time:{DateUtil.get_now_yyyymmddhhmmss()}')
    return resp


@v1.route('/completions', methods=['POST'])
@check_application_key
def completions():
    """
    补全
    ---
    tags:
      - LLM
    responses:
      200:
        res: 结果
    """
    kw = request.json
    result = LLMService.completions(**kw)
    if kw.get("stream"):
        resp = Response(stream_with_context(result), mimetype='text/event-stream', headers={
            "Content-Type": "text/event-stream",
        })
    else:
        resp = Response(result, mimetype='application/json')
    resp.headers['request_id'] = kw.get("request_id")
    return resp


@v1.route('/embeddings', methods=['POST'])
@check_application_key
def embedding():
    """
    嵌入
    ---
    tags:
      - LLM
    responses:
      200:
        res: 结果
    """
    kw = request.json
    result = LLMService.embedding(**kw)
    resp = Response(result, mimetype='application/json')
    resp.headers['request_id'] = kw.get("request_id")
    return resp
