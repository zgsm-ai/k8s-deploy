#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dao.base_dao import BaseDao
from models.system.dify_agent import DifyAgentModel


class DifyAgentDao(BaseDao):
    model = DifyAgentModel
