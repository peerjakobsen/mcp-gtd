"""
Error handling utilities for MCP tools.

This module provides standardized error response formats and exception handling
following MCP best practices for user-friendly error messages.
"""

import sqlite3
from collections.abc import Callable
from functools import wraps
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ParameterValidationError(ValueError):
    """
    Custom exception for parameter validation errors.

    This exception is raised when tool parameters fail validation
    and includes optional suggestions for fixing the issue.
    """

    def __init__(self, message: str, suggestions: list[str] | None = None):
        super().__init__(message)
        self.suggestions = suggestions or []


# GTD-specific error classes for repository operations


class GTDValidationError(ValueError):
    """Raised when GTD domain validation rules are violated."""

    pass


class GTDNotFoundError(ValueError):
    """Raised when requested GTD entity is not found."""

    pass


class GTDDuplicateError(ValueError):
    """Raised when attempting to create duplicate GTD entity."""

    pass


class GTDDatabaseError(Exception):
    """Raised when database operations fail due to constraints or integrity issues."""

    pass


def create_error_response(
    error_message: str,
    error_code: str,
    tool_name: str | None = None,
    suggestions: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create standardized error response for MCP tools.

    Args:
        error_message: User-friendly error message
        error_code: Machine-readable error code
        tool_name: Name of the tool that encountered the error
        suggestions: Optional list of suggestions to fix the error

    Returns:
        Standardized error response dictionary
    """
    response = {"success": False, "error": error_message, "error_code": error_code}

    if tool_name:
        response["tool_name"] = tool_name
    if suggestions:
        response["suggestions"] = suggestions

    return response


def handle_database_error(error: sqlite3.Error, tool_name: str) -> dict[str, Any]:
    """
    Handle database-specific errors with user-friendly messages.

    Args:
        error: The database error that occurred
        tool_name: Name of the tool that encountered the error

    Returns:
        Standardized error response
    """
    error_str = str(error).lower()

    if "foreign key" in error_str:
        message = "Database constraint violated - related record may not exist."
        suggestions = [
            "Verify that referenced records exist",
            "Check your input parameters",
        ]
    elif "unique" in error_str or "duplicate" in error_str:
        message = "A record with these details already exists."
        suggestions = ["Use different values", "Update the existing record instead"]
    elif "not null" in error_str:
        message = "Required information is missing."
        suggestions = ["Provide all required fields", "Check for empty values"]
    else:
        message = "Database operation failed due to a constraint or integrity issue."
        suggestions = ["Verify your input data", "Try the operation again"]

    logger.warning(
        "Database error handled",
        tool=tool_name,
        error_type=type(error).__name__,
        original_error=str(error),
    )

    return create_error_response(message, "DATABASE_ERROR", tool_name, suggestions)


def handle_parameter_validation_error(
    error: ParameterValidationError, tool_name: str
) -> dict[str, Any]:
    """
    Handle parameter validation errors.

    Args:
        error: The parameter validation error
        tool_name: Name of the tool that encountered the error

    Returns:
        Standardized error response
    """
    logger.warning(
        "Parameter validation error handled",
        tool=tool_name,
        error_message=str(error),
        suggestions_count=len(error.suggestions),
    )

    return create_error_response(
        str(error),
        "PARAMETER_ERROR",
        tool_name,
        error.suggestions if error.suggestions else None,
    )


def handle_resource_exhaustion_error(
    error: Exception, tool_name: str
) -> dict[str, Any]:
    """
    Handle resource exhaustion errors (memory, disk, etc.).

    Args:
        error: The resource exhaustion error
        tool_name: Name of the tool that encountered the error

    Returns:
        Standardized error response
    """
    error_str = str(error).lower()

    if "memory" in error_str or isinstance(error, MemoryError):
        if "too large" in error_str:
            message = "Input data is too large to process."
            suggestions = [
                "Reduce the size of your input",
                "Split the operation into smaller parts",
            ]
        else:
            message = "Operation requires too much memory."
            suggestions = [
                "Try with smaller data sets",
                "Contact support if the issue persists",
            ]
    else:
        message = "System resource limit exceeded."
        suggestions = ["Try again later", "Reduce the complexity of your request"]

    logger.warning(
        "Resource exhaustion error handled",
        tool=tool_name,
        error_type=type(error).__name__,
        original_error=str(error),
    )

    return create_error_response(message, "RESOURCE_ERROR", tool_name, suggestions)


def handle_generic_error(error: Exception, tool_name: str) -> dict[str, Any]:
    """
    Handle generic/unexpected errors.

    Args:
        error: The unexpected error that occurred
        tool_name: Name of the tool that encountered the error

    Returns:
        Standardized error response
    """
    # Sanitize error message for user consumption
    error_str = str(error)
    if not error_str:
        message = "An unexpected error occurred."
    else:
        # Convert to user-friendly message
        message = f"An unexpected error occurred: {error_str}"

    logger.error(
        "Unexpected error handled",
        tool=tool_name,
        error_type=type(error).__name__,
        original_error=str(error),
    )

    return create_error_response(
        message,
        "INTERNAL_ERROR",
        tool_name,
        ["Try the operation again", "Contact support if the problem persists"],
    )


def safe_tool_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for comprehensive error handling across all MCP tools.

    This decorator catches all exceptions and converts them to standardized
    error responses while maintaining proper logging.

    Args:
        func: The MCP tool function to wrap

    Returns:
        Wrapped function with comprehensive error handling
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__

        try:
            result = func(*args, **kwargs)
            return result

        except ParameterValidationError as e:
            return handle_parameter_validation_error(e, tool_name)

        except sqlite3.Error as e:
            return handle_database_error(e, tool_name)

        except (MemoryError, OSError) as e:
            return handle_resource_exhaustion_error(e, tool_name)

        except Exception as e:
            return handle_generic_error(e, tool_name)

    return wrapper
