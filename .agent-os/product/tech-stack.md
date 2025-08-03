# Technical Stack

## Context

Technical stack for GTD Manager MCP Server - a Getting Things Done implementation for team leads.

- MCP Framework: FastMCP latest
- Language: Python 3.13+
- Primary Database: PostgreSQL 17+
- Database Features: JSONB for flexible schemas
- Cache Layer: Redis 7+
- Event Store: EventStore (optional, phase 3+)
- ORM: SQLAlchemy 2.0+
- Async Framework: asyncio with FastMCP
- API Integration: Quip API (optional storage backend)
- Local Storage: Markdown files with frontmatter
- Testing Framework: pytest with pytest-asyncio
- Code Quality: Black, Ruff, mypy
- MCP Protocol Version: Model Context Protocol (MCP) 1.0+
- MCP Client Support: Claude Desktop, Cursor, other MCP-compatible clients
- Container Platform: Docker
- Container Orchestration: Docker Compose (development)
- Development Environment: macOS primary, Linux compatible
- Python Package Management: uv (modern Python package manager)
- Virtual Environment: uv venv
- Dependency Management: pyproject.toml with uv
- Configuration Management: Environment variables with .env files
- Schema Validation: Pydantic v2
- Date/Time Handling: Python datetime with timezone awareness
- Markdown Processing: Python-Markdown with frontmatter extension
- Task Queue: Celery (optional, phase 3+)
- Monitoring: structlog for structured logging
- Error Tracking: Sentry (optional, production)
- Documentation: MkDocs with Material theme
- API Documentation: Automatically generated from FastMCP
- Security: OAuth 2.1 ready (phase 4)
- Deployment: uvx for easy distribution
- CLI Framework: Click (for management commands)