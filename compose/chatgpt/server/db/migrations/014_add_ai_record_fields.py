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
    migrator.add_fields(AIRecordAction, git_path=pw.CharField(default='', verbose_name='git仓库'))
    migrator.add_fields(AIRecordAction, analysis_result=pw.CharField(default='', max_length=1000,
                                                                     verbose_name='分析结果'))
    migrator.add_fields(AIRecordAction, process_state=pw.BooleanField(default=False, verbose_name='处理状态'))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_fields(AIRecordAction, git_path=pw.CharField(default='', verbose_name='git仓库'))
    migrator.remove_fields(AIRecordAction, analysis_result=pw.CharField(default='', max_length=1000,
                                                                        verbose_name='分析结果'))
    migrator.remove_fields(AIRecordAction, process_state=pw.BooleanField(default=False, verbose_name='处理状态'))
