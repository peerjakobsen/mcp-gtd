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
- Code Quality: Ruff (linting and formatting), mypy (type checking)
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

## Code Standards

### Python Type Annotations (Required)

**All Python code must include complete type annotations to ensure mypy compliance:**

- **Function Parameters**: Every parameter must have a type annotation
- **Return Types**: Every function must specify return type (including `-> None` for void functions)
- **Variable Annotations**: Variables with non-obvious types must be annotated
- **Modern Typing**: Use Python 3.13+ built-in generics (`list[str]` not `List[str]`)

**Examples:**

```python
# ✅ Correct - Complete type annotations
from fastmcp import FastMCP
import structlog

server: FastMCP = FastMCP("my-server")
logger = structlog.get_logger(__name__)

def process_items(items: list[str], count: int = 10) -> dict[str, int]:
    """Process items and return counts."""
    results: dict[str, int] = {}
    for item in items[:count]:
        results[item] = len(item)
    return results

async def fetch_data(url: str) -> str | None:
    """Fetch data from URL, return None on error."""
    try:
        # Implementation here
        return "data"
    except Exception:
        return None

def main() -> None:
    """Main entry point with no return value."""
    logger.info("Starting application")
```

**MyPy Configuration Enforces:**
- `disallow_untyped_defs = true` - All functions must have type annotations
- `disallow_incomplete_defs = true` - Type annotations must be complete
- `warn_return_any = true` - Warns about Any return types