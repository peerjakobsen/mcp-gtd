"""
Tests for database path detection and connection management.

Tests the smart database path detection logic that handles Claude Desktop
MCP server requirements across different deployment scenarios.
"""

import contextlib
import os
import sqlite3
from unittest.mock import patch

import pytest

from gtd_manager.database import get_database_path, get_db_connection, init_database


class TestDatabasePathDetection:
    """Test database path detection across different environments."""

    def test_environment_variable_override_takes_priority(self, tmp_path):
        """Test that MCP_GTD_DB_PATH environment variable overrides all other logic."""
        custom_db_path = tmp_path / "custom_location" / "gtd.db"

        with patch.dict(os.environ, {"MCP_GTD_DB_PATH": str(custom_db_path)}):
            result = get_database_path()
            assert result == custom_db_path.resolve()

    def test_uvx_cache_environment_detection(self, tmp_path, monkeypatch):
        """Test detection of uvx/cache environment and proper user data directory."""
        # Mock __file__ to simulate running from .cache directory
        cache_path = tmp_path / ".cache" / "uvx" / "mcp-gtd" / "database.py"
        cache_path.parent.mkdir(parents=True)

        with (
            patch("gtd_manager.database.__file__", str(cache_path)),
            patch("pathlib.Path.home") as mock_home,
        ):
            mock_home.return_value = tmp_path / "home"

            # Clear environment variable
            monkeypatch.delenv("MCP_GTD_DB_PATH", raising=False)

            result = get_database_path()
            expected = tmp_path / "home" / ".local" / "share" / "mcp-gtd" / "data.db"
            assert result == expected

    def test_site_packages_environment_detection(self, tmp_path, monkeypatch):
        """Test detection of site-packages (system install) environment."""
        # Mock __file__ to simulate running from site-packages
        site_packages_path = tmp_path / "site-packages" / "gtd_manager" / "database.py"
        site_packages_path.parent.mkdir(parents=True)

        with (
            patch("gtd_manager.database.__file__", str(site_packages_path)),
            patch("pathlib.Path.home") as mock_home,
        ):
            mock_home.return_value = tmp_path / "home"

            # Clear environment variable
            monkeypatch.delenv("MCP_GTD_DB_PATH", raising=False)

            result = get_database_path()
            expected = tmp_path / "home" / ".local" / "share" / "mcp-gtd" / "data.db"
            assert result == expected

    def test_development_environment_detection(self, tmp_path, monkeypatch):
        """Test detection of local development environment."""
        # Mock __file__ to simulate running from project source
        project_path = tmp_path / "mcp-gtd" / "src" / "gtd_manager" / "database.py"
        project_path.parent.mkdir(parents=True)

        with patch("gtd_manager.database.__file__", str(project_path)):
            # Clear environment variable
            monkeypatch.delenv("MCP_GTD_DB_PATH", raising=False)

            result = get_database_path()
            expected = tmp_path / "mcp-gtd" / "data.db"
            assert result == expected

    def test_path_creation_on_demand(self, tmp_path):
        """Test that parent directories are created when they don't exist."""
        custom_db_path = tmp_path / "new" / "nested" / "directory" / "gtd.db"

        with patch.dict(os.environ, {"MCP_GTD_DB_PATH": str(custom_db_path)}):
            result = get_database_path()

            # Path should be returned and parent directory should be created
            assert result == custom_db_path.resolve()
            assert result.parent.exists()

    def test_permission_error_handling(self, tmp_path, monkeypatch):
        """Test graceful handling when preferred path is not writable."""
        # Create a path that will cause mkdir to fail
        restricted_path = tmp_path / "readonly_parent" / "subdir" / "gtd.db"
        restricted_path.parent.parent.mkdir(parents=True)

        # Make parent read-only to prevent mkdir
        try:
            restricted_path.parent.parent.chmod(
                0o555
            )  # Read-only, can't create subdirs
        except (OSError, PermissionError):
            # If we can't set permissions, skip this test
            pytest.skip("Cannot set directory permissions in this environment")

        with (
            patch.dict(os.environ, {"MCP_GTD_DB_PATH": str(restricted_path)}),
            patch(
                "gtd_manager.database.__file__",
                str(tmp_path / "src" / "gtd_manager" / "database.py"),
            ),
        ):
            try:
                result = get_database_path()
                # In environments where permission restrictions don't work as expected,
                # the function might still succeed. Check if fallback was used.
                expected_fallback = tmp_path / "data.db"
                if result == expected_fallback:
                    # Fallback worked as expected
                    pass
                elif result == restricted_path.resolve():
                    # Permission restriction didn't work, but path was created successfully
                    # This can happen in containerized environments
                    pytest.skip(
                        "Permission restrictions not enforced in this environment"
                    )
                else:
                    pytest.fail(f"Unexpected result: {result}")
            finally:
                # Clean up permissions
                with contextlib.suppress(OSError, PermissionError):
                    restricted_path.parent.parent.chmod(0o755)

    def test_expanduser_support(self, tmp_path):
        """Test that tilde (~) expansion works in environment variable."""
        with (
            patch.dict(os.environ, {"MCP_GTD_DB_PATH": "~/custom/gtd.db"}),
            patch("pathlib.Path.expanduser") as mock_expanduser,
        ):
            custom_path = tmp_path / "home" / "custom" / "gtd.db"
            mock_expanduser.return_value = custom_path

            result = get_database_path()
            expected = custom_path.resolve()
            assert result == expected


