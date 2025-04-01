import re
from collections import namedtuple

import requests

from omnia_sdk.workflow.tools.channels.config import INFOBIP_API_KEY, INFOBIP_BASE_URL
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

"""
This module provides integration with Infobip's Whatsapp API.
User may alternatively use omni_channels.py module to send messages to Whatsapp.

"""

url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/template"

WhatsAppTemplateMessage = namedtuple("WhatsAppTemplateMessage", ["phone_number", "template_name", "placeholders"])


def send_wa_template(config: dict, template_message: WhatsAppTemplateMessage, sender: str):
    """
    Send a single WhatsApp template message.

    :param sender: a business number sending the template message
    :param config: with session details
    :param template_message: phone_number, template_name and placeholders
    :return: None or raises exception if WA gateways are down
    """
    send_bulk_wa_template(config=config, template_messages=[template_message], sender=sender)


def send_bulk_wa_template(config: dict, template_messages: list[WhatsAppTemplateMessage], sender: str):
    """
    Send a bulk WhatsApp template message to multiple receivers

    :param sender: a business number sending the template message
    :param config: with session details
    :param template_messages: list of: (phone_number, template_name and placeholders)
    :return: None or raises exception if WA gateways are down
    """
    headers = {"Authorization": f"App {INFOBIP_API_KEY}"}
    messages = [_create_payload(template_message=message, config=config, sender=sender) for message in template_messages]
    # if this fails, we (or WhatsApp) have serious outage
    retryable_request(x=requests.post, config=config, url=url, json={"messages": messages}, headers=headers)


def _create_payload(template_message: WhatsAppTemplateMessage, config: dict, sender: str) -> dict:
    # prepares WhatsApp API payload
    return {
        "from": sender,
        "to": template_message.phone_number,
        "content": {
            "templateName": template_message.template_name,
            "templateData": {"body": {"placeholders": _escape_placeholders(template_message.placeholders)}},
            "language": config.get("language"),
            },
        }


def _escape_placeholders(placeholders: list[str]) -> list[str]:
    # Whatsapp api does not allow newline, tab and 4 or more whitespaces. Newline is allowed if escaped.
    cleaned_placeholders = []
    for p in placeholders:
        p = p.replace("\n", "\\n").replace("\t", " ")
        p = re.sub(r"\s{4,}", " ", p)
        cleaned_placeholders.append(p)
    return cleaned_placeholders
