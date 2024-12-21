#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/7/27 10:52
"""
import datetime
import hashlib
import json
import logging

from flask import g

from common.constant import AIReviewConstant, ConfigurationConstant
from common.exception.exceptions import FieldValidateError
from config import CONFIG
from dao.system.ai_review import AIReviewTaskRecordDao
from services.ai_review.ai_review_task_record_service import AIReviewTaskRecordService
from services.ai_review.ai_review_main_record_service import AIReviewMainRecordService
from services.base_service import BaseService
from services.system.configuration_service import ConfigurationService
from third_platform.es.chat_messages.ai_review_es_service import ai_review_es_service

logger = logging.getLogger(__name__)


class ReviewService(BaseService):
    @classmethod
    def validate_fields(cls, fields):
        rules = [
            {'label': 'language', 'type': str},
            {'label': 'code', 'type': str},
            {'label': 'review_type', 'type': str},
            {'label': 'file_path', 'type': str},
            {'label': 'custom_instructions', 'type': str, 'optional': True},
            {'label': 'stream', 'type': bool, 'optional': True},
        ]
        return cls._validate(fields, rules)

    @classmethod
    def insert_task_record(cls, data):
        start_time = datetime.datetime.now()
        display_name = g.current_user.display_name
        language = data.get('language', '')
        file_path = data.get('file_path', '')
        code = data.get('code', '')
        code_hash = hashlib.md5(f'{file_path}{code}'.encode()).hexdigest()
        initial_prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.MANUAL_REVIEW_PROMPT)
        prompt = initial_prompt.format(language=language,
                                       custom_instructions=data.get('custom_instructions', ''),
                                       selectedText=code)

        # 赋值给外部参数，浅拷贝
        data['start_time'] = start_time
        data['prompt'] = prompt

        kwargs = {
            'display_name': display_name,
            'file_path': file_path,
            'language': language,
            'code_hash': code_hash,
            'code': code,
            'prompt': prompt,
            'start_time': start_time,
        }
        task = AIReviewTaskRecordService.create(**kwargs)
        if task:
            data['code_task_id'] = task.id
            return task.id, data
        return None, data

    @classmethod
    def review_done_handler(cls, data, review_is_success=True):
        """
        review 成功/失败处理，更新数据，存入es
        """
        code_task_id = data.get('code_task_id')
        review_type = data.get('review_type')
        end_time = datetime.datetime.now()
        logger.info(f'review完成处理 {code_task_id} {end_time}')
        if code_task_id is None:
            logger.error('code_task_id is None.')
            return False

        start_time = data.get('start_time')
        if not start_time:
            logger.error(f'code_task_id {code_task_id} start_time is None.')
            return False

        cost_time = int((end_time - start_time).total_seconds() * 1000)
        kwargs = {
            'review_state': AIReviewConstant.ReviewState.FAIL,
            'cost_time': cost_time,
            'start_time': start_time,
            'end_time': end_time,
            'fail_msg': data.get('fail_msg', ''),
        }
        if review_is_success:
            response_text = data.get('response_text', '')
            kwargs['review_state'] = AIReviewConstant.ReviewState.SUCCESS
            kwargs['response_text'] = response_text
            kwargs['model'] = data.get('model', '')
            kwargs['prompt_tokens'] = data.get('prompt_tokens', '')
            kwargs['total_tokens'] = data.get('total_tokens', '')

            if review_type and response_text:
                # 若返回json外的额外字符，将其切除
                end_str = '}'
                if end_str in response_text and not response_text.endswith(end_str):
                    split_result = response_text.rsplit(end_str, 1)
                    response_text = split_result[0] + end_str
                    kwargs['response_text'] = response_text
                    kwargs['response_extra_text'] = split_result[1]

                try:
                    response_text_dic = json.loads(response_text)
                    kwargs['has_problem'] = response_text_dic.get('has_problem')
                except Exception as e:
                    err_msg = f'response_text: {e}'
                    logger.error(err_msg)
                    kwargs['fail_msg'] = err_msg
                    pass
        else:
            data['review_state'] = AIReviewConstant.ReviewState.FAIL

        res = AIReviewTaskRecordService.update_by_id(code_task_id, **kwargs)

        # 更新主记录 完成状态
        review_record_id = data.get('review_record_id')
        if review_type == AIReviewConstant.ReviewType.AUTO and review_record_id:
            cls.update_main_record_is_done(review_record_id)

        # 插入es数据
        ai_review_es_service.insert_ai_review(data)

        return True if res else False

    @classmethod
    def update_main_record_is_done(cls, id_):
        """根据任务表状态，决定是否更新主记录状态为done"""
        kw = {
            'review_record_id': id_,
            'review_state': AIReviewConstant.ReviewState.INIT
        }
        nums = AIReviewTaskRecordDao.get_nums(**kw)
        if nums == 0:
            update_record = {
                'is_done': True,
                'review_done_time': datetime.datetime.now()
            }
            AIReviewMainRecordService.update_by_id(mid=id_, **update_record)

    @classmethod
    def get_poll(cls, search_kw):
        ids = search_kw.pop('ids').split(',')
        try:
            ids = [int(id_) for id_ in ids]
        except Exception as e:
            logger.error(e)
            raise FieldValidateError('ids格式有误')

        search_kw['is_done'] = True
        search_kw['conditions'] = ((AIReviewMainRecordService.dao.model.id.in_(ids)),)
        query, total = AIReviewMainRecordService.list(**search_kw)
        records = [item.dict() for item in query]
        if total > 0:
            review_record_ids = [item.id for item in query]
            tasks = AIReviewTaskRecordService.get_review_done_by_ids(review_record_ids)

            # 把主记录对应代码块review信息关联
            result = [
                {**record, 'children': [item for item in tasks if item['review_record_id'] == record['id']]}
                for record in records
            ]
            return result
        return records

    @classmethod
    def calibration_review_data(cls):
        """矫正review任务数据"""
        timeout = CONFIG.app.AI_REVIEW.REVIEW_STATE_TIMEOUT  # 超时时间
        timeout_date = datetime.datetime.now() - datetime.timedelta(minutes=timeout)  # 获取超时日期

        # review task
        search_kw = {'review_state': AIReviewConstant.ReviewState.INIT}
        conditions = ((AIReviewTaskRecordService.dao.model.created_at < timeout_date),)
        update_fields = {
            'update_at': datetime.datetime.now(),
            'review_state': AIReviewConstant.ReviewState.FAIL,
            'fail_msg': 'calibration review data',
        }
        AIReviewTaskRecordService.dao.bulk_update(check_fields=search_kw, update_fields=update_fields,
                                                  conditions=conditions)

        # review 主记录
        search_kw = {'is_done': False}
        conditions = ((AIReviewMainRecordService.dao.model.created_at < timeout_date),)
        update_record = {
            'update_at': datetime.datetime.now(),
            'is_done': True,
            'review_done_time': datetime.datetime.now(),
        }
        AIReviewMainRecordService.dao.bulk_update(check_fields=search_kw, update_fields=update_record,
                                                  conditions=conditions)
