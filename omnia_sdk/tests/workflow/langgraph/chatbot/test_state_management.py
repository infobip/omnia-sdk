from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.constants import END

from omnia_sdk.workflow.chatbot.chatbot_configuration import ChatbotConfiguration
from omnia_sdk.workflow.chatbot.chatbot_state import Message
from omnia_sdk.workflow.chatbot.constants import ASSISTANT, CONFIGURABLE, TEXT, TYPE, USER
from omnia_sdk.workflow.langgraph.chatbot.chatbot_graph import THREAD_ID, ChatbotFlow, State

thread_id = "123"
m1 = Message(role=USER, content={TYPE: TEXT.upper(), TEXT: "Hello from John Doe"})
a1 = Message(role=ASSISTANT, content={TYPE: TEXT.upper(), TEXT: "Hello back at you"})
foo, bar = ("foo", "bar")
start, date = ("start", "date")

"""
This module tests that chatbot state management works correctly with node_checkpointer.py decorator to propagate state updates.
Test will run user message twice, each message triggering its own cycle.
The state should be saved correctly over 2 cycles and variables should be propagated correctly.

And yes this test has multiple asserts :)
"""


class TinyChatbot(ChatbotFlow):
    def __init__(self, checkpointer: BaseCheckpointSaver = None, configuration: ChatbotConfiguration = None, translation_table=None):
        super().__init__(checkpointer=checkpointer, configuration=configuration, translation_table=translation_table)

    def start(self, state: State, config: dict):
        assert m1 == self.get_user_message(state=state)
        assert config[CONFIGURABLE][THREAD_ID] == thread_id
        self.save_message(state=state, message=a1)
        self.save_variable(name=foo, value=bar, state=state)

    def date(self, state: State):
        # transition to date node decorated with node_checkpointer.py should work even if it does not declare config parameter
        assert bar == self.get_variable(name=foo, state=state)
        assert m1 == self.get_user_message(state=state)
        assert a1 == self.get_last_message(state=state)

    def _nodes(self):
        self.add_node(start, self.start)
        self.add_node(date, self.date)
        self.create_entry_point(start_node=start)

    def _transitions(self):
        self.add_edge(start, date)
        self.add_edge(date, END)


# ensure that note_checkpointer.py decorator propagates state updates correctly without explicit returns in every node function
def test_state_variables_should_be_propagated_with_decorated_nodes():
    chatbot = TinyChatbot(configuration=ChatbotConfiguration(default_language="en"))
    cfg = {CONFIGURABLE: {THREAD_ID: thread_id}}
    # run same message twice to ensure that state is saved correctly over 2 cycles
    cycles = [(chatbot.run, {"message": m1, "config": cfg})] * 2
    for cycle in cycles:
        cycle[0](**cycle[1])
    state = chatbot.get_state(config=cfg)
    # TypedDict does not allow constants to access keys (without warnings), yet LangGraph allows reductions only on TypedDicts
    # so we need to use string keys here
    conversation_cycles = state["chatbot_state"]["conversation_cycles"]

    # ensure that we have 2 conversation cycles
    assert len(conversation_cycles) == len(cycles)
    assert conversation_cycles[0].messages == [m1, a1]
    # as we ran same message twice, cycles should be identical
    assert conversation_cycles[0].messages == conversation_cycles[1].messages
    # variables do not depend on the cycle and reduced with merge operation
    assert chatbot.get_variables(state) == {foo: bar}
