#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/23 14:36
"""

from dao.base_dao import BaseDao
from models.system.components_map import ComponentsMap


class ComponentsMapDao(BaseDao):
    model = ComponentsMap
