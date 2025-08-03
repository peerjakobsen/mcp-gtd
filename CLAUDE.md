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
- ✅ Parameter preprocessing decorators for MCP client compatibility
- ✅ Standardized error response format
- ✅ Comprehensive stdout cleanliness testing
- ⚠️ GTD business logic not yet implemented (referenced in README but not in code)

## Development Lessons Learned

**Critical guidance to avoid repeating common mistakes encountered during development.**

### TDD Discipline

- **Always write tests first** when implementing new features or functionality
- Follow strict red-green-refactor cycle: write failing test → implement code → refactor
- If user mentions TDD or asks about tests, write tests before implementation
- Don't implement features before seeing tests fail - this prevents proper TDD workflow

### FastMCP Testing Best Practices

- **Use `Client(server)` pattern** for in-memory testing of FastMCP servers
- Never try to access FastMCP server internals directly (avoid `server.list_tools()`, `server.get_tools()`)
- All MCP tool testing should go through proper FastMCP Client API
- Example correct pattern:

  ```python
  async with Client(server) as client:
      result = await client.call_tool("tool_name", {"param": "value"})
  ```

### External Library Integration

- **Consult Context7 documentation** before making assumptions about API usage
- When working with FastMCP, research proper patterns rather than guessing
- If struggling with library usage, explicitly research correct patterns using available documentation tools
- "Think hard" and look up authoritative examples before implementing

### Python Development Environment

- **Use `PYTHONPATH=src`** during development testing to handle package imports
- Understanding package import structure is critical for both development and production
- Handle async testing properly with `asyncio.run()` and `async with` patterns
- MCP servers are async by nature - all testing must follow async patterns

### MCP Protocol Critical Compliance Rules

- **Stdout contamination breaks MCP** - JSON-RPC communication relies on clean stdout
- All logging must go to stderr only (already configured with structlog)
- Always verify stdout cleanliness in protocol compliance tests
- Never use print() statements in MCP server code
- Test stdout cleanliness rigorously with captured stdout/stderr in tests

### Testing Development Flow

- Run tests with: `PYTHONPATH=src uv run pytest tests/ -v`
- Focus on protocol compliance tests for MCP servers
- Maintain high test coverage but prioritize critical MCP compliance tests
- Use proper FastMCP testing patterns to avoid false negatives

When implementing GTD features, follow the MCP server patterns established in `server.py` and maintain strict MCP protocol compliance.

### GitHub Actions & Release Workflow

- **CI runs on ALL branches** - test locally first with `act -j quality` or `act -j test`
- **Conventional commits for auto-versioning**: `fix:` → patch, `feat:` → minor, `BREAKING CHANGE:` → major
- **Two-stage releases**: Main merge → version bump + tag | Manual tag push → PyPI publish
- **Never manually edit version** in pyproject.toml (managed by semantic-release)
- **PyPI publishing**: `git push origin v1.2.0` or `gh release create v1.2.0`
