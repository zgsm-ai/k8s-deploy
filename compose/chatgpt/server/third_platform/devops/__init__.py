#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/14 20:33
    :修改者: 苏德利 16646
    :更新时间: 2023/3/14 20:33
"""
from third_platform.base_manager import BaseManager
from common.exception.exceptions import RequestError
from config import get_config
import logging
from copy import deepcopy


class DevopsConfig(BaseManager):
    base_url = get_config().get("devops_url")
    headers = deepcopy(BaseManager.headers)
    headers['token'] = get_config().get("devops_token")

    @classmethod
    def format_resp(cls, resp):
        if not resp.get('success'):
            logging.error(f"数据获取失败, {resp.get('message')}")
            raise RequestError("请求devops失败")
        # if resp.get('total'):
        #     return resp.get('data'), resp.get('total')
        # return resp.get('data')
        if resp.__contains__('data') and resp.__contains__('total'):
            return resp.get('data'), resp.get('total')
        return resp.get('data')
