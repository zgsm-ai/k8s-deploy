#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from dao.system.statistics_token_dao import StatisticsTokenDao
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class StatisticsTokenService(BaseService):
    dao = StatisticsTokenDao

    @classmethod
    def statistics_token(cls,
                         application_name: str,
                         username: str,
                         model_identification: str,
                         user_req_token: int,
                         input_token: int,
                         output_token: int):
        """
        记录请求模型的token数
        :param model_identification: 模型标识
        :param username: 用户名
        :param application_name: 应用名称
        :param user_req_token: 用户请求token数：包含（system、user）
        :param input_token: 请求模型token数：包含（system、user、上下文）
        :param output_token: 模型响应文本
        """
        return cls.dao.record_tokens(application_name=application_name,
                                     username=username,
                                     model_identification=model_identification,
                                     user_req_token=user_req_token,
                                     input_token=input_token,
                                     output_token=output_token)
