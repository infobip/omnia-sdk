from contextvars import ContextVar

"""
This variable is used to track state when flow is used within another chatbot (e.g. Answers).
These methods are used by runtime environment, user should never call these directly.
"""

_workflow_state = ContextVar("workflow_state", default={})


def set_workflow_state(state: dict) -> None:
    # Since Langgraph is creating a new context for each invoke of the graph,
    # we need to update the existing state instead of replacing it.
    _workflow_state.get().update(state)


def get_workflow_state() -> dict:
    return _workflow_state.get()


def reset_workflow_state() -> None:
    _workflow_state.set({})
