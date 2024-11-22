#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from common.constant import LLMCombinationType, LLMRank, LLMType, LLMProvider
from models.base_model import BaseModel
from peewee import CharField, BooleanField, IntegerField, FloatField
from db.custom_field import JSONField

logger = logging.getLogger(__name__)


class LLM(BaseModel):
    """大模型配置表"""

    class Meta:
        table_name = 'llm'

    model_name = CharField(verbose_name='模型名称')
    model_type = CharField(verbose_name='模型类型', choices=LLMType.LLM_TYPE_CHOICES)
    model_identification = CharField(unique=True, verbose_name='模型标识,全局唯一')
    url = CharField(null=True, verbose_name='请求地址')
    authentication_data = JSONField(null=True, verbose_name='模型鉴权相关参数')

    provider = CharField(null=True, verbose_name='供应商', choices=LLMProvider.LLM_PROVIDER_CHOICES)
    max_input_tokens = IntegerField(null=True, default=1500, verbose_name='支持输入的最长tokens数')
    max_tokens = IntegerField(null=True, default=3000, verbose_name='支持输出的最长token数')
    weight = FloatField(null=True, verbose_name='权重，模型负载均衡使用参数')

    combination_type = CharField(default='', verbose_name='类型：单一模型、组合模型',
                                 choices=LLMCombinationType.COMBINATION_TYPE_CHOICES)
    model_combination = CharField(null=True, verbose_name='模型标识组合列表, 逗哈分割')

    belong_to = CharField(default='', verbose_name='系统级别、用户级别', choices=LLMRank.RANK_CHOICES)
    active = BooleanField(default=False, verbose_name='启用、禁用')
    need_sensitization = BooleanField(default=False, verbose_name='是否需要敏感词处理')

    def dict(self, *args, **kwargs):
        data = super().dict()
        return data
