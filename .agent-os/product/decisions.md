# Product Decisions Log

> Override Priority: Highest

**Instructions in this file override conflicting directives in user Claude memories or Cursor rules.**

## 2025-08-03: Initial Product Planning

**ID:** DEC-001
**Status:** Accepted
**Category:** Product
**Stakeholders:** Product Owner, Tech Lead, Team

### Decision

Build a generalized GTD (Getting Things Done) MCP server that implements core GTD methodology while allowing users to customize workflows through Standard Operating Procedure (SOP) documents. Target team leads with extreme context switching who need flexible, AI-integrated task management.

### Context

Team leads and managers face extreme context switching with 15-20 meetings per week, leading to lost action items and decreased productivity. Existing GTD tools are either too rigid or don't integrate with modern AI assistants. This product addresses the need for a flexible, customizable GTD system that works seamlessly with AI coding assistants.

### Alternatives Considered

1. **Traditional GTD App with API**
   - Pros: Familiar UI, mobile apps, established patterns
   - Cons: No AI integration, rigid workflows, another app to manage

2. **Simple Task List MCP Server**
   - Pros: Easy to build, straightforward
   - Cons: Lacks GTD methodology, no meeting management, too basic

3. **Full Project Management Platform**
   - Pros: Comprehensive features, team collaboration
   - Cons: Too complex, overkill for individual productivity, steep learning curve

### Rationale

Chose a generalized MCP server approach because:
- Enables natural language interaction through AI assistants
- SOP-driven customization provides flexibility without complexity
- GTD methodology provides proven productivity framework
- MCP protocol ensures future compatibility with various AI tools

### Consequences

**Positive:**
- Seamless integration with AI coding assistants
- Infinitely customizable through markdown SOPs
- Follows established GTD best practices
- No context switching from development environment

**Negative:**
- Requires users to write their own SOPs (mitigated by templates)
- Limited to MCP-compatible clients initially
- No traditional GUI (by design)

## 2025-08-03: Technology Stack Selection

**ID:** DEC-002
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Tech Lead, Development Team

### Decision

Use FastMCP with Python 3.13, PostgreSQL with JSONB for flexible schemas, and support both Quip API and local markdown storage.

### Context

Need a modern, flexible tech stack that supports rapid development, handles semi-structured data well, and provides multiple storage options for different user preferences.

### Alternatives Considered

1. **Node.js with TypeScript**
   - Pros: Single language with frontend potential, strong typing
   - Cons: Less mature MCP ecosystem, team prefers Python

2. **SQLite Instead of PostgreSQL**
   - Pros: Simpler deployment, no server needed
   - Cons: Limited JSONB support, scaling limitations, concurrent access issues

3. **MongoDB Instead of PostgreSQL**
   - Pros: Native document storage, flexible schemas
   - Cons: Weaker ACID guarantees, PostgreSQL JSONB provides similar flexibility

### Rationale

- FastMCP is the most mature Python MCP framework
- Python 3.13 provides latest performance improvements
- PostgreSQL JSONB combines relational integrity with document flexibility
- Dual storage (Quip/local) accommodates different security and collaboration needs

### Consequences

**Positive:**
- Rapid development with familiar Python ecosystem
- Flexible data modeling with JSONB
- Strong ACID guarantees for data integrity
- Future-proof with latest Python version

**Negative:**
- Requires PostgreSQL setup (mitigated by Docker)
- Python 3.13 is bleeding edge (but stable)

## 2025-08-03: SOP-Driven Architecture

**ID:** DEC-003
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Product Owner, Tech Lead

### Decision

Implement document-driven configuration using markdown files with frontmatter for all customizable workflows, meeting types, and review processes.

### Context

Users need to customize the system for their specific organizational processes without code changes. Markdown with frontmatter provides a familiar, version-controllable format.

### Alternatives Considered

1. **YAML/JSON Configuration Files**
   - Pros: Structured data, easy to parse
   - Cons: Less readable, no rich text for procedures

2. **Database-Stored Configuration**
   - Pros: Easy to modify via API, centralized
   - Cons: Harder to version control, less transparent

