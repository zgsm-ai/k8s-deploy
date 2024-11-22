#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 黄伟伦z24224
@Date    : 2023/11/16 18:09
"""
import peewee as pw

from models.system.ai_record import AIRecordAction

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.change_columns(AIRecordAction, origin_prompt=pw.TextField(null=True, default='', verbose_name='用户原始的问答内容'))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.change_columns(AIRecordAction, origin_prompt=pw.CharField(null=True, default='', verbose_name='用户原始的问答内容'))