class TestDatabaseConnectionManager:
    """Test database connection context manager."""

    def test_connection_context_manager(self, tmp_path):
        """Test that database connection context manager works properly."""
        db_path = tmp_path / "test.db"

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                assert isinstance(conn, sqlite3.Connection)

                # Test that foreign keys are enabled
                cursor = conn.execute("PRAGMA foreign_keys")
                assert cursor.fetchone()[0] == 1

                # Test that row factory is set
                assert conn.row_factory is sqlite3.Row

    def test_database_initialization_on_first_connection(self, tmp_path):
        """Test that database is initialized when file doesn't exist."""
        db_path = tmp_path / "new_test.db"

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            # Database file shouldn't exist yet
            assert not db_path.exists()

            with get_db_connection() as conn:
                # After connection, database should exist and be initialized
                assert db_path.exists()

                # Check that basic tables exist (from init_database)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                assert "schema_version" in tables

    def test_connection_error_handling(self, tmp_path):
        """Test proper error handling in database connections."""
        # Use a path that definitely cannot be a valid database file
        # Use invalid characters that would cause SQLite to fail
        db_path = tmp_path / "invalid\x00database.db"

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            # Should raise some kind of error when trying to connect to invalid path
            with (
                pytest.raises((sqlite3.Error, OSError, ValueError)),
                get_db_connection(),
            ):
                pass

    def test_transaction_rollback_on_error(self, tmp_path):
        """Test that transactions are rolled back on error."""
        db_path = tmp_path / "transaction_test.db"

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            # Initialize database
            with get_db_connection():
                pass

            try:
                with get_db_connection() as conn:
                    conn.execute("CREATE TABLE test_rollback (id INTEGER PRIMARY KEY)")
                    conn.commit()  # Commit the table creation first

                    # Now start a transaction that will be rolled back
                    conn.execute("INSERT INTO test_rollback (id) VALUES (1)")
                    # Force an error before commit
                    raise sqlite3.Error("Test error")
            except sqlite3.Error:
                pass

            # Verify rollback occurred - table exists but insert was rolled back
            with get_db_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM test_rollback")
                assert cursor.fetchone()[0] == 0


class TestDatabaseInitialization:
    """Test database initialization and schema setup."""

    def test_init_database_creates_schema_version_table(self, tmp_path):
        """Test that init_database creates schema version tracking."""
        db_path = tmp_path / "schema_test.db"

        init_database(db_path)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            assert cursor.fetchone() is not None

            # Check initial version
            cursor = conn.execute("SELECT version FROM schema_version")
            assert cursor.fetchone()[0] == 1

    def test_init_database_is_idempotent(self, tmp_path):
        """Test that running init_database multiple times is safe."""
        db_path = tmp_path / "idempotent_test.db"

        # Initialize twice
        init_database(db_path)
        init_database(db_path)

        with sqlite3.connect(db_path) as conn:
            # Should still have only one version record
            cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
            assert cursor.fetchone()[0] == 1

    def test_init_database_with_foreign_keys(self, tmp_path):
        """Test that init_database properly enables foreign key constraints."""
        db_path = tmp_path / "fk_test.db"

        init_database(db_path)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Verify foreign keys are working by testing a constraint
            conn.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
            conn.execute("""
                CREATE TABLE child (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER REFERENCES parent(id)
                )
            """)

            # This should fail due to foreign key constraint
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO child (parent_id) VALUES (999)")
                conn.commit()

    def test_database_file_permissions(self, tmp_path):
        """Test that database file has appropriate permissions."""
        db_path = tmp_path / "permissions_test.db"

        init_database(db_path)

        # Check that file exists and is readable/writable by owner
        assert db_path.exists()
        assert os.access(db_path, os.R_OK)
        assert os.access(db_path, os.W_OK)


class TestClaudeDesktopIntegration:
    """Test specific Claude Desktop MCP server integration scenarios."""

    def test_uvx_installation_path_pattern(self, tmp_path, monkeypatch):
        """Test the exact path pattern for Claude Desktop uvx installations."""
        # Simulate uvx cache directory structure
        uvx_cache = tmp_path / ".cache" / "uv" / "builds-v0" / "mcp-gtd"
        uvx_cache.mkdir(parents=True)

        mock_file_path = (
            uvx_cache
            / "lib"
            / "python3.13"
            / "site-packages"
            / "gtd_manager"
            / "database.py"
        )

        with (
            patch("gtd_manager.database.__file__", str(mock_file_path)),
            patch("pathlib.Path.home") as mock_home,
        ):
            mock_home.return_value = tmp_path / "home"

            monkeypatch.delenv("MCP_GTD_DB_PATH", raising=False)

            result = get_database_path()
            expected = tmp_path / "home" / ".local" / "share" / "mcp-gtd" / "data.db"
            assert result == expected

    def test_claude_desktop_config_path_override(self, tmp_path):
        """Test that Claude Desktop can override database path via environment."""
        claude_config_path = tmp_path / "claude_data" / "mcp_gtd.db"

        with patch.dict(os.environ, {"MCP_GTD_DB_PATH": str(claude_config_path)}):
            result = get_database_path()
            assert result == claude_config_path.resolve()

            # Verify parent directory is created
            assert result.parent.exists()

    def test_no_stdout_contamination_during_path_detection(self, tmp_path, capsys):
        """Test that database path detection doesn't contaminate stdout (MCP protocol)."""
        with patch.dict(os.environ, {"MCP_GTD_DB_PATH": str(tmp_path / "test.db")}):
            get_database_path()

            # Verify no stdout output (critical for MCP protocol)
            captured = capsys.readouterr()
            assert captured.out == ""

    def test_error_logging_goes_to_stderr_only(self, tmp_path, capsys):
        """Test that database errors are logged to stderr, not stdout."""
        # Force a permission error
        restricted_path = tmp_path / "restricted"
        restricted_path.mkdir()
        restricted_path.chmod(0o444)  # Read-only

        db_path = restricted_path / "test.db"

        with patch.dict(os.environ, {"MCP_GTD_DB_PATH": str(db_path)}):
            # This should log error to stderr but not stdout
            get_database_path()

            captured = capsys.readouterr()
            assert captured.out == ""  # No stdout contamination
            # stderr may contain error logs (which is fine for MCP)


