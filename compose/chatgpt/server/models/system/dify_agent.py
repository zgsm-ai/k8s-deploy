#!/usr/bin/env python
# -*- coding: utf-8 -*-
from peewee import CharField, TextField, BooleanField

from models.base_model import BaseModel
from common.constant import DifyAgentConstant


class DifyAgentModel(BaseModel):
    """dify agent 配置"""

    class Meta:
        table_name = 'dify_agent'

    display_name = CharField(default='', verbose_name='展示名称')
    dify_key = CharField(default='', verbose_name='dify 应用key')
    dify_typo = CharField(default='', verbose_name='dify 应用类型')
    dify_url = CharField(null=True, default='', verbose_name='dify 地址. 不填默认选配置文件中的地址')
    description = TextField(null=True, default='', verbose_name='应用描述')
    is_first = BooleanField(null=True, default=False, verbose_name='是否为初始应用')
    is_last = BooleanField(null=True, default=False, verbose_name='是否为最后一个应用')
    role = CharField(null=True, default='', verbose_name='应用角色', choices=DifyAgentConstant.ROLE_CHOICES)
    icon = CharField(null=True, default='', verbose_name='头像地址')
    tooltip = CharField(null=True, default='', verbose_name='展示说明')
