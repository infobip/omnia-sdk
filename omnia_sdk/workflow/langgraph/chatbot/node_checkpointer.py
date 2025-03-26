import inspect
from typing import Callable

"""
This decorator ensures that LangGraph will checkpoint state with specified memory saver without requiring user to explicitly
add return state to every node function.
Adding return with deltas is both tedious and error prone.
We mutate state in-place and perform identity reduction after each node execution automatically.
"""


class NodeCheckpointer:
    def __init__(self, action: Callable):
        # node function to execute
        self.action = action

    def __call__(self, state=None, config=None):
        object_spect = inspect.signature(self.action)
        # langgraph passes config/state as arguments to node functions only if those functions explicitly declare them
        arguments = {k: v for k, v in locals().items() if k in object_spect.parameters}
        self.action(**arguments)
        return state
