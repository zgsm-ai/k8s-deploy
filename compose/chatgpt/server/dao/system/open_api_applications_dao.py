#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/20 9:28
"""

from dao.base_dao import BaseDao
from models.system.open_api_applications import OpenApiApplication


class OpenApiApplicationDao(BaseDao):
    model = OpenApiApplication

    @classmethod
    def update_state(cls, obj, value):
        obj.state = value
        obj.save()
        return obj
