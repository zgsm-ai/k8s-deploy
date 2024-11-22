#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dao.base_dao import BaseDao
from models.system.llm import LLM


class LLMDao(BaseDao):
    model = LLM

    @classmethod
    def get_by_model_identification(cls, model_identification: str):
        query, _ = cls.list(deleted=False, active=True)
        for each in query:
            # 统一改为小写对比,兼容历史请求数据
            if each.model_identification.lower() == model_identification.lower():
                return each
        return None

    @classmethod
    def get_by_combind_models(cls, model_combination: str):
        models = list()
        model_combinations = model_combination.split(',')
        for model_identification in model_combinations:
            model = cls.get_or_none(model_identification=model_identification, active=True)
            if model:
                models.append(model)
        return models
