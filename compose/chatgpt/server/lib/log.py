#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    设置log debug模式是否开启

    :作者: 苏德利 16646
    :时间: 2023/3/29 10:01
    :修改者: 苏德利 16646
    :更新时间: 2023/3/29 10:01
"""
# -*- coding: utf-8 -*-
from logging import Filter, Formatter
from config import conf
from contextlib import contextmanager


class RequireDebugFalse(Filter):
    def filter(self, record):
        return not conf.get('log_debug')


class RequireDebugTrue(Filter):
    def filter(self, record):
        return conf.get('log_debug')


class SocketFilter(Filter):
    def __init__(self, sid=None):
        super().__init__()
        self.sid = sid

    def filter(self, record):
        record.sid = self.sid
        return True


class SocketLoggerWrapper:
    def __init__(self, logger):
        self.logger = logger
        formatter = Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [SID: %(sid)s] - %(message)s'
        )

        # 为所有处理程序设置格式化器
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)

    @contextmanager
    def set_sid(self, sid):
        sid_filter = SocketFilter(sid)
        self.logger.addFilter(sid_filter)

        try:
            yield
        finally:
            self.logger.removeFilter(sid_filter)
