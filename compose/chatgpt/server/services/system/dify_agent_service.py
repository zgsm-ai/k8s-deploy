#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dao.system.dify_agent_dao import DifyAgentDao
from services.base_service import BaseService
from common.constant import DifyAgentConstant


class DifyAgentService(BaseService):
    dao = DifyAgentDao

    def get_observer_agent(self):
        return self.dao.get_or_none(role=DifyAgentConstant.ROLE_OBSERVER)

    def get_group_members(self):
        result, _ = self.dao.list(role=DifyAgentConstant.ROLE_GROUP_MEMBER)
        return result

    def get_group_guardian(self):
        """获取守卫者，当选不到角色的时候，用守卫者兜底"""
        return self.dao.get_or_none(role=DifyAgentConstant.ROLE_GROUP_GUARDIAN)

    def get_normal_chat_agent(self):
        return self.dao.get_or_none(role=DifyAgentConstant.ROLE_NORMAL_CHAT)

    def get_agent_type_key(self, action):
        """
        获取agent对应的name,type,key
        """
        return self.dao.get_or_none(role=action)

    def get_agent_name_key(self, name):
        """
        根据agent的display_name获取对应agent的key
        """
        return self.dao.get_or_none(display_name=name)
