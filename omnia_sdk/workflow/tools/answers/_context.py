from contextvars import ContextVar

"""
This variable is used to track state when flow is used within another chatbot (e.g. Answers).
These methods are used by runtime environment, user should never call these directly.
"""

_flow_final_state = ContextVar("flow_final_state", default={})


def set_flow_final_state(state: dict) -> None:
    # Since Langgraph is creating a new context for each invoke of the graph,
    # we need to update the existing state instead of replacing it.
    _flow_final_state.get().update(state)


def get_flow_final_state() -> dict:
    return _flow_final_state.get()


def reset_final_state() -> None:
    _flow_final_state.set({})
