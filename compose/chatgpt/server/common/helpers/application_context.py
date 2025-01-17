#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2023/3/16 9:38
"""

import logging
from flask import request
from common.constant import ServeConstant

from lib.jwt_session.session import session

logger = logging.getLogger(__name__)


class ApplicationContext:
    """
    上下文,用在RESTAPI中,用于管理与服务交互的用户信息
    """
    @classmethod
    def get_session(cls):
        return session

    # @classmethod
    # def get_current(cls, raise_not_found_exception=True):
    #     from services.system.users_service import UsersService
    #     user = UsersService.create_test_user()
    #     return user
    @classmethod
    def get_current(cls, raise_not_found_exception=True):
        user = cls._get_for_api_key()
        if user:
            return user
        from services.system.users_service import UsersService
        username = cls.get_current_username()
        if not username:
            username = cls.get_username_by_authorization()
        current_user = UsersService().get_by_username(username)
        if not current_user and raise_not_found_exception:
            # 放头部会出现循环导入 导致异常
            from common.exception.exceptions import NoLoginError
            raise NoLoginError()
        else:
            return current_user

    @classmethod
    def _get_for_api_key(cls):
        from services.system.users_service import UsersService
        api_key = request.args.get("api-key") if not request.headers.get(
            "api-key") else request.headers.get("api-key")
        if not api_key:
            # for socket
            if hasattr(request, "event"):
                auth = request.event.get("args", [{}])[-1]
                api_key = auth.get("api-key")
        if api_key:
            try:
                user = UsersService.get_user_by_api_key(api_key)
                return user
            except Exception as err:
                logger.error(f"解析api_key：{api_key}出现异常:{str(err)}")
        return None

    @classmethod
    def get_cookie(cls):
        return request.headers.get("cookie")

    @classmethod
    def get_access_ip(cls):
        if request.headers.get('X-Forwarded-For') is not None:
            ips = str(request.headers.get('X-Forwarded-For'))
            _ip = ips.split(",")[0]
        elif request.headers.get('X-Real-IP') is not None:
            _ip = str(request.headers.get('X-Real-IP'))
        else:
            _ip = str(request.remote_addr)
        return _ip

    @classmethod
    def get_current_username(cls):
        username = session.get("username")
        if username:
            return username
        return None

    @classmethod
    def get_username_by_authorization(cls):
        """
        *.sangfor.com域名平台可以直接通过Cookie获取认证信息
        但是部分eolinker平台不支持，这里通过authorization进行验证
        """
        username = None
        if request.headers.get('Authorization') and request.headers.get('Origin'):
            # 避免循环导入
            from third_platform.eolinker.api_studio_manager import ApiStudioManager
            user_info = ApiStudioManager.get_user_info(request.headers.get('Authorization'),
                                                       request.headers.get('Origin'))
            if user_info:
                work_id = user_info.get('userMail').split('@')[0]
                from third_platform.services.analysis_service import AnalysisService
                work_info = AnalysisService.get_by_work_id(work_id)
                from services.system.users_service import users_service
                if work_info:
                    user = users_service.get_or_create_by_username_and_display_name(
                        work_id, work_info.get('nameid'))
                    if user:
                        username = user.username
                else:
                    # 如果没有则创建一个eolinker用户
                    username_eolinker = f"{user_info.get('userNickName')}{ServeConstant.EOLINKER_SUFFIX}"
                    display_name_eolinker = f"{user_info.get('userNickName')}_{work_id}{ServeConstant.EOLINKER_SUFFIX}"
                    user = users_service.get_by_username(username_eolinker)
                    if not user:
                        user = users_service.create_eolinker_user(username_eolinker,
                                                                  display_name_eolinker)
                    if user:
                        username = user.username
        return username

    @classmethod
    def get_current_app_id(cls):
        return request.headers.get('app-id')

    @classmethod
    def clear_session(cls):
        session.clear()

    @classmethod
    def update_session_attr(cls, maps):
        if maps:
            for key in maps.keys():
                session[key] = maps[key]

    @classmethod
    def reset_session(cls, data):
        cls.clear_session()
        cls.update_session_attr(data)

    @classmethod
    def update_session_user(cls, user):
        session['username'] = user.username

    @classmethod
    def update_username(cls, username):
        session['username'] = username
