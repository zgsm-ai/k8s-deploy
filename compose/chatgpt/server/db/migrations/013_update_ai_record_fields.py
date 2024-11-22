#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/19 18:09
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
    AIRecordAction.update(is_accept=False, accept_num=0).where(AIRecordAction.is_accept >> None).execute()

    migrator.change_columns(AIRecordAction, is_accept=pw.BooleanField(default=False, verbose_name='是否接受'))
    migrator.change_columns(AIRecordAction, accept_num=pw.IntegerField(default=0, verbose_name='接受行数'))
    migrator.change_columns(AIRecordAction, refusal_cause=pw.CharField(default='', max_length=1000, verbose_name='拒绝原因'))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.change_columns(AIRecordAction, is_accept=pw.BooleanField(null=True, verbose_name='是否接受'))
    migrator.change_columns(AIRecordAction, accept_num=pw.IntegerField(null=True, verbose_name='接受行数'))
    migrator.change_columns(AIRecordAction, refusal_cause=pw.CharField(default='', verbose_name='拒绝原因'))
