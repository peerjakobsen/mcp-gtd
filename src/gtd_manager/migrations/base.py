"""Base migration class - minimal implementation for TDD."""

import sqlite3
from dataclasses import dataclass


@dataclass
class DataIntegrityResult:
    """Result of data integrity validation."""

    is_valid: bool
    row_count: int
    constraint_violations: list[str]


@dataclass
class RiskAssessment:
    """Migration risk assessment result."""

    level: str
    warnings: list[str]
    backup_recommended: bool


class Migration:
    """Minimal migration base class."""

    def upgrade(self, conn: sqlite3.Connection) -> None:
        """Upgrade the database schema."""
        raise NotImplementedError

    def downgrade(self, conn: sqlite3.Connection) -> None:
        """Downgrade the database schema."""
        raise NotImplementedError
