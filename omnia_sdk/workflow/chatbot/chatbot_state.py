import dataclasses
from typing import Literal

from typing_extensions import TypedDict

"""
This module contains dataclasses for chatbot state management.
"""


@dataclasses.dataclass
class Message:
    """
    Represent inbound or outbound message. Content corresponds to channel message format.
    ChatbotGraphFlow has utilities to extract and interpret message object.
    """
    role: Literal["user", "assistant"]
    content: dict


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
