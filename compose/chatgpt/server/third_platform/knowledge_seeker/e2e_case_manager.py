#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/25 14:18
"""
from common.utils.request_util import RequestUtil
from third_platform.knowledge_seeker import KsConfig


class E2ECaseKsManager(KsConfig):
    # 检索步骤关联信息
    GET_STEP_ASSOCIATION_DATA = "/api/knowledge_seeker/e2e_case/case_experience"

    @classmethod
    def make_headers(cls):
        return {
            "Content-Type": "application/json",
            "token": cls.token,
        }

    @classmethod
    def get_step_associated_info(
            cls,
            action: list,
            step_desc: str,
            case_module: str,
            product_id: str,
            product_name: str,
            step_intent: list,
            top_k: int = 3,
    ) -> dict:
        """
        检索步骤关联信息
        @param action: 检索历史经验的动作 [step, keyword, api, cli]
        @param step_desc: 手工用例步骤
        @param case_module: 用例模块
        @param product_id: 产品id
        @param product_name: 产品名称
        @param step_intent: 步骤的操作意向
        @param top_k: 最相似的个数
        @return: 返回字典，包含 step,keyword,api,cli 四种key
        """
        url = f'{cls.base_url}{cls.GET_STEP_ASSOCIATION_DATA}'
        headers = cls.make_headers()
        data = {
            "step_desc": step_desc,
            "action": action,
            "case_module": case_module,
            "product_id": str(product_id),
            "product_name": product_name,
            "top_k": top_k,
            "step_intent": step_intent,
            "display_name": cls.user
        }
        response = RequestUtil.post(url=url, json=data, headers=headers)
        return response['data'] or dict()
