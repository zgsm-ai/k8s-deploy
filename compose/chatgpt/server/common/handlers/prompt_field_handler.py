#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/17 10:49
    :修改者: 苏德利 16646
    :更新时间: 2023/3/17 10:49
"""

from common.handlers.base_field_handler import BaseFieldHandler


class PromptFieldHandler(BaseFieldHandler):

    def __init__(self):
        super(PromptFieldHandler, self).__init__()

    def get_field_type(self, field_key):
        if field_key == "create_at":
            return "datetime"


prompt_field_handler = PromptFieldHandler()
