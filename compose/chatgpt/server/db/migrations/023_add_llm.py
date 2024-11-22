#!/usr/bin/env python
# -*- coding: utf-8 -*-

import peewee as pw

from models.system.llm import LLM

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.create_model(LLM)


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_model(LLM)
