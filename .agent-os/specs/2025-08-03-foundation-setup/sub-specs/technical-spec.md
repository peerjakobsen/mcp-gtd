# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-03-foundation-setup/spec.md

## Technical Requirements

### Project Structure Requirements

- Reorganize existing code into proper Python package structure: `src/gtd_manager/`
- Create proper entry point in `src/gtd_manager/server.py` for FastMCP server initialization
- Move existing MCP server logic from root level files into the package structure
- Establish proper `__init__.py` files for package imports
- Configure `pyproject.toml` with proper entry points and dependencies

### FastMCP Integration Requirements

- Set up FastMCP server instance with proper configuration
- Implement server initialization with structured logging to stderr only
- Create centralized tool registration system using decorator pattern
- Establish proper error handling framework for all MCP tools
- Configure MCP protocol compliance (JSON-RPC over stdio transport)

### Development Environment Requirements

- Python 3.13+ environment with uv package management
- Configure `pyproject.toml` with all necessary dependencies (FastMCP, structlog, pytest, etc.)
- Set up proper development dependencies (ruff, mypy, pytest-cov)
- Create comprehensive test configuration with stdout cleanliness verification
- Establish database management with smart path detection for multiple environments

### MCP Protocol Compliance Requirements

- Configure all logging to stderr using structlog with JSON output
- Never allow any stdout contamination that would break MCP JSON-RPC communication
- Implement proper MCP server lifecycle management
- Create standardized error response formats for consistent client experience
- Test MCP protocol compliance with automated test suite

### Database Foundation Requirements

- Smart database path detection supporting uvx, local development, and system installations
- SQLite database initialization with proper schema constraints and indexes
- Database connection management with proper error handling and transactions
- Migration system foundation (not full implementation, just structure)
- Environment variable configuration with fallback to reasonable defaults

## External Dependencies

**Core Dependencies:**

- **FastMCP** - MCP server framework for Python
- **structlog** - Structured logging with stderr output
- **sqlite3** - Database backend (built into Python)

**Development Dependencies:**

- **pytest** - Testing framework with stdout cleanliness tests
- **pytest-cov** - Test coverage reporting
- **ruff** - Fast Python linter and formatter
- **mypy** - Static type checking

**Justification:** These dependencies follow the MCP best practices guidance and provide the minimal foundation needed for a robust MCP server without over-engineering the initial setup.
