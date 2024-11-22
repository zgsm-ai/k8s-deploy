#!/usr/bin/env python
# -*- coding: utf-8 -*-

from admin.auth import AdminPermission
from admin.base import BaseView
from common.utils.date_util import DateUtil
from models.system.application import Application


class ApplicationAdmin(AdminPermission, BaseView):
    column_labels = BaseView.get_column_labels(Application)

    # 排除 'application_key' 字段
    form_excluded_columns = ['application_key', "created_at", "update_at"]

    def create_model(self, form):
        model = super().create_model(form)
        model.application_key = DateUtil.generate_unique_md5()
        model.save()
        return model


ApplicationAdminView = ApplicationAdmin(Application, endpoint='_application_admin', name='应用配置表')
