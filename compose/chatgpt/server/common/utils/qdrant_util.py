#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    :作者: 黄伟伦 z24224
    :时间: 2023/9/7 14:18
    :修改者: 黄伟伦 z24224
    :更新时间: 2023/9/19 14:18
"""

import logging

from flask import request

from common.exception.exceptions import RequestError
from common.utils.request_util import RequestUtil
from config import get_config

QDRANT_HOST = get_config().get("qdrant_server")


class QdrantUtil:
    logger = logging.getLogger(__name__)

    @classmethod
    def search_similarity_code_snippet(cls, collection_list, query, score_limit, top_k):
        headers = {
            'Content-Type': 'application/json',
            "Accept": "application/json",
            'api-key': request.headers.get('api-key')
        }
        url = f'{QDRANT_HOST}/api/qdrant/get_similarity_code_snippet'
        params = {
            "collection_name_list": collection_list,
            "query": query,
            "score_limit": score_limit,
            "top_k": top_k
        }
        data = cls.format_resp(RequestUtil.post(url, data=params, headers=headers))
        return data

    @classmethod
    def search_api_docs(cls, collection_list, component_list):
        url = f'{QDRANT_HOST}/api/qdrant/api_docs'
        headers = {
            'Content-Type': 'application/json',
            "Accept": "application/json",
            'api-key': request.headers.get('api-key')
        }
        params = {
            "component_list": component_list,
            "collection_list": collection_list
        }
        data = cls.format_resp(RequestUtil.post(url, data=params, headers=headers))
        return data

    @classmethod
    def format_resp(cls, resp):
        if not resp.get('success'):
            logging.error(f"数据获取失败, {resp.get('message')}")
            raise RequestError("请求code-indexer失败")
        return resp.get('data')


qdrant_util = QdrantUtil()
