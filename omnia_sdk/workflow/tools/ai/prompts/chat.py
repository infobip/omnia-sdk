import asyncio
from typing import Any

import requests
from google import genai
from google.genai.types import ContentListUnion, GenerateContentConfig, GenerateContentResponse, HttpOptions
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from omnia_sdk.workflow.chatbot.constants import CONFIGURABLE, THREAD_ID, WORKFLOW_ID, WORKFLOW_VERSION
from omnia_sdk.workflow.tools.ai.constants import SESSION_ID_HEADER, WORKFLOW_ID_HEADER, WORKFLOW_VERSION_HEADER
from omnia_sdk.workflow.tools.ai.llm_models import ChatSessionRequest, ChatSessionResponse, IntentInstruction
from omnia_sdk.workflow.tools.channels.config import INFOBIP_API_KEY, INFOBIP_BASE_URL
from omnia_sdk.workflow.tools.rest.exceptions import ApplicationError
from omnia_sdk.workflow.tools.rest.retryable_http_client import retryable_request

default_headers = {"Authorization": f"App {INFOBIP_API_KEY}"}

openai_client = OpenAI(api_key="", base_url=f"{INFOBIP_BASE_URL}/gpt-creator/omnia/openai/v1", default_headers=default_headers)
openai_client_async = AsyncOpenAI(api_key="", base_url=f"{INFOBIP_BASE_URL}/gpt-creator/omnia/openai/v1", default_headers=default_headers)

google_client = client = genai.Client(
    api_key="dummy_api_key",
    http_options=HttpOptions(base_url=f"{INFOBIP_BASE_URL}/gpt-creator/omnia/google", api_version="v1", headers=default_headers)
)


def google_generate_content(
    model: str, contents: ContentListUnion, google_config: GenerateContentConfig | None = None, config: dict | None = None
) -> GenerateContentResponse:
    """
    Sends request to Infobip's Google Gemini endpoint to generate content.
    
    :param config: channel and session details
    :param google_config: optional Google Gemini configuration
    :param kwargs: additional parameters for the request
    """
    google_config = _add_headers(google_config, config)
    return client.models.generate_content(model=model, contents=contents, config=google_config)


async def google_generate_content_async(
    model: str, contents: ContentListUnion, google_config: GenerateContentConfig | None = None, config: dict | None = None
) -> GenerateContentResponse:
    """
    Sends async request to Infobip's Google Gemini endpoint to generate content.
    
    :param config: channel and session details
    :param google_config: optional Google Gemini configuration
    :param kwargs: additional parameters for the request
    """
    google_config = _add_headers(google_config, config)
    return await client.aio.models.generate_content(model=model, contents=contents, config=google_config)


def chat_completions(
    messages: list, model: str = None, extract_params: bool = False, config: dict = None, **chat_completions_params
) -> ChatCompletion:
    """
    Sends request to Infobip's chat completions endpoint which should be 1/1 compatible with OpenAI's chat completions endpoint.
    User may also specify Gemini models and we will use Gemini with OpenAI compatible API.
    # TODO see models here ...

    Extract params feature is also supported on this endpoint, see the chat_session pydocs for details.

    :param messages: OpenAI like messages list
    :param model: OpenAI or Gemini model
    :param extract_params: whether to extract params from llm response
    :param config: channel and session details
    :param chat_completions_params: OpenAI like chat completions parameters
    :return: ChatCompletion model instance
    """
    try:
        return openai_client.chat.completions.create(
            messages=messages, model=model, extra_headers=_prepare_headers(config), extra_body={"extract_params": extract_params},
            **chat_completions_params
        )
    except Exception as e:
        raise ApplicationError(code=500, message=str(e))


async def chat_completions_async(
    messages: list, model: str = None, extract_params: bool = False, config: dict = None, **chat_completions_params
) -> ChatCompletion:
    """
    Sends request to Infobip's chat completions endpoint asynchronously, returning coroutine.
    See chat_completions pydocs for API details.
    """
    try:
        return await openai_client_async.chat.completions.create(
            messages=messages,
            model=model,
            extra_headers=_prepare_headers(config),
            extra_body={"extract_params": extract_params},
            **chat_completions_params,
        )
    except Exception as e:
        raise ApplicationError(code=500, message=str(e))


