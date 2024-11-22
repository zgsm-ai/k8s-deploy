#!/usr/bin/env python
# -*- coding: utf-8 -*-
from openai.lib.azure import AzureOpenAI
from common.constant import LLMProvider
from services.llm.llm_adatper.adatper_data import BaseModelData
from services.llm.llm_adatper.base_adatper import BaseAdapter


class AzureOpenAiAdapter(BaseAdapter):
    provider = LLMProvider.AZURE_OPENAI

    def __init__(self, model_data: BaseModelData):
        super().__init__(model_data)
        self.client = AzureOpenAI(
            azure_endpoint=self.model_data.model_url,
            api_key=self.model_data.authentication_data.get("api_key"),
            api_version=self.model_data.authentication_data.get("api_version")
        )
