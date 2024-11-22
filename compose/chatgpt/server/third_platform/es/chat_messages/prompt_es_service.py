#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/16 20:33
    :修改者: 苏德利 16646
    :更新时间: 2023/3/16 20:33
"""

import logging
from datetime import datetime

import pytz
from elasticsearch_dsl.search import Search

from common.handlers.prompt_field_handler import prompt_field_handler
from common.utils.util import get_work_id_by_display_name, code_get_line_and_language
from third_platform.es.base_es import es, PROMPT_INDEX, DOC, BaseESService
from third_platform.services.analysis_service import analysis_service


class PromptESService(BaseESService):
    """操作记录es"""
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(PromptESService, self).__init__()
        self.index = PROMPT_INDEX
        self.s = Search(using=es, index=self.index)
        self.field_handler = prompt_field_handler
        self._doc = DOC

    def insert_prompt(self, data, response_content='', usage=None):
        """
        插入prompt请求数据，插入异常不影响主流程执行
        :param data: 接口请求参数信息
        :param response_content: 接口请求content返回
        :param usage: 接口消耗的tokens
        """
        try:
            work_id = get_work_id_by_display_name(data.get("display_name", ''))
            department = analysis_service.get_user_multilevel_dept(work_id)

            code_total_lines, code_languages = code_get_line_and_language(response_content)
            language = data.get("language", "")
            if language:
                language = language.lower()
            # 处理系统预设，若有多个将其拼接为字符串
            system_prompt = data.get("systems", "")
            if isinstance(system_prompt, list):
                system_prompt = '\n----------\n'.join(system_prompt)

            usage = usage or {}

            obj_dict = {
                "username": data.get("display_name", ''),
                "app_id": data.get("app_id", ''),
                "current_model": data.get("current_model", ""),
                "system_prompt": system_prompt,
                "prompt": data.get("prompt", ""),
                "action": data.get("action", "chat"),
                "language": language,
                "code": data.get("code", ""),
                "create_at": datetime.now(pytz.timezone('Asia/Shanghai')),
                "path": data.get("path", ""),
                "User-Agent": data.get("user_agent", ""),
                "host": data.get("host", ""),
                "department": department,
                "response_content": response_content,
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "code_total_lines": code_total_lines,
                "code_languages": code_languages,
                "collection_list": ','.join(data.get("collection_list", [])),
                "conversation_id": data.get("conversation_id", ""),
            }
            # 考虑只有插件有ide参数需要存es的情况
            if data.get('ide') is not None:
                obj_dict["ide"] = data.get('ide', '')
            if data.get('ide_version') is not None:
                obj_dict["ide_version"] = data.get('ide_version', '')
            if data.get('ide_real_version') is not None:
                obj_dict["ide_real_version"] = data.get('ide_real_version', '')
            if data.get('sample_code') is not None:
                obj_dict["sample_code"] = data.get('sample_code', '')

            # 新增一个extra_kwargs字段, 格式为dict, 里面的所有参数都保存, 未来新加的字段都可以放这里面。
            if 'extra_kwargs' in data.keys():
                for key, value in data['extra_kwargs'].items():
                    try:
                        # 可能存在iso格式字符串，尝试将字符串解析为 datetime 对象
                        value = datetime.fromisoformat(value)
                    except Exception:
                        # 只要解析失败，就直接按源格式存储
                        pass
                    obj_dict[key] = value

            if data.get("id") and es.exists(index=self.index, id=data['id']):
                self.update_by_id(id=data['id'],
                                  update_data={'is_accept': data.get('isAccept', False),
                                               'accept_num': data.get('acceptNum', 0)})
            else:
                self.insert(obj_dict)

        except Exception as err:
            self.logger.error(f"es插入prompt数据失败，失败日志： {str(err)}")


prompt_es_service = PromptESService()
