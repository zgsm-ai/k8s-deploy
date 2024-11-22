#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/3/30 14:22
"""
from admin.views.ai_review_admin import AIReviewMainRecordAdminView, AIReviewTaskRecordAdminView
from admin.views.api_rule_admin import ApiRuleAdminView
from admin.views.components_map_admin import ComponentsMapAdminView
from admin.views.configuration_admin import ConfigurationAdminView
from admin.views.llm import LLMAdminView
from admin.views.application import ApplicationAdminView
from admin.views.sensitivite_words import SensitiveWordsView
from admin.views.open_api_applications_admin import OpenApiApplicationAdminView
from admin.views.users_admin import UsersView

Views = [
    UsersView,
    OpenApiApplicationAdminView,
    ConfigurationAdminView,
    ApiRuleAdminView,
    AIReviewMainRecordAdminView,
    AIReviewTaskRecordAdminView,
    ComponentsMapAdminView,
    LLMAdminView,
    ApplicationAdminView,
    SensitiveWordsView,
]
