#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import random

from common.constant import LLMCombinationType, LLMRank
from common.exception.exceptions import RequestError, CustomException
from dao.system.llm_dao import LLMDao
from services.base_service import BaseService
from services.llm.llm_manage import ModelManager


class LLMService(BaseService):
    dao = LLMDao

    @classmethod
    def get_request_data(cls, **kwargs):
        """
        Retrieve request data
        1. Merge interface request data and backend model configuration data
        """
        if "model" not in kwargs:
            raise Exception('model is required')

        model_identification = kwargs.pop('model', "")
        model = cls.distribution_model(model_identification)
        if not model:
            raise Exception('Model not found')
        model_conf_data = model.dict()
        cls.check_request_data(model_conf_data, kwargs)
        model_conf_data.update(kwargs)
        return model_conf_data

    @classmethod
    def check_request_data(cls, model_conf_data: dict, req_data: dict):
        """
        Check request data
        """
        if req_data.get("max_tokens", 0) > model_conf_data.get("max_tokens", 0):
            raise Exception(f'max_tokens is greater than: {model_conf_data.get("max_tokens", 0)}')

    @classmethod
    def chat_completion(cls, **kwargs):
        """
        Session model request entry
        """
        try:
            return ModelManager(cls.get_request_data(**kwargs)).get_chat_completion()
        except CustomException as e:
            logging.error(f"Chat completion error, kw:{kwargs}, error:{e}", exc_info=True)
            raise e
        except Exception as e:
            logging.error(f"Chat completion error, kw:{kwargs}, error:{e}", exc_info=True)
            raise RequestError(f"Chat completion error: {e}")

    @classmethod
    def completions(cls, **kwargs):
        """
        Complete the model request entry
        """
        try:
            return ModelManager(cls.get_request_data(**kwargs)).get_completion()
        except Exception as e:
            logging.error(f"completion error, kw:{kwargs}, error:{e}", exc_info=True)
            raise RequestError(f"completion error: {e}")

    @classmethod
    def embedding(cls, **kwargs):
        """
        embedding the model request entry
        """
        try:
            return ModelManager(cls.get_request_data(**kwargs)).get_embedding()
        except Exception as e:
            logging.error(f"embedding error, kw:{kwargs}, error:{e}", exc_info=True)
            raise RequestError(f"embedding error: {e}")

    @classmethod
    def distribution_model(cls, model_identification):
        """
        Allocation Model
        1. Single model direct query result return
        2. The combination model needs to be randomly assigned based on weights
        """
        llm = cls.dao.get_by_model_identification(model_identification)

        if llm and llm.combination_type == LLMCombinationType.COMBINATION:
            llms = cls.dao.get_by_combind_models(llm.model_combination)
            if len(llms) == 0:
                return None
            model_identifications = [echo.model_identification for echo in llms]
            weights = [echo.weight for echo in llms]

            model_identification = random.choices(model_identifications, weights)[0]
            llm = cls.dao.get_by_model_identification(model_identification)

        return llm

    @classmethod
    def list(cls, **kwargs):
        llm = list()
        kwargs.update(belong_to=LLMRank.USER)
        query, total = cls.dao.list(**kwargs)

        for each in query:
            data = dict(
                model_identification=each.model_identification,
                model_type=each.model_type,
                name=each.model_name,
            )
            llm.append(data)
        data = dict(
            llm=llm,
            total=total,
        )

        return data
