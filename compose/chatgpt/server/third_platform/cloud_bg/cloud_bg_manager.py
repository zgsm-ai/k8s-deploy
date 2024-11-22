#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import re
from common.utils.request_util import RequestUtil
from services.system.ai_record_service import AIRecordActionService
from services.system.configuration_service import ConfigurationService


class CloudBgManager:
    api_url = None
    stream = True
    resp_id = None
    raw_data = None
    middle_process_records = []
    suffix = "-cloud-bg"
    repo_list_conf_attribute_key = "cloud_bg_repo_match_list"
    repo_list_conf_belong_type = "permission"
    api_url_conf_attribute_key = "cloud_bg_api_url"
    api_url_conf_belong_type = "permission"

    @classmethod
    def is_cloud_bg_repo(cls, git_path):
        repo_match_list = ConfigurationService.get_configuration(
            cls.repo_list_conf_belong_type, cls.repo_list_conf_attribute_key)
        if not repo_match_list:
            logging.info("未获取到云BG的仓库的配置")
            return False

        cls.api_url = ConfigurationService.get_configuration(
            cls.api_url_conf_belong_type, cls.api_url_conf_attribute_key)
        if not cls.api_url:
            logging.info("未获取到云BG的接口地址的配置")
            return False

        try:
            repo_match_list = json.loads(repo_match_list)
            for pattern in repo_match_list:
                if re.match(pattern, git_path.strip(), re.IGNORECASE):
                    logging.info("匹配到云BG的仓库的配置，后续CloudBgManager里面的逻辑:" + git_path.strip())
                    return True

            return False
        except Exception as e:
            logging.error("云BG的仓库的配置,json格式化失败：error: " + str(e))
            return False

    @classmethod
    def get_response(cls, data, resp_id, stream):
        cls.raw_data = data.raw_data
        # id添加一个后缀 区分 cloud-bg 的数据
        cls.resp_id = resp_id + cls.suffix
        cls.stream = stream

        request_data = cls.make_request_data(data)
        if cls.stream:
            return cls.make_stream_response(request_data)
        else:
            return cls.make_response(request_data)

    @classmethod
    def make_response(cls, request_data):
        resp = {
            "data": {"id": cls.resp_id, "code": "", "text": ""},
            "success": True,
            "message": ""
        }
        try:
            response = RequestUtil.post(url=cls.api_url, data=request_data)
            response_data = response.get('data', '')

            if response_data:
                code, text = cls.extract_code_just(response_data)
                resp['data']['code'] = code
                resp['data']['text'] = text
                resp['message'] = "请求成功"

                cls.insert_ai_record_action_service(code)
            else:
                resp['success'] = False
                resp['message'] = "请求无响应"

        except Exception as e:
            logging.error("请求cloud_bg 失败: " + str(e))
            resp['success'] = False
            resp['message'] = "请求失败"

        return resp

    @classmethod
    def make_stream_response(cls, request_data):
        try:
            response = RequestUtil.post(url=cls.api_url, data=request_data, stream=True, raw=True)
            if response.status_code == 200:
                return cls.process_stream_response(response)

        except Exception as e:
            print(e.args)

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

    @classmethod
    def make_request_data(cls, data):
        user_prompt = data.raw_data.get('prompt', '')
        code = data.raw_data.get('code', '')
        language = data.raw_data.get('language', '')
        display_name = data.raw_data.get('display_name', '')
        git_path = data.raw_data.get('git_path', '')

        return {
            "message": user_prompt,
            "code": code,
            "stream": cls.stream,
            "language": language,
            "display_name": display_name,
            "git_path": git_path,
        }

    @classmethod
    def process_stream_response(cls, response):
        """yield 写在 make_result() 内会导致非流式接口也返回生成器，故将其单独封装"""
        full_response = ''  # 完整响应
        full_code = ''  # 完整代码
        is_block_code = False  # 是代码时再流式返回
        content_temp = ''  # 暂存代码块标记 ``` （为兼容 ```分开返回场景）
        for response_data in response.iter_content(chunk_size=2048):
            # 将 chunk 转换为字符串，并去掉前缀和后缀
            response_data_str = response_data.decode('utf-8').replace("data:", "").strip()
            # stream 完成
            if response_data_str == "[DONE]":
                break

            content = json.loads(response_data_str).get("data", "")

            full_response += content

            if full_code and is_block_code is False:  # 已返回过代码块
                continue
            elif content in ['`', '``', '```']:  # 暂存，先不返回
                content_temp += content
                continue
            elif full_response.endswith('```markdown\n'):  # 因为流式的```和语言是分开返回，故使用正则匹配最新数据结尾
                content_temp = ''  # 初始
            elif re.search(r'```(.+)\n$', full_response):  # 代码块开始
                is_block_code = True
                content_temp = ''  # 初始
                # 当匹配到该条件的时候 content 会是一个\n ，这里置为空，不然第一行会是一个换行符
                content = ""
            elif is_block_code and re.search(r'```(\n)?$', full_response):  # 代码块结束
                is_block_code = False

            if is_block_code:
                if content_temp:  # 此时不是作为代码块结束符，故返回
                    content = content_temp + content
                    content_temp = ''  # 清空
                full_code += content
                yield content

        cls.insert_ai_record_action_service(full_code)

    @classmethod
    def insert_ai_record_action_service(cls, response_code):
        AIRecordActionService.insert_db_ai_record(data=cls.raw_data,
                                                  middle_process_records=cls.middle_process_records,
                                                  prompt=cls.raw_data.get("prompt", ""),
                                                  response_code=response_code,
                                                  response_id=cls.resp_id)
