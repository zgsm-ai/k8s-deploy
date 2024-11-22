#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    用于web2.0 表单生成代码的接口 的 prompt
    :作者: 卫聪w91323
    :时间: 2023/10/10
    :修改者: 卫聪w91323
    :更新时间: 2023/10/10
"""
from services.action.base_service import ActionStrategy, ChatRequestData
from services.action.generate_code_base_service import GenerateCodeBase
from template.generate_code import FORM_PROMPT
from common.constant import ActionsConstant, GenerateCodeAttr


class GenerateCodeByFormStrategy(GenerateCodeBase, ActionStrategy):

    name = ActionsConstant.GENERATE_CODE_BY_FORM
    generation_type_map = GenerateCodeAttr.GENERATION_TYPES

    def get_prompt(self, data: ChatRequestData):
        # 代码版本更新,如果传了prompt,走新的逻辑,旧版本不会传这个字段
        if data.raw_data.get("prompt"):
            return self.get_prompt_new(data)

        # 生成类型
        generation_type = data.raw_data.get("generation_type", "api_interface")
        # 技术栈
        program_stack = data.raw_data.get("program_stack", "")
        # 输入指令
        input_str = data.raw_data.get("input", "")
        # 输出指令
        output_str = data.raw_data.get("output", "")

        input_instructions = ''
        output_instructions = ''
        if input_str:
            input_instructions = "input content : {input} .".format(input=input_str)
        if output_str:
            output_instructions = "output content : {output} .".format(output=output_str)

        prompt = FORM_PROMPT.format(custom_instructions=data.custom_instructions,
                                    program_stack=program_stack,
                                    generation_type=self.generation_type_map.get(generation_type),
                                    input_instructions=input_instructions,
                                    output_instructions=output_instructions)
        return prompt

    def get_prompt_new(self, data):
        """
        代码版本更新 兼容旧的 所以这里写了新的函数
        raw_data:
        {
            "language": "python",
            "prompt": "python",
            "generation_type":
                {
                "key": "func",
                "prompt": "function",
                "form_fields": [{
                    "key": "input",
                    "value":"",
                    "prompt": "input params: {value}"
                },{
                    "key": "output",
                    "value":"",
                    "prompt": "output value: {value}"
                }]
            }
        }
        :param data:
        :return:仅限管理员登录
        """
        raw_data = data.raw_data
        # 语言的prompt
        language_prompt = raw_data.get("prompt")
        # 生成类型
        generation_type = raw_data.get("generation_type")
        generation_type_prompt = generation_type.get("prompt")
        generation_type_str = f"The result's content type is {generation_type_prompt}."
        form_fields = generation_type.get("form_fields")

        output_requirements = ""
        for form_field in form_fields:
            if form_field['value']:
                output_requirements += form_field['prompt'].format(value=form_field['value'])

        prompt_template = self.get_prompt_template()
        prompt = prompt_template.format(language=language_prompt,
                                        generation_type=generation_type_str if generation_type_prompt else "",
                                        output_requirements=output_requirements,
                                        requirement_desc=data.custom_instructions
                                        )
        return prompt
