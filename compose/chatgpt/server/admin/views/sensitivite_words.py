#!/usr/bin/env python
# -*- coding: utf-8 -*-


from admin.auth import AdminPermission
from admin.base import BaseView
from models.system.sensitive_words import SensitiveWords


class SensitiveWordsdmin(AdminPermission, BaseView):
    column_labels = BaseView.get_column_labels(SensitiveWords)


SensitiveWordsView = SensitiveWordsdmin(SensitiveWords, endpoint='_sensitive_words', name='敏感词配置表')
