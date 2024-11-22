#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/8/27 17:17
"""
from typing import Generator

from services.ai_e2e.manual_case import ManualCase


class RobotResultHandle:
    # step后面3个空格，expect后面一个空格，保持上下可以对齐
    STEP_PREFIX = "#@step   "
    EXPECT_PREFIX = "#@expect "

    def __init__(self, result_generator: Generator, manual_case: ManualCase):
        self.result_generator = result_generator
        self.manual_case = manual_case

    def handle(self):
        step_map_expect = self.manual_case.step_map_expect
        pre_steps_list = self.manual_case.pre_steps_list
        post_steps_list = self.manual_case.post_steps_list
        step_index = 0
        pre_step_index = 0
        post_step_index = 0

        # 单行内容
        line_content = ""
        # 全部内容
        full_content = ""
        # 块缓存
        block_content = ""

        # 当前流式处于哪个部分
        section = ""
        # 是否进入步骤识别
        is_step = False
        # 是否进入期望结果识别
        is_expect = False
        # 是否进入setup/teardown
        is_setup_block = False
        is_teardown_block = False

        # 是否有前置条件
        is_need_pre = len(pre_steps_list) > 0
        # 是否有后置条件
        is_need_post = len(post_steps_list) > 0

        for content in self.result_generator:
            full_content += content
            line_content += content
            # 因为换行符不一定是单个token返回
            lines = line_content.split('\n')
            if len(lines) > 1:
                # 处理完整的一行
                line = f"{lines[0]}\n"
                # 后面的内容重新加入行缓存
                line_content = "\n".join(lines[1:])

                if '*** Test Cases ***' in line or '*** Test Case ***' in line:
                    section = "test_case"
                elif line.strip() == '_setup':
                    section = "_setup"
                    is_setup_block = True
                elif line.strip() == '_teardown':
                    section = "_teardown"
                    is_teardown_block = True

                if section == "test_case" and line.strip().startswith("#@step"):
                    is_step = True

                if section in ["_setup", "_teardown"] and line.strip().startswith("#@step"):
                    is_step = True

                if is_setup_block and not is_need_pre:
                    block_content += line
                    lines = block_content.splitlines()
                    # 判断代码块结束的标志是最后一行开头是没有缩进的
                    if len(lines) > 1 and not line.startswith(" ") and not line.isspace():
                        if is_teardown_block and not is_need_post:
                            block_content = line
                        else:
                            yield line
                            block_content = ""
                        is_setup_block = False
                    else:
                        continue

                elif is_teardown_block and not is_need_post:
                    block_content += line
                    lines = block_content.splitlines()
                    # 判断代码块结束的标志是最后一行开头是没有缩进的
                    if len(lines) > 1 and not line.startswith(" ") and not line.isspace():
                        if is_setup_block and not is_need_pre:
                            block_content = line
                        else:
                            yield line
                            block_content = ""
                        is_teardown_block = False
                    else:
                        continue

                elif is_step or is_expect:
                    if is_expect:
                        if section == "test_case":
                            step = step_map_expect[step_index]
                            expect = step[1]
                            if expect:
                                yield splice_content(line, expect, self.EXPECT_PREFIX)
                            step_index += 1
                        if not line.strip().startswith("#@expect"):
                            yield line
                        is_expect = False
                    else:
                        desc = ""
                        if section == "test_case":
                            step = step_map_expect[step_index]
                            desc = step[0]
                        elif section == "_setup":
                            desc = pre_steps_list[pre_step_index]
                            pre_step_index += 1
                        elif section == "_teardown":
                            desc = post_steps_list[post_step_index]
                            post_step_index += 1
                        if desc:
                            yield splice_content(line, desc, self.STEP_PREFIX)
                        # step 和 expect是相邻的, 也可能step下面没有expect
                        is_expect = True
                    is_step = False
                else:
                    if not (not is_need_pre and line.strip().startswith('Test Setup')) and not (
                            not is_need_post and line.strip().startswith('Test Teardown')):
                        yield line
        if line_content:
            # 如果最后没有以换行结尾，需要把剩下的也输出
            yield line_content


def splice_content(next_line: str, new_content: str, prefix_str: str):
    """
    拼接内容，保持缩进一致
    @param next_line:  示例   "    @expect 1. 未配置成功 xxxx \n"
    @param new_content:  示例    "1. 配置成功"
    @return:
    """
    # 找到第一个非空格字符的位置
    first_non_space_index = len(next_line) - len(next_line.lstrip())

    # 保留前面的空格
    leading_spaces = next_line[:first_non_space_index]

    # 拼接新的字符串
    if new_content.startswith(prefix_str):
        result = f"{leading_spaces}{new_content}\n"
    else:
        result = f"{leading_spaces}{prefix_str}{new_content}\n"
    return result