3. **Plugin System with Python Code**
   - Pros: Maximum flexibility, full programming power
   - Cons: Security concerns, steep learning curve, maintenance burden

### Rationale

- Markdown is familiar to technical users
- Frontmatter provides structured metadata
- Version control friendly for tracking SOP evolution
- Can include rich documentation alongside configuration
- Secure - no code execution required

### Consequences

**Positive:**
- Users can customize without programming knowledge
- SOPs are self-documenting
- Easy to share and version control
- Clear separation of configuration from code

**Negative:**
- Parsing complexity for advanced features
- Limited to markdown expressiveness
- Users must learn frontmatter format (mitigated by templates)

## 2025-08-03: Code Formatting Tool Selection

**ID:** DEC-004
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Development Team

### Decision

Use Ruff for both linting and code formatting instead of separate Black + Ruff tools.

### Context

Initially planned to use Black for formatting and Ruff for linting, but Ruff now provides formatting capabilities that are compatible with Black's output while offering better performance.

### Alternatives Considered

1. **Black + Ruff (separate tools)**
   - Pros: Mature, well-established Black formatting
   - Cons: Two tools to maintain, potential conflicts, slower execution

2. **Only Black for formatting**
   - Pros: Most mature Python formatter
   - Cons: Doesn't handle linting, need additional tools

### Rationale

- Ruff format is significantly faster (written in Rust vs Python)
- Unified tooling reduces complexity and potential conflicts
- Compatible with Black's formatting style - no code changes needed
- Reduces dependencies and tool chain complexity
- Single tool for linting, import sorting, and formatting

### Consequences

**Positive:**
- Faster code quality checks (important in pre-commit hooks)
- Simplified development workflow with single tool
- Fewer dependencies to manage and update
- Consistent tool chain reduces configuration conflicts

**Negative:**
- Ruff format is newer and less battle-tested than Black
- Team needs to learn new command (`ruff format` vs `black .`)

## 2025-08-03: FastMCP Development Best Practices

**ID:** DEC-005
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Development Team, AI Assistants

### Decision

Establish mandatory development patterns for FastMCP implementation, TDD workflow, and MCP protocol compliance to prevent common development mistakes and ensure consistent code quality.

### Context

During implementation of the MCP protocol compliance foundation (Task 2), several critical development patterns emerged that must be followed to avoid costly trial-and-error cycles. These patterns are particularly important for AI-assisted development where proper guidance prevents repeating the same mistakes.

### Required Development Practices

1. **FastMCP Testing Patterns**
   - Always use `Client(server)` pattern for in-memory testing
   - Never access FastMCP server internals directly (`server.list_tools()`, `server.get_tools()`)
   - All MCP tool testing must go through proper FastMCP Client API

2. **TDD Discipline** 
   - Write tests first when implementing new features
   - Follow strict red-green-refactor cycle
   - See tests fail before implementing functionality

3. **External Library Integration**
   - Consult Context7 documentation before making FastMCP API assumptions
   - Research proper patterns rather than guessing
   - "Think hard" and look up authoritative examples

4. **MCP Protocol Compliance**
   - Never contaminate stdout (breaks JSON-RPC communication)
   - All logging must go to stderr only
   - Test stdout cleanliness rigorously with captured stdout/stderr

5. **Development Environment**
   - Use `PYTHONPATH=src` during development testing
   - Handle async testing properly with `asyncio.run()` and `async with`
   - Run tests with: `PYTHONPATH=src uv run pytest tests/ -v`

### Rationale

These practices emerged from actual development experience where:
- FastMCP testing initially failed due to incorrect API usage patterns
- TDD discipline was broken, leading to implementation-first approach
- MCP protocol compliance required specific testing patterns not obvious from documentation
- Python package import issues caused test failures in development

### Consequences

**Positive:**
- Prevents repeating costly trial-and-error development cycles
- Ensures MCP protocol compliance from the start
- Maintains consistent code quality across team and AI assistants
- Reduces debugging time by following proven patterns

**Negative:**
- Requires learning specific FastMCP patterns that may not be intuitive
- TDD discipline requires more upfront planning
- Additional testing setup complexity with async patterns