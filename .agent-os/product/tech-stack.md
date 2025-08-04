# Technical Stack

## Context

Technical stack for GTD Manager MCP Server - a Getting Things Done implementation for team leads.

- MCP Framework: FastMCP latest
- Language: Python 3.13+
- Primary Database: SQLite with smart path detection
- Database Features: Foreign keys, indexes, constraints, migration system
- Data Access Pattern: Custom Repository Pattern (not ORM)
- Domain Architecture: Domain-Driven Design with rich models
- API Integration: Quip API (planned Phase 4)
- Storage Strategy: Database-first with optional document export
- Testing Framework: pytest with pytest-asyncio
- Code Quality: Ruff (linting and formatting), mypy (type checking)
- MCP Protocol Version: Model Context Protocol (MCP) 1.0+
- MCP Client Support: Claude Desktop, Cursor, other MCP-compatible clients
- Distribution: uvx (uv execute) for easy installation
- Database Path: Smart detection (uvx/development/system installs)
- Development Environment: macOS primary, Linux compatible
- Python Package Management: uv (modern Python package manager)
- Virtual Environment: uv venv
- Dependency Management: pyproject.toml with uv
- Configuration Management: Environment variables with .env files
- Domain Validation: Custom validation in domain models and repositories
- Date/Time Handling: Python datetime with timezone awareness
- Markdown Processing: Python-Markdown with frontmatter extension
- RACI System: Comprehensive stakeholder relationship management
- Monitoring: structlog for structured logging
- Error Tracking: Sentry (optional, production)
- Documentation: MkDocs with Material theme
- API Documentation: Automatically generated from FastMCP
- Security: OAuth 2.1 ready (phase 4)
- Deployment: uvx for easy distribution
- Energy Management: 1-5 scale task energy levels for productivity optimization
- Context System: GTD contexts (@computer, @phone, @meeting) with many-to-many relationships

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

## Architectural Patterns

### Repository Pattern

**Purpose**: Encapsulates data access logic and provides uniform interface for domain objects.

**Implementation**:
```python
# Abstract base repository
class BaseRepository(ABC, Generic[T]):
    def create(self, entity: T) -> T: ...
    def read(self, entity_id: str) -> T: ...
    def update(self, entity: T) -> T: ...
    def delete(self, entity_id: str) -> None: ...
    def list_all(self) -> list[T]: ...

    # Template method hooks
    def validate_before_save(self, entity: T) -> None: ...
    def validate_business_rules(self, entity: T) -> None: ...

# Concrete repositories
class GTDItemRepository(BaseRepository[GTDItem]): ...
class ContextRepository(BaseRepository[Context]): ...
class StakeholderRepository(BaseRepository[Stakeholder]): ...
```

**Benefits**:
- Simplified MCP tool implementation (just call repository methods)
- Centralized business logic and validation
- Database-agnostic domain layer
- Easy testing with mock repositories

### Domain-Driven Design (DDD)

**Rich Domain Models**: Entities contain behavior, not just data.

```python
@dataclass
class GTDItem:
    def get_owner(self) -> Stakeholder:
        """Business logic embedded in domain model"""
        return self._find_stakeholder_by_role(RACIRole.ACCOUNTABLE)

    def add_context(self, context: Context) -> None:
        """Domain behavior for context management"""
        if context not in self.contexts:
            self.contexts.append(context)
```

**Business Rules Enforcement**:
- "Exactly one ACCOUNTABLE per GTD item" - enforced in domain model
- GTD workflow state transitions validated
- Energy level constraints (1-5 scale) validated
- RACI relationship constraints enforced

### Decorator Pattern

**Parameter Preprocessing**:
```python
@preprocess_params
def create_action(title: str, contexts: list[str]) -> dict:
    # Handles MCP client serialization: '["@computer"]' → ["@computer"]
```

**Error Handling**:
```python
@safe_tool_execution
def risky_operation() -> dict:
    # Catches all exceptions, returns standardized MCP responses
```

**Tool Registration**:
```python
@register_tool
def gtd_capture_item(title: str) -> dict:
    # Automatically registers with FastMCP server
```

### Template Method Pattern

