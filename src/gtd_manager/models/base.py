"""
Base GTD Item model with workflow states and stakeholder relationships.

This module provides the GTDItem base class that all GTD entities inherit from,
including support for RACI stakeholder relationships and automatic timestamp management.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from .enums import GTDStatus, RACIRole


@dataclass
class GTDItem:
    """
    Base class for all GTD items (Actions, Projects, etc.).

    Provides common functionality for workflow state management,
    timestamps, and stakeholder relationships through RACI model.

    Attributes:
        id: Unique identifier for the item
        title: Brief descriptive title
        description: Detailed description (optional)
        status: Current workflow state
        created_at: When the item was first created
        updated_at: When the item was last modified
        completed_at: When the item was marked complete (None if not complete)
    """

    title: str
    status: GTDStatus
    description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def __post_init__(self):
        """Post-initialization hook to handle status-dependent logic."""
        # Set completed_at if status is COMPLETE
        if self.status == GTDStatus.COMPLETE and self.completed_at is None:
            self.completed_at = datetime.now(UTC)

    def __setattr__(self, name: str, value) -> None:
        """Override setattr to handle automatic timestamp updates."""
        # Update updated_at timestamp when any field changes (except timestamps)
        if hasattr(self, "updated_at") and name not in ("updated_at", "completed_at"):
            object.__setattr__(self, "updated_at", datetime.now(UTC))

        # Set completed_at when status becomes COMPLETE
        if (
            name == "status"
            and value == GTDStatus.COMPLETE
            and hasattr(self, "completed_at")
        ):
            object.__setattr__(self, "completed_at", datetime.now(UTC))

        object.__setattr__(self, name, value)

    # Stakeholder relationship access methods
    # These will be implemented once we have the GTDItemStakeholder junction model

    def get_owner(self) -> Optional["Stakeholder"]:
        """
        Get the Accountable stakeholder (owner) for this GTD item.

        Returns:
            The stakeholder with ACCOUNTABLE role, or None if not set
        """
        from .relationships import GTDItemStakeholder

        accountable_rels = GTDItemStakeholder.get_stakeholders_by_role(
            self.id, RACIRole.ACCOUNTABLE
        )
        return accountable_rels[0].stakeholder if accountable_rels else None

    def get_responsible(self) -> list["Stakeholder"]:
        """
        Get all stakeholders with RESPONSIBLE role for this GTD item.

        Returns:
            List of stakeholders who are responsible for doing the work
        """
        from .relationships import GTDItemStakeholder

        responsible_rels = GTDItemStakeholder.get_stakeholders_by_role(
            self.id, RACIRole.RESPONSIBLE
        )
        return [rel.stakeholder for rel in responsible_rels if rel.stakeholder]

    def get_consulted(self) -> list["Stakeholder"]:
        """
        Get all stakeholders with CONSULTED role for this GTD item.

        Returns:
            List of stakeholders who provide expertise and consultation
        """
        from .relationships import GTDItemStakeholder

        consulted_rels = GTDItemStakeholder.get_stakeholders_by_role(
            self.id, RACIRole.CONSULTED
        )
        return [rel.stakeholder for rel in consulted_rels if rel.stakeholder]

    def get_informed(self) -> list["Stakeholder"]:
        """
        Get all stakeholders with INFORMED role for this GTD item.

        Returns:
            List of stakeholders who need to be informed of progress
        """
        from .relationships import GTDItemStakeholder

        informed_rels = GTDItemStakeholder.get_stakeholders_by_role(
            self.id, RACIRole.INFORMED
        )
        return [rel.stakeholder for rel in informed_rels if rel.stakeholder]

    def add_stakeholder(self, stakeholder: "Stakeholder", role: RACIRole) -> None:
        """
        Add a stakeholder with specified RACI role to this GTD item.

        Args:
            stakeholder: The stakeholder to add
            role: The RACI role for this stakeholder

        Raises:
            ValueError: If trying to add second ACCOUNTABLE stakeholder
        """
        # Will implement after GTDItemStakeholder is created
        pass

    def remove_stakeholder(
        self, stakeholder: "Stakeholder", role: RACIRole | None = None
    ) -> None:
        """
        Remove a stakeholder from this GTD item.

        Args:
            stakeholder: The stakeholder to remove
            role: Specific role to remove (if None, removes all roles for this stakeholder)
        """
        # Will implement after GTDItemStakeholder is created
        pass
