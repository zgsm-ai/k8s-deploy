#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/3/18 10:10
"""
import re
import logging

from common.eolinker_constant import EolinkerConstant, REQUEST_TYPE, API_PARAM_JSON_TYPE, ApiRequestParamType, \
    ApiResponseType, ApiMarkdownKeyword
from third_platform.eolinker.api_studio_manager import ApiStudioManager
from common.exception.exceptions import ApiDocsError


class ApiHelper:

    def __init__(self, api_info):
        self.api_info = api_info
        self.restore_param_info()

    def get_raw_api_info(self):
        return self.api_info

    def restore_param_info(self):
        # 重新存储参数信息，把参数结构体id替换成实际的参数结构体
        request_info = self.request_info
        default_result_info = self.default_result_info

        def replace_structure(params):
            params_list = []

            if not params:
                return []

            for index, param in enumerate(params):
                if "childList" in param:
                    # 递归替换结构体
                    child_list = param.get("childList", [])
                    param["childList"] = replace_structure(child_list)
                is_extend = False
                if "structureID" in param:
                    structure_id = param["structureID"]
                    if structure_id:
                        # structure_id有可能是字符串或者数字,eolinker文档api返回的
                        s = self.data_structure_list.get(structure_id, {}) \
                            or self.data_structure_list.get(str(structure_id), {})
                        if s:
                            structure_data = s.get("structureData", [])
                            params_list.extend(structure_data)
                            is_extend = True
                if not is_extend:
                    params_list.append(param)
            return params_list

        self.api_info['requestInfo'] = replace_structure(request_info)
        default_result_info['paramList'] = replace_structure(default_result_info['paramList'])

    @property
    def api_url(self):
        # 去掉url的参数信息，部分文档不规范带上参数信息，会导致出现重复传参情况
        return self.base_info.get('apiURI', '').split('?')[0]

    @property
    def header_info(self):
        return self.api_info.get('headerInfo', '')

    @property
    def request_method(self):
        return REQUEST_TYPE.get(self.base_info.get('apiRequestType', "0"), "")

    @property
    def base_info(self):
        return self.api_info['baseInfo']

    @property
    def request_info(self):
        return self.api_info.get("requestInfo", [])

    @property
    def result_info(self):
        return self.api_info.get("resultInfo", [])

    @property
    def data_structure_list(self):
        # 参数中如果引用了固定的数据结构,需要通过id在 dataStructureList 中进行找到并还原
        return self.api_info.get("dataStructureList", {})

    @property
    def default_result_info(self):
        # 获取用户设置的默认结果，result_info里面可能有多个
        default_result_info = None
        for result in self.result_info:
            if result.get('isDefault', 0) == 1:
                default_result_info = result
                break
        # default_result_info如果为None，说明接口返回的结果有问题
        return default_result_info

    def to_markdown(self, with_header=True):
        base_info = self.base_info
        request_info = self.request_info
        url_param = self.api_info['urlParam']
        restful_param = self.api_info['restfulParam']
        api_id = self.api_info.get('apiID', 0)

        # API基本信息
        api_name = base_info.get('apiName', '')
        api_path = self.api_url
        api_protocol = 'HTTP' if base_info.get('apiProtocol', 0) == 0 else 'HTTPS'
        api_method = REQUEST_TYPE.get(base_info.get('apiRequestType', "0"), "")
        api_note = base_info.get('apiNoteRaw', '')
        header_info = self.header_info

        # Markdown文档
        markdown = f"#### {api_name}\n##### 接口信息\n\n"
        markdown += f"**API ID**\n{api_id}\n\n"
        markdown += f"**API Path**\n{api_path}\n\n"
        markdown += f"**请求协议**\n{api_protocol}\n\n"
        markdown += f"**请求方法**\n{api_method}\n\n"

        # 请求头部
        if header_info and with_header:
            markdown += "**请求头部**：\n"
            markdown += self._format_header_table(header_info)

        # params请求参数
        # 不管有没有参数值，参数头信息都需要固定添加，并且头信息和期望返回的参数名称信息保持一致，
        # 避免出现参数类型混淆问题（如REST参数识别为params参数）
        markdown += f"**{ApiMarkdownKeyword.PARAMS}**：\n"
        if request_info:
            request_param_type = ApiRequestParamType.MAP.get(base_info.get('apiRequestParamType', 0), "")
            request_param_json_type = API_PARAM_JSON_TYPE.get(base_info.get('apiRequestParamJsonType', 0), "")
            markdown += f"{request_param_type}\n" \
                        f"{request_param_json_type if request_param_type == ApiRequestParamType.json_value else ''}\n\n"
            markdown += self._format_params_table(request_info)
        else:
            markdown += "无\n\n"

        # Query(url_param)参数
        markdown += f"**{ApiMarkdownKeyword.URL_PARAM}**：\n"
        if url_param:
            markdown += self._format_params_table(url_param)
        else:
            markdown += "无\n\n"

        # REST(restful_param)参数
        markdown += f"**{ApiMarkdownKeyword.RESTFUL_PARAM}**：\n"
        if restful_param:
            markdown += self._format_params_table(restful_param)
        else:
            markdown += "无\n\n"

        # 响应内容
        result_info = self.result_info
        index = 0
        for result_info_item in result_info:
            index += 1
            # markdown += f"**{ApiMarkdownKeyword.RESPONSE}**：\n\n"
            response_name = result_info_item.get("responseName", "")
            response_code = result_info_item.get("responseCode", "")
            result_str = f"结果名称:{response_name}\nHTTP状态码:{response_code}"

            response_type = result_info_item.get("responseType", "")
            response_type = ApiResponseType.MAP.get(response_type, "")
            param_json_type = result_info_item.get("paramJsonType", "")
            param_json_type = API_PARAM_JSON_TYPE.get(param_json_type, "")
            if response_type == ApiResponseType.json_value:
                result_type_str = f"{response_type} -- {param_json_type}\n"
            else:
                result_type_str = f"{response_type}\n"
            result_param_list = result_info_item.get("paramList", [])
            markdown += f"**{ApiMarkdownKeyword.RESULT}-{index}**\n{result_str}\n响应类型:{result_type_str}"
            markdown += "响应体:\n"
            markdown += self._format_params_table(result_param_list)

        # 详细说明
        if api_note:
            markdown += f"**{ApiMarkdownKeyword.API_NOTE}**：\n{api_note}\n"
        return markdown

    def to_dict(self):
        request_info = self.request_info
        url_param = self.api_info.get('urlParam')
        restful_param = self.api_info.get('restfulParam')
        header_info = self.header_info

        # 请求头部
        api_header_params = self._format_header_list(header_info) if header_info else []

        # 请求参数
        if request_info:
            api_request_params = self._format_params_list(request_info)
        else:
            api_request_params = []

        # Query参数
        api_url_params = self._format_params_list(url_param) if url_param else []

        # REST参数
        api_restful_params = self._format_params_list(restful_param) if restful_param else []

        # 响应内容
        default_result_info = self.default_result_info
        result_param_list = default_result_info.get("paramList", [])
        api_result_params = self._format_params_list(result_param_list)

        # 组装返回值
        api_params = {
            'api_header_params': api_header_params,
            'api_request_params': api_request_params,
            'api_url_params': api_url_params,
            'api_restful_params': api_restful_params,
            'api_result_params': api_result_params
        }

        return api_params

    @staticmethod
    def _format_header_table(headers_info):
        tb = "| 头部标签 | 必填 | 说明 | 类型 | 值可能性 | 限制 | 示例 | \n"
        tb += "| :------------ | :------------ | :------------ | :------------ " \
              "| :------------ | :------------ | :------------ |\n"
        for header in headers_info:
            header_name = header.get('headerName', '')
            param_name = header.get('paramName', '')
            param_not_null = '是' if header.get('paramNotNull', '0') == '0' else '否'
            param_type = header.get('paramType', '')
            param_type = EolinkerConstant.PARAM_TYPE_LIST.get(param_type, '')
            param_value_list = ', '.join(
                [f"[{str(value.get('value', ''))}]" for value in header['paramValueList']]) \
                if 'paramValueList' in header and isinstance(header['paramValueList'], list) else ''
            param_limit = header.get('paramLimit', '')
            header_value = header.get('headerValue', '')
            tb += f"|{header_name}|{param_not_null}|{param_name}|{param_type}|{param_value_list}|" \
                  f"{param_limit}|{header_value}|\n"
        return tb

    @staticmethod
    def _format_header_list(headers_info):
        ls = []
        for header in headers_info:
            header_name = header.get('headerName', '')
            param_name = header.get('paramName', '')
            param_not_null = '是' if header.get('paramNotNull', '0') == '0' else '否'
            param_type = header.get('paramType', '')
            param_type = EolinkerConstant.PARAM_TYPE_LIST.get(param_type, '')
            param_value_list = ', '.join(
                [f"[{str(value.get('value', ''))}]" for value in header['paramValueList']]) \
                if 'paramValueList' in header and isinstance(header['paramValueList'], list) else ''
            param_limit = header.get('paramLimit', '')
            header_value = header.get('headerValue', '')
            ls.append(f"|{header_name}|{param_not_null}|{param_name}|{param_type}|{param_value_list}|"
                      f"{param_limit}|{header_value}|\n")
        return ls

    @staticmethod
    def _format_params_table(params):
        table = "| 参数名 | 说明 | 必填 | 类型 | 值可能性 |  限制 | 示例 |\n"
        table += "| :------------ | :------------ | :------------ " \
                 "| :------------ | :------------ | :------------ | :------------ |\n"

        def get_param_not_null(parent_param):
            """
            获取必填参数值，只要子参数中有一个必填，则父参数必填
            """
            param_not_null_key = 'paramNotNull'
            param_not_null_f_value = '0'
            param_not_null_f = '是'  # 参数非空属性为false表示参数必填
            param_not_null_t = '否'  # 参数非空属性为true表示参数非必填
            # 检查当前参数是否必填
            if parent_param.get(param_not_null_key, param_not_null_f_value) == param_not_null_f_value:
                return param_not_null_f

            # 递归检查子参数
            def check_child_params(child_params):
                for child in child_params:
                    # 如果子参数必填，返回 '是'
                    if child.get(param_not_null_key, param_not_null_f_value) == param_not_null_f_value:
                        return param_not_null_f
                    # 如果子参数有自己的子参数，递归检查
                    if 'childList' in child:
                        if check_child_params(child['childList']) == param_not_null_f:
                            return param_not_null_f
                return param_not_null_t  # 如果所有子参数都不必填，返回 '否'

            # 检查当前参数的子参数
            child_list = parent_param.get('childList', [])
            return check_child_params(child_list)

        def handle_params(tb, ps, parent_key='', parent_type=''):
            for param in ps:
                param_name = param.get('paramName', '')
                param_key = param.get('paramKey', '')
                if parent_type and parent_type == EolinkerConstant.ARRAY and parent_key \
                        and not parent_key.endswith('[]'):
                    # 对于array类型参数添加数组下标，与object类型参数进行区分
                    parent_key = f"{parent_key}[]"
                param_key = f"{parent_key}>>{param_key}" if parent_key else param_key
                param_not_null = get_param_not_null(param)
                p_type = param.get('paramType', '')
                param_type = EolinkerConstant.PARAM_TYPE_LIST.get(p_type, '')
                param_limit = param.get('paramLimit', '')
                param_value = param.get('paramValue', '')
                param_value_list = ', '.join(
                    [f"[{str(value.get('value', ''))}]" for value in param['paramValueList']]) \
                    if 'paramValueList' in param and isinstance(param['paramValueList'], list) else ''
                tb += f"|{param_key}|{param_name}|{param_not_null}|[{param_type}]" \
                      f"|{param_value_list}|{param_limit}|{param_value}|\n"
                child_list = param.get('childList', [])
                if child_list:
                    param_type = param.get('paramType', '')
                    tb = handle_params(tb, child_list, param_key, param_type)
            return tb

        table = handle_params(table, params)
        table += "\n"
        return table

    @staticmethod
    def _format_params_list(params):
        ls = []

        def handle_params(ls_inner, ps, parent_key=''):
            for param in ps:
                param_name = param.get('paramName', '')
                param_key = param.get('paramKey', '')
                param_key = f"{parent_key}>>{param_key}" if parent_key else param_key
                param_not_null = '是' if param.get('paramNotNull', '0') == '0' else '否'
                p_type = param.get('paramType', '')
                param_type = EolinkerConstant.PARAM_TYPE_LIST.get(p_type, '')
                param_limit = param.get('paramLimit', '')
                param_value = param.get('paramValue', '')
                param_value_list = ', '.join(
                    [f"[{str(value.get('value', ''))}]" for value in param['paramValueList']]) \
                    if 'paramValueList' in param and isinstance(param['paramValueList'], list) else ''
                ls_inner.append(f"|{param_key}|{param_name}|{param_not_null}|[{param_type}]"
                                f"|{param_value_list}|{param_limit}|{param_value}|\n")
                child_list = param.get('childList', [])
                if child_list:
                    ls_inner = handle_params(ls_inner, child_list, param_key)
            return ls_inner

        ls = handle_params(ls, params)
        return ls

    @staticmethod
    def get_all_api_info(api_list, space_id, authorization, origin):
        """
        获取所有API信息，返回包含所有API信息的字典
        :param api_list: 包含api id和项目id的列表信息
        :param space_id: 空间ID
        :param authorization: 授权信息
        :param origin: 来源
        return {api_id: api_info}
        """
        api_info_dict = {}
        for api in api_list:
            api_id = api.get("api_id")
            project_id = api.get("project_id")
            api_info = api_info_dict.get(api_id)
            if api_info:
                continue
            api_info = ApiStudioManager.get_api_info_pro(space_id, project_id, api_id, authorization, origin)
            if api_info:
                # 不同项目下的api_id不会重复，这里通过此方式获取接口信息可以避免重复获取
                api_helper = ApiHelper(api_info)  # 使用ApiHelper统一api_info的格式，比如对structure数据的处理
                api_info_dict[str(api_id)] = api_helper.api_info

        return api_info_dict

    @staticmethod
    def get_markdown_by_api_id(api_id, api_detail_info_dict: dict, with_header=True):
        api_info = api_detail_info_dict.get(str(api_id))
        if not api_info:
            logging.error(f"获取API pro详情信息失败: {api_info}")
            raise ApiDocsError(f"获取API文档详情信息失败: {api_id}")
        h = ApiHelper(api_info)
        return h.to_markdown(with_header)

    @staticmethod
    def get_compare(space_id, project_id, api_id, current_history_id, old_history_id, authorization, origin):
        """
        获取 api 版本对比信息
        :param space_id: 空间 id
        :param project_id: 项目 id
        :param api_id: api id
        :param current_history_id: 新 api 版本的版本 id
        :param old_history_id: 旧 api 版本的版本 id
        :param authorization: 鉴权 key
        :param origin:
        :return: 元组 (old_api_params, new_api_params)。其中 api 参数已经被转换为 dict，具体格式参考 ApiHelper.to_dict() 方法。
        """

        old_api_info, new_api_info = ApiStudioManager.get_api_compare(space_id, project_id, api_id,
                                                                      cur_version_id=current_history_id,
                                                                      old_history_id=old_history_id,
                                                                      authorization=authorization, origin=origin)
        old_api_params = ApiHelper(old_api_info).to_dict()
        new_api_params = ApiHelper(new_api_info).to_dict()
        return old_api_params, new_api_params

    @staticmethod
    def get_increment_markdown(api_id, old_api_params, new_api_params):
        # 参数增量 dict
        is_modified = False
        api_info_increment = {}
        for key in old_api_params.keys():
            if old_api_params[key] != new_api_params[key]:
                api_info_increment[key] = list(set(new_api_params[key]) - set(old_api_params[key]))
                is_modified = True

        if is_modified:
            api_info_increment['api_id'] = api_id

        md_increment = ApiHelper.parse_api_markdown_from_dict(api_info_increment)
        return md_increment

    @staticmethod
    def parse_api_markdown_from_dict(api_info):

        table_header_head = "| 头部标签 | 必填 | 说明 | 类型 | 值可能性 | 限制 | 示例 | \n" \
                            "| :------------ | :------------ | :------------ | :------------ " \
                            "| :------------ | :------------ | :------------ |\n"

        table_param_head = "| 参数名 | 说明 | 必填 | 类型 | 值可能性 |  限制 | 示例 | \n" \
                           "| :------------ | :------------ | :------------ | :------------ " \
                           "| :------------ | :------------ | :------------ |\n"

        sections = [
            ("请求头部", api_info.get('api_header_params'), table_header_head),
            ("请求参数", api_info.get('api_request_params'), table_param_head),
            ("Query参数", api_info.get('api_url_params'), table_param_head),
            ("Rest参数", api_info.get('api_restful_params'), table_param_head),
            ("响应内容", api_info.get('api_result_params'), table_param_head),
        ]

        parsed_md = f"**API ID**\n{api_info.get('api_id')}\n\n"
        for title, content, table_header in sections:
            if content and len(content) > 0:
                parsed_md += f"**{title}**：\n" + table_header + ''.join(content) + "\n"

        return parsed_md.strip()

    @staticmethod
    def parse_api_from_markdown(md):
        api_request_type_dict = {
            "POST": "0",
            "GET": "1",
            "PUT": "2",
            "DELETE": "3",
            "HEAD": "4",
            "OPTIONS": "5",
            "PATCH": "6"
        }
        api_protocol_dict = {
            "HTTP": 0,
            "HTTPS": 1
        }
        api_pattern = re.compile(
            r'\*\*API ID\*\*\s*\n(\d+).*?\*\*请求协议\*\*\s*\n(\w+).*?\*\*请求方法\*\*\s*\n(\w+)',
            re.DOTALL
        )

        matches = api_pattern.findall(md)

        api_dict = {}
        for api_id, api_protocol, api_request_type in matches:
            if api_request_type in api_request_type_dict and api_protocol in api_protocol_dict:
                api_dict[int(api_id)] = (api_request_type_dict[api_request_type], api_protocol_dict[api_protocol])
            else:
                logging.error(f"解析API信息失败, markdown = {md}")

        return api_dict

    @staticmethod
    def build_param_lookup(test_steps):
        """
        建立参数查找表，以一个格式为(api_id, param_key)的元组唯一地指代一个参数。
        :param test_steps: 测试步骤
        :return: 参数查找表，list
        """
        param_key_list = ["url_params", "restful_param", "params"]
        param_lookup = []

        for test_step in test_steps["test_steps"]:
            api_id = test_step.get("api_id")
            case_data = test_step.get("case_data")
            headers = case_data.get('headers')

            for header in headers:
                param_lookup.append((str(api_id), header.get("header_name")))

            for param_key in param_key_list:
                params = case_data.get(param_key)
                if not params:
                    continue
                for param in params:
                    param_lookup.append((str(api_id), param.get("param_key")))

        return param_lookup


class EolinkerDataHandler:
    # 引用参数名映射
    REF_PARAM_NAME_MMAP = {
        "response": "response",
        "params": "requestBody",
        "url_param": "queryParams",
        "restful_param": "restParams"
    }

    @classmethod
    def deal_param_info(cls, params_obj, step_num_id_dict):
        """
        处理关联参数,需要递归处理
        :param params_obj: 参数数据字典
        :param step_num_id_dict: step下标和id对应字典
        :return: 参数数据字典
        """
        param_info = params_obj.get("param_info", "")
        child_list = params_obj.get("child_list", [])
        if isinstance(param_info, str):
            param_info = cls.transfer_relate_param_info_str(step_num_id_dict, param_info)

        # 如果是列表则把每个元素都进行关联参数处理后，把数组转成字符串
        elif isinstance(param_info, list):
            param_info = cls.transfer_list_param(param_info, step_num_id_dict)
        else:
            param_info = str(param_info)

        params_obj["param_info"] = param_info

        if child_list:
            for child_list_item in child_list:
                cls.deal_param_info(params_obj=child_list_item, step_num_id_dict=step_num_id_dict)

    @classmethod
    def transfer_list_param(cls, param_list, step_num_id_dict):
        res_str = "["
        # 拼接成数组字符串发给eolinker
        for index, item in enumerate(param_list):
            res = cls.transfer_relate_param_info_str(step_num_id_dict, item)
            # 第一个元素不用加逗号
            comma = '' if index == 0 else ','
            if isinstance(res, str) and res == item:
                # 如果是没有转换过的字符串,手动加上引号
                res_str += f'{comma}"{res}"'
            else:
                # 其他的结构都直接拼接成字符串
                res_str += f'{comma}{res}'
        res_str += "]"
        return res_str

    @classmethod
    def transfer_relate_param_info_str(cls, step_num_id_dict, param_info):
        if isinstance(param_info, str) and 'step[' in param_info:
            parsed_list = cls.parse_relate_params_str(param_info)
            if parsed_list:
                step_num = parsed_list[1]
                data_area = parsed_list[2]
                # 参数名称转换
                data_area = cls.REF_PARAM_NAME_MMAP.get(data_area, data_area)
                step_eo_link_id = step_num_id_dict.get(step_num)
                if step_eo_link_id:
                    new_param_info = ''.join(f'["{item}"]' for item in parsed_list[3:])
                    new_param_info = f'<{data_area}["{step_eo_link_id}"]{new_param_info}>'
                    return new_param_info
        return param_info

    @staticmethod
    def parse_relate_params_str(input_str):
        """
        处理关联参数字符串
        :param input_str: 输入关联字符串 示例：step[0]["response"]["data"]["id"]
        :return: ['step', 0, 'response', 'data', 'id']
        """
        # 使用正则表达式来匹配所有的键和索引
        pattern = r"\[?['\"]?([^\[\]'\"]+)['\"]?\]?"
        matches = re.findall(pattern, input_str)
        if len(matches) < 4:
            return False

        # 将匹配到的字符串转换为正确的类型（字符串或整数）
        parsed_list = [int(match) if match.isdigit() else match for match in matches]
        return parsed_list
