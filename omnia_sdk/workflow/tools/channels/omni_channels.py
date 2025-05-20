import logging as log
from collections import namedtuple

import requests

from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE, TEXT, TYPE
from omnia_sdk.workflow.tools.channels import config as channels_config
from omnia_sdk.workflow.tools.channels._context import add_response, set_session_id
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

BUSINESS_NUMBER = "business_number"
END_USER_NUMBER = "end_user_number"
CHANNEL = "channel"
HTTP = "HTTP"
BUTTON_REPLY = "BUTTON_REPLY"
CONSOLE = "CONSOLE"
POSTBACK_DATA = "postbackData"

messages_url = f"{channels_config.INFOBIP_BASE_URL}/messages-api/1/messages"

"""
This module provides integration with Infobip's Omni Channel API
User may send content to various channels with a single API which abstracts channel details.
"""

InboundContent = namedtuple("InboundContent", ["type", "payload"])
ButtonDefinition = namedtuple("ButtonDefinition", ["type", "text", "postback_data"])


def get_outbound_text_format(text: str) -> dict:
    """
    Prepares text message to be compliant with Messages API format.
    Messages API https://www.infobip.com/docs/api/platform/messages-api

    :param text: to send
    :return: message content in Messages API format
    """
    return {"body": {TYPE: TEXT.upper(), TEXT: text}}


def get_outbound_buttons_format(text: str, buttons: list[ButtonDefinition]) -> dict:
    """
    Prepares text message with buttons to be compliant with Messages API format.

    :param text: to send
    :param buttons: buttons to show
    :return: message content in Messages API format
    """
    return {
        "body": {TYPE: TEXT.upper(), TEXT: text},
        "buttons": [{TYPE: button.type, TEXT: button.text, POSTBACK_DATA: button.postback_data} for button in buttons],
        }


def send_message(message: Message, config: dict) -> None:
    """
    Sends text message to the channel defined in config.
    :param message: to send
    :param config: with session and channel details
    """
    _send_to_channel(content=message.content, config=config)


def send_text(text: str, config: dict) -> None:
    """
    Sends text message to the channel defined in config. This method directly sends text message
    to the channel without persisting message in state of flow. If you also want to persist message in state of flow
    use send_text_response from ChatbotGraphFlow.

    :param text: to send
    :param config: with session and channel details
    """
    content = get_outbound_text_format(text=text)
    _send_to_channel(content=content, config=config)


def send_buttons(text: str, buttons: list[ButtonDefinition], config: dict) -> None:
    """
    Sends message and buttons to the channel defined in config. This method directly sends button message
    to the channel without persisting message in state of flow. If you also want to persist message in state of flow
    use send_buttons_response from ChatbotGraphFlow.

    :param text: to send with buttons
    :param buttons: to render in chat
    :param config: with session and channel details
    """
    content = get_outbound_buttons_format(text=text, buttons=buttons)
    _send_to_channel(content=content, config=config)


def send_template():
    pass


# sends message to whichever channel we received request from
def _send_to_channel(content: dict, config: dict):
    configurable = config[CONFIGURABLE]
    channel = configurable[CHANNEL]
    if channel == CONSOLE:
        log.info(f"Sending content to console:\n{content}")
        return
    if channel == HTTP:
        callback_url = configurable.get("callback_url")
        # asynchronous HTTP communication if user specified callback url
        if callback_url:
            headers = {
                "session-id": configurable["thread_id"],
                "message-id": configurable["message_id"],
                "user-id": configurable["user_id"],
                "flow-id": configurable["flow_id"],
                }
            _ = retryable_request(config=config, x=requests.post, url=callback_url, json=content, headers=headers, timeout=5)
        # collect response for synchronous HTTP communication
        else:
            add_response(response=content)
    # deliver message to OTT Gateway
    else:
        _send_messages(config=config, content=content, channel=channel)
    # if this results with an error, Infobip and/or META teams are already working on the issue


# sends a message to the channel in which user started communication
def _send_messages(config: dict, content: dict, channel: str) -> None:
    configurable = config[CONFIGURABLE]
    sender = configurable[BUSINESS_NUMBER]
    destination = configurable[END_USER_NUMBER]
    message = {"channel": channel, "sender": sender, "destinations": [{"to": destination}], "content": content}
    body = {"messages": [message]}
    headers = {"Authorization": f"App {channels_config.INFOBIP_API_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    _ = retryable_request(config=config, x=requests.post, url=messages_url, json=body, headers=headers)
