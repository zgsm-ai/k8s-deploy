#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/19 17:40
"""
import logging

from peewee import CharField, BooleanField, TextField, IntegerField

from common.utils.date_util import DateUtil
from db.custom_field import JSONField
from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class AIRecordAction(BaseModel):
    """AI请求 action类别记录"""

    class Meta:
        table_name = 'ai_record_action'

    response_id = CharField(default='', max_length=50, verbose_name='响应id')
    action = CharField(default='', max_length=20, verbose_name='action动作')
    display_name = CharField(default='', max_length=20, verbose_name='用户')
    dept = CharField(default='', max_length=50, verbose_name='用户部门')
    second_dept = CharField(default='', max_length=50, verbose_name='用户二级部门')
    prompt = TextField(default='', verbose_name='用户prompt')
    origin_prompt = TextField(null=True, default='', verbose_name='用户原始的问答内容')
    code = TextField(default='', verbose_name='用户代码')
    language = CharField(default='', max_length=10, verbose_name='语言')
    git_path = CharField(default='', verbose_name='git仓库')
    response_code = TextField(default='', verbose_name='响应代码')
    middle_process_records = JSONField(default=[], verbose_name='中间处理过程记录')
    is_accept = BooleanField(default=False, verbose_name='是否接受')
    accept_num = IntegerField(default=0, verbose_name='接受行数')
    refusal_cause = CharField(default='', max_length=1000, verbose_name='拒绝原因')
    analysis_result = CharField(default='', max_length=1000, verbose_name='分析结果')
    process_state = BooleanField(default=False, verbose_name='处理状态')
    history = JSONField(default=[], verbose_name='追问历史')

    def dict(self, *args, **kwargs):
        data = super().dict()
        data['cost_time'] = self.get_cost_time(data)
        return data

    @staticmethod
    def get_cost_time(data):
        time_diff = 0
        middle_process_records = data['middle_process_records']
        try:
            if len(middle_process_records) > 0:
                start_time = middle_process_records[0]['start_time']
                end_time = middle_process_records[-1]['end_time']
                start_time = DateUtil.str_to_format_gmt_datetime(start_time)
                end_time = DateUtil.str_to_format_gmt_datetime(end_time)
                time_diff = int((end_time - start_time).total_seconds())
        except Exception as e:
            logger.error(e)
        return time_diff
