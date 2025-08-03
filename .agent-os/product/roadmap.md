# Product Roadmap

## Phase 0: Foundation Setup (Partially Complete)

**Goal:** Establish core infrastructure and development environment
**Success Criteria:** Basic MCP server running with database connectivity

### Features

- [x] **Project setup with FastMCP and Python 3.13** - Repository structure, package setup, development tooling `COMPLETED`
- [x] **Database foundation** - SQLite with smart path detection and connection management `COMPLETED` 
- [x] **Basic MCP server skeleton** - Hello world MCP tool working with protocol compliance `COMPLETED`
- [ ] **Core domain models** - GTDItem, Action, Project entities `M`
- [ ] **Database schema setup** - Create tables for GTD entities `S`

### Completed Infrastructure

- ✅ Python 3.13+ with uv package management
- ✅ FastMCP framework integration with tool registry
- ✅ SQLite database with connection management
- ✅ Comprehensive test suite (123 tests, 86% coverage)
- ✅ Code quality tools (ruff, mypy, pytest-cov)
- ✅ MCP protocol compliance verified
- ✅ Smart database path detection (uvx, development, system installs)

### Dependencies

- ✅ Python 3.13 environment
- ✅ FastMCP framework understanding
- SQLite replaces PostgreSQL/Docker for better MCP distribution

## Phase 1: Minimum Lovable Product (Capture & Clarify)

**Goal:** Basic GTD capture and clarification workflow
**Success Criteria:** Can capture items and process them through basic GTD flow

### Features

- [ ] Universal capture tool - Add any item to inbox via MCP `M`
- [ ] Inbox listing resource - View all inbox items `S`
- [ ] Clarify item tool - Process inbox items into actions/projects `M`
- [ ] Next actions list - View actionable items `S`
- [ ] Basic contexts support - @computer, @phone, @meeting tags `S`
- [ ] Local markdown storage - Alternative to database storage `M`

### Dependencies

- Phase 0 completed
- Basic GTD workflow understanding

## Phase 2: Meeting Management & SOPs

**Goal:** Enable SOP-driven meeting workflows
**Success Criteria:** Can create meetings with custom SOPs and extract actions

### Features

- [ ] SOP markdown parser - Process frontmatter and checklists `L`
- [ ] Create meeting tool - Schedule meetings with SOP association `M`
- [ ] Meeting notes capture - Store and process meeting notes `M`
- [ ] Action extraction - Identify action items from notes `L`
- [ ] Basic SOP templates - Provide starter templates for common meetings `M`
- [ ] Meeting review resource - List meetings and their outcomes `S`

### Dependencies

- Markdown processing library
- Example SOP documents

## Phase 3: Reviews & Productivity Features

**Goal:** Complete GTD review cycles and productivity enhancements
**Success Criteria:** Daily and weekly reviews functioning smoothly

### Features

- [ ] Daily review prompt - Guided morning planning `M`
- [ ] Weekly review workflow - Comprehensive GTD weekly review `L`
- [ ] Project tracking - Multi-step outcome management `M`
- [ ] Waiting-for list - Track delegated items `S`
- [ ] Quick filters - Context and energy-based filtering `M`
- [ ] Basic reporting - Review summaries and statistics `M`

### Dependencies

- Stable capture and organize workflow
- User feedback from Phase 2

## Phase 4: External Integrations

**Goal:** Connect with external systems
**Success Criteria:** Seamless integration with Quip and other tools

### Features

- [ ] Quip API integration - Read/write documents `L`
- [ ] Storage abstraction layer - Switch between local/Quip storage `M`
- [ ] Email to inbox - Process emails as GTD items `L`
- [ ] Calendar integration - Sync meetings with calendar `L`
- [ ] Stakeholder management - Track people and relationships `M`

### Dependencies

- Quip API key and documentation
- Stable core system

## Phase 5: Advanced Features & Polish

**Goal:** Enterprise-ready features and polish
**Success Criteria:** Production-ready system with advanced capabilities

### Features

- [ ] Multi-user support - Team shared contexts `XL`
- [ ] Advanced SOPs - Conditional logic and variables `L`
- [ ] OAuth authentication - Secure multi-user access `L`
- [ ] Performance optimization - Caching and query optimization `M`
- [ ] Comprehensive documentation - User and developer guides `L`
- [ ] Mobile-friendly web UI - Optional web interface `XL`

### Dependencies

- User feedback from earlier phases
- Performance benchmarks
