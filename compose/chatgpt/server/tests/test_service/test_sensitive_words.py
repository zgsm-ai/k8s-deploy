#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from services.llm.llm_adatper.sensitive_words import SensitiveWords


def get_content(completion: dict):
    return completion["choices"][0]["message"].get("content", None)


def update_content(completion: dict, content: str):
    completion["choices"][0]["message"]["content"] = content
    return completion


class Completion:
    data = {
        "id": "chatcmpl-9rcdllJdD1T30y1yleXLJqwIUuJmG",
        "choices": [
            {"message": {"content": "",
                         "function_call": None,
                         "role": None,
                         "tool_calls": None
                         },
             "finish_reason": None,
             "index": 0,
             "logprobs": None}
        ],
        "created": 1722566945,
        "model": "gpt-4o-mini",
        "object": "chat.completion.chunk",
        "system_fingerprint": "fp_a9bfe9d51d",
        "usage": None
    }

    def __init__(self, content, stop=False):
        self.content = content
        self.stop = stop

    def model_dump(self):
        self.data["choices"][0]["message"]["content"] = self.content
        if self.stop:
            self.data["choices"][0]["finish_reason"] = "stop"
        return self.data


class MockSensitiveWordsDao:
    @classmethod
    def get_sensitization_data(cls):
        """
        获取敏化数据
        """
        s_data = [("深信服", "颙镔槊"), ("sangfor", "YONGBINSHUO")]
        d_data = [("颙镔槊", "深信服"), ("YONGBINSHUO", "YONGBINSHUO")]
        return s_data, d_data


sensitive_words = SensitiveWords
sensitive_words.dao = MockSensitiveWordsDao
sensitive_words = sensitive_words(
    get_content_func=get_content,
    update_content_func=update_content,
    need_sensitization=True,
)


def test_sensitization_process_messages():
    messages = list()
    input_content = "深信服"
    output_content = "颙镔槊"
    messages.append(dict(role="system", content=input_content))
    messages = sensitive_words.sensitization_process_messages(messages=messages)
    for message in messages:
        assert message["content"] == output_content


def test_desensitization_process_blocking():
    input_content = "颙镔槊"
    output_content = "深信服"
    completion = Completion(content=input_content)
    res = sensitive_words.desensitization_process_blocking(completion)
    assert res["choices"][0]["message"]["content"] == output_content


def create_completion_stream(contents):
    for content in contents:
        completion = Completion(content=content)
        yield completion
    completion = Completion(content=None, stop=True)
    yield completion


def test_desensitization_process_stream():
    contents = ["介绍如下," "颙", "镔槊", "是一上市公司"]
    output_content = "介绍如下,深信服是一上市公司"
    completion_stream = create_completion_stream(contents)
    completion = sensitive_words.desensitization_process_stream(completion_stream)
    content = ""
    for response in completion:
        if response["choices"][0]["finish_reason"] == "stop":
            break
        content += response["choices"][0]["message"]["content"]
    assert content == output_content
