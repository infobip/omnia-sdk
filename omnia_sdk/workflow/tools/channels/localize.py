def is_value_in_table(key: str, value: str, translation_table: dict[str, dict]) -> bool:
    """
    Returns true if there is value in any language in translation table for the given key
    :param key: for which to check set of values
    :param value: to look for in values for the given key in translation table
    :param translation_table: with localisation data
    :return: true if there is value in any language in translation table for the given key
    """
    return value in translation_table[key].values()
