import requests

from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE
from omnia_sdk.workflow.logging.logging import omnia_logger
from omnia_sdk.workflow.tools.channels import config as channels_config
from omnia_sdk.workflow.tools.channels._context import add_response, set_session_id
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

BUSINESS_NUMBER = "business_number"
END_USER_NUMBER = "end_user_number"
CHANNEL = "channel"

HTTP = "HTTP"


messages_url = f"{channels_config.INFOBIP_BASE_URL}/messages-api/1/messages"


"""
This module provides integration with Infobip's Omni Channel API
User may send content to various channels with a single API which abstracts channel details.
"""


def send_message(message: str, config: dict) -> None:
    """
    Sends text message to the channel defined in config.
    :param message:to send
    :param config: with session and channel details
    """
    content = {"body": {"text": message, "type": "TEXT"}}
    _send_to_channel(content=content, config=config)


def send_buttons(message: str, buttons: list[str], config: dict) -> None:
    """
    Sends message and buttons to the channel defined in config.

    :param message:to send
    :param buttons: to render in chat
    :param config: with session and channel details
    """
    content = {
        "body": {"text": message, "type": "TEXT"},
        "buttons": [{"type": "REPLY", "text": button, "postbackData": button} for button in buttons],
    }
    _send_to_channel(content=content, config=config)


def send_template():
    pass


# sends message to whichever channel we received request from
def _send_to_channel(content: dict, config: dict):
    configurable = config[CONFIGURABLE]
    channel = configurable[CHANNEL]
    omnia_logger.debug(f"sending: {content}\n to channel: {channel}")
    try:
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
                set_session_id(session_id=configurable["thread_id"])
        # deliver message to OTT Gateway
        else:
            _send_messages(config=config, content=content, channel=channel)
    # if this results with an error, Infobip and/or META teams are already working on the issue
    except Exception as e:
        omnia_logger.error(e)


# sends a message to the channel in which user started communication
def _send_messages(config: dict, content: dict, channel: str) -> None:
    configurable = config[CONFIGURABLE]
    sender = configurable[BUSINESS_NUMBER]
    destination = configurable[END_USER_NUMBER]
    message = {"channel": channel, "sender": sender, "destinations": [{"to": destination}], "content": content}
    body = {"messages": [message]}
    headers = {"Authorization": f"App {channels_config.INFOBIP_API_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    _ = retryable_request(config=config, x=requests.post, url=messages_url, json=body, headers=headers)
