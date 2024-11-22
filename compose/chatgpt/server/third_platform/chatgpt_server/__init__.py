#!/usr/bin/env python
# -*- coding: utf-8 -*-
from third_platform.base_manager import BaseManager
from common.exception.exceptions import RequestError
from config import CONFIG
import logging


class ChatGptServerConfig(BaseManager):
    base_url = CONFIG.app.APP_URL

    @classmethod
    def format_resp(cls, resp):
        if not resp.get('success'):
            logging.error(f"数据获取失败, {resp.get('message')}")
            raise RequestError("请求devops失败")
        if resp.__contains__('data') and resp.__contains__('total'):
            return resp.get('data'), resp.get('total')
        return resp.get('data')
