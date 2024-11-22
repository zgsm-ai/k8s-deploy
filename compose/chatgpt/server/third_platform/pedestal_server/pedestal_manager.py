#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib.parse import urljoin
import requests
import logging

from common.exception.exceptions import RequestError, ParameterConversionError
from third_platform.pedestal_server import PedestalServerConfig

logger = logging.getLogger(__name__)


class PedestalServerManager(PedestalServerConfig):
    """
    此类主要请求底座服务
    """

    @classmethod
    def get_model(cls, **kwargs):
        headers = cls.base_headers.copy()
        url = urljoin(PedestalServerConfig.base_url, "/api/llm/list")
        try:
            response = requests.get(url=url, params=kwargs, headers=headers)
        except Exception as e:
            raise Exception(f"请求底座服务失败, get_model, url:{url}, error：{e}")
        if response.status_code == 200:
            return response.json()
        try:
            res = response.json()
            message = res.get("message", "")
        except ValueError:
            message = response.text
        if response.status_code >= 500:
            raise RequestError(message)
        if response.status_code >= 400:
            raise ParameterConversionError(message)

    @classmethod
    def chat_completion(cls, conversation_id, data, api_key=None):

        headers = cls.base_headers.copy()
        headers.update({'conversation-id': conversation_id})
        if api_key:
            headers.update({'api-key': api_key})

        url = urljoin(PedestalServerConfig.base_url, "/api/inference/v1/chat/completions")
        timeout = data.get("timeout", 300)
        stream = data.get("stream", False)

        try:
            response = requests.post(url=url, json=data, headers=headers, timeout=timeout, stream=stream)
        except Exception as e:
            raise Exception(f"请求底座服务失败, chat_completion, url:{url}, conversation_id:{conversation_id}, error：{e}")
        if response.status_code == 200:
            return response
        try:
            res = response.json()
            message = res.get("message", "")
        except ValueError:
            message = response.text
        if response.status_code >= 500:
            raise RequestError(message)
        if response.status_code >= 400:
            raise ParameterConversionError(message)
