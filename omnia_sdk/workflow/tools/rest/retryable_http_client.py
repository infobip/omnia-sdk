import logging as log
import time

from requests import Response

from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE
from omnia_sdk.workflow.tools.rest.exceptions import ApplicationError, UserRequestError

READ_TIMEOUT_SECONDS = 35
_max_attempts = 3
_backoff_seconds = 2

"""
This module provides basic retryable HTTP client for making requests to external services.
Intra-cluster requests are subject to automatic retries, but this SDK mostly communicates with public APIs outside the cluster.

"""


def retryable_request(config, x, decode_json: bool = True, **kwargs) -> dict | bytes:
    """
    Retries request x if failure occurs up to MAX_ATTEMPTS times.

    :param config: channel and session details
    :param x: HTTP method to execute
    :param decode_json: whether to decode response content to JSON or return raw content
    :param kwargs: params for HTTP request
    :return: response of HTTP operation
    """
    config = config.get(CONFIGURABLE, config)
    kwargs = {"timeout": READ_TIMEOUT_SECONDS} | kwargs
    attempts = []
    for _ in range(_max_attempts):
        try:
            response: Response = x(**kwargs)
        # this will most of the time correspond to timeout error
        except Exception as most_likely_timeout:
            log.error(str(most_likely_timeout))
            time.sleep(_backoff_seconds)
            attempts.append({"error": str(most_likely_timeout)})
            continue

        if response.status_code < 400:
            return response.json() if decode_json else response.content

        # API call error, no recovery/retries from this
        if response.status_code < 500:
            _log_error(config, kwargs, response)
            raise UserRequestError(code=response.status_code, message=response.text)

        # Transient API error (500+) might be fixed with retry
        time.sleep(_backoff_seconds)
        _log_error(config, kwargs, response, error_type="application")
        attempts.append({"error": f"{response.text}", "status_code": {response.status_code}})

    # all retries failed, endpoint is AFK
    raise ApplicationError(code=500, message=f"Request failed after {_max_attempts} attempts.", trace=attempts)


def _log_error(config, kwargs, response, error_type: str = "user"):
    log.error(
        f"url: {kwargs.get('url')}\nrequest info: {_logging_details(config)}\n request failed due to {error_type} error with status code: "
        f"{response.status_code}.\n response: {response.text}"
    )


def _logging_details(config: dict) -> str:
    return f"Account info: chid: {config.get('chid')} session-id: {config.get('thread_id')} channel: {config.get('channel')}"
