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
