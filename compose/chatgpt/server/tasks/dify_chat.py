from common.constant import DifyAgentConstant
from services.agents.agent_data_classes import ChatRequestData, make_cls_with_dict
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
        context_uuid = request_data.get("context", "").strip("\r\n").strip("\n")
        logger.info(f"context uuid： {context_uuid}, request: {request_data}")
        data = CodeNavigationService.get_cache_data(context_uuid)
        context = data.get("context") or "{}" if isinstance(data, dict) else "{}"
        request_data["context"] = context

        req = make_cls_with_dict(ChatRequestData, request_data)
        req.display_name = user_display_name
        agent_chat_with_redis(req)
