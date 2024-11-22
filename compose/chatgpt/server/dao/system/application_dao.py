#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dao.base_dao import BaseDao
from models.system.application import Application


class ApplicationDao(BaseDao):
    model = Application

    @classmethod
    def get_by_application_key(cls, application_key):
        return cls.get_or_none(application_key=application_key)
