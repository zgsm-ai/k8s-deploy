#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/14 20:37
    :修改者: 苏德利 16646
    :更新时间: 2023/3/14 20:37
"""

import logging
from common.exception.exceptions import RequestError


class BaseManager:
    """
    默认所有接口都符合restful风格
    """
    headers = {
        'Content-Type': 'application/json',
        "Accept": "application/json",
    }

    @classmethod
    def format_resp(cls, resp):
        if not resp.get('success'):
            logging.error(f"数据获取失败, {resp.get('message')}")
            raise RequestError(f"请求失败！{resp.get('message')}")
        if resp.__contains__('data') and resp.__contains__('total'):
            return resp.get('data'), resp.get('total')
        return resp.get('data')

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass
