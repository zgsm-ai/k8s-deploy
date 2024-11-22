#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/25 14:59
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : __init__.py.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : eolinker平台http基础配置

from third_platform.base_manager import BaseManager
from common.exception.exceptions import RequestError
from config import CONFIG
import logging
from copy import deepcopy
from flask import g


class EoLinkerConfig(BaseManager):
    base_url = CONFIG.app.Eolinker[0].get("server_url")
    headers = deepcopy(BaseManager.headers)
    headers['Eo-Secret-Key'] = CONFIG.app.Eolinker[0].get("token")

    @classmethod
    def format_resp(cls, resp):
        if resp.get('status') != "success":
            logging.error(f"数据获取失败, {resp.get('message')}")
            raise RequestError("请求Eolinker失败")
        if resp.__contains__('result') and resp.__contains__('total'):
            return resp.get('result'), resp.get('total')
        return resp.get('result')

    @classmethod
    def get_origin_url_and_headers(cls, origin, space_id=None):
        """
        eolinker存在多套平台，这里根据接口请求头origin字段判断，获取对应的key
        :param origin:
        :param space_id:
        :return:
        """
        api_key = None
        if space_id and g.authorization:
            # 注意这里引用了flask对象g.authorization，需要在request请求中调用此方法
            # 先获取space 的 api_key , 给后续调用 eoliner openapi使用,获取不到 该api_key 就会用配置文件默认的用户
            from third_platform.eolinker.api_studio_manager import ApiStudioHelper
            api_key = ApiStudioHelper.get_space_api_key(space_id=space_id, authorization=g.authorization, origin=origin)
        base_url = cls.base_url
        headers = deepcopy(cls.headers)
        host = origin.replace("https://", "").replace("http://", "")
        for eolinker_conf in CONFIG.app.Eolinker:
            server_url = eolinker_conf.get("server_url")
            server_host = server_url.replace("https://", "").replace("http://", "")
            if server_host.startswith(host) and eolinker_conf.get("token"):
                base_url = server_url
                headers['Eo-Secret-Key'] = api_key if api_key else eolinker_conf.get("token")
                break

        return base_url, headers
