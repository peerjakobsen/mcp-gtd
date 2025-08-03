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