#!/usr/bin/env python
# -*- coding: utf-8 -*-

import openai

from common.constant import LLMProvider
from services.llm.llm_adatper.adatper_data import BaseModelData
from services.llm.llm_adatper.base_adatper import BaseAdapter


class OpenAiAdapter(BaseAdapter):
    provider = LLMProvider.OPENAI

    def __init__(self, model_data: BaseModelData):
        super().__init__(model_data)
        kw = dict(base_url=self.model_data.model_url)
        if isinstance(self.model_data.authentication_data, dict) \
                and "api_key" in self.model_data.authentication_data.keys():
            kw["api_key"] = self.model_data.authentication_data.get("api_key")
        self.client = openai.OpenAI(**kw)
