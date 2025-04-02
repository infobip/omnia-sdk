from omnia_sdk.workflow.tools.localization.translation_table import dfs_format_json


def test_empty_dict():
    data = {}
    expected = {}
    result = dfs_format_json(data, foo="Won't Appear")
    assert result == expected


def test_unformatted_string():
    data = "No placeholders here"
    expected = "No placeholders here"
    result = dfs_format_json(data, foo="Won't Appear")
    assert result == expected


def test_format_string():
    data = "Hello, {foo}!"
    expected = "Hello, World!"
    result = dfs_format_json(data, foo="World")
    assert result == expected


def test_format_list():
    data = ["{foo}1", "{foo}2"]
    expected = ["Bar1", "Bar2"]
    result = dfs_format_json(data, foo="Bar")
    assert result == expected


def test_format_dict():
    data = {"key1": "{foo}", "key2": "Value"}
    expected = {"key1": "Bar", "key2": "Value"}
    result = dfs_format_json(data, foo="Bar")
    assert result == expected


def test_format_nested_dict():
    data = {"a": "{foo}", "b": {"c": "X{foo}Y"}}
    expected = {"a": "Baz", "b": {"c": "XBazY"}}
    result = dfs_format_json(data, foo="Baz")
    assert result == expected


def test_format_mixed_nested_structures():
    data = {
        "greeting": "Hi {foo}",
        "items": ["{foo}1", {"deep": "{foo}2"}],
        "meta": 123
    }
    expected = {
        "greeting": "Hi Sam",
        "items": ["Sam1", {"deep": "Sam2"}],
        "meta": 123
    }
    result = dfs_format_json(data, foo="Sam")
    assert result == expected


def test_format_with_non_string_leaves():
    data = {
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
        "string": "{foo}"
    }
    expected = {
        "int": 42,
        "float": 3.14,
        "bool": True,
        "none": None,
        "string": "Zed"
    }
    result = dfs_format_json(data, foo="Zed")
    assert result == expected


def test_deeply_nested_structures():
    data = {"a": [{"b": ["{foo}", {"c": "{foo}"}]}]}
    expected = {"a": [{"b": ["Deep", {"c": "Deep"}]}]}
    result = dfs_format_json(data, foo="Deep", bar="Won't Appear")
    assert result == expected
