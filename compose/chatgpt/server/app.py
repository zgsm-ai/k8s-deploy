#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging

from flask import Flask, request, make_response, jsonify, Response, g
#from flasgger import Swagger

from admin import register_admin
from bot.bot_util import get_chat_model
from common.exception import register_exception
from common.helpers.custom_json_encoder import CustomJSONEncoder
from common.helpers.custom_permission import PermissionChecker
from common.helpers.custom_throttle import register_throttle
from common.helpers.response_helper import Result
from bot.cache import get_redis
from services.answer import AnswerService
from template import explain_code, find_bugs, generate_unit_test, improve_readability, generate_code, js2ts
from common.constant import ActionsConstant, GPTModelConstant, AppConstant
from config import conf
from db import db
from common.helpers.application_context import ApplicationContext
from controllers import register_controller, registry_session
from logger import register_logger
from common.exception.exceptions import NoLoginError

CHATGPT_VERSION = "1.5.9"

MODELS = [
    {
        "label": "gpt-3.5-turbo", "value": GPTModelConstant.GPT_TURBO, "desc": "gpt-3.5-turbo", "default": True
    },
    {
        "label": "gpt-4", "value": GPTModelConstant.GPT_4, "desc": "gpt-4"
    }
]

WHITE_LIST_PATHS = [
    '/api/test',
    '/api/sessions/idtrust',
    '/api/sessions/idtrust_callback',
    # '/api/users/current'
    # TODO agent 过程的 context 更新接口，给 dify 用的，后续再考虑鉴权
    '/api/v4/agent/context',
    "/api/llm/list",
    "/api/inference/v1/chat/completions",
    "/api/inference/v1/completions",
    "/api/inference/v1/embeddings"
]

def software_version():
    """
    获取软件版本
    正常情况下软件版本定义在代码中，随着软件代码变更由程序员维护，
    特殊情况下，系统管理员可以通过环境变量CHATGPT_VERSION定义版本号
    """
    if "CHATGPT_VERSION" in os.environ:
        return os.environ["CHATGPT_VERSION"]
    else:
        return CHATGPT_VERSION

def print_logo():
    try:
        print("""
    ███████╗██╗  ██╗██╗   ██╗ ██████╗ ███████╗       █████╗ ██╗
    ╚══███╔╝██║  ██║██║   ██║██╔════╝ ██╔════╝      ██╔══██╗██║
      ███╔╝ ███████║██║   ██║██║  ███╗█████╗  █████╗███████║██║
     ███╔╝  ██╔══██║██║   ██║██║   ██║██╔══╝  ╚════╝██╔══██║██║
    ███████╗██║  ██║╚██████╔╝╚██████╔╝███████╗      ██║  ██║██║
    ╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝      ╚═╝  ╚═╝╚═╝
        """)
        print(f"    version:  {software_version()}")
    except UnicodeEncodeError:
        print("ZHUGE-AI START")


def create_app():
    print_logo()
    app = Flask(__name__)
    app.config.update(conf.get("flask_config"))
    # custom json encoder
    app.json_encoder = CustomJSONEncoder
