from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt

from omnia_sdk.workflow.chatbot.chatbot_configuration import ChatbotConfiguration
from omnia_sdk.workflow.chatbot.chatbot_state import (
    ChatbotState,
    ConversationCycle,
    Message,
)
from omnia_sdk.workflow.chatbot.constants import (
    ASSISTANT,
    CONFIGURABLE,
    LANGUAGE,
    METADATA,
    USER,
    THREAD_ID,
    RECURSION_LIMIT,
)
from omnia_sdk.workflow.langgraph.chatbot.node_checkpointer import NodeCheckpointer
from omnia_sdk.workflow.tools.answers._context import set_workflow_state
from omnia_sdk.workflow.tools.channels.omni_channels import (
    ButtonDefinition,
    get_outbound_buttons_format,
    get_outbound_text_format,
    send_message,
    ListSectionDefinition,
    get_outbound_list_format,
    get_outbound_image_format,
)
from omnia_sdk.workflow.tools.localization.cpaas_translation_table import (
    CPaaSTranslationTable,)
from omnia_sdk.workflow.tools.localization.translation_table import TranslationTable
"""
This class should enable easy access to Infobip's SaaS, CPaaS and AI services while simplifying LangGraph state management.
Built graph is **channel agnostic** and can be multilingual with the help of language detector and translation table.

This module contains the prototype class for chatbot applications built via LangGraph.
To get started we recommend to first check TinyChatbot example in the project.
Afterwards, you could check more complete examples here:
 - https://github.com/infobip/omnia-sdk-examples
To get familiar with LangGraph features, check examples here:
 - https://github.com/langchain-ai/langgraph/tree/main/examples

To get started with Omnia-sdk user should create a new class that inherits from ChatbotFlow and implement methods:
 - nodes(...)
 - transitions(...)
User is also required to invoke method create_entry_point("start_node_name") inside nodes(...) method.

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


MAX_RECURSION_LIMIT = 100


class ChatbotFlow(ABC):
    # This constructor will be invoked by runtime environment with user submitted files
    def __init__(self, checkpointer: BaseCheckpointSaver = None, configuration: ChatbotConfiguration | None = None,
                 translation_table: TranslationTable | None = None, environment: dict | None = None):
        self.__graph = StateGraph(State)
        self.configuration = configuration
        self.translation_table = translation_table if translation_table else CPaaSTranslationTable(
            translation_table_cpaas={}, translation_table_constants={})
        self._nodes()
        self._transitions()
        checkpointer = checkpointer if checkpointer else MemorySaver()
        self.workflow = self.__graph.compile(checkpointer=checkpointer)
        self.__environment = environment

    @abstractmethod
    def _nodes(self):
        """
        User should implement this method to define nodes of the chatbot graph.
        We strongly encourage users to use method:
         - self.add_node("node_name", self.node_function)
        instead of directly modifying the graph.

        IMPORTANT:
        User must invoke create_entry_point method to set the entry point of the graph:
            self.create_entry_point("start_node_name")

        This method will ensure that LangGraph state is always correctly checkpointed after each node execution without requiring
        users to return deltas in every node function.
        """
        pass

    def _transitions(self):
        """
        User should implement this method to define transitions of the chatbot graph.
        We strongly encourage users to use methods:
            - self.add_edge("from_node", "to_node")
            - self.add_conditional_edge("from_node", self.transition_function)
        instead of directly modifying the graph.

        ALTERNATIVE IMPLEMENTATION:
        Users may also define edges via Command objects or Transition objects in the node functions.
        - https://blog.langchain.dev/command-a-new-tool-for-multi-agent-architectures-in-langgraph/
        See the test_commands_state_management.py for example

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

        :param message: user message
        :param config: channel and session details
        :return: true if chatbot flow should continue, false otherwise
        """
        # line here is to avoid warning for unused variables
        _ = (self, message, config)
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

        :param message: user message
        :param config: channel and session parameters
        """
        # end node does not have any nodes to which it loops back
        self._set_recursion_limit(config=config)
        if self.workflow.get_state(config).next:
            self._resume(message=message, config=config)
            return
        self._invoke(message=message, config=config)

    # continue with human input
    def _resume(self, message: Message, config: dict) -> None:
        self.workflow.invoke(input=Command(resume=message), config=config)

    # this method is executed every time user starts a new conversation cycle in chatbot graph (from the start node)
    def _invoke(self, message: Message, config: dict) -> None:
        current_state = self._prepare_state(message=message, config=config)
        if self._should_start(config=config, message=message):
            self.workflow.invoke({CHATBOT_STATE: current_state}, config=config)

    def _set_recursion_limit(self, config: dict):
        if self.configuration and self.configuration.recursion_limit:
            config[RECURSION_LIMIT] = min(self.configuration.recursion_limit, MAX_RECURSION_LIMIT)

    def add_node(self, name: str, function: Callable) -> None:
        """
        Adds a node to the graph with the name and node function.
        This method will ensure that LangGraph state is always correctly checkpointed after the node execution.
        User should not need to write return state deltas in every node function.

        :param name: node name
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
        Translation table values should contain messages, buttons, etc. which can be sent to the user in the Infobip's
        messaging format.
        You can see example in our omnia-sdk-examples repository.

        :param key: in translation table
        :param state: having user's language
        :param config: channel and session details
        :param kwargs: parameters which can be used to format the localised response template.
        """
        kwargs = self.get_variables(state) | kwargs
        content = self.translation_table.get_localized_message(key=key, language=self.get_language(state), **kwargs)
        ChatbotFlow.send_response(content=content, state=state, config=config)

    def get_localized_constant(self, key: str, state: State) -> str:
        """
        Returns localized constant from the translation table.
        :param key: in the translation table
        :param state: with user's language
        :return: localized constant
        """
        language = self.get_language(state=state)
        return self.translation_table.get_localized_constant(key=key, language=language)

    # returns true if this is the first user's message in the session, false otherwise
    def _is_new_session(self, config: dict) -> bool:
        snapshot = self.workflow.get_state(config=config).values
        return len(snapshot) == 0

    # returns true if graph should be executed for this context (e.g. successful authorization), false otherwise
    def _should_start(self, config: dict, message: Message) -> bool:
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

    def get_environment_variable(self, variable_name: str, default: Any | None = None) -> Any | None:
        if not self.__environment:
            return default
        return self.__environment.get(variable_name, default)

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
    def get_user_message(state: State) -> Message | None:
        """
        Returns the last user message from the current conversation cycle in the state.
        :param state: from which to return the user's message
        :return: the last user message
        """
        messages = state[CHATBOT_STATE][CONVERSATION_CYCLES][-1].messages
        for message in reversed(messages):
            if message.role == USER:
                return message
        return None

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
    def get_variable(state: State, name: str) -> Any:
        """
        Returns user defined variable saved in the state.

        :param state: of conversation
        :param name: of the variable
        :return: user defined variable saved in the state
        """
        return state[CHATBOT_STATE][VARIABLES].get(name)

    @staticmethod
    def get_variables(state: State) -> dict:
        """
        Returns all user defined variables saved in the state.
        """
        return state[CHATBOT_STATE][VARIABLES]

    @staticmethod
    def get_session_id(config) -> str:
        return config[CONFIGURABLE][THREAD_ID]

    @staticmethod
    def get_metadata(config: dict) -> dict:
        """
        Returns metadata from the config.
        
        :param config: with session and channel details
        :return: metadata dictionary
        """
        return config[CONFIGURABLE].get(METADATA, {})

    @staticmethod
    def send_text_response(text: str, state: State, config: dict):
        """
        Sends text response to the user on the channel in which user initiated the conversation.

        :param text: to send to the user
        :param state: conversation state
        :param config: channel and session details
        """
        content = get_outbound_text_format(text=text)
        ChatbotFlow.send_response(content=content, state=state, config=config)

    @staticmethod
    def send_buttons_response(text: str, buttons: list[ButtonDefinition], state: State, config: dict):
        """
        Sends text message with buttons to the user on the channel in which user initiated the conversation.

        :param text: to send to the user
        :param buttons: to render in chat
        :param state: conversation state
        :param config: channel and session details
        """
        content = get_outbound_buttons_format(text=text, buttons=buttons)
        ChatbotFlow.send_response(content=content, state=state, config=config)

    @staticmethod
    def send_list_response(text: str, subtext: str, sections: list[ListSectionDefinition], state: State, config: dict):
        """
        Sends text message with list of options to the user on the channel in which user initiated the conversation.

        :param text: to send to the user
        :param subtext: text shown inside of list picker
        :param sections: to render in list picker
        :param state: conversation state
        :param config: channel and session details
        """
        content = get_outbound_list_format(text=text, subtext=subtext, sections=sections)
        ChatbotFlow.send_response(content=content, state=state, config=config)

    @staticmethod
    def send_image_response(image_url: str, state: State, config: dict):
        """
        Sends image response to the user on the channel in which user initiated the conversation.
        :param image_url: URL of the image to send to user
        :param state: conversation state
        :param config: channel and session details
        """
        content = get_outbound_image_format(image_url=image_url)
        ChatbotFlow.send_response(content=content, state=state, config=config)

    @staticmethod
    def send_response(content: dict, state: State, config: dict = None) -> None:
        """
        Sends response to the user on the channel in which user initiated the conversation.
        :param content: channel payload to send to user
        :param state: conversation state
        :param config: channel and session details
        """
        message = Message(role=ASSISTANT, content=content)
        send_message(message=message, config=config)
        ChatbotFlow.save_message(state=state, message=message)

    @staticmethod
    def wait_user_input(state: State, config: dict, variable_name: str = None, extractor: Callable = lambda x: x) -> Any | None:
        """
        Waits for user input over the communication channel and saves it in the state. Variable name if specified will
        save the extracted value from the user's message.
        Extractor callable can be used to pre-process extracted value, e.g. convert user's message to desired type.
        We extract text content from the user's message with the following rules:
         - If user sends text message, we extract entire content
         - If user sends button message, we extract postback data

        IMPORTANT!
        When interrupt is used to read human's input, LangGraph will execute node from the beginning!
        If there is any code before this method is invoked, that code will be executed again!
        Therefore, we suggest that separate node is created every time user input is expected with this method on top of
        the node.

        :param state: of conversation with latest user input
        :param config: session and channel details
        :param variable_name: in which user's input should be saved
        :param extractor: function that maps user's message to desired type
        :return: extracted text content from user message
        """
        message: Message = interrupt(value="")
        state[CHATBOT_STATE][_user_language] = (config[CONFIGURABLE][LANGUAGE]
                                                if LANGUAGE in config[CONFIGURABLE] else state[CHATBOT_STATE][_user_language])
        ChatbotFlow.save_message(state=state, message=message)
        if variable_name:
            ChatbotFlow.save_variable(name=variable_name, value=extractor(message.get_text()), state=state)
        return extractor(message.get_text())

    @staticmethod
    def save_variable(name: str, value: Any, state: State) -> None:
        """
        Saves a variable in the state.
        :param name: lookup name of the variable
        :param value: variable value
        :param state: to persist the variable
        """
        state[CHATBOT_STATE][VARIABLES][name] = value

    @staticmethod
    def save_message(state: State, message: Message) -> None:
        """
        Saves message of the user to the current conversation cycle in the state.
        :param state: in which to save the message
        :param message: user message
        """
        ChatbotFlow.get_current_cycle(state=state).messages.append(message)

    @staticmethod
    def return_to_answers(state: dict) -> None:
        """
        This method is used to return the session back to Answers chatbot.

        :param state: state that will be returned to Answers chatbot
        """
        set_workflow_state(state)
