#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/5/6 16:04
"""
import logging

from wtforms import ValidationError

from admin.auth import AdminPermission
from admin.base import BaseView
from admin.views.open_api_applications_admin import CustomFilter
from common.constant import ApiRuleConstant
from models.system.api_rule import ApiRule
from services.system.api_rule_service import ApiRuleService
from third_platform.services.analysis_service import analysis_service

logger = logging.getLogger(__name__)


class ApiRuleAdmin(AdminPermission, BaseView):
    column_list = ('rule_type', 'rule_info', 'deleted')
    column_searchable_list = ('rule_info',)
    can_export = False
    can_delete = True
    column_default_sort = ('created_at', True)
    # 额外过滤条件
    column_extra_filters = [
        # 类型过滤下拉框
        CustomFilter(
            column=ApiRule.rule_type,
            name=ApiRule.rule_type.verbose_name,
            options=ApiRule.RULE_TYPE_CHOICES
        )
    ]
    # 列表页 字段显示verbose_name值
    column_labels = BaseView.get_column_labels(ApiRule)
    # 列表页 字段值显示choices值
    column_formatters = {
        'rule_type': lambda v, c, m, p: dict(m.RULE_TYPE_CHOICES).get(m.rule_type)
    }

    # 修改前触发
    def on_model_change(self, form, model, is_created):
        model.rule_info = model.rule_info.strip()
        if model.rule_info == '':
            raise ValidationError(f'请填写 {ApiRule.rule_info.verbose_name} 字段')
        elif model.rule_type == ApiRuleConstant.DEPT and model.rule_info not in analysis_service.get_dept_list():
            logger.info(f'部门填写错误或部门不存在: {model.rule_info}')
            raise ValidationError('部门填写错误或部门不存在')

        # 校验规则是否已配置，软删除则不校验
        elif model.deleted is False and ApiRuleService.rule_is_exist(model.id, model.rule_type, model.rule_info):
            raise ValidationError('规则已存在')

        super().on_model_change(form, model, is_created)


ApiRuleAdminView = ApiRuleAdmin(ApiRule, endpoint='_api_rule', name='api规则')
