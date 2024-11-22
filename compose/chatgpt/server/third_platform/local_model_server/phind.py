#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 18212
@Date    : 2023/11/07
"""
from config import Config
import requests
import logging

logger = logging.getLogger(__name__)


class PhindManage:
    model_server = Config().ut.get("phind_server")

    @classmethod
    def ask(cls, data):

        url = cls.model_server.get("url")
        print(f"url:{url}")
        print(f"data:{data}")
        timeout = cls.model_server.get("timeout")
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=timeout, stream=data.get("stream", False))
            return resp
        except Exception as e:
            logging.error(e, exc_info=True)
            raise Exception(e)
