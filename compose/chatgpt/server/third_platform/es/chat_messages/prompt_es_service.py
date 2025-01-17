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
import hashlib
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

    @staticmethod
    def _calc_rid(data):
        """
        计算rid
        :param data:
        :return:
        """
        conv_id = data.get("conversation_id", "")
        chat_id = data.get("chat_id", "")
        action = data.get("action", "chat")
        rid = conv_id + "-" + chat_id + "-" + action
        # 创建一个SHA-256哈希对象
        sha256_hash = hashlib.sha256()
        # 更新哈希对象以包含输入字符串的字节
        sha256_hash.update(rid.encode('utf-8'))
        # 获取十六进制格式的散列值
        hash_result = sha256_hash.hexdigest()
        return hash_result
    
    def insert_prompt(self, data, response_content='', usage=None):
        """
        插入prompt请求数据，插入异常不影响主流程执行
        :param data: 接口请求参数信息
        :param response_content: 接口请求content返回
        :param usage: 接口消耗的tokens
        """
        try:
            logging.info(f"insert_prompt(): data: {data}, usage: {usage}, response: {response_content}")
            rid = data.get("id")
            if rid is None:
                rid = PromptESService._calc_rid(data)
            if rid and es.exists(index=self.index, id=rid):
                self.update_by_id(id=rid,
                                  update_data={'is_accept': data.get('isAccept', False),
                                               'accept_num': data.get('acceptNum', 0)})
            else:               
                obj_dict = {
                    **data, 
                    "id": rid,
                    "usage": usage, 
                    "response": response_content
                }
                obj_dict["finish_at"] = datetime.now(pytz.timezone('Asia/Shanghai'))
                self.insert(obj_dict)
        except Exception as err:
            self.logger.error(f"es插入prompt数据失败，失败日志： {str(err)}")


prompt_es_service = PromptESService()
