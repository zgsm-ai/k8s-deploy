#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/9/22 10:48
"""
import json
import logging

from bot.bot_util import compute_tokens
from common.constant import ActionsConstant, GPTConstant
from common.exception.exceptions import PromptTokensError
from common.utils.util import process_code_just, get_work_id_by_display_name, get_second_dept
from services.action.base_service import ActionStrategy, ChatbotOptions
from services.system.configuration_service import ConfigurationService
from third_platform.services.analysis_service import analysis_service
from services.agents.agent_data_classes import ChatRequestData

logger = logging.getLogger(__name__)


class GiveAdviceStrategy(ActionStrategy):
    name = ActionsConstant.GIVE_ADVICE

    @staticmethod
    def check_prompt(prompt):
        """tokens长度限制"""
        tokens_num = compute_tokens(prompt)
        if tokens_num > GPTConstant.SCRIBE_MAX_PROMPT_TOKENS:
            logger.info(f'prompt tokens 超限: {tokens_num} > {GPTConstant.SCRIBE_MAX_PROMPT_TOKENS}')
            raise PromptTokensError()

    def get_prompt(self, data: ChatRequestData):
        prompt_template = self.get_prompt_template()
        code = data.raw_data.get("code") if data.raw_data.get("code") != "" else "无"
        prompt = prompt_template \
            .replace("{user_prompt}", data.raw_data.get("prompt")) \
            .replace("{code}", code)

        return prompt

    def make_result(self, data: ChatRequestData, options: ChatbotOptions = None):
        # 用户的原始问答内容
        advice = {"is_problem": False, "result": [], "understand": True, "msg": ""}
        origin_prompt = data.raw_data.get("prompt")

        default_data = {
            "data": {
                "id": "",
                "advice": advice,
                "origin_prompt": origin_prompt
            }
        }

        ask_gpt = self.ask_gpt_by_white_list_switch(data)
        # 不用问gpt， 直接返回默认数据
        if ask_gpt is False:
            return default_data

        result = self.ask(data, options=options)
        # 提取markdown中的json
        result = process_code_just(result)

        if (len(result["choices"])):
            try:
                advice = json.loads(str(result["choices"][0]['message']["content"]).strip())
            except Exception as e:
                logging.error("转化格式失败: result: " + str(result) + " error: " + str(e))
                advice = {"is_problem": False, "result": [], "understand": True, "msg": ""}

        return {
            "data": {
                "id": result.get("id"),
                "advice": advice,
                "origin_prompt": origin_prompt,
            }
        }

    def ask_gpt_by_white_list_switch(self, data):
        """ 根据白名单开卡来判断是否 需要询问 gpt 去获取建议"""
        # 获取用户的部门
        work_id = get_work_id_by_display_name(data.raw_data.get("display_name", ''))
        dept = analysis_service.get_user_multilevel_dept(work_id)
        second_dept = get_second_dept(dept)
        logging.info("当前二级部门 " + str(second_dept))
        in_white_list = False
        # 默认白名单的开关是打开的 (打开后，则需要配置白名单，只针对白名单内的部门生效， 如果关闭的话则不验证白名单，所有部门均生效)
        white_list_switch = True
        try:
            # 没有配置，则默认不问gpt 直接返回 默认数据
            advice_switch_json_str = ConfigurationService.get_configuration("permission", "advice_white_list_switch")
            if not advice_switch_json_str:
                logging.info("（无建议）没有获取到开关配置，则默认是打开的状态")
                return False

            white_list_switch_json = json.loads(advice_switch_json_str)
            white_list_switch = True if white_list_switch_json.get('advice_switch') is True else False
            if white_list_switch:
                for item in white_list_switch_json.get("dept_prefix"):
                    if second_dept in item:
                        in_white_list = True
                        break
        except Exception as e:
            logging.error("（无建议）开关逻辑异常: error: " + str(e))
            return False

        # 没有打开白名单的开关 则 需要问gpt 给出建议
        if white_list_switch is False:
            return True

        # 如果开关是打开的， 并且 用户不在白名单中，则不给出建议，直接返回数据
        if white_list_switch is True and in_white_list is False:
            logging.info("（无建议）语言规范化白名单开关: " + str(white_list_switch) + " 是否存在白名单：" + str(in_white_list))
            return False
        else:
            return True
