from functools import reduce

from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import TYPE, PAYLOAD, TEXT


def convert_messages_to_openai_format(messages: list[Message], system_message: str = None) -> list[dict]:
    """
    Converts a list of omnia-sdk messages to OpenAI Chat Completion format.

    :param messages: List of omnia-sdk messages.
    :param system_message: Optional system message to include at the start of the conversation.
    :return: List of messages in OpenAI Chat Completion format.
    """
    openai_messages = []
    if system_message:
        openai_messages.append([{'role': 'system', 'content': system_message}])
    for msg in messages:
        additional_content = {k: v for k, v in msg.content.items() if k not in [TYPE, PAYLOAD, TEXT]}
        openai_messages.append({'role': msg.role, 'content': msg.get_text(), **additional_content})
    return openai_messages


def get_history_text(messages: list[Message]) -> str:
    """
    Returns conversation history as string.

    :param messages: list of user and ai assistant messages
    :return: conversation history as string
    """
    return reduce(lambda m1, m2: f"{m1}\n{m2.role}: {m2.get_text()}", messages, "") if messages else ""


_translation_table = dict.fromkeys(map(ord, '\\!@#*$.{}\n/:|;,-?"'), " ")


def clean_text(text: str):
    """
    Returns lowercase text without blacklisted special characters.

    :param text: text to clean
    :returns: text without blacklisted special characters
    """
    return text.translate(_translation_table).strip()
