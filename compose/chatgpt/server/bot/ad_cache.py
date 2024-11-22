#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2023/3/27 11:47
"""

# 插入广告缓存

from common.constant import ConfigurationConstant, ADConstant
from services.system.configuration_service import ConfigurationService


class AdHelper:
    def __init__(self):
        self.ad = ConfigurationService.get_qianliu_ad()

    def _is_insert_ad(self, display_name, redis):
        # 是否在回答后面插入广告
        if self.ad.attribute_key == ConfigurationConstant.AD_ON:
            cache_key = self.get_cache_key(display_name)
            res = redis.setnx(cache_key, "true")
            # 一个月显示一次
            if res:
                redis.expire(cache_key, ADConstant.CACHE_TIMEOUT)
            return res
        else:
            return False

    def yield_ad(self, display_name, redis):
        if self.ad and self._is_insert_ad(display_name, redis):
            yield self.ad.attribute_value

    @staticmethod
    def get_cache_key(display_name):
        return ":".join([ADConstant.CACHE_PREFIX_KEY, str(display_name)])
