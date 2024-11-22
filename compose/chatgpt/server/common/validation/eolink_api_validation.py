from pydantic import BaseModel, Field
from typing import List, Optional, ForwardRef, Union
import json

# ==============single_case_edit  start 由于数据嵌套从下往上看比较合适==============
# 定义一个类型别名，包含param_info可以接受的类型
ParamInfoType = Union[str, bool, int]


class BasicAuth(BaseModel):
    username: str
    password: str


class JwtAuth(BaseModel):
    typ: Optional[str] = "JWT"
    alg: Optional[str] = "HS256"
    payload: Optional[str] = None
    secret_salt: str
    position: Optional[str] = "header"
    token_name: str
    is_bearer: int  # 使用 Bearer Token，在 token 前加入 Bearer 前缀


# 权限校验
class _Auth(BaseModel):
    status: Optional[int] = 0  # 0：无 1：basicAuth 2：JWt
    basic_auth: Optional[BasicAuth] = None  # 当status等于1是需要传，反之不需要传
    jwt_auth: Optional[JwtAuth] = None  # 当status等于2是需要传，反之不需要传


# 请求头部
class _Header(BaseModel):
    header_name: str  # 参数名
    header_value: Optional[str] = None  # 参数值
    checkbox: Optional[bool] = True  # 是否选中


# rest参数
class RestfulParam(BaseModel):
    param_key: str  # 参数名
    param_info: Optional[ParamInfoType] = None  # 参数值
    param_name: Optional[str] = None  # 说明
    checkbox: Optional[bool] = True  # 是否选中


# url参数
class UrlParam(BaseModel):
    param_key: str  # 参数名
    param_info: Optional[ParamInfoType] = None  # 参数值
    param_name: Optional[str] = None  # 说明
    checkbox: Optional[bool] = True  # 是否选中


class _Param(BaseModel):
    param_type: str  # 参数类型
    param_key: str  # 参数名
    param_info: Optional[ParamInfoType] = None  # 参数值
    param_name: Optional[str] = None  # 说明
    checkbox: Optional[bool] = True  # 是否选中
    is_arr_item: Optional[bool] = False  # 是否为array数组元素
    child_list: Optional[List[ForwardRef('_Param')]] = []  # 子字段，字段和父级一样


# 在模型类定义之后，你需要调用model_rebuild()方法来解决前向引用
_Param.model_rebuild()


# 脚本
class _Script(BaseModel):
    before: Optional[str] = None
    after: Optional[str] = None


class StatusCodeVerification(BaseModel):
    check_status: Optional[bool] = True  # 是否检验状态码
    status_code: Optional[int] = 200


class JsonResultVerification(BaseModel):
    result_type: Optional[str] = None  # json结果类型
    match_rule: Optional[str] = None  # 数组校验的第几个元素


class MatchRule(BaseModel):
    param_key: str  # 参数名
    param_info: Optional[ParamInfoType] = None  # 预期结果
    match_rule: Optional[str] = None  # 内容校验
    check_exist: Optional[str] = None  # 是否必含
    check_param_type: Optional[str] = None  # 是否校验类型
    param_type: Optional[str] = None  # 参数类型
    child_list: Optional[List[ForwardRef('MatchRule')]] = []  # 子字段，字段和父级一样


# 在模型类定义之后，你需要调用model_rebuild()方法来解决前向引用
MatchRule.model_rebuild()


# 响应体验证
class ResponseResultVerification(BaseModel):
    check_status: Optional[bool] = False  # 是否检验结果
    param_match: Optional[str] = None  # 校验方式
    json_result_verification: Optional[JsonResultVerification] = False  # json
    match_rule: List[MatchRule] = []


# 响应时间验证
class ResponseTimeVerification(BaseModel):
    check_status: Optional[bool] = False  # 是否开启检验超时
    project_timeout_setting: Optional[str] = "customize"  # 超时设置
    timeout_limit: Optional[str] = "5000"  # 时间设置（毫秒ms）
    timeout_limit_type: Optional[str] = "totalTime"  # 计时依据


