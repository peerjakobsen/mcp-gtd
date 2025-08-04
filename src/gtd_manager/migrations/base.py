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

    def upgrade(self, _conn: sqlite3.Connection) -> None:
        """Upgrade the database schema."""
        raise NotImplementedError

    def downgrade(self, _conn: sqlite3.Connection) -> None:
        """Downgrade the database schema."""
        raise NotImplementedError

    def involves_data_loss(self) -> bool:
        """Return True if this migration might cause data loss."""
        return False

    def get_risk_factors(self) -> list[str]:
        """Return list of specific risks this migration poses."""
        return []

    def get_dependencies(self) -> list[int]:
        """Return list of migration versions this migration depends on."""
        return []

    def get_estimated_duration(self) -> int | None:
        """Return estimated duration in milliseconds, or None if unknown."""
        return None

    def validate_preconditions(self) -> bool:
        """Validate that preconditions for this migration are met."""
        return True
