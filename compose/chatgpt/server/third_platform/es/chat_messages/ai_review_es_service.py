#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from datetime import datetime

import pytz

from common.handlers.prompt_field_handler import prompt_field_handler
from common.utils.util import get_work_id_by_display_name
from third_platform.es.base_es import es, AI_REVIEW_INDEX, DOC, BaseESService
from third_platform.services.analysis_service import analysis_service


class AIReviewESService(BaseESService):
    """操作记录es"""
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(AIReviewESService, self).__init__()
        self.index = AI_REVIEW_INDEX
        self.field_handler = prompt_field_handler
        self._doc = DOC

    def insert_ai_review(self, data: dict):
        try:
            work_id = get_work_id_by_display_name(data.get('display_name', ''))
            department = analysis_service.get_user_multilevel_dept(work_id)

            isset = es.exists(index=self.index, id=data.get('code_task_id', ''))
            if not isset:
                response_text = data.get('response_text', '')
                obj_dict = {
                    'id': data.get('code_task_id', ''),
                    'display_name': data.get('display_name', ''),
                    'language': data.get('language', '').lower(),
                    'file_path': data.get('file_path', ''),
                    'review_type': data.get('review_type', ''),
                    'review_state': data.get('review_state', 'success'),
                    'flag': data.get('flag', ''),
                    'prompt': data.get('prompt', ''),
                    'response_text': response_text,
                    'response_text_lines': len(response_text.splitlines()),
                    'response_reuse': data.get('response_reuse', False),
                    'model': data.get('model', ''),
                    'prompt_tokens': data.get('prompt_tokens', ''),
                    'total_tokens': data.get('total_tokens', ''),
                    'created_at': datetime.now(pytz.timezone('Asia/Shanghai')),
                    'ide': data.get('ide', ''),
                    'ide_version': data.get('ide_version', ''),
                    'ide_real_version': data.get('ide_real_version', ''),
                    'department': department,
                }
                self.insert(obj_dict)
            else:
                self.update_by_id(id=data.get('code_task_id', ''), update_data={'flag': data.get('flag', '')})

        except Exception as e:
            self.logger.error(f'es 操作 ai_review数据失败，失败日志： {str(e)}')


ai_review_es_service = AIReviewESService()
