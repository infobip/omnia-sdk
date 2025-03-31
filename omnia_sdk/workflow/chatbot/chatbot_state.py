import dataclasses

from typing_extensions import TypedDict

from omnia_sdk.workflow.chatbot.constants import PAYLOAD

"""
This module contains dataclasses for chatbot state management.
"""


# this can be end user request or AI assistant message
@dataclasses.dataclass
class Message:
    role: str  # human, AI, tool
    content: dict

    def get_payload(self):
        return self.content[PAYLOAD]


# every time users completes a flow and comes back to <start> node, we create a new conversation cycle
@dataclasses.dataclass
class ConversationCycle:
    messages: list
    intent: str = None


# this is the main data model for chatbot state
class ChatbotState(TypedDict):
    conversation_cycles: list[ConversationCycle]
    user_language: str
    variables: dict
