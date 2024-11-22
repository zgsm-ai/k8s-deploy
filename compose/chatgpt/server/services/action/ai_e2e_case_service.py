#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/25 10:18
"""
from services.action.base_service import ActionStrategy
from common.constant import ActionsConstant


class AiE2EManualCaseCheckStrategy(ActionStrategy):
    name = ActionsConstant.E2E_MANUAL_CASE_CHECK
    desc = "E2E用例: 检查手工用例规范性"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            test_case=raw_data.get("test_case"),
        )
        return prompt


class AiE2EIdentifyRelationshipsStrategy(ActionStrategy):
    name = ActionsConstant.E2E_IDENTIFY_RELATIONSHIPS
    desc = "E2E用例: 步骤和期望结果关系识别"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            step_desc=raw_data.get("step_desc"),
            expect_result=raw_data.get("expect_result"),
        )
        return prompt


class AiE2EStepIntentExtractStrategy(ActionStrategy):
    name = ActionsConstant.E2E_STEP_INTENT_EXTRACT
    desc = "E2E用例: 手工步骤的意图提取"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(
            step_desc=raw_data.get("step_desc"),
        )
        return prompt


class AiE2ERagFilterStrategy(ActionStrategy):
    name = ActionsConstant.E2E_RAG_FILTER
    desc = "E2E用例: 过滤rag检索的结果"

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


class AiE2ECaseGenStrategy(ActionStrategy):
    name = ActionsConstant.E2E_CASE_GEN
    desc = "E2E用例: 生成自动化用例"

    def get_prompt(self, data):
        raw_data = data.raw_data
        prompt_template = self.get_prompt_template()

        # 定义需要获取的字段及其默认值
        fields = {
            "associated_keywords": "无",
            "associated_steps": "无",
            "associated_cli": "无",
            "associated_api": "无"
        }

        # 获取字段值，如果不存在则使用默认值
        for field, default in fields.items():
            fields[field] = raw_data.get(field, default)

        prompt = prompt_template.format(
            test_case=raw_data.get("test_case"),
            associated_graph=raw_data.get("associated_graph"),
            associated_keywords=fields["associated_keywords"],
            associated_steps=fields["associated_steps"],
            associated_cli=fields["associated_cli"],
            associated_api=fields["associated_api"],
            # example=raw_data.get("example")  # 示例后面再动态
        )
        return prompt
