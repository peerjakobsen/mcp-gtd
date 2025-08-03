# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for Getting Things Done (GTD) task management. The project provides AI assistant integration for GTD workflows through MCP-compatible clients like Claude Desktop and Cursor.

## Key Architecture

- **FastMCP Framework**: Built on FastMCP for MCP protocol implementation
- **Package Structure**: Standard Python package in `src/gtd_manager/` following hatchling build system
- **MCP Tools**: Server exposes GTD tools through MCP protocol for AI assistant consumption
- **Structured Logging**: Uses structlog with stderr output (critical for MCP protocol compliance)
- **Entry Point**: Main server runs through `gtd-manager` console script

## Development Commands

### Environment Setup
```bash
# Install dependencies (development mode)
uv sync

# Install with development dependencies
uv sync --group dev
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage reports
uv run pytest --cov=gtd_manager

# Run specific test file
uv run pytest tests/test_package_structure.py
```

### Code Quality
```bash
# Format and lint with ruff
uv run ruff format .
uv run ruff check .

# Type checking with mypy
uv run mypy src/
```

### Running the Server
```bash
# Run MCP server locally
uv run gtd-manager

# Or via Python module
uv run python -m gtd_manager.server
```

## Critical MCP Protocol Requirements

**NEVER write to stdout** - MCP uses stdout for JSON-RPC communication. All logging must go to stderr or the protocol will break. The codebase correctly configures logging to stderr only.

## Package Distribution

- **Entry Point**: `gtd-manager` console script points to `gtd_manager.server:main`
- **Distribution**: Designed for uvx installation from git repository
- **Dependencies**: Minimal runtime dependencies (fastmcp, structlog)
- **Python Version**: Requires Python 3.13+

## Testing Strategy

- **Package Structure Tests**: Verify import paths and module organization
- **Coverage**: Configured to report on `src/` directory with branch coverage
- **Test Markers**: `integration`, `unit`, `slow` markers available
- **Strict Configuration**: Tests run with strict markers and config validation

## Code Standards

- **Line Length**: 88 characters (Black default)
- **Target Python**: 3.13+
- **Type Hints**: Required for all functions (enforced by mypy)
- **Import Style**: `gtd_manager` as known first-party package
- **Docstrings**: Google-style docstrings for all public functions

## Current Implementation Status

The codebase is in early development with:
- ✅ Basic FastMCP server setup
- ✅ Package structure and build configuration
- ✅ MCP protocol compliance (stderr logging)
- ✅ Hello world tool for connectivity testing
- ⚠️ GTD business logic not yet implemented (referenced in README but not in code)

When implementing GTD features, follow the MCP server patterns established in `server.py` and maintain strict MCP protocol compliance.