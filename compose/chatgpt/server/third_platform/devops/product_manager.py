# -*- coding: utf-8 -*-
"""
    对接devops的产品相关

    :作者: 崔剑飞w68841
    :时间: 2021-08-02
    :修改者: 崔剑飞w68841
    :更新时间: 2021-08-02
"""
from lib.cache.cache_anno import cache_able
from . import DevopsConfig
from common.utils.request_util import RequestUtil


class ProductManager(DevopsConfig):
    """
    此类主要打通devOps平台的产品相关接口
    """

    base_url = DevopsConfig.base_url + '/api/products'
    PRODUCT_ROLE_BY_ID_CANCHE_KEY = 'devops:product:id:role'
    PRODUCT_USER_BY_ID_CACHE_KEY = 'devops_user:username:product_id'
    PRODUCT_USER_GROUP_BY_ID_CACHE_KEY = 'devops_user_group:product_id'

    @classmethod
    def get_by_id(cls, product_id):
        url = f'{cls.base_url}/{product_id}'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data

    @classmethod
    def create_repos(cls, product_id, **params):
        """
        在产品中新建代码仓库源
        product_id：产品id
        """
        url = f'{cls.base_url}/{product_id}/repos'
        data = cls.format_resp(RequestUtil.post(url, data=params, headers=cls.headers))
        return data

    @classmethod
    def get_repos_by_version_repo(cls, product_id, path_with_namespace):
        """
        根据代码仓库的名称在产品中查询该代码仓库的信息
        product_id：产品id
        path_with_namespace：代码仓库名称
        """
        url = f'{cls.base_url}/{product_id}/repos?path_with_namespace={path_with_namespace}'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data

    @classmethod
    def get_by_name(cls, product_name):
        url = f'{cls.base_url}/?name={product_name}'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data

    @classmethod
    def list_repos(cls, product_id, **params):
        url = f'{cls.base_url}/{product_id}/repos'
        data = cls.format_resp(RequestUtil.get(url, params=params, headers=cls.headers))
        return data

    @classmethod
    @cache_able(PRODUCT_ROLE_BY_ID_CANCHE_KEY, index=[1, 2], expire=60 * 60)
    def get_product_manager_by_id(cls, product_id, role_id):
        url = f'{cls.base_url}/{product_id}/rels?page=1&per=200&paginate=true&role_ids={role_id}&name=&type=user'
        data = cls.format_resp(RequestUtil.get(url, headers=cls.headers))
        return data

    @classmethod
    def list_rels(cls, product_id, **params):
        url = f'{cls.base_url}/{product_id}/rels'
        data = cls.format_resp(RequestUtil.get(url, params=params, headers=cls.headers))
        return data
