#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@Author  : 范立伟33139
@Date    : 2024/7/26 10:45
"""
import json

from typing import Any, Union
from time import time
from functools import wraps


# 装饰器把函数返回的dict dump转换成chunk
def dump_chunk(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return f"{json.dumps(func(*args, **kwargs))}\n\n"

    return wrapper


class ChunkHelper:
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_FINISHED = "workflow_finished"
    WORKFLOW_FAIL = "workflow_fail"
    NODE_STARED = "node_started"
    MESSAGE = "text_chunk"
    NODE_FINISHED = "node_finished"
    NODE_FAIL = "node_fail"
    NODE_DIFF_CHUNK = "node_diff_chunk"
    DIFY_ERROR = "dify_error"

    @classmethod
    @dump_chunk
    def workflow_started_chunk(cls, agent_name: str, agent_id: str, data: Any):
        return dict(
            agent_name=agent_name,
            agent_id=agent_id,
            event=cls.WORKFLOW_STARTED,
            data=data,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def workflow_finished_chunk(cls, agent_name: str, agent_id: str, data: Any):
        return dict(
            agent_name=agent_name,
            agent_id=agent_id,
            event=cls.WORKFLOW_FINISHED,
            data=data,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def workflow_fail_chunk(cls, agent_name: str, agent_id: str, data: Any):
        return dict(
            agent_name=agent_name,
            agent_id=agent_id,
            event=cls.WORKFLOW_FAIL,
            data=data,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def node_started_chunk(cls, node_name: str, node_id: str, node_type: str, data: Any):
        return dict(
            node_name=node_name,
            node_id=node_id,
            node_type=node_type,
            event=cls.NODE_STARED,
            data={
                "title": data
            },
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def node_finished_chunk(cls, node_name: str, node_id: str, node_type: str, data: Any):
        return dict(
            node_name=node_name,
            node_id=node_id,
            node_type=node_type,
            event=cls.NODE_FINISHED,
            data=data,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def node_fail_chunk(cls, node_name: str, node_id: str, node_type: str, data: Any):
        return dict(
            node_name=node_name,
            node_id=node_id,
            node_type=node_type,
            event=cls.NODE_FAIL,
            data=data,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def message_chunk(cls, node_name: str, node_id: str, node_type: str, task_id: Union[int, str], data: Any):
        return dict(
            node_name=node_name,
            node_id=node_id,
            node_type=node_type,
            event=cls.MESSAGE,
            data={
                "text": data
            },
            task_id=task_id,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def node_diff_chunk(
            cls,
            node_name: str,
            node_id: str,
            node_type: str,
            data: Any,
            language: str,
            title: str
    ):
        return dict(
            node_name=node_name,
            node_id=node_id,
            node_type=node_type,
            event=cls.NODE_DIFF_CHUNK,
            data={
                "text": data
            },
            language=language,
            title=title,
            created_at=int(time())
        )

    @classmethod
    @dump_chunk
    def dify_error(cls, data: str):
        return dict(
            event=cls.DIFY_ERROR,
            message=data,
            created_at=int(time())
        )
