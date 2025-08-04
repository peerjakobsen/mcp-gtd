# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-03-phase0-completion/spec.md

## Schema Changes

### New Tables

**gtd_items** - Base table for all GTD items

```sql
CREATE TABLE gtd_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'inbox',
    item_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    project_id INTEGER,
    FOREIGN KEY (project_id) REFERENCES gtd_items(id) ON DELETE SET NULL,
    CHECK (status IN ('inbox', 'clarified', 'organized', 'reviewing', 'complete', 'someday')),
    CHECK (item_type IN ('action', 'project'))
);
```

**contexts** - GTD contexts for organizing actions

```sql
CREATE TABLE contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**action_contexts** - Many-to-many relationship between actions and contexts

```sql
CREATE TABLE action_contexts (
    action_id INTEGER NOT NULL,
    context_id INTEGER NOT NULL,
    PRIMARY KEY (action_id, context_id),
    FOREIGN KEY (action_id) REFERENCES gtd_items(id) ON DELETE CASCADE,
    FOREIGN KEY (context_id) REFERENCES contexts(id) ON DELETE CASCADE
);
```

### Indexes

```sql
CREATE INDEX idx_gtd_items_status ON gtd_items(status);
CREATE INDEX idx_gtd_items_type ON gtd_items(item_type);
CREATE INDEX idx_gtd_items_project ON gtd_items(project_id);
CREATE INDEX idx_gtd_items_created ON gtd_items(created_at);
CREATE INDEX idx_contexts_name ON contexts(name);
```

### Triggers

```sql
CREATE TRIGGER update_gtd_items_timestamp
    AFTER UPDATE ON gtd_items
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE gtd_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

## Migration Implementation

- Create migration script in `src/gtd_manager/migrations/001_initial_schema.py`
- Include schema version tracking table for future migrations
- Support rollback capability for development
- Integrate with existing database connection management

## Data Integrity Rules

- Actions must have at least one context when status is 'organized'
- Projects cannot be nested more than 3 levels deep
- Completed items cannot be modified except for status changes
- Foreign key constraints enforce referential integrity
