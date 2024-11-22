#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from peewee import CharField, IntegerField

from common.constant import ApiTestCaseConstant
from db.custom_field import JSONField
from models.base_model import BaseModel

logger = logging.getLogger(__name__)


class ApiTestCaseTask(BaseModel):
    """api测试用例任务表"""
    choices = ApiTestCaseConstant.ApiTestCaseTaskStatus.CHOICES

    class Meta:
        table_name = 'api_test_case_task'

    display_name = CharField(index=True, verbose_name='用户')
    status = CharField(verbose_name='任务状态', choices=choices)
    test_case_stage = CharField(default=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST,
                                verbose_name='测试用例类型，区分API管理页面和API自动化测试页面用例')
    req_data = JSONField(default={}, verbose_name='请求参数')
    remark = CharField(default="", verbose_name='备注')
    celery_task_id = CharField(default="", verbose_name='celery任务id')

    def status_display(self):
        """获取状态码对应的文字描述"""
        return dict(self.choices).get(self.status, self.status)

    def to_dict_with_status_display(self, **kwargs):
        """将模型实例转换为字典，并包含状态码转换为文字的逻辑"""
        model_dict = super().dict(self, **kwargs)
        model_dict['status_display'] = self.status_display()
        return model_dict

    def get_req_data(self):
        return self.req_data

    @property
    def is_final_status(self):
        return self.status in ApiTestCaseConstant.ApiTestCaseTaskStatus.FINAL_STATUS


class ApiTestEolinkerCaseTask(BaseModel):
    """api测试 eolinker 用例创建任务"""
    choices = ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.CHOICES

    class Meta:
        table_name = 'api_test_eolinker_case_task'

    display_name = CharField(index=True, verbose_name='用户')
    status = CharField(verbose_name='任务状态', choices=choices)
    req_data = JSONField(default={}, verbose_name='请求参数')
    remark = CharField(default="", verbose_name='备注')
    celery_task_id = CharField(default="", verbose_name='celery任务id')
    api_test_case_task_id = IntegerField(index=True, null=True, verbose_name='主记录id')

    def status_display(self):
        """获取状态码对应的文字描述"""
        return dict(self.choices).get(self.status, self.status)

    def to_dict_with_status_display(self, **kwargs):
        """将模型实例转换为字典，并包含状态码转换为文字的逻辑"""
        model_dict = super().dict(self, **kwargs)
        model_dict['status_display'] = self.status_display()
        return model_dict

    @property
    def is_final_status(self):
        return self.status in ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.FINAL_STATUS


class ApiTestCaseTaskEvents(BaseModel):
    """api测试用例任务事件表"""
    ApiTestCaseTaskEventsTypeChoices = ApiTestCaseConstant.ApiTestCaseTaskEventsType.CHOICES
    ApiTestCaseTaskEventsStatusChoices = ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.CHOICES

    class Meta:
        table_name = 'api_test_case_task_events'

    # ApiTestCaseTask的id
    api_test_case_task_id = IntegerField(index=True, null=True, verbose_name='主记录id')
    # ApiTestEolinkerCaseTask的id
    gen_eoliner_task_id = IntegerField(index=True, null=True, verbose_name='子记录id')
    event_type = CharField(verbose_name='事件类型', choices=ApiTestCaseTaskEventsTypeChoices)
    status = CharField(verbose_name='事件状态', choices=ApiTestCaseTaskEventsStatusChoices)
    remark = CharField(default="", verbose_name='备注')
    data = JSONField(default={}, verbose_name='相关参数')

    def status_display(self):
        """获取状态码对应的文字描述"""
        return dict(self.ApiTestCaseTaskEventsStatusChoices).get(self.status, self.status)

    def event_type_display(self):
        """获取事件码对应的文字描述"""
        return dict(self.ApiTestCaseTaskEventsTypeChoices).get(self.event_type, self.event_type)

    def to_dict_with_status_display(self, **kwargs):
        """将模型实例转换为字典，并包含状态码转换为文字的逻辑"""
        model_dict = super().dict(self, **kwargs)
        model_dict['status_display'] = self.status_display()
        model_dict['event_type_display'] = self.event_type_display()
        return model_dict

    @property
    def is_final_status(self):
        return self.status in ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.FINAL_STATUS
