#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/25 14:17
"""
from third_platform.base_manager import BaseManager
from config import CONFIG


class KsConfig(BaseManager):
    base_url = CONFIG.app.KnowledgeSeeker.base_url
    user = CONFIG.app.KnowledgeSeeker.user
    token = CONFIG.app.KnowledgeSeeker.token
