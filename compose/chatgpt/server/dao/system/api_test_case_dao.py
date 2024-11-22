#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dao.base_dao import BaseDao
from models.system.api_test_case import ApiTestCaseTask, ApiTestCaseTaskEvents, \
    ApiTestEolinkerCaseTask


class ApiTestCaseTaskDao(BaseDao):
    model = ApiTestCaseTask


class ApiTestEolinkerCaseTaskDao(BaseDao):
    model = ApiTestEolinkerCaseTask


class ApiTestCaseTaskEventsDao(BaseDao):
    model = ApiTestCaseTaskEvents
