#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/6/3 11:05
"""

from common.constant import ConfigurationConstant
from template import DEFAULT_TEMPLATE_MAP
from services.action.api_test_case_service import ApiTestCaseStrategy, ApiTestSingleCaseStrategy, \
    ApiTestGenStepStrategy, ApiTestCaseModifyStrategy, ApiTestCaseRepeatVerifiedStrategy, \
    ApiTestPointDocInspectorStrategy, ApiTestGenODGStrategy
from services.action.generate_api_test_point import GenerateApiTestPointStrategy
from services.action.generate_api_test_set import GenerateApiTestSetStrategy
from services.action import strategy_map
from services.system.configuration_service import ConfigurationService


class ApiTestConfigurationHandler:

    @classmethod
    def run(cls):
        cls.add_or_update()

    @classmethod
    def add_or_update(cls):
        api_test_strategy_set = (
            ApiTestCaseStrategy,
            ApiTestSingleCaseStrategy,
            ApiTestGenStepStrategy,
            ApiTestCaseModifyStrategy,
            ApiTestCaseRepeatVerifiedStrategy,
            ApiTestPointDocInspectorStrategy,
            ApiTestGenODGStrategy,
            GenerateApiTestPointStrategy,
            GenerateApiTestSetStrategy
        )
        for strategy in api_test_strategy_set:
            cls.add_or_update_strategy_template(strategy)

    @classmethod
    def add_or_update_strategy_template(cls, strategy):
        # 获取默认模板
        template_value = DEFAULT_TEMPLATE_MAP.get(strategy.name, None)
        # 固定模板belong_type
        belong_type = ConfigurationConstant.PROMPT_TEMPLATE
        # 策略描述
        desc = strategy.desc
        # 确定数据库是否存在
        template_config = ConfigurationService.dao.get_or_none(belong_type=belong_type,
                                                               attribute_key=strategy.name)
        if template_config:
            # 数据库存在，则更新成和代码中的一致
            # 该处有风险，如果线上单独更新过，会导致线上的丢失，建议线上更新完后，代码中也得更新，保持一致。
            ConfigurationService.update_by_id(template_config.id, attribute_value=template_value, desc=desc)
            print(f"[{desc}]{strategy.name}： 更新成功")
        else:
            # 数据库不存在则创建
            ConfigurationService.create(belong_type=belong_type, attribute_key=strategy.name,
                                        attribute_value=template_value, desc=desc)
            print(f"[{desc}]{strategy.name}： 添加成功")
        # 清除缓存
        ConfigurationService.clear_cache(belong_type, strategy.name)

    @classmethod
    def clear_all_action_strategy_prompt_template_cache(cls):
        for action_name in strategy_map:
            ConfigurationService.clear_cache(ConfigurationConstant.PROMPT_TEMPLATE, action_name)
