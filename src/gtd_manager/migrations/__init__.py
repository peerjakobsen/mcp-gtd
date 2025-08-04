"""
Database migration system for GTD Manager.

Provides schema versioning, rollback capabilities, and data protection
for safe database evolution across GTD Manager versions.
"""

from .base import Migration
from .manager import MigrationManager

__all__ = ["Migration", "MigrationManager"]
