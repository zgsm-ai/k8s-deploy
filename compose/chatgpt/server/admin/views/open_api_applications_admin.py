#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/20 15:21
"""
from flask_admin.contrib.peewee.filters import BasePeeweeFilter
from wtforms import ValidationError

from admin.auth import AdminPermission
from admin.base import BaseView, CustomTextAreaField
from common.constant import ApplicantNoticeContent, OpenAppConstant
from config import CONFIG
from models.system.open_api_applications import OpenApiApplication
from third_platform.devops.notice_manager import send_notice_server_async


class CustomFilter(BasePeeweeFilter):

    def apply(self, query, value):
        return query.where(self.column == value)

    def operation(self):
        return 'equals'


class OpenApiApplicationAdmin(AdminPermission, BaseView):
    model = OpenApiApplication
    column_list = ('project_name', 'state', 'applicant', 'application_time', 'expiration_time', 'application_reason',
                   'expected_profit', 'deleted')
    can_create = False
    can_export = False
    # 额外过滤条件
    column_extra_filters = [
        CustomFilter(
            column=OpenApiApplication.state,
            name=OpenApiApplication.state.verbose_name,
            options=OpenAppConstant.STATE_CHOICES
        )
    ]
    # 排序
    column_default_sort = ('application_time', True)
    # 列表页 字段显示verbose_name值
    column_labels = BaseView.get_column_labels(OpenApiApplication)
    # 列表页 字段值显示choices值
    column_formatters = {
        'state': lambda v, c, m, p: dict(m.STATE_CHOICES).get(m.state)
    }
    # 编辑页 是否只读
    form_widget_args = {
        'applicant': {'readonly': True},
        'created_at': {'readonly': True},
        'update_at': {'readonly': True},
    }
    # 编辑页 修改编辑框类型
    form_overrides = {
        'application_reason': CustomTextAreaField,
        'expected_profit': CustomTextAreaField,
        'approve_remark': CustomTextAreaField,
    }
    old_data = None

    # 进入编辑页触发
    def on_form_prefill(self, form, _id):
        self.old_data = form.data  # 修改前数据
        # 调用父类的 on_form_prefill 方法
        return super().on_form_prefill(form, _id)

    # 修改前触发
    def on_model_change(self, form, model, is_created):
        if model.state in OpenAppConstant.APPROVE_REMARK_NOT_EMPTY_STATES and not model.approve_remark:
            raise ValidationError('请填写审批备注 说明原因')
        super().on_model_change(form, model, is_created)

    # 修改后触发
    def after_model_change(self, form, model, is_created=False):
        state = model.state
        # 发送通知
        if model.deleted is False:
            if self.old_data['state'] != state and state in OpenAppConstant.ALLOW_NOTICE_STATES:
                approve_remark = model.approve_remark
                first_line = ''
                if state == OpenAppConstant.APPROVED:
                    first_line = '您申请的千流AI的API账号已审批通过'
                    approve_remark = ''
                elif state == OpenAppConstant.FAIL:
                    first_line = '您申请的千流AI的API账号审批未通过'
                    approve_remark = '\n原因：' + approve_remark
                elif state == OpenAppConstant.DISABLE:
                    first_line = '您的千流AI的API账号被平台方禁用'
                    approve_remark = '\n原因：' + approve_remark
                chat_url = CONFIG.app.NOTICE_CONTENT.CHAT_URL
                content = ApplicantNoticeContent.CONTENT.format(first_line=first_line,
                                                                approve_remark=approve_remark,
                                                                project_name=model.project_name,
                                                                expiration_time=model.expiration_time,
                                                                application_reason=model.application_reason,
                                                                expected_profit=model.expected_profit,
                                                                chat_url=chat_url)
                send_notice_server_async(username=model.applicant, content=content)


OpenApiApplicationAdminView = OpenApiApplicationAdmin(OpenApiApplication, endpoint='_open_api_applications',
                                                      name='开放API应用')
