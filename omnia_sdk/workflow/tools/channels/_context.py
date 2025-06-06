from contextvars import ContextVar

"""
This variable is used to track state of message requests to chatbot.
These methods are used by runtime environment, user should never call these directly.
"""

_api_request = ContextVar("outbound_context", default=[])
_session_id = ContextVar("chatbot_session", default="")


# single request may trigger multiple outbound messages, hence we add them into list
def add_response(response: dict):
    _api_request.get().append(response)


# returns responses in order they are generated
def get_responses() -> list[dict]:
    return _api_request.get()


def set_session_id(session_id: str):
    _session_id.set(session_id)


def get_session_id() -> str:
    return _session_id.get()


def reset_responses():
    _api_request.set([])
