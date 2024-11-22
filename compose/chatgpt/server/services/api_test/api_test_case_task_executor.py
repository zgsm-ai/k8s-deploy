#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2024/5/20 11:28
@Desc    ：该文件用于调度执行正在生成测试测试点和测试用例的流程，属于比较上层的文件，只被celery任务的函数内调用，不然会循环引用
"""
import os
import re
import uuid
import logging
import json

from common.constant import ActionsConstant, GPTModelConstant, GPTConstant, ApiTestCaseConstant
from common.exception.exceptions import RequireParamsMissingError
from common.utils.util import retry_on_exception
from common.validation.eolink_api_validation import SingleCaseEditReqBody, ApiManagemenTestCaseEditReqBody, \
    format_data_to_eolinker_web
from services.api_test.api_test_ai_helper import ApiAiHelper, ApiOdgAiHelper
from services.api_test.api_test_case_corrector import ApiTestCaseCorrector
from services.api_test.api_test_case_service import ApiTestEolinkerCaseTaskService, ApiTestCaseService
from services.api_test.api_test_case_task_events_service import ApiTestCaseTaskEventsService
from services.api_test.eolinker_api_helper import ApiHelper, EolinkerDataHandler
from tasks.api_test_case_task import execute_api_test_eolinker_case_task_async, execute_modify_exist_case_async, \
    execute_api_management_test_eolinker_case_task_async
from third_platform.eolinker.api_studio_manager import ApiStudioHelper, ApiStudioManager

logger = logging.getLogger(__name__)


class TaskExecuteManager:

    @classmethod
    @retry_on_exception(RequireParamsMissingError, retry_count=1)
    def execute_gen_management_case_to_eolinker(cls, request_data: dict):
        api_detail_info_dict = request_data.get("api_detail_info_dict")
        api_id = next(iter(api_detail_info_dict))
        tested_api = request_data.get("tested_api")
        pre_api_content = request_data.get("pre_api_content")
        post_api_content = request_data.get("post_api_content")
        display_name = request_data.get("display_name")
        test_point = request_data.get("test_point")
        api_test_case_task_id = request_data.get("api_test_case_task_id")
        gen_eoliner_task_id = request_data.get("gen_eoliner_task_id")
        origin = request_data.get("origin")
        space_id = request_data.get("space_id")
        authorization = request_data.get("authorization")

        api_info_dict = ApiHelper.parse_api_from_markdown(tested_api + pre_api_content + post_api_content)

        if cls.check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
            return None

        logger.info(f'execute_gen_management_case_to_eolinker开始执行 display_name: {display_name};'
                    f' task_id: {gen_eoliner_task_id}')

        ApiTestEolinkerCaseTaskService.start_task(gen_eoliner_task_id)
        # management页面只有一个步骤，
        test_steps = [{
            "api_id": api_id,
            "step_description": test_point,
        }, ]
        ask_data = {
            "test_steps": test_steps,
            "tested_api": tested_api,
            "pre_api_content": pre_api_content,
            "post_api_content": post_api_content,
            "test_point": test_point,
            "display_name": display_name,
            "stream": False,
            "action": ActionsConstant.API_TEST_SINGLE_CASE,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        logger.info(
            f'execute_gen_management_case_to_eolinker 开始询问AI测试集; api_test_case_task_id: {api_test_case_task_id}')
        data_obj = ApiAiHelper.get_ai_resp(api_test_case_task_id, ask_data,
                                           ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_TEST_SETS,
                                           gen_eoliner_task_id=gen_eoliner_task_id)
        logger.info(
            f'execute_gen_management_case_to_eolinker 成功询问AI测试集; api_test_case_task_id: {api_test_case_task_id}')

        # 因为后台任务无法及时中止，这里AI请求完再判断一次是否被中止
        if cls.check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
            return None
        # 校验及修正不合理步骤或参数
        ApiTestCaseCorrector.generate_case_corrector(data_obj.get("test_steps", []), api_detail_info_dict, test_point,
                                                     tested_api, display_name,
                                                     case_type=ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT)

        # 组织已有数据，调用eolinker平台前端接口来创建测试用例

        # 使用AI生成数据更新测试用例
        test_steps = data_obj.get("test_steps", [])
        if test_steps:
            test_case_data = test_steps[0]
            api_info = api_detail_info_dict.get(str(api_id)) if api_detail_info_dict.get(
                str(api_id)) else api_detail_info_dict.get(api_id)

            # 处理测试步骤前后关联参数
            case_data = test_case_data.get("case_data", {})
            url_param = case_data.get("url_param", [])
            ApiTestCaseService.add_param_name_to_step_params(api_info.get("urlParam"), url_param)
            restful_param = case_data.get("restful_param", [])
            ApiTestCaseService.add_param_name_to_step_params(api_info.get("restfulParam"), restful_param)
            params = case_data.get("params", [])
            ApiTestCaseService.add_param_name_to_step_params(api_info.get("requestInfo"), params)

            api_type_info = api_info_dict.get(api_id)
            if api_type_info:
                api_request_type, _ = api_type_info
                test_case_data["case_data"]["api_request_type"] = api_request_type

            else:
                logger.info(f'execute_gen_management_case_to_eolinker 解析API信息异常，采用AI生成值; '
                            f'api_test_case_task_id: {api_test_case_task_id}；；'
                            f'api_id：{api_id}; '
                            f'gen_eoliner_task_id: {gen_eoliner_task_id}')
            # 更新测试用例的数据
            test_case_edit_data = ApiManagemenTestCaseEditReqBody(
                space_id=request_data['space_id'],
                project_id=request_data['project_id'],
                case_data=test_case_data.get("case_data", {}),
                status_code_verification=test_case_data.get("status_code_verification"),
                response_result_verification=test_case_data.get("response_result_verification"),
                response_header_verification=test_case_data.get("response_header_verification"),
            )
            logger.info(f'execute_gen_management_case_to_eolinker 开始更新测试用例; '
                        f'test_case_data: {test_case_data}；\n；'
                        f'test_case_edit_data：{test_case_edit_data.model_dump()}; ')
            url_param = format_data_to_eolinker_web(test_case_edit_data.model_dump().get("case_data").get("url_param"))
            # 构建附带query参数的url
            url_param_lst = []
            # 如果参数中带"&"字符，则需要进行转义
            for p in url_param:
                url_param_key = p.get("paramKey")
                param_info = p.get("paramInfo")
                if "&" in param_info:
                    param_info = param_info.replace("&", "%26")
                url_param_lst.append(str(url_param_key) + "=" + str(param_info))
            url_param_str = ("?" + "&".join(url_param_lst)) if url_param_lst else ""
            url = api_detail_info_dict.get(api_id).get("baseInfo").get("apiURI") + url_param_str
            api_protocol = format_data_to_eolinker_web(
                test_case_edit_data.model_dump().get("case_data").get("api_protocol"))
            restful_param = format_data_to_eolinker_web(
                test_case_edit_data.model_dump().get("case_data").get("restful_param"))
            params = format_data_to_eolinker_web(test_case_edit_data.model_dump().get("case_data").get("params"))
            status_code_verification = format_data_to_eolinker_web(
                test_case_edit_data.model_dump().get("status_code_verification"))
            response_result_verification = format_data_to_eolinker_web(
                test_case_edit_data.model_dump().get("response_result_verification"))
            response_header_verification = format_data_to_eolinker_web(
                test_case_edit_data.model_dump().get("response_header_verification"))
            # 创建测试用例
            case_name = data_obj.get("test_point")
            case_tag = request_data.get("case_tag")
            case_data_template = {
                "messageEncoding": "utf-8",
                "headers": [],
                "params": params,
                "URL": url,
                "requestType": api_detail_info_dict.get(api_id).get("baseInfo").get("apiRequestParamType"),
                "raw": "",
                "apiRequestType": api_detail_info_dict.get(api_id).get("baseInfo").get("apiRequestType"),
                "httpHeader": api_protocol,
                "urlParam": url_param,
                "restfulParam": restful_param,
                "auth": {
                    "status": "0"
                },
                "apiRequestParamJsonType": api_detail_info_dict.get(api_id).get("baseInfo").get(
                    "apiRequestParamJsonType"),
                "apiRequestMetadata": [],
                "script": {
                    "before": "",
                    "after": "",
                    "prepare": "",
                    "type": "0"
                },
                "isUseHex": 0
            }
            add_test_case_template_data = {
                'apiType': api_detail_info_dict.get(api_id).get("apiType"),
                'spaceKey': space_id,
                'projectHashKey': request_data.get('project_id'),
                'apiID': api_id,
                'priority': request_data.get('priority'),
                'caseName': case_name,
                'caseData': json.dumps(case_data_template),
                'statusCodeVerification': json.dumps(status_code_verification),
                'responseResultVerification': json.dumps(response_result_verification),
                'responseHeaderVerification': json.dumps(response_header_verification),
                'tags': f'["{case_tag}"]',
                'beforeScriptMode': '1',
                'afterScriptMode': '1',
                'beforeScriptList': '[]',
                'afterScriptList': '[]'
            }

            logger.info(f'execute_gen_management_case_to_eolinker 开始创建测试用例;'
                        f' api_test_case_task_id: {api_test_case_task_id}；'
                        f' case_name：{case_name}; case_tag={case_tag} case_data_template={case_data_template}'
                        f' add_test_case_template_data={add_test_case_template_data}')
            event_id = ApiTestCaseTaskEventsService.create(
                api_test_case_task_id=api_test_case_task_id,
                event_type=ApiTestCaseConstant.ApiTestCaseTaskEventsType.CREATE_TEST_CASE,
                status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
                remark=f"{gen_eoliner_task_id}",
                gen_eoliner_task_id=gen_eoliner_task_id,
                data={
                    "index": f"{gen_eoliner_task_id}",
                    "case_name": case_name,
                    "req_data": add_test_case_template_data,
                    "authorization": authorization,
                    "origin": origin
                }
            )
            result, _data = ApiStudioManager.add_test_case_pro(add_test_case_template_data, authorization, origin,
                                                               ApiTestCaseConstant.ApiTestCaseStage.MANAGEMENT)
            if not result:
                ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=f"{gen_eoliner_task_id}；"
                                                                            f"创建测试用例失败:{_data}")
                raise Exception(
                    f"api_test_case_task_id：{api_test_case_task_id}; gen_eoliner_task_id: {gen_eoliner_task_id} "
                    f"case_name：{case_name}; 创建测试用例失败:{_data}")

            # 所有步骤操作完成
            logger.info(f'execute_api_testcases_task 完成创建测试用例; '
                        f'api_test_case_task_id: {api_test_case_task_id}； case_name：{case_name}；'
                        f'case_id：;gen_eoliner_task_id: {gen_eoliner_task_id}')
            ApiTestCaseTaskEventsService.event_to_done(event_id)
        ApiTestEolinkerCaseTaskService.success_task(display_name, gen_eoliner_task_id)

    @classmethod
    @retry_on_exception(RequireParamsMissingError, retry_count=1)
    def execute_gen_case_to_eolinker(cls, request_data: dict):
        api_detail_info_dict = request_data.get("api_detail_info_dict")
        tested_api = request_data.get("tested_api")
        pre_api_content = request_data.get("pre_api_content")
        post_api_content = request_data.get("post_api_content")
        display_name = request_data.get("display_name")
        test_point = request_data.get("test_point")
        api_test_case_task_id = request_data.get("api_test_case_task_id")
        gen_eoliner_task_id = request_data.get("gen_eoliner_task_id")
        origin = request_data.get("origin")
        space_id = request_data.get("space_id")
        authorization = request_data.get("authorization")
        api_odg = request_data.get("api_odg")

        api_info_dict = ApiHelper.parse_api_from_markdown(tested_api + pre_api_content + post_api_content)

        if cls.check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
            return None

        logger.info(f'execute_gen_api_testcases_task开始执行 display_name: {display_name};'
                    f' task_id: {gen_eoliner_task_id}')

        ApiTestEolinkerCaseTaskService.start_task(gen_eoliner_task_id)

        all_api = f"{pre_api_content}\n{tested_api}\n{post_api_content}"
        # 开始询问AI识别测试步骤顺序
        ask_data = {
            "tested_api": tested_api,
            "all_api": all_api,
            "api_odg": api_odg,
            "test_point": test_point,
            "display_name": display_name,
            "stream": False,
            "action": ActionsConstant.API_TEST_GEN_STEP,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        logger.info(f'execute_gen_case_to_eolinker 开始生成测试步骤; api_test_case_task_id: {api_test_case_task_id}')
        res = ApiAiHelper.get_ai_resp(
            api_test_case_task_id, ask_data, ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_TEST_STEPS,
            gen_eoliner_task_id=gen_eoliner_task_id
        )
        test_steps = res.get("steps")
        logger.info(f'execute_gen_case_to_eolinker 成功生成测试步骤; api_test_case_task_id: {api_test_case_task_id}')

        # 组装测试步骤需要的前后置api文档
        test_steps_api_id_list = [step.get("api_id") for step in test_steps]

        pre_api_id_list = [api_id for api_id in test_steps_api_id_list if str(api_id) in pre_api_content]
        pre_api_content_in_test_steps = "\n".join(
            ApiHelper.get_markdown_by_api_id(api_id, api_detail_info_dict) for api_id in pre_api_id_list
        )

        post_api_id_list = [api_id for api_id in test_steps_api_id_list if str(api_id) in post_api_content]
        post_api_content_in_test_steps = "\n".join(
            ApiHelper.get_markdown_by_api_id(api_id, api_detail_info_dict) for api_id in post_api_id_list
        )

        ask_data = {
            "test_steps": test_steps,
            "tested_api": tested_api,
            "pre_api_content": pre_api_content_in_test_steps,
            "post_api_content": post_api_content_in_test_steps,
            "test_point": test_point,
            "display_name": display_name,
            "stream": False,
            "action": ActionsConstant.API_TEST_SINGLE_CASE,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }
        logger.info(f'execute_gen_case_to_eolinker 开始询问AI测试集; api_test_case_task_id: {api_test_case_task_id}')
        data_obj = ApiAiHelper.get_ai_resp(api_test_case_task_id, ask_data,
                                           ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_TEST_SETS,
                                           gen_eoliner_task_id=gen_eoliner_task_id)
        logger.info(f'execute_gen_case_to_eolinker 成功询问AI测试集; api_test_case_task_id: {api_test_case_task_id}')

        # 因为后台任务无法及时中止，这里AI请求完再判断一次是否被中止
        if cls.check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
            return None
        # 校验及修正不合理步骤或参数
        ApiTestCaseCorrector.generate_case_corrector(data_obj.get("test_steps", []), api_detail_info_dict, test_point,
                                                     tested_api, display_name)

        # 组织已有数据，调用eolinker平台接口来创建测试用例
        # 先获取space 的 api_key , 给后续调用 eoliner openapi使用,获取不到 该api_key 就会用配置文件默认的用户
        api_key = ApiStudioHelper.get_space_api_key(space_id=space_id, authorization=authorization, origin=origin)
        if not isinstance(data_obj, list):
            data_obj = [data_obj]
        # 遍历测试集
        for test_set in data_obj:
            # 创建测试用例
            case_name = test_set.get("test_point")

            add_test_case_data = {
                "spaceKey": space_id,
                "projectHashKey": request_data['project_id'],
                "module": request_data['module'],
                "caseName": case_name,
                "groupID": request_data['group_id'],
                "priority": request_data['priority'],
                "caseStyle": request_data['case_style'],
                "caseTag": request_data['case_tag'],
                "caseType": request_data['case_type']
            }

            logger.info(f'execute_api_testcases_task 开始创建测试用例; api_test_case_task_id: {api_test_case_task_id}；'
                        f' case_name：{case_name}')
            event_id = ApiTestCaseTaskEventsService.create(
                api_test_case_task_id=api_test_case_task_id,
                event_type=ApiTestCaseConstant.ApiTestCaseTaskEventsType.CREATE_TEST_CASE,
                status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
                remark=f"{gen_eoliner_task_id}",
                gen_eoliner_task_id=gen_eoliner_task_id,
                data={
                    "index": f"{gen_eoliner_task_id}",
                    "case_name": case_name,
                    "req_data": add_test_case_data,
                    "authorization": authorization,
                    "origin": origin
                }
            )
            result, _data = ApiStudioManager.add_test_case_pro(add_test_case_data, authorization, origin)

            if not result:
                ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=f"{gen_eoliner_task_id}；"
                                                                            f"创建测试用例失败:{_data}")
                raise Exception(
                    f"api_test_case_task_id：{api_test_case_task_id}; gen_eoliner_task_id: {gen_eoliner_task_id} "
                    f"case_name：{case_name}; 创建测试用例失败:{_data}")
            case_id = int(_data)

            # 测试步骤列表
            test_steps = test_set.get("test_steps", [])
            test_steps_num = len(test_steps)
            step_index = 0
            detail_events = []
            step_num_id_dict = {}
            # 遍历测试步骤列表
            for test_step in test_steps:
                step_index += 1
                api_id = test_step.get("api_id")
                api_info = api_detail_info_dict.get(str(api_id)) if api_detail_info_dict.get(
                    str(api_id)) else api_detail_info_dict.get(api_id)
                api_name = test_step.get("api_name")
                logger.info(
                    f'execute_gen_case_to_eolinker 开始创建测试步骤; '
                    f'api_test_case_task_id: {api_test_case_task_id}；case_id：{case_id}；'
                    f'gen_eoliner_task_id: {gen_eoliner_task_id}, api_id：{api_id}; '
                    f'api_name：{api_name}; step_index: {step_index}')
                # 创建测试用例步骤的数据
                add_single_case_data = {
                    "space_id": request_data['space_id'],
                    "project_id": request_data['project_id'],
                    "case_id": case_id,
                    "api_id": [api_id],
                    "api_case_id": [],
                    "module": request_data['module'],
                }
                # 增加事件
                detail_events.append({
                    "index": f"创建测试步骤,共{test_steps_num}个,完成{step_index}个",
                    "req_data": add_single_case_data,
                    "test_step": test_step,
                })
                ApiTestCaseTaskEventsService.update_by_id_json(event_id, data={"detail_events": detail_events})
                # 创建测试用例步骤
                result, _data = ApiStudioManager.add_single_case_by_api_doc(
                    add_single_case_data, origin, api_key=api_key)
                if not result:
                    ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=f"创建测试步骤失败:{_data}")
                    raise Exception(f"api_test_case_task_id：{api_test_case_task_id}; case_name：{case_name}; "
                                    f"api_id：{api_id}; api_name：{api_name}; 创建测试步骤失败:{_data}; "
                                    f"gen_eoliner_task_id: {gen_eoliner_task_id}")

                # 查询刚刚创建的测试步骤的ID
                case_detail_req = {
                    "space_id": request_data['space_id'],
                    "project_id": request_data['project_id'],
                    "case_id": case_id,
                    "module": request_data['module'],
                }
                case_detail = ApiStudioManager.get_test_case(case_detail_req, origin, api_key=api_key)
                single_case_list = case_detail.get("single_case_list") or []
                single_case_id = single_case_list[-1].get("conn_id")

                # 按下标存储id,用于后面转换数据
                step_num_id_dict[step_index - 1] = single_case_id

                # 处理测试步骤前后关联参数
                case_data = test_step.get("case_data", {})
                url_param = case_data.get("url_param", [])
                ApiTestCaseService.add_param_name_to_step_params(api_info.get("urlParam"), url_param)
                restful_param = case_data.get("restful_param", [])
                ApiTestCaseService.add_param_name_to_step_params(api_info.get("restfulParam"), restful_param)
                params = case_data.get("params", [])
                ApiTestCaseService.add_param_name_to_step_params(api_info.get("requestInfo"), params)
                for params_obj in url_param + restful_param + params:
                    # 注意：需要递归处理参数，会修改不规范的参数格式
                    EolinkerDataHandler.deal_param_info(params_obj, step_num_id_dict)
                # 组装编辑测试步骤的数据
                test_step["conn_id"] = single_case_id
                test_step["case_id"] = case_id

                api_info = api_info_dict.get(api_id)

                if api_info:
                    api_request_type, api_protocol = api_info
                    test_step["api_protocol"] = api_protocol
                    test_step["case_data"]["api_request_type"] = api_request_type

                else:
                    logger.info(f'execute_api_testcases_task 解析API信息异常，采用AI生成值; '
                                f'api_test_case_task_id: {api_test_case_task_id}；case_id：{case_id}；'
                                f'api_id：{api_id}; api_name：{api_name}; step_index: {step_index};'
                                f'gen_eoliner_task_id: {gen_eoliner_task_id}')

                single_case_edit_data = SingleCaseEditReqBody(
                    data=test_step,
                    space_id=request_data['space_id'],
                    project_id=request_data['project_id'],
                )
                # 编辑测试步骤
                result, _data = ApiStudioManager.single_case_edit(single_case_edit_data.model_dump(), origin,
                                                                  api_key=api_key)
                if not result:
                    ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=f"测试步骤绑定用例失败:{_data}")
                    raise Exception(f"api_test_case_task_id：{api_test_case_task_id}; case_name：{case_name}; "
                                    f"api_id：{api_id}; api_name：{api_name}; 测试步骤绑定用例失败:{_data}")
                logger.info(f'execute_api_testcases_task 成功创建测试步骤; '
                            f'api_test_case_task_id: {api_test_case_task_id}；case_id：{case_id}；'
                            f'api_id：{api_id}; api_name：{api_name}; step_index: {step_index};'
                            f'gen_eoliner_task_id: {gen_eoliner_task_id}')

            # 所有步骤创建完成
            logger.info(f'execute_api_testcases_task 完成创建测试用例; '
                        f'api_test_case_task_id: {api_test_case_task_id}； case_name：{case_name}；'
                        f'case_id：{case_id};gen_eoliner_task_id: {gen_eoliner_task_id}')
            ApiTestCaseTaskEventsService.event_to_done(event_id, data={"case_id": case_id})
        ApiTestEolinkerCaseTaskService.success_task(display_name, gen_eoliner_task_id)

    @classmethod
    @retry_on_exception(RequireParamsMissingError, retry_count=1)
    def execute_modify_exist_case(cls, request_data: dict):
        display_name = request_data.get("display_name")
        gen_eoliner_task_id = request_data.get("gen_eoliner_task_id")
        api_list = request_data.get("api_list")
        api_compare_infos = request_data.get("api_compare_info")
        api_test_case_task_id = request_data.get("api_test_case_task_id")
        space_id = request_data.get("space_id")
        project_id = request_data.get("project_id")
        authorization = request_data.get("authorization")
        origin = request_data.get("origin")
        modify_case = request_data.get("modify_case")

        ApiTestEolinkerCaseTaskService.start_task(gen_eoliner_task_id)

        if cls.check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
            return None

        case_id = modify_case.get("case_id")
        case_name = modify_case.get("case_name")

        if not case_id or not case_name:
            raise Exception(f"api_test_case_task_id:{api_test_case_task_id}; case_name:{case_name}; case_id:{case_id};"
                            f"获取待修改用例信息失败")

        # 根据 case_id 获取旧测试步骤
        old_test_steps, conn_id_list, raw_resp = ApiTestCaseService.get_case_steps_info(space_id, project_id, case_id,
                                                                                        authorization,
                                                                                        origin)

        is_newest = ApiTestCaseService.is_newest_case(api_list, case_info=raw_resp)

        # 从 raw_resp 中解析 api id 与 api project key
        api_list = []
        case_list = raw_resp.get("singleCaseList", [])
        for case in case_list:
            api_list.append({
                "api_id": case.get("apiID"),
                "project_id": case.get("apiProjectHashKey")
            })

        api_detail_info_dict = ApiHelper.get_all_api_info(api_list, space_id, authorization, origin)

        # 组装新 API 文档
        api_document = "\n".join(
            [f"{ApiHelper.get_markdown_by_api_id(api['api_id'], api_detail_info_dict)}"
             for api in api_list])
        # 解析请求协议，请求方式等API信息
        api_info_dict = ApiHelper.parse_api_from_markdown(api_document)

        test_steps_title = old_test_steps.get("test_steps_title", [])
        test_point = old_test_steps.get("test_point", "")
        test_steps = [test_step_title.get("api_id") for test_step_title in test_steps_title]

        # 判断是否跳过 AI 生成
        # 建立旧测试步骤参数查找表 old_param_lookup 用于后续判断改动参数是否在旧测试步骤中
        old_param_lookup = ApiHelper.build_param_lookup(old_test_steps)

        # 重建改动文档，只保留在旧测试步骤中出现的参数
        bypass_ai_generation_param, reduced_api_increment_info, param_deleted = cls.bypass_ai_generation_with_param(
            api_compare_infos,
            old_param_lookup)

        bypass_ai_generation = True if is_newest or bypass_ai_generation_param else False

        if bypass_ai_generation:
            logger.info(f"跳过AI生成：case_id = {case_id}"
                        f"规则：is_newest = {is_newest}, bypass_ai_generation = {bypass_ai_generation_param}"
                        f"旧步骤参数 {old_param_lookup}")
        else:

            # 组装差异文档
            api_increment_content, api_delete_content = "", ""

            for api_id in reduced_api_increment_info.keys():
                api_diff, api_delete = reduced_api_increment_info[api_id]
                api_increment_content += ApiHelper.parse_api_markdown_from_dict(api_diff)
                api_delete_content += ApiHelper.parse_api_markdown_from_dict(api_delete)

            # 询问 AI 生成新的测试步骤
            ask_data = {
                "test_steps": test_steps,
                "tested_api": api_document,
                "test_point": test_point,
                "old_test_steps": old_test_steps,
                "api_diff_content": api_increment_content,
                "api_del_content": api_delete_content,
                "display_name": display_name,
                "stream": False,
                "action": ActionsConstant.API_TEST_CASE_MODIFY,
                "conversation_id": str(uuid.uuid4()),
                "seed": 0,
                "model": GPTModelConstant.GPT_4o,
                "response_format": GPTConstant.RESPONSE_JSON_OBJECT
            }

            logger.info(f'execute_gen_case_to_eolinker 开始询问AI修改已有用例; api_test_case_task_id: {api_test_case_task_id}')
            data_obj = ApiAiHelper.get_ai_resp(api_test_case_task_id, ask_data,
                                               ApiTestCaseConstant.ApiTestCaseTaskEventsType.ASK_AI_TEST_SETS,
                                               gen_eoliner_task_id=gen_eoliner_task_id)
            logger.info(f'execute_gen_case_to_eolinker 成功询问AI修改已有用例; api_test_case_task_id: {api_test_case_task_id}')

            if cls.check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
                return None

            # 校验及修正不合理步骤或参数
            test_steps = data_obj.get("test_steps", [])
            ApiTestCaseCorrector.modify_case_corrector(test_steps, old_test_steps.get('test_steps'),
                                                       api_detail_info_dict)

            api_key = ApiStudioHelper.get_space_api_key(space_id=space_id, authorization=authorization, origin=origin)

            # 标记用例为 AI-已更新
            tag_list = raw_resp.get("caseTag", [])
            tag_list.append(ApiTestCaseConstant.ApiTestCaseTags.UPDATED)
            modify_req = {
                "data": {
                    "group_id": 0,
                    "case_id": case_id,
                    "case_tag": ",".join(tag_list)
                },
                "space_id": space_id,
                "project_id": project_id,
                "module": 0,
            }
            ApiStudioManager.edit_test_case_info(modify_req, origin=origin, api_key=api_key)

            logger.info(f'execute_api_testcases_task 开始修改测试用例; api_test_case_task_id: {api_test_case_task_id}；'
                        f'case_id: {case_id} case_name：{case_name}')
            event_id = ApiTestCaseTaskEventsService.create(
                api_test_case_task_id=api_test_case_task_id,
                event_type=ApiTestCaseConstant.ApiTestCaseTaskEventsType.MODIFY_TEST_CASE,
                status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
                remark=f"{gen_eoliner_task_id}",
                gen_eoliner_task_id=gen_eoliner_task_id,
                data={
                    "index": f"{gen_eoliner_task_id}",
                    "case_name": case_name,
                    "case_id": case_id,
                    "authorization": authorization,
                    "origin": origin
                }
            )

            step_index = 0
            step_num_id_dict = {}
            # 遍历测试步骤列表
            for test_step in test_steps:
                step_index += 1
                api_id = test_step.get("api_id")
                api_name = test_step.get("api_name")

                single_case_id = case_id

                # 按下标存储id,用于后面转换数据
                step_num_id_dict[step_index - 1] = single_case_id

                # 处理测试步骤前后关联参数
                case_data = test_step.get("case_data", {})
                url_param = case_data.get("url_param", [])
                restful_param = case_data.get("restful_param", [])
                params = case_data.get("params", [])
                for params_obj in url_param + restful_param + params:
                    # 需要递归处理
                    EolinkerDataHandler.deal_param_info(params_obj, step_num_id_dict)
                # 组装编辑测试步骤的数据
                test_step["case_id"] = case_id
                api_info = api_info_dict.get(api_id)

                if api_info:
                    api_request_type, api_protocol = api_info
                    test_step["api_protocol"] = api_protocol
                    test_step["case_data"]["api_request_type"] = api_request_type

                else:
                    logger.info(f'execute_api_testcases_task 解析API信息异常，采用AI生成值; '
                                f'api_test_case_task_id: {api_test_case_task_id}；case_id：{case_id}；'
                                f'api_id：{api_id}; api_name：{api_name}; step_index: {step_index};'
                                f'gen_eoliner_task_id: {gen_eoliner_task_id}')

                single_case_edit_data = SingleCaseEditReqBody(
                    data=test_step,
                    space_id=space_id,
                    project_id=project_id,
                )
                # 编辑测试步骤
                result, _data = ApiStudioManager.single_case_edit(single_case_edit_data.model_dump(), origin,
                                                                  api_key=api_key)
                if not result:
                    ApiTestCaseTaskEventsService.event_to_fail(event_id, remark=f"测试步骤绑定用例失败:{_data}")
                    raise Exception(f"api_test_case_task_id：{api_test_case_task_id}; case_name：{case_name}; "
                                    f"api_id：{api_id}; api_name：{api_name}; 测试步骤绑定用例失败:{_data}")
                logger.info(f'execute_api_testcases_task 成功修改测试步骤; '
                            f'api_test_case_task_id: {api_test_case_task_id}；case_id：{case_id}；'
                            f'api_id：{api_id}; api_name：{api_name}; step_index: {step_index};'
                            f'gen_eoliner_task_id: {gen_eoliner_task_id}')

            logger.info(f'execute_api_testcases_task 完成修改测试用例; '
                        f'api_test_case_task_id: {api_test_case_task_id}； case_name：{case_name}；'
                        f'case_id：{case_id};gen_eoliner_task_id: {gen_eoliner_task_id}')
            ApiTestCaseTaskEventsService.event_to_done(event_id, data={"case_id": case_id})

        ApiTestEolinkerCaseTaskService.success_task(display_name, gen_eoliner_task_id)

    @classmethod
    def execute_gen_api_management_testcases_task(cls, request_data: dict):
        """执行API管理页面用例生成任务"""
        display_name = request_data.get('display_name')
        task_id = request_data['task_id']
        origin = request_data['origin']
        api_list = [request_data.get('api_info')]
        space_id = request_data.get('api_info', {}).get('space_id')
        authorization = request_data.get('authorization')
        test_points = request_data.get('test_points')
        logger.info(f'execute_gen_api_management_testcases_task开始执行 display_name: {display_name}; task_id: {task_id}')
        api_test_case_obj = ApiTestCaseService.get_by_id(task_id)
        if api_test_case_obj.is_final_status:
            # 如果是终态，直接结束
            logger.info(f'execute_gen_api_management_testcases_task父任务为终态，跳过执行，task_id: {task_id}')
            return None
        # 任务开始
        ApiTestCaseService.start_task(task_id)
        # 请求eolinker拿到详情数据
        get_eolinker_data_event_id = ApiTestCaseTaskEventsService.create(
            api_test_case_task_id=task_id,
            event_type=ApiTestCaseConstant.ApiTestCaseTaskEventsType.GET_EOLINKER_DATA,
            status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
            data={}
        )

        api_detail_info_dict = ApiHelper.get_all_api_info(api_list, space_id,
                                                          authorization,
                                                          origin)
        # 已有用例列表，用于避免重复创建用例
        exist_case_list = []
        for api in api_list:
            api_relation_testcase_list = api.get('api_relation_testcase_list', [])
            if len(api_relation_testcase_list) > 0:
                for api_relation_testcase in api_relation_testcase_list:
                    exist_case_list.append(api_relation_testcase.get('case_name', ''))

        # 组装前置api文档
        pre_api_content = "Na"
        # 组装主流程api文档
        tested_api = "\n".join(
            [f"{ApiHelper.get_markdown_by_api_id(api['api_id'], api_detail_info_dict)}"
             for api in api_list])
        # 组装后置api文档
        post_api_content = "Na"

        ApiTestCaseTaskEventsService.event_to_done(get_eolinker_data_event_id)

        # 开始创建询问AI测试集的子任务
        index = 0
        # 遍历测试点
        for test_point in test_points:
            # 避免重复测试点生成
            exist_case = "\n".join(f"测试点{i + 1}: {case.strip()}" for i, case in enumerate(exist_case_list))
            if exist_case_list and (
                    test_point in exist_case_list or ApiTestCaseService.test_point_is_repeated(task_id, exist_case,
                                                                                               test_point,
                                                                                               display_name)):
                logger.info(f"execute_api_testcases_task 跳过重复测试点, task_id = {task_id}\n"
                            f"test_point = {test_point}")
                continue
            # 将生成的新测试点追加到已存在测试点列表，避免本身生成的测试点重复
            exist_case_list.append(test_point)

            # 避免超长字符串测试
            over_length_pattern = r"超[出长]|过长|超出长度(字符串|限制)"
            if re.search(over_length_pattern, test_point):
                logger.info(f"execute_api_testcases_task 跳过超长内容测试, task_id = {task_id}\n"
                            f"test_point = {test_point}")
                continue

            index += 1
            # 去掉测点序号如“10. 测试xxx”改为“测试xxx”
            pattern = r'^\d+\.(.*)$'
            test_point = re.sub(pattern, r"\1", test_point)
            req_data = dict(
                tested_api=tested_api,
                pre_api_content=pre_api_content,
                post_api_content=post_api_content,
                display_name=display_name,
                test_point=test_point,
                api_test_case_task_id=task_id,
                origin=origin,
                space_id=space_id,
                project_id=request_data.get('api_info', {}).get('project_id'),
                priority=request_data.get('priority', 'P0'),
                case_tag=request_data.get('case_tag', "千流AI"),
                authorization=authorization,
            )
            obj = ApiTestEolinkerCaseTaskService.create(
                display_name=display_name,
                status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.PENDING,
                req_data=req_data,
                api_test_case_task_id=task_id,
            )
            req_data["gen_eoliner_task_id"] = obj.id
            req_data["api_detail_info_dict"] = api_detail_info_dict
            api_test_sync = os.environ.get("API_TEST_SYNC")
            if api_test_sync:
                # 同步调用，不使用异步任务，调试的时候才用execute_gen_management_case_to_eolinker
                TaskExecuteManager.execute_gen_management_case_to_eolinker(req_data)
                celery_task_id = "ssssssssssssssssss"
            else:
                result = execute_api_management_test_eolinker_case_task_async.delay(req_data)
                # 获取任务ID
                celery_task_id = str(result.id)
            # 将celery任务id添加到数据库
            ApiTestEolinkerCaseTaskService.update_by_id(
                obj.id,
                celery_task_id=celery_task_id,
            )
            logger.info(f'execute_api_testcases_task 创建 api_test_eolinker_case_task: {obj.id}')

        # 提升任务结束鲁棒性
        if index == 0:
            ApiTestCaseService.success_task(display_name, task_id)

        logger.info(f'execute_api_testcases_task 创建测试点任务完成 display_name: {display_name}; task_id: {task_id}')

    @classmethod
    def execute_gen_api_testcases_task(cls, request_data: dict):
        """执行API测试用例任务"""
        display_name = request_data['display_name']
        task_id = request_data['task_id']
        origin = request_data['origin']
        pre_api_list = request_data['pre_api_list']
        api_list = request_data['api_list']
        post_api_list = request_data['post_api_list']
        space_id = request_data['space_id']
        authorization = request_data['authorization']
        logger.info(f'execute_gen_api_testcases_task执行 display_name: {display_name}; task_id: {task_id}')
        obj = ApiTestCaseService.get_by_id(task_id)
        if obj.is_final_status:
            # 如果是终态，直接结束
            logger.info(f'execute_gen_api_testcases_task执行, 为终态，task_id: {task_id}')
            return None
        # 任务开始
        ApiTestCaseService.start_task(task_id)
        # 请求eolinker拿到详情数据
        event_id = ApiTestCaseTaskEventsService.create(
            api_test_case_task_id=task_id,
            event_type=ApiTestCaseConstant.ApiTestCaseTaskEventsType.GET_EOLINKER_DATA,
            status=ApiTestCaseConstant.ApiTestCaseTaskEventsStatus.STARTED,
            data={}
        )

        api_detail_info_dict = ApiHelper.get_all_api_info(pre_api_list + api_list + post_api_list, space_id,
                                                          authorization,
                                                          origin)
        # 已有用例列表
        exist_case_list = []

        # 对于每个API， 判断是否进行增量生成
        api_incremental_list = []
        for api in api_list:
            if api.get('old_history', {}).get("id") != api.get('current_history', {}).get("id"):
                # 记录有修改的 api_id
                api_incremental_list.append(api)
            api_relation_testcase_list = api.get('api_relation_testcase_list', [])
            if len(api_relation_testcase_list) > 0:
                for api_relation_testcase in api_relation_testcase_list:
                    exist_case_list.append(api_relation_testcase.get('case_name', ''))

        exist_case = "\n".join(f"测试点{i + 1}: {case.strip()}" for i, case in enumerate(exist_case_list))

        # 组装前置api文档
        pre_api_content = "\n".join(
            [f"{ApiHelper.get_markdown_by_api_id(api['api_id'], api_detail_info_dict)}"
             for api in pre_api_list])

        # 组装主流程api文档
        tested_api = "\n".join(
            [f"{ApiHelper.get_markdown_by_api_id(api['api_id'], api_detail_info_dict)}"
             for api in api_list])

        # 组装后置api文档
        post_api_content = "\n".join(
            [f"{ApiHelper.get_markdown_by_api_id(api['api_id'], api_detail_info_dict)}"
             for api in post_api_list])

        # 解析差异文档
        api_increment_content = ""
        modify_case_list = []
        api_compare_info = {}

        for api in api_incremental_list:
            old_api_params, new_api_params = ApiHelper.get_compare(space_id, api['project_id'],
                                                                   api['api_id'],
                                                                   api.get('current_history', {}).get("id"),
                                                                   api.get('old_history', {}).get("id"),
                                                                   authorization,
                                                                   origin)

            api_compare_info[api['api_id']] = (old_api_params, new_api_params)
            api_increment_content += ApiHelper.get_increment_markdown(api['api_id'], old_api_params,
                                                                      new_api_params)

            # 解析 API 关联用例
            api_relation_testcase_list = api.get('api_relation_testcase_list', [])

            # 轮询传入列表，解析exits_case以及判断是否需要执行修改存量用例异步任务
            if len(api_relation_testcase_list) > 0:
                for api_relation_testcase in api_relation_testcase_list:
                    if api_relation_testcase.get('is_selected', False):
                        modify_case_list.append(api_relation_testcase)

        ApiTestCaseTaskEventsService.event_to_done(event_id)

        # 生成API接口依赖图 start
        other_api = f'{pre_api_content}\n{post_api_content}'
        logger.info(f'execute_api_testcases_task 开始询问AI生成接口 odg 图; api_test_case_task_id: {task_id}')
        if len(api_detail_info_dict.keys()) == 1:
            # 只有一个接口时没有依赖图谱，直接就是接口本身
            api_id = list(api_detail_info_dict.keys())[0]
            api_info = api_detail_info_dict.get(api_id)
            api_odg = f"{api_info.get('baseInfo', {}).get('apiName', '')}({api_id})"
        else:
            # 依赖图用于生成测试步骤时辅助使用
            api_odg = ApiOdgAiHelper.gen(tested_api, other_api, display_name, task_id)
        # 生成API接口依赖图 end

        # 开始询问AI测试点
        # 测试点生成不需要请求头信息
        tested_api_without_header = "\n".join(
            [f"{ApiHelper.get_markdown_by_api_id(api['api_id'], api_detail_info_dict, with_header=False)}"
             for api in api_list])
        ask_data = {
            "tested_api": tested_api_without_header,
            "api_diff_content": api_increment_content,
            "display_name": display_name,
            "exist_case": exist_case,
            "stream": True,
            "action": ActionsConstant.API_TEST_CASE,
            "conversation_id": str(uuid.uuid4()),
            "seed": 0,
            "model": GPTModelConstant.GPT_4o,
            "response_format": GPTConstant.RESPONSE_JSON_OBJECT
        }

        test_points = ApiAiHelper.get_points_stream(task_id, ask_data)

        # 开始创建询问AI测试集的子任务
        index = 0
        # 遍历测试点
        for test_point in test_points:
            # 避免重复测试点生成
            exist_case = "\n".join(f"测试点{i + 1}: {case.strip()}" for i, case in enumerate(exist_case_list))
            if exist_case_list and (
                    test_point in exist_case_list or ApiTestCaseService.test_point_is_repeated(task_id, exist_case,
                                                                                               test_point,
                                                                                               display_name)):
                logger.info(f"execute_api_testcases_task 跳过重复测试点, task_id = {task_id}\n"
                            f"test_point = {test_point}")
                continue
            # 将生成的新测试点追加到已存在测试点列表，避免本身生成的测试点重复
            exist_case_list.append(test_point)

            # 避免超长字符串测试
            over_length_pattern = r"超[出长]|过长|超出长度(字符串|限制)"
            if re.search(over_length_pattern, test_point):
                logger.info(f"execute_api_testcases_task 跳过超长内容测试, task_id = {task_id}\n"
                            f"test_point = {test_point}")
                continue

            index += 1
            req_data = dict(
                tested_api=tested_api,
                pre_api_content=pre_api_content,
                post_api_content=post_api_content,
                display_name=display_name,
                test_point=test_point,
                api_test_case_task_id=task_id,
                origin=origin,
                space_id=space_id,
                project_id=request_data['project_id'],
                module=request_data['module'],
                group_id=request_data['group_id'],
                priority=request_data['priority'],
                case_style=request_data['case_style'],
                case_tag=request_data['case_tag'],
                case_type=request_data['case_type'],
                authorization=authorization,
                api_odg=api_odg,
            )
            obj = ApiTestEolinkerCaseTaskService.create(
                display_name=display_name,
                status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.PENDING,
                req_data=req_data,
                api_test_case_task_id=task_id,
            )
            req_data["gen_eoliner_task_id"] = obj.id
            req_data["api_detail_info_dict"] = api_detail_info_dict
            api_test_sync = os.environ.get("API_TEST_SYNC")
            if api_test_sync:
                # 同步调用，不使用异步任务，调试的时候才用
                TaskExecuteManager.execute_gen_case_to_eolinker(req_data)
                celery_task_id = "ssssssssssssssssss"
            else:
                result = execute_api_test_eolinker_case_task_async.delay(req_data)
                # 获取任务ID
                celery_task_id = str(result.id)
            # 将celery任务id添加到数据库
            ApiTestEolinkerCaseTaskService.update_by_id(
                obj.id,
                celery_task_id=celery_task_id,
            )
            logger.info(f'execute_api_testcases_task 创建 api_test_eolinker_case_task: {obj.id}')

        # 开始发起异步任务，修改存量用例
        if len(modify_case_list) > 0:
            for modify_case in modify_case_list:
                index += 1
                req_data = dict(
                    tested_api=tested_api,
                    pre_api_content=pre_api_content,
                    post_api_content=post_api_content,
                    display_name=display_name,
                    modify_case=modify_case,
                    api_compare_info=api_compare_info,
                    api_test_case_task_id=task_id,
                    origin=origin,
                    module=request_data['module'],
                    space_id=space_id,
                    project_id=request_data['project_id'],
                    authorization=authorization
                )
                obj = ApiTestEolinkerCaseTaskService.create(
                    display_name=display_name,
                    status=ApiTestCaseConstant.ApiTestEolinkerCaseTaskStatus.PENDING,
                    req_data=req_data,
                    api_test_case_task_id=task_id,
                )
                req_data["gen_eoliner_task_id"] = obj.id
                req_data["api_list"] = api_list
                api_test_sync = os.environ.get("API_TEST_SYNC")
                if api_test_sync:
                    # 同步调用，不使用异步任务，调试的时候才用
                    TaskExecuteManager.execute_modify_exist_case(req_data)
                    celery_task_id = "ssssssssssssssssss"
                else:
                    result = execute_modify_exist_case_async.delay(req_data)
                    # 获取任务ID
                    celery_task_id = str(result.id)
                # 将celery任务id添加到数据库
                ApiTestEolinkerCaseTaskService.update_by_id(
                    obj.id,
                    celery_task_id=celery_task_id,
                )
                logger.info(f'execute_api_testcases_task 创建 api_test_modify_case_task: {obj.id}')
            logger.info(f'api_test_modify_case_task 创建用例修改任务完成 display_name: {display_name}; task_id: {task_id}')

        # 提升任务结束鲁棒性
        if index == 0:
            ApiTestCaseService.success_task(display_name, task_id)

        logger.info(f'execute_api_testcases_task 创建测试点任务完成 display_name: {display_name}; task_id: {task_id}')

    @staticmethod
    def check_status_is_final(api_test_case_task_id, gen_eoliner_task_id, display_name):
        """
        :param api_test_case_task_id: 生成测试用例任务ID
        :param gen_eoliner_task_id: 生成eolinker用例任务ID
        :param display_name: 用户名
        :return: 是否最终状态
        """
        obj = ApiTestEolinkerCaseTaskService.get_by_id(gen_eoliner_task_id)
        if obj.is_final_status:
            # 如果是终态，直接结束
            logger.info(f'execute_gen_case_to_eolinker, 为终态，gen_eoliner_task_id: {gen_eoliner_task_id}')
            return True

        api_test_case_task = ApiTestCaseService.get_by_id(api_test_case_task_id)
        if api_test_case_task.is_final_status:
            logger.info(f'execute_gen_case_to_eolinker, 父任务为终态：{api_test_case_task.status}，直接结束当前任务；'
                        f'gen_eoliner_task_id: {gen_eoliner_task_id}')
            ApiTestEolinkerCaseTaskService.stop_task(
                display_name, gen_eoliner_task_id, remark=f"任务启动时父任务是终态: {api_test_case_task.status}")
            return True
        return False

    @staticmethod
    def bypass_ai_generation_with_param(api_compare_infos, old_param_lookup):
        """
        判断是否根据参数规则跳过存量用例修改AI生成，重构API改动文档，并判断是否有参数被删除
        :param api_compare_infos: 上游调用传入
        :param old_param_lookup: 旧步骤参数查找便，list格式，其中项为元组 ("api_id", "param_key")，用于唯一地指定一个参数
        :return:
        bypass_ai_generation: 布尔值，表示是否依据参数规则跳过AI生成
        reduced_api_increment_info: 重构的API改动文档，dict
        have_param_deleted: 布尔值，表示是否有参数被删除
        """
        reduced_api_increment_info = {}
        bypass_ai_generation = True
        have_param_deleted = False
        for api_id in api_compare_infos.keys():
            old_api_params, new_api_params = api_compare_infos.get(api_id)

            api_increment, api_modify = {}, {}
            api_delete, api_diff = {"api_id": api_id}, {"api_id": api_id}

            for key in old_api_params.keys():
                api_increment[key], api_modify[key], api_delete[key], api_diff[key] = [], [], [], []

                if old_api_params[key] != new_api_params[key]:
                    old_param_key_list = [old_param.split("|")[1].strip() for old_param in old_api_params[key]]
                    new_param_key_list = [new_param.split("|")[1].strip() for new_param in new_api_params[key]]

                    # 解析差异文档
                    raw_diff_params = list(set(new_api_params[key]) - set(old_api_params[key]))
                    for diff_param in raw_diff_params:
                        diff_param_key = diff_param.split("|")[1].strip()

                        # 只保留新增参数中的必填项
                        if diff_param_key in new_param_key_list and diff_param_key not in old_param_key_list:
                            if diff_param.split("|")[3].strip() == "是":
                                api_increment[key].append(diff_param)
                                bypass_ai_generation = False

                        # 只保留修改参数中，出现在旧测试步骤中的项
                        if diff_param_key in new_param_key_list and diff_param_key in old_param_key_list:
                            if (api_id, diff_param_key) in old_param_lookup:
                                api_modify[key].append(diff_param)
                                bypass_ai_generation = False

                    # 只保留删除参数中，出现在旧测试步骤中的项
                    for index, old_param_key in enumerate(old_param_key_list):
                        if old_param_key not in new_param_key_list and (api_id, old_param_key) in old_param_lookup:
                            api_delete[key].append(old_api_params[key][index])
                            bypass_ai_generation = False
                            have_param_deleted = True

                api_diff[key] = list(set(api_increment[key]) | set(api_modify[key]))

            reduced_api_increment_info[api_id] = (api_diff, api_delete)

        return bypass_ai_generation, reduced_api_increment_info, have_param_deleted
