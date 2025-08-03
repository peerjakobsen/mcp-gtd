# Project Architecture

## Current Structure

```
mcp-gtd/
├── src/gtd_manager/
│   ├── __init__.py          # Package initialization and version
│   └── server.py            # FastMCP server setup and main entry point
├── tests/
│   ├── __init__.py
│   └── test_package_structure.py  # Package import and structure tests
├── .agent-os/               # Agent OS product documentation
│   ├── product/            # Product mission, roadmap, decisions
│   └── specs/             # Feature specifications
├── pyproject.toml          # Build system and tool configuration
├── .pre-commit-config.yaml # Code quality automation
├── README.md               # Project documentation
├── CLAUDE.md              # AI assistant guidance
└── LICENSE                # CC BY-NC 4.0 license
```

## Planned Architecture (from README)

```
gtd-manager-mcp/
├── src/gtd_manager/
│   ├── server.py          # FastMCP server setup
│   ├── domain/            # GTD domain models
│   ├── services/          # Business logic
│   ├── repositories/      # Data access
│   └── sops/             # SOP processing
├── tests/                # Test suite
├── migrations/           # Database migrations
├── examples/            # Example SOPs
└── docs/               # Documentation
```

## Key Components

### FastMCP Server (`server.py`)

- Main entry point for MCP protocol
- Configured with structured logging to stderr
- Currently implements hello_world tool for testing
- Proper MCP protocol compliance

### Package Configuration (`pyproject.toml`)

- Hatchling build backend
- Console script entry point: `gtd-manager`
- Comprehensive tool configuration (ruff, mypy, pytest)
- Development dependencies clearly separated

### Testing Framework

- pytest with coverage reporting
- Package structure validation tests
- Configured for strict test execution
- Coverage reports in multiple formats

### Code Quality Pipeline

- Pre-commit hooks for automated quality checks
- Ruff for formatting and linting
- MyPy for static type checking
- Bandit for security scanning
- Multiple file format validation

## Design Patterns

### MCP Protocol Compliance

- All logging directed to stderr
- JSON-RPC communication over stdout
- Tool functions return structured data
- Proper error handling for MCP clients

### Structured Logging

- JSON-formatted logs for better parsing
- Contextual information in log entries
- ISO timestamp formatting
- Logger factory pattern with caching

### Package Organization

- Standard src layout for clean imports
- Clear separation of concerns (planned)
- Domain-driven design approach (planned)
- Repository pattern for data access (planned)
