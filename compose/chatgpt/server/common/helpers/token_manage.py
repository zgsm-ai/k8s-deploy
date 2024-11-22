#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/14 20:24
    :修改者: 苏德利 16646
    :更新时间: 2023/3/14 20:24
"""

import jwt
from config import get_config
import logging
from third_platform.services.user_service import UserService
from services.system.users_service import users_service


class TokenManage:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.secret = get_config().get("jwt_secret")

    def get_token_from_request(self, request):
        if request.headers.get('ep_jwt_token') is not None:
            token = request.headers.get('ep_jwt_token')
        elif request.cookies.get('ep_jwt_token') is not None:
            token = request.cookies.get('ep_jwt_token')
        else:
            token = request.args.get("ep_jwt_token")
        return token

    def decode(self, token):
        """
        解码
        :param token:
        :return:
        """
        try:
            return jwt.decode(token, self.secret, algorithms=['HS256']) if token else None
        except Exception as err:
            self.logger.error(f"解析token：{token}出现异常:{str(err)}")
            return None

    def decode_from_request(self, request):
        user = self.decode(self.get_token_from_request(request))
        if user:
            return user
        token = request.headers.get('token')
        if token:
            try:
                user = UserService.get_by_token(token)
                return user
            except Exception as err:
                self.logger.error(f"解析token：{token}出现异常:{str(err)}")
        api_key = request.headers.get('api-key')
        if api_key:
            try:
                user = users_service.get_user_by_api_key(api_key)
                return user
            except Exception as err:
                self.logger.error(f"解析api_key：{api_key}出现异常:{str(err)}")
        return None


token_manage = TokenManage()
