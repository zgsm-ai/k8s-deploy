#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 18212
@Date    : 2023/11/07
"""

from config import Config
from controllers.completion_helper import completion_main

from third_platform.local_model_server.llama import LlamaManage
from third_platform.local_model_server.phind import PhindManage


class UTModelService:

    @classmethod
    def get_ut_res(cls, data, use_model=""):
        prompt = data.get("inputs")
        parameters = data.get("parameters")
        if use_model == "GPTModel":
            resp = cls.ask_gpt(data)

        elif use_model == "PhindModel":
            combination_data = dict(parameters=dict(parameters), inputs=prompt, stream=data.get("stream"))
            resp = cls.ask_phind(combination_data)

        else:
            combination_data = dict(parameters=dict(parameters), inputs=prompt, stream=data.get("stream"))
            resp = cls.ask_llama(combination_data)
        return resp

    @classmethod
    def ask_gpt(cls, data):
        prompt = data.get("prompt")
        system_prompt = data.get("system_prompt")

        ut_config = Config().ut
        model_map = ut_config.get("models").get("GPTModel")
        max_tokens = model_map.get("token_length").get("all_length")
        stream = data.get("stream", False)
        temperature = model_map.get("temperature", 0.3)

        data = {"systems": [system_prompt],
                "prompt": prompt,
                "stream": stream,
                "conversation_id": "",
                "temperature": temperature,
                "max_tokens": max_tokens,
                "gpt_model": data["gpt_model"]
                }

        resp = completion_main(data, is_ut=True)
        if stream:
            return resp
        result = resp.get("choices")[0].get("message", {}).get("content", "")
        resp = {
            "model_res": result
        }
        return resp

    @classmethod
    def ask_llama(cls, data):
        resp = LlamaManage.ask(data)
        stream = data.get("stream", False)
        if stream:
            return resp
        return resp.json()

    @classmethod
    def ask_phind(cls, data):
        resp = PhindManage.ask(data)
        stream = data.get("stream", False)
        if stream:
            return resp
        return resp.json()
