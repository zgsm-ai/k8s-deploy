#!/usr/bin/env python
# -*- coding: utf-8 -*-
import peewee as pw

from models.ai_e2e.ai_e2e_case_task import AiE2ECaseTask, AiE2ECaseTaskEvents

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.create_model(AiE2ECaseTask)
    migrator.create_model(AiE2ECaseTaskEvents)


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_model(AiE2ECaseTaskEvents, cascade=True)
    migrator.remove_model(AiE2ECaseTask, cascade=True)
