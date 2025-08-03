# Tech Stack

## Core Technologies
- **Python**: 3.13+ (latest version requirement)
- **MCP Framework**: FastMCP for Model Context Protocol implementation
- **Build System**: Hatchling (modern Python packaging)
- **Package Manager**: uv (modern Python dependency management)
- **Logging**: structlog with JSON formatting for structured logging

## Planned Dependencies
- **Database**: PostgreSQL 17+ with JSONB support
- **External APIs**: Quip API for document integration
- **Storage**: Hybrid approach (local markdown + Quip)

## Current Dependencies
```toml
dependencies = [
    "fastmcp>=0.1.0",
    "structlog>=23.1.0",
]

dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0", 
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.3.0",
]
```

## Package Structure
- **Standard src layout**: `src/gtd_manager/`
- **Entry point**: `gtd-manager` console script
- **Main module**: `gtd_manager.server:main`
- **Test directory**: `tests/` with pytest configuration

## MCP Protocol Requirements
- **Critical**: No stdout contamination (MCP uses stdout for JSON-RPC)
- **Logging**: All output to stderr only
- **Protocol**: JSON-RPC over stdio transport
- **Structured logging**: JSON format for better debugging