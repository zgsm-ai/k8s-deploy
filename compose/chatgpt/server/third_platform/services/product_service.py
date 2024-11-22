#!/usr/bin/env python3
# -*- coding: utf8 -*-

from config import CONFIG
from lib.cache.cache_anno import cache_able
from third_platform.devops.product_manager import ProductManager


class ProductService:
    manager = ProductManager

    PRODUCT_BY_ID_CANCHE_KEY = 'devops:product:id'
    PRODUCT_ROLE_BY_ID_CANCHE_KEY = 'devops:product:id:role'
    PRODUCT_PM_BY_ID_CACHE_KEY = 'devops_pm:product:id'
    PRODUCT_USER_BY_ID_CACHE_KEY = 'devops_user:username:product_id'
    PRODUCT_USER_GROUP_BY_ID_CACHE_KEY = 'devops_user_group:product_id'
    EXPIRE_TIME = CONFIG.app.get('LOCK_EX', {}).get('DEVOPS_DADA_CACHE', 300)

    @classmethod
    @cache_able(PRODUCT_BY_ID_CANCHE_KEY, index=[1], expire=60 * 60 * 24)
    def get_by_id(cls, _id):
        return cls.manager.get_by_id(_id)

    @classmethod
    def create_repos(cls, product_id, repos_list):
        """
        在产品中创建代码仓库
        product_id：项目id
        main_branch：分支名称（此处定义为master）
        repos_list：创建信息(列表)
            gitlab_app_id：gitlab_app_id
            name：仓库地址名称（深圳总部Gitlab）
            path_with_namespace：仓库名称
        """
        params = {
            "main_branch": 'master',
            "repos": repos_list
        }
        return cls.manager.create_repos(product_id, **params)

    @classmethod
    def get_repos_by_version_repo(cls, product_id, path_with_namespace):
        """
        根据path_with_namespace获取产品仓库源的ids和master_branch_name
        path_with_namespace：仓库名称
        """
        data, _ = cls.manager.get_repos_by_version_repo(product_id, path_with_namespace)
        if data is None:
            result = {}
        elif not data:
            result = {}
        else:
            result = data[0]
        return result

    @classmethod
    def list_repos(cls, version_id, page=None, per=None, paginate='false', path_with_namespace=None,
                   search_full_path='false'):
        data, total = cls.manager.list_repos(
            version_id, page=page, per=per, paginate=paginate, path_with_namespace=path_with_namespace,
            search_full_path=search_full_path)
        return data, total

    @classmethod
    @cache_able(PRODUCT_PM_BY_ID_CACHE_KEY, index=[1], expire=EXPIRE_TIME)
    def list_pm(cls, product_id, page=1, per=100, paginate='true', role_ids=None, **search):
        """获取产品线pm"""
        if role_ids:
            search.update(dict(role_ids=role_ids))
        data, _ = cls.manager.list_rels(product_id, page=page, per=per, paginate=paginate, **search)
        return list(filter(lambda d: not d.get("group"), data))

    @classmethod
    @cache_able(PRODUCT_USER_BY_ID_CACHE_KEY, index=[1, 2], expire=EXPIRE_TIME)
    def get_user_info_from_product(cls, username, product_id):
        """获取用户在产线的信息"""
        search = dict(name=username, type='user')
        data, _ = cls.manager.list_rels(product_id, page=1, per=100, paginate='true', **search)
        return data

    @classmethod
    @cache_able(PRODUCT_USER_GROUP_BY_ID_CACHE_KEY, index=[1, ], expire=EXPIRE_TIME)
    def get_user_group_from_product(cls, product_id):
        """获取用户在产线的信息"""
        search = dict(type='group')
        data, _ = cls.manager.list_rels(product_id, page=1, per=100, paginate='true', **search)
        if isinstance(data, list) and len(data):
            data = [each for each in data if each.get("type") == 'group']
        else:
            data = []
        return data
