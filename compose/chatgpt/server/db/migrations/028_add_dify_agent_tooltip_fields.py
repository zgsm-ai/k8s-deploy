#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 王政w27894
@Date    : 2024/9/11 18:09
"""
import peewee as pw

from models.system.dify_agent import DifyAgentModel

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.add_fields(DifyAgentModel, tooltip=pw.CharField(default='', null=True))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_fields(DifyAgentModel, 'tooltip')
