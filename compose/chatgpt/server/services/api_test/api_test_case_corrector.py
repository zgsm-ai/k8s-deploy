#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/6 17:48
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : api_test_case_corrector.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : 用于对AI返回的api_test_case信息做校验及修正

from common.eolinker_constant import EolinkerConstant, PARAM_CLASS_MAP
from common.constant import ApiTestCaseConstant
from common.exception.exceptions import ParamsTypeError
from common.exception.exceptions import RequireParamsMissingError
from services.api_test.api_test_case_inspector import ApiTestCaseInspector
from services.api_test.api_test_case_service import ApiTestCaseService
import logging
import re

logger = logging.getLogger(__name__)


class ApiTestCaseCorrector:
    match_rule_not_verify = '0'  # 不校验
    param_info_null = ''  # 校验值为空
    match_rule_length_gt = '8'  # 校验值为空或空字符串
    param_info_zero = '0'  # 校验值为0
    # 定义超长参数正则表达式模式
    long_param_info_pattern = re.compile(r"(.*)重复(\d+)次(.*)?")

    @classmethod
    def generate_case_corrector(cls, test_steps, api_detail_info_dict, test_point, tested_api, display_name="",
                                case_type=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST):
        """
        针对新生成用例场景的校验及修正
        :param test_steps: 测试步骤列表
        :param api_detail_info_dict: api文档信息
        :param test_point: 测试点
        :param tested_api: 测试点对应api信息，markdom格式
        :param display_name: 执行人名称
        :param case_type: 用例类型
        :return:
        """
        if case_type == ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST:
            # api管理页面不用做这些强校验，避免用户看到用例数少于勾选测试点数量
            # 检查必填参数是否缺失
            if not cls.check_all_require_params_is_existence(test_steps, api_detail_info_dict):
                raise RequireParamsMissingError
            # 检查array参数嵌套object参数类型子参数是否缺失，避免参数同名情况导致子参数缺失情况
            # 比如{data: [{data: "123"}]} 场景会识别为{data: ["123"]}
            cls.check_array_params_childlist_is_existence(test_steps, api_detail_info_dict)
            # 检查参数类型是否正确，对异常的类型进行修正
            cls.validate_and_convert_param_types(test_steps, api_detail_info_dict)
        if test_steps:
            # 校验param_key是否正常，对异常param_key进行修正
            cls.validate_and_convert_param_key(test_steps)

        # 校验文档是否覆盖异常场景说明，对不覆盖的直接返回固定校验场景
        cls.validate_and_convert_response_body(test_steps, test_point, tested_api, display_name)
        # 校验及修正test_steps的参数列表内的param_info参数值
        cls.check_and_replace_step_param_info(test_steps)

    @classmethod
    def modify_case_corrector(cls, test_steps, old_test_steps, api_detail_info_dict):
        """
        针对新增用例场景的校验及修正
        :param test_steps: 测试步骤列表
        :param old_test_steps: 旧测试步骤列表
        :param api_detail_info_dict: api文档信息
        :return:
        """
        # 检查必填参数是否缺失
        if not cls.check_all_require_params_is_existence(test_steps, api_detail_info_dict):
            raise RequireParamsMissingError
        cls.fill_params2test_steps(test_steps, old_test_steps.get('test_steps', []), api_detail_info_dict)
        cls.validate_and_convert_param_types(test_steps, api_detail_info_dict)

    @classmethod
    def fill_params2test_steps(cls, test_steps, old_test_steps, api_detail_info_dict):
        """
        为新的测试步骤test_steps补充参数，补充条件为旧测试步骤和api文档中存在此参数而新步骤中无此参数场景
        为了解决部分chatgpt返回场景缺少参数问题，如https://td.sangfor.com/#/defect/details/2024043000323
        :param test_steps: 测试步骤列表
        :param old_test_steps: 旧测试步骤列表
        :param api_detail_info_dict: api文档信息
        :return:
        """

        # 递归函数，用于处理嵌套的child_list
        def process_params(params, api_keys, process_test_params, parent_path=''):
            for param in params:
                param_key = param.get('param_key')
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('param_key')}" if parent_path else param.get('param_key')
                # 检查参数是否在api_info中定义
                if current_path in api_keys:
                    # 检查参数是否在test_steps中存在
                    # print(f"current_path={current_path} in process_test_params={process_test_params}")
                    test_param_keys = [p['param_key'] for p in process_test_params]
                    if param_key not in test_param_keys:
                        # 如果参数不存在，则将其添加到test_steps中
                        process_test_params.append(param)
                        logger.info(f"Added {param_key} to test_steps.")
                # 递归处理子参数
                if 'child_list' in param and param['child_list']:
                    # print(f"current_path in process_test_params={process_test_params}, param_key={param_key}")
                    process_params(param['child_list'], api_keys,
                                   cls.get_child_list_by_param_key(param_key, process_test_params),
                                   current_path)

        # 遍历old_test_steps中的参数
        for old_step in old_test_steps:
            for param_class in PARAM_CLASS_MAP.values():
                old_params = old_step.get('case_data', {}).get(param_class, [])
                api_id = old_step.get('api_id', "")
                api_info_param_type = cls.get_api_info_param_type(api_detail_info_dict, api_id)
                api_info_keys = api_info_param_type.keys()
                # 对于每个test_step，检查并添加缺失的参数
                for test_step in test_steps:
                    test_params = test_step['case_data'].get(param_class, [])
                    process_params(old_params, api_info_keys, test_params, param_class)

    @classmethod
    def get_api_info_param_type(cls, api_detail_info_dict, api_id):
        """
        获取api_info所有参数的param_type，由于嵌套参数可能存在同名参数，这里加上parent_path进行区分
        :param api_detail_info_dict: api_detail_info_dict
        :param api_id: api_id
        :return: api_info_param_type
        """
        api_info = api_detail_info_dict.get(str(api_id)) if api_detail_info_dict.get(
            str(api_id)) else api_detail_info_dict.get(api_id)
        # 提取api_info中所有的param_key, 参数类型转换和步骤中的类型一致，并支持嵌套childList
        api_info_param_type = dict()

        # 递归函数，用于填充param_key_to_name字典
        def fill_api_info_keys(sub_param_list, parent_path=""):
            for param in sub_param_list:
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('paramKey')}" if parent_path else param.get('paramKey')
                api_info_param_type[current_path] = param.get('paramType')
                # 递归检查子参数
                if 'childList' in param:
                    fill_api_info_keys(param['childList'], current_path)

        for section in PARAM_CLASS_MAP.keys():
            fill_api_info_keys(api_info.get(section, []), PARAM_CLASS_MAP.get(section))

        return api_info_param_type

    @classmethod
    def get_child_list_by_param_key(cls, param_key, param_list):
        """
        根据param_key获取child_list
        :param param_key: child_list对应的param_key
        :param param_list: 参数列表
        :return: 返回param_list中param_key对应的child_list
        """
        if not param_list:
            return []

        for param in param_list:
            # print(f"get_child_list_by_param_key: param_key={param_key},param={param} param_list={param_list}")
            if param.get('param_key') == param_key:
                return param.get('child_list')

    @classmethod
    def validate_and_convert_param_types(cls, test_steps, api_detail_info_dict):
        """
        部分array类型数据概率性识别为object类型，这里添加类型检查，如果是array类型被识别为object类型，则将其转换为array类型
        如果是其他类型错误则抛出异常
        :param test_steps: 测试步骤列表
        :param api_detail_info_dict: api文档信息
        :return:
        """

        # 递归函数，嵌套处理child_list的参数类型校验
        def recursive_validate_and_convert_param_types(api_param_types, process_test_params, parent_path='',
                                                       _test_point='', _api_id=0):
            for index, param in enumerate(process_test_params):
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('param_key')}" if parent_path else param.get('param_key')
                step_param_type = param.get('param_type')
                if not step_param_type:
                    continue
                api_param_type = api_param_types.get(current_path)
                # 检查参数是否在api_info中定义
                if current_path in api_param_types and \
                        step_param_type != EolinkerConstant.API_INFO_AND_TEST_STEP_PARAM_TYPE_MAP.get(
                        api_param_types.get(current_path)):
                    if step_param_type == EolinkerConstant.OBJECT and api_param_type == EolinkerConstant.ARRAY:
                        # 如果步骤参数类型为object类型，而文档参数格式为array，则将其转换array
                        # print(f"before object_to_array: {process_test_params[index]}")
                        process_test_params[index] = cls.object_to_array(param)
                        # print(f"after object_to_array: {process_test_params[index]}")
                    elif api_param_type in [EolinkerConstant.STRING, EolinkerConstant.CHAR, EolinkerConstant.SHORT,
                                            EolinkerConstant.DATE, EolinkerConstant.DATETIME, EolinkerConstant.BYTE,
                                            EolinkerConstant.NUMBER, EolinkerConstant.INT, EolinkerConstant.FLOAT,
                                            EolinkerConstant.DOUBLE, EolinkerConstant.LONG]:
                        # 如果步骤参数类型为object类型，而文档参数类型为string，则将其转换string
                        param['param_type'] = EolinkerConstant.API_INFO_AND_TEST_STEP_PARAM_TYPE_MAP.get(
                            api_param_types.get(current_path))
                    else:
                        # 通过AI判断是否为测试参数类型异常场景，如果是则跳过参数类型校验异常
                        is_test_param_type_error = ApiTestCaseService.api_test_point_is_test_param_type_error(
                            _test_point,
                            _api_id)
                        if is_test_param_type_error:
                            continue
                        # 步骤参数类型和文档参数类型映射关系不一致，且不符合上述更正情况，则抛出异常
                        logger.error(f"params type error: current_path={current_path} "
                                     f"step_param_type={step_param_type} api_param_type={api_param_type}")
                        raise ParamsTypeError
                # 递归处理子参数
                if 'child_list' in param and param['child_list']:
                    # print(f"current_path in process_test_params={process_test_params}, param_key={param_key}")
                    recursive_validate_and_convert_param_types(api_param_types,
                                                               cls.get_child_list_by_param_key(param.get('param_key'),
                                                                                               process_test_params),
                                                               current_path,
                                                               _test_point,
                                                               _api_id)

        # 遍历test_steps中的参数
        for param_class in PARAM_CLASS_MAP.values():
            # 对于每个test_step，校验并更正参数类型
            for test_step in test_steps:
                api_id = test_step.get('api_id', "")
                test_point = test_step.get('api_name')
                api_info_param_type = cls.get_api_info_param_type(api_detail_info_dict, api_id)
                test_params = test_step['case_data'].get(param_class, [])
                recursive_validate_and_convert_param_types(api_info_param_type, test_params, param_class, test_point,
                                                           api_id)

    @classmethod
    def object_to_array(cls, object_param):
        """
        将object类型转换为array类型
        :param object_param: object类型参数
        :return: array类型参数
        """
        # 创建一个新的字典，用于存放转换后的数据
        array_data_format = {
            "param_type": EolinkerConstant.ARRAY,  # 更改param_type
            "param_key": object_param.get("param_key"),
            "param_info": "",
            "child_list": []
        }

        # 添加一个新的子项到child_list，该子项包含is_arr_item: true
        new_child = {
            "param_type": EolinkerConstant.OBJECT,
            "param_key": "item[0]",
            "param_info": "",
            "is_arr_item": True,  # 添加is_arr_item键
            "child_list": []
        }

        # 将原始error_data_format的child_list中的每个子项添加到new_child的child_list中
        for child in object_param["child_list"]:
            # 创建一个新的字典，用于存放转换后的子项数据
            new_child_item = {
                "param_type": child["param_type"],
                "param_key": child["param_key"],
                "param_info": child["param_info"],
                "child_list": []
            }
            new_child["child_list"].append(new_child_item)

        # 将new_child添加到correct_data_format的child_list中
        array_data_format["child_list"].append(new_child)

        # 输出转换后的数据格式
        return array_data_format

    @staticmethod
    def check_all_require_params_is_existence(test_steps, api_detail_info_dict):
        """
        检查测试步骤中是否包含所有必填参数，通过必填参数数量判断
        :param test_steps: 生成测试用例步骤
        :param api_detail_info_dict: api接口详情信息，{api_id: api_info}
        :return: boolean
        """
        is_existence = True
        for test_step in test_steps:
            api_id = test_step.get("api_id")
            api_info = api_detail_info_dict.get(str(api_id)) if api_detail_info_dict.get(
                str(api_id)) else api_detail_info_dict.get(api_id)
            # 校验body参数必填参数数量
            request_info = api_info.get("requestInfo")
            request_param_not_null_count = max(str(request_info).count("'paramNotNull': '0'"),
                                               str(request_info).count('"paramNotNull": "0"'))
            step_params = test_step.get("case_data", {}).get("params", [])
            step_params_count = str(step_params).count("param_key")
            step_name = test_step.get("api_name", "")
            # 如果测试步骤有exclude_key_name字段，说明步骤为缺参数测试，这里不做校验
            exclude_key_name = ["必填", "不提供"]
            if step_params_count < request_param_not_null_count and all(
                    [key_name not in step_name for key_name in exclude_key_name]):
                logger.info(f'【{step_name}】 【{step_params_count}】'
                            f'【{request_param_not_null_count}】非必填body参数测试步骤中包含必填参数，但数量不正确;')
                is_existence = False
                break
            # 校验Query（url_param）参数缺失场景
            url_param = api_info.get("urlParam")
            url_param_not_null_count = max(str(url_param).count("'paramNotNull': '0'"),
                                           str(url_param).count('"paramNotNull": "0"'))
            step_url_param = test_step.get("case_data", {}).get("url_param", [])
            step_url_param_count = str(step_url_param).count("param_key")
            if step_url_param_count < url_param_not_null_count and all(
                    [key_name not in step_name for key_name in exclude_key_name]):
                logger.info(f'【{step_name}】 【{step_params_count}】'
                            f'【{request_param_not_null_count}】非必填Query（url_param）参数测试步骤中包含必填参数，但数量不正确;')
                is_existence = False
                break
            # 校验REST（restful_param）参数缺失场景
            restful_param = api_info.get("restfulParam")
            restful_param_not_null_count = max(str(restful_param).count("'paramNotNull': '0'"),
                                               str(restful_param).count('"paramNotNull": "0"'))
            step_restful_param = test_step.get("case_data", {}).get("restful_param", [])
            step_restful_param_count = str(step_restful_param).count("param_key")
            if step_restful_param_count < restful_param_not_null_count and all(
                    [key_name not in step_name for key_name in exclude_key_name]):
                logger.info(f'【{step_name}】【{step_params_count}】【{request_param_not_null_count}】'
                            f'非必填REST（restful_param）参数测试步骤中包含必填参数，但数量不正确;')
                is_existence = False
                break

        return is_existence

    @classmethod
    def transform_param_key(cls, param_key, parent_match_rule="", parent_param_info=""):
        parts = param_key.split('.')
        if len(parts) == 1:
            if parent_match_rule and parent_match_rule == cls.match_rule_length_gt and not parent_param_info:
                parent_param_info = cls.param_info_zero
            return {
                "check_exist": "1",
                "param_key": parts[0],
                "param_info": parent_param_info,
                "match_rule": parent_match_rule,
                "child_list": []
            }
        else:
            return {
                "check_exist": "1",
                "param_key": parts[0],
                "param_info": cls.param_info_null,
                "match_rule": cls.match_rule_not_verify,
                "child_list": [cls.transform_param_key('.'.join(parts[1:]), parent_match_rule, parent_param_info)]
            }

    @classmethod
    def transform_match_rule(cls, match_rule):
        new_match_rule = []
        for rule in match_rule:
            if '.' in rule['param_key']:
                match_rule_value = rule.get('match_rule')
                param_info = rule.get('param_info')
                new_rule = cls.transform_param_key(rule.get('param_key'), match_rule_value, param_info)
                new_rule['param_info'] = cls.param_info_null
                new_rule['match_rule'] = cls.match_rule_not_verify
                new_match_rule.append(new_rule)
            else:
                new_rule = rule.copy()
                if rule.get('match_rule') and rule.get('match_rule') == cls.match_rule_length_gt and not rule.get(
                        'param_info'):
                    new_rule['param_info'] = cls.param_info_zero
                new_rule['child_list'] = cls.transform_match_rule(rule.get('child_list', []))
                new_match_rule.append(new_rule)
        return new_match_rule

    @classmethod
    def validate_and_convert_param_key(cls, test_steps):
        """
        目前关于返回体校验部分，多级嵌套参数存在子参数概率性以message.content格式返回，这类针对这类参数做格式转换，转为使用child_list表示
        比如：
        {
            "check_exist": "1",
            "param_key": "message.content",
            "param_info": "0",
            "match_rule": "8",
            "child_list": []
        }
        会被转换为：
        {
            "check_exist": "1",
            "param_key": "message",
            "param_info": "",
            "match_rule": "0",
            "child_list": [
                {
                    "check_exist": "1",
                    "param_key": "content",
                    "param_info": "0",
                    "match_rule": "8",
                    "child_list": []
                }
            ]
        }
        :param test_steps: 测试步骤列表
        :return:
        """
        for step in test_steps:
            if step.get('response_result_verification', {}).get('match_rule'):
                step['response_result_verification']['match_rule'] = cls.transform_match_rule(
                    step['response_result_verification']['match_rule']
                )
        return test_steps

    @classmethod
    def validate_and_convert_response_body(cls, test_steps, test_point, tested_api, display_name=""):
        """
        校验响应体格式，如果响应体格式不符合要求，则抛出异常
        :param test_steps: 测试步骤列表
        :param test_point: 测试点
        :param tested_api: 测试点对应api信息，markdom格式
        :param display_name: 执行人名称
        :return:
        """
        need_check_case = "异常场景"  # 仅异常场景需要做校验
        if need_check_case not in test_point:
            return
        default_abnormal_match_rule = []
        # 对于不包含测试点异常场景响应体描述信息的测试步骤，删除match_rule信息
        for test_step in test_steps:
            # 这里仅对tested_api相关的步骤进行变更，避免前后置脚本也被改了
            if str(test_step.get('api_id')) not in tested_api:
                continue
            logger.info(f"文档未覆盖测试点{test_point}，使用默认响应校验，api_id={test_step.get('api_id')}")
            # 获取响应体校验规则
            match_rule = test_step.get('response_result_verification', {}).get('match_rule')
            if match_rule:
                # 检查文档是否包含测试点异常场景响应体描述信息
                is_cover = ApiTestCaseInspector.api_test_point_doc_inspector(test_point, tested_api, display_name)
                if not is_cover:
                    # 如果文档中不包含测试则使用默认值
                    test_step['response_result_verification']['match_rule'] = default_abnormal_match_rule

    @classmethod
    def get_api_info_array_param_childlist(cls, api_detail_info_dict, api_id):
        """
        获取api_info所有array参数的childlist，由于嵌套参数可能存在同名参数，这里加上parent_path进行区分
        :param api_detail_info_dict: api_detail_info_dict
        :param api_id: api_id
        :return: api_info_param_type
        """
        api_info = api_detail_info_dict.get(str(api_id))
        # 提取api_info中所有的param_key, 参数类型转换和步骤中的类型一致，并支持嵌套childList
        api_info_array_param_childlist = dict()

        # 递归函数，用于填充api_info_array_param_childlist字典
        def fill_api_info_array_param_childlist(sub_param_list, parent_path=""):
            for param in sub_param_list:
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('paramKey')}" if parent_path else param.get('paramKey')
                if param.get('paramType') == EolinkerConstant.ARRAY:
                    api_info_array_param_childlist[current_path] = param.get('childList')
                # 递归检查子参数
                if 'childList' in param:
                    fill_api_info_array_param_childlist(param['childList'], current_path)

        for section in PARAM_CLASS_MAP.keys():
            fill_api_info_array_param_childlist(api_info.get(section, []), PARAM_CLASS_MAP.get(section))

        return api_info_array_param_childlist

    @classmethod
    def check_array_params_childlist_is_existence(cls, test_steps, api_detail_info_dict):
        """
        检查数组参数中是否包含子项
        :param test_steps: 测试步骤列表
        :param api_detail_info_dict: api接口详情信息，{api_id: api_info}
        :return: boolean
        """

        # 递归函数，嵌套处理child_list的参数类型校验，如果array参数中包含子项，而步骤参数中第一个元素类型不是object类型，
        # 则抛出参数缺失异常报错
        def validate_array_param_with_childlist(array_param_childlist_map, process_test_params, parent_path=''):
            for index, param in enumerate(process_test_params):
                # 构建当前参数的唯一路径
                current_path = f"{parent_path}/{param.get('param_key')}" if parent_path else param.get('param_key')
                step_param_type = param.get('param_type')
                if not step_param_type:
                    continue
                # 仅校验array参数
                api_param_childlist = array_param_childlist_map.get(current_path)
                # print(f"current_path={current_path}, array_param_childlist_map={array_param_childlist_map}"
                #       f" step_param_type={step_param_type}")
                # 检查参数是否在api_info中定义
                if current_path in array_param_childlist_map and api_param_childlist \
                        and step_param_type == EolinkerConstant.ARRAY:
                    # 当array参数存在子参数时，校验步骤参数是否为object类型
                    param_childlist = param.get('child_list', [{"param_type": ''}])
                    if param_childlist and len(param_childlist) > 0:
                        param_childlist_type = param.get('child_list', [{"param_type": ''}])[0].get("param_type")
                        if param_childlist_type and param_childlist_type != EolinkerConstant.OBJECT:
                            logger.info(f"【{current_path}】【{step_param_type}】【{param_childlist_type}】"
                                        f"非object类型，步骤参数中第一个元素类型不是object类型，"
                                        f"请检查是否存在子项，api_id={api_id}")
                            raise RequireParamsMissingError

                # 递归处理子参数
                if 'child_list' in param and param['child_list']:
                    # print(f"current_path in process_test_params={process_test_params}, param_key={param_key}")
                    validate_array_param_with_childlist(array_param_childlist_map,
                                                        cls.get_child_list_by_param_key(param.get('param_key'),
                                                                                        process_test_params),
                                                        current_path)

        # 遍历test_steps中的参数
        for param_class in PARAM_CLASS_MAP.values():
            # 对于每个test_step，校验并更正参数类型
            for test_step in test_steps:
                api_id = test_step.get('api_id', "")
                api_info_array_param_childlist = cls.get_api_info_array_param_childlist(api_detail_info_dict, api_id)
                test_params = test_step['case_data'].get(param_class, [])
                validate_array_param_with_childlist(api_info_array_param_childlist, test_params, param_class)

    @classmethod
    def check_and_replace_param_info(cls, params):
        """
        递归函数，用于遍历和修改param列表内的param_info参数值
        针对字符串超长场景让AI返回r"(.*)重复(\d+)次(.*)?"语义话格式，避免AI返回的重复信息过长触发复读机机制
        :param params: 测试步骤参数列表
        :return:
        """
        for param in params:
            # 检查param_info是否满足正则表达式模式
            match = re.search(cls.long_param_info_pattern, param['param_info'])
            if 'param_info' in param and match:
                # 替换param_info的值
                param['param_info'] = match.group(1) * int(match.group(2)) + match.group(3)
            # 如果存在child_list，递归调用函数处理子列表
            if 'child_list' in param and param['child_list']:
                cls.check_and_replace_param_info(param['child_list'])
        return params

    @classmethod
    def check_and_replace_step_param_info(cls, test_steps):
        """
        递归函数，用于遍历和修改test_steps的参数列表内的param_info参数值
        :param test_steps: 测试步骤参数列表
        :return:
        """
        for step in test_steps:
            case_data = step.get("case_data", {})
            url_param = case_data.get("url_param", [])
            case_data["url_param"] = cls.check_and_replace_param_info(url_param)
            restful_param = case_data.get("restful_param", [])
            case_data["restful_param"] = cls.check_and_replace_param_info(restful_param)
            params = case_data.get("params", [])
            case_data["params"] = cls.check_and_replace_param_info(params)
