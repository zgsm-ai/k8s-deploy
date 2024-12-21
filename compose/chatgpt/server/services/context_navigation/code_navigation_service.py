import json
import logging
import uuid

from common.constant import ContextNavigationConstant
from lib.cache import BaseCache
from services.agents.dify_chat_async import DifyMessageQueueHelper, DifySpecifiedContextHelper
from services.base_service import BaseService


logger = logging.getLogger(__name__)


class CodeNavigationService(BaseService):
    @classmethod
    def cache_context(cls, data) -> str:
        """
        将对话的上下文提前将数据缓存至Redis
        redis key有前缀
        args:
            data: 需要缓存的数据
        return:
            存储数据的Redis键
        """
        context_uuid = str(uuid.uuid4())
        # 存储key携带前缀
        redis_key = ContextNavigationConstant.code_navigation_context_redis_key.format(uuid=context_uuid)
        cls.cache(redis_key, data)
        return redis_key

    @classmethod
    def cache_specified_context_content(cls, data, chat_id: str) -> str:
        """
        将dify指定的上下文提前将数据缓存至Redis
        redis key有前缀
        args:
            data: 需要缓存的数据
            chat_id: 本次会话id
        return:
            存储数据的Redis键
        """
        # 这里采用列表的方式放入内容，方便提取的时候阻塞提取
        DifySpecifiedContextHelper.push_json_data(chat_id, data)
        return chat_id

    @classmethod
    def specified_context_request(cls, data, chat_id: str):
        """
        过程中的上下文请求通过对话发给sdk
        args:
            data: 需要缓存的数据
            chat_id: 缓存key的uuid
        return:
            返回用于缓存数据的redis_key
        """
        # 1.和正常对话复用同一个key，因为会在聊天中推往前端
        data["event"] = "get_specified_context"
        DifyMessageQueueHelper.push_json_data(chat_id, data)

    @classmethod
    def _file_path_output(cls, data):
        """
        通过文件路径生成输出内容
        args:
            data: 包含文件路径和操作类型的数据字典
        return:
            返回格式化的输出字符串
        """
        file_paths = data.get("file_paths", "")
        if isinstance(file_paths, str):
            try:
                file_paths = json.loads(file_paths)
            except json.JSONDecodeError:
                logger.info(f"json解析file_symblos报错，{file_paths}")
                file_paths = list()
        content = "内容" if data["action"] == ContextNavigationConstant.get_file_content_action else "签名"
        # 2.需要在步骤里渲染出正在读取什么文件，
        output = f" ```text \n 正在读取文件{content}： \n {file_paths} \n``` \n "
        return output

    @classmethod
    def _file_symbols_output(cls, data: dict):
        """
        根据传入的数据生成文件符号的文本输出
        args:
            data: 包含文件符号信息的字典
        return:
            格式化后的文本输出内容
        """
        file_symbols = data.get("file_symbols", "")
        if isinstance(file_symbols, str):
            try:
                file_symbols = json.loads(file_symbols)
            except json.JSONDecodeError:
                logger.info(f"json解析file_symblos报错，{file_symbols}")
                file_symbols = list()
        output = " ```text \n 正在读取文件: "
        for each in file_symbols:
            if isinstance(each, dict):
                file_path = each.get("file_path")
                specified_func_names = each.get("func_names")
                output += f"\n {file_path} \n 函数内容: {specified_func_names}"
        output += " \n``` \n "
        return output

    @classmethod
    def cache(cls, redis_key, data, ex=ContextNavigationConstant.cnc_redis_ex_time) -> str:
        """
        定义类方法cache，用于将数据缓存到Redis中
        args:
            redis_key: Redis缓存键
            data: 缓存的数据
            ex: 缓存过期时间，默认为ContextNavigationConstant.cnc_redis_ex_time
        return:
            返回用于缓存数据的redis_key
        """
        cache = BaseCache()
        cache.set(redis_key, data, ex=ex)
        return redis_key

    @classmethod
    def validate_fields(cls, fields):
        """校验创建数据参数，去除冗余参数"""
        rules = [
            {'label': 'conversation_id', 'type': str, 'optional': True, 'name': '上下文id'},
        ]
        return cls._validate(fields, rules)

    @classmethod
    def get_cache_data(cls, redis_key):
        """
        定义类方法get_cache_data, 用于获取及删除特定redis缓存数据
        args:
            redis_key: 要获取和删除的redis缓存键
        return:
            返回缓存中对应键的数据，如果不存在则返回None
        """
        data = None
        if redis_key:
            cache = BaseCache()
            data = cache.get(redis_key)
            logger.info(f"获取到的redis_key： {redis_key}, data长度: {len(str(data))}")
            if data:
                cache.delete(redis_key)
        return data

    @classmethod
    def get_specified_context_content(cls, chat_id: str):
        """阻塞获取上下文"""
        return DifySpecifiedContextHelper.blpop_data(chat_id)
