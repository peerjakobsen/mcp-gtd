"""
Tests for MCP error handling and response formatting.

These tests verify that error responses are standardized and user-friendly,
following MCP best practices for error handling.
"""

import sqlite3


def test_create_error_response_basic():
    """Test basic error response creation."""
    from gtd_manager.errors import create_error_response

    response = create_error_response(
        error_message="Something went wrong", error_code="GENERIC_ERROR"
    )

    assert response["success"] is False
    assert response["error"] == "Something went wrong"
    assert response["error_code"] == "GENERIC_ERROR"


def test_create_error_response_with_tool_name():
    """Test error response with tool name included."""
    from gtd_manager.errors import create_error_response

    response = create_error_response(
        error_message="Invalid parameter",
        error_code="PARAMETER_ERROR",
        tool_name="test_tool",
    )

    assert response["success"] is False
    assert response["error"] == "Invalid parameter"
    assert response["error_code"] == "PARAMETER_ERROR"
    assert response["tool_name"] == "test_tool"


def test_create_error_response_with_suggestions():
    """Test error response with helpful suggestions."""
    from gtd_manager.errors import create_error_response

    suggestions = ["Try using a different format", "Check the documentation"]
    response = create_error_response(
        error_message="Format error", error_code="FORMAT_ERROR", suggestions=suggestions
    )

    assert response["success"] is False
    assert response["error"] == "Format error"
    assert response["error_code"] == "FORMAT_ERROR"
    assert response["suggestions"] == suggestions


def test_safe_tool_execution_decorator_catches_exceptions():
    """Test that safe_tool_execution decorator catches and formats exceptions."""
    from gtd_manager.errors import safe_tool_execution

    @safe_tool_execution
    def failing_tool():
        raise ValueError("Test error")

    result = failing_tool()

    assert result["success"] is False
    assert "Test error" in result["error"]
    assert result["error_code"] == "INTERNAL_ERROR"
    assert result["tool_name"] == "failing_tool"


def test_safe_tool_execution_decorator_passes_through_success():
    """Test that safe_tool_execution decorator passes through successful results."""
    from gtd_manager.errors import safe_tool_execution

    @safe_tool_execution
    def successful_tool():
        return "Success!"

    result = successful_tool()

    assert result == "Success!"


def test_handle_database_error():
    """Test database-specific error handling."""
    from gtd_manager.errors import handle_database_error

    db_error = sqlite3.IntegrityError("FOREIGN KEY constraint failed")
    response = handle_database_error(db_error, "test_tool")

    assert response["success"] is False
    assert "database constraint" in response["error"].lower()
    assert response["error_code"] == "DATABASE_ERROR"
    assert response["tool_name"] == "test_tool"


def test_handle_parameter_validation_error():
    """Test parameter validation error handling."""
    from gtd_manager.errors import (
        ParameterValidationError,
        handle_parameter_validation_error,
    )

    validation_error = ParameterValidationError("Invalid ID format")
    response = handle_parameter_validation_error(validation_error, "test_tool")

    assert response["success"] is False
    assert response["error"] == "Invalid ID format"
    assert response["error_code"] == "PARAMETER_ERROR"
    assert response["tool_name"] == "test_tool"


def test_handle_resource_exhaustion_error():
    """Test resource exhaustion error handling."""
    from gtd_manager.errors import handle_resource_exhaustion_error

    memory_error = MemoryError("String too large")
    response = handle_resource_exhaustion_error(memory_error, "test_tool")

    assert response["success"] is False
    assert "too large" in response["error"]
    assert response["error_code"] == "RESOURCE_ERROR"
    assert response["tool_name"] == "test_tool"


def test_handle_generic_error():
    """Test generic error handling for unexpected exceptions."""
    from gtd_manager.errors import handle_generic_error

    generic_error = RuntimeError("Unexpected error")
    response = handle_generic_error(generic_error, "test_tool")

    assert response["success"] is False
    assert "unexpected error" in response["error"].lower()
    assert response["error_code"] == "INTERNAL_ERROR"
    assert response["tool_name"] == "test_tool"


class TestParameterValidationError:
    """Test the custom ParameterValidationError exception."""

    def test_parameter_validation_error_creation(self):
        """Test creating ParameterValidationError."""
        from gtd_manager.errors import ParameterValidationError

        error = ParameterValidationError("Invalid parameter")
        assert str(error) == "Invalid parameter"
        assert isinstance(error, ValueError)

    def test_parameter_validation_error_with_suggestions(self):
        """Test ParameterValidationError with suggestions."""
        from gtd_manager.errors import ParameterValidationError

        suggestions = ["Use a different format", "Check the docs"]
        error = ParameterValidationError("Invalid format", suggestions=suggestions)

        assert str(error) == "Invalid format"
        assert error.suggestions == suggestions


class TestSafeToolExecution:
    """Test comprehensive safe tool execution scenarios."""

    def test_safe_tool_execution_with_different_error_types(self):
        """Test that different error types are handled appropriately."""
        from gtd_manager.errors import ParameterValidationError, safe_tool_execution

        @safe_tool_execution
        def validation_error_tool():
            raise ParameterValidationError("Bad parameter")

        @safe_tool_execution
        def database_error_tool():
            raise sqlite3.Error("Database problem")

        @safe_tool_execution
        def memory_error_tool():
            raise MemoryError("Out of memory")

        # Test parameter validation error
        result1 = validation_error_tool()
        assert result1["error_code"] == "PARAMETER_ERROR"

        # Test database error
        result2 = database_error_tool()
        assert result2["error_code"] == "DATABASE_ERROR"

        # Test memory error
        result3 = memory_error_tool()
        assert result3["error_code"] == "RESOURCE_ERROR"

    def test_safe_tool_execution_preserves_function_metadata(self):
        """Test that the decorator preserves function metadata."""
        from gtd_manager.errors import safe_tool_execution

        @safe_tool_execution
        def documented_tool():
            """This tool has documentation."""
            return "result"

        assert documented_tool.__name__ == "documented_tool"
        assert "This tool has documentation" in documented_tool.__doc__
