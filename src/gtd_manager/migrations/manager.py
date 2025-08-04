"""Migration manager - minimal implementation for TDD."""

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from .base import DataIntegrityResult, Migration, RiskAssessment


class MigrationManager:
    """Minimal migration manager to pass initial test."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_current_version(self) -> int:
        """Get current schema version from database."""
        if not self.db_path.exists():
            return 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
                )
                result = cursor.fetchone()
                return int(result[0]) if result else 0
        except sqlite3.Error:
            return 0

    def create_backup(self, from_version: int, to_version: int) -> Path:
        """Create backup of database."""
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_v{from_version}_to_v{to_version}_{timestamp}.db"
        backup_path = backup_dir / backup_name

        # Only create backup if database file exists
        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_path)
        else:
            # Create empty backup file for consistency
            backup_path.touch()

        return backup_path

    def validate_data_integrity(self) -> DataIntegrityResult:
        """Validate database integrity."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Count total rows
                cursor = conn.execute("SELECT COUNT(*) FROM gtd_items")
                row_count = cursor.fetchone()[0]

                return DataIntegrityResult(
                    is_valid=True, row_count=row_count, constraint_violations=[]
                )
        except sqlite3.Error:
            return DataIntegrityResult(
                is_valid=False, row_count=0, constraint_violations=["Database error"]
            )

    def apply_migration(self, migration: Migration, target_version: int) -> None:
        """Apply a migration with backup and validation."""
        # Initialize database if it doesn't exist
        if not self.db_path.exists():
            from ..database import init_database

            init_database(self.db_path)

        # Create backup before applying migration
        backup_path = self.create_backup(
            from_version=self.get_current_version(), to_version=target_version
        )

        try:
            # Apply the migration
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                migration.upgrade(conn)

                # Update schema version
                conn.execute("DELETE FROM schema_version")
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)", (target_version,)
                )
                conn.commit()

        except Exception:
            # Restore from backup on failure
            if backup_path.exists() and backup_path.stat().st_size > 0:
                shutil.copy2(backup_path, self.db_path)
            raise

    def rollback_migration(self, migration: Migration, target_version: int) -> None:
        """Rollback a migration."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            migration.downgrade(conn)

            # Update schema version
            conn.execute("DELETE FROM schema_version")
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (target_version,)
            )
            conn.commit()

    def create_json_export(self) -> Path:
        """Create JSON export of all database tables as safety net."""
        export_dir = self.db_path.parent / "exports"
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = export_dir / f"db_export_{timestamp}.json"

        export_data = {}

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get all tables except sqlite system tables
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Whitelist of allowed table names to prevent SQL injection
            allowed_tables = {
                "gtd_items",
                "contexts",
                "action_contexts",
                "organizations",
                "stakeholders",
                "gtd_item_stakeholders",
            }

            for table in tables:
                # Validate table name against whitelist
                if table not in allowed_tables:
                    continue

                # Safe to use f-string here since table is validated
                cursor = conn.execute(f"SELECT * FROM {table}")  # nosec B608
                rows = cursor.fetchall()
                # Convert Row objects to dictionaries
                export_data[table] = [dict(row) for row in rows]

        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        return export_path

    def assess_migration_risk(self, migration: Migration) -> RiskAssessment:
        """Assess the risk level of a migration."""
        warnings = []
        level = "LOW"
        backup_recommended = False

        # Check if migration has risk assessment methods
        if hasattr(migration, "involves_data_loss") and migration.involves_data_loss():
            level = "HIGH"
            backup_recommended = True
            warnings.append("Migration involves potential data loss")

        if hasattr(migration, "get_risk_factors"):
            risk_factors = migration.get_risk_factors()
            warnings.extend(risk_factors)
            if risk_factors:
                level = "HIGH" if level == "LOW" else level
                backup_recommended = True

        return RiskAssessment(
            level=level, warnings=warnings, backup_recommended=backup_recommended
        )
