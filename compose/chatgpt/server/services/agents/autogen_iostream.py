import json

from autogen.io.base import IOStream

from common.constant import DifyAgentConstant


class AgentChatIOStream(IOStream):
    blockAgents = ["user"]

    def __init__(self, send_msg_func, send_json_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._agent_sending = False
        self._send_msg_func = send_msg_func
        self._send_json_func = send_json_func

    def finish(self):
        self._agent_end()
        self._send_msg(DifyAgentConstant.AGENT_CHAT_DONE_MSG)

    def _send_json(self, json_data):
        agent_name = json_data.get("agent_name")
        if agent_name and agent_name.lower() in self.blockAgents:
            return
        self._send_json_func(json_data)

    def _send_msg(self, msg):
        self._send_msg_func(msg)

    def _agent_start(self, agent_name=None, agent_icon=None, message="", increment=False):
        self._send_json({
            "event": DifyAgentConstant.AGENT_START_EVENT,
            "agent_name": agent_name,
            "agent_icon": agent_icon,
            "message": message,
            "increment": increment
        })
        self._agent_sending = True

    def _dify_agent_thought(self, dify_chunk, agent_name, agent_icon=None):
        if not self._agent_sending:
            self._agent_start(agent_name, agent_icon=agent_icon)
        self._send_json({
            "event": DifyAgentConstant.AGENT_THOUGHT_EVENT,
            "agent_name": agent_name,
            "agent_icon": agent_icon,
            "dify_chunk": dify_chunk
        })

    def _agent_end(self, agent_name=None):
        if self._agent_sending:
            self._agent_sending = False
            self._send_json({
                "event": DifyAgentConstant.AGENT_THOUGHT_EVENT,
                "agent_name": agent_name,
            })

    def print_dify_chunk(self, chunk_data, sender, sender_icon=None):
        self.print(
            f"DIFY_DATA:{json.dumps(chunk_data)}",
            sender=sender,
            sender_icon=sender_icon,
            end="",
            flush=True
        )
    
    def print_agent_advise(self, advise_data):
        """
        输出LLM给出的下一步建议
        """
        self._send_json({
            "event": DifyAgentConstant.AGENT_ADVISE_EVENT,
            "advises": advise_data
        })

    def print_dify_end(self, sender):
        self.print("DIFY_END", sender=sender, end="", flush=True)

    def say_one(self, message, sender, sender_icon=None):
        self.print_dify_chunk({
            "event": "message",
            "answer": message
        }, sender=sender, sender_icon=sender_icon)
        self.print_dify_end(sender)

    def print(self, *args, **kwargs) -> None:
        # print(args, kwargs)
        # 分隔线
        if 'sep' in kwargs:
            return

        is_temp = True if 'end' in kwargs else False
        message = args[0]

        if is_temp:
            if message.startswith("DIFY_DATA:"):
                self._dify_agent_thought(
                    json.loads(message[10:].strip()),
                    agent_name=kwargs.get("sender"),
                    agent_icon=kwargs.get("sender_icon")
                )
                return
            if message == "DIFY_END":
                self._agent_end(kwargs.get("sender"))
