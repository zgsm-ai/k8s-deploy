#!/usr/bin/env python
# -*- coding: utf-8 -*-
import peewee as pw

from models.system.api_test_case import ApiTestCaseTask
from common.constant import ApiTestCaseConstant

try:
    import playhouse.postgres_ext as pw_pext
except ImportError:
    pass

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Write your migrations here."""
    migrator.add_fields(ApiTestCaseTask,
                        test_case_stage=pw.CharField(default=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST,
                                                     verbose_name='测试用例类型，区分API管理页面和API自动化测试页面用例'))


def rollback(migrator, database, fake=False, **kwargs):
    """Write your rollback migrations here."""
    migrator.remove_model(ApiTestCaseTask, "test_case_type")
