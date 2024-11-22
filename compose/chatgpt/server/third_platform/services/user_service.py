#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/14 20:32
    :修改者: 苏德利 16646
    :更新时间: 2023/3/14 20:32
"""

from third_platform.devops.user_manager import UserManager

from lib.cache.cache_anno import cache_able


class UserService:
    CACHE_KEY_ID = "user:id"
    CACHE_KEY_USERNAME = "user:username"
    CACHE_KEY_TOKEN = "user:token"
    CACHE_KEY_USER_GROUPS = "user:groups"
    manager = UserManager

    @classmethod
    @cache_able(CACHE_KEY_USERNAME, index=[1])
    def get_by_username(cls, username):
        return cls.manager.get_by_username(username)

    @classmethod
    @cache_able(CACHE_KEY_TOKEN, index=[1])
    def get_by_token(cls, token):
        return cls.manager.get_by_token(token)

    @classmethod
    @cache_able(CACHE_KEY_ID, index=[1])
    def get_by_user_id(cls, user_id):
        return cls.manager.get_by_id(user_id)

    @classmethod
    def get_user_roles(cls, username, source_key, source_id,
                       with_version_roles=True, with_product_roles=True, with_business_roles=True):
        return cls.manager.get_user_roles(
            username, source_key, source_id, with_version_roles, with_product_roles, with_business_roles)

    @classmethod
    def get_user_product_and_version(cls, username, source_key, source_id,
                                     with_version_roles=True, with_product_roles=True, with_business_roles=True):
        """
        获取用户所属的所有产品和项目
        :param username: 工号
        :param source_key: 产品或项目
        :param source_id: 产品id或项目id
        :param with_version_roles: 是否包含项目
        :param with_product_roles: 是否包含产品
        :param with_business_roles: 是否包含组织架构
        :return:
        """
        return cls.manager.get_user_product_and_version(
            username, source_key, source_id, with_version_roles, with_product_roles, with_business_roles)

    @classmethod
    def get_user_versions_by_username(cls, username, **kwargs):
        return cls.manager.get_user_versions_by_username(username, **kwargs)

    @classmethod
    def get_admin_jwt_token(cls):
        return cls.manager.get_admin_jwt_token()

    @classmethod
    @cache_able(CACHE_KEY_USER_GROUPS, index=[1], expire=60 * 60)
    def get_user_groups_by_username(cls, username):
        return cls.manager.get_user_groups_by_username(username)
