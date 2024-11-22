#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import tiktoken

logger = logging.getLogger(__name__)


def get_message_tokens(message: dict):
    """
    计算单个message的token数
    :return:
    """
    num_tokens = 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
    for key, value in message.items():
        num_tokens += compute_tokens(value)
        if key == "name":  # if there's a name, the role is omitted
            num_tokens += -1  # role is always required and always 1 token
    return num_tokens


def compute_tokens(text: str) -> int:
    """计算 token 数"""
    # 注意这个加载需要消耗较大内存（1.4GB），使用的时候再加载，且需要访问外网...
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens_num = len(encoding.encode(text))
    return tokens_num
