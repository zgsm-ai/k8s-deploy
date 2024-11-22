from common.constant import DifyAgentConstant
from services.agents.agent_data_classes import ChatAgentData, ChatRequestData, make_cls_with_dict
from services.agents.dify_chat_async import agent_chat_with_redis
from services.context_navigation.code_navigation_service import CodeNavigationService
from tasks import celery_app, handle_db
from lib.log import SocketLoggerWrapper
from logger import register_dify_chat_logger


logger = register_dify_chat_logger()
wrapped_logger = SocketLoggerWrapper(logger)


@celery_app.task(queue=DifyAgentConstant.DIFY_CHAT_CELERY_QUEUE,
                 soft_time_limit=DifyAgentConstant.CELERY_TASK_TIMEOUT)
@handle_db
def execute_dify_chat_async(sid: str, user_display_name: str, request_data: dict):
    # wrapped_logger日志封装了sid，必须前置
    with wrapped_logger.set_sid(sid):
        # 取出uuid从redis中获取上下文缓存数据
        random_uuid = request_data.get("context", "").strip("\r\n").strip("\n")
        logger.info(f"获取到的uuid： {random_uuid}, request: {request_data}")
        redis_key = random_uuid
        data = CodeNavigationService.get_cache_data(redis_key)
        context = data.get("context") or "{}" if isinstance(data, dict) else "{}"
        request_data["context"] = context

        agent_chat_data = ChatAgentData(
            user_display_name=user_display_name,
            request_data=make_cls_with_dict(ChatRequestData, request_data)
        )
        agent_chat_with_redis(agent_chat_data)
