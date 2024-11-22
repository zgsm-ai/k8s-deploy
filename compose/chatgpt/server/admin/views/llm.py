#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from admin.auth import AdminPermission
from admin.base import BaseView
from models.system.llm import LLM


class LLMAdmin(AdminPermission, BaseView):
    column_labels = BaseView.get_column_labels(LLM)

    # # 修改前触发
    def on_model_change(self, form, model, is_created):
        """
        将字典转换为格式化的 JSON 字符串
        """
        try:
            if form.authentication_data.data:
                # 将 JSON 字符串转换为字典
                model.authentication_data = json.loads(form.authentication_data.data)
        except Exception as e:
            raise Exception(f'必须是合法的json格式: {e}')
        super().on_model_change(form, model, is_created)

    def edit_form(self, obj=None):
        """
        自定义编辑表单
        """
        form = super().edit_form(obj)
        if form.authentication_data and isinstance(form.authentication_data.data, dict):
            # 将字典转换为格式化的 JSON 字符串
            form.authentication_data.data = json.dumps(obj.authentication_data, indent=4, ensure_ascii=False)
        return form


LLMAdminView = LLMAdmin(LLM, endpoint='_llm_admin', name='模型配置表')
