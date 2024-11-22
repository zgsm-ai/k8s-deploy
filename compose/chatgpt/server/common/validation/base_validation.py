#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/24 15:10
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : base_validation.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : 数据模型定义


from pydantic import BaseModel, Field
from typing import List


# 定义预期的数据模型
class ApiTestRequestModel(BaseModel):
    api_info: dict
    api_platform: str
    testcase_type: str
    authorization: str  # eolinker php token
    stream: bool
    response_format: str = Field(default="json_object", description="定义返回格式")
    action: str = Field(default="generateApiTestPoint", description="调度AI的行为字段，用于区分不同业务场景")
    test_points: list = Field(default=[], description="测试点，生成测试集时需要改参数")


class VersionRequestModel(BaseModel):
    current_version: str


class TestCase(BaseModel):
    case_id: int
    case_name: str
    is_selected: bool


class ApiHistory(BaseModel):
    id: int
    update_time: str


class ApiIdInfo(BaseModel):
    api_id: int
    project_id: str
    current_history: ApiHistory = Field(default={"id": 0, "update_time": ""})
    old_history: ApiHistory = Field(default={"id": 0, "update_time": ""})
    api_relation_testcase_list: List[TestCase] = Field(default=[])


class BaseApiIdInfo(BaseModel):
    api_id: int
    project_id: str


class ApiTestCaseTaskRequestModel(BaseModel):
    space_id: str  # 工作空间key
    project_id: str  # 项目哈希key
    authorization: str  # eolinker php token
    # case_name: str = Field(default="千流AI生成用例", description="用例名称，实际在eolinker是必填")
    module: int = Field(default=0, description="用例类型 默认普通用例，0普通用例，1模板用例")
    group_id: int = Field(default=1, description="组ID，默认为1")
    priority: int = Field(default=0, description="优先级，值域0-9对应P1-P9")
    case_style: str = Field(default="general", description="用例类型arrange图形，general通用")
    case_tag: str = Field(default="千流AI", description="标签")
    case_type: int = Field(default=0, description="默认值0")
    pre_api_list: List[BaseApiIdInfo] = Field(...)
    api_list: List[ApiIdInfo] = Field(...)
    post_api_list: List[BaseApiIdInfo] = Field(...)
    api_case_id: List[int] = Field(default_factory=list)
