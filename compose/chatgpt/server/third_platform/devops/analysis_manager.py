#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    运营分析平台接口调度

    :作者: 苏德利 16646
    :时间: 2023/3/21 19:36
    :修改者: 刘鹏 z10807
    :更新时间: 2023/5/8 09:36
"""

from . import DevopsConfig
from common.utils.request_util import RequestUtil


class AnalysisManager(DevopsConfig):
    """
    此类主要打通devOps平台的user相关的接口
    """
    base_url = DevopsConfig.base_url + '/api/analysis'

    @classmethod
    def get_by_work_id(cls, work_id):
        # url = f'{cls.base_url}/dam/work_id?work_id={work_id}'
        # data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        # return data
        return {}

    @classmethod
    def get_all_dept(cls):
        """查询所有部门"""
        url = f'{cls.base_url}/dam/business'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data
