#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/9/26 17:11
"""
import logging

from bot.bot_util import compute_tokens
from common.constant import GPTConstant
from common.exception.exceptions import PromptTokensError

logger = logging.getLogger(__name__)


class ScribeDialogueBase:
    """针对划词对话场景"""

    @staticmethod
    def check_prompt(prompt):
        """使用 gpt4 tokens长度限制"""
        tokens_num = compute_tokens(prompt)
        if tokens_num > GPTConstant.GPT4_MAX_TOKENS:
            logger.info(f'prompt tokens 超限: {tokens_num} > {GPTConstant.GPT4_MAX_TOKENS}')
            raise PromptTokensError()

    @staticmethod
    def check_params_prompt(prompt):
        """tokens长度限制（用户输入参数校验）"""
        tokens_num = compute_tokens(prompt)
        if tokens_num > GPTConstant.SCRIBE_MAX_PROMPT_TOKENS:
            logger.info(f'prompt tokens 超限: {tokens_num} > {GPTConstant.SCRIBE_MAX_PROMPT_TOKENS}')
            raise PromptTokensError()
