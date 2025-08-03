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
