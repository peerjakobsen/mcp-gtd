"""
Tests for MCP decorators and parameter preprocessing.

These tests verify that the parameter preprocessing decorator correctly
handles MCP client serialization issues where parameters arrive as JSON strings.
"""

from typing import Any


def test_preprocess_params_decorator_handles_json_string_lists():
    """Test that JSON string lists are deserialized to Python lists."""
    from gtd_manager.decorators import preprocess_params

    @preprocess_params
    def sample_function(items: list[str]) -> list[str]:
        return items

    # Test with JSON string input (how MCP clients send it)
    json_string = '["item1", "item2", "item3"]'
    result = sample_function(items=json_string)

    assert result == ["item1", "item2", "item3"]
    assert isinstance(result, list)


def test_preprocess_params_decorator_handles_json_string_dicts():
    """Test that JSON string dictionaries are deserialized to Python dicts."""
    from gtd_manager.decorators import preprocess_params

    @preprocess_params
    def sample_function(data: dict[str, Any]) -> dict[str, Any]:
        return data

    # Test with JSON string input
    json_string = '{"key1": "value1", "key2": 42}'
    result = sample_function(data=json_string)

    assert result == {"key1": "value1", "key2": 42}
    assert isinstance(result, dict)


def test_preprocess_params_decorator_preserves_regular_parameters():
    """Test that non-JSON parameters are passed through unchanged."""
    from gtd_manager.decorators import preprocess_params

    @preprocess_params
    def sample_function(name: str, count: int) -> str:
        return f"{name}: {count}"

    result = sample_function(name="test", count=5)

    assert result == "test: 5"


def test_preprocess_params_decorator_handles_invalid_json():
    """Test that invalid JSON strings are passed through unchanged."""
    from gtd_manager.decorators import preprocess_params

    @preprocess_params
    def sample_function(data: list[str]) -> str:
        return str(data)

    # Invalid JSON should be passed through as-is
    invalid_json = '["incomplete'
    result = sample_function(data=invalid_json)

    assert result == '["incomplete'


def test_preprocess_params_decorator_ignores_non_json_strings():
    """Test that regular strings are not processed as JSON."""
    from gtd_manager.decorators import preprocess_params

    @preprocess_params
    def sample_function(message: str) -> str:
        return message

    # Regular string that doesn't start with [ or {
    regular_string = "hello world"
    result = sample_function(message=regular_string)

    assert result == "hello world"


def test_mcp_tool_decorator_combines_preprocessing_and_logging():
    """Test that the mcp_tool decorator applies parameter preprocessing."""
    from gtd_manager.decorators import mcp_tool

    @mcp_tool
    def sample_tool(items: list[str]) -> str:
        return f"Processed {len(items)} items"

    # Test with JSON string input
    json_string = '["a", "b", "c"]'
    result = sample_tool(items=json_string)

    assert result == "Processed 3 items"


def test_preprocess_params_decorator_handles_mixed_parameters():
    """Test preprocessing with mix of JSON and regular parameters."""
    from gtd_manager.decorators import preprocess_params

    @preprocess_params
    def sample_function(name: str, items: list[str], count: int) -> str:
        return f"{name} has {len(items)} items, count: {count}"

    json_string = '["item1", "item2"]'
    result = sample_function(name="test", items=json_string, count=42)

    assert result == "test has 2 items, count: 42"


class TestParameterPreprocessing:
    """Test class for comprehensive parameter preprocessing verification."""

    def test_function_signature_inspection(self):
        """Test that the decorator properly inspects function signatures."""
        from gtd_manager.decorators import preprocess_params

        @preprocess_params
        def typed_function(items: list[str], data: dict[str, int]) -> str:
            return f"items: {items}, data: {data}"

        # Both parameters as JSON strings
        items_json = '["a", "b"]'
        data_json = '{"x": 1, "y": 2}'

        result = typed_function(items=items_json, data=data_json)

        assert "items: ['a', 'b']" in result
        assert "data: {'x': 1, 'y': 2}" in result

    def test_decorator_preserves_function_metadata(self):
        """Test that the decorator preserves original function metadata."""
        from gtd_manager.decorators import preprocess_params

        @preprocess_params
        def documented_function(param: list[str]) -> str:
            """This function has documentation."""
            return str(param)

        assert documented_function.__name__ == "documented_function"
        assert "This function has documentation" in documented_function.__doc__

    def test_edge_case_empty_json_structures(self):
        """Test handling of empty JSON structures."""
        from gtd_manager.decorators import preprocess_params

        @preprocess_params
        def handle_empty(items: list[str], data: dict[str, Any]) -> str:
            return f"items: {len(items)}, data: {len(data)}"

        result = handle_empty(items="[]", data="{}")

        assert result == "items: 0, data: 0"
