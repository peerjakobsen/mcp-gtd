"""
GTD Manager MCP Server

Main entry point for the FastMCP server providing Getting Things Done tools.

Copyright (c) 2025 GTD Manager Team
Licensed under CC BY-NC 4.0 (Non-Commercial Use Only)
"""

import logging
import sys
from collections.abc import Callable
from typing import Any, overload

import structlog
from fastmcp import FastMCP

from .decorators import preprocess_params
from .errors import safe_tool_execution

# Configure structured logging to stderr only (critical for MCP protocol)
logging.basicConfig(
    stream=sys.stderr, level=logging.INFO, format="%(message)s", force=True
)

# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global registry for tools before server is available
_tool_registry: list[Callable[..., Any]] = []

# Initialize FastMCP server
server: FastMCP = FastMCP("gtd-manager")


@overload
def register_tool(
    func: Callable[..., Any], *, enable_preprocessing: bool = True
) -> Callable[..., Any]: ...


@overload
def register_tool(
    func: None = None, *, enable_preprocessing: bool = True
) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...


def register_tool(
    func: Callable[..., Any] | None = None, *, enable_preprocessing: bool = True
) -> Callable[..., Any] | Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to register MCP tools with centralized registry and preprocessing.

    This decorator combines parameter preprocessing, error handling, and tool registration
    into a single, easy-to-use decorator for MCP tool functions.

    Args:
        func: The function to register as an MCP tool
        enable_preprocessing: Whether to enable parameter preprocessing (default: True)

    Returns:
        Wrapped function with full MCP tool support and registry registration
    """

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        # Apply preprocessing if enabled
        processed_func = preprocess_params(f) if enable_preprocessing else f

        # Apply error handling
        safe_func = safe_tool_execution(processed_func)

        # Add to global registry
        _tool_registry.append(safe_func)

        logger.info(
            "Tool registered", tool_name=f.__name__, preprocessing=enable_preprocessing
        )

        return safe_func

    # Handle both @register_tool and @register_tool() syntax
    return decorator if func is None else decorator(func)


def setup_tool_registration(fastmcp_server: FastMCP) -> None:
    """
    Register all decorated tools with the FastMCP server.

    This function takes all tools in the global registry and registers them
    with the provided FastMCP server instance.

    Args:
        fastmcp_server: The FastMCP server instance to register tools with
    """
    for tool_func in _tool_registry:
        try:
            fastmcp_server.tool(tool_func)
            logger.info("Tool registered with FastMCP", tool_name=tool_func.__name__)
        except Exception as e:
            logger.error(
                "Failed to register tool with FastMCP",
                tool_name=tool_func.__name__,
                error=str(e),
                error_type=type(e).__name__,
            )


@register_tool
def hello_world(name: str = "World") -> str:
    """
    A simple hello world tool for testing MCP connectivity.

    Args:
        name: Name to greet (default: "World")

    Returns:
        A greeting message
    """
    logger.info("Hello world tool called", name=name, tool="hello_world")
    return f"Hello, {name}! GTD Manager MCP Server is running."


# Set up tool registration on server initialization
setup_tool_registration(server)


def main() -> None:
    """
    Main entry point for the GTD Manager MCP Server.

    This function initializes and runs the FastMCP server with proper
    MCP protocol compliance and graceful shutdown handling.
    """
    try:
        logger.info(
            "Starting GTD Manager MCP Server",
            version="0.1.0",
            server_name="gtd-manager",
            description="Getting Things Done task management via MCP protocol",
        )
        server.run()
    except KeyboardInterrupt:
        logger.info(
            "GTD Manager MCP Server shutdown requested",
            reason="keyboard_interrupt",
            status="graceful_shutdown",
        )
        sys.exit(0)
    except Exception as e:
        logger.error(
            "Failed to start GTD Manager MCP Server",
            error=str(e),
            error_type=type(e).__name__,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
