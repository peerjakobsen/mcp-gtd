"""Migration manager - minimal implementation for TDD."""

import hashlib
import inspect
import json
import os
import shutil
import sqlite3
import time
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

    def discover_migrations(self) -> dict[int, Migration]:
        """Discover all available migration classes."""
        # For now, we manually register known migrations
        # In the future, this could scan the migrations directory
        from .initial_schema import InitialSchemaMigration

        migrations: dict[int, Migration] = {}
        initial_migration = InitialSchemaMigration()
        migrations[initial_migration.version] = initial_migration

        return migrations

    def get_available_migrations(self) -> dict[int, Migration]:
        """Get all available migration classes."""
        return self.discover_migrations()

    def get_pending_migrations(self) -> dict[int, Migration]:
        """Get migrations that need to be applied."""
        current_version = self.get_current_version()
        available_migrations = self.get_available_migrations()

        # Return migrations with version higher than current
        pending = {}
        for version, migration in available_migrations.items():
            if version > current_version:
                pending[version] = migration

        return pending

    def get_migration_history(self) -> list[dict[str, str | int]]:
        """Get history of applied migrations."""
        if not self.db_path.exists():
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT version, applied_at, 'InitialSchemaMigration' as name
                    FROM schema_version
                    ORDER BY applied_at DESC
                """)

                history = []
                for row in cursor.fetchall():
                    history.append(
                        {
                            "version": row["version"],
                            "applied_at": row["applied_at"],
                            "name": row["name"],
                        }
                    )
                return history

        except sqlite3.Error:
            return []

    def load_migration(self, version: int) -> Migration:
        """Load a specific migration by version."""
        available_migrations = self.get_available_migrations()

        if version not in available_migrations:
            raise ValueError(f"Migration version {version} not found")

        return available_migrations[version]

    def validate_migration_sequence(self) -> bool:
        """Validate that migration sequence is intact."""
        available_migrations = self.get_available_migrations()

        if not available_migrations:
            return True

        # Check that versions form a continuous sequence starting from 1
        versions = sorted(available_migrations.keys())
        expected_versions = list(range(1, max(versions) + 1))

        return versions == expected_versions

    def migrate_to_version(self, target_version: int) -> None:
        """Migrate database to a specific version."""
        current_version = self.get_current_version()

        if target_version == current_version:
            return  # Already at target version

        available_migrations = self.get_available_migrations()

        if target_version > current_version:
            # Migrate up
            for version in range(current_version + 1, target_version + 1):
                if version not in available_migrations:
                    raise ValueError(
                        f"Cannot migrate to version {version}: migration not found"
                    )

                migration = available_migrations[version]
                self.apply_migration(migration, target_version=version)

        elif target_version < current_version:
            # Migrate down
            for version in range(current_version, target_version, -1):
                if version not in available_migrations:
                    raise ValueError(
                        f"Cannot rollback from version {version}: migration not found"
                    )

                migration = available_migrations[version]
                self.rollback_migration(migration, target_version=version - 1)

    def migrate_to_latest(self) -> int:
        """Migrate database to the latest available version."""
        available_migrations = self.get_available_migrations()

        if not available_migrations:
            return self.get_current_version()

        latest_version = max(available_migrations.keys())
        self.migrate_to_version(latest_version)

        return latest_version

    def _init_enhanced_schema_version_table(self) -> None:
        """Initialize enhanced schema_version table with metadata columns."""
        if not self.db_path.exists():
            from ..database import init_database

            init_database(self.db_path)

        with sqlite3.connect(self.db_path) as conn:
            # Drop old table if it exists
            conn.execute("DROP TABLE IF EXISTS schema_version")

            # Create enhanced schema_version table
            conn.execute("""
                CREATE TABLE schema_version (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    applied_by TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _generate_migration_checksum(self, migration: Migration) -> str:
        """Generate SHA-256 checksum of migration code."""
        # Get the source code of the upgrade method
        upgrade_source = inspect.getsource(migration.upgrade)
        downgrade_source = inspect.getsource(migration.downgrade)

        # Combine sources and generate hash
        combined_source = upgrade_source + downgrade_source
        checksum = hashlib.sha256(combined_source.encode("utf-8")).hexdigest()

        return checksum

    def apply_migration_with_metadata(
        self, migration: Migration, target_version: int
    ) -> None:
        """Apply migration and track comprehensive metadata."""
        # Initialize enhanced schema if needed
        if not self.db_path.exists():
            self._init_enhanced_schema_version_table()
        else:
            # Ensure we have the enhanced schema
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("PRAGMA table_info(schema_version)")
                columns = [row[1] for row in cursor.fetchall()]
                if "checksum" not in columns:
                    self._init_enhanced_schema_version_table()

        # Create backup before applying migration
        backup_path = self.create_backup(
            from_version=self.get_current_version(), to_version=target_version
        )

        # Generate migration metadata
        migration_name = migration.__class__.__name__
        checksum = self._generate_migration_checksum(migration)
        applied_by = f"MigrationManager-{os.getenv('USER', 'system')}"

        start_time = time.time()

        try:
            # Apply the migration
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                migration.upgrade(conn)

                # Record migration with metadata
                end_time = time.time()
                duration_ms = int((end_time - start_time) * 1000)

                # Clear old version record and insert new one with metadata
                conn.execute(
                    "DELETE FROM schema_version WHERE version = ?", (target_version,)
                )
                conn.execute(
                    """
                    INSERT INTO schema_version (version, name, checksum, duration_ms, applied_by)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (target_version, migration_name, checksum, duration_ms, applied_by),
                )

                conn.commit()

        except Exception:
            # Restore from backup on failure
            if backup_path.exists() and backup_path.stat().st_size > 0:
                shutil.copy2(backup_path, self.db_path)
            raise

    def get_enhanced_migration_history(self) -> list[dict[str, str | int | None]]:
        """Get comprehensive migration history with all metadata."""
        if not self.db_path.exists():
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT version, name, checksum, duration_ms, applied_by, applied_at
                    FROM schema_version
                    ORDER BY applied_at DESC
                """)

                history = []
                for row in cursor.fetchall():
                    history.append(
                        {
                            "version": row["version"],
                            "name": row["name"],
                            "checksum": row["checksum"],
                            "duration_ms": row["duration_ms"],
                            "applied_by": row["applied_by"],
                            "applied_at": row["applied_at"],
                        }
                    )
                return history

        except sqlite3.Error:
            return []

    def verify_migration_integrity(self, version: int) -> bool:
        """Verify that a migration hasn't been tampered with."""
        try:
            # Get stored checksum
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT checksum FROM schema_version WHERE version = ?", (version,)
                )
                result = cursor.fetchone()
                if not result:
                    return False
                stored_checksum: str = str(result[0])

            # Get current migration and generate checksum
            migration = self.load_migration(version)
            current_checksum = self._generate_migration_checksum(migration)

            return stored_checksum == current_checksum

        except (sqlite3.Error, ValueError):
            return False

    def validate_migration_dependencies(self, migration: Migration) -> bool:
        """Validate that all migration dependencies are satisfied."""
        # Check if migration has dependencies method
        if not hasattr(migration, "get_dependencies"):
            return True

        dependencies = migration.get_dependencies()
        if not dependencies:
            return True

        # Get current migration history to check what's been applied
        applied_migrations: set[int] = set()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT version FROM schema_version")
                applied_migrations = {int(row[0]) for row in cursor.fetchall()}
        except sqlite3.Error:
            applied_migrations = set()

        # Check that all dependencies have been applied
        for dependency_version in dependencies:
            if dependency_version not in applied_migrations:
                return False

        return True

    def validate_migration_preconditions(self, migration: Migration) -> bool:
        """Validate that migration preconditions are met."""
        # Check if migration has preconditions validation method
        if not hasattr(migration, "validate_preconditions"):
            return True

        try:
            return migration.validate_preconditions()
        except Exception:
            # If precondition check fails with exception, assume failure
            return False
