from dataclasses import dataclass
from typing import Dict, List
from common.constant import GPTModelConstant, ActionsConstant

        # # 查询信息
        # self.action: str = data.get("action", ActionsConstant.CHAT)
        # self.language: str = data.get('language', '')
        # self.comment_language: str = data.get("comment_language", "Chinese")
        # self.custom_instructions: str = data.get('custom_instructions', '')
        # self.query: str = data.get('query', '')
        # self.code: str = data.get('code', '')
        # self.prompt: str = data.get('prompt', '')
        # self.conversation_id: str = data.get('conversation_id', '')
        # # 请求信息
        # self.path: str = data.get("path", "")
        # self.user_agent: str = data.get("user_agent", "")
        # self.host: str = data.get("host", "")
        # self.display_name: str = data.get("display_name", "")
        # self.api_info = data.get("api_info", {})

@dataclass
class ChatRequestData:
    # 动作：chat,addDebugCode,addCommentCode,explain etc.
    action: str = ActionsConstant.CHAT
    # programming language: c, cpp, python, java etc.
    language: str = ""
    # 注释语言
    comment_language: str = "Chinese"
    # 自定义指令集
    custom_instructions: str = None
    # 用户输入的查询信息
    query: str = None
    # 当前代码文件的路径
    path: str = ""
    # 根据用户请求构造的提示信息
    prompt: str = None
    # 对话上下文
    context: str = None
    # 对话模式: 单人对话或智能团对话
    mode: str = "normal"
    # 选中代码提问，未选中则为空
    code: str = ""
    # 本轮会话的唯一标识
    conversation_id: str = None
    # 本轮会话里的本次会话的唯一标识
    chat_id: str = None
    # 用户使用的客户端
    user_agent: str = ""
    # 用户所在的主机
    host: str = ""
    # 用户名
    display_name: str = ""

    def __post_init__(self):
        """
        __post_init__ 方法会在 dataclass 的 __init__ 方法执行完毕后被调用
        """
        if not self.query:
            self.query = self.prompt
            if self.code:
                self.prompt = f"{self.query} \nSelected code:\n```\n{self.code}\n```"
        if not self.action:
            self.action = ActionsConstant.CHAT
        if not self.comment_language:
            self.comment_language = 'Chinese'

    def to_dict(self):
        """
        把请求数据转成字典
        """
        return self.__dict__


@dataclass
class ChatAgentData:
    user_display_name: str = None
    request_data: ChatRequestData = None

# class RequestData:
#     def __init__(self, data: Dict[str, any] = None):
#         if not data:
#             data = {}
#         # self.raw_data = data
#         # 查询信息
#         self.action: str = data.get("action", ActionsConstant.CHAT)
#         self.language: str = data.get('language', '')
#         self.comment_language: str = data.get("comment_language", "Chinese")
#         self.custom_instructions: str = data.get('custom_instructions', '')
#         self.query: str = data.get('query', '')
#         self.code: str = data.get('code', '')
#         self.prompt: str = data.get('prompt', '')
#         self.conversation_id: str = data.get('conversation_id', '')
#         # 请求信息
#         self.path: str = data.get("path", "")
#         self.user_agent: str = data.get("user_agent", "")
#         self.host: str = data.get("host", "")
#         self.display_name: str = data.get("display_name", "")
#         self.api_info = data.get("api_info", {})

#     def to_dict(self):
#         return self.__dict__

def make_cls_with_dict(cls, dict_data):
    """
    根据字典内容构建一个数据对象，采用数据对象是为了保障数据的一致性，提升可读性
    """
    valid_datas = {}
    for key, value in dict_data.items():
        if hasattr(cls, key):
            valid_datas[key] = value
    result = cls(**valid_datas)
    if hasattr(cls, "raw_data"):
        result.raw_data = dict_data
    return result
