#!/usr/bin/python
# -*- coding:utf-8 -*-
# @author  : 王政
# @time    : 2024/9/10 15:03
# @desc:
import re
import logging
from collections import defaultdict
from typing import List, Dict, Union, Tuple

from common.utils.str_util import StrUtil

logger = logging.getLogger(__name__)


class RobotParser:
    """
    分割robot用例成指定格式
    """

    # 解析设置正则
    PARSE_SETTING = (r"\*{1,3} (Settings|Setting) \*{1,3}(((?!\*{1,3} "
                     r"(Test Cases|Test Case|Variables|Variable|Keywords|Keyword|Settings|Setting) \*{1,3})"
                     r"[\s\S])*)")
    # 解析变量正则
    PARSE_VARIABLE = (r"\*{1,3} (Variables|Variable) \*{1,3}(((?!\*{1,3} "
                      r"(Test Cases|Test Case|Variables|Variable|Keywords|Keyword|Settings|Setting) \*{1,3})"
                      r"[\s\S])*)")
    # 解析测试用例正则
    PARSE_TESTCASE = (r"\*{1,3} (Test Cases|Test Case) \*{1,3}(((?!\*{1,3} "
                      r"(Test Cases|Test Case|Variables|Variable|Keywords|Keyword|Settings|Setting) \*{1,3})"
                      r"[\s\S])*)")
    # 解析关键字正则
    PARSE_KEYWORD = (r"\*{1,3} (Keywords|Keyword) \*{1,3}(((?!\*{1,3} "
                     r"(Test Cases|Test Case|Variables|Variable|Keywords|Keyword|Settings|Setting) \*{1,3})"
                     r"[\s\S])*)")

    def __init__(self, text: str):
        self.text = text
        self.setting_section = self.re_parse_section(self.PARSE_SETTING)
        self.variable_section = self.re_parse_section(self.PARSE_VARIABLE)
        self.testcase_section = self.re_parse_section(self.PARSE_TESTCASE)
        self.keyword_section = self.re_parse_section(self.PARSE_KEYWORD)

        self.testcase_list = self.split_by_indentation(self.testcase_section)
        self.keyword_list = self.split_by_indentation(self.keyword_section)

    def re_parse_section(self, pattern: str) -> str:
        result = re.findall(pattern, self.text)
        return result[0][1].strip('\n') if result else ''

    @staticmethod
    def split_by_indentation(text):
        """
        按缩进拆分文本
        :param text: 包含要拆分的文本
        :return: 按缩进拆分后的文本块列表
        """
        # 如果文本为空，返回空列表
        if not text:
            return []

        # 按行分割文本
        lines = text.split('\n')

        # 初始化存储文本块的列表
        blocks = []

        # 初始化当前文本块
        current_block = []

        # 遍历每一行
        for line in lines:
            # 如果行以空格或制表符开头，表示是当前块的一部分
            if line.startswith(' ') or line.startswith('\t'):
                current_block.append(line)
            elif not line:
                continue
            else:
                # 如果当前块不为空，将其加入块列表
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                # 将当前行作为新的块的开始
                current_block.append(line)

        # 如果最后一个块不为空，将其加入块列表
        if current_block:
            blocks.append('\n'.join(current_block))

        # 返回所有文本块
        return blocks


