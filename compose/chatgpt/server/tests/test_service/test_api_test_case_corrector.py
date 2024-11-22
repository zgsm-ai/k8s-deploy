#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/21 10:32
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : test_api_test_case_corrector.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : 测试services/api_test/api_test_case_corrector.py模块功能

from tests.mock.mock_api_test_corrector import MOCK_API_INFO_ARRAY, MOCK_TEST_STEPS_ARRAY_ERROR, \
    MOCK_TEST_STEPS_ARRAY_CORRECT, MOCK_TEST_STEPS_PARAM_KEY_ERROR, MOCK_TEST_STEPS_PARAM_KEY_CORRECT, \
    MOCK_API_INFO_ARRAY_OBJECT, MOCK_TEST_STEPS_ARRAY_OBJECT_ERROR
from services.api_test.api_test_case_corrector import ApiTestCaseCorrector
from common.exception.exceptions import RequireParamsMissingError
from services.api_test.eolinker_api_helper import ApiHelper


class TestApiTestCaseCorrector(object):

    def test_validate_and_convert_param_types(self):
        api_detail_info_dict = dict()
        api_helper = ApiHelper(MOCK_API_INFO_ARRAY)
        api_detail_info_dict[MOCK_API_INFO_ARRAY.get("baseInfo").get("apiID")] = api_helper.api_info
        assert MOCK_TEST_STEPS_ARRAY_ERROR != MOCK_TEST_STEPS_ARRAY_CORRECT
        ApiTestCaseCorrector.validate_and_convert_param_types(MOCK_TEST_STEPS_ARRAY_ERROR, api_detail_info_dict)
        assert MOCK_TEST_STEPS_ARRAY_ERROR == MOCK_TEST_STEPS_ARRAY_CORRECT

    def test_validate_and_convert_param_key(self):
        api_detail_info_dict = dict()
        api_detail_info_dict[MOCK_API_INFO_ARRAY.get("baseInfo").get("apiID")] = MOCK_API_INFO_ARRAY
        assert MOCK_TEST_STEPS_PARAM_KEY_ERROR != MOCK_TEST_STEPS_PARAM_KEY_CORRECT
        new_steps = ApiTestCaseCorrector.validate_and_convert_param_key(MOCK_TEST_STEPS_PARAM_KEY_ERROR)
        assert new_steps == MOCK_TEST_STEPS_PARAM_KEY_CORRECT
        assert MOCK_TEST_STEPS_PARAM_KEY_ERROR == MOCK_TEST_STEPS_PARAM_KEY_CORRECT

    def test_check_array_params_childlist_is_existence(self):
        api_detail_info_dict = dict()
        api_helper = ApiHelper(MOCK_API_INFO_ARRAY_OBJECT)
        api_detail_info_dict[str(MOCK_API_INFO_ARRAY_OBJECT.get("baseInfo").get("apiID"))] = api_helper.api_info
        try:
            ApiTestCaseCorrector.check_array_params_childlist_is_existence(MOCK_TEST_STEPS_ARRAY_OBJECT_ERROR,
                                                                           api_detail_info_dict)
        except RequireParamsMissingError:
            assert True
        else:
            assert False
