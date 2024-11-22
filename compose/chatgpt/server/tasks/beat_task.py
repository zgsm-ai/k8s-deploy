#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/8/9 17:04
"""
import logging

from services.ai_review.ai_review_service import ReviewService
from services.conversation.conversation_service import ConversationService
from tasks import celery_app, handle_db

logger = logging.getLogger(__name__)


@celery_app.task
@handle_db
def calibration_review_data_task():
    """
    定时矫正review任务数据
    """
    ReviewService.calibration_review_data()


@celery_app.task
@handle_db
def clean_up_expired_contexts_task():
    """
    定时清理过期会话记录
    """
    ConversationService.clean_up_expired_contexts()