async def batch_chat_completions(chat_completion_requests: list[dict[str, Any]], config: dict = None) -> list[ChatCompletion]:
    """
    Run multiple chat completion requests concurrently.
    This invocation should be wrapped with asyncio.run() to generate event loop as the runtime environment is synchronous.

    Example invocation:
        import asyncio
        ...
        cats = [{"role": "user","content": "Tell me joke about cats"}]
        dogs = [{"role": "user","content": "Tell me joke about dogs"}]
        tasks = [{'messages': cats}, {'messages': dogs}]
        foo = asyncio.run(batch_chat_completions(chat_completion_requests=tasks))
        print([f.choices[0].message.content for f in foo])

    Each request dict should include:
        - messages: list
        - model: str
        - extract_params: bool (optional)
        - any other OpenAI-like completion params


    return: List of ChatCompletion objects, in the same order as the requests.
    """
    tasks = [
        chat_completions_async(
            messages=req["messages"],
            model=req.get("model"),
            extract_params=req.get("extract_params", False),
            config=config,
            **{k: v for k, v in req.items() if k not in {"messages", "model", "extract_params"}},
        ) for req in chat_completion_requests
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)


def chat_session(config: dict, chat_session_request: ChatSessionRequest) -> ChatSessionResponse:
    """
    Sends request to Infobip's stateful chat completions endpoint.
    User may specify Gemini and OpenAI models.
    # TODO see models here ...
    Endpoint is intended to be used to save user <-> LLM interactions one by one so the caller does not need to track the conversation
    state in their own system.

    Session window parameter defines how many previous user <-> LLM interactions will endpoint consider.
    Memory_key parameter defines the key under which the endpoint will persist the user <-> LLM interactions.
    Extract_params parameter defines whether the endpoint should return parsed parameters from the user message.
    This works if system message/prompt contains instructions to extract params denoted with following delimiters: <>, [], {}.
    This might work better than json in some cases.

    API expectations:
    MEMORY
    Should user_message be specified, the endpoint will persist ONLY user message instead of complete prompt instruction.
    Otherwise, the endpoint will persist the prompt instruction.
    System message can be sent only once in the first message.
    Subsequent system messages will overwrite the previous one.

    TOOLS
    When the LLM returns tool_calls response, user should execute the tool_calls in the order they were returned.
    Afterward, this endpoint must be invoked with results of each tool_call and optional user message.
    If user message is not provided, LLM will generate response based on the previous message and tool call results.
    IF user message is provided, LLM will generate response based on the user message and tool call results.

    Example:
     - prompt= "What is the weather like in Paris today?"
     - tool_call:
        [{"id": "call_12345xyz", "type": "function","function": {"name": "get_weather","arguments": "{\"location\":\"Paris, France\"}"}}]
      execute tool_call
      - call the endpoint with the result of the tool_call to persist the result, and optionally new user message

    :param config: with channel and session details
    :param chat_session_request: stateful chat completions request
    :return: ChatSessionResponse model instance
    """
    headers = _prepare_headers(config) | default_headers
    body = {
        "prompt": chat_session_request.prompt,
        "user_message": chat_session_request.user_message,
        "tool_results": chat_session_request.tool_results,
        "system_message": chat_session_request.system_message,
        "images": chat_session_request.images,
        "session_window": chat_session_request.session_window,
        "memory_key": chat_session_request.memory_key,
        "extract_params": chat_session_request.extract_params,
        **chat_session_request.chat_completions_params,
    }
    url = f"{INFOBIP_BASE_URL}/gpt-creator/omnia/chat-session"
    response_body = retryable_request(x=requests.post, config=config, url=url, json=body, headers=headers)
    return ChatSessionResponse(**response_body)


def detect_intent(config: dict, intent_instruction: IntentInstruction) -> str:
    """
    Returns intent inferred for the message using GenAI tool.

    :param config: with session and channel details
    :param intent_instruction: prompt instructions for GenAI intent detection
    :return: inferred intent, or ApplicationError in request failed after retries
    """
    session_id = config[CONFIGURABLE][THREAD_ID]
    headers = {SESSION_ID_HEADER: session_id} | default_headers
    url = f"{INFOBIP_BASE_URL}/gpt-creator/omnia/2/intent"
    response_body = retryable_request(x=requests.post, config=config, url=url, json=intent_instruction.model_dump(), headers=headers)
    return response_body["response"]


def _prepare_headers(config: dict | None) -> dict:
    extra_headers = {
        SESSION_ID_HEADER: config[CONFIGURABLE][THREAD_ID],
        WORKFLOW_ID_HEADER: config[CONFIGURABLE].get(WORKFLOW_ID),
        WORKFLOW_VERSION_HEADER: config[CONFIGURABLE].get(WORKFLOW_VERSION),
    } if config else dict()
    # only defined headers are returned as httpx raises on None headers
    return {k: v for k, v in extra_headers.items() if v is not None}


def _add_headers(google_config: GenerateContentConfig, config: dict) -> GenerateContentConfig:
    headers = _prepare_headers(config)
    google_config = google_config or GenerateContentConfig()

    # Initialize http_options with headers if not present
    if not google_config.http_options:
        google_config.http_options = HttpOptions(headers=headers)
        return google_config

    # Merge headers with existing ones
    existing_headers = google_config.http_options.headers or {}
    google_config.http_options.headers = {**existing_headers, **headers}
    return google_config
