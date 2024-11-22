#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/8/27 20:37
"""
from tests.mock.mock_robot_content import (
    mock_robot_case,
    mock_step_map_expect,
    mock_no_post_expect_result,
    mock_manual_case_data_no_post,
    mock_no_pre_expect_result,
    mock_manual_case_data_no_pre
)
from services.ai_e2e.result_handle import RobotResultHandle
from services.ai_e2e.manual_case import ManualCase


def gen_robot_case():
    for item in mock_robot_case:
        yield item


def test_robot_result_handle():
    # 测试没有前置
    manual_case = ManualCase(**mock_manual_case_data_no_pre)
    manual_case.set_step_map_expect(mock_step_map_expect)
    robot_result_handle = RobotResultHandle(gen_robot_case(), manual_case)
    pre_content = ""
    for i in robot_result_handle.handle():
        pre_content += i
    assert pre_content.strip().strip('\n') == mock_no_pre_expect_result.strip().strip('\n')

    # 测试没有后置
    manual_case = ManualCase(**mock_manual_case_data_no_post)
    manual_case.set_step_map_expect(mock_step_map_expect)
    robot_result_handle = RobotResultHandle(gen_robot_case(), manual_case)
    post_content = ""
    for i in robot_result_handle.handle():
        post_content += i
    assert post_content.strip().strip('\n') == mock_no_post_expect_result.strip().strip('\n')
