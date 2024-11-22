#!/usr/bin/env python
# -*- coding: utf-8 -*-


from dao.system.application_dao import ApplicationDao
from services.base_service import BaseService


class ApplicationService(BaseService):
    dao = ApplicationDao
