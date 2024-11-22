#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/5/6 16:04
"""
import logging

from admin.auth import AdminPermission
from admin.base import BaseView
from admin.views.open_api_applications_admin import CustomFilter
from models.system.ai_review import AIReviewMainRecord, AIReviewTaskRecord

logger = logging.getLogger(__name__)


class AIReviewMainRecordAdmin(AdminPermission, BaseView):
    column_list = ('id', 'display_name', 'file_path', 'is_done', 'created_at', 'review_done_time')
    column_searchable_list = ('display_name',)
    column_default_sort = ('created_at', True)
    # 列表页 字段显示verbose_name值
    column_labels = BaseView.get_column_labels(AIReviewMainRecord)


class AIReviewTaskRecordAdmin(AdminPermission, BaseView):
    column_list = (
        'id', 'review_record_id', 'display_name', 'file_path', 'review_type', 'review_state', 'flag', 'has_problem',
        'response_reuse', 'created_at', 'prompt', 'response_text', 'response_reuse')
    column_searchable_list = ('display_name',)
    column_default_sort = ('created_at', True)
    form_widget_args = {
        'id': {'readonly': True},
        'created_at': {'readonly': True},
        'review_record_id': {'readonly': True},
    }

    # 额外过滤条件
    column_extra_filters = [
        CustomFilter(
            column=AIReviewTaskRecord.review_type,
            name=AIReviewTaskRecord.review_type.verbose_name,
            options=AIReviewTaskRecord.REVIEW_TYPE_CHOICES
        ),
        CustomFilter(
            column=AIReviewTaskRecord.review_state,
            name=AIReviewTaskRecord.review_state.verbose_name,
            options=AIReviewTaskRecord.REVIEW_STATE_CHOICES
        ),
        CustomFilter(
            column=AIReviewTaskRecord.flag,
            name=AIReviewTaskRecord.flag.verbose_name,
            options=AIReviewTaskRecord.FLAG_CHOICES
        ),
    ]

    # 列表页 字段显示verbose_name值
    column_labels = BaseView.get_column_labels(AIReviewTaskRecord)
    # 列表页 字段值显示choices值
    column_formatters = {
        'review_type': lambda v, c, m, p: dict(m.REVIEW_TYPE_CHOICES).get(m.review_type),
        'review_state': lambda v, c, m, p: dict(m.REVIEW_STATE_CHOICES).get(m.review_state),
        'flag': lambda v, c, m, p: dict(m.FLAG_CHOICES).get(m.flag),
    }


AIReviewMainRecordAdminView = AIReviewMainRecordAdmin(AIReviewMainRecord, endpoint='_ai_review_record', name='review主记录')
AIReviewTaskRecordAdminView = AIReviewTaskRecordAdmin(AIReviewTaskRecord, endpoint='_ai_review_task', name='review任务记录')
