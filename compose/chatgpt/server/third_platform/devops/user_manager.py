#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 苏德利 16646
    :时间: 2023/3/14 20:34
    :修改者: 苏德利 16646
    :更新时间: 2023/3/14 20:34
"""

from . import DevopsConfig
from common.utils.request_util import RequestUtil
import requests


class UserManager(DevopsConfig):
    """
    此类主要打通devOps平台的user相关的接口
    """
    base_url = DevopsConfig.base_url + '/api/users'

    @classmethod
    def get_by_username(cls, username):
        url = f'{cls.base_url}/by_username/{username}'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data

    @classmethod
    def get_by_token(cls, token):
        url = f'{cls.base_url}/get_by_token'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers, params={'token': token}))
        return data

    @classmethod
    def get_by_id(cls, _id):
        url = f'{cls.base_url}/{_id}'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data

    @classmethod
    def get_by_ids(cls, params):
        # 此处去掉了一个 token参数，因为是无效参数
        data = cls.format_resp(RequestUtil.get(
            cls.base_url, headers=cls.headers)
        )
        return data

    @classmethod
    def get_user_roles(cls, username, source_key, source_id,
                       with_version_roles=True, with_product_roles=True, with_business_roles=True, paginate=False):
        """
        获取用户角色
        """
        params = {
            'source_key': source_key,
            'source_id': source_id,
            'username': username,
            'with_version_roles': with_version_roles,
            'with_product_roles': with_product_roles,
            'with_business_roles': with_business_roles,
            'paginate': paginate
        }
        url = f'{cls.base_url}/roles'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers, params=params))
        return data

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
        params = {
            'source_key': source_key,
            'source_id': source_id,
            'username': username,
            'with_version_roles': with_version_roles,
            'with_product_roles': with_product_roles,
            'with_business_roles': with_business_roles,
        }
        url = f'{cls.base_url}/roles/all'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers, params=params))
        return data

    @classmethod
    def get_user_versions_by_username(cls, username, **kwargs):
        """
        获取用户参与的版本, 支持kwargs过滤， 分页，和名称搜索排序等支持
        """
        url = f'{cls.base_url}/versions'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers,
                                               params={'username': username, **kwargs}))
        return data

    @classmethod
    def get_admin_jwt_token(cls):
        """
        拿到管理员的jwt_token
        """
        url = f'{cls.base_url}/get_by_token'
        resp = requests.get(url, headers=cls.headers, params={'token': cls.headers.get('token')})
        jwt_token = resp.headers.get('jwt_token')
        return jwt_token

    @classmethod
    def get_user_groups_by_username(cls, username):
        """获取用户的用户组，一般用来作权限检查"""
        url = f'{cls.base_url}/{username}/groups'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data