class TestMigrationSystem:
    """Test database migration system with backup and rollback capabilities."""

    def test_migration_manager_initialization(self, tmp_path):
        """Test that MigrationManager initializes properly."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "migration_test.db"
        manager = MigrationManager(db_path)

        assert manager.db_path == db_path
        assert manager.get_current_version() == 0  # No migrations applied yet

    def test_migration_backup_creation(self, tmp_path):
        """Test that migrations create backups before applying changes."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "backup_test.db"
        init_database(db_path)

        # Create some test data
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test_data (id INTEGER, value TEXT)")
            conn.execute("INSERT INTO test_data VALUES (1, 'important_data')")
            conn.commit()

        manager = MigrationManager(db_path)
        backup_path = manager.create_backup(from_version=1, to_version=2)

        assert backup_path.exists()
        assert "backup" in str(backup_path)

        # Verify backup contains our data
        with sqlite3.connect(backup_path) as backup_conn:
            cursor = backup_conn.execute("SELECT value FROM test_data WHERE id = 1")
            assert cursor.fetchone()[0] == "important_data"

    def test_migration_data_integrity_validation(self, tmp_path):
        """Test pre and post migration data integrity checks."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "integrity_test.db"
        init_database(db_path)

        # Create test schema and data
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE gtd_items (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'inbox'
                )
            """)
            conn.execute("INSERT INTO gtd_items (title) VALUES ('Test Action')")
            conn.commit()

        manager = MigrationManager(db_path)

        # Test data integrity validation
        integrity_result = manager.validate_data_integrity()
        assert integrity_result.is_valid
        assert integrity_result.row_count > 0
        assert len(integrity_result.constraint_violations) == 0

    def test_migration_rollback_capability(self, tmp_path):
        """Test that migrations can be rolled back successfully."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "rollback_test.db"
        manager = MigrationManager(db_path)

        # Apply migration
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        # Verify migration was applied
        assert manager.get_current_version() == 1
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='gtd_items'"
            )
            assert cursor.fetchone() is not None

        # Rollback migration
        manager.rollback_migration(migration, target_version=0)

        # Verify rollback was successful
        assert manager.get_current_version() == 0
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='gtd_items'"
            )
            assert cursor.fetchone() is None

    def test_migration_failure_recovery(self, tmp_path):
        """Test that failed migrations restore from backup."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "failure_test.db"
        init_database(db_path)

        # Create important test data
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE important_data (id INTEGER, value TEXT)")
            conn.execute("INSERT INTO important_data VALUES (1, 'critical_info')")
            conn.commit()

        manager = MigrationManager(db_path)

        # Create a migration that will fail
        class FailingMigration:
            def upgrade(self, conn):
                raise sqlite3.Error("Simulated migration failure")

            def downgrade(self, conn):
                pass

        # Attempt migration - should fail and restore
        failing_migration = FailingMigration()

        with pytest.raises(sqlite3.Error):
            manager.apply_migration(failing_migration, target_version=1)

        # Verify data was preserved
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT value FROM important_data WHERE id = 1")
            assert cursor.fetchone()[0] == "critical_info"

    def test_json_export_import_safety_net(self, tmp_path):
        """Test JSON export/import as safety net for complex migrations."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "export_test.db"
        init_database(db_path)

        # Create complex test data
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE gtd_items (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'inbox',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE contexts (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            conn.execute("INSERT INTO gtd_items (title) VALUES ('Important Task')")
            conn.execute("INSERT INTO contexts (name) VALUES ('@computer')")
            conn.commit()

        manager = MigrationManager(db_path)

        # Create JSON export
        export_path = manager.create_json_export()
        assert export_path.exists()

        # Verify export contains our data
        import json

        with open(export_path) as f:
            export_data = json.load(f)

        assert "gtd_items" in export_data
        assert "contexts" in export_data
        assert export_data["gtd_items"][0]["title"] == "Important Task"
        assert export_data["contexts"][0]["name"] == "@computer"

    def test_migration_risk_assessment(self, tmp_path):
        """Test migration risk assessment warnings."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "risk_test.db"
        manager = MigrationManager(db_path)

        # Mock a risky migration (column drop)
        class RiskyMigration:
            def involves_data_loss(self):
                return True

            def get_risk_factors(self):
                return ["Column removal - potential data loss"]

        risky_migration = RiskyMigration()
        risk_assessment = manager.assess_migration_risk(risky_migration)

        assert risk_assessment.level == "HIGH"
        assert "data loss" in risk_assessment.warnings[0].lower()
        assert risk_assessment.backup_recommended is True


