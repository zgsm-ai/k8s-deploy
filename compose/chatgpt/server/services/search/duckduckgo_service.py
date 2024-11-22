#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 陈烜 42766
    :更新时间: 2023/3/24 14:12
"""
import requests
from urllib.parse import urljoin
from config import conf


class DuckDuckGoService:
    def __init__(self, conf) -> None:
        self.api_base = conf.get("duckduck_api_base")

    def search(self, query: str, limit: int = 5, timeout: int = 10):
        resp = requests.post(
            url=urljoin(self.api_base, "/search"),
            json={"query": query, "limit": limit},
            timeout=timeout,
        )
        resp.encoding = "utf-8" if resp.encoding is None else resp.encoding
        return resp.json()


duckduckgo_search_service = DuckDuckGoService(conf)
