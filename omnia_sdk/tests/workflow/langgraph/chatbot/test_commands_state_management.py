from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.constants import END
from langgraph.types import Command

from omnia_sdk.workflow.chatbot.chatbot_configuration import ChatbotConfiguration
from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE, TEXT, TYPE, USER
from omnia_sdk.workflow.langgraph.chatbot.chatbot_graph import THREAD_ID, ChatbotFlow, State
from omnia_sdk.workflow.langgraph.chatbot.langgraph_commands import Transition

thread_id = "123"
m1 = Message(role=USER, content={TYPE: TEXT.upper(), TEXT: "Hello from John Doe"})
m2 = Message(role=USER, content={TYPE: TEXT.upper(), TEXT: "Bye!"})

foo, bar = ("foo", "bar")
start, second = ("start", "second")

"""
This module tests that chatbot state management works correctly with node_checkpointer.py decorator to propagate state updates.
Additionally we test that the Command object transitions work as expected:
- https://langchain-ai.github.io/langgraph/concepts/low_level/#command

There are no explicit transition definitions in this example, the Command object is used to transition between nodes.
Our abstraction Transition is a wrapper around Command which manages the state, although user can use Command directly.
"""


class TinyCommandsChatbot(ChatbotFlow):
    def __init__(self, checkpointer: BaseCheckpointSaver = None, configuration: ChatbotConfiguration = None,
                 translation_table=None):
        super().__init__(checkpointer=checkpointer, configuration=configuration, translation_table=translation_table)

    def start(self, state: State):
        assert m1 == self.get_user_message(state=state)
        self.save_variable(name=foo, value=bar, state=state)
        return Transition(goto="second")

    # ensure that state is updated correctly when graph resumes from user's input
    def second(self, state: State, config: dict):
        self.wait_user_input(state=state, config=config)
        assert bar == self.get_variable(name=foo, state=state)
        assert m2 == self.get_user_message(state=state)
        # you can use Transition instead of Command as shown in start node
        return Command(update=state, goto="third")

    def third(self, state: State, config: dict):
        # we should arrive to this node with correct state when Command is used to transition
        assert bar == self.get_variable(name=foo, state=state)
        assert m2 == self.get_user_message(state=state)
        return Transition(goto=END)

    def _nodes(self):
        self.add_node(start, self.start)
        self.add_node(second, self.second)
        self.add_node("third", self.third)
        self.create_entry_point(start_node=start)


# ensure that note_checkpointer.py decorator propagates state updates correctly without explicit returns in every node function
def test_state_variables_should_be_propagated_with_command_nodes():
    chatbot = TinyCommandsChatbot(configuration=ChatbotConfiguration(default_language="en"))
    cfg = {CONFIGURABLE: {THREAD_ID: thread_id}}
    chatbot.run(message=m1, config=cfg)
    chatbot.run(message=m2, config=cfg)
    state = chatbot.get_state(config=cfg)
    conversation_cycles = state["chatbot_state"]["conversation_cycles"]

    assert len(conversation_cycles) == 1
    assert conversation_cycles[0].messages == [m1, m2]
    assert chatbot.get_variables(state) == {foo: bar}
