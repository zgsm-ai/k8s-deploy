#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/24 11:06
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : api_test_service.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : api测试服务，生成API测试点和测试用例主业务逻辑
import json
import json_repair
import logging
from common.constant import ActionsConstant, CheckApiParamsType, ConfigurationConstant, \
    ApiTestConstant, GPTModelConstant
from common.eolinker_constant import EolinkerConstant
from common.exception.exceptions import ParameterConversionError
from services.api_test.api_test_case_service import ApiTestCaseService
from services.system.configuration_service import ConfigurationService
from controllers.completion_helper import completion_main
from third_platform.eolinker.api_studio_manager import ApiStudioManager
import re


# logger = logging.getLogger(__name__)  # logger不输出日志！


class ApiTestService:
    EOLINKER_TESTCASE_TYPE = "eolinker"
    PYTEST_TESTCASE_TYPE = "pytest"

    @classmethod
    def is_latest_version(cls, current_version):
        """
        判断版本是否为最新版本
        :param current_version: eolinker插件当前版本
        :return: 处理后的API详情信息
        """
        is_latest = False
        latest_version = ConfigurationService.get_configuration_with_cache(
            ConfigurationConstant.API_TEST_KEY,
            ConfigurationConstant.EOLINKER_BUNDLE_JS_VERSION,
            "default"
        )
        logging.info(f"EOLINKER_BUNDLE_JS_VERSION:current_version={current_version}, latest_version={latest_version}")
        if current_version == latest_version:
            is_latest = True
        return is_latest

    # api_info信息预处理，返回更易于理解的格式
    @classmethod
    def process_api_info(cls, api_info: dict) -> (dict, list):
        """
        处理API详情信息
        :param api_info: API详情信息
        :return: 处理后的API详情信息
        """
        api_info_param = {}
        api_info_desc, request_param_key_list = cls.process_request_info_for_api_info(api_info['request_info'])
        url_param, api_url_param_desc, url_param_key_list = cls.process_url_param_for_api_info(api_info['url_param'])
        api_info_processed = {
            "api_id": api_info['base_info']['api_id'],
            "api_name": api_info['base_info']['api_name'],
            "api_url": api_info['base_info']['api_url'],
            "api_request_type": api_info['base_info']['api_request_type'],
            "api_url_param": url_param,
            "api_url_param_desc": api_url_param_desc,
            "api_info_param": api_info_param,
            "api_info_desc": api_info_desc
        }
        logging.info(f"api_name: {api_info_processed['api_name']}")
        logging.info(f"api_url:{api_info_processed['api_url']}")
        logging.info(f"api_info_desc: {api_info_desc}")
        waiting_test_param_list = request_param_key_list + url_param_key_list
        return api_info_processed, waiting_test_param_list

    @classmethod
    def get_min_max_desc(cls, sub_request_info: dict) -> str:
        """
        获取最小最大值描述
        :param sub_request_info: 子参数信息
        :return: 最小最大值描述
        """
        min_max_desc = ""
        if sub_request_info.get('min_value'):
            min_max_desc += f"最小值{sub_request_info.get('min_value')}，"
        if sub_request_info.get('max_value'):
            min_max_desc += f"最大值{sub_request_info.get('max_value')}，"
        if sub_request_info.get('min_length'):
            min_max_desc += f"最小长度{sub_request_info.get('min_length')}，"
        if sub_request_info.get('max_length'):
            min_max_desc += f"最大长度{sub_request_info.get('max_length')}，"
        return min_max_desc

    @classmethod
    def process_request_info_for_api_info(cls, request_info: list, indent_level=0) -> (str, list):
        """
        处理API详情信息request_info参数信息，返回易于理解的参数信息
        :param request_info: API详情信息内的request_info列表信息
        :param indent_level: 当前嵌套层级的缩进等级
        :return: 处理后的API详情信息request_info参数信息
        """
        request_param_key_list = []
        api_info_desc = ""
        param_type_list = EolinkerConstant.PARAM_TYPE_LIST
        indent = "    " * indent_level  # 根据嵌套层级增加缩进
        for sub_request_info in request_info:
            request_param_key_list.append(sub_request_info.get('param_key'))
            min_max_desc = cls.get_min_max_desc(sub_request_info)
            api_info_desc += f"{indent}{sub_request_info.get('param_key')}: " \
                             f"{'必填' if sub_request_info.get('param_not_null') == '0' else '非必填'}, " \
                             f"参数值类型：" \
                             f"{param_type_list.get(sub_request_info.get('param_type'), 'string')}, " \
                             f"参数说明：{sub_request_info.get('param_name')}, {sub_request_info.get('param_limit')} " \
                             f"{min_max_desc}" \
                             f"参数示例：{sub_request_info.get('param_value')}\n"

            # 如果参数类型是array或object，并且有子参数列表，则递归处理子参数
            if sub_request_info.get('param_type') in [EolinkerConstant.ARRAY, EolinkerConstant.OBJECT] \
                    and sub_request_info.get('child_list'):
                child_info_desc, child_param_keys = cls.process_request_info_for_api_info(
                    sub_request_info.get('child_list'), indent_level + 1)
                api_info_desc += f"{indent}    {sub_request_info.get('param_key')}参数的子参数列表：\n{child_info_desc}"
                request_param_key_list.extend(child_param_keys)

        return api_info_desc, request_param_key_list

    @classmethod
    def process_url_param_for_api_info(cls, url_param: list) -> (str, str, list):
        """
        处理API详情信息url_param参数信息，返回易于理解的参数信息
        :param url_param: API详情信息内的url_param列表信息
        :return: 处理后的API详情信息url_param参数信息
        """
        url_param_key_list = []
        url_param_list = []
        api_url_param_desc = ""
        for sub_url_param in url_param:
            url_param_key_list.append(sub_url_param.get('param_key'))
            min_max_desc = cls.get_min_max_desc(sub_url_param)
            url_param_list.append(f"{sub_url_param.get('param_key')}={sub_url_param.get('param_value')}")
            api_url_param_desc += f"{sub_url_param.get('param_key')}: " \
                                  f"{'必填' if sub_url_param.get('param_not_null') == '0' else '非必填'}, " \
                                  f"参数值类型：" \
                                  f"{EolinkerConstant.PARAM_TYPE_LIST.get(sub_url_param.get('param_type'), 'string')}," \
                                  f"参数说明：{sub_url_param.get('param_name')}, {sub_url_param.get('param_limit')} " \
                                  f"{min_max_desc}" \
                                  f"参数示例：{sub_url_param.get('param_value')}\n"

        url_param = "&".join(url_param_list)
        return url_param, api_url_param_desc, url_param_key_list

    @classmethod
    def generate_api_test_point(cls, request_data):
        """
        生成API测试点
        :param request_data: 请求数据
        :return: 测试点
        """
        resp = completion_main(request_data, is_ut=True)
        if request_data.get("stream"):
            process_response = cls.process_stream_response_by_test_point(resp)
        else:
            process_response = resp.get("choices")
        return process_response

    @classmethod
    def generate_pytest_test_case(cls, request_data):
        """
        生成pytest框架API测试用例
        :param request_data: 请求数据
        :return: pytest框架API测试用例
        """
        resp = None
        resp_list = []
        api_info = request_data.get('api_info')
        test_points = request_data.get("test_points")
        test_point_list = [test_points[i:i + ApiTestConstant.generate_test_set_size] for i in
                           range(0, len(test_points), ApiTestConstant.generate_test_set_size)]
        for test_points in test_point_list:
            test_points = '\n'.join(test_points)
            request_data_copy = request_data.copy()
            request_data_copy['test_points'] = test_points
            resp = completion_main(request_data_copy, is_ut=True)
            resp_list.append(resp)
        if request_data.get("stream"):
            process_response = cls.process_stream_response_by_test_set(resp_list, api_info)
        else:
            case_number = 1
            testcase_list = []
            for resp in resp_list:
                try:
                    resp_content = json_repair.loads(resp.get('choices', [{}])[0].get('message', {}).get('content', ''))
                except Exception as e:
                    logging.error(f'JSON repair loads failed: {e}')
                    resp_content = {}
                for test_set in resp_content.get("test_sets", []):
                    testcase, case_number = cls.format_pytest_testcase(test_set,
                                                                       api_info,
                                                                       case_number)
                    testcase_list.append(testcase)
            process_response = {
                "id": resp.get("id"),
                "model": resp.get("model"),
                "test_point": resp.get("choices")[0].get("message", {}).get("content", ""),
                "test_case": testcase_list
            }
        return process_response

    @classmethod
    def generate_eolinker_test_case(cls, request_data, display_name, origin=None):
        """
        生成eolinker平台上的API测试用例
        :param request_data: 请求数据
        :param display_name: 执行用户名称
        :param origin: 原始调度地址
        :return:
        """
        logging.info("start generate_eolinker_test_case")
        return ApiTestCaseService.api_management_test_case_task(request_data, display_name, origin=origin)

    @classmethod
    def replace_structure(cls, params, data_structure_list):
        params_list = []

        if not params:
            return []

        for index, param in enumerate(params):
            if "child_list" in param:
                # 递归替换结构体
                child_list = param.get("child_list", [])
                param["child_list"] = cls.replace_structure(child_list, data_structure_list)
            is_extend = False
            if "structure_id" in param:
                structure_id = param["structure_id"]
                if structure_id:
                    # structure_id有可能是字符串或者数字,eolinker文档api返回的
                    s = data_structure_list.get(structure_id, {}) \
                        or data_structure_list.get(str(structure_id), {})
                    if s:
                        structure_data = s.get("structure_data", [])
                        params_list.extend(structure_data)
                        is_extend = True
            if not is_extend:
                params_list.append(param)
        return params_list

    @classmethod
    def replace_api_structure(cls, v2_api_info, v3_api_info):
        """
        因为v3有 data_structure_list ， v2没有，但是v3的其他字段和v2又有点不一样，所以先把v3的拿过来用，直接全部替换v3改动太大
        TODO: 后续再优化，eolinker 自己的api返回的内容也很乱
        @param v2_api_info:
        @param v3_api_info:
        @return:
        """
        data_structure_list = v3_api_info["data_structure_list"]
        result_info = v2_api_info["result_info"]
        request_info = v2_api_info["request_info"]
        v2_api_info["request_info"] = cls.replace_structure(request_info, data_structure_list)
        result_info_list = []
        for result in result_info:
            result["param_list"] = cls.replace_structure(result["param_list"], data_structure_list)
            result_info_list.append(result)
        v2_api_info["result_info"] = result_info_list
        return v2_api_info

    @classmethod
    def get_api_info(cls, raw_api_info, testcase_type="", origin=None):
        """
        获取API详情信息
        :param raw_api_info: 原始API详情信息
        :param authorization: 认证信息
        :param testcase_type: 测试用例类型
        :param origin: 原始调度地址
        :return: API详情信息
        """
        if testcase_type == cls.EOLINKER_TESTCASE_TYPE:
            api_info = raw_api_info

        else:
            api_info = raw_api_info.get('data')
            if not api_info:
                # 如果接口未传入API详情信息，则需要根据id获取API详情信息
                # 因为v3有data_structure_list ， v2没有，但是v3的其他字段和v2又有点不一样，所以先把v3的拿过来用，直接全部替换v3改动太大
                # TODO: 后续再优化，eolinker 自己的api返回的内容也很乱
                v2_api_info = ApiStudioManager.get_api_info(
                    raw_api_info.get('space_id'), raw_api_info.get('project_id'),
                    raw_api_info.get('api_id'), origin
                )
                v3_api_info = ApiStudioManager.get_api_info_v3(
                    raw_api_info.get('space_id'), raw_api_info.get('project_id'),
                    raw_api_info.get('api_id'), origin
                )
                api_info = cls.replace_api_structure(v2_api_info, v3_api_info)
                if not api_info:
                    logging.warning(f"获取API详情信息失败，尝试重新获取{api_info}")
                    return False

            # 检查API详情信息是否正确，对参数进行规范检查，返回错误信息
            result, check_data = cls.check_api_info(api_info)
            if not result:
                # 有问题直接返回错误信息
                raise ParameterConversionError(check_data)

            # 经过处理的api接口信息, todo这里仅覆盖了接口参数是json类型单嵌套参数转换，多嵌套的待适配
            api_info, waiting_test_param_list = cls.process_api_info(api_info)

            # 若没有body或query参数，返回错误信息
            if not waiting_test_param_list:
                raise ParameterConversionError(EolinkerConstant.NOT_PARAM_ERROR)

            waiting_test_param = '、'.join(waiting_test_param_list)
            api_info["waiting_test_param"] = waiting_test_param
        return api_info

    @classmethod
    def generate_testcases(cls, data, origin=None, display_name=""):
        api_info = cls.get_api_info(data.api_info, data.testcase_type, origin=origin)
        request_data = {"api_info": api_info,
                        "stream": data.stream,
                        "action": data.action,
                        "response_format": data.response_format,
                        "conversation_id": "",
                        "test_points": data.test_points,
                        "gpt_model": GPTModelConstant.GPT_4,
                        }
        if data.action == ActionsConstant.GENERATE_API_TEST_SET:
            if data.testcase_type == cls.EOLINKER_TESTCASE_TYPE:
                # 生成eolinker用例
                process_response = cls.generate_eolinker_test_case(data,
                                                                   display_name,
                                                                   origin=origin)
            else:
                # 默认生成pytest用例
                process_response = cls.generate_pytest_test_case(request_data)
        else:
            # 这里复用单测is_ut=True逻辑，保留模型获取使用gpt4
            process_response = cls.generate_api_test_point(request_data)
        return process_response

    @classmethod
    def process_stream_response_by_test_point(cls, response):
        """
        生成测试点 处理流式响应
        :param response: 流式响应迭代器
        :return: 处理后的响应
        """
        if not response:
            return None

        discard_prefix = '{"test_params_description"'  # 需要丢弃的非固定JSON前缀
        json_prefix = '"test_points":"'  # 不需要的固定JSON前缀
        json_suffix = '"}'  # 不需要的固定JSON后缀

        full_response = ''  # 完整响应
        line_content = ''  # 一行内容
        stream_state = 0  # 流式返回状态。0:未开始; 1:已开始; 2:已结束.
        try:
            for content in response:
                full_response += content
                if stream_state == 0:
                    full_response = full_response.replace(' ', '').replace('\n', '')
                    # 以 discard_prefix 开头并且第一次包含 json_prefix 时开始流式
                    index = full_response.find(json_prefix)
                    if full_response.startswith(discard_prefix) and index != -1:
                        stream_state = 1  # 开始流式
                        line_content = full_response[index + len(json_prefix):]

                elif stream_state == 1:
                    line_content += content
                    if line_content.replace(' ', '').replace('\n', '').endswith(json_suffix):
                        stream_state = 2  # 结束流式
                        line_content = line_content.replace(' ', '').replace('\n', '').replace(json_suffix, '')
                        yield line_content.replace('\\"', '"') + '\n'
                        continue

                    if '\\n' in line_content:
                        line_content, next_line_content = line_content.split('\\n')  # 以换行符分割前行和行后内容
                        # 当遇到双引号里面带双引号时会存在转义双引号的情况，但是这里本身已经使用换行分割字符串，不需要再对双引号进行转义
                        # 这里取消转义符号
                        yield line_content.replace('\\"', '"') + '\n'
                        line_content = next_line_content
        except Exception as e:
            logging.error(f'生成测试点处理异常: {e}')
        finally:
            if response is not None and hasattr(response, 'close'):
                logging.info("close generator test point")
                response.close()

    @classmethod
    def process_stream_response_by_test_set(cls, resp_list, api_info):
        """
        生成测试集处理流式响应
        :param resp_list: 流式响应迭代器列表
        :param api_info: api接口信息
        :return: 处理后的响应
        """
        case_number = 1
        for response in resp_list:
            if not response:
                continue
            json_prefix = '{"test_sets":['  # 不需要的JSON前缀

            full_response = ''  # 完整响应
            a_json_content = ''  # 一个json对象
            stream_state = 0  # 流式返回状态。0:未开始; 1:已开始.
            try:
                for content in response:
                    full_response += content
                    if stream_state == 0:
                        if full_response.replace(' ', '').replace('\n', '').startswith(json_prefix):
                            stream_state = 1
                            a_json_content = full_response.replace(' ', '').replace('\n', '').replace(json_prefix, '')

                    elif stream_state == 1:
                        a_json_content += content
                        try:  # 匹配并转化字典，成功则表示完整的对象
                            re_result = re.search(r'(\{[\s\S]*\})(.*)', a_json_content)
                            if re_result:
                                re_json_object = re_result.group(1)  # 完整的json
                                right_of_brace = re_result.group(2)  # json后的字符
                                try:  # 匹配并转化字典，成功则表示完整的对象
                                    test_set_dict = json.loads(re_json_object)
                                except Exception:  # 失败则跳过
                                    continue
                                if not isinstance(test_set_dict, dict):
                                    continue

                                a_json_content = right_of_brace
                                test_set_dict = json.loads(cls.replace_text(json.dumps(test_set_dict)))  # 特殊处理
                                result, case_number = cls.process_test_set(test_set_dict, api_info, case_number)
                                yield result

                        except Exception as e:
                            logging.error(f'处理测试数据异常 {e}')
                            continue

            except Exception as e:
                logging.error(f'生成测试集处理异常: {e}')
                yield ''
            finally:
                if response is not None and hasattr(response, 'close'):
                    logging.info("close generator test set")
                    response.close()

    @classmethod
    def process_test_set(cls, test_set_dict, api_info, case_number):
        # 解析测试点并返回测试用例
        testcase, case_number = cls.format_pytest_testcase(test_set_dict, api_info, case_number)
        if testcase:
            return testcase, case_number
        return '', case_number

    @staticmethod
    def replace_text(input_text):
        """
        "a*10" 转为: "aaaaaaaaaa"
        """
        pattern = r'(\w)\*(\d+)'  # 匹配类似 'r*10' 的模式

        def replace_match(match):
            char = match.group(1)
            count = int(match.group(2))

            # 大于10000的，不进行填充，会卡前端
            if count > 10000:
                return f"这是一段长度为{count}的字符串"
            return char * count

        output_text = re.sub(pattern, replace_match, input_text)
        return output_text

    @classmethod
    def format_pytest_testcase(cls, test_set: dict, api_info: dict, case_number: int):
        """
        格式化API测试用例
        :param test_set: 测试集字典
        :param api_info: api接口信息
        :param case_number: 测试集序号
        :return: 格式化后的测试用例
        """
        pytest_testcase = ""
        try:
            # 部分文档url带参数或空格，这里要去掉参数或空格部分
            base_api_url = api_info.get('api_url', "").split("?")[0].strip()
            testcase_id = f"{base_api_url.replace('/', '-').strip('-').strip()}-" \
                          f"{api_info.get('api_request_type', '')}-case-{str(case_number).zfill(3)}"
            test_point_name = f"AI_{test_set.get('name')}"
            test_case_title = test_set.get("test_case_title", "test_http_mock").replace("test", "test_ai", 1)
            test_point_input_body_param = test_set.get("input_body_param")
            test_point_input_query_param = test_set.get("input_query_param")
            api_url = base_api_url
            if test_point_input_query_param:
                api_url = f"{base_api_url}?{test_point_input_query_param}"
            test_point_output_status_code = test_set.get("output_status_code")
            # 一期只支持xdr，这里先写死，后面需要扩展其他业务线再添加相关逻辑
            pytest_case_template = ConfigurationService.get_pytest_case_template("xdr")

            if case_number // 2 == 0:
                number = f"{str(case_number)}(命中jsonschema)"  # 调试信息，先埋点，后期计划输出jsonschema后匹配用例是否命中
            else:
                number = f"{str(case_number)}"
            pytest_testcase += pytest_case_template.format(number=number,
                                                           test_point_name=test_point_name.replace('"', '\\"'),
                                                           test_case_title=test_case_title,
                                                           request_json=test_point_input_body_param,
                                                           api_url=api_url,
                                                           request_type=api_info.get('api_request_type', ""),
                                                           status_code=test_point_output_status_code,
                                                           testcase_id=testcase_id) + "\n\n"
            case_number += 1
        except Exception as e:
            logging.error(f"格式化测试用例失败，{e}")
            # logging.warning(f"testpoint: {testpoint}, formatted_json={formatted_json}")
        return pytest_testcase, case_number

    @classmethod
    def format_testpoint_str(cls, testpoint_str):
        """
        格式化测试点
        :param testpoint_str: 测试点
        :return: 格式化后的测试点,删掉前面的测试点列表方便后续处理
        """
        pattern = ".*测试数据："
        # 使用 re.sub() 函数替换匹配的文本为空字符串
        testpoint_str = re.sub(pattern, '', testpoint_str, flags=re.DOTALL)
        testpoint_str = testpoint_str.strip().lstrip("```json")
        testpoint_str = testpoint_str.rstrip("```")
        if ".repeat(" in testpoint_str:
            # json不支持".repeat(n)"格式字符串
            # 替换 ".repeat(n)" 为实际的字符串
            testpoint_str = re.sub(r'(\w+=)" \+ "(\w)".repeat\((\d+)\)', cls.repeat_replacer, testpoint_str)
            testpoint_str = re.sub(r'"(\w)".repeat\((\d+)\)', cls.repeat_replacer, testpoint_str)
        if "new Array(" in testpoint_str:
            # json不支持"new Array(129).fill("test")"格式字符串
            # 替换 "new Array(129).fill("test")" 为实际的字符串
            testpoint_str = re.sub(r'new Array\((\d+)\).fill\("(\w+)"\)', cls.repeat_array_fill, testpoint_str)
            testpoint_str = re.sub(r'new Array\((\d+)\)', cls.repeat_array_fill, testpoint_str)
        # logging.info(testpoint_str)
        return testpoint_str

    # 使用正则表达式匹配 ".repeat(n)" 模式并替换
    @staticmethod
    def repeat_replacer(match):
        if match.lastindex == 2:
            char_repeat = match.group(1)  # 获取重复的字符
            count = int(match.group(2))  # 获取重复的次数
            result = '"' + char_repeat * count + '"'  # 返回重复指定次数的字符
        else:
            char_key = match.group(1)
            char_repeat = match.group(2)
            count = int(match.group(3))
            result = char_key + char_repeat * count + '"'  # 返回重复指定次数的字符
        return result

    # 使用正则表达式匹配new Array(129).fill("test")模式并替换
    @staticmethod
    def repeat_array_fill(match):
        count = int(match.group(1))  # 获取重复的次数
        if match.lastindex == 2:
            string = match.group(2)  # 获取列表元素
        else:
            string = "test"
        return '"' + str([string] * count) + '"'  # 返回重复指定次数的字符

    @classmethod
    def check_api_info(cls, api_info):
        """
        校验API详情信息
        :param api_info: API详情信息
        :return: 处理结果和结果信息
        """
        check_api_params_type = ConfigurationService.get_configuration_with_cache(
            ConfigurationConstant.API_TEST_KEY,
            ConfigurationConstant.CHECK_API_PARAMS_TYPE,
            CheckApiParamsType.ALL
        )
        error_message = ""
        if check_api_params_type == CheckApiParamsType.CLOSE:
            return True, ""

        # 入参校验
        if check_api_params_type in [CheckApiParamsType.ALL, CheckApiParamsType.REQUEST]:
            url_param = api_info.get('url_param') or []
            msg = cls.check_params_info(url_param)
            if msg:
                error_message += f"## url参数\n{msg}"
            request_info = api_info.get('request_info') or []
            msg = cls.check_params_info(request_info)
            if msg:
                error_message += f"## 请求参数\n{msg}"

        # 出参校验
        if check_api_params_type in [CheckApiParamsType.ALL]:
            result_info = api_info.get('result_info') or []
            result_info_msg = ""
            for sub_result_info in result_info:
                param_list = sub_result_info.get('param_list') or []
                response_name = sub_result_info.get("response_name")
                response_code = sub_result_info.get("response_code")
                msg = cls.check_params_info(param_list, indent_level=1)
                if msg:
                    result_info_msg += f"### {response_name}({response_code})\n{msg}"
            if result_info_msg:
                error_message += f"## 返回结果\n{result_info_msg}"

        if error_message:
            error_message = "# 接口文档规范校验失败，请完善相关字段\n" + error_message
            return False, error_message
        return True, ""

    @classmethod
    def check_params_info(cls, params_info: list, indent_level=0) -> (str, list):
        """
        校验参数信息规范，如果有问题，返回参数缺少的信息详情，如果是嵌套结构参数需要递归
        :param params_info: 参数的详情信息
        :param indent_level: 当前嵌套层级的缩进等级
        :return: 处理结果和结果信息
        """

        def is_empty(value):
            # 如果value是None，返回True
            if value is None:
                return True
            # 如果value是数字0，返回False
            elif value == 0:
                return False
            # 对于其他情况，使用bool转换判断
            return not bool(value)

        param_type_list = EolinkerConstant.PARAM_TYPE_LIST
        indent = "  " * indent_level + "- "  # 根据嵌套层级增加缩进
        error_message = ""
        for sub_params_info in params_info:
            param_key = sub_params_info.get('param_key')  # 参数名
            param_not_null = sub_params_info.get('param_not_null')  # 必填
            param_type = sub_params_info.get('param_type')  # 参数值类型
            param_type_name = param_type_list.get(sub_params_info.get('param_type'), 'string')  # 参数值类型
            param_name = sub_params_info.get('param_name')  # 参数说明
            param_value = sub_params_info.get('param_value')  # 参数示例

            check_dict = {
                '必填': param_not_null,
                '类型': param_type,
                '说明': param_name,
                '示例': param_value
            }
            error_fields = [field for field, value in check_dict.items() if is_empty(value)]
            if error_fields:
                error_fields_str = '、'.join(error_fields)
                error_message += f"{indent}参数名**{param_key}**：【{error_fields_str}】字段不可为空\n"

            error_fields = []
            # int、float、double、byte、short、long、number需要校验最大最小值
            if param_type in [EolinkerConstant.INT, EolinkerConstant.FLOAT, EolinkerConstant.DOUBLE,
                              EolinkerConstant.BYTE, EolinkerConstant.SHORT, EolinkerConstant.LONG,
                              EolinkerConstant.NUMBER]:
                min_value = sub_params_info.get('min_value')
                max_value = sub_params_info.get('max_value')
                check_dict = {
                    '最小值': min_value,
                    '最大值': max_value,
                }
                error_fields += [field for field, value in check_dict.items() if is_empty(value)]

            # string、array需要校验最大最小长度
            elif param_type in [EolinkerConstant.STRING, EolinkerConstant.ARRAY]:
                min_length = sub_params_info.get('min_length')
                max_length = sub_params_info.get('max_length')
                check_dict = {
                    '最小长度': min_length,
                    '最大长度': max_length,
                }
                error_fields += [field for field, value in check_dict.items() if is_empty(value)]

            error_fields_str = '、'.join(error_fields)
            if error_fields_str:
                error_message += f"{indent}参数名**{param_key}**类型为{param_type_name}：" \
                                 f"【{error_fields_str}】字段不可为空\n"

            # 如果参数类型是array或object，并且有子参数列表，则递归处理子参数
            if param_type in [EolinkerConstant.ARRAY, EolinkerConstant.OBJECT] and sub_params_info.get('child_list'):
                _error_message = cls.check_params_info(sub_params_info.get('child_list'), indent_level + 1)
                error_message += _error_message

        return error_message
