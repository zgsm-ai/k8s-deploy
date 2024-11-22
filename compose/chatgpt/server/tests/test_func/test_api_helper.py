#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/3/18 20:02
"""

from services.api_test.eolinker_api_helper import ApiHelper, EolinkerDataHandler
from common.eolinker_constant import REQUEST_TYPE, ApiMarkdownKeyword
from tests.mock.mock_api_test import MOCK_API_INFO1, MOCK_API_INFO2, MOCK_API_INFO3
from tests.mock.mock_rel_param import (
    MOCK_PARAM_1,
    MOCK_PARAM_2,
    MOCK_PARAM_3,
    MOCK_PARAM_4,
    MOCK_PARAM_5,
    MOCK_PARAM_6,
    MOCK_STEP_NUM_ID_DICT,
    MOCK_PARAM_RES_1,
    MOCK_PARAM_RES_2,
    MOCK_PARAM_RES_3,
    MOCK_PARAM_RES_4,
    MOCK_PARAM_RES_5,
    MOCK_PARAM_RES_6
)


def test_to_markdown1():
    api_helper = ApiHelper(MOCK_API_INFO1)
    md = api_helper.to_markdown()
    assert ApiMarkdownKeyword.URL_PARAM in md
    assert ApiMarkdownKeyword.RESTFUL_PARAM in md
    assert ApiMarkdownKeyword.PARAMS in md
    assert ApiMarkdownKeyword.RESULT in md
    assert REQUEST_TYPE.get(0) in md
    assert ApiMarkdownKeyword.API_ID in md


def test_to_markdown2():
    # 引用了数据结构的api
    api_helper = ApiHelper(MOCK_API_INFO2)
    md = api_helper.to_markdown()
    # 断言请求数据结构引用
    assert "DataSource>>status" in md
    # 断言请求嵌套数据结构引用
    assert "group>>group>>data" in md
    # 断言响应体中数据结构引用
    assert "data>>data" in md


def test_to_markdown3():
    # 引用了数据结构的api
    api_helper = ApiHelper(MOCK_API_INFO3)
    md = api_helper.to_markdown()
    # 断言请求数据结构引用
    assert "DataSource>>status" in md
    # 断言响应数据结构引用
    assert "|code|" in md


def test_deal_param_info():
    # 测试ai返回参数提取函数
    EolinkerDataHandler.deal_param_info(MOCK_PARAM_1, MOCK_STEP_NUM_ID_DICT)
    assert MOCK_PARAM_1.get("param_info") == MOCK_PARAM_RES_1

    EolinkerDataHandler.deal_param_info(MOCK_PARAM_2, MOCK_STEP_NUM_ID_DICT)
    assert MOCK_PARAM_2.get("param_info") == MOCK_PARAM_RES_2

    EolinkerDataHandler.deal_param_info(MOCK_PARAM_3, MOCK_STEP_NUM_ID_DICT)
    assert MOCK_PARAM_3.get("param_info") == MOCK_PARAM_RES_3

    EolinkerDataHandler.deal_param_info(MOCK_PARAM_4, MOCK_STEP_NUM_ID_DICT)
    assert MOCK_PARAM_4.get("param_info") == MOCK_PARAM_RES_4

    EolinkerDataHandler.deal_param_info(MOCK_PARAM_5, MOCK_STEP_NUM_ID_DICT)
    assert MOCK_PARAM_5.get("param_info") == MOCK_PARAM_RES_5

    EolinkerDataHandler.deal_param_info(MOCK_PARAM_6, MOCK_STEP_NUM_ID_DICT)
    assert MOCK_PARAM_6.get('child_list')[0].get('child_list')[0].get("param_info") == MOCK_PARAM_RES_6
