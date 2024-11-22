#!/usr/bin/env python
# -*- coding: utf-8 -*-
import peewee as pw

from models.system.api_test_case import ApiTestCaseTask

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.create_model(ApiTestCaseTask)


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_model(ApiTestCaseTask)
