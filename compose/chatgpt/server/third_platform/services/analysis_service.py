#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/21 19:57
    :修改者: 苏德利 16646
    :更新时间: 2023/3/21 19:57
"""
import logging

from common.constant import ApiRuleConstant, AppConstant, AnalysisConstant
from common.utils.util import flatten_dept_list
from third_platform.devops.analysis_manager import AnalysisManager
from lib.cache.cache_anno import cache_able

import traceback

logger = logging.getLogger(__name__)


class AnalysisService:
    CACHE_KEY_WORK_ID = AnalysisConstant.CACHE_KEY_WORK_ID
    CACHE_KEY_DEPT_LIST = AnalysisConstant.CACHE_KEY_DEPT_LIST
    manager = AnalysisManager

    @classmethod
    @cache_able(CACHE_KEY_WORK_ID, index=[1])
    def get_by_work_id(cls, work_id):
        return cls.manager.get_by_work_id(work_id)

    @classmethod
    def get_user_multilevel_dept(cls, work_id):
        """
        获取用户多级部门
        return：例：研发体系/xx部门
        """
        work_info = cls.get_by_work_id(work_id)
        department = ''
        if work_info:
            # 目前最多有4级部门
            departments = [work_info.get(f"dept_{i}") for i in range(1, 5) if work_info.get(f"dept_{i}")]
            department = '/'.join(departments)
        else:
            logger.warning(f'未查到用户部门. work_id:{work_id}')
            traceback.print_stack()
        return department

    @classmethod
    @cache_able(CACHE_KEY_DEPT_LIST, expire=AppConstant.DEPT_CACHE_TIMEOUT)
    def get_dept_list(cls):
        """查询部门列表"""
        dept_data = list(filter(lambda x: x['name'] == ApiRuleConstant.ALLOW_COMPANY,
                                cls.manager.get_all_dept()))[0]['children']
        return flatten_dept_list(dept_data)


analysis_service = AnalysisService()
