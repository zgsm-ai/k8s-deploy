#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/5/15 15:45
"""

from common.constant import ActionsConstant, ScribeConstant
from services.base_service import BaseService
from services.system.components_map_service import ComponentsMapService
from services.system.configuration_service import ConfigurationService


class V2CompletionService(BaseService):

    @classmethod
    def process_params(cls, data: dict) -> dict:
        git_path = data.get('git_path')
        language = data.get('language')
        scribe_components = data.get('scribe_components', [])
        collection_list = []
        if data.get('action') == ActionsConstant.SCRIBE:
            # 若指定了划词组件且非空，直接使用指定组件
            if language in ScribeConstant.CUSTOM_COMPONENT_ALLOW_LANGUAGES \
                    and scribe_components \
                    and isinstance(scribe_components, list):

                # 过滤无效组件
                scribe_component_options = ConfigurationService.get_scribe_component_options()
                scribe_components = list(
                    filter(lambda x: x in [item["value"] for item in scribe_component_options], scribe_components))
                collection_list = scribe_components
            # 否则走原逻辑
            else:
                # 若参数 git_path 能匹配到对应组件库，则替换 collection_list，保底使用默认
                if git_path:
                    collection_list = ComponentsMapService.get_collection_list(**{'git_path': git_path})
            if not collection_list:
                collection_list = ComponentsMapService.get_collection_list(**{'git_path': "default"}) or ["idux"]
            data['collection_list'] = collection_list
        return data


class CompletionService(BaseService):

    @classmethod
    def validate_fields(cls, fields):
        """校验创建数据参数，去除冗余参数"""
        rules = [
            {'label': 'system_prompt', 'type': list, 'optional': True, 'name': '系统预设'},
            {'label': 'prompt', 'type': str, 'name': 'prompt'},
            {'label': 'stream', 'type': bool, 'optional': True, 'name': '是否流式响应'},
            {'label': 'conversation_id', 'type': str, 'optional': True, 'name': '上下文id'},
            {'label': 'context_association', 'type': bool, 'optional': True, 'name': '是否开启上下文'},
            {'label': 'max_tokens', 'type': int, 'optional': True},
            {'label': 'response_format', 'type': str, 'optional': True},
            {'label': 'replace_forbidden_word', 'type': bool, 'optional': True},  # 是否自动替换敏感词
            {'label': 'context', 'type': str, 'optional': True, 'name': '上下文'}
        ]
        return cls._validate(fields, rules)


class UserGiveFeedbacks(BaseService):
    @classmethod
    def validate_fields(cls, fields):
        rules = [
            {'label': 'action', 'type': str, 'optional': False, 'name': 'action'},
            {'label': 'agent_name', 'type': str, 'optional': False, 'name': 'agent_name'},
            {'label': 'message_id', 'type': str, 'optional': True, 'name': '消息id'},
            {'label': 'conversation_id', 'type': str, 'optional': False, 'name': 'ed平台id'},
            {'label': 'rating', 'type': str, 'optional': True, 'name': '用户反馈'}
        ]
        return cls._validate(fields, rules)
