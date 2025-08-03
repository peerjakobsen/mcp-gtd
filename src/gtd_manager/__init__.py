"""
GTD Manager MCP Server

A Model Context Protocol (MCP) server for Getting Things Done task management.
Provides tools for inbox capture, context management, and Notion integration.

Copyright (c) 2025 GTD Manager Team
Licensed under CC BY-NC 4.0 (Non-Commercial Use Only)
"""

__version__ = "0.1.0"
__author__ = "GTD Manager Team"
__email__ = "support@gtdmanager.dev"

# Package-level imports for convenience
from .server import main

__all__ = ["main", "__version__"]