**BaseRepository Structure**:
```python
def create(self, entity: T) -> T:
    self.validate_before_save(entity)    # Hook for subclasses
    self.validate_business_rules(entity) # Hook for subclasses
    # ... perform database operations ...
    return entity
```

**Subclass Implementation**:
```python
class GTDItemRepository(BaseRepository[GTDItem]):
    def validate_business_rules(self, entity: GTDItem) -> None:
        if entity.status == GTDStatus.COMPLETE:
            # Ensure completion timestamp is set
            if entity.completed_at is None:
                entity.completed_at = datetime.now(UTC)
```

### Registry Pattern

**Global Tool Registry**:
```python
_tool_registry: list[Callable] = []

@register_tool
def my_mcp_tool():
    pass  # Automatically added to registry

# Bulk registration with FastMCP
for tool in _tool_registry:
    server.tool(tool)
```

**RACI Relationship Registry**:
```python
_raci_relationships: list[GTDItemStakeholder] = []

# Enforces business rule: exactly one ACCOUNTABLE per item
def __post_init__(self):
    if self.raci_role == RACIRole.ACCOUNTABLE:
        # Check registry for existing ACCOUNTABLE relationships
```

### Strategy Pattern

**Database Path Detection**:
```python
def get_database_path() -> Path:
    # Strategy 1: Environment variable override
    if db_path := os.getenv("MCP_GTD_DB_PATH"):
        return Path(db_path)

    # Strategy 2: uvx/cache environment detection
    if ".cache" in str(Path(__file__)):
        return Path.home() / ".local/share/mcp-gtd/data.db"

    # Strategy 3: Development mode
    return Path("./data.db")
```

**Error Handling Strategies**:
```python
def safe_tool_execution(func):
    try:
        return func(*args, **kwargs)
    except ParameterValidationError as e:
        return handle_parameter_validation_error(e)
    except sqlite3.Error as e:
        return handle_database_error(e)
    except MemoryError as e:
        return handle_resource_exhaustion_error(e)
```

### Factory Pattern

**Test Data Factory**:
```python
class GTDTestDataFactory:
    def create_team_lead_organization_structure(self) -> dict:
        # Creates realistic org hierarchy with stakeholders

    def create_weekly_meeting_outcomes(self) -> list[Action]:
        # Generates 20 realistic action items from meetings
```

**Connection Factory**:
```python
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(get_database_path())
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    yield conn
```

## Implementation Standards

### Data Access Layer
- **Always use Repository Pattern** - Never direct database access in MCP tools
- **Business Logic in Repositories** - Validation, constraints, complex queries
- **Domain Models are Rich** - Behavior methods, not just data containers
- **Template Method for Extension** - Override validation hooks in repository subclasses

### MCP Tool Development
- **Use Decorators Consistently**:
  - `@register_tool` for all MCP tools
  - `@preprocess_params` for parameter handling
  - `@safe_tool_execution` for error handling
- **Repository-Based Implementation** - Tools call repository methods
- **Standardized Error Responses** - Use error handling decorators

### Business Rule Enforcement
- **Domain Model Validation** - Rules enforced in `__post_init__()` methods
- **Repository Validation** - Complex rules in `validate_business_rules()`
- **Registry Pattern for Constraints** - Global state tracking for business rules
- **Clear Error Messages** - User-friendly error responses

### Testing Architecture
- **Integration Tests with Real Repositories** - Test complete workflows
- **Factory Pattern for Test Data** - Realistic scenarios with GTDTestDataFactory
- **Repository Mocking for Unit Tests** - Isolate business logic testing
- **Comprehensive Scenario Coverage** - Team lead workflows, RACI assignments, energy optimization

### Extension Guidelines

**Adding New Domain Entity**:
1. Create domain model with business methods
2. Implement concrete repository extending BaseRepository
3. Add validation hooks for entity-specific rules
4. Create MCP tools using decorator pattern
5. Add integration tests with factory pattern

**Adding New MCP Tool**:
1. Use `@register_tool` decorator
2. Add `@preprocess_params` for parameter handling
3. Add `@safe_tool_execution` for error handling
4. Call repository methods, not direct database access
5. Return standardized response format
