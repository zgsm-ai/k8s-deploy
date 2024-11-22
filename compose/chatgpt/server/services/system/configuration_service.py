#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/4/20 10:56
"""
import json
import logging
from json import JSONDecodeError

from common.constant import ConfigurationConstant, PromptConstant, ADConstant, AIReviewConstant, DifyAgentConstant
from dao.system.configuration_dao import ConfigurationDao
from lib.cache.cache_anno import cache_able, cache_evict, cache_all_evict
from services.base_service import BaseService
from template import DEFAULT_TEMPLATE_MAP
from template.generate_api_test import DEFAULT_PYTEST_CASE_TEMPLATE, DEFAULT_API_TEST_RANGE

logger = logging.getLogger(__name__)


class ConfigurationService(BaseService):
    dao = ConfigurationDao
    CACHE_KEY_PREFIX = ConfigurationConstant.CACHE_KEY_PREFIX
    CACHE_KEY_FORBID_WORD = PromptConstant.CACHE_KEY_FORBID_WORD
    CACHE_KEY_QIANLIU_AD = ADConstant.CACHE_KEY_QIANLIU_AD
    CACHE_KEY_LANGUAGE_MAP = ConfigurationConstant.CACHE_KEY_LANGUAGE_MAP
    CACHE_KEY_MAX_REVIEW_NUM = ConfigurationConstant.CACHE_KEY_MAX_REVIEW_NUM
    CACHE_KEY_ZHUGE_ADS = DifyAgentConstant.CACHE_KEY_ZHUGE_ADS

    @classmethod
    def get_editor_limit_version(cls):
        kwargs = {
            'belong_type': ConfigurationConstant.EDITOR_LIMIT_TYPE,
            'is_need_total': False,
        }
        query, _ = cls.dao.list(**kwargs)
        return {ide.attribute_key: ide.attribute_value for ide in query}

    @classmethod
    def get_list(cls, **kwargs):
        attribute_key = kwargs.get('attribute_key')
        total = 1
        if attribute_key == ConfigurationConstant.LANGUAGE_KEY_MAP:
            data_list = cls.get_language_map(kwargs)
        # 划词组件库
        elif attribute_key == ConfigurationConstant.CACHE_KEY_SCRIBE_COMPONENTS:
            data_list = cls.get_scribe_component_options()
            total = len(data_list)
        else:
            query, total = cls.dao.list(**kwargs)
            data_list = [data.dict() for data in query]

            for item in data_list:
                try:
                    # 若是json字符串，则进行反序列化
                    item['attribute_value'] = json.loads(item['attribute_value'])
                except JSONDecodeError:
                    pass

        return data_list, total

    @classmethod
    def get_configuration(cls, belong_type, attribute_key, default=None):
        """通用查询"""
        kwargs = {
            'belong_type': belong_type,
            'attribute_key': attribute_key,
            'is_need_total': False,  # 节省一次统计查询
        }
        query, _ = cls.dao.list(**kwargs)
        return query[0].attribute_value if query and len(query) > 0 else default

    @classmethod
    @cache_able(CACHE_KEY_PREFIX, index=[1, 2])
    def get_configuration_with_cache(cls, belong_type, attribute_key, default=None):
        """通用查询缓存"""
        res = cls.get_configuration(belong_type, attribute_key, default)
        return res

    @classmethod
    @cache_evict(CACHE_KEY_PREFIX, index=[1, 2])
    def clear_cache(cls, belong_type, attribute_key):
        """通用清理缓存"""
        logging.info(f"clear_cache {cls.CACHE_KEY_PREFIX}:{belong_type}:{attribute_key}")

    @classmethod
    def get_prompt_template(cls, attribute_key):
        """查询prompt模板，有缓存"""
        default = DEFAULT_TEMPLATE_MAP.get(attribute_key, '')
        prompt = cls.get_configuration_with_cache(ConfigurationConstant.PROMPT_TEMPLATE, attribute_key, default)
        return prompt

    @classmethod
    def get_api_test_range(cls, attribute_key):
        """根据业务线查询api测试范围模板，有缓存"""
        prompt = cls.get_configuration_with_cache(ConfigurationConstant.API_TEST_RANGE, attribute_key,
                                                  DEFAULT_API_TEST_RANGE)
        return prompt

    @classmethod
    def get_pytest_case_template(cls, attribute_key):
        """根据业务线查询pytest测试用例模板，有缓存"""
        pytest_case_template = cls.get_configuration_with_cache(ConfigurationConstant.PYTEST_CASE_TEMPLATE,
                                                                attribute_key, DEFAULT_PYTEST_CASE_TEMPLATE)
        return pytest_case_template

    @classmethod
    def get_prompt_forbidden_word(cls):
        return cls.get_configuration_with_cache(ConfigurationConstant.PROMPT_TYPE,
                                                ConfigurationConstant.PROMPT_KEY_FORBID_STRING,
                                                None)

    @classmethod
    @cache_evict(CACHE_KEY_FORBID_WORD)
    def evict_cache(cls):
        logger.info('清理禁用敏感词缓存')
        return

    @classmethod
    @cache_able(CACHE_KEY_ZHUGE_ADS)
    def get_zhuge_ads(cls):
        data = cls.dao.get_or_none(belong_type=ConfigurationConstant.ZHUGE_ADS_TYPE)
        if data:
            return json.loads(data.attribute_value)
        else:
            return []

    @classmethod
    @cache_evict(CACHE_KEY_ZHUGE_ADS)
    def evict_zhuge_ads_cache(cls):
        logger.info('清理千流诸葛广告配置缓存')
        return

    @classmethod
    @cache_able(CACHE_KEY_QIANLIU_AD)
    def get_qianliu_ad(cls):
        data = cls.dao.get_or_none(belong_type=ConfigurationConstant.QIANLIU_AD_TYPE)
        return data

    @classmethod
    @cache_evict(CACHE_KEY_QIANLIU_AD)  # 清除广告配置缓存
    def evict_ad_cache(cls):
        logger.info('清理广告配置缓存')
        return

    @classmethod
    @cache_all_evict(ADConstant.CACHE_PREFIX_KEY)
    def evict_user_ad_cache(cls):
        logger.info('清理用户广告记录缓存')
        return

    @classmethod
    def get_plugin_user(cls):
        data = cls.dao.get_or_none(belong_type='plugin', attribute_key='users')
        return data

    @classmethod
    @cache_able(CACHE_KEY_LANGUAGE_MAP)
    def get_language_map(cls, kwargs):
        data = cls.dao.get_or_none(**kwargs)
        if data:
            return json.loads(data.attribute_value)
        else:
            return []

    @classmethod
    @cache_all_evict(CACHE_KEY_LANGUAGE_MAP)
    def evict_language_map_cache(cls):
        logger.info('清理语言映射缓存')
        return

    @classmethod
    def get_review_max_review_num(cls, attribute_key=CACHE_KEY_MAX_REVIEW_NUM):
        data = cls.get_configuration_with_cache(ConfigurationConstant.REVIEW_TYPE, attribute_key)
        try:
            return int(data) if data else AIReviewConstant.MAX_REVIEW_NUM
        except Exception as e:
            logger.error(e)
            return AIReviewConstant.MAX_REVIEW_NUM

    @classmethod
    def get_scribe_component_options(cls):
        try:
            data = json.loads(
                cls.get_configuration_with_cache(ConfigurationConstant.CACHE_TYPE_IDE_CONFIG,
                                                 ConfigurationConstant.CACHE_KEY_SCRIBE_COMPONENTS,
                                                 '[]'))
        except Exception as e:
            logger.error(e)
            data = []
        return data

    @classmethod
    def get_system_config(cls):
        try:
            data = json.loads(cls.get_configuration_with_cache(ConfigurationConstant.SYSTEM_TYPE,
                                                               ConfigurationConstant.SYSTEM_KEY,
                                                               '{}'))
        except JSONDecodeError:
            data = {'error': 'json error'}
        return data

    @classmethod
    def get_model_ide_normal(cls, attribute_key):
        """根据action端的配置获取model"""
        data = cls.dao.get_or_none(belong_type=attribute_key, attribute_key=attribute_key)
        if data:
            return data.attribute_value
        else:
            return 'deepseek-chat'

    @classmethod
    def get_check_e2e_case_config(cls):
        """获取e2e 检查 case配置"""
        is_check = cls.get_configuration_with_cache(
            ConfigurationConstant.E2E_BELONG_TYPE,
            ConfigurationConstant.E2E_IS_CHECK_CASE,
            ConfigurationConstant.E2E_IS_CHECK_CASE_DEFAULT
        )
        if is_check == 'true':
            is_check = True
        else:
            is_check = False
        score = cls.get_configuration_with_cache(
            ConfigurationConstant.E2E_BELONG_TYPE,
            ConfigurationConstant.E2E_MIN_CASE_SCORE,
            ConfigurationConstant.E2E_MIN_CASE_SCORE_DEFAULT
        )
        try:
            score = int(score)
        except Exception as err:
            logger.error(f"配置错误，改成默认值: {err},  score: {score}")
            score = ConfigurationConstant.E2E_MIN_CASE_SCORE_DEFAULT
        return is_check, score
