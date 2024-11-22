#!/usr/bin/env python
# -*- coding: utf-8 -*-
import peewee as pw

from models.system.api_test_case import ApiTestCaseTaskEvents

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.add_fields(ApiTestCaseTaskEvents,
                        gen_eoliner_task_id=pw.IntegerField(index=True, null=True, verbose_name='子记录id'))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_model(ApiTestCaseTaskEvents, "gen_eoliner_task_id")
