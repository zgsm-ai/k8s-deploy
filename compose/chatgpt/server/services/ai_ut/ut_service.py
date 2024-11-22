#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 18212
@Date    : 2023/11/07
"""
import json
import logging
import re

from common.constant import ConfigurationConstant
from config import Config
from services.ai_ut.model_service import UTModelService
from services.system.configuration_service import ConfigurationService
from third_platform.es.chat_messages.ut_prompt_es_service import ut_prompt_es_service
from third_platform.services.analysis_service import AnalysisService


class UTService:

    @classmethod
    def check_ut_button(cls, user):
        u_dept = AnalysisService.get_user_multilevel_dept(user.username)
        res = False

        dept_result = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                        ConfigurationConstant.UT_OPEN_DEPT,
                                                                        '')
        ut_button_dept = dept_result.split(',') if dept_result else []

        for d in ut_button_dept:
            if d in u_dept:
                res = True
                break
        data = dict(result=res)
        return data

    @classmethod
    def get_plugin_min_version(cls):
        vs_min_v = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                     ConfigurationConstant.UT_PLUGIN_VSCODE_MIN_VERSION,
                                                                     '1.0.1')
        jb_min_v = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                     ConfigurationConstant.UT_PLUGIN_JETB_MIN_VERSION,
                                                                     '1.0.1')
        data = dict(plugin_min_version=dict(vscode=vs_min_v, jetbrains=jb_min_v))
        return data

    @classmethod
    def get_ai_test_config(cls):
        ut_config = Config().ut
        use_model = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                      ConfigurationConstant.UT_USE_MODEL,
                                                                      ut_config.get("use_model"))
        ut_result_file_spc = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                               ConfigurationConstant.UT_RESULT_FILE_SPC,
                                                                               ut_config.get("ut_result_file_spc"))
        language = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                     ConfigurationConstant.UT_LANGUAGE,
                                                                     ut_config.get("language"))
        language = json.loads(language)

        sdk_config = ut_config.get("sdk")
        max_point = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                      ConfigurationConstant.UT_MAX_POINT,
                                                                      sdk_config.get("max_point"))
        req_timeout = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                        ConfigurationConstant.UT_REQ_TIMEOUT,
                                                                        sdk_config.get("req_timeout"))
        req_times = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                      ConfigurationConstant.UT_REQ_TIMES,
                                                                      sdk_config.get("req_times"))

        model_data = ut_config.get("models", {}).get(use_model)
        max_workers = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                        ConfigurationConstant.UT_MAX_WORKERS,
                                                                        model_data.get("max_workers"))
        token_length = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                         ConfigurationConstant.UT_TOKEN_LENGTH,
                                                                         model_data.get("token_length"))
        token_length = json.loads(token_length)
        point_template = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                           ConfigurationConstant.UT_POINT_TEMPLATE,
                                                                           model_data.get("point_template"))
        case_template = ConfigurationService.get_configuration_with_cache(ConfigurationConstant.UT_RULES,
                                                                          ConfigurationConstant.UT_CASE_TEMPLATE,
                                                                          model_data.get("case_template"))

        res = {
            "model": use_model,
            "language": language,
            "point_template": point_template,
            "case_template": case_template,
            "req_timeout": int(req_timeout),
            "req_times": int(req_times),
            "token_length": token_length,
            "max_workers": int(max_workers),
            "ut_result_file_spc": ut_result_file_spc,
            "max_point": int(max_point)
        }
        return res

    @classmethod
    def generate_testcases(cls, data: dict, user):

        data["display_name"] = user.display_name if user and user.display_name else ""
        data["username"] = user.username if user and user.username else ""

        prompt = data.get("inputs")
        parameters = data.get("parameters")

        if not all([prompt, parameters]):
            return False, "缺少必填参数"

        use_model = Config().ut.get("use_model")
        if data.get("gpt_model"):
            use_model = "GPTModel"
        resp = UTModelService.get_ut_res(data, use_model)
        if data.get("stream") is True:
            return True, cls.process_stream_response(resp, data, use_model)
        else:
            data["response"] = resp
            ut_prompt_es_service.insert_code_completion(data)
            return True, resp

    @staticmethod
    def process_stream_response(response, data, use_model=""):
        content = ""
        if use_model == "GPTModel":
            # 已经被处理过了，不能在iter_lines()
            for line in response:
                yield line
        else:
            re_str = r'"text":"(.*?)"'
            try:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        text = ""
                        try:
                            # 使用正则表达式匹配"text"字段下的内容
                            match = re.search(re_str, line_str)
                            if match:
                                # 获取匹配到的内容
                                text = match.group(1)
                        except Exception as e:
                            logging.error("解析响应内容失败，原因：{}".format(e))

                        # 处理每行数据
                        content += text
                        yield text
            except Exception as e:
                logging.error(f'生成单测处理异常: {e}')
            finally:
                if response is not None and hasattr(response, 'close'):
                    logging.info("close generator test ut")
                    response.close()

        data["response"] = {
            "stream_content": content
        }
        ut_prompt_es_service.insert_code_completion(data)
