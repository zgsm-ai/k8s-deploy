#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/20 9:26
"""
import datetime
import logging
import re

from flask import g

from common.constant import AdminNoticeContent, OpenAppConstant
from common.exception.exceptions import FieldValidateError
from config import CONFIG
from dao.system.open_api_applications_dao import OpenApiApplicationDao
from lib.session import SessionService
from services.base_service import BaseService
from services.system.users_service import users_service
from third_platform.devops.notice_manager import send_notice_server_async


class OpenApiApplicationService(BaseService):
    dao = OpenApiApplicationDao
    logger = logging.getLogger(__name__)

    @classmethod
    def get_square_list(cls, **fields):
        fields['conditions'] = ((cls.dao.model.state.in_(OpenAppConstant.SQUARE_RETURN_STATES)),)
        query, total = cls.dao.list(**fields)
        for item in query:
            item.app_id = ''
        return query, total

    @classmethod
    def create(cls, **fields):
        user = g.current_user
        fields['applicant'] = user.display_name
        app_id = SessionService.gen_state()  # 生成随机app_id
        fields['app_id'] = app_id
        fields['application_time'] = datetime.datetime.now()
        expiration_time = datetime.datetime.strptime(fields['expiration_time'], '%Y-%m-%d')
        if fields['application_time'] >= expiration_time:
            raise FieldValidateError('[到期时间] 不支持今天及以前日期')
        fields['expiration_time'] = fields['expiration_time'] + ' 23:59:59'
        res = super().create(**fields)
        res.app_id = ''
        if res.id:
            # 发送通知给管理员
            chat_admin_url = CONFIG.app.NOTICE_CONTENT.CHAT_ADMIN_URL
            content = AdminNoticeContent.CONTENT.format(username=user.display_name, chat_admin_url=chat_admin_url)
            send_notice_to_admin_users = [user.username for user in users_service.list(is_admin=True)[0]]
            send_notice_server_async(username=send_notice_to_admin_users, content=content)
        return res

    @classmethod
    def validate_fields(cls, fields):
        """校验创建数据参数"""
        rules = [
            {'label': 'project_name', 'type': str, 'length': 70, 'name': '应用名称'},
            {'label': 'expiration_time', 'type': str, 'name': '到期时间'},
            {'label': 'application_reason', 'type': str, 'length': 255, 'name': '申请原因'},
            {'label': 'expected_profit', 'type': str, 'length': 255, 'name': '预期收益'}
        ]
        return cls._validate(fields, rules)

    @classmethod
    def validate_update_fields(cls, mid, fields):
        """校验更新时的参数"""
        rules = [
            {'label': 'app_link', 'type': str, 'length': 1000, 'allow_empty': True, 'name': '应用案例'},
        ]
        return cls._validate(fields, rules)

    @classmethod
    def is_valid_date(cls, date_str):
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise FieldValidateError('[到期时间] 字段格式错误')

    @classmethod
    def is_valid_app_link(cls, url):
        pattern = r'^(http|https)://((\d{1,3}\.){3}\d{1,3}|[a-zA-Z0-9\-\.]+(\.[a-zA-Z]{2,3}){1,2})(:\d+)?(/[^\s]*)?'
        if not bool(re.match(pattern, url)):
            raise FieldValidateError(f'[{cls.dao.model.app_link.verbose_name}] 字段格式错误')

    @classmethod
    def get_by_app_id(cls, app_id):
        return cls.dao.get_or_none(app_id=app_id)
