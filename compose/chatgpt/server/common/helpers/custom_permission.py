#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : 刘鹏z10807
@Date    : 2023/3/27 10:58
"""
import logging
import time
from functools import wraps

from flask import g, request, make_response, Response

from common.constant import OpenAppConstant, PromptConstant, ConfigurationConstant, ActionsConstant, ScribeConstant, \
    ServeConstant
from common.exception.exceptions import AuthFailError, PermissionFailError
from common.helpers.application_context import ApplicationContext
from distutils.version import LooseVersion
from services.system.api_rule_service import ApiRuleService
from services.system.configuration_service import ConfigurationService
from services.system.open_api_applications_service import OpenApiApplicationService
from third_platform.services.product_service import ProductService
from third_platform.services.analysis_service import analysis_service
from third_platform.services.user_service import UserService

logger = logging.getLogger(__name__)


class PermissionChecker:
    """
    权限检查
    """

    def __init__(self):
        pass

    @staticmethod
    def check_is_admin_or_creator(service):
        """校验是否是超管或创建者"""

        def outer(func):
            @wraps(func)
            def has_permission(*args, **kwargs):
                user = ApplicationContext.get_current()
                creator = service.get_by_id(kwargs.get('mid'))
                if not user or not creator:
                    raise AuthFailError(msg="您没有此操作权限。")
                elif not user.is_admin and user.display_name != creator.creator:
                    raise AuthFailError(msg="您没有此操作权限。")
                return func(*args, **kwargs)

            return has_permission

        return outer

    @staticmethod
    def check_open_api_permission(func):
        """校验访问开放api的权限"""

        @wraps(func)
        def has_permission(*args, **kwargs):
            app_id = ApplicationContext.get_current_app_id()
            data = OpenApiApplicationService.get_by_app_id(app_id=app_id)
            if not app_id or not data:
                raise AuthFailError(msg="您没有调用操作权限，可联系千流客服续期或者在设置页面申请API账号")
            if data.state_is_approval:
                raise AuthFailError(msg="API账号未审批，可联系千流客服进行审批")
            elif data.state_is_fail:
                raise AuthFailError(msg="API账号审批未通过，可联系千流客服寻求帮助")
            elif data.state_is_disable:
                raise AuthFailError(msg="API账号已禁用，不支持继续使用，可联系千流客服续期或者在设置页面重新申请API账号")
            elif data.state_is_expired:
                raise AuthFailError(msg="API账号已超期，不支持继续使用，可联系千流客服续期或者在设置页面重新申请API账号")
            return func(*args, **kwargs)

        return has_permission

    @staticmethod
    def check_open_api_delete_permission(func):
        """
        校验删除 开放api申请记录的权限
        申请人本人可删除
        部分state可删除
        """

        @wraps(func)
        def has_permission(mid):
            data = OpenApiApplicationService.get_by_id(mid)
            if data and data.applicant != g.current_user.display_name:
                raise AuthFailError(msg="您没有此操作权限。")
            elif data and data.state not in OpenAppConstant.ALLOW_DELETE_STATES:
                raise AuthFailError(msg="您没有此操作权限。")
            return func(mid)

        return has_permission

    @staticmethod
    def check_open_api_is_applicant_permission(func):
        """
        校验是否申请人本人 开放api申请记录的权限
        申请人本人可操作
        """

        @wraps(func)
        def has_permission(mid):
            data = OpenApiApplicationService.get_by_id(mid)
            if data and data.applicant != g.current_user.display_name:
                raise AuthFailError(msg="您没有此操作权限。")
            return func(mid)

        return has_permission

    @staticmethod
    def check_api_rule():
        """校验请求api权限"""
        work_id = g.current_user.username
        department = analysis_service.get_user_multilevel_dept(work_id)
        if ApiRuleService.user_rule_is_exist(g.current_user.display_name):
            return True
        elif ApiRuleService.dept_rule_is_exist(department):
            return True
        elif work_id.endswith(ServeConstant.EOLINKER_SUFFIX):
            # eolinker平台用户方通权限
            return True
        else:
            raise PermissionFailError(msg="抱歉，只支持研发体系+4大BG访问，您暂未被授权访问本应用！<br>如您是刚入职的新员工，请入职第二天再访问。")

    @staticmethod
    def check_plugin_user_permission(func):
        """校验插件用户权限，旧版本禁用对话功能"""

        @wraps(func)
        def has_permission(*args, **kwargs):
            user_agent = request.headers.get('user-agent')
            ide_version = request.headers.get('ide-version')
            ide_type = request.headers.get('ide')
            limit_version = get_editor_limit_version(ide_type)
            # --智能问答(智能问答, 解释代码)
            # 提醒升级场景 插件版本低于configuration的vscode_version,jbt_version
            # 若数据库没有配置或者请求头为'cicd service','qianliu-devops',  则不进行限制
            if request.get_json().get("action") in ["chat", "explain"] and limit_version \
                    and user_agent not in PromptConstant.DEVOPS_LABELS:
                if not ide_version or LooseVersion(ide_version) < LooseVersion(limit_version):
                    content = PromptConstant.OLD_PLUGIN_RETURN_MESSAGE
                    return Response(content, mimetype='text/plain')

            if user_agent in PromptConstant.PLUGIN_LABELS and not ide_version:
                user_display_name = g.current_user.display_name
                users = ConfigurationService.get_plugin_user()
                if users and users.attribute_value and user_display_name in users.attribute_value.split('|'):
                    content = PromptConstant.OLD_PLUGIN_RETURN_MESSAGE
                    if request.is_json:
                        if request.json.get('stream', True):
                            return Response(content, mimetype='text/plain')
                        response = make_resp_dict_by_action(request.json.get('action', ''), content)
                    else:
                        response = make_resp_dict_by_action('', content)
                    return make_response(response)
            return func(*args, **kwargs)

        return has_permission

    @classmethod
    def check_user_agent_permission(cls, func):
        """校验 user-agent白名单"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            user_agent = request.headers.get('user-agent', '')
            allow_user_agent_list = ConfigurationService.get_configuration_with_cache(
                ConfigurationConstant.PERMISSION_TYPE,
                ConfigurationConstant.ALLOW_USER_AGENT_KEY,
                ConfigurationConstant.ALLOW_USER_AGENT_DEFAULT
            ).split(',')
            if not user_agent.lower() in allow_user_agent_list:
                raise PermissionFailError(msg='抱歉，您没有此接口访问权限')
            return func(*args, **kwargs)

        return wrapper

    @classmethod
    def check_components_map_permission(cls, func):
        """待实现，暂时不用"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            raise PermissionFailError(msg='抱歉，您没有此接口访问权限')
            return func(*args, **kwargs)

        return wrapper

    @classmethod
    def check_user_is_product_member(cls, username, product_id):
        """
        check user is product member
        :param username: 操作人
        :param product_id:
        """
        # 判断用户是否在产品下
        product_users = ProductService.get_user_info_from_product(username, product_id)
        if isinstance(product_users, list) and len(product_users):
            return True
        # 判断用户是否在产品关联的用户组下
        # 获取用户所在的用户组
        user_groups = UserService.get_user_groups_by_username(username)
        if isinstance(user_groups, list) and len(user_groups):
            user_group_ids = [each.get('id') for each in user_groups]
        else:
            return False

        # 获取产品关联的用户组
        product_users = ProductService.get_user_group_from_product(product_id)
        if isinstance(product_users, list) and len(product_users):
            product_group_ids = [each.get('group', {}).get('id') for each in product_users]
        else:
            return False

        # 用户所在的用户组 和 产品关联的用户组 取交集
        if len(list(set(user_group_ids) & set(product_group_ids))) > 0:
            return True
        return False


def make_resp_dict_by_action(action, content):
    if action and action == ActionsConstant.SCRIBE:
        response = ScribeConstant.RESPONSE_TEMPLATE
        response['message'] = content
        return response
    else:
        response = PromptConstant.RESPONSE_TEMPLATE
        response['choices'][0]['message']['content'] = content
        response['created'] = int(time.time())
        return response


def get_editor_limit_version(editor_type="vscode"):
    """
    根据编辑器类型, 设置的环境变量 来获取预设值
    vscode和jetbrains版本号限制支持分开设置
    当只设置了一个版本时，两个插件都使用同一个版本限制
    """
    ide_limit_map = ConfigurationService.get_editor_limit_version()
    vscode_version = ide_limit_map.get("vscode_version")
    jbt_version = ide_limit_map.get("jbt_version")
    if editor_type == "vscode":
        return vscode_version or jbt_version
    else:
        return jbt_version or vscode_version
