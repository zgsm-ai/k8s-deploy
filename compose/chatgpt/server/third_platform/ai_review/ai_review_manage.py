#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/6/14 14:03
"""
import logging

import requests
from flask import request
from retry import retry

from config import conf

logger = logging.getLogger(__name__)


class AIReviewManage:
    base_url = conf.get('review_url')

    @retry(tries=2)  # 失败后重试1次
    def request_review(self, prompt):
        """请求本地模型接口"""
        url = f'{self.base_url}/review/v1/engines/codegen/completions'
        data = {
            'prompt': prompt,
            "max_tokens": 1000,
            "beta_mode": False,
            "best_of": 1,
            "temperature": 0.1,
            "stop": [
                "\n\n"
            ]
        }
        try:
            api_key = request.headers.get('api-key')
            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            res = requests.post(url=url, json=data, headers=headers)
            if res.status_code == 200:
                data = res.json()
                return data
            else:
                logger.error(f'review request error: status code: {res.status_code} {res.text}')
                return False
        except Exception as e:
            logger.error(f'review request error: {e}')
            return False


ai_review_manage = AIReviewManage()
