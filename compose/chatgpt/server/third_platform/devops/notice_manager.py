#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/20 17:42
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from common.utils.request_util import RequestUtil
from config import CONFIG
from third_platform.devops import DevopsConfig

executor = ThreadPoolExecutor()


class NoticeManager(DevopsConfig):
    """
    此类主要打通devOps平台的通知相关的接口
    """
    base_url = DevopsConfig.base_url + '/api/notice'

    @classmethod
    def send_notice(cls, **params):
        data = cls.format_resp(RequestUtil.post(cls.base_url, data=params, headers=cls.headers))
        return data

    @classmethod
    def send_notice_server(cls, **params):
        url = CONFIG.app.NOTICE_SERVER.server_url + '/api/notice_server/notice'
        headers = {
            'Content-Type': 'application/json',
            "Accept": "application/json",
            "token": CONFIG.app.NOTICE_SERVER.token
        }
        data = cls.format_resp(RequestUtil.post(url, data=params, headers=headers))
        return data

    @classmethod
    def send_notice_callback(cls, future):
        result = future.result()
        logging.info(f'成功发送通知至{result["username"]}')


def send_notice_server_async(**params) -> None:
    """
    异步发送通知，不等待
    :param: 消息参数
    :return: 无返回
    """
    if params.get('type') is None:
        params['type'] = ["dim", "moa"]  # 默认通知类型
    logging.info(f'开始发送通知至{params["username"]}')
    future = executor.submit(NoticeManager.send_notice_server, **params)
    future.add_done_callback(NoticeManager.send_notice_callback)
