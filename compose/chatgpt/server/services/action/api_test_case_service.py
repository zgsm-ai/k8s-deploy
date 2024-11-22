#!/usr/bin/env python
# -*- coding: utf-8 -*-

from services.action.base_service import ActionStrategy
from common.constant import ActionsConstant


class ApiTestCaseStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_CASE
    desc = "组合API接口测试: 生成测试点"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            tested_api=raw_data.get("tested_api"),
            pre_api_content=raw_data.get("pre_api_content"),
            post_api_content=raw_data.get("post_api_content"),
            api_diff_content=raw_data.get("api_diff_content"),
            exist_case=raw_data.get("exist_case")
        )
        return prompt


class ApiTestPointDocInspectorStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_POINT_DOC_INSPECTOR
    desc = "组合API接口测试: 校验API文档是否包含异常场景测试点详细响应描述"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            test_point=raw_data.get("test_point"),
            tested_api=raw_data.get("tested_api"),
        )
        return prompt


class ApiTestCaseRepeatVerifiedStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_CASE_REPEAT_VERIFIED
    desc = "组合API接口测试: 重复测试点校验"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            exist_case=raw_data.get("exist_case"),
            new_case=raw_data.get("new_case")
        )
        return prompt


class ApiTestParamTypeErrorVerifiedStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_PARAM_TYPE_ERROR_VERIFIED
    desc = "单API接口测试: 校验测试点是否为参数类型异常"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            test_point=raw_data.get("test_point")
        )
        return prompt


class ApiTestCaseModifyStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_CASE_MODIFY
    desc = "组合API接口测试: 更新旧用例步骤"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            test_point=raw_data.get("test_point"),
            test_steps=raw_data.get("test_steps"),
            old_test_steps=raw_data.get("old_test_steps"),
            tested_api=raw_data.get("tested_api"),
            api_diff_content=raw_data.get("api_diff_content"),
            api_del_content=raw_data.get("api_del_content")
        )
        return prompt


class ApiTestGenStepStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_GEN_STEP
    desc = "组合API接口测试: 生成测试用例步骤"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            test_point=raw_data.get("test_point"),
            tested_api=raw_data.get("tested_api"),
            all_api=raw_data.get("all_api"),
            api_odg=raw_data.get("api_odg"),
        )
        return prompt


class ApiTestGenODGStrategy(ActionStrategy):
    # 生成api接口依赖图
    name = ActionsConstant.API_TEST_GEN_ODG
    desc = "组合API接口测试: 接口操作依赖图生成"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            target_api=raw_data.get("target_api"),
            other_api=raw_data.get("other_api")
        )
        return prompt


class ApiTestSingleCaseStrategy(ActionStrategy):
    name = ActionsConstant.API_TEST_SINGLE_CASE
    desc = "组合API接口测试: 生成最终单个用例测试步骤和测试数据"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            test_steps=raw_data.get("test_steps"),
            test_point=raw_data.get("test_point"),
            tested_api=raw_data.get("tested_api"),
            pre_api_content=raw_data.get("pre_api_content"),
            post_api_content=raw_data.get("post_api_content")
        )
        return prompt
