"""
Repository pattern implementation for GTD Manager domain models.

This module provides the data access layer for GTD entities using the repository pattern.
Repositories handle database operations, validation, and business rule enforcement.

Key Features:
- Abstract base repository with common CRUD operations
- Concrete repositories for each domain entity
- Database transaction management
- Business rule validation
- RACI constraint enforcement
- GTD workflow query methods
"""

import re
import sqlite3
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

import structlog

from .errors import (
    GTDDatabaseError,
    GTDDuplicateError,
    GTDNotFoundError,
    GTDValidationError,
)
from .models import (
    Action,
    Context,
    GTDItem,
    GTDItemStakeholder,
    GTDStatus,
    Project,
    RACIRole,
    Stakeholder,
)

logger = structlog.get_logger(__name__)

# Type variable for generic repository operations
T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):  # noqa: UP046
    """
    Abstract base repository providing common database operations.

    All concrete repositories inherit from this class and implement
    the abstract methods for their specific entity type.
    """

    def __init__(self, connection: sqlite3.Connection):
        """Initialize repository with database connection."""
        self.connection = connection

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create new entity in database."""
        pass

    @abstractmethod
    def read(self, entity_id: str) -> T:
        """Read entity from database by ID."""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity in database."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """Delete entity from database by ID."""
        pass

    @abstractmethod
    def list_all(self) -> list[T]:
        """List all entities of this type."""
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """Check if entity exists in database."""
        pass

    def validate_before_save(self, entity: T) -> None:
        """Override in subclasses for entity-specific validation."""
        # Default implementation does nothing - subclasses override as needed
        return

    def validate_business_rules(self, entity: T) -> None:
        """Override in subclasses for business rule validation."""
        # Default implementation does nothing - subclasses override as needed
        return


class GTDItemRepository(BaseRepository[GTDItem]):
    """Repository for GTDItem entities (Actions and Projects)."""

    def create(self, entity: GTDItem) -> GTDItem:
        """Create new GTDItem in database."""
        self.validate_before_save(entity)
        self.validate_business_rules(entity)

        try:
            # Determine item type
            item_type = "action" if isinstance(entity, Action) else "project"

            # Handle Action-specific fields
            due_date = getattr(entity, "due_date", None)
            energy_level = getattr(entity, "energy_level", None)
            project_id = getattr(entity, "project_id", None)

            # Handle Project-specific fields
            success_criteria = getattr(entity, "success_criteria", None)

            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO gtd_items (
                    id, title, description, status, item_type,
                    created_at, updated_at, completed_at,
                    due_date, energy_level, project_id, success_criteria
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entity.id,
                    entity.title,
                    entity.description,
                    entity.status.value,
                    item_type,
                    entity.created_at.isoformat(),
                    entity.updated_at.isoformat(),
                    entity.completed_at.isoformat() if entity.completed_at else None,
                    due_date.isoformat() if due_date else None,
                    energy_level,
                    project_id,
                    success_criteria,
                ),
            )

            self.connection.commit()

            logger.info(
                "GTDItem created",
                entity_id=entity.id,
                item_type=item_type,
                title=entity.title,
            )

            return entity

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to create GTDItem", error=str(e), entity_id=entity.id)
            raise GTDDatabaseError(f"Failed to create GTDItem: {e}") from e

    def read(self, entity_id: str) -> GTDItem:
        """Read GTDItem from database by ID."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                WHERE id = ?
            """,
                (entity_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise GTDNotFoundError(f"GTDItem with ID '{entity_id}' not found")

            return self._row_to_entity(row)

        except sqlite3.Error as e:
            logger.error("Failed to read GTDItem", error=str(e), entity_id=entity_id)
            raise GTDDatabaseError(f"Failed to read GTDItem: {e}") from e

    def update(self, entity: GTDItem) -> GTDItem:
        """Update existing GTDItem in database."""
        if not self.exists(entity.id):
            raise GTDNotFoundError(f"GTDItem with ID '{entity.id}' not found")

        self.validate_before_save(entity)
        self.validate_business_rules(entity)

        try:
            # Update timestamp
            entity.updated_at = datetime.now(UTC)

            # Get type-specific fields
            due_date = getattr(entity, "due_date", None)
            energy_level = getattr(entity, "energy_level", None)
            project_id = getattr(entity, "project_id", None)
            success_criteria = getattr(entity, "success_criteria", None)

            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE gtd_items SET
                    title = ?, description = ?, status = ?,
                    updated_at = ?, completed_at = ?,
                    due_date = ?, energy_level = ?, project_id = ?, success_criteria = ?
                WHERE id = ?
            """,
                (
                    entity.title,
                    entity.description,
                    entity.status.value,
                    entity.updated_at.isoformat(),
                    entity.completed_at.isoformat() if entity.completed_at else None,
                    due_date.isoformat() if due_date else None,
                    energy_level,
                    project_id,
                    success_criteria,
                    entity.id,
                ),
            )

            self.connection.commit()

            logger.info("GTDItem updated", entity_id=entity.id, title=entity.title)
            return entity

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to update GTDItem", error=str(e), entity_id=entity.id)
            raise GTDDatabaseError(f"Failed to update GTDItem: {e}") from e

    def delete(self, entity_id: str) -> None:
        """Delete GTDItem from database by ID."""
        if not self.exists(entity_id):
            raise GTDNotFoundError(f"GTDItem with ID '{entity_id}' not found")

        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM gtd_items WHERE id = ?", (entity_id,))
            self.connection.commit()

            logger.info("GTDItem deleted", entity_id=entity_id)

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to delete GTDItem", error=str(e), entity_id=entity_id)
            raise GTDDatabaseError(f"Failed to delete GTDItem: {e}") from e

    def list_all(self) -> list[GTDItem]:
        """List all GTDItems."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                ORDER BY created_at DESC
            """)

            return [self._row_to_entity(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error("Failed to list GTDItems", error=str(e))
            raise GTDDatabaseError(f"Failed to list GTDItems: {e}") from e

    def exists(self, entity_id: str) -> bool:
        """Check if GTDItem exists in database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM gtd_items WHERE id = ?", (entity_id,))
            return cursor.fetchone() is not None

        except sqlite3.Error as e:
            logger.error(
                "Failed to check GTDItem existence", error=str(e), entity_id=entity_id
            )
            raise GTDDatabaseError(f"Failed to check GTDItem existence: {e}") from e

    def list_by_status(self, status: GTDStatus) -> list[GTDItem]:
        """List GTDItems filtered by status."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                WHERE status = ?
                ORDER BY created_at DESC
            """,
                (status.value,),
            )

            return [self._row_to_entity(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(
                "Failed to list GTDItems by status", error=str(e), status=status.value
            )
            raise GTDDatabaseError(f"Failed to list GTDItems by status: {e}") from e

    def list_actions_by_project(self, project_id: str) -> list[Action]:
        """List Actions that belong to specific Project."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                WHERE project_id = ? AND item_type = 'action'
                ORDER BY created_at DESC
            """,
                (project_id,),
            )

            return [self._row_to_action(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(
                "Failed to list actions by project", error=str(e), project_id=project_id
            )
            raise GTDDatabaseError(f"Failed to list actions by project: {e}") from e

    def list_next_actions(self) -> list[Action]:
        """List next actions (organized status, not complete)."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                WHERE status = ? AND item_type = 'action'
                ORDER BY created_at DESC
            """,
                (GTDStatus.ORGANIZED.value,),
            )

            return [self._row_to_action(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error("Failed to list next actions", error=str(e))
            raise GTDDatabaseError(f"Failed to list next actions: {e}") from e

    def list_next_actions_for_stakeholder(self, stakeholder_id: str) -> list[Action]:
        """List next actions assigned to specific stakeholder."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT g.id, g.title, g.description, g.status, g.item_type,
                       g.created_at, g.updated_at, g.completed_at,
                       g.due_date, g.energy_level, g.project_id, g.success_criteria
                FROM gtd_items g
                JOIN gtd_item_stakeholders gis ON g.id = gis.gtd_item_id
                WHERE gis.stakeholder_id = ?
                  AND g.status = ?
                  AND g.item_type = 'action'
                  AND gis.raci_role IN ('accountable', 'responsible')
                ORDER BY g.energy_level DESC, g.created_at ASC
            """,
                (stakeholder_id, GTDStatus.ORGANIZED.value),
            )

            return [self._row_to_action(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(
                "Failed to list next actions for stakeholder",
                error=str(e),
                stakeholder_id=stakeholder_id,
            )
            raise GTDDatabaseError(
                f"Failed to list next actions for stakeholder: {e}"
            ) from e

    def list_actions_by_energy_level(
        self, min_energy: int = 1, max_energy: int = 5
    ) -> list[Action]:
        """List actions filtered by energy level range."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                WHERE item_type = 'action'
                  AND energy_level >= ?
                  AND energy_level <= ?
                  AND status IN ('organized', 'reviewing')
                ORDER BY energy_level DESC, due_date ASC NULLS LAST
            """,
                (min_energy, max_energy),
            )

            return [self._row_to_action(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error("Failed to list actions by energy level", error=str(e))
            raise GTDDatabaseError(
                f"Failed to list actions by energy level: {e}"
            ) from e

    def get_project_completion_stats(self, project_id: str) -> dict[str, Any]:
        """Get detailed completion statistics for a project."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_actions,
                    SUM(CASE WHEN status IN ('organized', 'reviewing') THEN 1 ELSE 0 END) as active_actions,
                    SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as completed_actions,
                    SUM(CASE WHEN status = 'inbox' THEN 1 ELSE 0 END) as inbox_actions,
                    AVG(CAST(energy_level AS FLOAT)) as avg_energy_level,
                    MIN(created_at) as project_start_date,
                    MAX(updated_at) as last_activity_date,
                    ROUND(
                        (SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                        1
                    ) as completion_percentage
                FROM gtd_items
                WHERE project_id = ? AND item_type = 'action'
            """,
                (project_id,),
            )

            row = cursor.fetchone()
            if row:
                stats = dict(row)
                # Convert timestamps to proper format
                if stats["project_start_date"]:
                    stats["project_start_date"] = datetime.fromisoformat(
                        stats["project_start_date"]
                    )
                if stats["last_activity_date"]:
                    stats["last_activity_date"] = datetime.fromisoformat(
                        stats["last_activity_date"]
                    )
                return stats
            return {}

        except sqlite3.Error as e:
            logger.error(
                "Failed to get project completion stats",
                error=str(e),
                project_id=project_id,
            )
            raise GTDDatabaseError(
                f"Failed to get project completion stats: {e}"
            ) from e

    def list_overdue_actions(self) -> list[Action]:
        """List actions that are overdue (past due date and not complete)."""
        try:
            from datetime import date

            today = date.today().isoformat()

            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, title, description, status, item_type,
                       created_at, updated_at, completed_at,
                       due_date, energy_level, project_id, success_criteria
                FROM gtd_items
                WHERE item_type = 'action'
                  AND due_date IS NOT NULL
                  AND DATE(due_date) < ?
                  AND status != 'complete'
                ORDER BY due_date ASC
            """,
                (today,),
            )

            return [self._row_to_action(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error("Failed to list overdue actions", error=str(e))
            raise GTDDatabaseError(f"Failed to list overdue actions: {e}") from e

    def get_actions_grouped_by_project(self) -> dict[str | None, dict[str, Any]]:
        """Get actions grouped by project with summary statistics."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    COALESCE(project_id, 'standalone') as project_key,
                    project_id,
                    COUNT(*) as action_count,
                    AVG(CAST(energy_level AS FLOAT)) as avg_energy_level,
                    SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as completed_count,
                    SUM(CASE WHEN status IN ('organized', 'reviewing') THEN 1 ELSE 0 END) as active_count
                FROM gtd_items
                WHERE item_type = 'action'
                GROUP BY project_id
                ORDER BY action_count DESC
            """)

            result = {}
            for row in cursor.fetchall():
                row_dict = dict(row)
                key = row_dict["project_id"] if row_dict["project_id"] else None
                result[key] = row_dict

            return result

        except sqlite3.Error as e:
            logger.error("Failed to get actions grouped by project", error=str(e))
            raise GTDDatabaseError(
                f"Failed to get actions grouped by project: {e}"
            ) from e

    def validate_before_save(self, entity: GTDItem) -> None:
        """Validate GTDItem before saving."""
        # Basic validation
        if not entity.title or not entity.title.strip():
            raise GTDValidationError("GTDItem title cannot be empty")

        if len(entity.title.strip()) > 255:
            raise GTDValidationError("GTDItem title cannot exceed 255 characters")

        if entity.description and len(entity.description) > 2000:
            raise GTDValidationError(
                "GTDItem description cannot exceed 2000 characters"
            )

        # Action-specific validation
        if isinstance(entity, Action):
            self._validate_action_fields(entity)

        # Project-specific validation
        if isinstance(entity, Project):
            self._validate_project_fields(entity)

    def _validate_action_fields(self, action: Action) -> None:
        """Validate Action-specific fields."""
        if (
            hasattr(action, "energy_level")
            and action.energy_level is not None
            and not (1 <= action.energy_level <= 5)
        ):
            raise GTDValidationError("Action energy level must be between 1 and 5")

        # Validate due date is not in the past (with tolerance for today)
        if hasattr(action, "due_date") and action.due_date is not None:
            from datetime import date

            if action.due_date.date() < date.today():
                raise GTDValidationError("Action due date cannot be in the past")

        # Validate project_id exists if specified
        if (
            hasattr(action, "project_id")
            and action.project_id is not None
            and not self._project_exists(action.project_id)
        ):
            raise GTDValidationError(
                f"Referenced project '{action.project_id}' does not exist"
            )

    def _validate_project_fields(self, project: Project) -> None:
        """Validate Project-specific fields."""
        if project.status == GTDStatus.ORGANIZED and not getattr(
            project, "success_criteria", None
        ):
            raise GTDValidationError(
                "Project requires success criteria to be organized"
            )

        if (
            hasattr(project, "success_criteria")
            and project.success_criteria
            and len(project.success_criteria) > 1000
        ):
            raise GTDValidationError(
                "Project success criteria cannot exceed 1000 characters"
            )

    def _project_exists(self, project_id: str) -> bool:
        """Check if a project exists in the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT 1 FROM gtd_items WHERE id = ? AND item_type = 'project'",
                (project_id,),
            )
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def _row_to_action(self, row: sqlite3.Row) -> Action:
        """Convert database row to Action entity (for action-specific queries)."""
        # Parse timestamps
        created_at = datetime.fromisoformat(row["created_at"])
        updated_at = datetime.fromisoformat(row["updated_at"])
        completed_at = (
            datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        )
        due_date = datetime.fromisoformat(row["due_date"]) if row["due_date"] else None

        return Action(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=GTDStatus(row["status"]),
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            due_date=due_date,
            energy_level=row["energy_level"],
            project_id=row["project_id"],
        )

    def _row_to_entity(self, row: sqlite3.Row) -> GTDItem:
        """Convert database row to GTDItem entity."""
        # Parse timestamps
        created_at = datetime.fromisoformat(row["created_at"])
        updated_at = datetime.fromisoformat(row["updated_at"])
        completed_at = (
            datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
        )
        due_date = datetime.fromisoformat(row["due_date"]) if row["due_date"] else None

        # Create appropriate entity type
        if row["item_type"] == "action":
            return Action(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=GTDStatus(row["status"]),
                created_at=created_at,
                updated_at=updated_at,
                completed_at=completed_at,
                due_date=due_date,
                energy_level=row["energy_level"],
                project_id=row["project_id"],
            )
        else:  # project
            return Project(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                status=GTDStatus(row["status"]),
                created_at=created_at,
                updated_at=updated_at,
                completed_at=completed_at,
                success_criteria=row["success_criteria"],
            )


class ContextRepository(BaseRepository[Context]):
    """Repository for Context entities."""

    def create(self, entity: Context) -> Context:
        """Create new Context in database."""
        self.validate_before_save(entity)

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO contexts (id, name, description, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    entity.id,
                    entity.name,
                    entity.description,
                    entity.created_at.isoformat(),
                ),
            )

            self.connection.commit()

            logger.info("Context created", entity_id=entity.id, name=entity.name)
            return entity

        except sqlite3.IntegrityError as e:
            self.connection.rollback()
            if "unique" in str(e).lower():
                raise GTDDuplicateError(
                    f"Context with name '{entity.name}' already exists"
                ) from e
            raise GTDDatabaseError(f"Failed to create Context: {e}") from e
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to create Context", error=str(e), entity_id=entity.id)
            raise GTDDatabaseError(f"Failed to create Context: {e}") from e

    def read(self, entity_id: str) -> Context:
        """Read Context from database by ID."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, name, description, created_at
                FROM contexts
                WHERE id = ?
            """,
                (entity_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise GTDNotFoundError(f"Context with ID '{entity_id}' not found")

            return Context(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

        except sqlite3.Error as e:
            logger.error("Failed to read Context", error=str(e), entity_id=entity_id)
            raise GTDDatabaseError(f"Failed to read Context: {e}") from e

    def update(self, entity: Context) -> Context:
        """Update existing Context in database."""
        if not self.exists(entity.id):
            raise GTDNotFoundError(f"Context with ID '{entity.id}' not found")

        self.validate_before_save(entity)

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE contexts SET name = ?, description = ?
                WHERE id = ?
            """,
                (entity.name, entity.description, entity.id),
            )

            self.connection.commit()

            logger.info("Context updated", entity_id=entity.id, name=entity.name)
            return entity

        except sqlite3.IntegrityError as e:
            self.connection.rollback()
            if "unique" in str(e).lower():
                raise GTDDuplicateError(
                    f"Context with name '{entity.name}' already exists"
                ) from e
            raise GTDDatabaseError(f"Failed to update Context: {e}") from e
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to update Context", error=str(e), entity_id=entity.id)
            raise GTDDatabaseError(f"Failed to update Context: {e}") from e

    def delete(self, entity_id: str) -> None:
        """Delete Context from database by ID."""
        if not self.exists(entity_id):
            raise GTDNotFoundError(f"Context with ID '{entity_id}' not found")

        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM contexts WHERE id = ?", (entity_id,))
            self.connection.commit()

            logger.info("Context deleted", entity_id=entity_id)

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to delete Context", error=str(e), entity_id=entity_id)
            raise GTDDatabaseError(f"Failed to delete Context: {e}") from e

    def list_all(self) -> list[Context]:
        """List all contexts alphabetically."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, name, description, created_at
                FROM contexts
                ORDER BY name ASC
            """)

            return [
                Context(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error("Failed to list Contexts", error=str(e))
            raise GTDDatabaseError(f"Failed to list Contexts: {e}") from e

    def exists(self, entity_id: str) -> bool:
        """Check if Context exists in database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM contexts WHERE id = ?", (entity_id,))
            return cursor.fetchone() is not None

        except sqlite3.Error as e:
            logger.error(
                "Failed to check Context existence", error=str(e), entity_id=entity_id
            )
            raise GTDDatabaseError(f"Failed to check Context existence: {e}") from e

    def find_by_name(self, name: str) -> Context | None:
        """Find Context by exact name match."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, name, description, created_at
                FROM contexts
                WHERE name = ?
            """,
                (name,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return Context(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

        except sqlite3.Error as e:
            logger.error("Failed to find Context by name", error=str(e), name=name)
            raise GTDDatabaseError(f"Failed to find Context by name: {e}") from e

    def validate_before_save(self, entity: Context) -> None:
        """Validate Context before saving."""
        if not entity.name or not entity.name.strip():
            raise GTDValidationError("Context name cannot be empty")

        if not entity.name.startswith("@"):
            raise GTDValidationError("Context name must start with @ symbol")


class StakeholderRepository(BaseRepository[Stakeholder]):
    """Repository for Stakeholder entities."""

    def create(self, entity: Stakeholder) -> Stakeholder:
        """Create new Stakeholder in database."""
        self.validate_before_save(entity)

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO stakeholders (id, name, email, organization_id, team_id, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entity.id,
                    entity.name,
                    entity.email,
                    entity.organization_id,
                    getattr(entity, "team_id", None),
                    getattr(entity, "role", None),
                    entity.created_at.isoformat(),
                ),
            )

            self.connection.commit()

            logger.info(
                "Stakeholder created",
                entity_id=entity.id,
                name=entity.name,
                email=entity.email,
            )
            return entity

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(
                "Failed to create Stakeholder", error=str(e), entity_id=entity.id
            )
            raise GTDDatabaseError(f"Failed to create Stakeholder: {e}") from e

    def read(self, entity_id: str) -> Stakeholder:
        """Read Stakeholder from database by ID."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, name, email, organization_id, team_id, role, created_at
                FROM stakeholders
                WHERE id = ?
            """,
                (entity_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise GTDNotFoundError(f"Stakeholder with ID '{entity_id}' not found")

            return Stakeholder(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                organization_id=row["organization_id"],
                team_id=row["team_id"],
                role=row["role"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

        except sqlite3.Error as e:
            logger.error(
                "Failed to read Stakeholder", error=str(e), entity_id=entity_id
            )
            raise GTDDatabaseError(f"Failed to read Stakeholder: {e}") from e

    def update(self, entity: Stakeholder) -> Stakeholder:
        """Update existing Stakeholder in database."""
        if not self.exists(entity.id):
            raise GTDNotFoundError(f"Stakeholder with ID '{entity.id}' not found")

        self.validate_before_save(entity)

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE stakeholders SET
                    name = ?, email = ?, organization_id = ?, team_id = ?, role = ?
                WHERE id = ?
            """,
                (
                    entity.name,
                    entity.email,
                    entity.organization_id,
                    getattr(entity, "team_id", None),
                    getattr(entity, "role", None),
                    entity.id,
                ),
            )

            self.connection.commit()

            logger.info("Stakeholder updated", entity_id=entity.id, name=entity.name)
            return entity

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(
                "Failed to update Stakeholder", error=str(e), entity_id=entity.id
            )
            raise GTDDatabaseError(f"Failed to update Stakeholder: {e}") from e

    def delete(self, entity_id: str) -> None:
        """Delete Stakeholder from database by ID."""
        if not self.exists(entity_id):
            raise GTDNotFoundError(f"Stakeholder with ID '{entity_id}' not found")

        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM stakeholders WHERE id = ?", (entity_id,))
            self.connection.commit()

            logger.info("Stakeholder deleted", entity_id=entity_id)

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(
                "Failed to delete Stakeholder", error=str(e), entity_id=entity_id
            )
            raise GTDDatabaseError(f"Failed to delete Stakeholder: {e}") from e

    def list_all(self) -> list[Stakeholder]:
        """List all stakeholders."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, name, email, organization_id, team_id, role, created_at
                FROM stakeholders
                ORDER BY name ASC
            """)

            return [
                Stakeholder(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    organization_id=row["organization_id"],
                    team_id=row["team_id"],
                    role=row["role"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error("Failed to list Stakeholders", error=str(e))
            raise GTDDatabaseError(f"Failed to list Stakeholders: {e}") from e

    def exists(self, entity_id: str) -> bool:
        """Check if Stakeholder exists in database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM stakeholders WHERE id = ?", (entity_id,))
            return cursor.fetchone() is not None

        except sqlite3.Error as e:
            logger.error(
                "Failed to check Stakeholder existence",
                error=str(e),
                entity_id=entity_id,
            )
            raise GTDDatabaseError(f"Failed to check Stakeholder existence: {e}") from e

    def list_by_organization(self, organization_id: str) -> list[Stakeholder]:
        """List stakeholders filtered by organization."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, name, email, organization_id, team_id, role, created_at
                FROM stakeholders
                WHERE organization_id = ?
                ORDER BY name ASC
            """,
                (organization_id,),
            )

            return [
                Stakeholder(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    organization_id=row["organization_id"],
                    team_id=row["team_id"],
                    role=row["role"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error(
                "Failed to list Stakeholders by organization",
                error=str(e),
                organization_id=organization_id,
            )
            raise GTDDatabaseError(
                f"Failed to list Stakeholders by organization: {e}"
            ) from e

    def find_by_email(self, email: str) -> Stakeholder | None:
        """Find Stakeholder by email address."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT id, name, email, organization_id, team_id, role, created_at
                FROM stakeholders
                WHERE email = ?
            """,
                (email,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return Stakeholder(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                organization_id=row["organization_id"],
                team_id=row["team_id"],
                role=row["role"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

        except sqlite3.Error as e:
            logger.error(
                "Failed to find Stakeholder by email", error=str(e), email=email
            )
            raise GTDDatabaseError(f"Failed to find Stakeholder by email: {e}") from e

    def get_stakeholder_workloads(self) -> list[dict[str, Any]]:
        """Get workload analysis for all stakeholders."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    gis.stakeholder_id,
                    s.name as stakeholder_name,
                    s.email,
                    s.organization_id,
                    COUNT(*) as total_tasks,
                    AVG(CAST(g.energy_level AS FLOAT)) as avg_energy_level,
                    SUM(CASE WHEN gis.raci_role = 'accountable' THEN 1 ELSE 0 END) as accountable_count,
                    SUM(CASE WHEN gis.raci_role = 'responsible' THEN 1 ELSE 0 END) as responsible_count,
                    SUM(CASE WHEN gis.raci_role = 'consulted' THEN 1 ELSE 0 END) as consulted_count,
                    SUM(CASE WHEN gis.raci_role = 'informed' THEN 1 ELSE 0 END) as informed_count,
                    SUM(CASE WHEN g.status IN ('organized', 'reviewing') THEN 1 ELSE 0 END) as active_tasks,
                    SUM(CASE WHEN g.status = 'complete' THEN 1 ELSE 0 END) as completed_tasks
                FROM gtd_item_stakeholders gis
                JOIN stakeholders s ON gis.stakeholder_id = s.id
                JOIN gtd_items g ON gis.gtd_item_id = g.id
                GROUP BY gis.stakeholder_id, s.name, s.email, s.organization_id
                ORDER BY total_tasks DESC, s.name ASC
            """)

            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error("Failed to get stakeholder workloads", error=str(e))
            raise GTDDatabaseError(f"Failed to get stakeholder workloads: {e}") from e

    def get_cross_organizational_collaboration_stats(self) -> dict[str, Any]:
        """Get statistics on cross-organizational collaboration."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT s.organization_id) as total_organizations,
                    COUNT(DISTINCT gis.gtd_item_id) as total_collaborative_items,
                    COUNT(DISTINCT CASE
                        WHEN EXISTS (
                            SELECT 1 FROM gtd_item_stakeholders gis2
                            JOIN stakeholders s2 ON gis2.stakeholder_id = s2.id
                            WHERE gis2.gtd_item_id = gis.gtd_item_id
                            AND s2.organization_id != s.organization_id
                        ) THEN gis.gtd_item_id
                    END) as cross_org_items,
                    COUNT(DISTINCT s.id) as total_stakeholders
                FROM gtd_item_stakeholders gis
                JOIN stakeholders s ON gis.stakeholder_id = s.id
            """)

            row = cursor.fetchone()
            return dict(row) if row else {}

        except sqlite3.Error as e:
            logger.error("Failed to get cross-organizational stats", error=str(e))
            raise GTDDatabaseError(
                f"Failed to get cross-organizational stats: {e}"
            ) from e

    def validate_before_save(self, entity: Stakeholder) -> None:
        """Validate Stakeholder before saving."""
        if not entity.name or not entity.name.strip():
            raise GTDValidationError("Stakeholder name cannot be empty")

        if len(entity.name.strip()) > 100:
            raise GTDValidationError("Stakeholder name cannot exceed 100 characters")

        if not entity.email or not entity.email.strip():
            raise GTDValidationError("Stakeholder email cannot be empty")

        if len(entity.email) > 254:  # RFC 5321 limit
            raise GTDValidationError("Stakeholder email cannot exceed 254 characters")

        # Enhanced email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, entity.email):
            raise GTDValidationError("Stakeholder email format is invalid")

        # Validate email domain
        if "@" in entity.email:
            domain = entity.email.split("@")[1]
            if len(domain) > 63:  # DNS label limit
                raise GTDValidationError("Email domain name is too long")

        # Validate optional fields
        if hasattr(entity, "role") and entity.role and len(entity.role) > 100:
            raise GTDValidationError("Stakeholder role cannot exceed 100 characters")

        # Validate organization_id if provided (allow flexible ID formats for GTD use cases)
        if entity.organization_id and not entity.organization_id.strip():
            raise GTDValidationError("Organization ID cannot be empty if provided")

    def _is_valid_uuid_format(self, uuid_string: str) -> bool:
        """Check if string matches UUID format."""
        import uuid

        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False


class RACIRepository(BaseRepository[GTDItemStakeholder]):
    """Repository for RACI relationship entities."""

    def create(self, entity: GTDItemStakeholder) -> GTDItemStakeholder:
        """Create new RACI relationship in database."""
        self.validate_business_rules(entity)

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO gtd_item_stakeholders (gtd_item_id, stakeholder_id, raci_role, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    entity.gtd_item_id,
                    entity.stakeholder_id,
                    entity.raci_role.value,
                    entity.created_at.isoformat(),
                ),
            )

            self.connection.commit()

            logger.info(
                "RACI relationship created",
                gtd_item_id=entity.gtd_item_id,
                stakeholder_id=entity.stakeholder_id,
                raci_role=entity.raci_role.value,
            )
            return entity

        except sqlite3.IntegrityError as e:
            self.connection.rollback()
            error_str = str(e).lower()
            if "accountable" in error_str or "check" in error_str:
                raise GTDDatabaseError(
                    "Only one Accountable allowed per GTD item"
                ) from e
            raise GTDDatabaseError(f"Failed to create RACI relationship: {e}") from e
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to create RACI relationship", error=str(e))
            raise GTDDatabaseError(f"Failed to create RACI relationship: {e}") from e

    def read(self, entity_id: str) -> GTDItemStakeholder:
        """Not implemented for RACI relationships (use composite key methods)."""
        raise NotImplementedError(
            "Use list_by_gtd_item_and_role or other query methods"
        )

    def update(self, entity: GTDItemStakeholder) -> GTDItemStakeholder:
        """Update existing RACI relationship in database."""
        self.validate_business_rules(entity)

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE gtd_item_stakeholders SET raci_role = ?
                WHERE gtd_item_id = ? AND stakeholder_id = ?
            """,
                (entity.raci_role.value, entity.gtd_item_id, entity.stakeholder_id),
            )

            if cursor.rowcount == 0:
                raise GTDNotFoundError("RACI relationship not found")

            self.connection.commit()

            logger.info(
                "RACI relationship updated",
                gtd_item_id=entity.gtd_item_id,
                stakeholder_id=entity.stakeholder_id,
                raci_role=entity.raci_role.value,
            )
            return entity

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to update RACI relationship", error=str(e))
            raise GTDDatabaseError(f"Failed to update RACI relationship: {e}") from e

    def delete(self, entity_id: str) -> None:
        """Not implemented for RACI relationships (use composite key methods)."""
        raise NotImplementedError("Use delete_by_gtd_item_and_stakeholder method")

    def list_all(self) -> list[GTDItemStakeholder]:
        """List all RACI relationships."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT gtd_item_id, stakeholder_id, raci_role, created_at
                FROM gtd_item_stakeholders
                ORDER BY created_at DESC
            """)

            return [
                GTDItemStakeholder(
                    gtd_item_id=row["gtd_item_id"],
                    stakeholder_id=row["stakeholder_id"],
                    raci_role=RACIRole(row["raci_role"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error("Failed to list RACI relationships", error=str(e))
            raise GTDDatabaseError(f"Failed to list RACI relationships: {e}") from e

    def exists(self, entity_id: str) -> bool:
        """Not implemented for RACI relationships (use composite key methods)."""
        raise NotImplementedError("Use composite key existence checks")

    def list_by_gtd_item_and_role(
        self, gtd_item_id: str, raci_role: RACIRole
    ) -> list[GTDItemStakeholder]:
        """List RACI relationships by GTD item and role."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT gtd_item_id, stakeholder_id, raci_role, created_at
                FROM gtd_item_stakeholders
                WHERE gtd_item_id = ? AND raci_role = ?
                ORDER BY created_at DESC
            """,
                (gtd_item_id, raci_role.value),
            )

            return [
                GTDItemStakeholder(
                    gtd_item_id=row["gtd_item_id"],
                    stakeholder_id=row["stakeholder_id"],
                    raci_role=RACIRole(row["raci_role"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

        except sqlite3.Error as e:
            logger.error(
                "Failed to list RACI relationships by item and role", error=str(e)
            )
            raise GTDDatabaseError(
                f"Failed to list RACI relationships by item and role: {e}"
            ) from e

    def delete_by_gtd_item_and_stakeholder(
        self, gtd_item_id: str, stakeholder_id: str
    ) -> None:
        """Delete RACI relationship by GTD item and stakeholder IDs."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM gtd_item_stakeholders
                WHERE gtd_item_id = ? AND stakeholder_id = ?
            """,
                (gtd_item_id, stakeholder_id),
            )

            if cursor.rowcount == 0:
                raise GTDNotFoundError("RACI relationship not found")

            self.connection.commit()

            logger.info(
                "RACI relationship deleted",
                gtd_item_id=gtd_item_id,
                stakeholder_id=stakeholder_id,
            )

        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error("Failed to delete RACI relationship", error=str(e))
            raise GTDDatabaseError(f"Failed to delete RACI relationship: {e}") from e

    def validate_business_rules(self, entity: GTDItemStakeholder) -> None:
        """Validate comprehensive RACI business rules."""
        # Validate GTD item exists
        if not self._gtd_item_exists(entity.gtd_item_id):
            raise GTDValidationError(f"GTD item '{entity.gtd_item_id}' does not exist")

        # Validate stakeholder exists
        if not self._stakeholder_exists(entity.stakeholder_id):
            raise GTDValidationError(
                f"Stakeholder '{entity.stakeholder_id}' does not exist"
            )

        # Validate exactly one Accountable rule
        if entity.raci_role == RACIRole.ACCOUNTABLE:
            self._validate_single_accountable_rule(entity)

        # Validate no duplicate role assignments
        self._validate_no_duplicate_role_assignment(entity)

        # Business rule: Every GTD item should have an Accountable
        self._validate_gtd_item_has_accountable_after_creation(entity)

    def _gtd_item_exists(self, gtd_item_id: str) -> bool:
        """Check if GTD item exists."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM gtd_items WHERE id = ?", (gtd_item_id,))
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def _stakeholder_exists(self, stakeholder_id: str) -> bool:
        """Check if stakeholder exists."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM stakeholders WHERE id = ?", (stakeholder_id,))
            return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def _validate_single_accountable_rule(self, entity: GTDItemStakeholder) -> None:
        """Validate exactly one Accountable per GTD item."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM gtd_item_stakeholders
                WHERE gtd_item_id = ? AND raci_role = ? AND stakeholder_id != ?
            """,
                (entity.gtd_item_id, RACIRole.ACCOUNTABLE.value, entity.stakeholder_id),
            )

            row = cursor.fetchone()
            if row and row["count"] > 0:
                raise GTDDatabaseError("Only one Accountable allowed per GTD item")

        except sqlite3.Error as e:
            logger.error("Failed to validate single accountable rule", error=str(e))
            raise GTDDatabaseError(
                f"Failed to validate RACI business rules: {e}"
            ) from e

    def _validate_no_duplicate_role_assignment(
        self, entity: GTDItemStakeholder
    ) -> None:
        """Validate no duplicate role assignment for same stakeholder on same GTD item."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM gtd_item_stakeholders
                WHERE gtd_item_id = ? AND stakeholder_id = ? AND raci_role = ?
            """,
                (entity.gtd_item_id, entity.stakeholder_id, entity.raci_role.value),
            )

            row = cursor.fetchone()
            if row and row["count"] > 0:
                raise GTDDuplicateError(
                    f"Stakeholder already has {entity.raci_role.value} role for this GTD item"
                )

        except sqlite3.Error as e:
            logger.error("Failed to validate duplicate role assignment", error=str(e))
            raise GTDDatabaseError(
                f"Failed to validate duplicate assignment: {e}"
            ) from e

    def _validate_gtd_item_has_accountable_after_creation(
        self, entity: GTDItemStakeholder
    ) -> None:
        """Warn if GTD item will not have an Accountable after this operation."""
        # This is a soft validation - log warning but don't fail
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM gtd_item_stakeholders
                WHERE gtd_item_id = ? AND raci_role = ?
            """,
                (entity.gtd_item_id, RACIRole.ACCOUNTABLE.value),
            )

            row = cursor.fetchone()
            if row and row["count"] == 0 and entity.raci_role != RACIRole.ACCOUNTABLE:
                logger.warning(
                    "GTD item has no Accountable stakeholder",
                    gtd_item_id=entity.gtd_item_id,
                    recommendation="Consider assigning an Accountable role",
                )

        except sqlite3.Error as e:
            logger.error("Failed to validate accountable presence", error=str(e))