class E2ERobotParser(RobotParser):

    def __init__(self, text: str,
                 api_info: Dict[Tuple[str, str], str],
                 cli_info: Dict[str, list],
                 keyword_info: List[str]):
        super().__init__(text)
        self.api_info = api_info
        self.cli_info = cli_info
        self.keyword_info = keyword_info
        self.case_id = self.__parse_id()
        self.case_sys_id = self.__parse_sys_id()
        self.steps = []
        self.__step_already_parsed = False

        # 如何用例中出现#TODO字眼，这个用例标记为坏用例，不进行解析
        self.is_bad_case = False
        if '#TODO' in self.text:
            self.is_bad_case = True
        else:
            self.__parse_case_to_steps()

    def get_template_data(self):
        """
        获取模板数据
        :return: 模板数据
        """
        template_data = self.text
        for step in self.steps:
            step_code = step.get("step_code", "")
            if step_code:
                # 去除首尾空格
                step_code = step_code.strip()
                # 按行切割
                step_code_lines = step_code.split('\n')
                for step_code_line in step_code_lines:
                    # 替换掉模板中的代码
                    template_data = template_data.replace(step_code_line + "\n", "").replace(step_code_line, "")
        return template_data

    def __parse_id(self):
        """
        解析用例ID
        :return: 用例ID
        """
        ids = re.findall(r'\[[Tt][Aa][Gg][Ss]\][^\n]*?ID-([^\s]+)', self.text)
        if ids:
            return ids[0]
        else:
            return None

    def __parse_sys_id(self):
        """
        解析用例ID
        :return: 用例ID
        """
        sys_id = re.findall(r'\[[Tt][Aa][Gg][Ss]\][^\n]*?系统ID-([^\s]+)', self.text)
        if sys_id:
            return sys_id[0]
        else:
            return None

    def __parse_case_to_steps(self):
        """
        解析前置，后置，用例中的步骤都会按照手工用例的方式分割出来
        """
        testcase_steps = self.split_testcase()
        setup_and_teardown_steps = self.split_setup_and_teardown()
        self.steps = [*testcase_steps, *setup_and_teardown_steps]
        self.__step_already_parsed = True

    def split_testcase(self):
        """
        拆分测试用例
        :return: 包含所有步骤的列表
        """
        # 初始化一个空的步骤列表
        step_list = []

        # 遍历测试用例列表中的每一个用例
        for i, case in enumerate(self.testcase_list):
            # 将用例按第一行和其余部分分割
            case_sp = case.split('\n', 1)

            # 如果分割后的列表长度小于2，说明用例格式不正确
            if len(case_sp) < 2:
                # 打印错误信息
                logger.debug(f"关键字异常，小于2两行: {case}")
                # 跳过当前用例，继续下一个
                continue

            # 获取用例的名称并去除首尾空格
            case_name = case_sp[0].strip()

            # 解析当前用例并将结果扩展到步骤列表中
            step_list.extend(self._parse_testcase(case, case_name, i))

        # 返回包含所有步骤的列表
        return step_list

    def split_setup_and_teardown(self):
        """
        解析用例前置和后置中的步骤
        :return: 步骤列表
        """
        step_list = []
        # 从前后置中找出拆解出步骤和代码的对应关系
        for keyword in self.keyword_list:
            keyword_sp = keyword.split('\n', 1)
            if len(keyword_sp) < 2:
                # 说明是异常用例用例
                logger.debug(f"关键字异常，小于2两行: {keyword}")
                continue
            keyword_name = keyword_sp[0].strip()
            if keyword_name in ['_setup', '_teardown']:
                step_list.extend(self._parse_setup_and_teardown(keyword, keyword_name))
        return step_list

    def _parse_setup_and_teardown(self, text: str, keyword_name: str) -> List[Dict[str, Union[str, List[str]]]]:
        """
        解析设置和拆卸步骤
        :param text: 包含步骤数据的文本
        :param keyword_name: 关键字名称，"_setup" 或 "_teardown"
        :return: 已解析的步骤列表，每个步骤包含步骤信息、步骤代码及其预期结果等
        """
        parsed_data = []
        current_step = {}
        lines = text.split('\n')
        # 读取步骤开始的标记
        read_step_start = False
        read_step_code = False
        step_type = "setup" if keyword_name == "_setup" else "teardown"
        for index, line in enumerate(lines):
            if index == 0:
                # 第一行是名字，不用处理
                continue
            line = line.strip()
            if line.startswith('#@step'):
                read_step_start = True
                if read_step_code is True and current_step:
                    parsed_data.append(current_step)
                    # 置空
                    read_step_code = False
                step_desc = line.split('@step', 1)[1].strip()
                if not current_step:
                    current_step = {
                        "case_name": keyword_name,
                        "case_id": self.case_id,
                        "case_sys_id": self.case_sys_id,
                        "step_desc": step_desc,
                        "step_type": step_type,
                        "step_code": "",
                        "step_expect": "",
                        "step_keywords": [],
                        "step_apis": [],
                        "step_clis": []
                    }
                else:
                    current_step["step_desc"] += f"\n{step_desc}"
            elif line.startswith('#@expect'):
                if read_step_start is True:
                    current_step["step_expect"] = line.split('@expect', 1)[1].strip()
            elif line.startswith('#@'):
                # 非 #@ 开头的内容都认为是其他标记，先排除
                read_step_start = False
            elif line.startswith('#'):
                # 注释内容先跳过
                pass
            else:
                if read_step_start is True and line.strip():
                    read_step_code = True
                    current_step["step_code"] += line + '\n'

                    # 判断是关键字、CLI还是API
                    # 如果前面有返回值，先去除掉
                    ret_pattern = r'\$\{.*?\}'
                    matches = re.findall(ret_pattern, line)
                    if matches:
                        # 如果匹配成功，去除开头的部分
                        line = line.replace(matches[0], "").strip()

                    # 可能是关键字、API、CLI
                    word = re.split(r'\s{2,}', line)[0]
                    if word.startswith("API请求"):
                        url_pattern = r'连接=([^ ]+)'
                        method_pattern = r'方法=([^ ]+)'
                        match_url = re.search(url_pattern, line)
                        match_method = re.search(method_pattern, line)
                        if match_url:
                            url = match_url.group(1)
                        else:
                            logger.warning(f"无法得知该API来源:{self.case_id},{line}")
                            continue

                        method = None
                        if match_method:
                            method = match_method.group(1)
                        else:
                            logger.warning("没有给出API调用方法")

                        # 从api_info中根据url和method来匹配api
                        url_del_params = StrUtil.remove_url_params(url)
                        url_clean = url_del_params.replace('api/', "")
                        for tup, api_name in self.api_info.items():
                            if StrUtil.is_filled_url(tup[0], url_clean):
                                # 没有给出method或者method匹配上都算匹配成功
                                if not method or (method and method.upper() == tup[1].upper()):
                                    current_step["step_apis"].append(api_name)

                    elif word.startswith("CLI"):
                        cli_pattern = r"命令=(.*?)(?=\s{2,}|\t|$)"
                        match_cli = re.search(cli_pattern, line)

                        if match_cli:
                            clis = match_cli.group(1)
                        else:
                            logger.error(f"找不到具体的CLI命令:{self.case_id},{line}")
                            continue

                        resutl_cli = self.cli_line_2_cli_list(self.cli_info, clis)
                        if resutl_cli:
                            current_step["step_clis"].extend(resutl_cli)

                    else:
                        if word in current_step["step_keywords"] or word.strip() not in self.keyword_info:
                            continue
                        current_step["step_keywords"].append(word)

        if current_step:
            parsed_data.append(current_step)
        # 生成step_id
        for i, step in enumerate(parsed_data):
            step["step_id"] = f"{self.case_id}_{step_type}_{i + 1}"

        return parsed_data

    def _parse_testcase(self, text: str, case_name: str, case_index: int) -> List[Dict[str, Union[str, List[str]]]]:
        """
        解析测试用例文本，将其转化为结构化的数据
        :param text: 测试用例文本
        :param case_name: 测试用例名称
        :param case_index: 测试用例索引
        :return: 包含测试用例步骤的列表，每个步骤是一个字典
        """
        parsed_data = []
        current_step = {}
        lines = text.split('\n')
        read_step_start = False
        read_step_code = False
        for index, line in enumerate(lines):
            if index == 0:
                continue
            line = line.strip()
            if line.startswith('#@step'):
                read_step_start = True
                if read_step_code is True and current_step:
                    parsed_data.append(current_step)
                    # 置空
                    current_step = {}
                    read_step_code = False
                step_desc = line.split('@step', 1)[1].strip()
                if not current_step:
                    current_step = {
                        "case_name": case_name,
                        "case_id": self.case_id,
                        "case_sys_id": self.case_sys_id,
                        "step_desc": step_desc,
                        "step_type": "case",
                        "step_code": "",
                        "step_expect": "",
                        "step_keywords": [],
                        "step_apis": [],
                        "step_clis": []
                    }
            elif line.startswith('#@expect'):
                if read_step_start is True:
                    current_step["step_expect"] = line.split('@expect', 1)[1].strip()
            elif line.startswith('#@'):
                #  #@ 开头的内容都认为是其他标记，先排除
                read_step_start = False
            elif line.startswith('#'):
                # 注释内容先跳过
                pass
            else:
                if read_step_start is True and line.strip():
                    read_step_code = True
                    current_step["step_code"] += line + '\n'

                    # 判断是关键字、CLI还是API
                    # 如果前面有返回值，先去除掉
                    ret_pattern = re.compile(r'^\$\{[^\}]+\}\s*')
                    while ret_pattern.match(line):
                        line = ret_pattern.sub('', line)

                    # 可能是关键字、API、CLI
                    word = re.split(r'\s{2,}', line)[0]
                    if word.startswith("API请求"):
                        url_pattern = r'连接=([^ ]+)'
                        method_pattern = r'方法=([^ ]+)'
                        match_url = re.search(url_pattern, line)
                        match_method = re.search(method_pattern, line)
                        if match_url:
                            url = match_url.group(1)
                        else:
                            logger.warning(f"无法得知该API来源:{self.case_id},{line}")
                            continue

                        method = None
                        if match_method:
                            method = match_method.group(1)
                        else:
                            logger.warning("没有给出API调用方法")

                        # 从api_info中根据url和method来匹配api
                        url_del_params = StrUtil.remove_url_params(url)
                        url_clean = url_del_params.replace('api/', "")
                        for tup, api_name in self.api_info.items():
                            if StrUtil.is_filled_url(tup[0], url_clean):
                                # 没有给出method或者method匹配上都算匹配成功
                                if not method or (method and method.upper() == tup[1].upper()):
                                    current_step["step_apis"].append(api_name)

                    elif word.startswith("CLI"):
                        cli_pattern = r"命令=(.*?)(?=\s{2,}|\t|$)"
                        match_cli = re.search(cli_pattern, line)

                        if match_cli:
                            clis = match_cli.group(1)
                        else:
                            logger.error(f"找不到具体的CLI命令:{self.case_id},{line}")
                            continue

                        resutl_cli = self.cli_line_2_cli_list(self.cli_info, clis)
                        if resutl_cli:
                            current_step["step_clis"].extend(resutl_cli)

                    else:
                        # 关键字
                        if word in current_step["step_keywords"] or word.strip() not in self.keyword_info:
                            continue

                        current_step["step_keywords"].append(word)

        if current_step:
            parsed_data.append(current_step)

        # 生成step_id
        for i, step in enumerate(parsed_data):
            step["step_id"] = f"{self.case_id}_{case_index}_testcase_{i + 1}"

        return parsed_data

    @staticmethod
    def cli_line_2_cli_list(cli_info: Dict[str, list], cli_str: str) -> list:
        """
        匹配cli命令, 详细结果查看单测中mock的数据
        :param cli_info: 格式示例如下
        {
            "interface": ["interface", "ddns;interface", "ipsec-config;interface"],
            "ip": ["interface;ip"],
            "no ip": ["interface;no ip"],
            "ipv6": ["interface;ipv6", "ipv6"],
            "dhcp-server": ["interface;dhcp-server"],
            "wan": ["interface;wan"],
            "no dhcpv6-server": ["interface;no dhcpv6-server"],
            "ips": ["ips"],
            "client": ["ips;client"],
            "semantic-web-engine": ["ips;semantic-web-engine"],
            "ddns": ["ddns"],
            "ipsec-config": ["ipsec-config"],
            "snat-rule": ["snat-rule"],
            "src-zone": ["snat-rule;src-zone"],
            "dst-if": ["snat-rule;dst-if"],
            "src-ipgroup": ["snat-rule;src-ipgroup"],
            "dst-ipgroup": ["snat-rule;dst-ipgroup"],
            "service": ["snat-rule;service"],
            "transfer": ["snat-rule;transfer"],
            "enable": ["snat-rule;enable"],
            "move": ["snat-rule;move"]
        }
        :param cli_str: 格式如下
        config; interface eth12;ip address 191.168.0.1/16
        :return: 匹配到的cli full_command列表
        """
        cli_list = cli_str.split(";")
        keys = cli_info.keys()
        cli_count = defaultdict(int)
        result = []
        for cli in cli_list:
            real_cli_name = StrUtil.find_best_match(keys, cli.strip())
            # 能够找到CLI文档
            if real_cli_name:
                cli_count[real_cli_name] = 0
                # 在cli_info中再次确认是否有父命令
                full_command_list = cli_info[real_cli_name]
                match_command = ""
                # 优先判断full_command_list中有没有real_cli_name和stack中每个元素拼接后相等的，没有则判断有没有和real_cli_name完全相等的
                full_command_set = set(full_command_list)
                for item in cli_count:
                    combined_command = f"{item};{real_cli_name}"
                    if combined_command in full_command_set:
                        match_command = combined_command
                        # 父命令和当前命令都使用过
                        cli_count[item] += 1
                        cli_count[real_cli_name] += 1
                        break

                if match_command:
                    result.append(match_command)

        for item, count in cli_count.items():
            # 没有找到父命令和子命令的默认为独立命令,并加入结果
            if count == 0:
                full_command_set = set(cli_info[item])
                if item in full_command_set:
                    result.append(item)
        return result
