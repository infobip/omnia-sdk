import requests

from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE, THREAD_ID
from omnia_sdk.workflow.tools.ai.constants import SESSION_ID_HEADER
from omnia_sdk.workflow.tools.channels.config import INFOBIP_API_KEY, INFOBIP_BASE_URL
from omnia_sdk.workflow.tools.rest.exceptions import ApplicationError
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

default_headers = {"Authorization": f"App {INFOBIP_API_KEY}"}

"""
This module provides integration with Infobip's RAG system.
RAG pipeline should be built via portal or API (TODO details) before using this module.
"""


def assistant_response(message: str, assistant_id: str, config: dict, prompt_var: str = None, context: str = None,
                       error_message: str = None, language: str = None) -> str:
    """
    Calls pre-built RAG assistant endpoint for the user's message.
    In an event of unlikely error, the error_message will be returned.
    If no error message is specified, ApplicationError will be raised.

    :param message: of the user
    :param assistant_id: specifying exact RAG assistant
    :param config: with session and channel parameters
    :param prompt_var: which can be used to dynamically modify RAG prompt
    :param context: external context which can override RAG chunks
    :param error_message: optional message which can returned to user in case of an unexpected error. Otherwise, error is raised.
    :param language: language of the user message
    :return: RAG response if successful. In case of an error, error_message if defined will be returned with fallback to
    raising  ApplicationError.
    """
    session_id = config[CONFIGURABLE][THREAD_ID]
    headers = {"return-contexts": "true", SESSION_ID_HEADER: session_id, "assistant-id": assistant_id} | default_headers
    message = f"{message}\n{_get_local_language_instruction(lang_iso=language)}"
    body = {"message": message, "prompt_var": prompt_var, "context": context}
    try:
        response = retryable_request(
            x=requests.post, config=config, url=f"{INFOBIP_BASE_URL}/gpt-creator/omnia/2/query", json=body, headers=headers
            )
        return response["message"]
    except ApplicationError as application_error:
        if error_message:
            return error_message
        raise application_error


"""
This method returns localised instruction for RAG assistant for the expected language.
We noticed when there are multiple languages in the prompt:
 - language of the retrieved chunks
 - system message and instructions
 - user's question
method bellow is most robust to ensure output is in the correct language.
"""


def _get_local_language_instruction(lang_iso: str) -> str:
    if not lang_iso:
        return ""
    match lang_iso:
        case "hr":
            return "- Odgovori korisniku na Hrvatskom jeziku."
        case _:
            return "- Reply to user in English language."
