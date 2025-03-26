from datetime import datetime

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.constants import END

from omnia_sdk.workflow.chatbot.chatbot_configuration import ChatbotConfiguration
from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE, PAYLOAD
from omnia_sdk.workflow.langgraph.chatbot.chatbot_graph import THREAD_ID, ChatbotFlow, State

"""
This is a "hello world" chatbot which demonstrates how user can build LangGraph chatbot workflows with the SDK.
See this github repo for more complete examples:
 - https://github.com/infobip/omnia-sdk-examples
"""


class TinyChatbot(ChatbotFlow):
    # constructor with these parameters is mandatory, check the super class ChatbotFlow for details
    def __init__(self, checkpointer: BaseCheckpointSaver = None, configuration: ChatbotConfiguration = None, translation_table=None):
        super().__init__(checkpointer=checkpointer, configuration=configuration, translation_table=translation_table)

    def start(self, state: State, config: dict):
        print(state)
        print(config[CONFIGURABLE][THREAD_ID])
        self.save_message(state=state, message=Message(role="AI", content={"type": "text", PAYLOAD: "Hello back at you"}))
        self.save_variable(name="name", value="foo", state=state)

    def date(self, state: State):
        print(state)
        print(f"Today is: {datetime.now()}")

    def _nodes(self):
        self.add_node("start", self.start)
        self.add_node("date", self.date)
        self.create_entry_point(start_node="start")

    def _transitions(self):
        self.add_edge("start", "date")
        self.add_edge("date", END)


if __name__ == "__main__":
    cfg = {CONFIGURABLE: {THREAD_ID: "123"}}
    message = Message(role="user", content={"type": "text", PAYLOAD: "Hello from John Doe"})
    chatbot = TinyChatbot(configuration=ChatbotConfiguration(default_language="en"))
    chatbot.run(message=message, config=cfg)
    message = Message(role="user", content={"type": "text", PAYLOAD: "Bye!"})
    chatbot.run(message=message, config=cfg)