# 提取结果参数
class ResultParam(BaseModel):
    param_type: int  # 类型
    param_key: str  # 参数名
    param_info: Optional[ParamInfoType] = None  # 参数描述


# 提起响应头参数
class ResponseHeader(BaseModel):
    header_name: str  # 参数
    param_name: Optional[str] = None  # 描述


# 响应头验证
class ResponseHeaderVerification(BaseModel):
    check_status: Optional[bool] = False  # 是否验证
    match_rule: Optional[List[_Header]] = []


# 说明
class CustomInfo(BaseModel):
    caseNote: Optional[str] = ""


# 高级设置
class AdvancedSetting(BaseModel):
    request_redirect: Optional[int] = 1  # 自动跟随请求重定向
    check_ssl: Optional[int] = 0  # 验证 SSL 证书
    sende_eo_token: Optional[int] = 0  # 发送 Eolink Token 头部
    send_nocache_token: Optional[int] = 0  # 发送 no-cache 头部（cache-control：no-cache）


class CaseData(BaseModel):
    auth: Optional[_Auth] = _Auth(
        status=0
    )  # 权限校验
    headers: Optional[List[_Header]] = []  # 请求头部
    restful_param: Optional[List[RestfulParam]] = []  # rest参数
    url_param: Optional[List[UrlParam]] = []  # query参数
    url: Optional[str] = None  # url
    params: List[_Param] = []  # 请求体
    api_request_type: Optional[str] = "0"  # 请求方式 0post 1get 2put 3delete 4head 5options 6patch
    script: Optional[_Script] = _Script(
        before="",
        after=""
    )  # 脚本
    keep_going: Optional[bool] = True  # 当前步骤出错或未通过时，依然执行下一个步骤
    message_encoding: Optional[str] = "utf-8"  # 报文编码格式
    request_type: Optional[str] = "2"  # 请求头类型 0form-data 1raw 2json 3xml
    api_protocol: Optional[str] = "0"  # 协议类型 0http 1https


# 编辑用例测试步骤的全部数据
class SingleCaseEditReqData(BaseModel):
    conn_id: int  # 步骤id
    case_id: int  # 用例id
    case_data: CaseData  # 请求参数
    status_code_verification: Optional[StatusCodeVerification] = StatusCodeVerification(
        check_status=False,
        status_code=200
    )  # 状态码验证 非必填
    response_result_verification: Optional[ResponseResultVerification] = ResponseResultVerification(
        check_status=False,
        param_match="json",
        json_result_verification=JsonResultVerification(
            result_type="object",
            match_rule="allElement"
        ),
        match_rule=[]
    )  # 响应体验证 非必填
    # response_time_verification: Optional[ResponseTimeVerification] = ResponseTimeVerification(
    #     check_status=True,
    #     project_timeout_setting="project",
    #     timeout_limit="5000",
    #     timeout_limit_type="totalTime"
    # )  # 响应时间验证 非必填
    api_name: Optional[str] = None  # 接口名称
    api_url: Optional[str] = None  # 接口url
    # result_param: Optional[List[ResultParam]] = []  # 提取结果参数，非必填
    # response_header: Optional[List[ResponseHeader]] = []  # 提起响应头参数，非必填
    response_header_verification: Optional[ResponseHeaderVerification] = ResponseHeaderVerification(
        check_status=False,
        match_rule=[]
    )  # 响应头验证 非必填
    # judge_setting: Optional[int] = Field(default=1, description="当某一校验规则判断为失败时，依然判断其余规则")
    # result_param_json_type: Optional[str] = "object"  # 提取结果的json类型
    # result_param_type: Optional[str] = "json"  # 参数提取方式
    # delay_time: Optional[int] = 0  # 延迟执行时间（单位毫秒）
    # step_type: Optional[int] = 0  # 步骤类型(0:添加api请求 1：添加脚本)
    # custom_info: Optional[CustomInfo] = CustomInfo(
    #     case_note="",
    # )  # 说明
    api_protocol: Optional[int] = 0  # 接口协议（0：http 1：https）
    # advanced_setting: Optional[AdvancedSetting] = AdvancedSetting(
    #     request_redirect=1,
    #     check_ssl=0,
    #     sende_eo_token=1,
    #     send_nocache_token=0,
    # )  # 高级设置


