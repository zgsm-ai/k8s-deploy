#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/06 11:32
# @Author  : 刘鹏z10807
# @Contact : z10807@sangfor.com
# @File    : generate_api_test_point.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : 生成API测试点

from common.constant import ActionsConstant
from services.action.base_service import ActionStrategy
from services.system.configuration_service import ConfigurationService


class GenerateApiTestPointStrategy(ActionStrategy):
    name = ActionsConstant.GENERATE_API_TEST_POINT
    desc = "单API接口测试: 生成测试点"

    def get_prompt(self, data):
        api_info = data.api_info
        # 一期只支持xdr，这里先写死，后面需要扩展其他业务线再添加相关逻辑
        test_range = ConfigurationService.get_api_test_range("xdr")
        prompt_template = self.get_prompt_template()
        prompt = prompt_template\
            .replace('{test_range}', str(test_range))\
            .replace('{api_name}', api_info.get("api_name"))\
            .replace('{api_url}', api_info.get("api_url"))\
            .replace('{api_request_type}', api_info.get("api_request_type"))\
            .replace('{url_param}', api_info.get("api_url_param"))\
            .replace('{api_url_param_desc}', api_info.get("api_url_param_desc"))\
            .replace('{api_request_info_desc}', api_info.get("api_info_desc"))\
            .replace('{waiting_test_param}', api_info.get("waiting_test_param"))
        return prompt