class TestMigrationOrchestration:
    """Test high-level migration orchestration and discovery methods."""

    def test_discover_migrations(self, tmp_path):
        """Test automatic discovery of migration files."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "discovery_test.db"
        manager = MigrationManager(db_path)

        # Should discover the InitialSchemaMigration
        available_migrations = manager.discover_migrations()

        assert len(available_migrations) >= 1
        assert 1 in available_migrations  # Version 1 should be available
        assert hasattr(available_migrations[1], "upgrade")
        assert hasattr(available_migrations[1], "downgrade")

    def test_get_available_migrations(self, tmp_path):
        """Test getting list of all available migrations."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "available_test.db"
        manager = MigrationManager(db_path)

        available = manager.get_available_migrations()

        assert isinstance(available, dict)
        assert 1 in available  # InitialSchemaMigration should be version 1
        assert available[1].__class__.__name__ == "InitialSchemaMigration"

    def test_get_pending_migrations(self, tmp_path):
        """Test getting list of migrations that need to be applied."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "pending_test.db"
        manager = MigrationManager(db_path)

        # Before any migrations are applied
        pending = manager.get_pending_migrations()
        assert len(pending) >= 1
        assert 1 in pending

        # After applying initial migration
        migration = pending[1]
        manager.apply_migration(migration, target_version=1)

        # Should have no pending migrations
        pending_after = manager.get_pending_migrations()
        assert len(pending_after) == 0

    def test_get_migration_history(self, tmp_path):
        """Test getting history of applied migrations."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "history_test.db"
        manager = MigrationManager(db_path)

        # Initially no history
        history = manager.get_migration_history()
        assert len(history) == 0

        # Apply a migration
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        # Should now have history
        history_after = manager.get_migration_history()
        assert len(history_after) == 1
        assert history_after[0]["version"] == 1
        assert "applied_at" in history_after[0]
        assert "name" in history_after[0]

    def test_migrate_to_version(self, tmp_path):
        """Test migrating to a specific version."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "version_test.db"
        manager = MigrationManager(db_path)

        # Should be at version 0 initially
        assert manager.get_current_version() == 0

        # Migrate to version 1
        manager.migrate_to_version(1)
        assert manager.get_current_version() == 1

        # Verify schema was created
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='gtd_items'"
            )
            assert cursor.fetchone() is not None

    def test_migrate_to_latest(self, tmp_path):
        """Test migrating to the latest available version."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "latest_test.db"
        manager = MigrationManager(db_path)

        # Should be at version 0 initially
        assert manager.get_current_version() == 0

        # Migrate to latest
        final_version = manager.migrate_to_latest()
        assert final_version >= 1
        assert manager.get_current_version() == final_version

        # Should have no pending migrations
        pending = manager.get_pending_migrations()
        assert len(pending) == 0

    def test_load_migration(self, tmp_path):
        """Test loading a specific migration by version."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "load_test.db"
        manager = MigrationManager(db_path)

        # Load version 1 migration
        migration = manager.load_migration(1)
        assert migration is not None
        assert hasattr(migration, "upgrade")
        assert hasattr(migration, "downgrade")
        assert hasattr(migration, "version")
        assert migration.version == 1

        # Try to load non-existent migration
        with pytest.raises(ValueError):
            manager.load_migration(999)

    def test_validate_migration_sequence(self, tmp_path):
        """Test validation of migration sequence integrity."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "sequence_test.db"
        manager = MigrationManager(db_path)

        # Should validate successfully with current migrations
        is_valid = manager.validate_migration_sequence()
        assert is_valid is True

    def test_migrate_to_version_with_multiple_steps(self, tmp_path):
        """Test migrating through multiple versions in sequence."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "multi_step_test.db"
        manager = MigrationManager(db_path)

        # For now we only have version 1, but test the framework
        # In future when we have version 2, 3, etc., this will test multi-step migration
        manager.migrate_to_version(1)
        assert manager.get_current_version() == 1

        # Test that migrating to current version is a no-op
        manager.migrate_to_version(1)
        assert manager.get_current_version() == 1

    def test_migration_rollback_to_version(self, tmp_path):
        """Test rolling back to a previous version."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "rollback_version_test.db"
        manager = MigrationManager(db_path)

        # Migrate up to version 1
        manager.migrate_to_version(1)
        assert manager.get_current_version() == 1

        # Rollback to version 0
        manager.migrate_to_version(0)
        assert manager.get_current_version() == 0

        # Verify tables were dropped
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='gtd_items'"
            )
            assert cursor.fetchone() is None


