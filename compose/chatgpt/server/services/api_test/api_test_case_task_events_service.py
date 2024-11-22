#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/5/18 15:46
ApiTestCaseTaskEvents 是 api test case任务中最底层的实体，用来记录任务事件的状态，以及任务事件的执行结果，不要调用其他的service
@File    ：api_test_case_task_events_service.py
@Software: PyCharm
"""
import logging

from common.constant import ApiTestCaseConstant
from dao.system.api_test_case_dao import ApiTestCaseTaskEventsDao
from services.base_service import BaseService
from third_platform.eolinker.api_studio_manager import ApiStudioHelper, ApiStudioManager

logger = logging.getLogger(__name__)


class ApiTestCaseTaskEventsService(BaseService):
    """
    API测试用例事件相关服务
    """
    dao = ApiTestCaseTaskEventsDao

    @classmethod
    def change_status_by_task_id(cls, task_id, status, **kwargs):
        """
        根据任务ID修改任务状态
        :param task_id: 任务ID
        :param status: 任务状态
        :return:
        """
        query, total = ApiTestCaseTaskEventsService.list(
            api_test_case_task_id=task_id,
            include_fields=["id"],
            status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED
        )
        if status == ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.REVOKED:
            func = cls.event_to_revoked
        elif status == ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.FAILURE:
            func = cls.event_to_fail
        else:
            func = cls.event_to_done
        for event in query:
            func(event.id, **kwargs)

    @classmethod
    def event_to_done(cls, event_id, **kwargs):
        """
        事件转完成
        :param event_id: 事件ID
        :return:
        """
        # 更新事件状态
        cls.update_by_id_json(event_id, status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.SUCCESS, **kwargs)

    @classmethod
    def event_to_fail(cls, event_id, **kwargs):
        """
        事件转失败
        :param event_id: 事件ID
        :return:
        """
        # 更新事件状态
        cls.update_by_id_json(event_id, status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.FAILURE, **kwargs)

    @classmethod
    def event_to_revoked(cls, event_id, **kwargs):
        """
        事件转中止
        :param event_id: 事件ID
        :return:
        """
        # 更新事件状态
        cls.update_by_id_json(event_id, status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.REVOKED, **kwargs)

    @classmethod
    def update_by_id_json(cls, mid, **kwargs):
        logging.info(f"更新{cls.dao.model.__name__},id:{mid},kwargs:{kwargs}")
        # 更新前， 检查是否存在该资源
        _obj = cls.get_by_id(mid)
        if "data" in kwargs:
            data = kwargs.pop("data")
            old_data = _obj.data
            old_data.update(data)
            kwargs["data"] = old_data

        cls.dao.update_by_id(mid, **kwargs)
        result = cls.get_by_id(mid)
        try:
            # 待优化，不应该在更新的时候去调API去清理
            cls.clean_abnormal_test_case(result)
        except Exception as e:
            logger.error(f"清理异常用例失败，event_id: {result.id}, error: {e}")
        return result

    @classmethod
    def clean_abnormal_test_case(cls, event):
        """
        清理异常用例
        :param event: 事件
        :return:
        """
        if event and event.status in ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.ABNORMAL_STATUS \
                and event.event_type == ApiTestCaseConstant.ApiTestCaseTaskEventsType.CREATE_TEST_CASE:
            # 创建用例任务异常需要清理测试用例，避免出现异常用例
            req_data = event.data.get("detail_events", [{}])[0].get("req_data", {})
            if req_data.get("case_id"):
                logging.warning(f"清理测试用例，case_id: {req_data.get('case_id')}")
                delete_test_case_data = {
                    "space_id": req_data.get("space_id"),
                    "project_id": req_data.get("project_id"),
                    "data": {
                        "case_id": [req_data.get("case_id")],
                    },
                    "module": 0
                }
                api_key = ApiStudioHelper.get_space_api_key(req_data.get("space_id"), event.data.get("authorization"),
                                                            event.data.get("origin"))
                ApiStudioManager.delete_test_case(delete_test_case_data, origin=event.data.get("origin"),
                                                  api_key=api_key)
