import dataclasses
from typing import Self

import yaml

from omnia_sdk.workflow.chatbot.constants import LLM_DETECTOR

"""
This configuration lets user control automatic runtime environment features:
 - language detection and localisation (optional)
 - concurrent sessions (called Double Texting in LangGraph Studio)

We require one mandatory parameter:
 - default language

Should user wish to have pre-defined responses, we would expect translation.yaml to have all keys in the default language.
This will simplify addition of more languages later for users that wish to start with one language only.

###
 Language detector can work in two regimes:
  - LLM detector
  - Infobip's NLP model custom trained for language detection task
LLM detector will work better for deployments with frequent hybrid language scenarios, e.g. Arabic mixed with English inside same text.
However, it is going to come with latency (+500ms) and cost considerations.

NLP model is *free* and has 1 ms latency. It should work great when user tends to not mix the languages in same message.
There is actually a set of language detection models user can choose, where each model supports subset of languages to
maximise performance. Less languages = better performance.

Available model list will be made public at a later date.
###

###
Parameter:
 - concurrent_session
is used to resolve situations when a user sends second message while the first one is still being processed.
Currently supported strategy is to wait for the first message to finish before executing the second one.
We will add platform support for "rollback" strategy soon which will merge two messages and execute them together.
###

"""


@dataclasses.dataclass
class LanguageDetectorConfig:
    expected_languages: set[str]
    model: str = LLM_DETECTOR

    # if used, language detector does not make sense for less than 2 languages
    def __post_init__(self):
        if len(self.expected_languages) <= 1:
            raise ValueError("At least two languages must be provided")


# TODO not yet supported, leaving as an idea for future
@dataclasses.dataclass
class SessionHooks:
    max_cycles_check: int = None
    callback: str = "{action:agent_transfer}"


@dataclasses.dataclass
class ChatbotConfiguration:
    default_language: str
    language_detector: LanguageDetectorConfig = None
    concurrent_session: str = "enqueue"  # this is the only strategy supported for now, see the module docstring for details

    @staticmethod
    def from_yaml(path: str) -> "ChatbotConfiguration":
        """
        Load configuration from YAML file.

        :param path: Path to the YAML file.
        :return: An instance of ChatbotConfiguration.
        """
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
        language_detector = ChatbotConfiguration._read_language_detector(data.get("language_detector"))
        return ChatbotConfiguration(default_language=data["default_language"], language_detector=language_detector,
                                    concurrent_session=data.get("concurrent_session", "enqueue"))

    @staticmethod
    def _read_language_detector(lang_detector_data) -> LanguageDetectorConfig | None:
        if not lang_detector_data:
            return None
        return LanguageDetectorConfig(expected_languages=set(lang_detector_data["expected_languages"]),
                                      model=lang_detector_data.get("model", LLM_DETECTOR))
