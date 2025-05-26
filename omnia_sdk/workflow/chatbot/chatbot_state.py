import dataclasses

from typing_extensions import TypedDict

from omnia_sdk.workflow.chatbot.constants import TYPE, TEXT, PAYLOAD, BUTTON_REPLY

"""
This module contains dataclasses for chatbot state management.
"""


@dataclasses.dataclass
class Message:
    """
    Represents inbound or outbound message.
    Role should be one of: user, assistant, tool.
    Content corresponds to channel message format e.g. {"type": "TEXT", "text": "Hi"} TODO: add link to docs
    """
    role: str
    content: dict

    def get_text(self):
        content = self.content
        if "body" in content:
            content = content["body"]
        if content[TYPE] == TEXT.upper():
            return content[TEXT]
        if content[TYPE] == BUTTON_REPLY:
            return content[PAYLOAD]
        return None

    @staticmethod
    def get_message(role: str, text: str) -> 'Message':
        return Message(role=role, content={TYPE: TEXT.upper(), TEXT: text})


# every time users completes a flow and comes back to <start> node, we create a new conversation cycle
@dataclasses.dataclass
class ConversationCycle:
    messages: list[Message]
    intent: str = None


# this is the main data model for chatbot state
class ChatbotState(TypedDict):
    conversation_cycles: list[ConversationCycle]
    user_language: str
    variables: dict
