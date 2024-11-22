#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/12/11 15:49
"""
import peewee as pw

from db.custom_field import JSONField
from models.system.ai_record import AIRecordAction

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.add_fields(AIRecordAction, history=JSONField(default=[], verbose_name='追问历史'))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_fields(AIRecordAction, history=JSONField(default=[], verbose_name='追问历史'))
