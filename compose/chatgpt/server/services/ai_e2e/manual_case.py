#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/25 10:58
"""
import re
import logging

from collections import OrderedDict
from typing import Dict, Union, List
from pydantic import BaseModel

from common.exception.exceptions import ManualCaseError

logger = logging.getLogger(__name__)


class ManualCase(BaseModel):
    display_name: str
    # 用pydantic校验
    case_id: Union[int, str]
    case_code: str
    case_name: str
    case_pre_step: str
    case_step: str
    case_expect: str
    case_post_step: str
    case_level: str
    # 用例备注
    case_remark: str
    # 对应tp的用例路径
    case_module: str
    product_id: Union[int, str]
    product_name: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.handle_module()
        self.__case_structure = self.parse_test_case()
        self.__case_intent_cache = {}
        # 步骤和期望结果关系，通过ai识别后设置进来, 数据结构为二维数组
        self.__step_map_expect: List[List[str]] = []

    def handle_module(self):
        module_arr = self.case_module.split('/')
        # 模块例子: 基线/01-新架构用例基线/001-系统底座[bvt2948，手动1325-UI191]/06-网络部署/02-路由/01-静态路由
        # TODO: 当前仅用字符串判断，因为产品ID测试和线上环境不一样当前考虑也不完善，后续再考虑其他的扩展
        if self.product_name == 'AF':
            # AF定制逻辑
            if len(module_arr) < 3:
                # 小于长度3直接用原有的路径
                case_module = self.case_module
            else:
                # 路径大于3否则取第3级之后的，前两级目录一般是版本+目录
                module_arr = module_arr[2:]
                # AF的模块第一个元素格式是 001-系统底座[bvt3108，手动1325-UI113]，需要去掉中括号后面的内容
                module_arr[0] = module_arr[0].split('[')[0]
                # 去除掉前两级之后还是大于3级，则最多取3级
                if len(module_arr) >= 3:
                    case_module = '/'.join(module_arr[:3])
                else:
                    case_module = '/'.join(module_arr[2:])
        elif len(module_arr) >= 3:
            # 路径大于3否则取第3级之后的，前两级目录一般是版本+目录
            case_module = '/'.join(module_arr[2:])
        else:
            case_module = self.case_module
        self.case_module = case_module

    def set_case_intent_cache(self, case_intent: dict):
        """
        设置用例意图缓存
        @param case_intent: key是测试步骤，value 为提取出来的测试意图数据结构
        @return:
        """
        self.__case_intent_cache.update(case_intent)

    def set_step_map_expect(self, result: List[list]):
        """
        设置步骤和期望结果关系
        @param result: 二维数组，每个元素为步骤和期望结果的对应关系
        @return:
        """
        if self.__step_map_expect:
            # 已经存在不允许再次修改
            return
        step_list = self.steps_list
        expect_list = self.expect_list
        step_map_expect = []
        index_cache = -1
        last_expect_index = -10
        for item in result:
            step_index = item[0]
            if item[1] == "":
                expect_index = item[1]
            else:
                if last_expect_index == item[1]:
                    expect_index = index_cache
                else:
                    # 因为AI生成可能会把下标搞错，不会把空字符串搞错，所以这里自己计算下标
                    index_cache += 1
                    expect_index = index_cache
                last_expect_index = item[1]

            if isinstance(step_index, int) and isinstance(expect_index, int):
                step_map_expect.append([step_list[step_index], expect_list[expect_index]])
            elif isinstance(step_index, int) and expect_index == "":
                step_map_expect.append([step_list[step_index], ""])
            else:
                logger.error(f"步骤和期望结果识别错误: {result}")
                raise Exception(f"步骤和期望结果识别错误: {result}")
        else:
            if step_map_expect:
                self.__step_map_expect = step_map_expect

    @property
    def step_map_expect(self):
        return self.__step_map_expect

    @property
    def case_intent_cache(self):
        return self.__case_intent_cache

    @property
    def case_structure(self):
        # 只允许获取，不能修改
        return self.__case_structure

    @property
    def steps_list(self):
        return self.case_structure["步骤"]

    @property
    def expect_list(self):
        return self.case_structure["期望结果"]

    @property
    def pre_steps_list(self):
        return self.case_structure["前置条件"]

    @property
    def post_steps_list(self):
        return self.case_structure["后置条件"]

    def check_step(self):
        case_step = self.case_step.strip()
        # 去除&nbsp;标签
        case_step = re.sub(r'&nbsp;', '', case_step)
        # 去除<br />标签
        case_step = re.sub(r'<br\s*/*>', '', case_step)
        # 去除空格和换行符
        case_step = re.sub(r'\s+', '', case_step)
        # 去除数字和小数点
        case_step = re.sub(r'\d+|\.', '', case_step)
        if case_step == "":
            raise ManualCaseError("请检查步骤字段，内容过于简单，请完善后再进行生成")

    def parse_test_case(self) -> Dict[str, List[str]]:
        """
        解析测试用例文本，将其拆分为 '前置条件'，'步骤'，'期望结果' 和 '后置条件' 部分。
        @return: 包含解析结果的字典。
        规则如下：
        存在序号的情况

        按序号进行切割，以序号开头的是一个步骤的开始，直到下一个序号出现则为结束。
        序号以上的内容不当做步骤进行匹配历史步骤
        不存在序号的情况
        1.如果内容中没有序号存在，则按行切割
        """
        # 清洗掉图片
        self.case_pre_step = re.sub(r'<img src=.*?\/>', "", self.case_pre_step)
        self.case_step = re.sub(r'<img src=.*?\/>', "", self.case_step)
        self.case_expect = re.sub(r'<img src=.*?\/>', "", self.case_expect)
        self.case_post_step = re.sub(r'<img src=.*?\/>', "", self.case_post_step)
        self.case_remark = re.sub(r'<img src=.*?\/>', "", self.case_remark)
        sections = {
            "前置条件": [],
            "步骤": [],
            "期望结果": [],
            "后置条件": []
        }
        for index, text in enumerate([self.case_pre_step, self.case_step, self.case_expect, self.case_post_step]):
            if index == 0:
                current_section = "前置条件"
            elif index == 1:
                current_section = "步骤"
            elif index == 2:
                current_section = "期望结果"
            else:
                current_section = "后置条件"
            # 由于tp的字段是富文本，需要按照html的格式切割，并替换掉无用的html内容
            text = re.sub(r'<br.*?/*>', '\n', text, re.DOTALL)
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'<.*?>', '', text, re.DOTALL)
            text = text.strip()
            # 按序号找出所有的步骤
            lines = text.split('\n')
            step_list = []
            current_item = ''
            is_step_start = False
            for line in lines:
                stripped_line = line.strip()
                if re.match(r'^\d+[.、，,]', stripped_line):
                    if current_item:
                        step_list.append(current_item.strip())
                    current_item = stripped_line
                    is_step_start = True
                elif is_step_start:
                    current_item += f"\n{stripped_line}"
                else:
                    pass

            if current_item:
                step_list.append(current_item.strip())

            if step_list:
                # 去除每个匹配项的前后空白字符
                for step in step_list:
                    sections[current_section].append(step.strip())
            else:
                # 不存在序号的情况
                lines = text.splitlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        sections[current_section].append(line)
        return sections

    def convert_to_step_dict(self):
        """
        将解析后的测试用例转换为以指定结构
        @return: 转换后的指定数据结构。
        {
            "pre_step1": "xxx",
            "step1": "xxx",
            "post_step1": "xxx"
        }
        """
        case_structure = self.__case_structure
        result = dict()
        for i, content in enumerate(case_structure["前置条件"], 1):
            result[f"pre_step{i}"] = content
        for i, content in enumerate(case_structure["步骤"], 1):
            result[f"step{i}"] = content
        for i, content in enumerate(case_structure["后置条件"], 1):
            result[f"post_step{i}"] = content
        return result

    def convert_to_structure(self) -> Dict[str, List[dict]]:
        """
        将解析后的测试用例转化为指定的数据结构。
        @return: 转换后的指定数据结构。
        """
        result = OrderedDict([
            ("前置条件", []),
            ("步骤", []),
            ("期望结果", []),
            ("后置条件", [])
        ])
        case_structure = self.__case_structure
        # 处理前置条件
        for i, precondition in enumerate(case_structure["前置条件"], 1):
            result["前置条件"].append({
                "name": f"pre_step{i}",
                "content": precondition,
                "associated_steps": [],
                "associated_cli": [],
                "associated_api": [],
                "associated_keyword": []
            })

        # 处理步骤
        for i, step in enumerate(case_structure["步骤"], 1):
            result["步骤"].append({
                "name": f"step{i}",
                "content": step,
                "associated_steps": [],
                "associated_cli": [],
                "associated_api": [],
                "associated_keyword": []
            })

        # 处理期望结果
        for i, expect in enumerate(case_structure["期望结果"], 1):
            result["期望结果"].append({
                "name": f"expect{i}",
                "content": expect,
            })

        # 处理后置条件
        for i, post_step in enumerate(case_structure["后置条件"], 1):
            result["后置条件"].append({
                "name": f"post_step{i}",
                "content": post_step,
                "associated_steps": [],
                "associated_cli": [],
                "associated_api": [],
                "associated_keyword": []
            })

        return result

    def format_markdown(self, only_step=False):
        """
        将测试用例文本转换为Markdown格式。
        @param only_step: 是否只返回步骤部分
        @return: markdown 文本
        """

        pre_steps = "\n".join(self.__case_structure["前置条件"])
        steps = "\n".join(self.__case_structure["步骤"])
        expects = "\n".join(self.__case_structure["期望结果"])
        post_steps = "\n".join(self.__case_structure["后置条件"])
        step = (
            "### 前置条件\n"
            f"{pre_steps if pre_steps.strip() else '无'}\n"
            "### 步骤\n"
            f"{steps if steps.strip() else '无'}\n"
            "### 期望结果\n"
            f"{expects if expects.strip() else '无'}\n"
            "### 后置条件\n"
            f"{post_steps if post_steps.strip() else '无'}\n"
        )
        if only_step:
            return (
                "### 用例名称\n"
                f"{self.case_name}\n"
                f"{step}"
            )
        else:
            return (
                "### 用例名称\n"
                f"{self.case_name}\n"
                "### 用例ID\n"
                f"{self.case_code}\n"
                "### 系统ID\n"
                f"{self.case_id}\n"
                "### 用例级别\n"
                f"{self.case_level}\n"
                f"{step}"
                "### 用例备注\n"
                f"{self.case_remark}\n"
            )
