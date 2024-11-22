#!/usr/bin/python
# -*- coding:utf-8 -*-
# @author  : 王政
# @time    : 2024/9/10 17:32
# @desc:
import logging
from copy import deepcopy

from common.utils.request_util import RequestUtil
from third_platform.tp import TpConfig

logger = logging.getLogger(__name__)


class TpManager(TpConfig):
    """
    此类主要打通 TP 平台的相关接口
    """
    # 获取用例详情
    API_GET_CASE_INFO = "api/v1/versions/{version_id}/cases/{case_id}/?project_id={project_id}"
    # 获取用例模块路径
    API_GET_CASE_MODULE_PATH = "api/v1/versions/{version_id}/directorys/_detail/?dir_code={dir_code}&case_id={case_id}"

    @classmethod
    def get_case_info(cls, case_id, project_id, version_id):
        """
        获取TP用例信息
        :param case_id: 用例id
        :param project_id: 项目id
        :param version_id:
        :return:
        ""
        """
        url = cls.base_url + cls.API_GET_CASE_INFO.format(
            case_id=case_id,
            project_id=project_id,
            version_id=version_id
        )
        headers = deepcopy(cls.headers)
        headers["PROJECT-ID"] = str(project_id)
        headers["VERSION-ID"] = str(version_id)
        resp = RequestUtil.get(url, headers=headers, convert_to_json=False)

        return resp

    @classmethod
    def get_case_path(cls, case_id, project_id, version_id, dir_code):
        """
        获取TP用例模块路径
        :param case_id: 用例id
        :param project_id: 项目id
        :param version_id:
        :param dir_code:
        :return:
        ""
        """
        url = cls.base_url + cls.API_GET_CASE_MODULE_PATH.format(
            case_id=case_id,
            dir_code=dir_code,
            version_id=version_id
        )
        headers = deepcopy(cls.headers)
        headers["PROJECT-ID"] = str(project_id)
        headers["VERSION-ID"] = str(version_id)
        resp = RequestUtil.get(url, headers=headers, convert_to_json=False)

        return resp
