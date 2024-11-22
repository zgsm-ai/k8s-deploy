from autogen import GroupChatManager

from .context_helper import ContextHelper


class ObserverGroupManager(GroupChatManager):
    def __init__(self, conv_id, *args, **kwargs):
        super(ObserverGroupManager, self).__init__(*args, **kwargs)
        self.user_context = {}
        self.user_display_name = ""
        self.conv_id = conv_id

    def update_user_display_name(self, display_name: str):
        self.user_display_name = display_name

    def update_user_context(self, new_context: dict):
        if not new_context:
            return
        self.user_context.update(new_context)

    def update_env_context(self):
        new_context = ContextHelper.get_env_context(self.conv_id)
        if new_context:
            self.update_user_context(new_context)

    def do_finish(self):
        pass
        # 因为每次会话结束时清空上下文，会导致追问场景无法使用
        # 每个key 1h的过期时间，等自己过期即可
        # ContextHelper.clear_env_context(self.conv_id)
