#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
from queue import Queue
from typing import Optional

import requests

from common.utils.sensitive_util import sensitization_process, desensitization_process
from third_platform.dify import DifyConfig

logger = logging.getLogger(__name__)


class DifyHelper:
    typo = "default"
    user = DifyConfig.user

    @classmethod
    def make_url(cls, base_url: str) -> str:
        return ""

    @classmethod
    def make_data(cls, data: dict) -> dict:
        return data

    @classmethod
    def make_headers(cls, api_key: str) -> dict:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    @classmethod
    def make_request(cls, base_url: str, api_key: str, data: dict):
        url = cls.make_url(base_url)
        data = cls.make_data(data)
        headers = cls.make_headers(api_key)
        is_stream = data.get("response_mode", "blocking") == "streaming"
        if is_stream:
            return cls._make_request_streaming(url, data, headers)
        else:
            return cls._make_request_blocking(url, data, headers)

    @classmethod
    def _make_request_blocking(cls, url, data, headers):
        res = requests.post(url=url, json=data, headers=headers)
        if res.status_code != 200:
            logger.error(f'review request error: status code: {res.status_code} {res.text}')
            return False
        else:
            handle_resp = cls.handle_blocking_result(res.json())
            return cls.process_desensitization_data(handle_resp)

    @classmethod
    def get_chunk_content(cls, data: dict):
        return None

    @classmethod
    def replace_chunk_content(cls, data: dict, content: str):
        return None

    @classmethod
    def check_and_replace(cls, q):
        """
        队列中脱敏操作  目标词->敏感词
        """
        answers = ''.join([cls.get_chunk_content(item) for item in list(q.queue)])
        answers_desensitization = desensitization_process(answers)
        if answers != answers_desensitization:
            # 取 q 的第一个元素
            data = q.get()
            # 若 q 还有内容，则全清空
            while not q.empty():
                q.get()
            # 将转换后的完整文本塞回取到的第一个元素内，重新构造一个 obj 出去
            return cls.replace_chunk_content(data, answers_desensitization)
        elif q.qsize() > 3:
            return q.get()
        return None

    @classmethod
    def _make_request_streaming(cls, url, data, headers):
        data["inputs"] = cls.process_sensitization_data(data["inputs"])
        res = requests.post(url=url, json=data, headers=headers, stream=True)

        # 创建流式缓冲区
        q = Queue()

        # 一个用于暂存过程内容的变量，针对 stream 模式下的逐步输出过程做内容拼接
        temp_content = None
        total_tokens = None
        for line in res.iter_lines():
            if line:
                if not line.startswith(b"data: "):
                    error_message = line.decode("utf-8")
                    if error_message.startswith("event: "):  # event: ping
                        continue
                    yield error_message, None
                else:
                    json_data = line.split(b": ", 1)[1]
                    try:
                        obj = json.loads(json_data)
                        temp_content, obj, total_tokens = cls.handle_chunk(obj, temp_content)
                        if total_tokens:
                            yield {"event": "sf_tokens", "total_tokens": total_tokens}, None
                            # 对于最后结果，需要判断是否有accept_action，如果有，则需要返回前端；场景有：代码补全
                            if "accept_action" in temp_content:
                                yield None, temp_content
                        if not cls.get_chunk_content(obj):
                            while not q.empty():
                                yield q.get(), None
                            yield cls.process_desensitization_data(obj), None
                        else:
                            q.put(obj)
                            obj = cls.check_and_replace(q)
                            if obj:
                                yield obj, None
                    except json.decoder.JSONDecodeError:
                        yield cls.process_desensitization_data(json_data.decode("utf-8")), None
        yield {"event": "sf_tokens", "total_answer": temp_content}, None
        yield None, temp_content

    @classmethod
    def handle_chunk(cls, chunk_json: dict, last_temp_content: any) -> (Optional[str], dict, int):
        return None, chunk_json, 0

    @classmethod
    def handle_blocking_result(cls, blocking_result: dict):
        return None

    @classmethod
    def process_sensitization_data(cls, data):
        """
        敏化处理
        data: 需要敏化数据
        """

        if isinstance(data, str):
            data = sensitization_process(data)
        elif isinstance(data, dict):
            for k, v in data.items():
                data[k] = cls.process_sensitization_data(v)
        return data

    @classmethod
    def process_desensitization_data(cls, data):
        """
        脱敏处理
        data: 需要脱敏数据
        """

        if isinstance(data, str):
            data = desensitization_process(data)
        elif isinstance(data, dict):
            for k, v in data.items():
                data[k] = cls.process_desensitization_data(v)
        return data

    @classmethod
    def give_likes_dify(cls, data, message_id, dify_url, dify_key):
        """
        请求dify日志平台，进行点赞
        data:点赞数据
        dify_url:请求url
        dify_key:agent_key
        """

        base_url = f"{dify_url}v1/messages/{message_id}/feedbacks"
        request_header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {dify_key}"
        }
        try:
            # 对dify平台进行请求
            res = requests.post(url=base_url, json=data, headers=request_header)
            if res.status_code != 200:
                logger.error(f'review request error: status code: {res.status_code} {res.text}')
                return False
            else:
                return True
        except requests.RequestException as e:
            logger.error(f'review request error: {e}')
            return False


