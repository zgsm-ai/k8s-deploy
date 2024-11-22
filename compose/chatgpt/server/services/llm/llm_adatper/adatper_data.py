#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from dataclasses import dataclass
from typing import Union

logger = logging.getLogger(__name__)


@dataclass
class TokenNumber:
    user_req_token: int
    input_token: int
    output_token: int

    def __init__(self, **kwargs):
        self.user_req_token = kwargs.get("user_req_token", 0)
        self.input_token = kwargs.get("input_token", 0)
        self.output_token = kwargs.get("output_token", 0)


@dataclass
class BaseModelData:
    application_name: str
    username: str

    model_name: str
    model_type: str
    model_identification: str
    model_url: str  # 模型地址
    need_sensitization: bool  # 模型地址
    authentication_data: dict  # Model authentication data

    stream: bool  # Is it streaming
    temperature: float
    seed: int
    max_input_tokens: int
    max_tokens: int
    timeout: int
    response_format: str
    carry_context: bool  # Does it carry context

    messages: list  # Used for session model request parameters

    prompt: str  # Used to complete model request parameters

    input: str  # Used for vector model request parameters
    encoding_format: str  # Used for vector model encoding format

    stop: Union[str, list]

    conversation_id: str

    continue_generate: bool  # 是否继续
    overlap_skip: bool  # skip outputting overlap content

    token_number: TokenNumber  # Number of tokens object
    kw: dict

    def __init__(self, **kwargs):
        self.model_name = kwargs.get("model_name", "")
        self.model_type = kwargs.get("model_type", "")
        self.model_identification = kwargs.get("model_identification", "")
        self.need_sensitization = kwargs.get("need_sensitization", False)
        self.username = kwargs.get("username", "")
        self.model_url = kwargs.get("url", "")
        self.authentication_data = kwargs.get("authentication_data", "")
        self.application_name = kwargs.get("application_name")
        self.conversation_id = kwargs.get("conversation_id")
        self.token_number = TokenNumber()
        self.kw = kwargs


class BaseCompletionModelData(BaseModelData):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stream = kwargs.get("stream", False)
        self.temperature = kwargs.get("temperature")
        self.seed = kwargs.get("seed")
        self.max_input_tokens = kwargs.get("max_input_tokens")
        self.max_tokens = kwargs.get("max_tokens")
        self.timeout = kwargs.get("timeout")
        self.response_format = kwargs.get("response_format")
        self.continue_generate = kwargs.get("is_continue", False)
        self.overlap_skip = kwargs.get("overlap_skip", True)
        self.stop = kwargs.get("stop")


class ChatCompletionModelData(BaseCompletionModelData):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = kwargs['messages']
        self.carry_context = kwargs.get("carry_context", False)
        logger.info(f"Initialize ChatCompletion model request parameters, {self.model_name}, {self.conversation_id}, "
                    f"{self.application_name}")


class CompletionModelData(BaseCompletionModelData):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt = kwargs['prompt']
        logger.info(f"Initialize Completions model request parameters, {self.model_name}, {self.application_name}")


class EmbeddingModelData(BaseModelData):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input = kwargs['input']
        self.encoding_format = kwargs.get("encoding_format")
        logger.info(f"Initialize Embedding model request parameters, {self.model_name}, {self.application_name}")
