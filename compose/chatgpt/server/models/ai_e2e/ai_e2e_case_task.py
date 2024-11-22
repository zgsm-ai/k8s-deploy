#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import logging

from peewee import CharField, TextField, IntegerField

from db.custom_field import JSONField
from models.base_model import BaseModel
from common.constant import AiE2ECaseConstant


class AiE2ECaseTask(BaseModel):
    """E2E测试用例任务表"""

    class Meta:
        table_name = 'ai_e2e_case_task'

    display_name = CharField(index=True, verbose_name='用户')
    case_code = CharField(verbose_name='人为定义的用例id')
    case_id = CharField(index=True, verbose_name='tp数据库的用例id')
    case_name = CharField(default="", verbose_name='用例名称')
    case_pre_step = TextField(default="", verbose_name='用例前置条件')
    case_step = TextField(default="", verbose_name='用例步骤')
    case_expect = TextField(default="", verbose_name='用例名称')
    case_post_step = TextField(default="", verbose_name='用例名称')
    case_remark = TextField(default="", verbose_name='用例备注')
    case_level = CharField(default="", verbose_name='用例级别')
    # 对应tp的用例路径
    case_module = CharField(default="", verbose_name='用例模块')
    product_id = CharField(default="", verbose_name='产品ID')
    product_name = CharField(default="", verbose_name='产品名称')
    # 中间处理的过程记录，分为几个阶段，具体见service中的注释
    status = CharField(verbose_name='状态', choices=AiE2ECaseConstant.AiE2ECaseTaskStatus.CHOICES)
    remark = TextField(default="", verbose_name='备注')
    # 生成结果接受类型
    accept_type = CharField(default=AiE2ECaseConstant.AcceptType.NOT_ACCEPT, verbose_name='接受类型',
                            choices=AiE2ECaseConstant.AcceptType.CHOICES)
    # 生成结构接受的内容
    accept_content = TextField(default="", verbose_name='接受的内容')
    es_id = CharField(null=True, default="", verbose_name='对应es记录的id')
    accept_num = IntegerField(null=True, default=0, verbose_name='接受的行')


class AiE2ECaseTaskEvents(BaseModel):
    """用例步骤检索记录"""

    class Meta:
        table_name = 'ai_e2e_case_task_events'

    ai_e2e_case_task_id = CharField(index=True, verbose_name='用例生成任务id')
    status = CharField(verbose_name='状态', choices=AiE2ECaseConstant.AiE2ECaseTaskStatus.CHOICES)
    event_type = CharField(verbose_name='事件类型', choices=AiE2ECaseConstant.EVENTS_CHOICES)
    remark = TextField(default="", verbose_name='备注')
    data = JSONField(default={}, verbose_name='')
