"""
Initial GTD schema migration.

Creates the core GTD database tables: gtd_items, contexts, action_contexts,
organizations, stakeholders, and gtd_item_stakeholders with proper constraints.
"""

import sqlite3

from .base import Migration


class InitialSchemaMigration(Migration):
    """Create initial GTD database schema."""

    version = 1
    description = (
        "Create initial GTD schema with gtd_items, contexts, and relationships"
    )
    risk_level = "LOW"

    def upgrade(self, conn: sqlite3.Connection) -> None:
        """Create GTD tables and indexes."""
        # Core GTD items table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gtd_items (
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
            )
        """)

        # Contexts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Action-Context many-to-many relationship
        conn.execute("""
            CREATE TABLE IF NOT EXISTS action_contexts (
                action_id TEXT NOT NULL,
                context_id TEXT NOT NULL,
                PRIMARY KEY (action_id, context_id),
                FOREIGN KEY (action_id) REFERENCES gtd_items(id) ON DELETE CASCADE,
                FOREIGN KEY (context_id) REFERENCES contexts(id) ON DELETE CASCADE
            )
        """)

        # Organizations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (type IN ('internal', 'customer', 'partner', 'other'))
            )
        """)

        # Stakeholders table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stakeholders (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                organization_id TEXT,
                team_id TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL
            )
        """)

        # GTD Item Stakeholder RACI relationships
        conn.execute("""
            CREATE TABLE IF NOT EXISTS gtd_item_stakeholders (
                gtd_item_id TEXT NOT NULL,
                stakeholder_id TEXT NOT NULL,
                raci_role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (gtd_item_id, stakeholder_id, raci_role),
                FOREIGN KEY (gtd_item_id) REFERENCES gtd_items(id) ON DELETE CASCADE,
                FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
                CHECK (raci_role IN ('responsible', 'accountable', 'consulted', 'informed'))
            )
        """)

        # Triggers for automatic timestamp updates
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_gtd_items_timestamp
            AFTER UPDATE ON gtd_items
            FOR EACH ROW
            WHEN NEW.updated_at = OLD.updated_at
            BEGIN
                UPDATE gtd_items SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
            END
        """)

        # Performance indexes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_gtd_items_status ON gtd_items(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_gtd_items_type ON gtd_items(item_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_gtd_items_project ON gtd_items(project_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_gtd_items_created ON gtd_items(created_at)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_contexts_name ON contexts(name)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stakeholders_email ON stakeholders(email)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_stakeholders_org ON stakeholders(organization_id)"
        )

        conn.commit()

    def downgrade(self, conn: sqlite3.Connection) -> None:
        """Remove GTD schema."""
        # Drop in reverse order due to foreign key dependencies
        conn.execute("DROP TRIGGER IF EXISTS update_gtd_items_timestamp")
        conn.execute("DROP TABLE IF EXISTS gtd_item_stakeholders")
        conn.execute("DROP TABLE IF EXISTS stakeholders")
        conn.execute("DROP TABLE IF EXISTS organizations")
        conn.execute("DROP TABLE IF EXISTS action_contexts")
        conn.execute("DROP TABLE IF EXISTS contexts")
        conn.execute("DROP TABLE IF EXISTS gtd_items")
        conn.commit()

    def validate_postconditions(self, conn: sqlite3.Connection) -> bool:
        """Verify schema was created correctly."""
        # Check that all expected tables exist
        expected_tables = [
            "gtd_items",
            "contexts",
            "action_contexts",
            "organizations",
            "stakeholders",
            "gtd_item_stakeholders",
        ]

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        return all(table in existing_tables for table in expected_tables)
