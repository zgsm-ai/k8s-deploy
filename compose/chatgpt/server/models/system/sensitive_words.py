#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from models.base_model import BaseModel
from peewee import CharField

logger = logging.getLogger(__name__)


class SensitiveWords(BaseModel):
    """敏感词配置表"""

    class Meta:
        table_name = 'sensitive_words'

    sensitive_words = CharField(verbose_name='敏感词')
    permutation_words = CharField(verbose_name='置换词')

    def dict(self, *args, **kwargs):
        data = super().dict()
        return data
