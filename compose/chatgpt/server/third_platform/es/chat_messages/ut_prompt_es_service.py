#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import logging
from datetime import datetime

import pytz

from common.handlers.prompt_field_handler import prompt_field_handler
from common.utils.util import get_work_id_by_display_name
from third_platform.es.base_es import UT_PROMPT_INDEX, DOC, BaseESService
from third_platform.services.analysis_service import analysis_service


class UTPromptESservice(BaseESService):
    """用例统计到es"""
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(UTPromptESservice, self).__init__()
        self.index = UT_PROMPT_INDEX
        self.field_handler = prompt_field_handler
        self._doc = DOC

    def calculate_md5(self, data):
        md5_hash = hashlib.md5()
        md5_hash.update(data.encode('utf-8'))
        return md5_hash.hexdigest()

    def insert_code_completion(self, data):

        try:
            work_id = get_work_id_by_display_name(data.get("display_name", ''))
            department = analysis_service.get_user_multilevel_dept(work_id)
            # 同一个用户的 同一段代码 username
            code_md5 = self.calculate_md5(data['display_name'] + str(data['timestamp']) + str(data['type']))

            obj_dict = {
                "uuid": code_md5,
                "display_name": data['display_name'],
                "username": data.get("username"),
                "create_at": datetime.now(pytz.timezone('Asia/Shanghai')),
                "department": department,

                "response": data["response"],
                "timestamp": data.get("timestamp"),
                "type": data.get("type"),
                "inputs": data.get("inputs"),
                "record_time": data.get("record_time")
            }
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

            # 新增 server_extra_kwargs 服务端拓展字段
            if 'server_extra_kwargs' in data.keys():
                for key, value in data['server_extra_kwargs'].items():
                    try:
                        # 可能存在iso格式字符串，尝试将字符串解析为 datetime 对象
                        value = datetime.fromisoformat(value)
                    except Exception:
                        # 只要解析失败，就直接按源格式存储
                        pass
                    obj_dict[key] = value

            self.insert(obj_dict)

        except Exception as e:
            self.logger.error(f"es 操作 {self.index} 数据失败，失败日志： {str(e)}", exc_info=True)


ut_prompt_es_service = UTPromptESservice()
