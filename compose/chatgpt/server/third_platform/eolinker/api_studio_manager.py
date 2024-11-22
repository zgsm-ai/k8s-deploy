#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/1/25 15:23
# @Author  : 苏德利16646
# @Contact : 16646@sangfor.com
# @File    : api_studio_manager.py
# @Software: PyCharm
# @Project : chatgpt-server
# @Desc    : eolinker API研发管理接口封装
import logging
from copy import deepcopy
from third_platform.eolinker import EoLinkerConfig
from common.utils.request_util import RequestUtil
from common.constant import ApiTestCaseConstant

logger = logging.getLogger(__name__)


class ApiStudioManager(EoLinkerConfig):
    """
    此类主要打通 eolinker 平台的相关接口
    /v2 开头的接口是eoliner对外提供的openapi接口，认证方式是在请求头中加 Eo-Secret-Key
    非 /v2 开头的接口都是从在浏览器中抓取的前端请求后端的接口，认证方式是在请求头加 authorization (依赖前端发到后端)
    """
    API_V3_MANAGEMENT_PATH = '/v3/api-management'

    API_STUDIO_PATH = '/v2/api_studio/management'
    API_STUDIO_AUTOMATED_PATH = "/v2/api_studio/automated_test"
    API_STEP_INFO = "/v2/api_studio/automated_test/single_case/get"
    API_CASE_EDIT = "/v2/api_studio/automated_test/test_case/edit"
    # 执行用例
    API_CASE_EXECUTE = "/v2/api_studio/automated_test/test_case/execute"

    API_PRO_PATH = "/apiManagementPro/Api/getApi"
    API_SPACE_INFO_PATH = "/space/Space/getSpaceInfo"
    API_AUTOMATED_TEST_CASE = "/automatedTest/AutomatedTestCase"
    API_MANAGEMENT_TEST_CASE = "/apiManagementPro/TestCase"
    API_COMPARE_PATH = "/apiManagementPro/Api/CompareApiInfo"
    API_CASE_INTO = "/automatedTest/AutomatedTestCaseSingle/getSimpleSingleCaseList"
    # 获取用例执行报告
    API_CASE_TEST_REPORT_LIST = "/automatedTest/CaseTestReport/getReportList"
    API_SINGLE_CASE_TEST_REPORT = "/automatedTest/CaseTestReport/getReport"

    @classmethod
    def get_space_info(cls, space_id, authorization, origin=None):
        """
        获取空间信息
        :param space_id: 空间id
        :param authorization: authorization依赖从前端传过来
        :param origin:
        :return:
        ""
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_SPACE_INFO_PATH}'
        else:
            url = f'{cls.base_url}{cls.API_SPACE_INFO_PATH}'
            headers = deepcopy(cls.headers)

        headers.update({"authorization": authorization})
        resp = RequestUtil.post(url, headers=headers, data={"spaceKey": space_id}, convert_to_json=False)

        if resp.get("statusCode") != "000000":
            logger.warning(f"获取空间详情信息失败，resp={resp}, spaceKey={space_id}, url={url} {headers}")
            return None
        else:
            return resp.get("spaceInfo")

    @classmethod
    def get_api_info_pro(cls, space_id, project_id, api_id, authorization, origin=None):
        """
        获取API详情信息,获取的信息更全,但是需要authorization，authorization依赖从前端传过来
        :param space_id: 空间id
        :param project_id: 项目id
        :param api_id: eolinker api文档的数据库id
        :param authorization: authorization依赖从前端传过来
        :param origin:
        :return:
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_PRO_PATH}'
        else:
            url = f'{cls.base_url}{cls.API_PRO_PATH}'
            headers = deepcopy(cls.headers)

        headers.update({"authorization": authorization})
        resp = RequestUtil.post(url, headers=headers,
                                data={"spaceKey": space_id, "projectHashKey": project_id, "apiID": api_id},
                                convert_to_json=False)
        if resp.get("statusCode") != "000000":
            logger.warning(f"获取API详情信息失败，resp={resp}, spaceKey={space_id}, projectHashKey={project_id}, "
                           f"apiID={api_id}, url={url} {headers}")
            return None
        else:
            return resp.get("apiInfo")

    @classmethod
    def get_api_info_v3(cls, space_id, project_id, api_id, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin, space_id=space_id)
            url = (f'{base_url}{cls.API_V3_MANAGEMENT_PATH}/api?'
                   f'space_id={space_id}&project_id={project_id}&api_id={api_id}')
        else:
            url = (f'{base_url}{cls.API_V3_MANAGEMENT_PATH}/api?'
                   f'space_id={space_id}&project_id={project_id}&api_id={api_id}')
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.get(url, headers=headers)
        if resp.get("status") != "success":
            logger.warning(f"获取API详情信息失败，resp={resp}, space_id={space_id}, project_id={project_id}, "
                           f"api_id={api_id}, url={url} {headers}")
            return None
        else:
            return resp.get("data")

    @classmethod
    def get_api_info(cls, space_id, project_id, api_id, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin, space_id=space_id)
            url = f'{base_url}{cls.API_STUDIO_PATH}/api/api_info'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_PATH}/api/api_info'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.post(url, headers=headers, json={
            "space_id": space_id,
            "project_id": project_id,
            "api_id": api_id})
        if resp.get("status") != "success":
            logger.warning(f"获取API详情信息失败，resp={resp}, space_id={space_id}, project_id={project_id}, "
                           f"api_id={api_id}, url={url} {headers}")
            return None
        else:
            return resp.get("api_info")

    @classmethod
    def edit_api_test_case(cls, req_data, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STUDIO_PATH}/test_case/edit'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_PATH}/test_case/edit'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.post(url, headers=headers, json=req_data)
        if resp.get("status") != "success":
            logger.warning(f"编辑测试用例（API文档）失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, resp.get("error_info")
        else:
            return True, resp.get("status")

    @classmethod
    def execute_case(cls, space_id, project_id, case_id, env_id, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin, space_id=space_id)
            url = f'{base_url}{cls.API_CASE_EXECUTE}'
        else:
            url = f'{cls.base_url}{cls.API_CASE_EXECUTE}'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        data = {
            "space_id": space_id,
            "project_id": project_id,
            "case_id": case_id,
            "env_id": env_id
        }
        resp = RequestUtil.post(url, headers=headers, json=data)
        if resp.get("status") != "success":
            logger.warning(f"执行用例失败失败，resp={resp}, space_id={space_id}, project_id={project_id}, "
                           f"case_id={case_id}, env_id={env_id}, url={url} {headers}")
            return None
        else:
            return resp.get("report_id")

    @classmethod
    def get_step_info(cls, space_id, project_id, case_id, conn_id, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STEP_INFO}'
        else:
            url = f'{cls.base_url}{cls.API_STEP_INFO}'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})

        resp = RequestUtil.get(url, headers=headers, params={
            "space_id": space_id,
            "project_id": project_id,
            "case_id": case_id,
            "conn_id": conn_id})
        if resp.get("status") != "success":
            logger.warning(f"获取测试步骤详情信息失败，resp={resp}, space_id={space_id}, project_id={project_id}, "
                           f"case_id={case_id}, conn_id={conn_id}, url={url} {headers}")
            return None
        else:
            return resp

    @classmethod
    def get_case_info(cls, space_id, project_id, case_id, authorization, origin=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_CASE_INTO}'
        else:
            url = f'{cls.base_url}{cls.API_CASE_INTO}'
            headers = deepcopy(cls.headers)

        if authorization:
            headers.update({"Authorization": authorization})

        body = {
            "caseID": str(case_id),
            "spaceKey": space_id,
            "projectHashKey": project_id,
        }

        resp = RequestUtil.post(url, headers=headers,
                                data=body,
                                convert_to_json=False)

        if resp.get("statusCode") != "000000":
            logger.warning(f"获取测试用例详情信息失败，resp={resp}, spaceKey={space_id}, projectHashKey={project_id}, "
                           f"caseID={case_id}, url={url} {headers}")
            return None
        else:
            return resp

    @classmethod
    def get_case_test_report_list(cls, space_id, project_id, case_id, authorization, origin=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_CASE_TEST_REPORT_LIST}'
        else:
            url = f'{cls.base_url}{cls.API_CASE_TEST_REPORT_LIST}'
            headers = deepcopy(cls.headers)

        if authorization:
            headers.update({"Authorization": authorization})

        body = {
            "caseID": str(case_id),
            "spaceKey": space_id,
            "projectHashKey": project_id,
        }

        resp = RequestUtil.post(url, headers=headers,
                                data=body,
                                convert_to_json=False)

        if resp.get("statusCode") != "000000":
            logger.warning(f"获取测试用例详情信息失败，resp={resp}, spaceKey={space_id}, projectHashKey={project_id}, "
                           f"caseID={case_id}, url={url} {headers}")
            return None
        else:
            return resp.get("reportList", [])

    @classmethod
    def get_single_case_test_report(cls, space_id, project_id, case_id, report_id, authorization, origin=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_CASE_TEST_REPORT_LIST}'
        else:
            url = f'{cls.base_url}{cls.API_CASE_TEST_REPORT_LIST}'
            headers = deepcopy(cls.headers)

        if authorization:
            headers.update({"Authorization": authorization})

        body = {
            "caseID": str(case_id),
            "spaceKey": space_id,
            "projectHashKey": project_id,
            "reportID": report_id
        }

        resp = RequestUtil.post(url, headers=headers,
                                data=body,
                                convert_to_json=False)

        if resp.get("statusCode") != "000000":
            logger.warning(f"获取单个用例报告失败，resp={resp}, spaceKey={space_id}, projectHashKey={project_id}, "
                           f"caseID={case_id}, reportID={report_id}, url={url} {headers}")
            return None
        else:
            return resp.get("result", [])

    @classmethod
    def get_api_compare(cls, space_id, project_id, api_id, cur_version_id, old_history_id, authorization, origin=None):
        """
        @param space_id: 空间id
        @param project_id: 项目id
        @param api_id: api id
        @param old_history_id: 对比，旧历史版本版本号
        @param cur_version_id: 对比，新版本版本号
        @param authorization: 前端接口鉴权
        @param origin:
        @return: 元组，(oldApiInfo, newApiInfo)
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_COMPARE_PATH}'
        else:
            url = f'{cls.base_url}{cls.API_COMPARE_PATH}'
            headers = deepcopy(cls.headers)
        if authorization:
            headers.update({"Authorization": authorization})

        body = {
            "apiID": str(api_id),
            "spaceKey": space_id,
            "projectHashKey": project_id,
            "newHistoryID": str(cur_version_id),
            "oldHistoryID": str(old_history_id)
        }
        resp = RequestUtil.post(url, headers=headers, data=body, convert_to_json=False)
        if resp.get("statusCode") != "000000":
            logger.warning(f"获取API版本对比信息失败，resp={resp}, space_id={space_id}, project_id={project_id}, "
                           f"api_id={api_id}, url={url} {headers}"
                           f"old_history_id={old_history_id}, current_history_id={cur_version_id}")
            return None
        else:
            return resp.get("oldApiInfo"), resp.get("newApiInfo")

    @classmethod
    def get_user_info(cls, authorization, origin=None):
        # 内外网用的协议不一样导致
        if origin:
            base_url, _ = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}/common/User/getUserInfo'
        else:
            url = f'{cls.base_url}/common/User/getUserInfo'
        resp = RequestUtil.post(url, headers={"Authorization": authorization})
        if resp.get("statusCode") != "000000":
            logger.warning(f"获取用户信息失败，resp={resp}, url={url} {authorization}")
            return None
        else:
            return resp.get("userInfo")

    @classmethod
    def add_test_case_pro(cls, req_data, authorization, origin=None,
                          api_test_case_stage=ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST):
        """
        添加测试用例，前端请求的接口
        :param req_data: 请求数据
        :param authorization: authorization依赖从前端传过来
        :param origin:
        :param api_test_case_stage: 测试用例阶段
        :return:
        ""
        """
        if api_test_case_stage == ApiTestCaseConstant.ApiTestCaseStage.AUTOMATED_TEST:
            status, resp = cls.api_automated_test_case_request(req_data, authorization, path="addTestCase",
                                                               origin=origin)
        else:
            status, resp = cls.api_management_test_case_request(req_data, authorization, path="addTestCase",
                                                                origin=origin)
        if not status:
            logger.warning(f"添加测试用例失败，resp={resp}, req_data={req_data}")
            return False, None
        return True, resp.get("caseID")

    @classmethod
    def edit_test_case_info(cls, req_data, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_CASE_EDIT}'
        else:
            url = f'{cls.base_url}{cls.API_CASE_EDIT}'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.put(url, headers=headers, json=req_data)

        if resp.get("status") != "success":
            logger.warning(f"修改eolink测试用例基本信息失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False
        else:
            return True

    @classmethod
    def delete_test_case_pro(cls, req_data, authorization, origin=None):
        """
        删除测试用例，前端请求的接口
        :param req_data: 请求数据
        :param authorization: authorization依赖从前端传过来
        :param origin:
        :return:
        """
        status, resp = cls.api_automated_test_case_request(req_data, authorization, path="deleteTestCase",
                                                           origin=origin)
        if not status:
            logger.warning(f"删除测试用例失败，resp={resp}, req_data={req_data}")
            return False
        return True

    @classmethod
    def api_automated_test_case_request(cls, req_data, authorization, path, origin=None):
        """
        前端automatedTest/AutomatedTestCase公共请求方法
        :param req_data: 请求数据
        :param authorization: authorization依赖从前端传过来
        :param path: 请求路径
        :param origin:
        :return:
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_AUTOMATED_TEST_CASE}/{path}'
        else:
            url = f'{cls.base_url}{cls.API_AUTOMATED_TEST_CASE}/{path}'
            headers = deepcopy(cls.headers)

        headers.update({"authorization": authorization})
        resp = RequestUtil.post(url, headers=headers, data=req_data, convert_to_json=False)

        if resp.get("statusCode") != "000000":
            logger.warning(f"{path}失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, None
        return True, resp

    @classmethod
    def api_management_test_case_request(cls, req_data, authorization, path, origin=None):
        """
        前端apiManagementPro/TestCase公共请求方法
        :param req_data: 请求数据
        :param authorization: authorization依赖从前端传过来
        :param path: 请求路径
        :param origin:
        :return:
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_MANAGEMENT_TEST_CASE}/{path}'
        else:
            url = f'{cls.base_url}{cls.API_MANAGEMENT_TEST_CASE}/{path}'
            headers = deepcopy(cls.headers)

        headers.update({"authorization": authorization})
        resp = RequestUtil.post(url, headers=headers, data=req_data, convert_to_json=False)

        if resp.get("statusCode") != "000000":
            logger.warning(
                f"{cls.API_MANAGEMENT_TEST_CASE}/{path}失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, None
        return True, resp

    # 新增测试用例
    @classmethod
    def add_test_case(cls, req_data, origin=None, api_key=None):
        """
        请求eolinker创建用例
        :param req_data: 请求数据
        :param origin:
        :param api_key:
        :return:
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STUDIO_AUTOMATED_PATH}/test_case/add'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_AUTOMATED_PATH}/test_case/add'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.post(url, headers=headers, json=req_data)

        # {'type': 'test_case', 'status': 'success', 'data': 6}
        if resp.get("status") != "success":
            logger.warning(f"创建eolink测试用例失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, resp.get("error_info")
        else:
            return True, resp.get("data")  # 返回新增的测试用例id

    # 删除测试用例
    @classmethod
    def delete_test_case(cls, req_data, origin=None, api_key=None):
        """
        请求eolinker创建用例
        :param req_data: 请求数据
        :param origin:
        :param api_key:
        :return:
        """
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STUDIO_AUTOMATED_PATH}/test_case/delete'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_AUTOMATED_PATH}/test_case/delete'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.delete(url, headers=headers, json=req_data)

        # {'type': 'test_case', 'status': 'success'}
        if resp.get("status") != "success":
            logger.warning(f"删除eolink测试用例失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, resp.get("error_info")
        else:
            return True, resp.get("status")  # 返回新增的测试用例id

    # 新增测试步骤
    @classmethod
    def add_single_case_by_api_doc(cls, req_data, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STUDIO_AUTOMATED_PATH}/single_case/add_by_api_doc'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_AUTOMATED_PATH}/single_case/add_by_api_doc'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.post(url, headers=headers, json=req_data)
        if resp.get("status") != "success":
            logger.warning(f"添加用例测试步骤（API文档）失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, resp.get("error_info")
        else:
            return True, resp.get("status")

    # 查询测试用例详情
    @classmethod
    def get_test_case(cls, req_data, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STUDIO_AUTOMATED_PATH}/test_case/get'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_AUTOMATED_PATH}/test_case/get'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.get(url, headers=headers, params=req_data)
        if resp.get("status") != "success":
            logger.warning(f"查询测试用例详情失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return None
        else:
            return resp  # 返回查询结果

    # 编辑测试步骤
    @classmethod
    def single_case_edit(cls, req_data, origin=None, api_key=None):
        if origin:
            base_url, headers = cls.get_origin_url_and_headers(origin)
            url = f'{base_url}{cls.API_STUDIO_AUTOMATED_PATH}/single_case/edit'
        else:
            url = f'{cls.base_url}{cls.API_STUDIO_AUTOMATED_PATH}/single_case/edit'
            headers = deepcopy(cls.headers)
        if api_key:
            headers.update({"Eo-Secret-Key": api_key})
        resp = RequestUtil.put(url, headers=headers, json=req_data)
        if resp.get("status") != "success":
            logger.warning(f"编辑测试步骤失败，resp={resp}, req_data={req_data}, url={url} {headers}")
            return False, resp.get("error_info")
        else:
            return True, resp.get("status")


class ApiStudioHelper:
    manager = ApiStudioManager

    @classmethod
    def get_space_api_key(cls, space_id, authorization, origin=None):
        space_info = cls.manager.get_space_info(space_id, authorization, origin=origin)
        if space_info:
            return space_info.get("apiKey")
        else:
            return None
