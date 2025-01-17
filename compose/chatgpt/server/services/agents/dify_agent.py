import json

from autogen import ConversableAgent

from config import CONFIG

from .dify_model_client import DifyModelClient
from .observer_group_manager import ObserverGroupManager


class DifyAgent(ConversableAgent):
    def __init__(
        self,
        dify_agent,
        **kwargs
    ):
        self.dify_agent = dify_agent
        self.display_name = dify_agent.display_name
        self.is_first = dify_agent.is_first
        self.is_last = dify_agent.is_last
        # 用户过程中的 agent 指令存储
        self._objective = ""

        kwargs["name"] = dify_agent.display_name
        kwargs["description"] = dify_agent.description
        kwargs['llm_config'] = {
            "config_list": [
                {
                    "model_client_cls": "DifyModelClient",
                    "dify_typo": dify_agent.dify_typo,
                    "dify_key": dify_agent.dify_key,
                    "dify_url": dify_agent.dify_url or CONFIG.app.DIFY.base_url
                }
            ],
            # 是否缓存生成内容
            "cache_seed": None,
            "stream": True,
        }
        super().__init__(**kwargs)
        self.register_model_client(
            model_client_cls=DifyModelClient,
            sender=dify_agent.display_name,
            sender_icon=dify_agent.icon
        )
        self.register_reply(ObserverGroupManager, DifyAgent.generate_oai_reply)

    def set_objective(self, objective):
        self._objective = objective

    def generate_oai_reply(
        self,
        messages=None,
        sender=None,
        config=None,
    ):
        """Generate a reply using autogen.oai."""
        # 将 group 的完整上下文传过去。默认是只会拿跟这个 agent 相关的上下文
        history_messages = sender.chat_messages_for_summary(None)
        # 发送前尝试更新一下上下文
        sender.update_env_context()
        # 带上当前指令和历史上下文作为最后一个消息
        history_messages.append({
            "content": self._objective,
            "role": "user",
            # 需要解成 json 字符串
            "user_context": json.dumps(sender.user_context),
            "user": sender.username
        })
        try:
            return super().generate_oai_reply(
                messages=history_messages,
                sender=sender,
                config=config,
            )
        finally:
            # 每次生成完后，尝试更新一下上下文
            sender.update_env_context()