class TestEnhancedSchemaVersioning:
    """Test enhanced schema version tracking with metadata."""

    def test_enhanced_schema_version_table_structure(self, tmp_path):
        """Test that enhanced schema_version table has all required columns."""
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "enhanced_schema_test.db"
        manager = MigrationManager(db_path)

        # Initialize with enhanced schema
        manager._init_enhanced_schema_version_table()

        with sqlite3.connect(db_path) as conn:
            # Check table structure
            cursor = conn.execute("PRAGMA table_info(schema_version)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}

            assert "version" in columns
            assert "name" in columns
            assert "checksum" in columns
            assert "duration_ms" in columns
            assert "applied_by" in columns
            assert "applied_at" in columns

    def test_migration_metadata_tracking(self, tmp_path):
        """Test that migration metadata is properly tracked."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "metadata_test.db"
        manager = MigrationManager(db_path)

        # Apply migration with metadata tracking
        migration = InitialSchemaMigration()
        manager.apply_migration_with_metadata(migration, target_version=1)

        # Check metadata was recorded
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM schema_version WHERE version = 1")
            row = cursor.fetchone()

            assert row is not None
            assert row["version"] == 1
            assert row["name"] == "InitialSchemaMigration"
            assert row["checksum"] is not None
            assert len(row["checksum"]) > 0
            assert row["duration_ms"] >= 0
            assert row["applied_by"] is not None
            assert row["applied_at"] is not None

    def test_migration_checksum_generation(self, tmp_path):
        """Test that migration checksums are generated consistently."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "checksum_test.db"
        manager = MigrationManager(db_path)

        migration = InitialSchemaMigration()

        # Generate checksum twice - should be identical
        checksum1 = manager._generate_migration_checksum(migration)
        checksum2 = manager._generate_migration_checksum(migration)

        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex digest length

    def test_migration_duration_tracking(self, tmp_path):
        """Test that migration duration is tracked."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "duration_test.db"
        manager = MigrationManager(db_path)

        migration = InitialSchemaMigration()
        manager.apply_migration_with_metadata(migration, target_version=1)

        # Check duration was recorded
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT duration_ms FROM schema_version WHERE version = 1"
            )
            duration = cursor.fetchone()[0]

            assert duration is not None
            assert duration >= 0  # Should be a non-negative number

    def test_enhanced_migration_history(self, tmp_path):
        """Test enhanced migration history with full metadata."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "enhanced_history_test.db"
        manager = MigrationManager(db_path)

        # Apply migration with metadata
        migration = InitialSchemaMigration()
        manager.apply_migration_with_metadata(migration, target_version=1)

        # Get enhanced history
        history = manager.get_enhanced_migration_history()

        assert len(history) == 1
        record = history[0]

        assert record["version"] == 1
        assert record["name"] == "InitialSchemaMigration"
        assert "checksum" in record
        assert "duration_ms" in record
        assert "applied_by" in record
        assert "applied_at" in record

    def test_migration_integrity_verification(self, tmp_path):
        """Test that migration integrity can be verified via checksums."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "integrity_test.db"
        manager = MigrationManager(db_path)

        # Apply migration
        migration = InitialSchemaMigration()
        manager.apply_migration_with_metadata(migration, target_version=1)

        # Verify integrity
        is_valid = manager.verify_migration_integrity(1)
        assert is_valid is True

        # Test with tampered checksum
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE schema_version SET checksum = 'invalid' WHERE version = 1"
            )
            conn.commit()

        is_valid_after_tamper = manager.verify_migration_integrity(1)
        assert is_valid_after_tamper is False


class TestMigrationBaseClassExtensions:
    """Test optional methods in Migration base class."""

    def test_migration_optional_methods_defaults(self):
        """Test that optional methods have sensible defaults."""
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration

        migration = InitialSchemaMigration()

        # Test optional methods with defaults
        assert migration.involves_data_loss() is False
        assert migration.get_risk_factors() == []
        assert migration.get_dependencies() == []
        assert migration.get_estimated_duration() is None
        assert migration.validate_preconditions() is True

    def test_custom_migration_with_optional_methods(self, tmp_path):
        """Test a custom migration that implements optional methods."""
        from gtd_manager.migrations.base import Migration

        class CustomMigration(Migration):
            version = 2

            def upgrade(self, conn):
                conn.execute("CREATE TABLE test_table (id INTEGER)")

            def downgrade(self, conn):
                conn.execute("DROP TABLE test_table")

            def involves_data_loss(self):
                return True

            def get_risk_factors(self):
                return ["Drops existing table", "May lose user data"]

            def get_dependencies(self):
                return [1]  # Depends on version 1

            def get_estimated_duration(self):
                return 5000  # 5 seconds in milliseconds

            def validate_preconditions(self):
                # Custom validation logic
                return True

        migration = CustomMigration()

        # Test custom implementations
        assert migration.involves_data_loss() is True
        assert migration.get_risk_factors() == [
            "Drops existing table",
            "May lose user data",
        ]
        assert migration.get_dependencies() == [1]
        assert migration.get_estimated_duration() == 5000
        assert migration.validate_preconditions() is True

    def test_migration_risk_assessment_with_optional_methods(self, tmp_path):
        """Test risk assessment using optional methods."""
        from gtd_manager.migrations.base import Migration
        from gtd_manager.migrations.manager import MigrationManager

        class RiskyMigration(Migration):
            version = 3

            def upgrade(self, conn):
                pass

            def downgrade(self, conn):
                pass

            def involves_data_loss(self):
                return True

            def get_risk_factors(self):
                return ["Column removal", "Table restructuring"]

        db_path = tmp_path / "risk_assessment_test.db"
        manager = MigrationManager(db_path)

        migration = RiskyMigration()
        assessment = manager.assess_migration_risk(migration)

        assert assessment.level == "HIGH"
        assert assessment.backup_recommended is True
        assert "data loss" in assessment.warnings[0].lower()
        assert "Column removal" in assessment.warnings
        assert "Table restructuring" in assessment.warnings

    def test_migration_dependency_validation(self, tmp_path):
        """Test migration dependency validation."""
        from gtd_manager.migrations.base import Migration
        from gtd_manager.migrations.manager import MigrationManager

        class DependentMigration(Migration):
            version = 4

            def upgrade(self, conn):
                pass

            def downgrade(self, conn):
                pass

            def get_dependencies(self):
                return [1, 2, 3]  # Depends on versions 1, 2, 3

        db_path = tmp_path / "dependency_test.db"
        manager = MigrationManager(db_path)

        migration = DependentMigration()

        # Test dependency validation
        dependencies = migration.get_dependencies()
        assert dependencies == [1, 2, 3]

        # Test dependency validation method
        are_met = manager.validate_migration_dependencies(migration)
        # Should return False since we don't have versions 2, 3 applied
        assert are_met is False

    def test_migration_precondition_validation(self, tmp_path):
        """Test migration precondition validation."""
        from gtd_manager.migrations.base import Migration
        from gtd_manager.migrations.manager import MigrationManager

        class ConditionalMigration(Migration):
            version = 5

            def upgrade(self, conn):
                pass

            def downgrade(self, conn):
                pass

            def validate_preconditions(self):
                # Custom precondition - check if certain table exists
                return True  # Simplified for test

        db_path = tmp_path / "precondition_test.db"
        manager = MigrationManager(db_path)

        migration = ConditionalMigration()

        # Test precondition validation
        preconditions_met = migration.validate_preconditions()
        assert preconditions_met is True

        # Test manager's precondition validation
        can_apply = manager.validate_migration_preconditions(migration)
        assert can_apply is True

    def test_migration_duration_estimation(self, tmp_path):
        """Test migration duration estimation."""
        from gtd_manager.migrations.base import Migration

        class TimedMigration(Migration):
            version = 6

            def upgrade(self, conn):
                pass

            def downgrade(self, conn):
                pass

            def get_estimated_duration(self):
                return 10000  # 10 seconds in milliseconds

        migration = TimedMigration()

        estimated_duration = migration.get_estimated_duration()
        assert estimated_duration == 10000


class TestSchemaValidation:
    """Test database schema validation and constraint enforcement."""

    def test_schema_version_tracking(self, tmp_path):
        """Test that schema version is properly tracked."""
        from gtd_manager.database import init_database

        db_path = tmp_path / "version_test.db"
        init_database(db_path)

        with sqlite3.connect(db_path) as conn:
            # Verify schema_version table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            )
            assert cursor.fetchone() is not None

            # Verify initial version is set
            cursor = conn.execute(
                "SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1"
            )
            assert cursor.fetchone()[0] == 1

    def test_foreign_key_constraint_enforcement(self, tmp_path):
        """Test that foreign key constraints are properly enforced."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection

        db_path = tmp_path / "fk_test.db"

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Create tables with foreign key relationship
                conn.execute("""
                    CREATE TABLE projects (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE actions (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        project_id TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    )
                """)

                # Insert valid relationship
                conn.execute(
                    "INSERT INTO projects (id, title) VALUES ('proj-1', 'Test Project')"
                )
                conn.execute(
                    "INSERT INTO actions (id, title, project_id) VALUES ('act-1', 'Test Action', 'proj-1')"
                )

                # Try to insert invalid relationship - should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute(
                        "INSERT INTO actions (id, title, project_id) VALUES ('act-2', 'Invalid Action', 'nonexistent')"
                    )
                    conn.commit()

    def test_check_constraint_validation(self, tmp_path):
        """Test CHECK constraints for data validation."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection

        db_path = tmp_path / "check_test.db"

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                conn.execute("""
                    CREATE TABLE gtd_items (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        status TEXT DEFAULT 'inbox',
                        item_type TEXT NOT NULL,
                        CHECK (status IN ('inbox', 'clarified', 'organized', 'reviewing', 'complete', 'someday')),
                        CHECK (item_type IN ('action', 'project'))
                    )
                """)

                # Valid insert should work
                conn.execute("""
                    INSERT INTO gtd_items (id, title, status, item_type)
                    VALUES ('item-1', 'Test Item', 'inbox', 'action')
                """)

                # Invalid status should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("""
                        INSERT INTO gtd_items (id, title, status, item_type)
                        VALUES ('item-2', 'Bad Status', 'invalid_status', 'action')
                    """)
                    conn.commit()

                # Invalid item_type should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("""
                        INSERT INTO gtd_items (id, title, status, item_type)
                        VALUES ('item-3', 'Bad Type', 'inbox', 'invalid_type')
                    """)
                    conn.commit()


class TestGTDItemOperations:
    """Test GTD item CRUD operations and constraint validation."""

    def test_create_gtd_action_item(self, tmp_path):
        """Test creating a basic GTD action item."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration first
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Create a basic action item
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type, status)
                    VALUES ('action-1', 'Call client about project', 'action', 'inbox')
                """)
                conn.commit()

                # Verify item was created
                cursor = conn.execute("SELECT * FROM gtd_items WHERE id = 'action-1'")
                item = cursor.fetchone()

                assert item is not None
                assert item["title"] == "Call client about project"
                assert item["item_type"] == "action"
                assert item["status"] == "inbox"
                assert item["created_at"] is not None

    def test_create_gtd_project_item(self, tmp_path):
        """Test creating a GTD project item."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Create a project item
                conn.execute("""
                    INSERT INTO gtd_items (
                        id, title, item_type, status, description, success_criteria
                    ) VALUES (
                        'project-1',
                        'Launch new website',
                        'project',
                        'clarified',
                        'Complete redesign and launch of company website',
                        'Website is live and receiving traffic'
                    )
                """)
                conn.commit()

                # Verify project was created
                cursor = conn.execute("SELECT * FROM gtd_items WHERE id = 'project-1'")
                project = cursor.fetchone()

                assert project is not None
                assert project["title"] == "Launch new website"
                assert project["item_type"] == "project"
                assert project["status"] == "clarified"
                assert (
                    project["description"]
                    == "Complete redesign and launch of company website"
                )
                assert (
                    project["success_criteria"]
                    == "Website is live and receiving traffic"
                )

    def test_gtd_item_status_constraint(self, tmp_path):
        """Test that GTD item status must be valid."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Valid status should work
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type, status)
                    VALUES ('action-1', 'Valid item', 'action', 'inbox')
                """)

                # Invalid status should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("""
                        INSERT INTO gtd_items (id, title, item_type, status)
                        VALUES ('action-2', 'Invalid item', 'action', 'invalid_status')
                    """)
                    conn.commit()

    def test_gtd_item_type_constraint(self, tmp_path):
        """Test that GTD item type must be 'action' or 'project'."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Valid types should work
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type)
                    VALUES ('action-1', 'Action item', 'action')
                """)
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type)
                    VALUES ('project-1', 'Project item', 'project')
                """)

                # Invalid type should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("""
                        INSERT INTO gtd_items (id, title, item_type)
                        VALUES ('invalid-1', 'Invalid item', 'invalid_type')
                    """)
                    conn.commit()

    def test_gtd_item_energy_level_constraint(self, tmp_path):
        """Test that energy level must be between 1-5 or NULL."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Valid energy levels should work
                for energy_level in [1, 2, 3, 4, 5, None]:
                    conn.execute(
                        """
                        INSERT INTO gtd_items (id, title, item_type, energy_level)
                        VALUES (?, 'Test item', 'action', ?)
                    """,
                        (f"action-{energy_level or 'null'}", energy_level),
                    )

                # Invalid energy levels should fail
                for invalid_level in [0, 6, -1, 10]:
                    with pytest.raises(sqlite3.IntegrityError):
                        conn.execute(
                            """
                            INSERT INTO gtd_items (id, title, item_type, energy_level)
                            VALUES (?, 'Invalid item', 'action', ?)
                        """,
                            (f"action-invalid-{invalid_level}", invalid_level),
                        )
                        conn.commit()

    def test_gtd_item_project_hierarchy(self, tmp_path):
        """Test project-action hierarchy with foreign key relationship."""
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Create a project first
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type, status)
                    VALUES ('project-1', 'Website Launch', 'project', 'clarified')
                """)

                # Create actions under the project
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type, status, project_id)
                    VALUES ('action-1', 'Design homepage', 'action', 'inbox', 'project-1')
                """)
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type, status, project_id)
                    VALUES ('action-2', 'Write content', 'action', 'inbox', 'project-1')
                """)
                conn.commit()

                # Verify hierarchy
                cursor = conn.execute("""
                    SELECT title FROM gtd_items
                    WHERE project_id = 'project-1'
                    ORDER BY title
                """)
                actions = cursor.fetchall()

                assert len(actions) == 2
                assert actions[0]["title"] == "Design homepage"
                assert actions[1]["title"] == "Write content"

                # Try to reference non-existent project - should fail
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("""
                        INSERT INTO gtd_items (id, title, item_type, project_id)
                        VALUES ('action-3', 'Invalid action', 'action', 'nonexistent-project')
                    """)
                    conn.commit()

    def test_gtd_item_automatic_timestamp_update(self, tmp_path):
        """Test that updated_at timestamp is automatically updated."""
        import time
        from unittest.mock import patch

        from gtd_manager.database import get_db_connection
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "gtd_test.db"

        # Apply schema migration
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with patch("gtd_manager.database.get_database_path") as mock_path:
            mock_path.return_value = db_path

            with get_db_connection() as conn:
                # Create item
                conn.execute("""
                    INSERT INTO gtd_items (id, title, item_type)
                    VALUES ('action-1', 'Test item', 'action')
                """)
                conn.commit()

                # Get initial timestamps
                cursor = conn.execute("""
                    SELECT created_at, updated_at FROM gtd_items WHERE id = 'action-1'
                """)
                initial_timestamps = cursor.fetchone()

                # Wait a moment and update
                time.sleep(0.1)
                conn.execute("""
                    UPDATE gtd_items SET title = 'Updated title'
                    WHERE id = 'action-1'
                """)
                conn.commit()

                # Check timestamps
                cursor = conn.execute("""
                    SELECT created_at, updated_at FROM gtd_items WHERE id = 'action-1'
                """)
                updated_timestamps = cursor.fetchone()

                # created_at should stay the same, updated_at should change
                assert (
                    updated_timestamps["created_at"] == initial_timestamps["created_at"]
                )
                assert (
                    updated_timestamps["updated_at"] > initial_timestamps["updated_at"]
                )


class TestContextOperations:
    """Test contexts table and action_contexts relationship operations."""

    def test_create_context(self, tmp_path):
        """Test basic context creation."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "contexts_test.db"
        init_database(db_path)

        # Apply migration to create tables
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        # Test context creation
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")

            # Create a context
            conn.execute("""
                INSERT INTO contexts (id, name, description)
                VALUES ('context-home', 'Home', 'Tasks that can be done at home')
            """)
            conn.commit()

            # Verify context was created
            cursor = conn.execute("SELECT * FROM contexts WHERE id = 'context-home'")
            context = cursor.fetchone()

            assert context["id"] == "context-home"
            assert context["name"] == "Home"
            assert context["description"] == "Tasks that can be done at home"
            assert context["created_at"] is not None

    def test_context_name_uniqueness(self, tmp_path):
        """Test that context names must be unique."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "contexts_unique_test.db"
        init_database(db_path)

        # Apply migration to create tables
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create first context
            conn.execute("""
                INSERT INTO contexts (id, name, description)
                VALUES ('context-1', 'Office', 'Work tasks')
            """)
            conn.commit()

            # Try to create second context with same name - should fail
            with pytest.raises(
                sqlite3.IntegrityError, match="UNIQUE constraint failed"
            ):
                conn.execute("""
                    INSERT INTO contexts (id, name, description)
                    VALUES ('context-2', 'Office', 'Different description')
                """)
                conn.commit()

    def test_action_context_relationship(self, tmp_path):
        """Test many-to-many relationship between actions and contexts."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "action_contexts_test.db"
        init_database(db_path)

        # Apply migration to create tables
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")

            # Create action and contexts
            conn.execute("""
                INSERT INTO gtd_items (id, title, status, item_type)
                VALUES ('action-1', 'Buy groceries', 'clarified', 'action')
            """)

            conn.execute("""
                INSERT INTO contexts (id, name, description)
                VALUES ('context-errands', 'Errands', 'Tasks requiring going out')
            """)

            conn.execute("""
                INSERT INTO contexts (id, name, description)
                VALUES ('context-weekend', 'Weekend', 'Weekend activities')
            """)
            conn.commit()

            # Link action to multiple contexts
            conn.execute("""
                INSERT INTO action_contexts (action_id, context_id)
                VALUES ('action-1', 'context-errands')
            """)

            conn.execute("""
                INSERT INTO action_contexts (action_id, context_id)
                VALUES ('action-1', 'context-weekend')
            """)
            conn.commit()

            # Verify relationships exist
            cursor = conn.execute("""
                SELECT c.name FROM action_contexts ac
                JOIN contexts c ON ac.context_id = c.id
                WHERE ac.action_id = 'action-1'
                ORDER BY c.name
            """)
            context_names = [row["name"] for row in cursor.fetchall()]

            assert context_names == ["Errands", "Weekend"]

    def test_action_context_foreign_key_constraints(self, tmp_path):
        """Test foreign key constraints on action_contexts table."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "fk_constraints_test.db"
        init_database(db_path)

        # Apply migration to create tables
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Try to create relationship with non-existent action - should fail
            with pytest.raises(
                sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"
            ):
                conn.execute("""
                    INSERT INTO action_contexts (action_id, context_id)
                    VALUES ('non-existent-action', 'some-context')
                """)
                conn.commit()

            # Try to create relationship with non-existent context - should fail
            with pytest.raises(
                sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"
            ):
                conn.execute("""
                    INSERT INTO action_contexts (action_id, context_id)
                    VALUES ('some-action', 'non-existent-context')
                """)
                conn.commit()

    def test_action_context_cascade_deletion(self, tmp_path):
        """Test cascade deletion when actions or contexts are deleted."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "cascade_test.db"
        init_database(db_path)

        # Apply migration to create tables
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create action and context with relationship
            conn.execute("""
                INSERT INTO gtd_items (id, title, status, item_type)
                VALUES ('action-1', 'Test action', 'inbox', 'action')
            """)

            conn.execute("""
                INSERT INTO contexts (id, name)
                VALUES ('context-1', 'Test context')
            """)

            conn.execute("""
                INSERT INTO action_contexts (action_id, context_id)
                VALUES ('action-1', 'context-1')
            """)
            conn.commit()

            # Verify relationship exists
            cursor = conn.execute("SELECT COUNT(*) FROM action_contexts")
            assert cursor.fetchone()[0] == 1

            # Delete action - should cascade delete relationship
            conn.execute("DELETE FROM gtd_items WHERE id = 'action-1'")
            conn.commit()

            # Verify relationship was deleted
            cursor = conn.execute("SELECT COUNT(*) FROM action_contexts")
            assert cursor.fetchone()[0] == 0

    def test_action_context_primary_key_constraint(self, tmp_path):
        """Test primary key constraint prevents duplicate relationships."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "pk_constraint_test.db"
        init_database(db_path)

        # Apply migration to create tables
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create action and context
            conn.execute("""
                INSERT INTO gtd_items (id, title, status, item_type)
                VALUES ('action-1', 'Test action', 'inbox', 'action')
            """)

            conn.execute("""
                INSERT INTO contexts (id, name)
                VALUES ('context-1', 'Test context')
            """)

            # Create relationship
            conn.execute("""
                INSERT INTO action_contexts (action_id, context_id)
                VALUES ('action-1', 'context-1')
            """)
            conn.commit()

            # Try to create duplicate relationship - should fail
            with pytest.raises(
                sqlite3.IntegrityError, match="UNIQUE constraint failed"
            ):
                conn.execute("""
                    INSERT INTO action_contexts (action_id, context_id)
                    VALUES ('action-1', 'context-1')
                """)
                conn.commit()


class TestDatabaseIndexes:
    """Test database indexes and query performance."""

    def test_gtd_items_indexes_exist(self, tmp_path):
        """Test that required indexes exist on gtd_items table."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "indexes_test.db"
        init_database(db_path)

        # Apply migration to create tables and indexes
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            # Check for expected indexes on gtd_items table
            cursor = conn.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND tbl_name='gtd_items'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            # Verify expected indexes exist
            expected_indexes = [
                "CREATE INDEX idx_gtd_items_created ON gtd_items(created_at)",
                "CREATE INDEX idx_gtd_items_project ON gtd_items(project_id)",
                "CREATE INDEX idx_gtd_items_status ON gtd_items(status)",
                "CREATE INDEX idx_gtd_items_type ON gtd_items(item_type)",
            ]

            for expected_index in expected_indexes:
                assert expected_index in indexes, f"Missing index: {expected_index}"

    def test_contexts_indexes_exist(self, tmp_path):
        """Test that required indexes exist on contexts table."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "contexts_indexes_test.db"
        init_database(db_path)

        # Apply migration to create tables and indexes
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            # Check for expected indexes on contexts table
            cursor = conn.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND tbl_name='contexts'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            # Verify contexts name index exists
            expected_index = "CREATE INDEX idx_contexts_name ON contexts(name)"
            assert expected_index in indexes, f"Missing index: {expected_index}"

    def test_stakeholders_indexes_exist(self, tmp_path):
        """Test that required indexes exist on stakeholders table."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "stakeholders_indexes_test.db"
        init_database(db_path)

        # Apply migration to create tables and indexes
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            # Check for expected indexes on stakeholders table
            cursor = conn.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='index' AND tbl_name='stakeholders'
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            # Verify expected stakeholder indexes exist
            expected_indexes = [
                "CREATE INDEX idx_stakeholders_email ON stakeholders(email)",
                "CREATE INDEX idx_stakeholders_org ON stakeholders(organization_id)",
            ]

            for expected_index in expected_indexes:
                assert expected_index in indexes, f"Missing index: {expected_index}"

    def test_query_performance_with_status_index(self, tmp_path):
        """Test that status queries use the index for better performance."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "performance_test.db"
        init_database(db_path)

        # Apply migration to create tables and indexes
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            # Create test data
            for i in range(100):
                status = (
                    "inbox"
                    if i % 4 == 0
                    else "clarified"
                    if i % 4 == 1
                    else "organized"
                    if i % 4 == 2
                    else "complete"
                )
                conn.execute(
                    """
                    INSERT INTO gtd_items (id, title, status, item_type)
                    VALUES (?, ?, ?, 'action')
                """,
                    (f"action-{i}", f"Task {i}", status),
                )
            conn.commit()

            # Query with EXPLAIN QUERY PLAN to verify index usage
            cursor = conn.execute("""
                EXPLAIN QUERY PLAN
                SELECT * FROM gtd_items WHERE status = 'inbox'
            """)
            query_plan = cursor.fetchall()

            # Check that the query plan mentions using the status index
            plan_text = " ".join([str(row) for row in query_plan])
            assert (
                "idx_gtd_items_status" in plan_text
            ), f"Status index not used in query plan: {query_plan}"

    def test_query_performance_with_project_hierarchy_index(self, tmp_path):
        """Test that project hierarchy queries use the project_id index."""
        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "hierarchy_performance_test.db"
        init_database(db_path)

        # Apply migration to create tables and indexes
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            # Create test data with project hierarchy
            conn.execute("""
                INSERT INTO gtd_items (id, title, status, item_type, success_criteria)
                VALUES ('project-1', 'Main Project', 'organized', 'project', 'All sub-actions completed')
            """)

            # Create many actions under the project
            for i in range(50):
                conn.execute(
                    """
                    INSERT INTO gtd_items (id, title, status, item_type, project_id)
                    VALUES (?, ?, 'clarified', 'action', 'project-1')
                """,
                    (f"action-{i}", f"Project Task {i}"),
                )
            conn.commit()

            # Query with EXPLAIN QUERY PLAN to verify index usage for project hierarchy
            cursor = conn.execute("""
                EXPLAIN QUERY PLAN
                SELECT * FROM gtd_items WHERE project_id = 'project-1'
            """)
            query_plan = cursor.fetchall()

            # Check that the query plan mentions using the project index
            plan_text = " ".join([str(row) for row in query_plan])
            assert (
                "idx_gtd_items_project" in plan_text
            ), f"Project index not used in query plan: {query_plan}"

    def test_query_performance_with_date_range_index(self, tmp_path):
        """Test that date range queries use the created_at index."""
        import datetime

        from gtd_manager.database import init_database
        from gtd_manager.migrations.initial_schema import InitialSchemaMigration
        from gtd_manager.migrations.manager import MigrationManager

        db_path = tmp_path / "date_performance_test.db"
        init_database(db_path)

        # Apply migration to create tables and indexes
        manager = MigrationManager(db_path)
        migration = InitialSchemaMigration()
        manager.apply_migration(migration, target_version=1)

        with sqlite3.connect(db_path) as conn:
            # Create test data with various creation dates
            base_date = datetime.datetime.now()
            for i in range(100):
                created_at = base_date - datetime.timedelta(days=i)
                conn.execute(
                    """
                    INSERT INTO gtd_items (id, title, status, item_type, created_at)
                    VALUES (?, ?, 'inbox', 'action', ?)
                """,
                    (f"action-{i}", f"Task {i}", created_at.isoformat()),
                )
            conn.commit()

            # Query with EXPLAIN QUERY PLAN to verify index usage for date ranges
            one_week_ago = (base_date - datetime.timedelta(days=7)).isoformat()
            cursor = conn.execute(
                """
                EXPLAIN QUERY PLAN
                SELECT * FROM gtd_items WHERE created_at >= ?
            """,
                (one_week_ago,),
            )
            query_plan = cursor.fetchall()

            # Check that the query plan mentions using the created_at index
            plan_text = " ".join([str(row) for row in query_plan])
            assert (
                "idx_gtd_items_created" in plan_text
            ), f"Created_at index not used in query plan: {query_plan}"
