from typing import override

from omnia_sdk.workflow.tools.localization.translation_table import TranslationTable, dfs_format_json


class CPaaSTranslationTable(TranslationTable):
    """
    Class representing a translation table for localization.
    The class expects two dictionaries as input:
     - CPaaS data
     - constants
    CPaaS data dictionary has localization entries which should correspond to Infobips Omni Channel API
    - https://www.infobip.com/docs/api/platform/messages-api
    Values in this dictionary correspond to outbound messages sent to the user.

    Constants dictionary has localization for hard coded values which can be used as variables in response sent to the user.
    Example of localization.py is available in omnia-sdk-examples repository.
    """

    def __init__(self, translation_table_cpaas: dict, translation_table_constants: dict):
        """
        Initializes the TranslationTable with the provided translation table.
        :param translation_table_cpaas: A dictionary with Infobips Omni Channel API message localization
        :param translation_table_constants: A dictionary with localization for hard coded values
        """
        super().__init__(translation_table_cpaas=translation_table_cpaas, translation_table_constants=translation_table_constants)

    @override
    def get_localized_message(self, key: str, language: str, **kwargs) -> dict:
        """
        Returns the localized message for the given key and language
        :param key: for which to get the localized message
        :param language: in which to get the localized message
        :return: localized message
        """
        message = self.translation_table_cpaas[key][language]
        message = dfs_format_json(message, **kwargs)
        return message

    @override
    def get_localized_constant(self, key: str, language: str) -> str:
        """
        Returns the localized constant for the given key and language
        :param key: for which to get the localized constant
        :param language: in which to localize constant
        :return: constant in correct language
        """
        return self.translation_table_constants[key][language]
