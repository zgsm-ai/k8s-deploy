#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 陈烜 42766
    :更新时间: 2023/3/24 14:12
"""
import re
from services.action.base_service import ActionStrategy, ChatbotOptions
from services.agents.agent_data_classes import ChatRequestData
from services.search.duckduckgo_service import duckduckgo_search_service
from common.constant import ActionsConstant
from template.lanjun_classification import CATEGORIES_MAP


class LanjunClassificationStrategy(ActionStrategy):
    name = ActionsConstant.LANJUN_CLASSIFICATION
    unknown_result = "unknown"

    def get_search_result(self, data: ChatRequestData):
        comp = self.get_comp(data)
        return duckduckgo_search_service.search(comp)

    def get_systems(self, data: ChatRequestData = None, options: ChatbotOptions = None):
        # 基于搜索内容构造 systems
        search_result = self.get_search_result(data)
        return [
            # noqa: E502
            "You are a component classification system that can access the internet, please provide a result " \
            "if possible. Internet search results will be sent from the system in JSON format. " \
            "Based on search results, improve your subsequent answers.",
            "Search result: {}".format(search_result)
        ]

    def get_comp(self, data: ChatRequestData):
        return data.prompt

    def get_ai_result(self,
                      comp: str,
                      label: str,
                      result_pattern: str,
                      data: ChatRequestData,
                      options: ChatbotOptions = None):
        prompt_tmp = self.get_prompt_tmp(label)
        # 不需要保留上下文
        options.context_association = False
        data.prompt = prompt_tmp.format(comp=comp)
        result = self.ask(data, options) or {}
        raw_result = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        # 防止 comp 名称影响正则分类结果提取
        match = re.search(result_pattern, raw_result.replace(comp, ""))
        if match:
            return match.group(0), raw_result
        else:
            return self.unknown_result, raw_result

    def make_result(self, data: ChatRequestData, options: ChatbotOptions = None):
        comp = self.get_comp(data)
        first_result, raw_result = self.get_ai_result(comp, "first", r"\d{3}", data, options)
        if first_result == self.unknown_result:
            return {
                "success": False,
                "result": self.unknown_result,
                "ai_answer": raw_result
            }
        result, raw_result = self.get_ai_result(comp, first_result, r"\d{8}", data, options)
        return {
            "success": result != self.unknown_result,
            "result": result,
            "ai_answer": raw_result
        }

    def get_prompt_tmp(self, label):
        categories = CATEGORIES_MAP.get(label)
        return """
记住以下分类与其对应的 ID:
""" + str(categories) + \
            """

简明扼要的回答 "{comp}" 最合适的分类 ID, 不要携带解释说明等信息. 如果无法作出判断，只需回复 "unknown".
"""