class DifyWorkflowHelper(DifyHelper):
    typo = "workflow"

    @classmethod
    def make_url(cls, base_url: str) -> str:
        return base_url + "/v1/workflows/run"

    @classmethod
    def make_data(cls, data: dict) -> dict:
        result_data = dict()
        stream = data.get("stream", False)
        if stream:
            result_data["response_mode"] = "streaming"
        else:
            result_data["response_mode"] = "blocking"
        result_data["user"] = data.get("user", None) or cls.user
        result_data["inputs"] = data
        return result_data

    @classmethod
    def handle_chunk(cls, chunk_json: dict, last_temp_content: any) -> (Optional[str], dict, int):
        data = None
        tokens = 0
        if isinstance(chunk_json, dict) and chunk_json.get("event") == "workflow_finished":
            data = chunk_json.get("data", {}).get("outputs", {})
            tokens = chunk_json.get("data", {}).get("total_tokens", 0)
            # 如果没有data的话，可能是dify报错，此时要记录下错误
            # 示例：{'outputs': None, 'error': "Node 给IDE返回'替换'标记 run failed: Output qianliu is missing."}
            if data is None:
                error = chunk_json.get("data", {}).get("error", "")
                logger.error(f"在处理chunk 流中，output返回None，怀疑异常，捕获如下：{error}")
            # IMPORTANT: 用工作流模式的 dify 应用，最终输出必需带有 result 或者 text 字段作为 ai 答复的文本结果
            elif data.get("result"):
                data = data.get("result")
            elif data.get("text"):
                data = data.get("text")
            else:
                # 如果都data中都非预期，则直接转成str，统一处理
                logger.error(f"在处理chunk 流中，output返回的数据结构非预期，不包含 result 或者 text 字段，转成str: {data}")
                data = str(data)
        elif last_temp_content:
            data = last_temp_content
        return data, chunk_json, tokens

    @classmethod
    def handle_blocking_result(cls, blocking_result: dict):
        return blocking_result.get("data", {}).get("outputs", {})

    @classmethod
    def get_chunk_content(cls, data: dict) -> str:
        return data.get("data", {}).get("text")

    @classmethod
    def replace_chunk_content(cls, data: dict, content: str):
        data["data"]["text"] = content
        return data


class DifyChatBotHelper(DifyHelper):
    typo = "chat-bot"

    @classmethod
    def make_url(cls, base_url: str) -> str:
        return base_url + "/v1/chat-messages"

    @classmethod
    def make_data(cls, data: dict) -> dict:
        result_data = dict()
        stream = data.get("stream")
        query = data.get("query")
        conversation_id = data.get("conv_id")
        if stream:
            result_data["response_mode"] = "streaming"
        else:
            result_data["response_mode"] = "blocking"
        result_data["user"] = data.get("user", None) or cls.user
        result_data["inputs"] = data
        result_data["query"] = query
        result_data["conversation_id"] = conversation_id or ""
        return result_data

    @classmethod
    def handle_chunk(cls, chunk_json: dict, last_temp_content: any) -> (Optional[str], dict, int):
        if isinstance(chunk_json, dict) and (chunk_json.get("event") == "message_end"):
            return last_temp_content, chunk_json, chunk_json.get("metadata", {}).get("usage", {}).get("total_tokens", 0)
        if isinstance(chunk_json, dict) and (chunk_json.get("event") in ["message", "agent_message"]):
            if not last_temp_content:
                last_temp_content = ""
            last_temp_content += chunk_json.get("answer", "")
        return last_temp_content, chunk_json, 0

    @classmethod
    def handle_blocking_result(cls, blocking_result: dict):
        return blocking_result.get("answer")

    @classmethod
    def get_chunk_content(cls, data: dict) -> str:
        return data.get("answer")

    @classmethod
    def replace_chunk_content(cls, data: dict, content: str):
        data["answer"] = content
        return data


class DifyManager(DifyConfig):
    """
    底座平台应用调用
    """

    @classmethod
    def get_helper_by_typo(cls, typo) -> DifyHelper:
        if typo == "workflow":
            return DifyWorkflowHelper
        else:
            return DifyChatBotHelper

    @classmethod
    def planning_step(cls, data: dict):
        """
        规划agent处理,根据用户提问的进行步骤拆解
        """
        helper = cls.get_helper_by_typo(cls.PLANNING_APPLICATION_TYPE)
        return helper.make_request(cls.base_url, cls.PLANNING_APPLICATION_KEY, data)

    @classmethod
    def do_app(cls, typo, key, data, url=None):
        helper = cls.get_helper_by_typo(typo)
        return helper.make_request(url or cls.base_url, key, data)

    @classmethod
    def give_likes_app(cls, typo, data, message_id, dify_url, dify_key):
        help = cls.get_helper_by_typo(typo)
        return help.give_likes_dify(data, message_id, dify_url, dify_key)
