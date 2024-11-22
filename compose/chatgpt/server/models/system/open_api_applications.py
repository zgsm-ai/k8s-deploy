#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/19 17:40
"""
from datetime import datetime

from peewee import CharField, DateTimeField

from common.constant import OpenAppConstant
from models.base_model import BaseModel


class OpenApiApplication(BaseModel):
    """开放API应用"""
    STATE_CHOICES = OpenAppConstant.STATE_CHOICES

    class Meta:
        table_name = 'open_api_application'

    applicant = CharField(default='', verbose_name='申请人')
    project_name = CharField(default='', verbose_name='应用名')
    app_id = CharField(default='', verbose_name='app_id')
    application_time = DateTimeField(default=datetime.now, verbose_name='申请时间')
    expiration_time = DateTimeField(null=True, verbose_name='到期时间')
    application_reason = CharField(default='', verbose_name='申请原因')
    expected_profit = CharField(default='', verbose_name='预期收益')
    app_link = CharField(default='', max_length=1000, verbose_name='应用案例')
    state = CharField(default=OpenAppConstant.APPROVAL, choices=STATE_CHOICES, verbose_name='状态')
    approve_remark = CharField(default='', verbose_name='审批备注', help_text='如拒绝审批、禁用该应用，请填写审批备注（前端展示）')

    def __str__(self):
        return self.project_name

    def dict(self, *args, **kwargs):
        data = super().dict()
        # approve_remark:在前端鼠标悬停状态上展示
        if self.state_is_approval:
            data['app_id'] = '审批通过后获取'  # 设置app_id，为前端展示使用
            data['approve_remark'] = '已收到申请通知，预计3个工作日内处理完毕，请耐心等待'
        elif self.state_is_fail:
            data['app_id'] = '因审批未通过，无法获取APPID'
        elif self.state_is_expired:
            data['approve_remark'] = '超过使用期限，可联系千流客服续期或者重新提交API申请'
            data['state'] = self.state
        data['application_time'] = self.date_format(data['application_time'])
        data['expiration_time'] = self.date_format(data['expiration_time'])
        return data

    @classmethod
    def date_format(cls, _date):
        # 返回：Y-m-d
        if isinstance(_date, str):
            return datetime.strptime(_date, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        elif isinstance(_date, datetime):
            return _date.strftime("%Y-%m-%d")
        else:
            return _date

    @property
    def state_is_approval(self):  # 是否审核中
        return True if self.state == OpenAppConstant.APPROVAL else False

    @property
    def state_is_approved(self):  # 是否审核通过
        return True if self.state == OpenAppConstant.APPROVED else False

    @property
    def state_is_fail(self):  # 是否审核不通过
        return True if self.state == OpenAppConstant.FAIL else False

    @property
    def state_is_disable(self):  # 是否被禁用
        return True if self.state == OpenAppConstant.DISABLE else False

    @property
    def state_is_expired(self):  # 是否已超期
        if self.state == OpenAppConstant.EXPIRED:
            return True
        # 如果审批通过且时间超期，更新状态为已超期
        elif self.state == OpenAppConstant.APPROVED and self.expiration_time and self.expiration_time < datetime.now():
            self.state = OpenAppConstant.EXPIRED
            self.save()
            return True
        else:
            return False
