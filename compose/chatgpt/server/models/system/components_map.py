#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/23 11:40
"""
from peewee import CharField

from models.base_model import BaseModel


class ComponentsMap(BaseModel):
    """组件库映射"""

    class Meta:
        table_name = 'components_map'

    team = CharField(max_length=50, verbose_name='团队名', help_text='唯一')
    git_repos = CharField(max_length=500, verbose_name='仓库路径匹配规则', help_text='可配置多项，支持正则')
    inline_chat_components = CharField(default='', verbose_name='划词对话相关组件库', help_text='多个值使用 , 分隔')
    fauxpilot_components = CharField(default='', verbose_name='代码自动补全相关组件库', help_text='多个值使用 , 分隔')

    def dict(self, *args, **kwargs):
        data = super().dict()
        # 查询时进行处理，返回列表
        data['inline_chat_components'] = data.get('inline_chat_components').split(',') if data.get(
            'inline_chat_components') else []
        data['fauxpilot_components'] = data.get('fauxpilot_components').split(',') if data.get(
            'fauxpilot_components') else []
        return data
