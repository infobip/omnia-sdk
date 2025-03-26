from typing import Optional

from pydantic import BaseModel

"""
This module defines models for the LLM applications. See chat.py and assistant.py modules for more details.
"""


### prompt models ###
class IntentInstruction(BaseModel):
    prompt: str
    intents: list[str]
    user_message: str | None = None
    system_message: str | None = None
    output_tokens: int = 70
    session_window: int = 1
    memory_key: str = "intent"
    chat_model: str | None = None


class ToolCallResult(BaseModel):
    tool_call_id: str
    content: str


# stateful request, check the chat.chat_session pydoc for more details
class ChatSessionRequest(BaseModel):
    prompt: str = None
    system_message: str = None
    user_message: str = None
    tool_results: list[ToolCallResult] = None
    images: list[str] = None
    session_window: int = 1
    memory_key: str = "prompt"
    extract_params: bool = False
    chat_completions_params: dict = None


class ChatSessionResponse(BaseModel):
    response: str | None
    tool_calls: list[dict] | None
    parsed_params: dict | None
    model_usages: list[dict]


### RAG models ###


class ChunkData(BaseModel):
    text: str
    score: Optional[float] = None
    filename: str


class ContextData(BaseModel):
    original_contexts: list[ChunkData]
    reranked_contexts: Optional[list[ChunkData]] = None


class AssistantResponse(BaseModel):
    message: str
    contexts: Optional[list[str]] = None
    optimal_context: Optional[list[str]] = None
    context: Optional[ContextData] = None


class PromptResponse(BaseModel):
    response: str
    parsed_params: Optional[dict] = None
