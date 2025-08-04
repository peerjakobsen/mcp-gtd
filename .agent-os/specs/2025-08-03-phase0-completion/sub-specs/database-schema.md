# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-03-phase0-completion/spec.md

## Schema Changes

### New Tables

**gtd_items** - Base table for all GTD items

```sql
CREATE TABLE gtd_items (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'inbox',
    item_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    project_id TEXT,
    due_date TIMESTAMP,
    energy_level INTEGER,
    success_criteria TEXT,
    FOREIGN KEY (project_id) REFERENCES gtd_items(id) ON DELETE SET NULL,
    CHECK (status IN ('inbox', 'clarified', 'organized', 'reviewing', 'complete', 'someday')),
    CHECK (item_type IN ('action', 'project')),
    CHECK (energy_level IS NULL OR (energy_level >= 1 AND energy_level <= 5))
);
```

**Architectural Decision**: Uses TEXT primary keys instead of INTEGER AUTOINCREMENT for better GTD item identification patterns (e.g., 'action-call-client-001', 'project-website-launch'). This provides more meaningful IDs for GTD workflows and integrates better with external systems.

**contexts** - GTD contexts for organizing actions

```sql
CREATE TABLE contexts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**action_contexts** - Many-to-many relationship between actions and contexts

```sql
CREATE TABLE action_contexts (
    action_id TEXT NOT NULL,
    context_id TEXT NOT NULL,
    PRIMARY KEY (action_id, context_id),
    FOREIGN KEY (action_id) REFERENCES gtd_items(id) ON DELETE CASCADE,
    FOREIGN KEY (context_id) REFERENCES contexts(id) ON DELETE CASCADE
);
```

**organizations** - RACI stakeholder organizations

```sql
CREATE TABLE organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (type IN ('internal', 'customer', 'partner', 'other'))
);
```

**stakeholders** - RACI stakeholder entities

```sql
CREATE TABLE stakeholders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    organization_id TEXT,
    team_id TEXT,
    role TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
);
```

**gtd_item_stakeholders** - RACI relationships between GTD items and stakeholders

```sql
CREATE TABLE gtd_item_stakeholders (
    gtd_item_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    raci_role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (gtd_item_id, stakeholder_id, raci_role),
    FOREIGN KEY (gtd_item_id) REFERENCES gtd_items(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
    CHECK (raci_role IN ('responsible', 'accountable', 'consulted', 'informed'))
);
```

### Indexes

```sql
CREATE INDEX idx_gtd_items_status ON gtd_items(status);
CREATE INDEX idx_gtd_items_type ON gtd_items(item_type);
CREATE INDEX idx_gtd_items_project ON gtd_items(project_id);
CREATE INDEX idx_gtd_items_created ON gtd_items(created_at);
CREATE INDEX idx_contexts_name ON contexts(name);
CREATE INDEX idx_stakeholders_email ON stakeholders(email);
CREATE INDEX idx_stakeholders_org ON stakeholders(organization_id);
```

### Triggers

```sql
CREATE TRIGGER update_gtd_items_timestamp
    AFTER UPDATE ON gtd_items
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE gtd_items SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
END;
```

## Migration Implementation

**✅ COMPLETED**:
- Migration script implemented in `src/gtd_manager/migrations/initial_schema.py`
- Schema version tracking table included for future migrations
- Full rollback capability with MigrationManager class
- Integrated with existing database connection management
- Backup creation with automatic restore on failure
- Data integrity validation and risk assessment
- JSON export safety net for complex migrations

## Data Integrity Rules

- Actions must have at least one context when status is 'organized'
- Projects cannot be nested more than 3 levels deep
- Completed items cannot be modified except for status changes
- Foreign key constraints enforce referential integrity
