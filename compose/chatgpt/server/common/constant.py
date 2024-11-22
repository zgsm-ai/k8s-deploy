#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    项目常量

    :作者: 苏德利 16646
    :时间: 2023/3/3 15:31
    :修改者: 刘鹏 z10807
    :更新时间: 2023/4/21 9:26
"""


class ActionsConstant:
    FIND_BUGS = "findProblems"
    ADD_TEST = "addTests"
    OPTIMIZE = "optimize"
    EXPLAIN = "explain"
    CHAT = "chat"
    ADVISE="advise"
    API_TEST_CASE = "apiTestCase"
    API_TEST_POINT_DOC_INSPECTOR = "apiTestPointDocInspector"
    API_TEST_CASE_REPEAT_VERIFIED = "apiTestCaseRepeatVerified"
    API_TEST_PARAM_TYPE_ERROR_VERIFIED = "apiTestParamTypeErrorVerified"
    API_TEST_CASE_MODIFY = "apiTestCaseModify"
    API_TEST_SINGLE_CASE = "apiTestSingleCase"
    API_TEST_GEN_STEP = "apiTestGenStep"
    API_TEST_GEN_ODG = "apiTestGenODG"
    GENERATE_API_TEST_POINT = "generateApiTestPoint"
    GENERATE_API_TEST_SET = "generateApiTestSet"
    GENERATE_CODE = "generateCode"
    GENERATE_CODE_BY_FORM = "generateCodeByForm"
    GENERATE_CODE_BY_ASK = "generateCodeByAsk"
    # e2e 用例生成========
    E2E_MANUAL_CASE_CHECK = "e2eManualCaseCheck"
    E2E_IDENTIFY_RELATIONSHIPS = "e2eIdentifyRelationships"
    E2E_STEP_INTENT_EXTRACT = "e2eStepIntentExtract"
    E2E_RAG_FILTER = "e2eRagFilter"
    E2E_CASE_GEN = "e2eCaseGen"
    # e2e 用例生成========
    JS2TS = "js2ts"
    REVIEW = "review"
    SCRIBE = "scribe"
    LANJUN_CLASSIFICATION = "lanjun_classification"
    ADD_DEBUG_CODE = "addDebugCode"  # 添加调试代码
    ADD_STRONGER_CODE = "addStrongerCode"  # 添加健壮性代码
    ADD_COMMENT = "addComment"  # 添加注释
    PICK_COMMON_FUNC = "pickCommonFunc"  # 公共函数提取
    SIMPLIFY_CODE = "simplifyCode"  # 精简代码
    GIVE_ADVICE = "giveAdvice"  # 给出建议
    CONTINUE = "continue"  # 续写
    ZHUGE_NORMALCHAT = 'zhuge_normal_chat'  # 诸葛普通聊天


class GenerateCodeAttr:
    GENERATION_TYPES = {
        "api_interface": "api interface",  # 接口
        "data_structure": "data interface",  # 数据结构
        "function": "function",  # 函数
        "class": "class",  # 类
    }


class GPTModelConstant:
    GPT_35 = "gpt-3.5"  # 使用 GPT_35_16K ，仅在请求参数中使用
    GPT_TURBO = "gpt-3.5-turbo"  # 使用 GPT_35_16K ，仅在请求参数中使用
    GPT_35_16K = "gpt-35-turbo-16k"  # 16k模型
    GPT_4 = "gpt-4"  # 128k模型
    GPT_4o = "gpt-4o"  # 128k模型
    GPT_35_CHAT_MODELS = [GPT_TURBO, GPT_35_16K]  # 支持模型列表
    DEEPSEEK_SEEK_CHAT = "deepseek-chat"
    CHAT_MODELS = [GPT_TURBO, GPT_35_16K, GPT_4, GPT_4o, DEEPSEEK_SEEK_CHAT, ]  # 支持模型列表


class GPTConstant:
    TIMEOUT = 120  # 单位: s
    GPT35_16K_MAX_TOKENS = 12000  # 输入上限12k
    GPT4_MAX_TOKENS = 60000  # 输入上限60k
    DEEPSEEK_SEEK_CHAT_TOKENS = 128000
    # 代码生成限制最大 token 数，要比最大 token 数小。
    CODE_GENERATE_MAX_PROMPT_TOKENS = GPT35_16K_MAX_TOKENS - 200

    # 响应格式类型
    RESPONSE_JSON_OBJECT = 'json_object'
    RESPONSE_FORMAT_TYPES = [RESPONSE_JSON_OBJECT]  # gpt新版支持返回格式类型列表

    SCRIBE_MAX_PROMPT_TOKENS = 6000  # 划词对话限制最大tokens

    MAX_CONTINUE_COUNT = 2  # 允许最大续写次数
    CONTINUE_SIGN = '\n----------续写----------\n'  # 续写标识
    # 允许自动续写actions
    ALLOW_CONTINUE_ACTIONS = [
        ActionsConstant.CONTINUE,
        ActionsConstant.SCRIBE,
        ActionsConstant.API_TEST_SINGLE_CASE
    ]

    # 完成原因
    class FinishReason:
        STOP = 'stop'  # API 返回了完整的模型输出。
        LENGTH = 'length'  # 由于 max_tokens 参数或标记限制，模型输出不完整。
        CONTENT_FILTER = 'content_filter'  # 由于内容筛选器的标志，省略了内容。
        NULL = 'null'  # API 回复仍在进行中或未完成。


class TikTokenEncodeType:
    CL100K_BASE = "cl100k_base"  # ChatGPT models, text-embedding-ada-002, include gpt-3.5-turbo
    P50K_BASE = "p50k_base"  # Code models, text-davinci-002, text-davinci-003
    R50K_BASE = "r50k_base"  # (or gpt2)	GPT-3 models like davinci


class ServeConstant:
    THREADS = 4  # waitress serve用于处理应用程序逻辑的线程数，默认为4。
    CONNECTION_LIMIT = 100
    DEFAULT_API_TYPE = "openai"
    AZURE_API_TYPE = "azure"
    EOLINKER_SUFFIX = "_eolinker"


class NullValueSort:
    """
    将None值排序放在前或者后
    """
    NULL_FIRST = 'null_first'
    NULL_LAST = 'null_last'


class AppConstant:
    DELETED = True
    REQUESTS_TIMEOUT_TIME = [2, 4, 8, 16, 32, 64]
    UNIT_TEST_USER = dict(username='w10458', display_name='刘铭哲w10458', is_admin=True, email='10458@sangfor.com')
    DEPT_CACHE_TIMEOUT = 86400  # 部门数据缓存24小时


class UserRole:
    ADMIN = "admin"  # 管理员
    USER = "user"  # 普通用户


class ErrorMsgs:
    TIMEOUT = 'Cancelling nested steps due to timeout'  # 任务执行时间超出设定的时间，默认60分钟
    GITLAB_NOT_RESPONDE = 'GitLab is not responding'  # gitlab 502报错关键字段


class AdminNoticeContent:
    """管理员通知内容"""
    CONTENT = '千流AI通知：\n用户{username}申请API账号。\n请前往后台管理进行审批：{chat_admin_url}'


class ApplicantNoticeContent:
    """申请人通知内容"""
    CONTENT = '千流AI通知：\n{first_line}{approve_remark}\n应用名称：{project_name}\n到期时间：{expiration_time}\n' \
              '申请原因：{application_reason}\n预期收益：{expected_profit}\n' \
              '更多操作，可前往千流AI平台：{chat_url}（跳转到千流ai首页）'


class OpenAppConstant:
    """开放应用"""
    APPROVAL = 'approval'  # 审批中
    APPROVED = 'approved'  # 审批通过
    FAIL = 'fail'  # 审批未通过
    DISABLE = 'disable'  # 已禁用
    EXPIRED = 'expired'  # 已超期
    STATE_CHOICES = (
        (APPROVAL, '审批中'),
        (APPROVED, '审批通过'),
        (FAIL, '审批未通过'),
        (DISABLE, '已禁用'),
        (EXPIRED, '已超期'),
    )
    ALLOW_DELETE_STATES = (FAIL, DISABLE, EXPIRED)  # 允许删除的状态
    ALLOW_NOTICE_STATES = (APPROVED, FAIL, DISABLE)  # 允许通知的状态
    APPROVE_REMARK_NOT_EMPTY_STATES = (FAIL, DISABLE)  # 审批备注必填的状态
    SQUARE_RETURN_STATES = (APPROVED, DISABLE, EXPIRED)  # 广场数据可返回的状态


class UserConstant:
    CACHE_KEY_API_KEY = "users:api_key"
    CACHE_KEY_ID = "users:id"
    CACHE_KEY_USERNAME = "users:username"
    # 用户头像背景色集合
    AVATAR_COLORS = ['#4179FF', '#3AC8FF', '#8439FF', '#E251F5', '#49F4BA', '#A2E40B', '#FFC800', '#FF8000', '#F55151',
                     '#FF5FA0']


class ApiRuleConstant:
    """api规则/权限"""
    DEPT = 'dept'
    USER = 'user'
    RULE_TYPE_CHOICES = (
        (DEPT, '部门'),
        (USER, '用户'),
    )
    ALLOW_COMPANY = '深信服科技股份有限公司'


class AnalysisConstant:
    CACHE_KEY_WORK_ID = 'Analysis:work_id'
    CACHE_KEY_DEPT_LIST = 'dept_list'


class ConfigurationConstant:
    CACHE_KEY_PREFIX = "configuration"
    PROMPT_TYPE = 'prompt'
    PROMPT_KEY_FORBID_STRING = 'forbidden_word'
    PROMPT_RE_MAX_LENGTH = 5000
    AD_ON = 'on'
    QIANLIU_AD_TYPE = 'qianliu_ad'
    ZHUGE_ADS_TYPE = 'zhuge_ads'
    LANGUAGE_TYPE = 'language'
    LANGUAGE_KEY_MAP = 'language_map'
    CACHE_KEY_LANGUAGE_MAP = 'language_map'
    CACHE_TYPE_IDE_CONFIG = 'ide_config'
    CACHE_KEY_SCRIBE_COMPONENTS = 'scribe_components'  # 划词可选组件库

    REVIEW_TYPE = 'review'
    CACHE_KEY_MAX_REVIEW_NUM = 'review_max_review_num'

    # prompt模板 其他每个action都有配置
    PROMPT_TEMPLATE = 'prompt_template'
    # 其他模板
    MANUAL_REVIEW_PROMPT = 'manual_review'
    AUTO_REVIEW_PROMPT = 'auto_review'
    # 划词对话模板
    SCRIBE_ADD_TAG_PROMPT = 'scribe_add_tag'
    SCRIBE_FILTER_COMPONENT_API = 'scribe_filter_api'
    SCRIBE_FILTER_DESC_PROMPT = 'scribe_filter_desc'
    SCRIBE_GENERATE_CODE_PROMPT = 'scribe_generate_code'
    SCRIBE_GENERAL_PROMPT = 'scribe_general'
    SCRIBE_MERGE_CODE_PROMPT = 'scribe_merge_code'
    SCRIBE_REPLACE_PROMPT = 'scribe_replace'
    # 续写模板
    CONTINUE_PROMPT = 'continue'
    # api 测试相关模板
    PYTEST_CASE_TEMPLATE = 'pytest_case_template'
    API_TEST_RANGE = 'api_test_range'

    # 权限
    PERMISSION_TYPE = 'permission'
    ALLOW_USER_AGENT_KEY = 'allow_user_agent'
    ALLOW_USER_AGENT_DEFAULT = 'node-fetch,qianliu-ai-jetbrains-plugin,cicd service,qianliu-devops'
    CODE_COMPLETION_TYPE = 'code_completion'

    SCRIBE_NEED_CAUSE_DEPT = 'need_cause_department'  # 划词对话 需要拒绝原因的部门

    # 单测配置表key定义
    UT_RULES = "ut_rules"
    UT_PLUGIN_VSCODE_MIN_VERSION = 'ut_plugin_vscode_min_version'  # vscode 单测插件最小版本
    UT_PLUGIN_JETB_MIN_VERSION = 'ut_plugin_jetbrains_min_version'  # jetbrains 单测插件最小版本
    UT_RESULT_FILE_SPC = 'ut_result_file_spc'  # 单测结果文件命名间隔符，用于根据文件名切割获取对应数据：文件名，方法命名，用例号
    UT_USE_MODEL = 'ut_use_model'  # 单测单测使用的模型
    UT_LANGUAGE = 'ut_language'  # 单测兼容语言配置
    UT_MAX_POINT = 'ut_max_point'  # 单测最大测试点配置
    UT_REQ_TIMEOUT = 'ut_req_timeout'  # sdk 请求超时时间
    UT_REQ_TIMES = 'ut_req_times'  # sdk 请求次数，用于超时重试
    UT_MAX_WORKERS = 'ut_max_workers'  # 当前使用模型sdk请求最大并发数
    UT_TOKEN_LENGTH = 'ut_token_length'  # 当前使用模型token配置
    UT_CASE_TEMPLATE = 'ut_case_template'  # 当前使用模型测试用例prompt模板
    UT_POINT_TEMPLATE = 'ut_point_template'  # 当前使用模型测试点prompt模板
    UT_OPEN_DEPT = 'ut_open_department'  # 单测生成 灰度放开的部门

    # 编辑器预设值
    EDITOR_LIMIT_TYPE = 'editor_limit_version'
    VSCODE_VERSION = 'vscode_version'
    JBT_VERSION = 'jbt_version'

    # 系统配置项
    SYSTEM_TYPE = 'system_config'
    SYSTEM_KEY = 'front_end'  # 前端通用

    # api_test相关
    API_TEST_KEY = 'api_test'
    CHECK_API_PARAMS_TYPE = 'check_api_params_type'  # 校验api_info中参数信息方式。相关子项定义查看CheckApiParamsType
    EOLINKER_BUNDLE_JS_VERSION = 'eolinker_bundle_js_version'  # eolinker平台js模块版本  用于校验是否需要刷新js模块

    # 模型控制值设置
    MODEL_BELONG_TYPE = "model"
    ENABLED_MODELS = "enable_models"

    # 上下文控制值设置
    CONTEXT_BELONG_TYPE = "context"
    CONTEXT_MAX_NUM = "context_max_num"

    # e2e 用例生成相关
    E2E_BELONG_TYPE = "e2e_test"
    E2E_MIN_CASE_SCORE = "min_case_score"
    E2E_MIN_CASE_SCORE_DEFAULT = 6  # 最低分数
    E2E_IS_CHECK_CASE = "is_check_case"  # 是否检查用例
    E2E_IS_CHECK_CASE_DEFAULT = "true"  # 默认开启


class PromptConstant:
    CACHE_KEY_FORBID_WORD = 'prompt_forbidden_word'
    CHECK_PARAM_LIST = ['prompt', 'code', 'custom_instructions', 'system_prompt']  # 需要校验敏感词的参数
    FORBID_WORD_RETURN_MESSAGE = '安全规定，提问词不允许包含 公司名称、密码等字样，请重新提问 （当前问题包含敏感词：{}）'
    OLD_PLUGIN_RETURN_MESSAGE = '为了提供更好的服务和用户体验，请升级到最新版本。升级完成之后，重启IDE即可。配置连接：http://docs.sangfor.org/x/rNnHDw '
    TOKENS_OVER_LENGTH = '您的提问超过了最大 token 数限制，请缩短提问后重试。'
    PLUGIN_LABELS = ['node-fetch', 'qianliu-ai-jetbrains-plugin']
    DEVOPS_LABELS = ['cicd service', 'qianliu-devops', 'tp service']
    RESPONSE_TEMPLATE = {
        'choices': [
            {
                'finish_reason': 'stop',
                'index': 0,
                'message': {
                    'content': '回答问题',
                    'role': 'assistant'
                }
            }
        ],
        'created': '1722650508',  # 需重新赋值当前 time.time()
        'id': 'chatcmpl-72bxP8TakrdRMN4Ln2b1VQrV2VpKJ',  # 根据需要重新赋值
        'model': None,  # 需指定对应model
        'object': 'chat.completion',
        'usage': {
            'completion_tokens': 34,
            'prompt_tokens': 50,
            'total_tokens': 84
        }
    }
    # 敏感词替换映射表（使用正则替换），键为替换后的字符，值为敏感词
    FORBIDDEN_WORD_MAP = {
        '_hello_': 'sangfor|sinfor|sangfor123|admin123|sangfor@123|Sangfor@123|sangforos',
        '_深圳_': '深信服|信服'
    }

    # 敏感词替换映射表 一对一 （皆为城市单词）
    SENSITIVE_WORD_MAP = {
        'Sangfor@123': 'Philadelphia',
        'sangfor@123': 'Colorado',
        'sangfor123': 'Pakistan',
        'sangforos': 'Illinois',
        'sangfor': 'Manchester',
        'sinfor': 'Alexander',
        'admin123': 'Hamilton',
        '深信服': 'Malaysia',
        '信服': 'Barcelona',
    }
    TARGET_WORD_MAP = {v: k for k, v in SENSITIVE_WORD_MAP.items()}


class ADConstant:
    CACHE_KEY_QIANLIU_AD = 'qianliu_ad'  # 千流广告配置缓存key
    CACHE_PREFIX_KEY = "AD"  # 用户广告缓存前缀key
    CACHE_TIMEOUT = 60 * 60 * 24 * 30  # 每个用户投放一次广告时间 1次/1月


class AIReviewConstant:
    TOKENIZER_PATH = 'runtime/tokenizer.json'
    MAX_TOKEN = 2048
    TREE_SITTER_LIB_PATH = 'runtime/languages.so'
    MAX_REVIEW_NUM = 5  # 单文件最多进行review数量（排除prompt超tokens的、直接复用结果的，实际需要请求review的数量）
    STREAM_SEPARATOR = '#data_id#'

    class ReviewType:
        AUTO = 'auto'  # 自动
        MANUAL = 'manual'  # 手动
        CHOICES = (
            (AUTO, '自动'),
            (MANUAL, '主动'),
        )

    class ReviewState:
        INIT = 'init'  # 初始
        SUCCESS = 'success'  # 成功
        FAIL = 'fail'  # 失败
        CHOICES = (
            (INIT, '初始'),
            (SUCCESS, '成功'),
            (FAIL, '失败')
        )

    class Flag:
        REPAIR = 'repair'  # 标记为解决
        NO_REPAIR = 'no_repair'  # 标记为不修复
        REJECT = 'reject'  # 拒绝此问题

        SKIP_REVIEW = (NO_REPAIR, REJECT)  # 跳过
        REUSE_REVIEW = ('', REPAIR)  # 复用

        CHOICES = (
            (REPAIR, '标记为解决'),
            (NO_REPAIR, '标记为不修复'),
            (REJECT, '拒绝此问题'),
        )

    TREE_SITTER_CODE_TYPE_MAP = {
        'vue': ['method_definition'],
        'javascript': ['method_definition', 'function_declaration'],
        'typescript': ['method_definition', 'function_declaration'],
        'python': ['function_definition'],
        'go': ['function_declaration'],
        'c': ['function_definition'],
        'bash': ['function_definition'],
        'lua': ['function_definition_statement'],
        'java': ['method_declaration'],
        'php': ['function_definition', 'method_declaration'],
        'ruby': ['method', 'singleton_method']
    }


class AskStreamConfig:
    # 循环次数太少容易误杀，提高一点
    LOOP_COUNT_LIMIT = 30


class CodeCompletionConstant:
    allow_departments = 'allow_department'


class ScribeConstant:
    ES_ID_TITLE = "dmsc"
    RESPONSE_TEMPLATE = {
        "success": False,
        "message": '我是一个问题回答人工智能，可以访问互联网并以中文 markdown 格式回答问题。',
        "data": None
    }
    # 划词生成代码的系统预设
    SCRIBE_SYSTEMS = [
        """You are an experienced development engineer.
        Your task is to implement code that meets the requirements,
        and the result needs to be compared with the selected code for diff differences,
        so you need to make sure that you do not omitted code for brevity,
        and finally, use the markdown format in output"""]
    # 中间处理类型
    ADD_TAG = 'add_tag'
    VECTOR_RECALL = 'vector_recall'
    BASIC_SAFEGUARD = 'basic_safeguard'
    FILTER_DESC = 'filter_desc'
    FILTER_API = 'filter_api_docs'
    GENERATE_CODE = 'generate_code'
    MERGE_CODE = 'merge_code'
    keyword_dict = {"表格": "表格", "表单": "表单", "详情列": "多列详情列"}
    # 允许前端指定组件库的语言
    CUSTOM_COMPONENT_ALLOW_LANGUAGES = ['javascript', 'typescript', 'html', 'vue']
    # 各文档中组件的正则表达式
    component_patterns = [
        r'(?<![A-Za-z\u4e00-\u9fa5])<([a-zA-Z0-9-]+)',  # 匹配组件名
        r'import .*?\{([^\}]+)\} from',  # 匹配带{}的导入的hook
        r'import (\w+[\s,]*\w*)+ from'  # 匹配不带{}的导入的hook
    ]
    exclude_component_list = ["a", "div", "template", "style", "script", "p", "img", "span", "i", "section", "h2", "h1"]


class CheckApiParamsType:
    """
    # 校验api_info中参数信息方式
    """
    # 1、close不校验；2、request仅校验入参；3、all校验入参和出参
    CLOSE = "close"
    REQUEST = "request"
    ALL = "all"


class ApiTestConstant:
    generate_test_set_size = 5  # 每次生成测试集个数（防止单次请求内容多）


class ApiTestCaseConstant:
    """API测试用例相关常量"""
    CELERY_API_CASE_QUEUE = "celery-api-test-case"  # celery队列名称"
    CELERY_EOLINKER_CASE_QUEUE = "celery-api-test-eolinker_case"  # celery队列名称"
    LOCK_API_TESTCASES_TASK_KEY = "lock_api_testcases_task-{display_name}"  # 用户任务数 redis-key
    TASK_TIMEOUT = 60 * 60  # 任务执行超时时间，1h

    class ApiTestCaseTaskStatus:
        # 与celery状态对应
        PENDING = 'PENDING'  # 排队中
        STARTED = 'STARTED'  # 进行中
        SUCCESS = 'SUCCESS'  # 成功
        REVOKED = 'REVOKED'  # 中止
        FAILURE = 'FAILURE'  # 失败
        CHOICES = (
            (PENDING, '排队中'),
            (STARTED, '进行中'),
            (SUCCESS, '成功'),
            (FAILURE, '失败'),
            (REVOKED, '中止')
        )
        FINAL_STATUS = [SUCCESS, FAILURE, REVOKED]

    class ApiTestEolinkerCaseTaskStatus:
        # 与celery状态对应
        PENDING = 'PENDING'  # 排队中
        STARTED = 'STARTED'  # 进行中
        SUCCESS = 'SUCCESS'  # 成功
        REVOKED = 'REVOKED'  # 中止
        FAILURE = 'FAILURE'  # 失败
        CHOICES = (
            (PENDING, '排队中'),
            (STARTED, '进行中'),
            (SUCCESS, '成功'),
            (FAILURE, '失败'),
            (REVOKED, '中止')
        )
        FINAL_STATUS = [SUCCESS, FAILURE, REVOKED]

    class ApiTestCaseTaskEventsType:
        # 事件类型
        GET_EOLINKER_DATA = 'get_eolinker_data'
        ASK_AI_TEST_POINTS = 'ask_ai_test_points'
        # 生成api依赖图
        ASK_AI_API_ODG = 'ask_ai_api_odg'
        ASK_AI_TEST_STEPS = 'ask_ai_test_steps'
        ASK_AI_TEST_SETS = 'ask_ai_test_sets'
        CREATE_TEST_CASE = 'create_test_case'
        MODIFY_TEST_CASE = 'modify_test_case'
        API_TEST_CASE_REPEAT_VERIFIED = 'ai_test_points_repeat_verified'
        CHOICES = (
            (GET_EOLINKER_DATA, '查询eolinker数据'),
            (ASK_AI_TEST_POINTS, '询问AI测试点'),
            (ASK_AI_API_ODG, '询问AI生成api依赖图'),
            (ASK_AI_TEST_STEPS, '询问AI测试步骤'),
            (ASK_AI_TEST_SETS, '询问AI测试集'),
            (CREATE_TEST_CASE, '创建测试用例'),
            (MODIFY_TEST_CASE, '修改测试用例'),
            (API_TEST_CASE_REPEAT_VERIFIED, API_TEST_CASE_REPEAT_VERIFIED)
        )

    class ApiTestCaseTaskEventsStatus:
        # 事件状态
        STARTED = 'STARTED'  # 进行中
        SUCCESS = 'SUCCESS'  # 成功
        FAILURE = 'FAILURE'  # 失败
        REVOKED = 'REVOKED'  # 中止
        CHOICES = (
            (STARTED, '进行中'),
            (SUCCESS, '成功'),
            (FAILURE, '失败'),
            (REVOKED, '中止'),
        )
        FINAL_STATUS = [SUCCESS, FAILURE, REVOKED]
        ABNORMAL_STATUS = [FAILURE, REVOKED]

    class ApiTestCaseTags:
        UPDATED = 'AI-已更新'

    class ApiTestCaseStage:
        MANAGEMENT = 'management'  # eolinker平台API文档管理页面测试用例
        AUTOMATED_TEST = 'automated_test'  # eolinker平台API自动化测试页面测试用例


class AiE2ECaseConstant:
    # e2e 的es记录id
    ES_ID_TITLE = "e2e"

    class AcceptType:
        # 未接受，部分接受，全部接受
        NOT_ACCEPT = "no_accept"
        PART_ACCEPT = "part_accept"
        ALL_ACCEPT = "all_accept"
        CHOICES = (
            (NOT_ACCEPT, '未接受'),
            (PART_ACCEPT, '部分接受'),
            (ALL_ACCEPT, '全部接受'),
        )

    class AiE2ECaseTaskStatus:
        # 所有任务状态
        # 进行中
        STARTED = 'STARTED'
        # 成功
        SUCCESS = 'SUCCESS'
        # 失败
        FAILURE = 'FAILURE'
        # 中止
        REVOKED = 'REVOKED'
        CHOICES = (
            (STARTED, '进行中'),
            (SUCCESS, '成功'),
            (FAILURE, '失败'),
            (REVOKED, '中止'),
        )
        # 最终状态
        FINAL_STATUS = [SUCCESS, FAILURE, REVOKED]
        # 异常状态
        ABNORMAL_STATUS = [FAILURE, REVOKED]

    # 事件类型
    EVENT_CHECK_CASE = 'check_case'
    EVENT_CHECK_CASE_NAME = '检查用例有效性'
    EVENT_IDENTIFY_RELATIONSHIPS = 'identify_relationships'
    EVENT_IDENTIFY_RELATIONSHIPS_NAME = '用例步骤和期望结果关系识别'
    EVENT_INTENT_EXTRACT = 'intent_extract'
    EVENT_INTENT_EXTRACT_NAME = '用例步骤意图提取'
    EVENT_KNOWLEDGE_SEEKER = 'knowledge_seeker'
    EVENT_KNOWLEDGE_SEEKER_NAME = '检索上下文'
    EVENT_RAG_FILTER = 'rag_filter'
    EVENT_RAG_FILTER_NAME = '知识重排和过滤'
    EVENT_GEN_CASE = 'e2e_case_gen'
    EVENT_GEN_CASE_NAME = '自动化用例生成'

    # 检查用例阶段
    NODE_CHECK_CASE = {
        "node_name": EVENT_CHECK_CASE_NAME,
        "node_id": EVENT_CHECK_CASE,
        "node_type": "script"
    }

    # 手工用例步骤和期望结果关系识别
    NODE_IDENTIFY_RELATIONSHIPS = {
        "node_name": EVENT_IDENTIFY_RELATIONSHIPS,
        "node_id": EVENT_IDENTIFY_RELATIONSHIPS_NAME,
        "node_type": "llm"
    }

    # 用例步骤意图提取
    NODE_INTENT_EXTRACT = {
        "node_name": EVENT_INTENT_EXTRACT_NAME,
        "node_id": EVENT_INTENT_EXTRACT,
        "node_type": "llm"
    }

    # 检查上下文阶段
    NODE_KNOWLEDGE_SEEKER = {
        "node_name": EVENT_KNOWLEDGE_SEEKER_NAME,
        "node_id": EVENT_KNOWLEDGE_SEEKER,
        "node_type": "knowledge_seeker"
    }

    # 检查过滤结果
    NODE_RAG_FILTER = {
        "node_name": EVENT_RAG_FILTER_NAME,
        "node_id": EVENT_RAG_FILTER,
        "node_type": "rag"
    }

    # 检查过滤结果
    NODE_GEN_CASE = {
        "node_name": EVENT_GEN_CASE_NAME,
        "node_id": EVENT_GEN_CASE,
        "node_type": "llm"
    }

    EVENTS_CHOICES = (
        (EVENT_CHECK_CASE_NAME, EVENT_CHECK_CASE_NAME),
        (EVENT_INTENT_EXTRACT, EVENT_INTENT_EXTRACT_NAME),
        (EVENT_KNOWLEDGE_SEEKER, EVENT_KNOWLEDGE_SEEKER_NAME),
        (EVENT_RAG_FILTER, EVENT_RAG_FILTER_NAME),
        (EVENT_GEN_CASE, EVENT_GEN_CASE_NAME),
    )


class DifyAgentConstant:
    DIFY_CHAT_CELERY_QUEUE = "dify_chat_celery_queue"
    CELERY_TASK_TIMEOUT = 60 * 60  # 任务执行超时时间，1h

    CACHE_KEY_ZHUGE_ADS = "CACHE_KEY_ZHUGE_ADS"  # 千流诸葛页面推荐词列表缓存key
    """
    [{
        "title": "",         # 首页展示标题
        "prompt": "",        # 具体提示词(点击后面板展示的内容),若不存在则取 title 为提示词
        "use_agent": true    # 是否启用智能团
    }]
    """

    AGENT_CHAT_DONE_MSG = "[DONE]"

    ROLE_OBSERVER = 'observer'  # 智能团观察者角色
    ROLE_GROUP_MEMBER = 'group_member'  # 智能团团员
    ROLE_GROUP_GUARDIAN = 'group_guardian'  # 智能团守卫者，兜底角色
    ROLE_NORMAL_CHAT = 'normal_chat'  # 普通聊天角色

    AGENT_THOUGHT_EVENT = "dify_agent_thought"
    AGENT_ADVISE_EVENT = "agent_advise"
    AGENT_START_EVENT = "agent_start"
    AGENT_END_EVENT = "agent_end"

    ROLE_CHOICES = (
        (ROLE_OBSERVER, '观察者'),
        (ROLE_GROUP_MEMBER, '群成员'),
        (ROLE_NORMAL_CHAT, '普通聊天')
    )

    # agent的服务于后台的展示提取规则，比如：历史会话里的名字获取
    AGENT_DISPLAY_NAME_PATTERN = r'\|([^\|]*)'
    # agent的服务于前端的展示提取规则
    AGENT_UI_PATTERN = r'^(.*?)\|'


class LoggerNameContant:
    DIFY_CHAT = "dify_chat"
    SOCKET_SERVER = "socket_server"
    SIO = "socketio"


class ContextNavigationConstant:
    # context的redis缓存key
    code_navigation_context_redis_key = "cnc-{uuid}"
    get_local_context_redis_key = "glc-{uuid}"
    cnc_redis_ex_time = 60 * 60  # 缓存时间 1小时

    # 动态上下文的key
    get_file_content_action = "get_file_content"
    get_file_sign_action = "get_file_sign"
    get_sign_contents_action = "get_sign_contents"


class UserBehaviorAction:
    # IDE端用户的四种交互行为，后期可继续扩展
    user_behavior = ["copy", 'accept', 'diff', 'ctrlc']
    behavior_keys = {
        "copy": "user_copy",
        "accept": "user_accept",
        "diff": "user_diff",
        "ctrlc": "user_ctrlc"
    }


# 模型供应商
class LLMProvider:
    OPENAI = "OpenAi"
    AZURE_OPENAI = "AzureOpenAI"

    LLM_PROVIDER_CHOICES = (
        (OPENAI, 'OpenAi'),
        (AZURE_OPENAI, 'AzureOpenAI'),

    )


# 模型组合类型
class LLMType:
    CHAT_COMPLETION = "chat_completion"
    COMPLETIONS = "completions"
    EMBEDDING = "embedding"

    LLM_TYPE_CHOICES = (
        (CHAT_COMPLETION, '会话'),
        (COMPLETIONS, '补全'),
        (EMBEDDING, '向量')
    )


# 模型组合类型
class LLMCombinationType:
    SINGLE = "single"
    COMBINATION = "combination"

    COMBINATION_TYPE_CHOICES = (
        (SINGLE, '单个'),
        (COMBINATION, '组合')
    )


# 模型级别
class LLMRank:
    SYSTEM = "system"
    USER = "user"

    RANK_CHOICES = (
        (SYSTEM, '系统'),
        (USER, '用户')
    )


class ConversationRole:
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
