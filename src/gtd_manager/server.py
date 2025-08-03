"""
GTD Manager MCP Server

Main entry point for the FastMCP server providing Getting Things Done tools.

Copyright (c) 2025 GTD Manager Team
Licensed under CC BY-NC 4.0 (Non-Commercial Use Only)
"""

import logging
import sys

import structlog
from fastmcp import FastMCP

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

# Initialize FastMCP server
server: FastMCP = FastMCP("gtd-manager")


@server.tool()  # type: ignore[misc]
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


def main() -> None:
    """
    Main entry point for the GTD Manager MCP Server.

    This function initializes and runs the FastMCP server with proper
    MCP protocol compliance.
    """
    try:
        logger.info("Starting GTD Manager MCP Server", version="0.1.0")
        server.run()
    except Exception as e:
        logger.error("Failed to start GTD Manager MCP Server", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
