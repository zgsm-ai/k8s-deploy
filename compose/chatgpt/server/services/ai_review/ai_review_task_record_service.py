#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/7/27 10:00
"""
import logging

from common.constant import AIReviewConstant
from dao.system.ai_review import AIReviewTaskRecordDao
from services.base_service import BaseService
from third_platform.es.chat_messages.ai_review_es_service import ai_review_es_service

logger = logging.getLogger(__name__)


class AIReviewTaskRecordService(BaseService):
    dao = AIReviewTaskRecordDao

    @classmethod
    def validate_update_fields(cls, mid, fields):
        rules = [
            {'label': 'flag', 'type': str, 'allow_empty': True},
        ]
        return cls._validate(fields, rules)

    @classmethod
    def update_flag(cls, mid, **fields):
        resp = AIReviewTaskRecordService.update_by_id(mid, **fields)
        fields['code_task_id'] = mid
        ai_review_es_service.insert_ai_review(fields)  # 更新es数据
        return resp

    @classmethod
    def get_exist_review_task(cls, search_kw):
        kwargs = {
            'ordering': '-created_at',
            'page': 1,
            'per': 1,
            'review_state': AIReviewConstant.ReviewState.SUCCESS,
            **search_kw
        }
        query, total = super().list(**kwargs)
        if len(query) > 0:
            return query[0]
        return None

    @classmethod
    def get_review_done_by_ids(cls, ids: list):
        kwargs = {
            'review_state': AIReviewConstant.ReviewState.SUCCESS,
            'has_problem': True,
            'conditions': ((AIReviewTaskRecordService.dao.model.review_record_id.in_(ids)),),
            'include_fields': (
                'id', 'review_type', 'review_state', 'language', 'file_path', 'code_hash', 'current_model',
                'display_name', 'flag', 'has_problem', 'response_reuse', 'response_text', 'review_record_id',
                'fail_msg', 'response_extra_text', 'cost_time', 'prompt_tokens', 'total_tokens', 'created_at',
                'code_start_lineno', 'code_end_lineno')
        }
        query, total = super().list(**kwargs)
        data = [item.dict() for item in query]
        data = sorted(data, key=lambda x: x.get('code_start_lineno'))
        return data
