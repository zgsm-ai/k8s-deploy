#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/24 17:06
"""
from pydantic import BaseModel
from typing import Union, Optional


class ManualCaseModel(BaseModel):
    case_code: str
    case_name: str
    case_pre_step: str
    case_step: str
    case_expect: str
    case_post_step: str
    case_level: str
    # 对应tp的用例路径
    case_module: str
    product_id: Optional[Union[int, str]]
    product_name: str
