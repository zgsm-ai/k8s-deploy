import re
import json
import logging

from autogen import UserProxyAgent
from autogen.io.base import IOStream

from services.action import RequestData, get_action_strategy, ChatbotOptions
from services.dify_chat import ChatBotWithHistory
from services.agents.dify_agent import DifyAgent
from services.agents.dify_helper import convert_raw_context_to_dict
from services.agents.dify_model_client import fix_messages
from services.agents.obsever_groupchat import ObserverGroupChat
from services.agents.observer_group_manager import ObserverGroupManager
from services.system.dify_agent_service import DifyAgentService
from common.constant import LoggerNameContant, DifyAgentConstant
from third_platform.dify.dify_manager import DifyManager

CHOSEN_PROMPT_TMP = """## `{action_name}`:
Description: {description}
Usage:
```
{{
    "next_action": "{action_name}",
    "objective": "<Describe the action item needed to progress towards the objective in Chinese>"
}}
```"""

logger = logging.getLogger(LoggerNameContant.DIFY_CHAT)
dify_agent_service = DifyAgentService()


class AgentChatBot(ChatBotWithHistory):
    def __init__(self, conv_id, chat_id):
        super().__init__()
        # 本轮对话
        self.conv_id = conv_id
        # 本次对话
        self.chat_id = chat_id
        # chat_group的通用参数
        self.chat_group_data = dict()

    def chat_stream(self, query: str, user_context: str, mode="normal", user=None):
        # iostream = IOStream.get_default()
        self.load_conversation(self.conv_id)
        user_context = convert_raw_context_to_dict(user_context)
        # 增加conversation id用于过程中上下文的获取
        user_context["conversation_id"] = self.conv_id
        user_context["chat_id"] = self.chat_id
        if mode == "group":
            self._chat_group(query, user_context, user=user)
        else:
            self._chat_normal(query, user_context, user=user)
        self.save_conversation(self.conv_id)

    def _chat_group(self, query: str, user_context: dict, user=None):
        """
        根据用户上下文进行multi-agent对话。
        场景划分：追问场景和首次对话场景
        轮次划分：本轮对话（conversation），本次对话（chat）
        agent划分：首节点、尾节点、守卫节点（兜底）等
        核心方法：custom_speaker_selection_func

        Args:
            query (str): 用户输入的查询。
            user_context (dict): 用户的上下文信息。
            user (optional): 当前用户信息。

        Returns:
            None
        """
        # 1.检测依赖对象是否都存在
        observer_agent = dify_agent_service.get_observer_agent()
        if not observer_agent:
            raise RuntimeError("未配置观察者 agent")
        registed_members = dify_agent_service.get_group_members()
        group_guardian_config = dify_agent_service.get_group_guardian()
        if not group_guardian_config:
            raise RuntimeError("未配置普通聊天 agent")

        group_guardian = DifyAgent(dify_agent=group_guardian_config)

        available_members = [DifyAgent(
            dify_agent=dify_member
        ) for dify_member in registed_members]
        user_proxy = UserProxyAgent("user", code_execution_config=False, human_input_mode="NEVER")

        # 用于传递参数到依赖函数
        self.chat_group_data = [
            available_members, group_guardian, observer_agent, user_context, query, user
        ]

        # 2.进行multi-agent对话
        groupchat = ObserverGroupChat(
            # 这个数组允许重复的人，兜底角色可以存在available_members
            agents=[user_proxy, group_guardian] + available_members,
            messages=self.chat_history,
            max_round=10,
            speaker_selection_method=self.custom_speaker_selection_func
        )
        manager = ObserverGroupManager(conv_id=self.conv_id, groupchat=groupchat)
        manager.update_user_context(user_context)
        manager.update_user_display_name(user)
        try:
            user_proxy.initiate_chat(manager, message=query, clear_history=False)

            # 3.保存历史上下文
            self.chat_history = fix_messages(groupchat.messages)
        finally:
            manager.do_finish()

    def _chat_normal(self, query: str, user_context: dict, user=None):
        """
        普通对话，无代码上下文

        Args:
            query (str): 用户输入的查询。
            user_context (dict): 用户的上下文信息。
            user (optional): 当前用户信息。

        Returns:
            None
        """
        iostream = IOStream.get_default()

        # normal_chat_agent = dify_agent_service.get_normal_chat_agent()
        # if not normal_chat_agent:
        #     raise RuntimeError("未配置普通聊天 agent")

        conversation = ""
        for message in fix_messages(self.chat_history):
            conversation += f"{message['role']}: {message['content']}\n"
        data = {
            "conversation": conversation,
            "context": json.dumps(user_context),
            "query": query,
            "user": user,
            "stream": True,
            "action": "zhuge_normal_chat"
        }
        data = RequestData(data)
        options = ChatbotOptions(data.raw_data)
        strategy = get_action_strategy(data.action)
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
        # 为保障后续的一问一答的正常运行，在这里构造历史完整会话流
        self.add_user_message(query)
        # 避免跟 autogen 的角色冲突，这里特意换一下名字
        self.add_ai_message(full_data, ai_name="ai")

    @staticmethod
    def is_last_speaker_last(last_speaker) -> bool:
        """
        判断上个agent是否是最后一个，是则返回True，不是则返回False；
        如果没有上个speaker，则不纳入该方法
        """
        # 前提必须是有上个speaker
        if last_speaker and hasattr(last_speaker, "is_last"):
            if last_speaker.is_last:
                return True
            else:
                return False

    @staticmethod
    def is_first_conversation(groupchat) -> bool:
        """
        判断是否本轮初始会话
        """
        return len(groupchat.messages) <= 1

    @staticmethod
    def is_first_chat(last_speaker) -> bool:
        """
        判断是否本次初始会话
        """
        if not last_speaker or last_speaker.name == "user":
            return True

    def custom_speaker_selection_func(self, last_speaker, groupchat):
        """
        自定义的说话者选择函数
        Args:
            last_speaker (): 上一个说话者
            groupchat (): 群聊对象
        Returns:
            返回选择的角色
        """
        # 若上一个为叶子节点，则直接结束
        if self.is_last_speaker_last(last_speaker) is True:
            return None

        # 获取依赖上下文：
        available_members, group_guardian, observer_agent, user_context, query, user = self.chat_group_data
        # 1. 根据内容选择下一个 agent，输出"干什么"
        # 历史信息
        conversation = ""
        # 如果是本轮对话第一次
        if self.is_first_conversation(groupchat):
            # 开头只从 first 类型的 members 中选
            members = list(filter(lambda a: a.is_first, available_members))
        else:
            # 从所有类型的 members 中选
            members = available_members
            if last_speaker:
                # 避免重复选择同一个 agent
                members = list(filter(lambda a: a.display_name != last_speaker.name, available_members))

            # 用户原始提问去掉，后面会加
            for message in fix_messages(groupchat.messages[1:]):
                conversation += f"{message['role']}: {message['content']}\n"
        # 可选项提示词
        chosen_prompt = "\n\n".join(
            [CHOSEN_PROMPT_TMP.format(
                action_name=re.search(DifyAgentConstant.AGENT_DISPLAY_NAME_PATTERN, member.display_name).group(1),
                description=member.description
            ) for member in members if "|" in member.display_name])
        # 观察者传递的参数
        result = DifyManager.do_app(observer_agent.dify_typo, observer_agent.dify_key, {
            # 给老何增加参数服务于提取
            "base_url": user_context.get("base_url", "http://chatgpt.sangfor.com"),
            "conversation_id": user_context.get("conversation_id", ""),
            "chat_id": user_context.get("chat_id", ""),
            "conversation": conversation,
            "chosen": chosen_prompt,
            "query": query,
            "user": user
        }, url=observer_agent.dify_url)
        next_action = result.get("next_action")
        logger.info(f"本轮对话：{self.conv_id}，本次对话: {self.chat_id}, 选择了：{next_action}")
        objective = query

        # 2. 处理下一个agent
        if not next_action:
            # 若没选则放行到兜底选择
            selected_result = None
        else:
            # 检查是否匹配
            selected_member = None
            for member in members:
                if next_action in member.display_name:
                    selected_member = member
                    break
            if selected_member:
                # 输出选择结果到 ui
                match = re.search(DifyAgentConstant.AGENT_UI_PATTERN, selected_member.display_name)
                if not match:
                    selected_result = None
                logger.info("选择了: {agent_name} 目标: {objective}".format(
                    agent_name=match.group(1),
                    objective=objective
                ))
                selected_member.set_objective(objective)
                selected_result = selected_member
            else:
                selected_result = None
        # 3. 返回结果
        if not selected_result and (
                self.is_first_chat(last_speaker) is True or self.is_last_speaker_last(last_speaker) is False):
            # 使用兜底规则：没有获取到下一个步骤者 && （本次对话首次 or 上一个说话者非最后一个）
            group_guardian.set_objective(objective)
            selected_result = group_guardian
            logger.info("未选择到目标，使用兜底的角色：group_guardian")
        return selected_result
