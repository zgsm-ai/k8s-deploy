import re
import json
import logging

from autogen.io.base import IOStream

from services.action import get_action_strategy, ChatbotOptions
from bot.chat_history import get_history
from services.agents.agent_data_classes import ChatRequestData, make_cls_with_dict
from services.agents.dify_helper import convert_raw_context_to_dict
from services.agents.dify_model_client import fix_messages
from common.constant import LoggerNameContant

logger = logging.getLogger(LoggerNameContant.DIFY_CHAT)

class AgentChatBot:
    """
    单角色对话
    """
    def __init__(self, conv_id, chat_id, history=None):
        super().__init__()
        # 本轮对话
        self.conv_id = conv_id
        # 本次对话
        self.chat_id = chat_id
        # 对话历史管理器
        self.history = history if history else get_history()

    def chat_stream(self, req: ChatRequestData, context: str, username=None):
        """
        流式对话，单角色对话
        """
        self.history.load_conversation(self.conv_id)
        # context = convert_raw_context_to_dict(context)
        # # 增加conversation id用于过程中上下文的获取
        # context["conversation_id"] = self.conv_id
        # context["chat_id"] = self.chat_id
        self._chat_normal(req, context, username=username)
        self.history.save_conversation(self.conv_id)

    def _get_advise(self, req: ChatRequestData, context: dict, username=None):
        """
        获取LLM建议的下一步操作列表，该操作是针对本轮对话的后续常见操作
        """
        iostream = IOStream.get_default()
        data = {
            # "context": json.dumps(context),
            "context": context,
            "username": username,
            "display_name": username,
            "conversation_id": self.conv_id,
            "chat_id": self.chat_id,
            "language": req.language,
            "prompt": req.prompt,
            "query": req.query,
            "code": req.code,
            "action": "advise"
        }
        data = make_cls_with_dict(ChatRequestData, data)
        options = ChatbotOptions()
        options.stream = True
        strategy = get_action_strategy(data.action)
        strategy.set_history(self.history)
        data.prompt = strategy.get_prompt(req)
        result = strategy.make_result(data, options)
        logger.info(f"_get_advise(): result: {result}")
        try:
            data = json.loads(result)
            iostream.print_agent_advise(data)
        except json.decoder.JSONDecodeError:
            iostream.print_agent_advise([{"title": "继续", "prompt": "继续"}])

    def _chat_normal(self, req: ChatRequestData, context: dict, username=None):
        """
        普通对话，无代码上下文

        Args:
            query (str): 用户输入的查询。
            context (dict): 用户的上下文信息。
            username (optional): 当前用户信息。

        Returns:
            None
        """
        iostream = IOStream.get_default()

        data = {
            # "context": json.dumps(context),
            "context": context,
            "username": username,
            "display_name": username,
            "conversation_id": self.conv_id,
            "chat_id": self.chat_id,
            "language": req.language,
            "prompt": req.prompt,
            "query": req.query,
            "code": req.code,
            "action": "zhuge_normal_chat"
        }
        data = make_cls_with_dict(ChatRequestData, data)
        options = ChatbotOptions()
        options.stream = True
        strategy = get_action_strategy(data.action)
        strategy.set_history(self.history)
        data.prompt = strategy.get_prompt(req)
        logger.info(f"chat_normal(): data: {data.__dict__}")
        logger.info(f"chat_normal(): strategy: {strategy.name}, options: {options.__dict__}")
        full_data = ""
        for chunk_data in strategy.make_result(data, options):
            if chunk_data:
                if chunk_data.get("event", "") == "sf_tokens":
                    full_data = chunk_data.get("total_answer", "")
                iostream.print_dify_chunk(
                    chunk_data,
                    sender="诸葛神码",
                    sender_icon=None
                )
        self._get_advise(req, context, username)
        # 为保障后续的一问一答的正常运行，在这里构造历史完整会话流
        self.history.add_user_message(req.prompt)
        self.history.add_ai_message(full_data)

