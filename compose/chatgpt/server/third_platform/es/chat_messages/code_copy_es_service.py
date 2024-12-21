#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/16 20:33
    :修改者: 苏德利 16646
    :更新时间: 2023/3/16 20:33
"""
import hashlib
import logging
from datetime import datetime

import pytz

from common.handlers.prompt_field_handler import prompt_field_handler
from common.utils.util import get_work_id_by_display_name
from third_platform.es.base_es import es, CODE_COPY_INDEX, DOC, BaseESService
from third_platform.services.analysis_service import analysis_service


class CodeCopyESservice(BaseESService):
    """操作记录es"""
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(CodeCopyESservice, self).__init__()
        self.index = CODE_COPY_INDEX
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
            # 同一个用户的 同一段代码 同一个动作
            action = data.get('action', '')
            code_md5 = self.calculate_md5(data['display_name'] + data['code_copy'] + action)

            isset = es.exists(index=self.index, id=code_md5)
            if not isset:
                obj_dict = {
                    "id": code_md5,
                    "display_name": data['display_name'],
                    "languageId": data['language'].lower(),
                    "code_copy": data['code_copy'],
                    "code_copy_text_lines": len(data['code_copy'].splitlines()),
                    "created_at": datetime.now(pytz.timezone('Asia/Shanghai')),
                    "ide": data.get('ide', ''),
                    "ide_version": data.get('ide_version', ''),
                    "ide_real_version": data.get('ide_real_version', ''),
                    "department": department,
                    "action": action,
                    "is_select": data.get('is_select', False)
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
            self.logger.error(f"es 操作 {self.index} 数据失败，失败日志： {str(e)}")


code_copy_es_service = CodeCopyESservice()
