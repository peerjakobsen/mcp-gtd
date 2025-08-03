"""
Decorators for MCP tool functions.

This module provides decorators that handle common MCP server requirements
like parameter preprocessing and error handling.
"""

import inspect
import json
from collections.abc import Callable
from functools import wraps
from typing import Any, get_origin

import structlog

logger = structlog.get_logger(__name__)


def preprocess_params(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Handle MCP parameter serialization issues.

    MCP clients sometimes send parameters as JSON strings instead of Python objects.
    This decorator automatically detects and deserializes JSON string parameters
    based on the function's type annotations.

    Example:
        - Client sends: '["item1", "item2"]' (JSON string)
        - Function expects: ["item1", "item2"] (Python list)
        - Decorator converts automatically

    Args:
        func: The function to wrap with parameter preprocessing

    Returns:
        Wrapped function that handles JSON string deserialization
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(func)
        processed_kwargs = {}

        for param_name, param_value in kwargs.items():
            if param_name in sig.parameters:
                param_type = sig.parameters[param_name].annotation

                # Handle JSON string deserialization for common types
                if isinstance(param_value, str) and param_value.startswith(("[", "{")):
                    try:
                        # Check if the expected type is a collection that could be JSON
                        if get_origin(param_type) in (list, dict, tuple):
                            deserialized = json.loads(param_value)
                            logger.debug(
                                "Deserialized JSON parameter",
                                param_name=param_name,
                                original_type=type(param_value).__name__,
                                new_type=type(deserialized).__name__,
                                tool=func.__name__,
                            )
                            param_value = deserialized
                    except json.JSONDecodeError:
                        # If JSON parsing fails, use original value
                        logger.debug(
                            "Failed to deserialize parameter as JSON, using original",
                            param_name=param_name,
                            param_value_preview=param_value[:100],
                            tool=func.__name__,
                        )

                processed_kwargs[param_name] = param_value
            else:
                processed_kwargs[param_name] = param_value

        return func(*args, **processed_kwargs)

    return wrapper


def mcp_tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Comprehensive decorator for MCP tools.

    Combines parameter preprocessing with basic error handling and logging.
    This is the recommended decorator for MCP tool functions.

    Args:
        func: The MCP tool function to wrap

    Returns:
        Wrapped function with full MCP tool support
    """
    # Apply parameter preprocessing first
    preprocessed_func = preprocess_params(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__

        try:
            logger.info(
                "MCP tool called",
                tool=tool_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            result = preprocessed_func(*args, **kwargs)

            logger.info(
                "MCP tool completed successfully",
                tool=tool_name,
                result_type=type(result).__name__,
            )

            return result

        except Exception as e:
            logger.error(
                "MCP tool execution failed",
                tool=tool_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Re-raise for now - comprehensive error handling will be added in task 2.4
            raise

    return wrapper
