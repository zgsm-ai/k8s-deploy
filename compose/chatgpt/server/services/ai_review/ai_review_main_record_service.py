#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/7/27 10:00
"""
import logging

from dao.system.ai_review import AIReviewMainRecordDao
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class AIReviewMainRecordService(BaseService):
    dao = AIReviewMainRecordDao
