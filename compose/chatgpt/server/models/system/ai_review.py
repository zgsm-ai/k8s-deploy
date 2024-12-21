#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/7/26 17:24
"""
import json
import logging

from peewee import CharField, IntegerField, DateTimeField, TextField, BooleanField

from common.constant import AIReviewConstant
from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class AIReviewMainRecord(BaseModel):
    """AIReview主记录"""

    class Meta:
        table_name = 'ai_review_main_record'

    display_name = CharField(default='', verbose_name='用户')
    file_path = CharField(default='', verbose_name='文件路径')
    is_done = BooleanField(default=False, verbose_name='review完成')
    review_done_time = DateTimeField(null=True, verbose_name='review完成时间')


class AIReviewTaskRecord(BaseModel):
    """AIReview任务记录"""

    REVIEW_TYPE_CHOICES = AIReviewConstant.ReviewType.CHOICES
    REVIEW_STATE_CHOICES = AIReviewConstant.ReviewState.CHOICES
    FLAG_CHOICES = AIReviewConstant.Flag.CHOICES

    class Meta:
        table_name = 'ai_review_task_record'

    review_record_id = IntegerField(index=True, null=True, verbose_name='主记录id')
    display_name = CharField(default='', verbose_name='用户')
    file_path = CharField(default='', verbose_name='文件路径')
    language = CharField(default='', verbose_name='语言')
    review_type = CharField(default=AIReviewConstant.ReviewType.MANUAL, choices=REVIEW_TYPE_CHOICES,
                            verbose_name='类型')
    review_state = CharField(default=AIReviewConstant.ReviewState.INIT, choices=REVIEW_STATE_CHOICES, verbose_name='状态')
    flag = CharField(default='', choices=FLAG_CHOICES, verbose_name='标记')
    model = CharField(default='', verbose_name='模型')
    code_hash = CharField(index=True, default='', verbose_name='代码hash')  # file_path + code
    code_start_lineno = IntegerField(null=True, verbose_name='代码块开始行')
    code_end_lineno = IntegerField(null=True, verbose_name='代码块结束行')
    code = TextField(default='', verbose_name='代码')
    prompt = TextField(default='', verbose_name='prompt')
    has_problem = BooleanField(null=True, verbose_name='有问题')  # 是否存在问题
    response_text = TextField(default='', verbose_name='响应内容')
    response_reuse = BooleanField(default=False, verbose_name='响应复用')
    cost_time = IntegerField(null=True, verbose_name='耗时.单位:ms')
    start_time = DateTimeField(null=True, verbose_name='review开始时间')  # 请求开始时间
    end_time = DateTimeField(null=True, verbose_name='review结束时间')  # 请求结束时间
    prompt_tokens = IntegerField(null=True, verbose_name='prompt token')
    total_tokens = IntegerField(null=True, verbose_name='所有token')
    fail_msg = TextField(default='', verbose_name='失败原因')
    response_extra_text = CharField(default='', max_length=1000, verbose_name='响应脏数据')

    def dict(self, *args, **kwargs):
        data = super().dict()
        if data.get('response_text') and self.review_type == AIReviewConstant.ReviewType.AUTO:
            try:
                data['response_text'] = json.loads(data.get('response_text'))
            except Exception as e:
                err_msg = f'response_text: {e}'
                logger.error(err_msg)
                self.fail_msg = err_msg
                data['fail_msg'] = err_msg
                self.save()
        return data
