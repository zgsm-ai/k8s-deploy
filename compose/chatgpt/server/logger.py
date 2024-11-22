#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    注册日志处理模块

    :作者: 苏德利 16646
    :时间: 2023/3/29 9:47
    :修改者: 苏德利 16646
    :更新时间: 2023/3/29 9:47
"""
import os
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from setup_logging import setup_logging
from common.constant import LoggerNameContant

runtime_path = os.path.dirname(os.path.realpath(__file__))
log_dir = os.path.join(runtime_path, 'logs')


def gen_handler(level, name):
    filename = os.path.join(log_dir, f'{name}.log')

    # 500M
    handler = RotatingFileHandler(
        filename, maxBytes=524288000, backupCount=5, encoding='utf8')
    handler.setLevel(level)
    handler.setFormatter(Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    return handler


def register_logger(app):
    setup_logging()
    error_handler = gen_handler('ERROR', 'error')
    info_handler = gen_handler('INFO', 'info')

    app.logger.addHandler(error_handler)
    app.logger.addHandler(info_handler)


def register_dify_chat_logger():
    error_handler = gen_handler('ERROR', 'dify_chat_error')
    info_handler = gen_handler('INFO', 'dify_chat_info')
    dify_chat_logger = logging.getLogger(LoggerNameContant.DIFY_CHAT)
    dify_chat_logger.setLevel(logging.DEBUG)
    dify_chat_logger.addHandler(error_handler)
    dify_chat_logger.addHandler(info_handler)
    return dify_chat_logger


def register_socket_server_logger():
    error_handler = gen_handler('ERROR', 'socket_server_error')
    info_handler = gen_handler('INFO', 'socket_server_info')
    socket_server_logger = logging.getLogger(LoggerNameContant.SOCKET_SERVER)
    socket_server_logger.setLevel(logging.INFO)
    socket_server_logger.addHandler(error_handler)
    socket_server_logger.addHandler(info_handler)
    return socket_server_logger


def register_sio_logger():
    sio_info_handler = gen_handler('INFO', 'sio_info')
    sio_logger = logging.getLogger(LoggerNameContant.SIO)
    sio_logger.setLevel(logging.INFO)
    sio_logger.addHandler(sio_info_handler)
    return sio_logger
