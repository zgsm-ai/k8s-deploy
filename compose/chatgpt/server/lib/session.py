#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2023/3/16 9:37
"""

import logging
import requests
from urllib import parse
import secrets

from common.helpers.application_context import ApplicationContext
from services.system.users_service import UsersService
from config import conf


class SessionService:
    logger = logging.getLogger(__name__)
    # pylint: disable=no-member
    config = {}

    @classmethod
    def gen_state(cls, length=32):
        """
        生成随机的state，防止csrf
        """
        return secrets.token_urlsafe(nbytes=length)[0:length]

    @classmethod
    def logout(cls):
        user = ApplicationContext.get_current()
        if user:
            ApplicationContext.clear_session()


class IDTrustService(SessionService):
    logger = logging.getLogger(__name__)
    # pylint: disable=no-member
    config = conf

    @classmethod
    def get_redirect_url(cls, redirect_uri, state, real_host):
        client_id = cls.config.get('client_id')
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,  # noqa E501
            'state': state,
            'response_type': 'code'
        }
        auth_url = cls.config.get('auth_url') + '/oauth2/authorize'
        redirect_url = "%s?%s" % (auth_url, parse.urlencode(params))
        return redirect_url

    @classmethod
    def idt_callback_login(cls, code, state, session_state, redirect_uri, real_host):
        if session_state == state:
            client_id = cls.config.get('client_id')
            client_secret = cls.config.get('secret')
            access_token = cls.get_access_token(code, redirect_uri, client_id, client_secret)
            user_info = cls.get_user_info(access_token)
            user_info = cls.deal_user_info(user_info, real_host)
            user = cls.auth_user(user_info)
            return user
        else:
            return None

    @classmethod
    def get_access_token(cls, code, redirect_uri, client_id, client_secret):
        params = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        token_url = "%s?%s" % (cls.config.get('auth_url') + '/oauth2/token', parse.urlencode(params))
        response = requests.get(token_url, verify=False)
        token = response.json()
        return token['access_token']

    @classmethod
    def get_user_info(cls, access_token):
        params = {
            'access_token': access_token
        }
        user_url = "%s?%s" % (cls.config.get('auth_url') + '/oauth2/get_user_info', parse.urlencode(params))
        response = requests.get(user_url, verify=False)
        return response.json()

    @classmethod
    def deal_user_info(cls, user_info, real_host):
        return user_info

    @classmethod
    def auth_user(cls, user_info):
        user_info_email = user_info.get('email', '')
        # user_by_email = UsersService.get_by_email(email)
        # if not user_by_email:
        # user_info_email = user_info['email']
        if user_info_email.startswith('w'):
            user_info_email = user_info_email.replace('w', '', 1)
        user_by_email = UsersService.get_or_create_by_username_and_display_name(
            username=user_info['name'],
            display_name=user_info['displayname'] + user_info['workid'],
            email=user_info_email
        )
        assert user_by_email is not None
        return user_by_email

    @classmethod
    def get_real_host(cls, req):
        """
        根据请求来获取host
        :param headers:
        :return:
        """
        real_host = req.headers.get('X-Forwarded-Host', req.host)
        return real_host
