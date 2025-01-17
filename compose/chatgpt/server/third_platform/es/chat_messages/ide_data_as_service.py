#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
import pytz
from elasticsearch_dsl.search import Search
from common.handlers.prompt_field_handler import prompt_field_handler
from common.utils.util import get_work_id_by_display_name, code_get_line_and_language, get_second_dept
from third_platform.es.base_es import es, IDE_DATA_INDEX, DOC, BaseESService
from third_platform.services.analysis_service import analysis_service
from common.constant import UserBehaviorAction, ActionsConstant


class PlugInESService(BaseESService):
    """操作记录es"""
    logger = logging.getLogger(__name__)

    def __init__(self):
        super(PlugInESService, self).__init__()
        self.index = IDE_DATA_INDEX
        self.s = Search(using=es, index=self.index)
        self.field_handler = prompt_field_handler
        self._doc = DOC

    def insert_data(self, data):
        """
        插入请求数据,根据conversation_id是否存在,走不同的逻辑
        :param data: 接口请求参数信息
        """
        try:
            es_id = data.get("conversation_id", "")
            # 计算大模型生成代码的总行数
            data["code_total_lines"], code_languages = code_get_line_and_language(data.get("response_content", ""))
            # 区分于快捷指令和智能问答
            if data.get("request_mode", "http") == "websocket":
                data["language"] = code_languages
            if es.exists(index=self.index, id=es_id):
                # 会话id存在,走数据合并
                self.merge_data(es_id, update_data=data)
            else:
                # 不存在,走插入的逻辑
                obj_dict = {
                    "username": data.get("username", ''),
                    "id": es_id,
                    "model": data.get("agent_name", "").split("|")[-1] or "",
                    "action": data.get("action", ""),
                    "code": data.get("code", ""),
                    "query": data.get("prompt", ""),
                    "agent_name": data.get("agent_name", ""),
                    "code_total_lines": data["code_total_lines"],
                    "accept_num": data.get('accept_num', 0),
                    "language": data.get("language", ""),
                    "feedbacks": data.get("feedbacks", ""),
                    "path": data.get("path", ""),
                    "User-Agent": data.get("user_agent", ""),
                    "host": data.get("host", ""),
                    "response_content": data.get("response_content", ""),
                    "total_tokens": data.get("total_tokens", 0),
                    "created_at": self.process_time_format(data.get("created_at", "")),
                    "finish_at": self.process_time_format(data.get("finish_at", "")),
                    "ide": data.get("ide", ""),
                    "ide_version": data.get('ide_version', ''),
                    "ide_real_version": data.get('ide_real_version', ''),
                    "callType": data.get("callType", ""),
                    "request_nums": 1,  # 新增一条会话时，默认请求次数为1
                    "user_copy": 0,
                    "user_diff": 0,
                    "user_accept": 0,
                    "user_ctrlc": 0
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
                self.insert(obj_dict)
        except Exception as err:
            self.logger.error(f"es插入ide_data数据失败，失败日志： {str(err)}")

    def process_time_format(self, timestamp):
        if timestamp:
            utc_time = datetime.utcfromtimestamp(timestamp)
            # 定义Asia/Shanghai时区
            shanghai_tz = pytz.timezone('Asia/Shanghai')
            # 将UTC时间转换为Asia/Shanghai时间
            return utc_time.replace(tzinfo=pytz.utc).astimezone(shanghai_tz)
        else:
            return datetime.now(pytz.timezone('Asia/Shanghai'))

    def update_es_feedbacks(self, es_id, key: str, value: str) -> dict:
        """
        更新es平台用户点赞数据
        es_id:对应es平台的id,
        key:es平台对应的key
        value:es平台对应的value
        """
        result = {}
        if es.exists(index=self.index, id=es_id):
            res = self.update_by_id(id=es_id, update_data={f"{key}": value})
            if res.get("_shards", {}).get("successful") == 1:
                result = {"es_status": "The es platform is updated successfully!"}
            else:
                result = {"es_status": "Failed,update data is consistent with es data, no need to update!"}
        else:
            result = {"es_status": f"Update failed, the conversation_id:{es_id} does not exist!"}
        return result

    def get_es_data(self, es_id):
        if es.exists(index=self.index, id=es_id):
            return self.get(es_id)
        else:
            return False

    def merge_data(self, es_id: str, update_data: dict):
        """
        插入数据时，当前会话id已经存在，走更新追加的逻辑
        es_id:id,唯一id
        update_data: 需要更新的数据
        """
        try:
            # 先获取已经存在的数据
            es_data = self.get_es_data(es_id)
            # 待更新数据
            es_update_data = {
                # 用户每请求一次，次数+1
                "request_nums": es_data.get("request_nums", 1) + 1,
                "code": es_data.get("code", "") + "---" + update_data.get("code", ""),
                "query": es_data.get("query", "") + "\n" + update_data.get("prompt", ""),
                "code_total_lines": es_data["code_total_lines"] + update_data["code_total_lines"],
                "response_content": es_data.get("response_content", "") + "\n" + update_data.get("response_content",
                                                                                                 ""),
                "total_tokens": es_data.get("total_tokens", 0) + update_data.get("total_tokens", 0),
                "finish_at": self.process_time_format(update_data.get("finish_at", ""))
            }
            res = self.update_by_id(id=es_id, update_data=es_update_data)
            if res.get("_shards", {}).get("successful") == 1:
                self.logger.info(f"es_id:{es_id}更新成功!")
            else:
                self.logger.error("更新数据失败!")
        except Exception as err:
            self.logger.error(f"es更新ide_data数据失败，失败日志： {str(err)}")

    def user_evaluate(self, name: str, es_id: str, **fields):
        """
        用户点赞处理，同时更新es平台和dify平台
        message_id:dify平台消息id
        action:每个agent对应的事件
        es_id:es平台对应的id
        """
        status = 200
        # 更新es平台的字段
        es_result = self.update_es_feedbacks(es_id, 'feedbacks', fields.get('rating', ''))
        es_updata = self.get_es_data(es_id)
        # 将用户点赞作为本次会话有效
        if es_updata and fields.get("rating", "") == "like" and es_updata.get("accept_num", 0) == 0:
            self.update_es_feedbacks(es_id, 'accept_num', 1)
        return es_result, status

    def user_behavior(self, es_id: str, accept_num: int, behavior: str) -> dict:
        """
        处理用户采纳结果,用户每一次的交互行为都要记录下来
        注意:一次会话可能有多次请求，多次请求可能包含多次交互
        es_id:es平台id
        accept_num:用户采纳行数
        """
        try:
            es_data = self.get_es_data(es_id)
            if es_data and behavior in UserBehaviorAction.user_behavior:
                user_behavior = UserBehaviorAction.behavior_keys.get(f"{behavior}")
                update_data = {
                    "accept_num": es_data["accept_num"] + accept_num,
                    f"{user_behavior}": es_data.get(user_behavior, 1) + 1
                }
                res = self.update_by_id(es_id, update_data)
                if res.get("_shards", {}).get("successful") == 1:
                    return {"es_status": "Successful"}
                else:
                    self.logger.error(f"es更新ide_data数据失败，失败日志： {str(res)}")
                    return {"es_status": "Failed"}
        except Exception as err:
            self.logger.error(f"es更新ide_data数据失败，失败日志： {str(err)}")


ide_es_service = PlugInESService()
