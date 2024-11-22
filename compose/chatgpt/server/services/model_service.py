#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common.constant import ConfigurationConstant
from services.system.configuration_service import ConfigurationService
from third_platform.pedestal_server.pedestal_manager import PedestalServerManager


class ModelService:

    @classmethod
    def list(cls, **kwargs):
        data = PedestalServerManager.get_model(**kwargs)
        all_models = data.get('data').get('llm')

        enable_models = cls.get_enable_models()
        if isinstance(enable_models, list) and len(enable_models):
            all_models = [model for model in all_models if model.get('model_identification') in enable_models]

        data = dict(
            llm=all_models,
            total=len(all_models),
        )
        return data

    @classmethod
    def get_enable_models(cls):

        enable_models = ConfigurationService.get_configuration(belong_type=ConfigurationConstant.MODEL_BELONG_TYPE,
                                                               attribute_key=ConfigurationConstant.ENABLED_MODELS)
        if enable_models:
            enable_models = enable_models.split(',')
        else:
            enable_models = []

        return enable_models
