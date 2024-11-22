import logging
import traceback

from autogen.io.base import IOStream

from services.agent_chat import AgentChatBot
from services.agents.autogen_iostream import AgentChatIOStream
from common.constant import LoggerNameContant

from .agent_data_classes import ChatAgentData


logger = logging.getLogger(LoggerNameContant.DIFY_CHAT)


def agent_chat(data: ChatAgentData, send_json_func, send_msg_func):
    """
    agent生成对话数据，并发送给请求对话的客户端
    """
    iostream = AgentChatIOStream(
        send_json_func=send_json_func,
        send_msg_func=send_msg_func,
    )
    req = data.request_data
    logger.info(f"agent_chat(): data: {data.__dict__}")
    try:
        if req.prompt:
            with IOStream.set_default(iostream):
                chatbot = AgentChatBot(req.conversation_id, req.chat_id)
                chatbot.chat_stream(req, req.context, 
                    mode=req.mode,
                    user=data.user_display_name
                )
    except Exception:
        # 将详细信息打印出来
        traceback.print_exc()
    finally:
        iostream.finish()
        logger.info("执行结束")
