import json
import random
import re
import time

from autogen.io.base import IOStream
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import ChatCompletionMessage, Choice
from openai.types.completion_usage import CompletionUsage

from common.constant import DifyAgentConstant
from third_platform.dify.dify_manager import DifyManager


def fix_messages(messages):
    fixed_messages = []
    for message in messages:
        if message["role"] == "system":
            continue
        if not message["content"]:
            continue
        role = message["role"]
        name = message.get("name")
        if name and name.lower() != "user":
            # 由于通过名字增加了一些匹配规则，这里用正则去提取
            match = re.search(DifyAgentConstant.AGENT_DISPLAY_NAME_PATTERN, name)
            if match:
                role = match.group(1)
            else:
                role = name
        fixed_messages.append({
            **message,
            "role": role,
        })
    return fixed_messages


class DifyModelClient:
    def __init__(self, config, sender, sender_icon=None):
        self.dify_client = DifyManager.get_helper_by_typo(config.get("dify_typo"))
        self.config = config
        self.sender = sender
        self.sender_icon = sender_icon

    def _make_request_data(self, params):
        messages = fix_messages(params.get("messages", []))

        conversation = ""
        query = ""
        for message in messages:
            role = message["role"]
            if role and role.lower() == "assistant":
                role = self.sender

            if role.lower() == "user" and message["content"]:
                query = message["content"]
            conversation += f"{role}: {message['content']}\n"
        if len(conversation) == 0:
            raise Exception(f"conversation is empty: {params}")

        context = messages[-1].get("user_context", "")
        data = {
            "stream": params.get("stream", False),
            "conversation": conversation,
            "context": context,
            "query": query,
            "user": messages[-1].get("user", None)
        }
        return data

    def create(self, params):
        """Create a new model."""
        iostream = IOStream.get_default()

        data = self._make_request_data(params)
        response_msg = ""

        url = self.config.get("dify_url")
        key = self.config.get("dify_key")
        for (chunk_data, reply_msg) in self.dify_client.make_request(url, key, data):
            if chunk_data:
                if isinstance(chunk_data, str):
                    try:
                        chunk_data = json.loads(chunk_data)
                    except json.JSONDecodeError:
                        continue
                iostream.print_dify_chunk(
                    chunk_data,
                    sender=self.sender,
                    sender_icon=self.sender_icon
                )
            elif reply_msg:
                # 将每个步骤的结果临时保存
                response_msg = reply_msg
        iostream.print_dify_end(self.sender)

        response = ChatCompletion(
            id=str(random.randint(0, 1000)),
            model="dify",
            created=int(time.time() * 1000),
            object="chat.completion",
            choices=[Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(
                    role="assistant",
                    content=response_msg,
                    function_call=None,
                    tool_calls=None
                ),
                logprobs=None,
            )],
            usage=CompletionUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            ),
        )
        return response

    def message_retrieval(self, response):
        """Retrieve the messages from the response."""
        return [choice.message for choice in response.choices]

    def cost(self, response):
        return 0

    @staticmethod
    def get_usage(response):
        """Return usage summary of the response using RESPONSE_USAGE_KEYS."""
        # ...  # pragma: no cover
        return {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "cost": response.cost,
            "model": response.model,
        }
