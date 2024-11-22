#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/3/18 21:00
"""


class EolinkerConstant:
    STRING = "0"
    STRING_NAME = "string"
    JSON = "2"
    JSON_NAME = "json"
    INT = "3"
    INT_NAME = "int"
    FLOAT = "4"
    FLOAT_NAME = "float"
    DOUBLE = "5"
    DOUBLE_NAME = "double"
    DATE = "6"
    DATE_NAME = "date"
    DATETIME = "7"
    DATETIME_NAME = "datetime"
    BOOLEAN = "8"
    BOOLEAN_NAME = "boolean"
    BYTE = "9"
    BYTE_NAME = "byte"
    SHORT = "10"
    SHORT_NAME = "short"
    LONG = "11"
    LONG_NAME = "long"
    ARRAY = "12"
    ARRAY_NAME = "array"
    OBJECT = "13"
    OBJECT_NAME = "object"
    NUMBER = "14"
    NUMBER_NAME = "number"
    NULL_ = "15"
    NULL_NAME = "null"
    CHAR = "char"
    CHAR_NAME = "char"

    # 参数类型常量
    PARAM_TYPE_LIST = {
        STRING: STRING_NAME,
        JSON: JSON_NAME,
        INT: INT_NAME,
        FLOAT: FLOAT_NAME,
        DOUBLE: DOUBLE_NAME,
        DATE: DATE_NAME,
        DATETIME: DATETIME_NAME,
        BOOLEAN: BOOLEAN_NAME,
        BYTE: BYTE_NAME,
        SHORT: SHORT_NAME,
        LONG: LONG_NAME,
        ARRAY: ARRAY_NAME,
        OBJECT: OBJECT_NAME,
        NUMBER: NUMBER_NAME,
        NULL_: NULL_NAME,
        CHAR: CHAR_NAME,
    }
    PYTEST_HEADER = "\n\n# pytest格式测试用例列表："
    NOT_PARAM_ERROR = "当前仅支持包含query或body参数接口，请先确认接口是否包含此类参数后重试！"
    API_INFO_AND_TEST_STEP_PARAM_TYPE_MAP = {
        STRING: STRING,
        CHAR: STRING,
        DATE: STRING,
        DATETIME: STRING,
        BYTE: STRING,
        NUMBER: NUMBER,
        INT: NUMBER,
        FLOAT: NUMBER,
        DOUBLE: NUMBER,
        SHORT: NUMBER,
        LONG: NUMBER,
        BOOLEAN: BOOLEAN,
        JSON: OBJECT,
        ARRAY: ARRAY,
        OBJECT: OBJECT,
        NULL_: NULL_
    }  # api文档和测试用例步骤中参数类型的映射关系，测试步骤中的参数类型比文档中的参数类型要少一些


# 请求方法
REQUEST_TYPE = {
    0: "POST",
    1: "GET",
    2: "PUT",
    3: "DELETE",
    4: "HEAD",
    5: "OPTIONS",
    6: "PATCH"
}

# 请求体/响应体如果是json类型时表示json类型是数组或者对象
API_PARAM_JSON_TYPE = {
    0: "Object",
    1: "Array"
}


# 请求体类型
class ApiRequestParamType:
    form_data_key = 0
    form_data_value = "Form-data"
    raw_key = 1
    raw_value = "Raw"
    json_key = 2
    json_value = "JSON"
    xml_key = 3
    xml_value = "XML"
    binary_key = 4
    binary_value = "Binary"

    MAP = {
        form_data_key: form_data_value,
        raw_key: raw_value,
        json_key: json_value,
        xml_key: xml_value,
        binary_key: binary_value,
    }


# 响应体类型
class ApiResponseType:
    json_key = 0
    json_value = "JSON"
    xml_key = 1
    xml_value = "XML"
    raw_key = 2
    raw_value = "Raw"
    binary_key = 3
    binary_value = "Binary"

    MAP = {
        json_key: json_value,
        xml_key: xml_value,
        raw_key: raw_value,
        binary_key: binary_value,
    }


class ApiMarkdownKeyword:
    PARAMS = "params请求参数"
    URL_PARAM = "url_param参数"
    RESTFUL_PARAM = "restful_param参数"
    RESPONSE = "响应内容"
    RESULT = "返回结果"
    API_ID = "API ID"
    API_NOTE = "API接口详细说明"


PARAM_CLASS_MAP = {
    "requestInfo": "params",
    "urlParam": "url_param",
    "restfulParam": "restful_param"
}  # 前后端接口返回的参数类型名称映射表
