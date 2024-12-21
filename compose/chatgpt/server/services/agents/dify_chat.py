import logging
import traceback

from autogen.io.base import IOStream

from services.agent_chat import AgentChatBot
from services.agents.autogen_iostream import AgentChatIOStream
from common.constant import LoggerNameContant

from .agent_data_classes import ChatRequestData


logger = logging.getLogger(LoggerNameContant.DIFY_CHAT)


def agent_chat(req: ChatRequestData, send_json_func, send_msg_func):
    """
    agent生成对话数据，并发送给请求对话的客户端
    """
    iostream = AgentChatIOStream(send_json_func=send_json_func, send_msg_func=send_msg_func)
    logger.info(f"agent_chat(): req: {req.__dict__}")
    try:
        if req.prompt:
            with IOStream.set_default(iostream):
                chatbot = AgentChatBot(req.conversation_id, req.chat_id)
                chatbot.chat_stream(req, req.context, user=req.display_name)
    except Exception:
        # 将详细信息打印出来
        traceback.print_exc()
    finally:
        iostream.finish()
        logger.info("agent_chat(): 执行结束")
