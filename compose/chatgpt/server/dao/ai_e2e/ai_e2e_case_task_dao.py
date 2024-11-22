#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/24 14:37
"""

from dao.base_dao import BaseDao
from models.ai_e2e.ai_e2e_case_task import AiE2ECaseTask, AiE2ECaseTaskEvents


class AiE2ECaseTaskDao(BaseDao):
    model = AiE2ECaseTask


class AiE2ECaseTaskEventsDao(BaseDao):
    model = AiE2ECaseTaskEvents
