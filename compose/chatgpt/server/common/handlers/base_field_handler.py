#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/16 20:51
    :修改者: 苏德利 16646
    :更新时间: 2023/3/16 20:51
"""

from peewee import CharField, BooleanField, DateTimeField, IntegerField, ForeignKeyField, BigIntegerField, TextField
import logging


class BaseFieldHandler:

    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

    def __init__(self):
        self.model = None

    def get_field_type(self, field_key):
        if "_id" in field_key:
            new_key = field_key.replace("_id", "")
            if hasattr(self.model, new_key) and isinstance(getattr(self.model, new_key), ForeignKeyField):
                return 'fk'
        if hasattr(self.model, field_key) is False:
            print(f"无此属性：{field_key}")
            return None
        if isinstance(getattr(self.model, field_key), CharField):
            return 'string'
        elif isinstance(getattr(self.model, field_key), ForeignKeyField):
            return 'fk'
        elif isinstance(getattr(self.model, field_key), DateTimeField):
            return 'datetime'
        elif isinstance(getattr(self.model, field_key), BooleanField):
            return 'bool'
        elif isinstance(getattr(self.model, field_key), IntegerField):
            return 'int'
        elif isinstance(getattr(self.model, field_key), BigIntegerField):
            return 'int'
        elif isinstance(getattr(self.model, field_key), TextField):
            return 'string'

    def gen_origin_field_key(self, field_key):
        return field_key


base_field_handler = BaseFieldHandler()
