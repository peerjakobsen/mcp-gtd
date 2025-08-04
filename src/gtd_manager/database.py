"""
Database management for GTD Manager MCP Server.

Provides smart database path detection and connection management
optimized for Claude Desktop MCP server deployment scenarios.
"""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def get_database_path() -> Path:
    """
    Determine appropriate database path based on deployment environment.

    Priority order:
    1. MCP_GTD_DB_PATH environment variable (highest priority)
    2. Detect uvx/cache environments or system installations → ~/.local/share/mcp-gtd/
    3. Development/local installs → ./data.db

    Returns:
        Path to the database file with parent directories created if needed
    """
    # 1. Environment variable override (highest priority)
    if db_path_env := os.getenv("MCP_GTD_DB_PATH"):
        db_path = Path(db_path_env).expanduser().resolve()
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(
                "Using database path from environment variable",
                path=str(db_path),
                source="environment_variable",
            )
            return db_path
        except OSError as e:
            logger.warning(
                "Cannot create database directory from environment variable, falling back",
                path=str(db_path),
                error=str(e),
                fallback_reason="permission_error",
            )

    # 2. Detect uvx/cache environments or system installations
    current_file_str = str(Path(__file__))
    if ".cache" in current_file_str or "site-packages" in current_file_str:
        try:
            home_db_dir = Path.home() / ".local" / "share" / "mcp-gtd"
            home_db_dir.mkdir(parents=True, exist_ok=True)
            db_path = home_db_dir / "data.db"
            logger.info(
                "Using user data directory for database",
                path=str(db_path),
                source="user_data_directory",
            )
            return db_path
        except OSError as e:
            logger.warning(
                "Cannot create user data directory, falling back to development path",
                error=str(e),
                fallback_reason="permission_error",
            )

    # 3. Development/local installs - project root
    try:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "data.db"
        logger.info(
            "Using development database path",
            path=str(db_path),
            source="development_mode",
        )
        return db_path
    except Exception as e:
        # Last resort fallback
        logger.error(
            "All database path detection methods failed, using current directory",
            error=str(e),
            fallback_path="./data.db",
        )
        return Path("./data.db").resolve()


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Get database connection with proper error handling and configuration.

    Yields:
        SQLite connection with proper configuration and error handling
    """
    db_path = get_database_path()

    # Initialize database if it doesn't exist
    if not db_path.exists():
        logger.info(
            "Database file not found, initializing new database", path=str(db_path)
        )
        init_database(db_path)

    conn = None
    try:
        conn = sqlite3.connect(db_path)

        # Configure connection
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row

        logger.debug("Database connection established", path=str(db_path))
        yield conn

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(
            "Database operation failed",
            error=str(e),
            error_type=type(e).__name__,
            path=str(db_path),
        )
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(
            "Unexpected error in database operation",
            error=str(e),
            error_type=type(e).__name__,
            path=str(db_path),
        )
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


def init_database(db_path: Path) -> None:
    """
    Initialize database with basic schema and constraints.

    Args:
        db_path: Path to the database file to initialize
    """
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Create schema version tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert initial version if not exists
            conn.execute("""
                INSERT OR IGNORE INTO schema_version (version)
                VALUES (1)
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_schema_version_applied_at
                ON schema_version(applied_at)
            """)

            conn.commit()

            logger.info(
                "Database initialized successfully", path=str(db_path), schema_version=1
            )

    except sqlite3.Error as e:
        logger.error(
            "Failed to initialize database",
            path=str(db_path),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
    except OSError as e:
        logger.error(
            "Failed to create database directory",
            path=str(db_path.parent),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise
