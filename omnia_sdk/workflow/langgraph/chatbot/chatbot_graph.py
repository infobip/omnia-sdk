from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt

from omnia_sdk.workflow.chatbot.chatbot_configuration import ChatbotConfiguration
from omnia_sdk.workflow.chatbot.chatbot_state import ChatbotState, ConversationCycle, Message
from omnia_sdk.workflow.chatbot.constants import (
    ASSISTANT,
    BUTTONS,
    CONFIGURABLE,
    LANGUAGE,
    MESSAGE,
    PAYLOAD,
    TYPE,
    USER_ROLE,
)
from omnia_sdk.workflow.langgraph.chatbot.node_checkpointer import NodeCheckpointer
from omnia_sdk.workflow.tools.channels.omni_channels import ButtonMessage, send_buttons, send_message

"""
This module contains the prototype class for chatbot applications built via LangGraph.
To get started we recommend to first check TinyChatbot example in the project.
Afterwards, you could check more complete examples here:
 - https://github.com/infobip/omnia-sdk-examples
To get familiar with LangGraph features, check examples here:
 - https://github.com/langchain-ai/langgraph/tree/main/examples

To get started with Omnia-sdk user should create a new class that inherits from ChatbotFlow and implement methods:
 - nodes(...)
 - transitions(...)

MEMORY STATE
This SDK will automatically checkpoint memory state so user does not have to return deltas in every node function.
Simply modify state in-place using accessor methods in ChatbotGraph class and SDK will take care of the rest.

Please remember to set the entry point and transitions to END node as shown in examples and pydoc bellow.

IMPORTANT:
- To ensure backwards compatibility it is highly recommended that user does NOT access chatbot_state directly.
Instead, use accessor methods in ChatbotGraph class to interact with the chatbot state.
"""

CHATBOT_STATE = "chatbot_state"
VARIABLES = "variables"
CONVERSATION_CYCLES = "conversation_cycles"
THREAD_ID = "thread_id"
_user_language = "user_language"


def reduce_state(cs1: ChatbotState, cs2: ChatbotState) -> ChatbotState:
    if not cs2:
        return cs1
    return cs2


"""
It is highly recommended to use TypedDict for top level state objects in LangGraph.
In theory dataclasses and Pydantic models are supported but reductions via Annotated do not work with those.
This makes it inconvenient to observe state outside of graph and in turn resume execution with merge reduction.
"""


class State(TypedDict):
    chatbot_state: Annotated[ChatbotState, reduce_state]


"""
This class is a prototype for chatbot applications via LangGraph.
User is required to implement methods:
 - nodes(...)
 - transitions(...)

This class should enable easy access to Infobip's SaaS, CPaaS and AI services while simplifying LangGraph state management.
Built graph is **channel agnostic** and can be multilingual with the help of language detector and translation table.
"""


