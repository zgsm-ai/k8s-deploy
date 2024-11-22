#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    简单介绍

    :作者: 陈烜 42766
    :时间: 2023/3/24 14:12
    :修改者: 陈烜 42766
    :更新时间: 2023/3/24 14:12
"""
import logging
import os
import json
from datetime import date
from typing import List

from bot.bot_util import get_prompt_max_tokens, compute_tokens
from common.constant import PromptConstant


def get_default_base_prompt():
    return f"""You are a question-answering AI that can access the internet and respond in Chinese markdown format.
Current date: {str(date.today())}
"""


class Prompt:
    """
    Prompt class with methods to construct prompt
    """

    def __init__(self,
                 user: str = "User",
                 ai: str = "ChatGPT",
                 end: str = "<|im_end|>",
                 systems: List[str] = None,
                 model: str = '') -> None:
        """
        Initialize prompt with base prompt
        """
        self.username = user
        self.ainame = ai
        self.end = end
        base_prompt = os.environ.get("CUSTOM_BASE_PROMPT") or get_default_base_prompt()
        self.base_prompt = systems or [base_prompt]
        # Track chat history
        self.chat_history: list = []
        self.model = model

    def add_to_chat_history(self, chat: str) -> None:
        """
        Add chat to chat history for next prompt
        """
        self.chat_history.append(chat)

    def add_to_history(self,
        user_request: str,
        response: str,
        user: str = None,
    ) -> None:
        """
        Add request/response to chat history for next prompt
        """
        self.add_to_chat_history({
            'role': (user or self.username),
            'content': user_request
        })
        self.add_to_chat_history({
            'role': (self.ainame),
            'content': response
        })
        # self.add_to_chat_history(
        #     (user or self.username)
        #     + ": "
        #     + user_request
        #     + "\n\n\n"
        #     + "{}: ".format(self.ainame)
        #     + response
        #     + "{}\n".format(self.end),
        # )

    @staticmethod
    def num_tokens_from_messages(messages):
        """Returns the number of tokens used by a list of messages."""
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += compute_tokens(value)
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant

        return num_tokens

    def cut_messages(self, messages):
        """
        对超大messages信息进行裁剪，保证发给接口的信息tokens数不能超过最大限制
        :param messages: 问询AI的上下文信息
        :return messages:
        """
        # Check if prompt tokens over max_token
        max_tokens = get_prompt_max_tokens(self.model)
        over_tokens = True
        max_remove = 1000
        messages_cut = False
        for _ in range(max_remove):
            if self.num_tokens_from_messages(messages) > max_tokens:
                messages_cut = True
                if len(messages) > 1:
                    messages.pop(1)
            else:
                over_tokens = False
                break
        if messages_cut:
            logging.warning("【删除历史提问】提问信息超长，自动删除部分最早的用户提问记录")
        if len(messages) <= 1:
            # 用户的提问字符串数量就超上限了，直接mock数据，后续使用
            messages = [{"role": "assistant", "content": PromptConstant.TOKENS_OVER_LENGTH}]
        elif over_tokens:
            # 如果删除的信息数量超max_remove之后tokens还是超了,直接mock数据，后续使用
            messages = [{"role": "assistant", "content": PromptConstant.TOKENS_OVER_LENGTH}]
        return messages

    def history(self, custom_history: list = None, user=None) -> str:
        """
        Return chat history
        """
        history_list = [item for item in (custom_history or self.chat_history)]
        return history_list

    def get_chat_messages(self, new_prompt: str, context_association: bool = True):
        """
        构造发送给LLM的消息列表
        """
        messages = []
        for system in self.base_prompt:
            messages.append({"role": "system", "content": system})
        if context_association:
            # 添加上下文
            for message in self.chat_history:
                # FIXME: 可能有其他场景
                if message["role"] == self.username or message["role"] == 'user':
                    messages.append({"role": "user", "content": message['content']})
                if message['role'] == self.ainame or message["role"] == 'assistant':
                    messages.append({"role": "assistant", "content": message['content']})
        messages.append({"role": "user", "content": new_prompt})
        messages = self.cut_messages(messages)
        prompt_tokens = self.num_tokens_from_messages(messages)
        return messages, prompt_tokens

    def get_user_req_messages(self, new_prompt: str):
        messages = []
        for system in self.base_prompt:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": new_prompt})

        return messages

    def construct_prompt(
            self,
            new_prompt: str,
            custom_history: list = None,
            user: str = None,
    ):
        """
        Construct prompt based on chat history and request
        """
        prompt = ("\n".join(self.base_prompt)
                  + self.history(custom_history=custom_history, user=user)
                  + (user or self.username)
                  + ": "
                  + new_prompt
                  + "\n{}:".format(self.ainame)
                  )
        # Check if prompt over 4000*4 characters
        max_tokens = get_prompt_max_tokens(self.model)
        prompt_tokens = compute_tokens(prompt)
        if prompt_tokens > max_tokens:
            # Remove oldest chat
            if len(self.chat_history) == 0:
                return prompt, prompt_tokens
            self.chat_history.pop(0)
            # Construct prompt again
            prompt, _ = self.construct_prompt(new_prompt, custom_history, user)
        return prompt, prompt_tokens


class Conversation:
    """
    For handling multiple conversations
    """

    def __init__(self, redis) -> None:
        self.cache = redis
        self.conversations = {}

    def add_conversation(self, key: str, history: list) -> None:
        """
        Adds a history list to the conversations dict with the id as the key
        """
        self.conversations[key] = history
        self.cache.set(key, history)
        self.cache.expire(key, 60 * 60)  # 缓存超时时间设置为1小时

    def get_conversation(self, key: str) -> list:
        """
        Retrieves the history list from the conversations dict with the id as the key
        """
        # return self.conversations[key]
        return self.cache.get(key)

    def remove_conversation(self, key: str) -> None:
        """
        Removes the history list from the conversations dict with the id as the key
        """
        del self.conversations[key]
        self.cache.remove(key)

    def is_exist(self, key: str):
        if key in self.cache.keys("*"):
            return True
        else:
            return False

    def __str__(self) -> str:
        """
        Creates a JSON string of the conversations
        """
        return json.dumps(self.conversations)

    def save(self, file: str) -> None:
        """
        Saves the conversations to a JSON file
        """
        with open(file, "w", encoding="utf-8") as f:
            f.write(str(self))

    def load(self, file: str) -> None:
        """
        Loads the conversations from a JSON file
        """
        with open(file, encoding="utf-8") as f:
            self.conversations = json.loads(f.read())
