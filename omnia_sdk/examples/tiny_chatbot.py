from datetime import datetime

from langgraph.constants import END

from omnia_sdk.workflow.chatbot.chatbot_configuration import ChatbotConfiguration
from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import ASSISTANT, CONFIGURABLE, TEXT, TYPE, USER, THREAD_ID
from omnia_sdk.workflow.langgraph.chatbot.chatbot_graph import ChatbotFlow, State
"""
This is a "hello world" chatbot which demonstrates how user can build LangGraph chatbot workflows with the SDK.
See this github repo for more complete examples:
 - https://github.com/infobip/omnia-sdk-examples
"""


class TinyChatbot(ChatbotFlow):

    def start(self, state: State, config: dict):
        print(state)
        print(config[CONFIGURABLE][THREAD_ID])
        self.save_message(state=state, message=Message(role=ASSISTANT, content={TYPE: TEXT.upper(), TEXT: "Hello back at you"}))
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
    message = Message(role=USER, content={TYPE: TEXT.upper(), TEXT: "Hello from John Doe"})
    chatbot = TinyChatbot(configuration=ChatbotConfiguration(default_language="en"))
    chatbot.run(message=message, config=cfg)
    message = Message(role=USER, content={TYPE: TEXT.upper(), TEXT: "Bye!"})
    chatbot.run(message=message, config=cfg)