class ChatbotFlow(ABC):
    # This constructor will be invoked by runtime environment with user submitted files
    def __init__(
        self, checkpointer: BaseCheckpointSaver = None, configuration: ChatbotConfiguration = None, translation_table: dict = None
    ):
        self.__graph = StateGraph(State)
        self.configuration = configuration
        self.translation_table = translation_table
        self._nodes()
        self._transitions()
        checkpointer = checkpointer if checkpointer else MemorySaver()
        self.workflow = self.__graph.compile(checkpointer=checkpointer)

    @abstractmethod
    def _nodes(self):
        """
        User should implement this method to define nodes of the chatbot graph.
        We strongly encourage users to use method:
         - self.add_node("node_name", self.node_function)
        instead of directly modifying the graph.

        IMPORTANT:
        user must define entry point once nodes are created via:
            self.create_entry_point("start_node_name")

        This method will ensure that LangGraph state is always correctly checkpointed after each node execution without requiring
        users to return deltas in every node function.
        """
        pass

    @abstractmethod
    def _transitions(self):
        """
        User should implement this method to define transitions of the chatbot graph.
        We strongly encourage users to use methods:
            - self.add_edge("from_node", "to_node")
            - self.add_conditional_edge("from_node", self.transition_function)
        instead of directly modifying the graph.

        IMPORTANT:
         - It is MANDATORY to use at least one edge to LangGraph's END node like bellow:
                 self.add_edge("travel_confirmation", END)
        see: https://langchain-ai.github.io/langgraph/concepts/low_level/
        """
        pass

    def create_entry_point(self, start_node: str) -> None:
        """
        Sets start_node as entry node in the graph.
        This method is MANDATORY to be called once nodes are created.
        :param start_node: to be set as entry point
        """
        self.__graph.set_entry_point(start_node)

    def on_session_start(self, message: Message, config: dict) -> bool:
        """
        This method is executed only once on first user message in the session. This can be done to validate user and/or render
        a welcome message.

        :param message: of the user
        :param config: channel and session details
        :return: None
        """
        # line here is to avoid warning for unused variables
        _ = (message, config)
        return True

    # Not yet supported
    def on_session_end(self, state: State, session_id: str):
        pass

    def run(self, message: Message, config: dict) -> None:
        """
        This method is invoked by runtime environment to start the chatbot graph execution.
        The method can be also used locally to test and debug the chatbot.

        Run method will start the graph from the entry point and continue execution until the END node is reached, or user's
        input is needed to proceed.
        Upon receiving user's input method will continue paused graph execution.

        :param message: of the user
        :param config: channel and session parameters
        """
        # end node does not have any nodes to which it loops back
        if self.workflow.get_state(config).next:
            self._resume(message=message, config=config)
            return
        self._invoke(message=message, config=config)

    # continue with human input
    def _resume(self, message: Message, config: dict) -> None:
        self.workflow.invoke(input=Command(resume=message), config=config)

    # this method is executed every time user starts a new journey in the session (from the start node)
    def _invoke(self, message: Message, config: dict) -> None:
        current_state = self._prepare_state(message=message, config=config)
        if self._should_continue(config, message):
            self.workflow.invoke({CHATBOT_STATE: current_state}, config=config)

    def add_node(self, name: str, function: Callable) -> None:
        """
        Adds a node to the graph with the name and node function.
        This method will ensure that LangGraph state is always correctly checkpointed after the node execution.
        User should not need to write return state deltas in every node function.

        :param name: of the node
        :param function: to be executed in the node
        """
        self.__graph.add_node(name, NodeCheckpointer(function))

    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        Adds static edge between from node and to node in the graph.
        :param from_node: from which to go into the next node
        :param to_node: to which to go from the previous node
        """
        self.__graph.add_edge(from_node, to_node)

    def add_conditional_edge(self, from_node: str, function: Callable) -> None:
        """
        Registers dynamic transition function between from node and to node in the graph. The function should return name of the next node.
        :param from_node: from which to go into the next node
        :param function: to determine the next node
        """
        self.__graph.add_conditional_edges(from_node, function)

    def send_predefined_response(self, key: str, state: State, config: dict, **kwargs) -> None:
        """
        Sends predefined response from translation table to the user, on the channel in which user initiated the conversation.

        :param key: in translation table
        :param state: having user's language
        :param config: channel and session details
        :param kwargs: parameters which can be used to format the localised response template.
        :return: None
        """
        message = self.get_localized_value(key=key, state=state)
        message = message.format(**(self.get_variables(state) | kwargs))
        ChatbotFlow.send_response(message=message, state=state, config=config)

    def send_buttons_response(self, key: str, state: State, config: dict, **kwargs) -> None:
        button_info = self.get_localized_value(key=key, state=state)
        message = button_info[MESSAGE].format(**(self.get_variables(state) | kwargs))
        send_buttons(message=message, buttons=button_info[BUTTONS], config=config)
        button_message = ButtonMessage(role=ASSISTANT, content={TYPE: "text", PAYLOAD: message}, buttons=button_info[BUTTONS])
        ChatbotFlow.get_current_cycle(state=state).messages.append(button_message)

    def get_localized_value(self, key: str, state: State) -> str | dict:
        """
        Returns value (str or dict) from translation table for the key in table and current language in the state
        :param key: in translation table
        :param state: having user's language
        :return: localised value from translation table
        """
        return self.translation_table[key][self.get_language(state=state)]

    # returns true if this is the first user's message in the session, false otherwise
    def _is_new_session(self, config: dict) -> bool:
        snapshot = self.workflow.get_state(config=config).values
        return len(snapshot) == 0

    # returns true if graph should be executed for this context (e.g. successful authorization), false otherwise
    def _should_continue(self, config, message):
        if not self._is_new_session(config=config):
            return True
        # first ever message in the session
        return self.on_session_start(message=message, config=config)

    def get_state(self, config: dict) -> State:
        """
        Returns the state of the chatbot.
        :param config: with session and channel details
        :return: current state of the chatbot
        """
        return self.workflow.get_state(config=config).values

    def _prepare_state(self, message: Message, config: dict) -> ChatbotState:
        """
        Returns the state of the chatbot with the user's message and session details.
        If this is a new conversation cycle, user message will initiative new conversation cycle in the state.
        """
        language = config[CONFIGURABLE][LANGUAGE] if LANGUAGE in config[CONFIGURABLE] else self.configuration.default_language
        snapshot = self.workflow.get_state(config=config).values
        if not snapshot:
            return ChatbotState(conversation_cycles=[ConversationCycle(messages=[message])], user_language=language, variables={})

        cycles = snapshot.get(CHATBOT_STATE).get(CONVERSATION_CYCLES)
        intent = cycles[-1].intent
        variables = dict(snapshot.get(CHATBOT_STATE).get(VARIABLES))
        cycles.append(ConversationCycle(messages=[message], intent=intent))
        return ChatbotState(conversation_cycles=cycles, user_language=language, variables=variables)

    @staticmethod
    def get_language(state: State) -> str:
        """
        Returns user's language from the state.
        Language will be automatically determined by runtime environment executing this graph.
        :param state: with the user's language
        :return: user's language
        """
        return state[CHATBOT_STATE][_user_language]

    @staticmethod
    def get_user_message(state: State) -> dict:
        """
        Returns the last user message from the current conversation cycle in the state.
        :param state: from which to return the user's message
        :return: the last user message
        """
        messages = state[CHATBOT_STATE][CONVERSATION_CYCLES][-1].messages
        for message in reversed(messages):
            if message.role == USER_ROLE:
                return message.content
        return {}

    @staticmethod
    def get_last_message(state: State) -> Message:
        """
        Returns the last user or AI message from the current conversation cycle in the state.
        :param state: from which to return the last message
        :return: the last message, can be inbound or outbound
        """

        last_message = ChatbotFlow.get_current_cycle(state=state).messages[-1]
        return last_message if last_message else None

    @staticmethod
    def get_intent(state: State) -> str:
        """
        Returns determined intent of the user from the state.
        :param state: with intent of the user
        :return: intent
        """
        return state[CHATBOT_STATE][CONVERSATION_CYCLES][-1].intent

    @staticmethod
    def save_intent(state: State, intent: str) -> None:
        """
        Saves intent of the user in the state.
        :param state: of conversation
        :param intent: determined by an intent engine
        :return: None
        """
        ChatbotFlow.get_current_cycle(state=state).intent = intent

    @staticmethod
    def get_current_cycle(state: State) -> ConversationCycle:
        """
        Returns the current conversation cycle from the state of conversation.
        This will be the most recent actions by the user and chatbot.

        :param state: of conversation
        :return: current conversation cycle with most recent actions by the user and chatbot.
        """
        return ChatbotFlow.get_all_cycles(state=state)[-1]

    @staticmethod
    def get_all_cycles(state: State) -> list[ConversationCycle]:
        """
        Returns all conversation cycles from the start of conversation.

        :param state: of conversation
        :return: all conversation cycles from the start of conversation
        """
        return state[CHATBOT_STATE][CONVERSATION_CYCLES]

    @staticmethod
    def get_variable(state: State, name: str) -> str:
        return state[CHATBOT_STATE][VARIABLES].get(name)

    @staticmethod
    def get_variables(state: State) -> dict:
        """
        Returns all user defined variables saved in the state.
        """
        return state[CHATBOT_STATE][VARIABLES]

    @staticmethod
    def get_session_id(config):
        return config[CONFIGURABLE][THREAD_ID]

    @staticmethod
    def send_response(message: str, state: State, config: dict) -> None:
        """
        Sends response to the user on the channel in which user initiated the conversation.
        :param message: to send to the user
        :param state: of the conversation
        :param config: channel and session details
        """
        message = Message(role=ASSISTANT, content={TYPE: "text", PAYLOAD: message})
        send_message(message=message.get_payload(), config=config)
        ChatbotFlow.save_message(state=state, message=message)

    @staticmethod
    def wait_user_input(state: State, config: dict, variable_name: str = None, extractor: Callable = lambda x: x) -> None:
        """
        Waits for user input over the communication channel and saves it in the state. Variable name if specified will
        save the extracted value from the user's message.
        Extractor callable can be used to pre-process extracted value, e.g. convert user's message to desired type.

        IMPORTANT!
        When interrupt is used to read human's input, LangGraph will execute node from the beginning!
        If there is any code before this method is invoked, that code will be executed again!
        Therefore, we suggest that separate node is created every time user input is expected with this method on top of
        the node.

        :param state: of conversation with latest user input
        :param config: session and channel details
        :param variable_name: in which user's input should be saved
        :param extractor: function that maps user's message to desired type
        """
        message: Message = interrupt(value="")
        state[CHATBOT_STATE][_user_language] = (
            config[CONFIGURABLE][LANGUAGE] if LANGUAGE in config[CONFIGURABLE] else state[CHATBOT_STATE][_user_language]
        )
        if variable_name:
            ChatbotFlow.save_variable(name=variable_name, value=extractor(message.content[PAYLOAD]), state=state)
        ChatbotFlow.save_message(state=state, message=message)

    @staticmethod
    def save_variable(name: str, value: Any, state: State) -> None:
        """
        Saves a variable in the state.
        :param name: lookup name of the variable
        :param value: of the variable
        :param state: to persist the variable
        """
        state[CHATBOT_STATE][VARIABLES][name] = value

    @staticmethod
    def save_message(state: State, message: Message) -> None:
        """
        Saves message of the user to the current conversation cycle in the state.
        :param state: in which to save the message
        :param message: of the user
        """
        ChatbotFlow.get_current_cycle(state=state).messages.append(message)
