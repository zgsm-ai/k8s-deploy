#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    用于web2.0 问答生成代码的接口 的 prompt
    :作者: 卫聪w91323
    :时间: 2023/10/10
    :修改者: 卫聪w91323
    :更新时间: 2023/10/10
"""
from services.action.base_service import ActionStrategy
from services.action.generate_code_base_service import GenerateCodeBase
from common.constant import ActionsConstant
from services.agents.agent_data_classes import ChatRequestData


class GenerateCodeByAskStrategy(GenerateCodeBase, ActionStrategy):
    name = ActionsConstant.GENERATE_CODE_BY_ASK

    def get_prompt(self, data: ChatRequestData):
        prompt_template = self.get_prompt_template()
        return prompt_template.format(custom_instructions=data.custom_instructions,
                                      code=data.code)