#    swagger = Swagger(app)

    # # register db mamager
    db.init_app(app)
    register_throttle(app)
    registry_session(app)
    register_admin(app)
    register_exception(app)
    register_logger(app)
    
    logging.info("create_app: starting...")

    def access_by_rules(current_path):
        # pylint: disable=no-member
        api_ban_list = conf.get('API_BAN_LIST', list())
        current_path = request.path
        if api_ban_list and current_path in api_ban_list:
            return False
        return True

    @app.before_request
    def check_request():
        """
        根据规则校验请求是否能够通过
        """
        access = True
        # api黑名单规则
        current_path = request.path
        access = access and access_by_rules(current_path)
        # 其他禁用规则
        # ·····
        if not access:
            return Result.fail(message='禁止访问')
        elif current_path == '/favicon.ico':  # 图标访问时省掉校验逻辑
            return
        try:
            for path in WHITE_LIST_PATHS:
                if request.path == path:
                    return
            if current_path.startswith("/admin"):
                return
            if request.path.startswith("/static"):
                return
            access_info = None

            # 跨域验证
            if request.method == 'OPTIONS':
                return Result.success()

            try:
                access_info = ApplicationContext.get_current()
            except NoLoginError:
                if conf.get('user_agent') and current_path.startswith("/api/completions") and \
                        conf.get('user_agent') in request.headers.get('User-Agent', 'Chrome/75.0.3770.142'):
                    # 临时针对IDE的插件类型请求进行放行
                    logging.warning('临时针对IDE的插件类型请求进行放行')
                    access_info = AppConstant.UNIT_TEST_USER
                _env = os.environ.get("FLASK_ENV")
                # 测试或者开发环境使用
                from services.system.users_service import UsersService
                if _env == 'development' or _env == 'test':
                    user = UsersService.create_test_user()
                    ApplicationContext.update_session_user(user)
                    access_info = ApplicationContext.get_current()
            if not access_info:
                raise Exception('认证失败')
            # 当前请求用户信息缓存到当前请求上下文，需要使用数据可用 g.current_user 获取
            g.current_user = access_info
            g.authorization = request.headers.get("Authorization", None)
        except Exception as err:
            logging.error('Unauthorized:' + str(err))
            if current_path.startswith("/api/completions"):
                if not request.headers.get('api-key'):
                    # 这里针对插件历史版本提供一个更新提示，老版本无api-key
                    return make_response('检测到当前插件版本不是最新版本，请先升级插件版本。\n'
                                         '插件下载地址：http://docs.sangfor.org/x/yJ0YDw', 401)
                else:
                    return make_response('Unauthorized: 认证失败，请到插件配置页面更新Token', 401)
            return make_response('Unauthorized', 401)

        # 校验请求api权限
        #PermissionChecker.check_api_rule()

    @app.after_request
    def add_header(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = "true"
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PATCH, DELETE, PUT'
        response.headers['Access-Control-Max-Age'] = '3600'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept,' \
                                                           'Api-Key, ide, ide-version, ide-real-version, host-ip, User-Agent, ' \
                                                           'Model, Authorization, Cookie'
        response.headers['Access-Control-Expose-Headers'] = 'resp_id, mock_stream'
        return response

    def format_prompt_string(string):
        return '{{' + str(string) + '}}'

    def get_vscode_prompt(data):
        """
        :param data: request参数，字典格式
        :return prompt:
        """
        app_conversation_id = data.get("conversation_id")
        action = data.get("action", "")
        language = data.get("language", "")
        selected_text = data.get("code", "")
        custom_instructions = data.get("custom_instructions", "")
        if action == ActionsConstant.FIND_BUGS:
            prompt = find_bugs.INITIAL_PROMPT.format(language=format_prompt_string(language),
                                                     custom_instructions=custom_instructions,
                                                     selectedText=format_prompt_string(selected_text))
        elif action == ActionsConstant.ADD_TEST:
            prompt = generate_unit_test.INITIAL_PROMPT.format(language=format_prompt_string(language),
                                                              custom_instructions=custom_instructions,
                                                              selectedText=format_prompt_string(selected_text))
        elif action == ActionsConstant.OPTIMIZE:
            prompt = improve_readability.INITIAL_PROMPT.format(language=format_prompt_string(language),
                                                               custom_instructions=custom_instructions,
                                                               selectedText=format_prompt_string(selected_text))
        elif action == ActionsConstant.EXPLAIN:
            prompt = explain_code.INITIAL_PROMPT.format(custom_instructions=custom_instructions,
                                                        selectedText=format_prompt_string(selected_text))
        elif action == ActionsConstant.GENERATE_CODE:
            prompt = generate_code.INITIAL_PROMPT.format(custom_instructions=custom_instructions,
                                                         content=format_prompt_string(selected_text))
        elif action == ActionsConstant.JS2TS:
            prompt = js2ts.INITIAL_PROMPT.format(language=format_prompt_string(language),
                                                 custom_instructions=custom_instructions,
                                                 selectedText=format_prompt_string(selected_text))
        else:
            # chat类型
            prompt = data.get("prompt", "")
        return prompt, app_conversation_id

    @app.route("/")
    def index():
        """
        空
        ---
        tags:
        - system
        responses:
        200:
            result: 结果
        """
        return "hello"

    @app.route("/models")
    def models():
        """
        模型列表
        ---
        tags:
        - LLM
        responses:
        200:
            result: 结果
        """
        return make_response(jsonify(MODELS))

    # 兼容两个接口
    @app.route("/answer", methods=["POST"])
    @app.route("/answer/", methods=["POST"])
    def answer():
        """
        问答
        ---
        tags:
        - 问答
        responses:
        200:
            result: 结果
        """
        return AnswerService().answer()

    @app.route("/api/completions", methods=["POST"])
    @PermissionChecker.check_user_agent_permission
    @PermissionChecker.check_plugin_user_permission
    def completion():
        """
        补全
        ---
        tags:
        - 补全
        responses:
        200:
            result: 结果
        """
        data = request.get_json()
        user = ApplicationContext.get_current()
        data['path'] = request.path
        data["ide"] = request.headers.get('ide', '')
        data["ide_version"] = request.headers.get('ide-version', '')
        data["ide_real_version"] = request.headers.get('ide-real-version', '')
        data['user_agent'] = request.headers.get("User-Agent")
        data['host'] = request.headers.get("Host")
        data['display_name'] = user.display_name
        prompt, app_conversation_id = get_vscode_prompt(data)
        data['prompt'] = prompt
        data['conversation_id'] = app_conversation_id
        
        stream = data.get("stream", False)
        # 是否开启上下文管理模式
        context_association = data.get("association", True)
        # data['context_association'] = context_association

        # 区别于应用的对话 id，还有 chat 自身的对话 id、message id
        model = get_chat_model(action=data.get('action', ActionsConstant.CHAT), request_data=data)
        data['model'] = model

        redis = get_redis(conf)
        from bot.apiBot import Chatbot as apiBot
        chatbot = apiBot(redis=redis, model=model)

        if stream:
            response = chatbot.ask_stream(prompt, temperature=0, 
                context_association=context_association, request_data=data)
            return Response(response, mimetype='text/plain')
        response = chatbot.ask(prompt, temperature=0, 
            context_association=context_association, request_data=data)
        return make_response(jsonify(response))

    @app.route("/api/test", methods=["POST"])
    def test_performance():
        """
        仅用于测试并发
        ---
        tags:
        - system
        responses:
        200:
            result: 结果
        """
        data = request.get_json()
        import time
        import logging
        from random import randint
        random_sleep = randint(1, 10)
        logging.warning(f"just test, sleep {random_sleep}")
        time.sleep(random_sleep)
        data['random_sleep'] = random_sleep
        return make_response(jsonify(data))

    register_controller(app)
    return app
