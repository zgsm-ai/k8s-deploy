#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 陈烜 42766
    :更新时间: 2023/3/24 14:12
"""
import copy
import datetime
import logging
import re
from collections import OrderedDict

from common.constant import ActionsConstant, ScribeConstant, GPTModelConstant, ConfigurationConstant, GPTConstant
from common.exception.exceptions import FieldValidateError
from common.utils.date_util import DateUtil
from common.utils.qdrant_util import qdrant_util
from common.utils.util import random_completion_id, generate_uuid, remove_duplicate_string
from services.action.base_service import ActionStrategy, ChatbotOptions, stream_error_response, \
    process_code_retract
from services.agents.agent_data_classes import ChatRequestData, make_cls_with_dict

from services.action.scribe_dialogue_base_service import ScribeDialogueBase
from services.system.ai_record_service import AIRecordActionService
from services.system.configuration_service import ConfigurationService
from third_platform.cloud_bg.cloud_bg_manager import CloudBgManager


class ScribeDialogueStrategy(ScribeDialogueBase, ActionStrategy):
    name = ActionsConstant.SCRIBE

    def __init__(self):
        super().__init__()
        self.middle_process_records = []
        self.mock_stream = False  # 此处表示mock流式错误信息，直接返回，不进行数据处理存库

    def clear_tag(self, string):
        """
        删除描述中标签
        使用正则表达式匹配第一行开头不间断的【】包裹的字符
        """
        pattern = r'^【[^】]*】'
        match = re.search(pattern, string)

        if match:
            # 删除匹配到的字符
            string = string.replace(match.group(), '', 1)
            string = self.clear_tag(string)
        return string

    @staticmethod
    def deduplicate_list(repeated_elements):

        return list(OrderedDict.fromkeys(repeated_elements))

    @staticmethod
    def find_tag_list(content):
        """匹配多场景标签提取的结果"""
        pattern = r"\d+、(【.*】)"
        result = re.findall(pattern, content, re.MULTILINE)
        if not result:
            result = re.findall(r"(【.*】)", content, re.MULTILINE)
        return result

    @staticmethod
    def get_gpt_record(start_time, end_time, type_='', model='', prompt='', result=None):
        gpt_record = {
            'type': type_,
            'model': model,
            'start_time': start_time,
            'end_time': end_time,
            'prompt': prompt,
            'result': result,
        }
        return gpt_record

    def vector_recall_desc(self, type_, collection_list, tag_list, score_limit, top_k):
        """向量召回匹配"""
        start_time = DateUtil.datetime_to_str(datetime.datetime.now())
        page_content_list = []
        for tag in tag_list:
            page_content_list += qdrant_util.search_similarity_code_snippet(collection_list, tag, score_limit, top_k)
        page_content_list = self.deduplicate_list(page_content_list)
        end_time = DateUtil.datetime_to_str(datetime.datetime.now())
        record = self.get_gpt_record(type_=type_, start_time=start_time, end_time=end_time,
                                     result=page_content_list)
        self.middle_process_records.append(record)
        return page_content_list

    @staticmethod
    def set_response_id(data):
        """获取随机响应id并赋值"""
        resp_id = random_completion_id(ScribeConstant.ES_ID_TITLE)
        request_data = data.raw_data.copy()
        if request_data.get("extra_kwargs"):
            request_data["extra_kwargs"].update({
                "id": resp_id,
                "is_accept": False,
                "accept_num": 0,
            })
        else:
            request_data["extra_kwargs"] = {
                "id": resp_id,
                "is_accept": False,
                "accept_num": 0,
            }
        data.raw_data = request_data
        return data, resp_id

    @staticmethod
    def process_options_and_data(data, model, code):
        """处理参数 data options"""
        raw_data = data.raw_data.copy()
        raw_data['model'] = raw_data['current_model'] = model
        raw_data['code'] = code
        raw_data['stream'] = False
        new_data = make_cls_with_dict(ChatRequestData, raw_data)
        new_options = ChatbotOptions(raw_data)
        new_options.model = model
        return new_data, new_options

    def request_gpt(self, type_, data, options, prompt, code='', model=GPTModelConstant.GPT_TURBO):
        """gpt请求"""
        start_time = DateUtil.datetime_to_str(datetime.datetime.now())
        # 通过gpt访问AI
        if type_ == ScribeConstant.GENERATE_CODE:
            data.raw_data['prompt'] = prompt
            # 生成代码时添加系统预设
            options.systems = ScribeConstant.SCRIBE_SYSTEMS
            kwargs = {'data': data, 'prompt': prompt, 'options': options, 'code': code, 'random': False}
        else:
            data, options = self.process_options_and_data(data, model, code)
            kwargs = {'data': data, 'prompt': prompt, 'options': options}
        content = self.make_ask(**kwargs)

        end_time = DateUtil.datetime_to_str(datetime.datetime.now())
        record = self.get_gpt_record(type_=type_, model=model, start_time=start_time, end_time=end_time,
                                     prompt=prompt, result=content)
        self.middle_process_records.append(record)
        return content

    def get_prompt(self, data):
        if not data.prompt:
            raise FieldValidateError("划词对话功能必须提供prompt")

        self.check_params_prompt(data.prompt + data.code)  # 先进行一次token校验
        collection_list = data.raw_data.get("collection_list", [])
        if not collection_list:
            raise FieldValidateError("划词对话功能必须提供qdrant collection")
        is_carry_code = data.raw_data.get("is_carry_code", False)
        query = data.prompt
        if is_carry_code:
            query += "\n" + data.code
        score_limit = data.raw_data.get("score_limit", 0.78)
        top_k = data.raw_data.get("top_k", 3)
        # 访问AI，给query加上标签
        tag_prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.SCRIBE_ADD_TAG_PROMPT)
        tag_prompt = tag_prompt.format(query=query)
        options = ChatbotOptions(data.raw_data)
        # # 通过gpt-35访问AI
        tag_query = self.request_gpt(type_=ScribeConstant.ADD_TAG, data=data, options=options, prompt=tag_prompt,
                                     model=GPTModelConstant.GPT_TURBO)
        tag_list = self.deduplicate_list(self.find_tag_list(tag_query))
        # 新版gpt-4 output 格式不一致
        tag_query_string = """"""
        for ind, content in enumerate(tag_list):
            tag_query_string += f"{ind + 1}、{content}\n"

        sample_code = """"""
        try:
            # logging.info(f"获取```{tag_query_string}```相似向量ing")
            page_content_list = self.vector_recall_desc(type_=ScribeConstant.VECTOR_RECALL,
                                                        collection_list=collection_list,
                                                        tag_list=tag_list,
                                                        score_limit=score_limit,
                                                        top_k=top_k)
            logging.info(f"获取示例数量：{len(page_content_list)}")
            selected_example_list = []
            if page_content_list:
                desc_content_list = [content.strip().split('\n')[0].rstrip('：') for content in page_content_list]
                desc_example_string = """"""
                for ind, content in enumerate(desc_content_list):
                    desc_example_string += f"{ind + 1}、{content}\n"

                serial_prompt = ConfigurationService.get_prompt_template(
                    ConfigurationConstant.SCRIBE_FILTER_DESC_PROMPT)
                serial_prompt = serial_prompt.format(requirements=query, tags=tag_query_string,
                                                     selectedText=desc_example_string)
                serial_format = self.request_gpt(type_=ScribeConstant.FILTER_DESC, data=data, options=options,
                                                 prompt=serial_prompt, model=GPTModelConstant.GPT_4)
                query_number = serial_format.split('、')
                logging.info(f"获取示例匹配结果，行号：{query_number}")
                if query_number[0].isdigit():
                    try:
                        serial_list = list(map(int, query_number))
                    except ValueError as err:
                        logging.info(f"行序号解析错误 {err}")
                        pattern = r'^\d+'  # 匹配每一行的第一个数字
                        matches = re.findall(pattern, serial_format, re.MULTILINE)
                        serial_list = list(map(int, matches))
                    for serial in self.deduplicate_list(serial_list):
                        if serial > 0 and serial <= len(page_content_list):
                            selected_example_list.append(page_content_list[serial - 1])
                # 关闭强制选择第一条示例逻辑
                # else:
                #     selected_example_list.append(page_content_list[0])
            sample_code = self.process_sample_code(selected_example_list, top_k, tag_query_string, query, collection_list)
            data.raw_data.update({"sample_code": sample_code})
        except Exception as err:
            logging.info(f"qdrant向量库连接失败： {err}")
        component_list = self.process_component_regex(sample_code, data.code)
        # 存在没有选中代码，且筛选示例为空的情况
        api_docs = """"""
        if component_list:
            api_prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.SCRIBE_FILTER_COMPONENT_API)
            api_prompt = api_prompt.format(requirements=query, components=",".join(component_list))
            component_format = self.request_gpt(type_=ScribeConstant.FILTER_API, data=data, options=options,
                                                prompt=api_prompt,
                                                model=GPTModelConstant.GPT_TURBO)  # gpt35
            api_docs_list = self.filter_api_docs(collection_list, component_format.split(","))
            for ind, docs in enumerate(api_docs_list):
                api_docs += f"{ind + 1}、{docs}\n"
        # 没有匹配到示例的情况使用通用prompt
        if sample_code:
            generate_code_prompt = ConfigurationService.get_prompt_template(
                ConfigurationConstant.SCRIBE_GENERATE_CODE_PROMPT)
            return generate_code_prompt.format(language=data.language,
                                               requirements=data.prompt,
                                               selectedText=data.code,
                                               api_docs=api_docs,
                                               sample_code=sample_code)
        else:
            generate_code_prompt = ConfigurationService.get_prompt_template(
                ConfigurationConstant.SCRIBE_GENERAL_PROMPT)
            return generate_code_prompt.format(language=data.language,
                                               requirements=data.prompt,
                                               api_docs=api_docs,
                                               selectedText=data.code)

    def filter_api_docs(self, collection_list, component_list):
        """
        api文档匹配
        组件或hook转小写去除“-”
        """
        lower_components = list(map(lambda x: x.lower().replace("-", ""), component_list))  # 转小写且去除横杆-
        deduplicate_component = self.deduplicate_list(lower_components)
        api_docs_mapping = qdrant_util.search_api_docs(collection_list, deduplicate_component)
        api_docs_list = [api_docs_mapping.get(component) for component in deduplicate_component
                         if api_docs_mapping.get(component)]
        return api_docs_list

    def process_component_regex(self, sample_code, selected_code):
        """
        通过匹配组件和hook方法的正则表达式
        从示例代码和选中代码中匹配使用到的组件和hook
        去重、去除首尾空格并且删除普通标签， such as "div", "p", and so on.
        """
        component_list = []
        for pattern in ScribeConstant.component_patterns:
            matches = re.findall(pattern, sample_code + selected_code, re.DOTALL)
            for match in matches:
                match_list = match.split(",")
                for item in match_list:
                    if "type " in item:
                        component = item.split("type ")[-1].strip()
                    elif " as " in item:
                        component = item.split(" as ")[0].strip()
                    else:
                        component = item.strip()
                    if component not in ScribeConstant.exclude_component_list:
                        component_list.append(component)
        return self.deduplicate_list(component_list)

    def process_sample_code(self, selected_example_list, top_k, tag_query, query, collection_list):
        """
        拼接sample_code
        且关键字会触发保底机制
        """
        sample_code = """"""
        for ind, content in enumerate(selected_example_list[:top_k]):
            sample_code += f"{ind + 1}、{self.clear_tag(content)}\n"
        keyword_query = []
        basic_safeguard_list = []
        keyword_dict = ScribeConstant.keyword_dict
        temp_keyword_list = []  # 后续兜底机制过滤使用
        for keyword in keyword_dict.keys():
            if keyword in f"{tag_query}{query}":
                if not sample_code or keyword not in sample_code:
                    temp_keyword_list.append(keyword)
                    keyword_query.append(keyword_dict[keyword])
                    logging.info(f"触发关键词匹配示例保底机制：{keyword_query}")
        if keyword_query:
            format_keyword = [f"【{keyword_dict[keyword]}】【基本使用】" for keyword in keyword_query]
            # score_limit=0.81为当前9个文档分析出来的最佳分值
            basic_safeguard_list = self.vector_recall_desc(type_=ScribeConstant.BASIC_SAFEGUARD,
                                                           collection_list=collection_list,
                                                           tag_list=format_keyword,
                                                           score_limit=0.81,
                                                           top_k=2)
        if basic_safeguard_list:
            unique_basic_safeguard = []
            while keyword_query:
                keyword = keyword_query.pop(0)
                for item in basic_safeguard_list:
                    if keyword in item:
                        unique_basic_safeguard.append(item)
                        break
            selected_example_list[:0] = self.deduplicate_list(unique_basic_safeguard)
        sample_code = """"""
        for ind, content in enumerate(selected_example_list):
            sample_code += f"{ind + 1}、{self.clear_tag(content)}\n"
        return sample_code

    @stream_error_response
    def make_result(self, data: ChatRequestData, options: ChatbotOptions = None):
        user_prompt = data.raw_data.get('prompt', '')
        # 生成随机ID
        data, resp_id = self.set_response_id(data)
        self.resp_headers['resp_id'] = resp_id

        # 匹配到 云BG的仓库 就直接走它们的接口返回数据, 不走我们的逻辑
        if CloudBgManager.is_cloud_bg_repo(data.raw_data.get("git_path", "")):
            self.resp_headers['resp_id'] = resp_id + CloudBgManager.suffix
            return CloudBgManager.get_response(data, resp_id, options.stream)
        # second_action==scribe_replace 目前用于sase项目迁移
        if data.raw_data.get('second_action', '') == "scribe_replace":
            replace_prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.SCRIBE_REPLACE_PROMPT)
            prompt_ = replace_prompt.format(language=data.language,
                                            requirements=data.prompt,
                                            selectedText=data.code)
        else:
            prompt_ = self.get_prompt(data)

        data.raw_data['extra_kwargs']['id'] = resp_id
        conversation_id = generate_uuid()
        data.raw_data['conversation_id'] = data.conversation_id = options.conversation_id = conversation_id
        result = self.request_gpt(type_=ScribeConstant.GENERATE_CODE, data=data, options=options,
                                  prompt=prompt_, code=data.code, model=options.model)
        logging.info("匹配gpt响应中code数据")
        if options.stream:  # 流式处理
            if self.mock_stream:
                # 直接返回，不进行处理和入库
                return result
            return self.process_stream_response(result, data, user_prompt, resp_id)
        else:  # 非流式
            code, text = self.extract_code_just(result, text_extract=True)
            if code:
                # 因为gpt4回答会省略代码，重新请求一次gpt3.5 将gpt4返回的代码补全
                # original_code = data.raw_data.get("code", "")
                # 关闭第四步合并代码逻辑
                # if len(original_code) > len(code):
                #     prompt = ConfigurationService.get_prompt_template(ConfigurationConstant.SCRIBE_MERGE_CODE_PROMPT)
                #     prompt = prompt.format(language=data.raw_data.get("language"),
                #                            requirements=user_prompt,
                #                            original_code=original_code,
                #                            developed_code=code
                #                            )
                #     result = self.request_gpt(type_=ScribeConstant.MERGE_CODE, data=data, prompt=prompt,
                #                               options=options, model=GPTModelConstant.GPT_35_16K)
                #     code, _ = self.extract_code_just(result)
                new_code = process_code_retract(data, code)
                if new_code != code:
                    code = new_code
                resp = {
                    "data": {"id": resp_id, "code": code, "text": text},
                    "success": True,
                    "message": "请求成功"
                }
            else:
                resp = {
                    "data": {"id": resp_id, "code": code, "text": text},
                    "success": False,
                    "message": text if text else "您的需求AI无法实现"
                }

            AIRecordActionService.insert_db_ai_record(data=data.raw_data,
                                                      middle_process_records=self.middle_process_records,
                                                      prompt=user_prompt,
                                                      response_code=code,
                                                      response_id=resp_id)
            return resp

    @staticmethod
    def extract_code_just(content, text_extract=False):
        """从AI响应中提取code"""
        pattern = r'```(.*?)\n(.*?)```'

        is_nesting = False  # 嵌套场景
        if '```markdown' in content:
            is_nesting = True

        if content.count('```') == 1:  # ai返回代码块不完整场景
            pattern = r'```(.*?)\n(.*)'
        elif is_nesting:
            pattern_1 = r'```(.*?)\n(.*?)```.*?```markdown'
            if re.search(pattern_1, content, re.DOTALL):  # ```markdown在代码块下方场景
                pattern = pattern_1
            else:  # ai返回嵌套markdown场景
                pattern = r'```markdown.*?\n```(.*?)\n(.*?)```'

        # 匹配```code```代码段
        match = re.search(pattern, content, re.DOTALL)
        if match:
            code = match.groups()[1]
        else:
            code = ""
        # 将代码段替换为省略号, 获取文本信息
        text = "说明文本："
        if text_extract:
            text += re.sub(pattern, "......", content, flags=re.DOTALL)

            # 移除代码块符号
            if '```markdown' in content:
                text = text.replace('```markdown', '')
            if '```' in content:
                text = text.replace('```', '')

        return code, text

    def make_ask(self, data: ChatRequestData, options: ChatbotOptions=None, random=True):
        make_data = copy.copy(data)
        if random:
            make_data, _ = self.set_response_id(make_data)
        result = self.ask(make_data, options)
        if options.stream is True:
            return result

        content = result['choices'][0]['message']['content']
        return content

    def process_stream_response(self, response, data, user_prompt, resp_id):
        """yield 写在 make_result() 内会导致非流式接口也返回生成器，故将其单独封装"""
        full_response = ''  # 完整响应
        full_code = ''  # 完整代码
        is_block_code = False  # 是代码时再流式返回
        content_temp = ''  # 暂存代码块标记 ``` （为兼容 ```分开返回场景）

        res_first_lines = ''  # 临时存储，方便找非空首行（非空格）
        res_first_line = ''  # 暂存非空首行
        offset = 0  # 空格偏移量
        line_temp = ''  # 暂存行内容
        # 输入代码非空首行
        source_first_line = next((v for v in data.code.splitlines() if v.strip()), '') if data.code != '' else ''

        is_recording_continue_first_line = False  # 是否开始记录 续写首行
        continue_first_line = ''  # 续写首行

        if '\t' in source_first_line:
            res_first_line = None  # 输入代码含制表符，不做缩进处理

        for content in response:
            full_response += content
            if full_code and is_block_code is False:  # 已返回过代码块
                continue
            elif content in ['`', '``', '```']:  # 暂存，先不返回
                content_temp += content
                continue
            elif full_response.endswith('```markdown\n'):  # 因为流式的```和语言是分开返回，故使用正则匹配最新数据结尾
                content_temp = ''  # 初始
            # 续写逻辑
            elif content == GPTConstant.CONTINUE_SIGN:
                content_temp = ''  # 初始
                is_recording_continue_first_line = True  # 开始暂存续写首行
                continue
            elif is_recording_continue_first_line:  # 如果需要开始暂存续写首行
                if '\n' not in content:
                    if content_temp:  # 暂存的代码块符号，拼接到首行
                        continue_first_line = content_temp + continue_first_line
                        content_temp = ''
                    continue_first_line += content  # 暂存续写首行
                    continue
                else:  # 首行暂存完毕，根据首行判断是否需要去重/去除冗余字符
                    try:
                        # 上次生成 行列表
                        pre_last_lines = full_response.rsplit(GPTConstant.CONTINUE_SIGN, 1)[0].splitlines()
                        # 首行内容、下一行内容
                        line_before, line_after = content.split('\n', 1)
                        continue_first_line += line_before  # 续写首行

                        # 代码块开始符 / 如果和倒数第二行重复，则移除本行，再从下行重新开始判断
                        if re.search(r'```(.+)\n$', continue_first_line + '\n') \
                                or continue_first_line == pre_last_lines[-2]:
                            continue_first_line = line_after
                            continue
                        pre_last_line = pre_last_lines[-1]
                        overlap = remove_duplicate_string(pre_last_line, continue_first_line)
                        content = continue_first_line[overlap:] + '\n' + line_after
                    except Exception as e:
                        logging.info(f'续写处理异常: {str(e)}')

                    # 处理完毕，恢复相关状态
                    continue_first_line = ''
                    is_recording_continue_first_line = False

            elif re.search(r'```(.+)\n$', full_response):  # 代码块开始
                is_block_code = True
                content_temp = ''  # 初始
                continue  # 此处结尾是换行符，故从下个token开始返回
            elif is_block_code and re.search(r'```\n$', full_response):  # 代码块结束
                is_block_code = False

            if is_block_code:
                # 处理流式缩进问题，有输入代码再进行以下逻辑
                try:
                    if data.code:
                        if res_first_line is not None:
                            res_first_lines += content
                            if content.strip() == '':  # 空行暂存
                                continue

                            # 取非空首行
                            res_first_line = next((v for v in res_first_lines.splitlines() if v.strip()), '')
                            # 原代码首行空格数
                            source_strip_count = len(source_first_line) - len(source_first_line.lstrip())
                            # 生成代码首行空格数
                            res_strip_count = len(res_first_line) - len(res_first_line.lstrip())
                            offset = source_strip_count - res_strip_count  # 缩进空格偏移量
                            content = res_first_lines
                            res_first_lines = ''
                            res_first_line = None
                            # 处理首行
                            if offset > 0:
                                content = ' ' * offset + content
                            elif offset < 0:
                                content = content[-offset:] if content.startswith(' ' * -offset) else content

                        if offset > 0 and '\n' in content:  # \n 有可能和上下字符一起返回
                            content = content.replace('\n', '\n' + ' ' * offset)
                        elif offset < 0:
                            if line_temp == '':  # 遇\n 开始暂存行
                                if '\n' in content:
                                    line_temp += content
                                    continue
                            else:
                                if len(line_temp) < abs(offset) + 1:  # 暂存行，只存储大于偏移量的长度即可。 +1 是因为有\n
                                    line_temp += content
                                    continue
                                else:  # 表示缩进暂存已结束，进行处理
                                    line_temp += content
                                    content = line_temp.replace('\n' + ' ' * -offset, '\n')
                                    line_temp = ''  # 清空行

                except Exception as e:
                    logging.info(f'缩进处理异常, {str(e)}')

                if content_temp:  # 此时不是作为代码块结束符，故返回
                    content = content_temp + content
                    content_temp = ''  # 清空
                full_code += content
                yield content

        # 因为流式，原result被赋值了生成器，故在此更新完整的值
        if self.middle_process_records[-1]['type'] == ScribeConstant.GENERATE_CODE:
            self.middle_process_records[-1]['result'] = full_response
            self.middle_process_records[-1]['end_time'] = DateUtil.datetime_to_str(datetime.datetime.now())
        AIRecordActionService.insert_db_ai_record(data=data.raw_data,
                                                  middle_process_records=self.middle_process_records,
                                                  prompt=user_prompt,
                                                  response_code=full_code,
                                                  response_id=resp_id)
