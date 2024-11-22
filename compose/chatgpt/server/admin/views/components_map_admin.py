#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/10/23 15:04
"""
import logging

from wtforms import ValidationError

from admin.auth import AdminPermission
from admin.base import BaseView
from models.system.components_map import ComponentsMap
from services.system.components_map_service import ComponentsMapService

logger = logging.getLogger(__name__)


class ComponentsMapAdmin(AdminPermission, BaseView):
    column_list = (
        'team', 'git_repos', 'inline_chat_components', 'fauxpilot_components', 'created_at', 'deleted')
    column_searchable_list = ('team', 'git_repos',)
    column_default_sort = ('created_at', True)
    # 列表页 字段显示verbose_name值
    column_labels = BaseView.get_column_labels(ComponentsMap)

    # 修改前触发
    def on_model_change(self, form, model, is_created):
        model.team = model.team.strip()
        model.git_repos = model.git_repos.strip()

        # 校验参数
        if model.deleted is False and ComponentsMapService.team_is_exist(mid=model.id, team=model.team):
            raise ValidationError('团队已存在')

        super().on_model_change(form, model, is_created)


ComponentsMapAdminView = ComponentsMapAdmin(ComponentsMap, endpoint='_components_map', name='组件映射表')
