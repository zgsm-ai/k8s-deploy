import json
import time
from lib.cache import Cache
from common.constant import DifyAgentConstant, ContextNavigationConstant
from third_platform.es.chat_messages.ide_data_as_service import ide_es_service

from .dify_chat import agent_chat
from .agent_data_classes import ChatAgentData

cache = Cache()


def ignore_exceptions(func):
    """
    定义函数ignore_exceptions，用于装饰其他函数以忽略所有异常
    args:
        func: 需要装饰的函数
    return:
        wrapper函数，捕获并忽略异常
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            pass
    return wrapper


class CursorObj:
    offset = 0


class DifyMessageQueueHelper:
    @classmethod
    def _push_data(cls, key, data):
        # 需要对key设置超时时间；但key必须得在创建的时候才能获取到
        is_exist_key = True if cache.connection.exists(key) else False
        cache.connection.rpush(key, cache.serialize(data))
        if is_exist_key is True:
            # 如果不存在，则本次是创建 key，则设置过期时间
            cache.connection.expire(key, 3600)

    @classmethod
    def _pop_data(cls, key):
        data = cache.connection.lpop(key)
        if not data:
            return data
        return cache.deserialize(data)

    @classmethod
    def _make_queue_key(cls, conv_id):
        return f"{DifyAgentConstant.DIFY_CHAT_CELERY_QUEUE}:{conv_id}"

    @classmethod
    def push_json_data(cls, conv_id, json_data, cursor: CursorObj = None):
        if cursor:
            cursor.offset += 1
            json_data["offset"] = cursor.offset
        cls._push_data(cls._make_queue_key(conv_id), f"json:{json.dumps(json_data)}")

    @classmethod
    def push_msg(cls, conv_id, msg, cursor: CursorObj = None):
        if cursor:
            cursor.offset += 1
        cls._push_data(cls._make_queue_key(conv_id), f"msg:{msg}")

    @classmethod
    def handle_data(cls, data):
        if not data:
            return None
        if not isinstance(data, str):
            return data
        if data.startswith("json:"):
            json_data = json.loads(data[5:])
            return json_data
        elif data.startswith("msg:"):
            msg = data[4:]
            return msg

    @classmethod
    def pop_data(cls, conv_id):
        data = cls._pop_data(cls._make_queue_key(conv_id))
        return cls.handle_data(data)

    @classmethod
    def get_data_by_offset(cls, conv_id, offset):
        data = cache.connection.lindex(cls._make_queue_key(conv_id), offset)
        if data:
            return cls.handle_data(cache.deserialize(data))
        else:
            return data


class DifySpecifiedContextHelper(DifyMessageQueueHelper):
    """这个类服务于过程中上下文的获取，业务逻辑的不同，需要复用队列的一些方法"""

    @classmethod
    def _make_queue_key(cls, conv_id):
        redis_key = ContextNavigationConstant.get_local_context_redis_key.format(uuid=conv_id)
        return redis_key

    @classmethod
    def _blpop_data(cls, key, timeout=6) -> str:
        """
        定义类方法_blpop_data，从缓存中阻塞读取数据
        args:
            key: 缓存键
            timeout: 阻塞超时时间，默认为6秒
        return:
            读取的数据，如果读取超时，返回默认值"{}"
        """

        try:
            _, data = cache.connection.blpop(key, timeout)
            if data:
                return cache.deserialize(data)
        except TypeError:
            data = ""
            return data

    @classmethod
    def blpop_data(cls, conv_id):
        data = cls._blpop_data(cls._make_queue_key(conv_id))
        if not data:
            return dict()
        json_data = json.loads(data[5:])
        return json_data


def agent_chat_with_redis(data: ChatAgentData):
    # conv_id = data.request_data.conversation_id
    chat_id = data.request_data.chat_id
    request_data = data.request_data.to_dict()
    request_data["created_at"] = time.time()
    request_data["total_tokens"] = 0
    request_data["total_context"] = ""

    # 游标，需保证所有入 redis 的数据都加上偏移量
    cursor = CursorObj()

    @ignore_exceptions
    def record_send_data(json_data):
        nonlocal request_data
        if json_data.get("dify_chunk", {}).get("event", "") == "sf_tokens":
            request_data["agent_name"] = json_data.get("agent_name", "")
            request_data["total_tokens"] += json_data.get("dify_chunk", {}).get("total_tokens", 0)
            request_data["total_context"] += json_data.get("dify_chunk", {}).get("total_answer", "") + "\n"

    @ignore_exceptions
    def record_send_msg(msg):
        nonlocal request_data
        if msg == DifyAgentConstant.AGENT_CHAT_DONE_MSG:
            request_data["finished_at"] = time.time()
            es_process_data(request_data)

    def send_json_func(json_data):
        # record_send_data(json_data)
        DifyMessageQueueHelper.push_json_data(chat_id, json_data, cursor)

    def send_msg_func(msg):
        # record_send_msg(msg)
        DifyMessageQueueHelper.push_msg(chat_id, msg, cursor)

    agent_chat(data, send_json_func, send_msg_func)


def es_process_data(data: dict):
    """
    es数据处理与存储,按照es自定义的数据进行格式化
    """
    mode = data.get("mode", "")
    # 区分于普通聊天和智能团聊天
    action = "dify_chat" if mode else "nomal_chat"
    request_data = {
        "username": data.get("username", ''),
        "conversation_id": data.get("conversation_id", ''),
        "action": action,
        "code": data.get("code", ""),
        "prompt": data.get("prompt", ""),
        "agent_name": data.get("agent_name", ""),
        "language": data.get("language"),
        "path": data.get("path", ""),
        "User-Agent": data.get("user_agent", ""),
        "host": data.get("host", ""),
        "response_content": data.get("total_context", ""),
        "total_tokens": data.get("total_tokens", 0),
        "created_at": data.get("created_at", ""),
        "finished_at": data.get("finished_at", ""),
        "ide": data.get("ide", ""),
        "ide_version": data.get('ide_version', ''),
        "ide_real_version": data.get('ide_real_version', ''),
        "request_mode": "websocket"
    }
    ide_es_service.insert_data(request_data)
