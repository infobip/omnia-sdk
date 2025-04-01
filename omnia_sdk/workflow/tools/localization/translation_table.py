from abc import ABC, abstractmethod


def dfs_format_json(data, **kwargs):
    """
    Recursively formats a JSON-like data structure using the provided kwargs.
    Strings in the data structure are formatted using the kwargs, non-String values are returned as-is.
    List and dict data containers are traversed recursively and their Strings formatted accordingly.

    :param data: JSON-like data structure to format
    :param kwargs: keyword arguments to use for formatting
    """
    if isinstance(data, str):
        # base case for recursion, format the string using kwargs
        return data.format(**kwargs)
    elif isinstance(data, list):
        return [dfs_format_json(item, **kwargs) for item in data]
    elif isinstance(data, dict):
        return {key: dfs_format_json(value, **kwargs) for key, value in data.items()}
    # For any other data types, return them as-is
    return data


class TranslationTable(ABC):
    """
    Class representing a translation table for localization.
    """

    def __init__(self, translation_table_cpaas: dict, translation_table_constants: dict):
        """
        Initializes the TranslationTable with the provided translation table.
        :param translation_table_cpaas: A dictionary with Infobips Omni Channel API message localization
        :param translation_table_constants: A dictionary with localization for hard coded values
        """
        self.translation_table_cpaas = translation_table_cpaas
        self.translation_table_constants = translation_table_constants

    @abstractmethod
    def get_localized_message(self, key: str, language: str, **kwargs) -> dict:
        """
        Returns the localized message for the given key and language
        :param key: for which to get the localized message
        :param language: in which to get the localized message
        :return: localized message
        """
        pass

    @abstractmethod
    def get_localized_constant(self, key: str, language: str) -> str:
        """
        Returns the localized constant for the given key and language
        :param key: for which to get the localized constant
        :param language: in which to get the localized constant
        :return: localized constant
        """
        pass
