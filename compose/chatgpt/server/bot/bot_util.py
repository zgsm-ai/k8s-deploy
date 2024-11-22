#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/16 11:54
"""

import tiktoken
from flask import request

from common.constant import GPTModelConstant, GPTConstant, ActionsConstant
from common.exception.exceptions import ResourceNotFoundError
from config import conf


# encoding = tiktoken.get_encoding(TikTokenEncodeType.CL100K_BASE)


def compute_tokens(text: str) -> int:
    """计算 token 数"""
    # 注意这个加载需要消耗较大内存（1.4GB），使用的时候再加载，且需要访问外网...
    encoding = tiktoken.encoding_for_model(GPTModelConstant.GPT_TURBO)
    tokens_num = len(encoding.encode(text))
    return tokens_num


def combination_input_str(request_data: dict) -> str:
    """组合传参所有字符"""
    all_input_str = ''
    if not isinstance(request_data, dict):
        return ''
    for _, val in request_data.items():
        if isinstance(val, str):
            all_input_str += val

    return all_input_str


def get_chat_model(action: str = '', request_data: dict = None, is_ut: bool = False) -> str:
    """
    模型选用策略：
        优先选用 headers 参数指定 model
        其次选用 beta_keys 指定 model
        默认选用 gpt35-16k
    模型说明：
        gpt35：
            模型使用gpt-35-turbo-16k
        gpt4：
            模型使用gpt-4
        gpt4o：
            模型使用gpt-4o
    """
    model = request.headers.get('model')
    if model:
        model = model.lower()
        if model == GPTModelConstant.GPT_35:
            model = GPTModelConstant.GPT_35_16K
        return model

    beta_keys = request.cookies.get('beta_keys', '').split(",")
    # 返回一个列表，逗号分隔，支持多种 beta 功能启用。例如：gpt-4,custom-prompt
    # gpt35-16k
    if any(key in beta_keys for key in (GPTModelConstant.GPT_TURBO, GPTModelConstant.GPT_35_16K, GPTModelConstant.GPT_35)):
        model = GPTModelConstant.GPT_35_16K
    # gpt4
    elif is_ut:
        # 客户端验证，保证gpt_model是这里所具备的
        model = request_data["gpt_model"] if request_data.get("gpt_model") else GPTModelConstant.GPT_4
    elif action == ActionsConstant.SCRIBE or GPTModelConstant.GPT_4 in beta_keys:
        model = GPTModelConstant.GPT_4
    # gpt35-16k
    if model not in [GPTModelConstant.GPT_4, GPTModelConstant.GPT_4o]:
        model = GPTModelConstant.GPT_35_16K
    return model


def get_azure_deployment_id(model):
    """
    根据model及环境变量配置获取azure的deployment_id，若为空则直接抛异常
    """
    # 根据模型类型选择对应的deployment_id
    if model == GPTModelConstant.GPT_4o:
        engine = conf.get("azure_gpt4o_deployment_id")
    elif model == GPTModelConstant.GPT_4:
        engine = conf.get("azure_gpt4_deployment_id")
    elif model == GPTModelConstant.GPT_35_16K:
        engine = conf.get("azure_gpt35_16k_deployment_id")
    else:
        engine = conf.get("azure_gpt35_16k_deployment_id")
    if not engine:
        # gpt4和gpt35都不存在时使用默认deployment_id
        engine = conf.get("azure_gpt35_16k_deployment_id")
    if not engine:
        # engine不允许为空
        raise ResourceNotFoundError("azure deployment_id is not exist!")
    return engine


def get_prompt_max_tokens(model: str) -> int:
    """
    根据模型获取 限制 token数
    """
    if model in [GPTModelConstant.GPT_4, GPTModelConstant.GPT_4o]:
        return GPTConstant.GPT4_MAX_TOKENS
    return GPTConstant.GPT35_16K_MAX_TOKENS
