#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from models.base_model import BaseModel
from peewee import CharField

logger = logging.getLogger(__name__)


class Application(BaseModel):
    """应用配置表"""

    class Meta:
        table_name = 'application'

    application_name = CharField(unique=True, verbose_name='应用名称')
    application_key = CharField(verbose_name='应用 key', default='')

    def dict(self, *args, **kwargs):
        data = super().dict()
        return data
