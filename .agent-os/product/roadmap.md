# Product Roadmap

## Phase 0: Foundation Setup (COMPLETED ✅)

**Goal:** Establish core infrastructure and development environment
**Success Criteria:** ✅ Complete - MCP server with full domain model and database implementation

### Features

- [x] **Project setup with FastMCP and Python 3.13** - Repository structure, package setup, development tooling `COMPLETED`
- [x] **Database foundation** - SQLite with smart path detection and connection management `COMPLETED`
- [x] **Basic MCP server skeleton** - Hello world MCP tool working with protocol compliance `COMPLETED`
- [x] **Core domain models** - GTDItem, Action, Project entities with RACI stakeholder support `COMPLETED`
- [x] **Database schema setup** - Create tables for GTD entities with migration system `COMPLETED`

### Completed Infrastructure

- ✅ Python 3.13+ with uv package management
- ✅ FastMCP framework integration with tool registry
- ✅ SQLite database with connection management
- ✅ Comprehensive domain models (GTDItem, Action, Project, Context, Organization, Stakeholder)
- ✅ RACI stakeholder relationship system with business constraints
- ✅ Repository pattern for data access and business logic
- ✅ Database migration system for schema evolution
- ✅ Integration test suite with realistic GTD scenarios (1,105 lines)
- ✅ Unit test coverage for all domain models and repositories
- ✅ Code quality tools (ruff, mypy, pytest-cov)
- ✅ MCP protocol compliance verified
- ✅ Smart database path detection (uvx, development, system installs)
- ✅ Error handling system with user-friendly MCP responses
- ✅ Parameter preprocessing decorators for MCP client compatibility

### Dependencies

- ✅ Python 3.13 environment
- ✅ FastMCP framework understanding
- SQLite replaces PostgreSQL/Docker for better MCP distribution

## Phase 1: Minimum Lovable Product (Capture & Clarify)

**Goal:** Basic GTD capture and clarification workflow
**Success Criteria:** Can capture items and process them through basic GTD flow

### Features

- [ ] Universal capture tool - Add any item to inbox via MCP `M`
- [ ] Inbox listing resource - View all inbox items with filtering `S`
- [ ] Clarify item tool - Process inbox items into actions/projects (simplified by domain models) `M`
- [ ] Next actions list - View actionable items with context/energy filtering `S`
- [ ] Context MCP tools - Expose existing Context entities via MCP (@computer, @phone, @meeting) `S`
- [ ] RACI stakeholder assignment - Assign accountable/responsible/consulted/informed roles to actions `M`
- [ ] Energy level management - Set and filter tasks by energy requirements (1-5 scale) `S`

### Dependencies

- ✅ Phase 0 completed (domain models, repository pattern, RACI system)
- Basic GTD workflow understanding

### Implementation Notes

Phase 1 is significantly simplified by Phase 0 over-delivery:
- Repository pattern makes all CRUD operations straightforward
- Domain models handle state transitions and validation
- RACI stakeholder system enables advanced assignment capabilities
- Context and energy filtering already proven in integration tests

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
- [ ] Project tracking - Multi-step outcome management (simplified by existing Project entities) `S`
- [ ] Waiting-for list - Track delegated items `S`
- [ ] Quick filters - Context and energy-based filtering (simplified by repository layer) `S`
- [ ] Energy-based task optimization - Recommend tasks based on current energy level `M`
- [ ] RACI stakeholder reporting - Show accountability and workload distribution `M`
- [ ] Advanced reporting - Review summaries with stakeholder and energy analytics `M`

### Dependencies

- Stable capture and organize workflow (Phase 1)
- User feedback from Phase 2

### Implementation Notes

Phase 3 benefits significantly from Phase 0 advanced implementation:
- Project entities with action collections make project tracking straightforward
- Repository layer enables efficient filtering and querying
- RACI stakeholder system enables advanced reporting capabilities
- Energy level system (proven in integration tests) enables optimization features

## Phase 4: External Integrations

**Goal:** Connect with external systems
**Success Criteria:** Seamless integration with Quip and other tools

### Features

- [ ] Quip API integration - Read/write documents `L`
- [ ] Email to inbox - Process emails as GTD items `L`
- [ ] Calendar integration - Sync meetings with calendar `L`
- [ ] External stakeholder sync - Import/export stakeholder data from external systems `M`
- [ ] Document-based storage option - Alternative markdown/document storage for specific use cases `M`

### Dependencies

- Quip API key and documentation
- Stable core system (Phases 1-3)

### Implementation Notes

**Stakeholder management already completed in Phase 0** - Comprehensive Organization/Team/Stakeholder system with RACI roles is fully implemented. Phase 4 focuses on external system integration rather than internal stakeholder management.

## Phase 5: Advanced Features & Polish

**Goal:** Enterprise-ready features and polish
**Success Criteria:** Production-ready system with advanced capabilities

### Features

- [ ] Multi-user support - Team shared contexts (simplified by existing Organization/Team structure) `L`
- [ ] Advanced RACI workflows - Complex stakeholder approval chains and delegation `M`
- [ ] Cross-organizational project management - Multi-tenant RACI coordination `M`
- [ ] Advanced SOPs - Conditional logic and variables `L`
- [ ] OAuth authentication - Secure multi-user access `L`
- [ ] Performance optimization - Caching and query optimization `M`
- [ ] Enterprise stakeholder analytics - Advanced reporting on workload and accountability `M`
- [ ] Comprehensive documentation - User and developer guides `L`
- [ ] Mobile-friendly web UI - Optional web interface `XL`

### Dependencies

- User feedback from earlier phases
- Performance benchmarks
- Security audit for multi-user features

### Implementation Notes

Phase 5 is significantly enabled by Phase 0 over-delivery:
- **Organization/Team/Stakeholder structure** provides foundation for multi-user support
- **RACI system** enables advanced enterprise workflow capabilities
- **Energy and context systems** proven in integration tests provide productivity features
- Multi-organizational coordination capabilities already demonstrated in test scenarios
