#!/usr/bin/env python
# -*- coding: utf-8 -*-
from third_platform.base_manager import BaseManager
from config import CONFIG


class DifyConfig(BaseManager):
    base_url = CONFIG.app.DIFY.base_url
    user = CONFIG.app.DIFY.user

    # 默认类型，若出现错误则走默认
    DEFAULT_QUESTION_CATEGORY_TYPE = CONFIG.app.DIFY.DEFAULT_QUESTION_CATEGORY_TYPE
    DEFAULT_QUESTION_CATEGORY_KEY = CONFIG.app.DIFY.DEFAULT_QUESTION_CATEGORY_KEY
    # 规划应用,基于IDE的原始提问进行步骤规划
    PLANNING_APPLICATION_TYPE = CONFIG.app.DIFY.PLANNING_APPLICATION_TYPE
    PLANNING_APPLICATION_KEY = CONFIG.app.DIFY.PLANNING_APPLICATION_KEY