# 编辑用例测试步骤（编辑api请求）
class SingleCaseEditReqBody(BaseModel):
    data: SingleCaseEditReqData  # 全部数据
    space_id: str  # 工作空间key
    project_id: str  # 项目哈希key
    module: int = Field(default=0, description="用例类型 默认普通用例，0普通用例，1模板用例")


# ===========================single_case_edit  end=============================

# ==============api_management_test_case_edit  start 结构和single_case_edit的类似==============
# 编辑api管理页面的测试用例（编辑api请求）
class ApiManagemenTestCaseEditReqBody(BaseModel):
    space_id: str  # 工作空间key
    project_id: str  # 项目哈希key
    case_id: Optional[int] = None  # 用例id，创建接口不需要id，编辑接口才需要id
    case_data: CaseData  # 请求参数
    status_code_verification: Optional[StatusCodeVerification] = StatusCodeVerification(
        check_status=False,
        status_code=200
    )  # 状态码验证 非必填
    response_result_verification: Optional[ResponseResultVerification] = ResponseResultVerification(
        check_status=False,
        param_match="json",
        json_result_verification=JsonResultVerification(
            result_type="object",
            match_rule="allElement"
        ),
        match_rule=[]
    )  # 响应体验证 非必填
    response_header_verification: Optional[ResponseHeaderVerification] = ResponseHeaderVerification(
        check_status=False,
        match_rule=[]
    )


# ===========================api_management_test_case_edit  end=============================

def format_data_to_eolinker_web(raw_data):
    # 将eolinker后端参数转换为前端参数
    eolinker_web_req_data = json.dumps(raw_data)
    web_to_backend_key_map = {"check_param_type": "checkParamType",
                              "json_result_verification": "jsonResultVerification",
                              "project_timeout_setting": "projectTimeoutSetting",
                              "secret_salt": "secretSalt",
                              "token_name": "tokenName",
                              "is_bearer": "isBearer",
                              "basic_auth": "basicAuth",
                              "jwt_auth": "jwtAuth",
                              "header_name": "headerName",
                              "header_value": "headerValue",
                              "param_key": "paramKey",
                              "param_info": "paramInfo",
                              "param_name": "paramName",
                              "param_type": "paramType",
                              "is_arr_item": "isArrItem",
                              "child_list": "childList",
                              "check_status": "checkStatus",
                              "status_code": "statusCode",
                              "result_type": "resultType",
                              "match_rule": "matchRule",
                              "check_exist": "checkExist",
                              "param_match": "paramMatch",
                              "timeout_limit_type": "timeoutLimitType",
                              "timeout_limit": "timeoutLimit",
                              "request_redirect": "requestRedirect",
                              "check_ssl": "checkSsl",
                              "sendeEoToken": "sendeEoToken",
                              "send_nocache_token": "sendNocacheToken",
                              "restful_param": "restfulParam",
                              "url_param": "urlParam",
                              "api_protocol": "httpHeader",
                              "api_request_type": "apiRequestType",
                              "keep_going": "keepGoing",
                              "message_encoding": "messageEncoding",
                              "request_type": "requestType",
                              }
    for key in web_to_backend_key_map:
        eolinker_web_req_data = eolinker_web_req_data.replace(key, web_to_backend_key_map[key])
    return json.loads(eolinker_web_req_data)
