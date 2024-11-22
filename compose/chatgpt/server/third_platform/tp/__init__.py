#!/usr/bin/python
# -*- coding:utf-8 -*-
# @author  : 王政
# @time    : 2024/9/10 17:29
# @desc:
from third_platform.base_manager import BaseManager
from config import CONFIG


class TpConfig(BaseManager):
    base_url = CONFIG.app.TP.base_url
    token = CONFIG.app.TP.token
    headers = {'token': token, 'Content-Type': 'application/json', "Accept": "application/json"}
