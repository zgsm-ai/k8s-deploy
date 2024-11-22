#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/23 14:41
"""
import re

from dao.system.components_map_dao import ComponentsMapDao
from services.base_service import BaseService


class ComponentsMapService(BaseService):
    dao = ComponentsMapDao

    @classmethod
    def compatible_git_repo_pattern(cls, pattern):
        """
        处理兼容 http:// 和 git@ 两种仓库地址
        示例:
            http://code.xxx.org/test/ATT/devops/xxx/xxx.git
            git@code.xxx.org:test/ATT/devops/xxx/xxx.git
        """
        http_pattern = r'http://'
        git_pattern = r'git@'
        pattern_list_processed = []
        pattern_list = pattern.split('|')
        for git_repo in pattern_list:
            pattern_list_processed.append(git_repo)

            # http 转 git，注意替换顺序
            if git_repo.startswith(http_pattern):
                git_repo_git = git_repo.replace(http_pattern, git_pattern).replace('/', ':', 1)
                pattern_list_processed.append(git_repo_git)
            # git 转 http，注意替换顺序
            elif git_repo.startswith(git_pattern):
                git_repo_http = git_repo.replace(':', '/', 1).replace(git_pattern, http_pattern)
                pattern_list_processed.append(git_repo_http)

        return '|'.join(pattern_list_processed)

    @classmethod
    def verify_git_path(cls, git_path, data):
        """验证匹配 git_path """
        pattern = data.get('git_repos', '')
        pattern = cls.compatible_git_repo_pattern(pattern)
        res = re.search(pattern=pattern, string=git_path, flags=re.I)
        return True if res else False

    @classmethod
    def filter_by_git_path(cls, lt, git_path):
        """正则过滤筛选数据"""
        return list(filter(lambda item: cls.verify_git_path(git_path, item), lt))

    @classmethod
    def list(cls, *args, **kwargs):
        git_path = kwargs.pop('git_path', '')
        query, total = super().list(*args, **kwargs)
        query = [item.dict() for item in query]
        if git_path:
            query = cls.filter_by_git_path(query, git_path)
        return query, len(query)

    @classmethod
    def get_collection_list(cls, **kwargs):
        query, total = cls.list(**kwargs)
        return query[0]['inline_chat_components'] if total > 0 else []

    @classmethod
    def validate_fields(cls, fields):
        """校验创建数据参数"""
        rules = [
            {'label': 'team', 'type': str, 'length': 50},
            {'label': 'git_repos', 'type': 're_str', 'length': 500},
            {'label': 'inline_chat_components', 'type': str, 'optional': True, 'length': 255},
            {'label': 'fauxpilot_components', 'type': str, 'optional': True, 'length': 255}
        ]
        return cls._validate(fields, rules)

    @classmethod
    def team_is_exist(cls, mid, team):
        fields = {
            'conditions': ((cls.dao.model.id != mid),),
            'team': team,
            'deleted': False
        }
        if cls.count(**fields) > 0:
            return True
        return False
