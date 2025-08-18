import logging as log
from collections import namedtuple

import requests

from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE, TEXT, TYPE, WORKFLOW_ID, THREAD_ID, ASSISTANT
from omnia_sdk.workflow.tools.channels import config as channels_config
from omnia_sdk.workflow.tools.channels._context import add_response
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

BUSINESS_NUMBER = "business_number"
END_USER_NUMBER = "end_user_number"
CHANNEL = "channel"
HTTP = "HTTP"
CONSOLE = "CONSOLE"
POSTBACK_DATA = "postbackData"
CALLBACK_URL = "callback_url"
BODY = "body"

messages_url = f"{channels_config.INFOBIP_BASE_URL}/messages-api/1/messages"
"""
This module provides integration with Infobip's Omni Channel API.
User may send content to various channels with a single API which abstracts channel details.
Messages API https://www.infobip.com/docs/api/platform/messages-api
"""

ButtonDefinition = namedtuple("ButtonDefinition", ["type", "text", "postback_data"])
ListSectionDefinition = namedtuple("ListDefinition", ["sectionTitle", "items"])


def get_outbound_text_format(text: str) -> dict:
    """
    Prepares text message to be compliant with Messages API format.

    :param text: to send
    :return: message content in Messages API format
    """
    return {BODY: {TYPE: TEXT.upper(), TEXT: text}}


def get_outbound_buttons_format(text: str, buttons: list[ButtonDefinition]) -> dict:
    """
    Prepares text message with buttons to be compliant with Messages API format.

    :param text: to send
    :param buttons: buttons to show
    :return: message content in Messages API format
    """
    return {
        BODY: {TYPE: TEXT.upper(), TEXT: text},
        "buttons": [{TYPE: button.type, TEXT: button.text, POSTBACK_DATA: button.postback_data} for button in buttons],
    }


def get_outbound_list_format(text: str, subtext: str, sections: list[ListSectionDefinition]) -> dict:
    """
    Prepares text message with list sections to be compliant with Messages API format.

    :param text: to send with list picker
    :param subtext: to show in list picker
    :param sections: list of sections to show
    :return: message content in Messages API format
    """
    return {
        BODY: {
            TYPE: "LIST", TEXT: text, "subtext": subtext, "sections": [{
                "sectionTitle": section.sectionTitle,
                "items": section.items,
            } for section in sections]
        }
    }


def get_outbound_image_format(image_url: str) -> dict:
    """
    Prepares image message to be compliant with Messages API format.

    :param image_url: URL of the image to send
    :return: message content in Messages API format
    """
    return {BODY: {TYPE: "IMAGE", "url": image_url}}


def send_message(message: Message, config: dict) -> None:
    """
    Sends text message to the channel defined in config.
    :param message: to send
    :param config: with session and channel details
    """
    _send_to_channel(content=message.content, config=config)


def send_template():
    pass


# sends message to whichever channel we received request from
def _send_to_channel(content: dict, config: dict):
    configurable = config[CONFIGURABLE]
    channel = configurable[CHANNEL]
    if channel == CONSOLE:
        log.info(f"Sending content to console:\n{content}")
        return
    # we add outbound content to the request state
    add_response(response=content)
    if channel == HTTP:
        callback_url = configurable.get(CALLBACK_URL)
        if not callback_url:
            return
        # asynchronous HTTP communication if user specified callback url
        headers = {
            "session-id": configurable[THREAD_ID],
            "message-id": configurable["message_id"],
            "user-id": configurable["user_id"],
            "workflow-id": configurable[WORKFLOW_ID],
        }
        _ = retryable_request(config=config, x=requests.post, url=callback_url, json=content, headers=headers, timeout=5)
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
