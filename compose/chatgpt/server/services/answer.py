#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import json
import logging
import re
from functools import wraps

from bot.ad_cache import AdHelper
from bot.cache import get_redis
from common.exception.exceptions import CustomException
from common.helpers.application_context import ApplicationContext
from common.helpers.custom_permission import make_resp_dict_by_action
from config import conf, CONFIG
from bot.apiBot import Chatbot as apiBot
from controllers.response_helper import Result
from services.model_service import ModelService
from third_platform.es.chat_messages.prompt_es_service import prompt_es_service
from third_platform.pedestal_server.pedestal_manager import PedestalServerManager
from flask import Response, stream_with_context, request


def handle_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if response.status_code >= 400:
            content = response.get_json().get('message', '')
            if request.json.get('stream', True):
                resp = Response(content, mimetype='text/plain')
                return resp
            else:
                response = make_resp_dict_by_action('', content)
            return response

        else:
            return response

    return decorated_function


class AnswerService:
    full_response = ""
    usage = ""
    prompt = ""
    data = dict()

    def __init__(self):
        self.redis = get_redis(conf)
        self.data = request.get_json()
        self.prompt = self.get_prompt(self.data.get("prompt"))
        self.stream = self.data.get("stream", False)
        self.temperature = self.data.get("temperature", 0)
        self.model = request.headers.get("model")
        self.messages = self.get_messages()
        self.conversation_id = request.headers.get("conversation-id", "")
        self.user = ApplicationContext.get_current()

        self.data['display_name'] = self.user.display_name
        self.data['username'] = self.user.username
        self.data['messages'] = self.messages
        self.data['model'] = self.model
        self.data['temperature'] = self.data.get("temperature", 0)

    @handle_exceptions
    def answer(self):
        try:
            if not self.prompt:
                return ("", 204)

            self.check_model()
            api_key = CONFIG.app.PEDESTAL_SERVER.get('qianliu_ai_web_api_key')
            response = PedestalServerManager.chat_completion(self.conversation_id, data=self.data, api_key=api_key)
            conversation_id = response.headers.get("conversation-id")
            request_id = response.headers.get("request_id")

            res = self.answer_res(response)

            if self.stream:
                ad_helper = AdHelper()
                res = itertools.chain(res, ad_helper.yield_ad(self.user.display_name, self.redis))

                response = Response(stream_with_context(res), mimetype='text/event-stream', headers={
                    "Content-Type": "text/event-stream",
                })

            else:
                response = Response(json.dumps(res), mimetype='application/json')

            response.headers.update(
                {"Current-Model": self.model, "conversation-id": conversation_id, "request_id": request_id})

            return response
        except CustomException as e:
            logging.error(f"Chat completion error, data:{self.data}, error:{e}", exc_info=True)
            return Result.fail(message=e.msg, code=e.code)
        except Exception as e:
            logging.error(f"Chat completion error, data:{self.data}, error:{e}", exc_info=True)
            return Result.fail(message="Chat completion error", code=500)

    def answer_res(self, response):
        if self.stream:
            return self.stream_generator(response)

        else:
            return self.generator(response)

    def stream_generator(self, response):
        for chunk in response.iter_lines(chunk_size=1, decode_unicode=True):
            if chunk:  # 跳过空行
                chunk = chunk.replace("data:", "").strip()
                try:
                    if chunk == "[DONE]":
                        continue
                    d = json.loads(chunk)
                    content = d["choices"][0]["delta"].get("content", "")
                    self.usage = d["usage"]
                    if not content:
                        continue
                    self.full_response += content
                    yield content
                except Exception as e:
                    raise Exception(f"stream error:{e}, chunk:{chunk}")
        self.record_data_es()

    def generator(self, response):
        res = response.json()
        self.full_response = res["choices"][0]["delta"].get("content", "")
        self.usage = res["usage"]
        self.record_data_es()
        return res

    def get_prompt(self, prompt):
        raw_prompt = re.match(r"Human:([\w\W]*)\nAI:", prompt)
        if not raw_prompt:
            return None
        return raw_prompt.group(1)

    def get_messages(self):
        chatbot = apiBot(redis=self.redis, model=self.model)
        messages = chatbot.prompt.get_user_req_messages(self.prompt)
        return messages

    def record_data_es(self):
        try:
            self.data['path'] = request.path
            self.data['user_agent'] = request.headers.get("User-Agent")
            self.data['host'] = request.headers.get("Host")
            self.data['current_model'] = self.model
            prompt_es_service.insert_prompt(self.data, self.full_response, self.usage)
        except Exception as e:
            logging.error(f"answer record_data_es error: {e}")

    def check_model(self):
        enable_models = ModelService.get_enable_models()
        if self.model not in enable_models:
            raise CustomException(msg="model is disabled")
