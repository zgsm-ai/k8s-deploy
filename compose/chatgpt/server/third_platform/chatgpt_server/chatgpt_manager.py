#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import logging
from third_platform.chatgpt_server import ChatGptServerConfig

logger = logging.getLogger(__name__)


class ChatGptServerManager(ChatGptServerConfig):
    """
    此类主要从外部重新调用一次chatgpt-server
    """

    @classmethod
    def completion(cls, **kwargs):
        url = ChatGptServerConfig.base_url + "/api/v2/completion"
        res = requests.post(url=url,
                            json=kwargs.get("data"),
                            headers=kwargs.get("headers"))
        if res.status_code == 200:
            data = res.json()
            return data
        else:
            logger.error(f'review request error: status code: {res.status_code} {res.text}')
            return False
