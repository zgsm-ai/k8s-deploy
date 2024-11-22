#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/06 11:32
# @Author  : 刘鹏z10807
# @Contact : z10807@sangfor.com
# @File    : generate_api_test_set.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : 生成API测试集

from common.constant import ActionsConstant
from services.action.base_service import ActionStrategy


class GenerateApiTestSetStrategy(ActionStrategy):
    name = ActionsConstant.GENERATE_API_TEST_SET
    desc = "单API接口测试: 生成测试集"

    def get_prompt(self, data):
        api_info = data.api_info
        prompt_template = self.get_prompt_template()
        prompt = prompt_template\
            .replace('{api_name}', api_info.get("api_name"))\
            .replace('{api_url}', api_info.get("api_url"))\
            .replace('{api_request_type}', api_info.get("api_request_type"))\
            .replace('{url_param}', api_info.get("api_url_param"))\
            .replace('{api_url_param_desc}', api_info.get("api_url_param_desc"))\
            .replace('{api_request_info_desc}', api_info.get("api_info_desc"))\
            .replace('{test_points}', data.raw_data.get('test_points', ''))
        return prompt
