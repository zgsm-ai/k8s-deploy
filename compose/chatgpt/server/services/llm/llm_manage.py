#!/usr/bin/env python
# -*- coding: utf-8 -*-
from common.constant import LLMProvider
from services.llm.llm_adatper.adatper_data import ChatCompletionModelData, CompletionModelData, EmbeddingModelData
from services.llm.llm_adatper.openai_adatper import OpenAiAdapter
from services.llm.llm_adatper.azure_openai_adatper import AzureOpenAiAdapter


class ModelManager:

    def __init__(self, request_data: dict):
        self.request_data = request_data
        self.provider = request_data.get("provider", "")
        self.adatper = self.get_adatper()

    def get_adatper(self):
        if self.provider == LLMProvider.OPENAI:
            return OpenAiAdapter
        if self.provider == LLMProvider.AZURE_OPENAI:
            return AzureOpenAiAdapter
        else:
            raise Exception("This supplier is not currently supported")

    def get_chat_completion(self):
        model_data = ChatCompletionModelData(**self.request_data)
        return self.adatper(model_data).get_chat_completion()

    def get_completion(self):
        model_data = CompletionModelData(**self.request_data)
        return self.adatper(model_data).get_completion()

    def get_embedding(self):
        model_data = EmbeddingModelData(**self.request_data)
        return self.adatper(model_data).get_embedding()
