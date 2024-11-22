#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/6/6 14:55
"""
import datetime
import hashlib
import logging

from flask import g

from bot.bot_util import compute_tokens
from common.constant import AIReviewConstant, ConfigurationConstant
from common.exception.error_code import ERROR_CODE
from common.exception.exceptions import OperationError
from common.utils.tree_sitter_util import TreeSitterUtil
from controllers.completion_helper import completion_main, request_data_process
from services.ai_review.ai_review_task_record_service import AIReviewTaskRecordService
from services.ai_review.ai_review_main_record_service import AIReviewMainRecordService
from services.ai_review.ai_review_service import ReviewService
from services.system.configuration_service import ConfigurationService
from tasks.ai_review_task import execute_ai_review
from third_platform.es.chat_messages.ai_review_es_service import ai_review_es_service

logger = logging.getLogger(__name__)


class ReviewMainService:
    # tokenizer = Tokenizer.from_file(AIReviewConstant.TOKENIZER_PATH)  # 本地模型获取获取tokens方法
    parser = None

    @classmethod
    def get_token_num(cls, prompt):
        """获取token数"""
        return compute_tokens(prompt)
        # return len(cls.tokenizer.encode(prompt).ids)  # 本地模型获取获取tokens方法

    @staticmethod
    def code_process(code: str, start_lineno: int = 1) -> str:
        """
        为每行加上相对行号
        由行号和空字符组成。行号占2空字符+固定8空字符（两个制表符）
        """
        return '\n'.join([f'{i + start_lineno: <10}{line}' for i, line in enumerate(code.splitlines())])

    @classmethod
    def prompt_process(cls, language: str, code: str) -> str:
        """组合prompt"""
        initial_prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.AUTO_REVIEW_PROMPT)
        return initial_prompt.replace('#language#', language).replace('#select_code#', code)

    @classmethod
    def run_manual_review(cls, fields: dict):
        """主动review"""
        code_task_id, request_data = ReviewService.insert_task_record(fields)
        try:
            fields['code_task_id'] = code_task_id
            fields['action'] = 'review'
            if fields.get('stream') is None:
                fields['stream'] = True
            return completion_main(fields)
        except Exception as e:
            logger.error(e)
            request_data['fail_msg'] = e
            ReviewService.review_done_handler(request_data, False)
            raise OperationError('review请求异常')

    @classmethod
    def run_auto_review(cls, fields: dict):
        """自动review"""
        file_path = fields.get('file_path')
        language = fields.get('language')
        review_type = fields.get('review_type')
        code = fields.get('code')
        user = g.current_user
        display_name = g.current_user.display_name

        max_review_num = ConfigurationService.get_review_max_review_num()  # 单文件向gpt最高请求数
        review_task_num = 0  # review请求任务数

        functions = TreeSitterUtil.split_code(language, code)
        if len(functions) == 0:
            return {'error_code': ERROR_CODE.SERVER.REQUEST_ERROR, 'message': '没有函数可review'}

        # 初始入库review主记录
        insert_review_main_record = {
            'display_name': display_name,
            'file_path': file_path,
        }
        record = AIReviewMainRecordService.create(**insert_review_main_record)
        if not record:
            raise OperationError('数据库操作异常')

        review_record_id = record.id

        for func_dict in functions:
            # 单文件review数量超过阈值，则忽略之后不再review
            if review_task_num >= max_review_num:
                break

            code = func_dict.get('text')
            code_start_lineno = func_dict.get('start_lineno')
            code_end_lineno = func_dict.get('end_lineno')

            # 代码块特殊处理
            code_processed = cls.code_process(code, func_dict.get('start_lineno', 1))
            # prompt处理
            prompt = cls.prompt_process(language, code_processed)

            # 超过限制token不进行review
            token_num = cls.get_token_num(prompt)
            if token_num >= AIReviewConstant.MAX_TOKEN:
                continue

            code_hash = hashlib.md5(f'{file_path}{code}'.encode()).hexdigest()

            # 校验是否已review过, 且状态为指定的，直接跳过忽略
            search_kw = {
                'code_hash': code_hash,
                'display_name': display_name,
                'conditions': ((AIReviewTaskRecordService.dao.model.flag.in_(AIReviewConstant.Flag.SKIP_REVIEW)),)
            }
            skip_review_data = AIReviewTaskRecordService.get_exist_review_task(search_kw)
            if skip_review_data:
                continue

            review_task = {
                'review_record_id': review_record_id,
                'display_name': display_name,
                'file_path': file_path,
                'language': language,
                'review_type': review_type,
                'code_hash': code_hash,
                'code_start_lineno': code_start_lineno,
                'code_end_lineno': code_end_lineno,
                'code': code,
                'prompt': prompt
            }

            # 校验是否已review过, 已review过的数据直接复用
            search_kw = {
                'code_hash': code_hash,
                'code_start_lineno': code_start_lineno
            }
            reuse_review_data = AIReviewTaskRecordService.get_exist_review_task(search_kw)
            if reuse_review_data:
                review_task['response_reuse'] = True
                review_task['current_model'] = reuse_review_data.current_model
                review_task['review_state'] = reuse_review_data.review_state
                review_task['has_problem'] = reuse_review_data.has_problem
                review_task['response_text'] = reuse_review_data.response_text
                review_task['prompt_tokens'] = reuse_review_data.prompt_tokens
                review_task['total_tokens'] = reuse_review_data.total_tokens
                review_task['start_time'] = review_task['end_time'] = datetime.datetime.now()
                review_task['cost_time'] = 0
                review_task['flag'] = ''

            # 初始入库review任务
            code_task = AIReviewTaskRecordService.create(**review_task)

            review_task['code_task_id'] = code_task.id
            review_task['prompt'] = prompt
            request_data = request_data_process(review_task, user.dict())

            # 若为复用数据，直接插入es，并跳过review队列
            if review_task.get('response_reuse'):
                ai_review_es_service.insert_ai_review(request_data)
            else:
                execute_ai_review.delay(request_data)
                review_task_num += 1

        # 可review数为0时，表示没有可review的代码块，直接更新主记录状态为done
        ReviewService.update_main_record_is_done(review_record_id)

        return record
