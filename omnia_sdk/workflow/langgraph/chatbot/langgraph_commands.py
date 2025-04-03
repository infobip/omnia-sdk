from abc import abstractmethod

from langgraph.types import Command

"""
This module defines abstract Command which maps to LangGraph Command object.
Abstraction is added to future proof the code for new Command types.
"""


class AbstractCommand:
    @abstractmethod
    def to_langgraph_command(self, state):
        """
        Converts this command to LangGraph Command like object
        """
        pass


# removes the need to pass the state delta every time to Command object
class Transition(AbstractCommand):
    def __init__(self, goto: str):
        self.goto = goto

    def to_langgraph_command(self, state):
        return Command(update=state, goto=self.goto)
