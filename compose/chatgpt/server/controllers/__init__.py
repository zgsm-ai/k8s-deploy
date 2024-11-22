#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Author  ：范立伟33139
@Date    ：2023/3/16 9:42
"""

import logging

from flask import request, make_response

from common.helpers.application_context import ApplicationContext
from config import conf
from lib.jwt_session.session import JwtTokenHandler, JwtSession

logger = logging.getLogger(__name__)


def register_controller(app=None):
    from .system.session_controller import sessions
    from .system.users_controller import users
    from .V2.action_controller import actions
    from .system.prompt_square_controller import prompt_square
    from controllers.system.open_api_applications_controller import open_api_applications
    from controllers.system.configuration_controller import configuration
    from .V3.action_controller import actions_v3
    from .V4.action_controller import actions_v4
    from .ai_review.ai_review_controller import review
    from .ut_case.ai_test_controller import ut_case
    from .system.ai_record_controller import ai_record
    from .api_test.api_test_controller import api_test
    from controllers.context_navigation.code_navigation_controller import code_navigation
    from controllers.llm.v1 import v1
    from controllers.llm.llm import llm
    from controllers.llm.model import model
    from controllers.ai_e2e.ai_e2e_case_task_controller import e2e_case_task

    app.register_blueprint(e2e_case_task, url_prefix='/api/e2e_case_task')
    app.register_blueprint(sessions, url_prefix='/api/sessions')
    app.register_blueprint(users, url_prefix='/api/users')
    app.register_blueprint(actions, url_prefix='/api/v2')
    app.register_blueprint(prompt_square, url_prefix='/api/prompt_square')
    app.register_blueprint(open_api_applications, url_prefix='/api/open_api_applications')
    app.register_blueprint(configuration, url_prefix='/api/configuration')
    app.register_blueprint(actions_v3, url_prefix='/api/v3')
    app.register_blueprint(actions_v4, url_prefix='/api/v4')
    app.register_blueprint(v1, url_prefix='/api/inference/v1')
    app.register_blueprint(llm, url_prefix='/api/llm')
    app.register_blueprint(model, url_prefix='/api/model')
    app.register_blueprint(review, url_prefix='/api/review')
    app.register_blueprint(ai_record, url_prefix='/api/ai_record')
    app.register_blueprint(ut_case, url_prefix="/api/ut")
    app.register_blueprint(code_navigation, url_prefix="/api/code_navigation")
    app.register_blueprint(api_test, url_prefix="/api/api_test")

    @app.before_request
    def check_request():
        """
        根据规则校验请求是否能够通过, 校验登录
        """
        pass

    @app.after_request
    def add_header(response):
        return response


NAME = conf.get("jwt", {}).get("NAME")
ALG = conf.get("jwt", {}).get("ALGORITHM")
EXP = conf.get("jwt", {}).get("EXPIRE")
SECRET = conf.get("jwt", {}).get("SECRET")
DOMAIN = conf.get("jwt", {}).get("DOMAIN")


def registry_session(app):
    from services.system.open_api_applications_service import OpenApiApplicationService
    from services.system.users_service import users_service

    @app.before_request
    def before_request():
        headers = request.headers
        cookies = request.cookies
        app_id = ApplicationContext.get_current_app_id()
        jwt_handler = JwtTokenHandler(
            headers, cookies, NAME, SECRET, EXP, domain=DOMAIN, algorithm=ALG)
        # 解析获得session
        session = jwt_handler.parse()
        if isinstance(session, JwtSession):
            # 查询或者创建用户
            username = session.get('username')
            display_name = session.get('display_name')
            user = users_service.get_or_create_by_username_and_display_name(
                username, display_name)
            if not user:
                # 用户非法,清空session
                ApplicationContext.clear_session()
                return
        elif not session and app_id:
            try:
                open_app = OpenApiApplicationService.get_by_app_id(app_id=app_id)
                user = users_service.get_by_display_name(display_name=open_app.applicant)
                session = {
                    'username': user.username,
                    'display_name': user.display_name,
                    'is_admin': user.is_admin,
                    'email': user.email,
                    'access_ip': headers.get('X-Real-IP') if headers.get('X-Real-IP') else ''
                }
            except Exception as e:
                logger.error(e)
                return make_response('Unauthorized', 401)
        ApplicationContext.reset_session(session)

    @app.after_request
    def after_request(response):
        from common.exception.exceptions import NoLoginError
        try:
            try:
                user = ApplicationContext.get_current()
            except NoLoginError:
                user = None
            if user:
                # 用户登录才设置jwt_token
                from services.system.jwt_token_service import JwtTokenService
                j_t = JwtTokenService(request)
                jwt_token = j_t.gen_token()
                domain = None if DOMAIN == 'current' else DOMAIN
                data = dict(
                    expires=j_t.get_expire(EXP)
                )
                response.set_cookie(
                    NAME, jwt_token, **data)
                if domain:
                    data.update(domain=domain)

                    response.set_cookie(
                        NAME, jwt_token, **data)
        except Exception as err:
            logger.info(f'生成jwt_token失败：{str(err)}')
            # 该后置请求出现任何异常认为是认证失败, 不做处理，返回原请求
            pass
        finally:
            return response
