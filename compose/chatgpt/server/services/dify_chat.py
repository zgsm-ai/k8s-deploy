import json
import logging
import time

from common.constant import UserBehaviorAction, ActionsConstant
from services.agents.agent_data_classes import ChatRequestData
from services.ai_e2e.ai_e2e_case_task import AiE2ECaseTaskService
from third_platform.dify.dify_manager import DifyManager
from services.system.dify_agent_service import DifyAgentService
from third_platform.es.chat_messages.ide_data_as_service import ide_es_service
from bot.chat_history import ChatHistory

dify_agent_service = DifyAgentService()
logger = logging.getLogger(__name__)

class DifyChatBot(ChatHistory):
    """
    与dify进行对话
    """
    def __init__(self, conv_id: str):
        super().__init__()
        self.conv_id = conv_id
        if conv_id:
            self.load_conversation(conv_id)
        # agent临时保存步骤结果
        self.temp_chat_history = []

    @property
    def history_messages(self) -> str:
        # 由于 dify 接口仅能接收字符串，所以这里统一转换一下
        history_messages_str = ""
        # TODO: 这里可能需要做一下上下文长度切割
        for message in self.chat_history:
            history_messages_str += f"{message['role']}: {message['content']}\n"
        return history_messages_str

    def add_temp_message(self, message: str, ai_name: str = "assistant") -> bool:
        """
        制作当前agent每个步骤临时会话历史
        """
        self.temp_chat_history.append({
            "role": ai_name,
            "content": message
        })
        return True

    @property
    def temp_history_message(self) -> str:
        """
        agent会话历史，历史会话+步骤执行结果
        """
        history_messages_str = ""
        for message in self.chat_history:
            history_messages_str += f"{message['role']}: {message['content']}\n"
        for temp_message in self.temp_chat_history:
            history_messages_str += f"{temp_message['role']}: {temp_message['content']}\n"
        return history_messages_str

    def make_plan_step_data(self, query: str) -> dict:
        return {
            "query": query,
            "hisotry_messages": self.history_messages
        }

    def make_agent_task_data(self, query: str, overall_plan: str, **kwargs) -> dict:
        """
        制作agent请求数据
        """
        data = {
            # dify 应用接口接收的数据结构(inputs)
            "query": query,
            "plan": overall_plan,
            "conversation": self.temp_history_message,
            # dify manager 处理的参数
            "stream": True
        }
        # 有额外上下文的话直接传递过去
        if kwargs:
            data.update(kwargs)
        return data

    def over_step_plan_join(self, data_list: list) -> str:
        """
        agent规划返回的步骤——>整体规划
        """
        content = ""
        for index, item in enumerate(data_list):
            step_data = item.get("args", {}).get("objective", "")
            content += f"{index + 1}. {step_data}" + "\n"
        return content

    def save_plan_conversation(self, conversation_id) -> None:
        """
        agent整体步骤结果保存
        """
        self.conversations.add_conversation(conversation_id, self.temp_chat_history)

    def make_agent_plugin_data(self, code: str, **kwargs) -> dict:
        data = {
            # dify 应用接口接收的数据结构(inputs)
            "code": code,
            # dify manager 处理的参数
            "stream": True
        }
        # 有额外上下文的话直接传递过去
        if kwargs:
            data.update(kwargs)
        return data

    def chat_stream(self, req: ChatRequestData, **kwargs):
        # 先添加用户的消息
        self.add_user_message(req.prompt)

        # 适配规划agent应用
        yield self.make_chunk({
            "event": "sf_start"
        })
        yield self.make_chunk({
            "event": "sf_task_planning_start"
        })
        # 调用规划agent进行步骤拆解
        agent_step_result = DifyManager.planning_step(self.make_plan_step_data(req.prompt))
        yield self.make_chunk({
            "event": "sf_task_planning_answer",
            "plans": agent_step_result
        })
        agent_step_list = agent_step_result.get("plans", [])
        if agent_step_list and len(agent_step_list) > 0:
            # 整体规划
            overall_plan = self.over_step_plan_join(agent_step_list)
            # 返回的整个步骤结果
            for agent_data in agent_step_list:
                agent_typo = agent_data.get("app_typo")
                agent_key = agent_data.get("app_key")
                query_step = agent_data.get("args", {}).get("objective", "")
                data = self.make_agent_task_data(query_step, overall_plan, **kwargs)
                for (chunk_data, reply_msg) in DifyManager.do_app(agent_typo, agent_key, data):
                    if chunk_data:
                        yield self.make_chunk(chunk_data)
                    elif reply_msg:
                        # 将每个步骤的结果临时保存
                        self.add_temp_message(reply_msg)
            # 保存整体返回结果
            self.save_plan_conversation(self.conv_id)
        yield self.make_chunk({
            "event": "sf_end"
        })

    def make_chunk(self, chunk_data: any) -> str:
        try:
            if isinstance(chunk_data, str):
                chunk_data = json.loads(chunk_data)
        except json.decoder.JSONDecodeError:
            # 这里可能是异常字符串错误，这种直接返回
            return chunk_data

        if not isinstance(chunk_data, dict):
            # 这里可能是异常类型，暂时直接返回
            return chunk_data

        # 针对dify异常参数做的日志和前端报错，支持排查
        if "code" in chunk_data:
            if chunk_data["code"] == "invalid_param":
                logger.error(f"识别到dify的chunk_data异常，异常数据：{chunk_data}, conversation_id: {self.conv_id}")
                chunk_data["dify_error"] = "unknown fail"
            else:
                logger.warning(f"识别到有code的日志，记录异常数据: {chunk_data}, conversation_id: {self.conv_id}")

        # 添加一些内部元信息
        chunk_data.update({
            "sf_conversation_id": self.conv_id
        })

        # 最后再反序列化回去
        chunk_data = json.dumps(chunk_data)
        # 为方便调试查看，这里加点换行符
        chunk_data += "\n\n"
        return chunk_data

    @staticmethod
    def get_nth_element(input_string, n, delimiter='|'):
        # 使用 split 方法根据指定的分隔符切割字符串
        elements = input_string.split(delimiter)

        # 检查切割后的列表长度是否大于等于 n，以确保有第 n 个元素
        if len(elements) >= n:
            return elements[n - 1]  # 使用 strip 方法去除前后空格
        else:
            return ""  # 如果没有第 n 个元素，返回 None

    def dispatch_execution_agent(self, code: str, action: str, req: dict, **kwargs):
        """
        agent分发与执行
        action:根据不同的action分别执行不同的agent功能
        code: 用户选中的代码
        **kwargs:其他参数
        """
        logger.info(f"dispatch_execution_agent: code:{code}, action: {action}, req: {req}")
        
        req["created_at"] = time.time()
        self.add_user_message(code)
        yield self.make_chunk({
            "event": "sf_start"
        })
        # 根据action 获取对应agent的name,typo以及key
        agent_data = dify_agent_service.get_agent_type_key(action)
        if not agent_data:
            raise RuntimeError("agent未配置")
        yield self.make_chunk({
            "event": "sf_task_agent_start",
            "agent_name": agent_data.display_name,
            "agent_icon": agent_data.icon,
            "tooltip": agent_data.tooltip,
            "actionName": self.get_nth_element(agent_data.display_name, 2)
        })

        # 此处区分E2E用例生成
        if action == ActionsConstant.E2E_CASE_GEN:
            for chunk_data in AiE2ECaseTaskService.make_result_by_ide(req):
                yield self.make_chunk(chunk_data)
        else:
            data = self.make_agent_plugin_data(code, **kwargs)

            total_tokens = 0
            for (chunk_data, reply_msg) in DifyManager.do_app(agent_data.dify_typo, agent_data.dify_key, data,
                                                              agent_data.dify_url):
                if chunk_data:
                    if "total_tokens" in chunk_data:
                        total_tokens += chunk_data.get("total_tokens", 0)
                    yield self.make_chunk(chunk_data)
                elif reply_msg:
                    # 预期 reply_msg 为str类型
                    if isinstance(reply_msg, str):
                        msg = reply_msg
                    else:
                        # 兼容返回类型不对的情况
                        msg = str(reply_msg)
                    req["response_content"] = msg
                    yield self.make_chunk({
                        "event": "sf_task_agent_answer",
                        "agent_answer": reply_msg
                    })
                    # 将执行结果存入到历史会话中
                    self.add_ai_message(reply_msg)
            logger.info(f"跟dify通信结束，conv_id: {self.conv_id}")
            # 保存数据
            self.save_conversation(self.conv_id)
            req.update({
                "finish_at": time.time(),
                "agent_name": agent_data.display_name,
                "total_tokens": total_tokens,
                "request_mode": "http"
            })
            # 保存es
            ide_es_service.insert_data(req)
        logger.info(f"快捷指令server收尾结束，conv_id: {self.conv_id}")
        yield self.make_chunk({
            "event": "sf_end"
        })

    def user_give_likes(self, name: str, es_id: str, **fields):
        """
        用户点赞处理，同时更新es平台和dify平台
        message_id:dify平台消息id
        action:每个agent对应的事件
        es_id:es平台对应的id
        """
        status = 200
        # 更新es平台的字段
        es_result = ide_es_service.update_es_feedbacks(es_id, 'feedbacks', fields.get('rating', ''))
        es_updata = ide_es_service.get_es_data(es_id)
        # 将用户点赞作为本次会话有效
        if es_updata and fields.get("rating", "") == "like" and es_updata.get("accept_num", 0) == 0:
            ide_es_service.update_es_feedbacks(es_id, 'accept_num', 1)
        if fields.get("message_id", ""):
            message_id = fields.pop("message_id")
            # 获取action对应的agent数据
            agent_data = dify_agent_service.get_agent_name_key(name)
            if not agent_data:
                es_result["dify_feedbacks_status"] = f"name:{name}无效,不存在此agent!"
                return es_result, 403
            # dify仅支持agent和聊天助手点赞
            if agent_data.dify_typo == "chat-bot":
                res = DifyManager.give_likes_app(agent_data.dify_typo, fields, message_id, agent_data.dify_url,
                                                 agent_data.dify_key)
                if res:
                    es_result.update({"dify_status": "Successful"})
                else:
                    es_result.update({"dify_status": "Failed"})
                    status = 500
            else:
                es_result["dify_status"] = "Failed,The agent does not support likes!"
            return es_result, status
        else:
            return es_result, status

    def user_give_feedbacks(self, es_id: str, accept_num: int, behavior: str) -> dict:
        """
        处理用户采纳结果,用户每一次的交互行为都要记录下来
        注意:一次会话可能有多次请求，多次请求可能包含多次交互
        es_id:es平台id
        accept_num:用户采纳行数
        """
        try:
            es_data = ide_es_service.get_es_data(es_id)
            if es_data and behavior in UserBehaviorAction.user_behavior:
                user_behavior = UserBehaviorAction.behavior_keys.get(f"{behavior}")
                update_data = {
                    "accept_num": es_data["accept_num"] + accept_num,
                    f"{user_behavior}": es_data.get(user_behavior, 1) + 1
                }
                res = ide_es_service.update_by_id(es_id, update_data)
                if res.get("_shards", {}).get("successful") == 1:
                    return {"es_status": "Successful"}
                else:
                    logger.error(f"es更新ide_data数据失败，失败日志： {str(res)}")
                    return {"es_status": "Failed"}
        except Exception as err:
            logger.error(f"es更新ide_data数据失败，失败日志： {str(err)}")
