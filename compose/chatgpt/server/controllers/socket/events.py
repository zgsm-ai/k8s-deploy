import os
import logging
import asyncio
import socketio
import time
import json

from common.helpers.application_context import ApplicationContext
from services.agents.dify_chat_async import DifyMessageQueueHelper as dify_queue_helper
from common.constant import DifyAgentConstant, LoggerNameContant
from common.exception.exceptions import NoLoginError

logger = logging.getLogger(LoggerNameContant.SOCKET_SERVER)

socket_pool = {}


def get_current_user(auth):
    from services.system.users_service import UsersService
    user = UsersService.create_test_user()
    # api_key = auth.get("api-key")
    # if api_key:
    #     user = UsersService.get_user_by_api_key(api_key)
    # if not user:
    #     _env = os.environ.get("SOCKET_ENV") or os.environ.get("FLASK_ENV")
    #     if _env == 'development' or _env == 'test':
    #         user = UsersService.create_test_user()
    #         ApplicationContext.update_session_user(user)
    return user


def get_current_user_in_socket(sid, auth=None):
    global socket_pool
    if auth:
        current_user = get_current_user(auth)
        if current_user:
            if sid:
                socket_pool[sid] = {"current_user": current_user, "auth": auth}
            return current_user
    else:
        if sid:
            return socket_pool.get(sid, {}).get("current_user")
        else:
            return None


def logout_user_in_socket(sid):
    global socket_pool
    if sid in socket_pool:
        del socket_pool[sid]


class ChatNamespace(socketio.AsyncNamespace):
    def on_connect(self, sid, environ, auth):
        current_user = get_current_user_in_socket(sid, auth)
        if not current_user:
            # 拒绝连接
            logger.error('当前用户不存在，拒绝连接')
            return False
        logger.info(f"Client connected({sid}): {current_user}")
        safe_environ = {k: v for k, v in environ.items() if isinstance(v, (str, int, float))}
        logger.info(f"env: {safe_environ or '{}'}")
        logger.info(f"auth: {auth or '{}'}")

    def on_disconnect(self, sid):
        logout_user_in_socket(sid)
        logger.info(f'Client disconnected({sid})')

    async def on_ping(self, sid, message):
        await self.emit("message", "pong", room=sid)

    async def send_message_loop(self, chat_id, sid, offset=0):
        if not offset:
            offset = 0
        while True:
            """
            通过消息类似缓冲区的形式取而不是使用队列
            因为客户端避免不了出现重连的情况，一旦重连之前服务端的消息就没法再次发送
            所以通过 offset 来记录客户端之前收到哪里再次执行时从断点开始
            """
            data = dify_queue_helper.get_data_by_offset(chat_id, offset)
            if not data:
                # FIXME: 如果传入的 chat_id 实际并不存在，这里会一直循环。考虑加个超时判断机制
                await asyncio.sleep(0)
            else:
                if isinstance(data, dict):
                    await self.emit('json', data, room=sid)
                elif isinstance(data, str):
                    await self.emit('message', data, room=sid)
                    if data == DifyAgentConstant.AGENT_CHAT_DONE_MSG:
                        break
                # 取到消息后才能更新 offset。offset 的顺序由 dify_queue_helper 内部进行管理和保障
                offset += 1

    async def on_chat(self, sid, request_data: dict):
        logger.info(f'Received message({sid}) in chat: {request_data}')
        current_user = get_current_user_in_socket(sid)
        # 使用chat_id作为每次返回给前端的内容, 也就是存储在redis的内容
        chat_id = sid
        if not current_user:
            raise NoLoginError()

        from tasks.dify_chat import execute_dify_chat_async
        request_data["created_at"] = time.time()
        request_data["ide"] = socket_pool.get(sid, {}).get("auth", {}).get('ide', '')
        request_data["ide_version"] = socket_pool.get(sid, {}).get("auth", {}).get('ide-version', '')
        request_data["ide_real_version"] = socket_pool.get(sid, {}).get("auth", {}).get('ide-real-version', '')
        request_data["username"] = current_user.display_name
        request_data["chat_id"] = chat_id
        execute_dify_chat_async.delay(
            sid=sid,
            user_display_name=current_user.display_name,
            request_data=request_data
        )

        # 发送 chat_id 给前端，前端若出现断联则可以通过 chat_id 重新连接
        await self.emit("updateChatId", chat_id, room=sid)
        await self.send_message_loop(chat_id, sid)

    async def on_rechat(self, sid, request_data):
        chat_id = request_data.get("chat_id")
        offset = request_data.get("offset", 0)
        logger.info(f'Received rechat request: {chat_id}')
        if chat_id:
            await self.send_message_loop(chat_id, sid, offset)


def register_socketio(socketio):
    # 注册自定义命名空间
    socketio.register_namespace(ChatNamespace('/chat'))
