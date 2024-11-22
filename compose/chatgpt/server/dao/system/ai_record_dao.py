#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/19 20:36
"""

from dao.base_dao import BaseDao
from models.system.ai_record import AIRecordAction


class AIRecordActionDao(BaseDao):
    model = AIRecordAction
