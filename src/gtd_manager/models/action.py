"""
Action model for specific GTD tasks.

Actions represent concrete tasks that can be completed, with support for
contexts, due dates, energy levels, and project relationships.
"""

from dataclasses import dataclass, field
from datetime import datetime

from .base import GTDItem


@dataclass
class Action(GTDItem):
    """
    Concrete action or task within the GTD system.

    Actions are specific, actionable items that can be completed.
    They can belong to projects and have contexts for organization.

    Attributes:
        due_date: Optional deadline for the action
        energy_level: Energy required (1=low, 5=high)
        project_id: ID of parent project (None for standalone actions)
        contexts: List of contexts this action belongs to
    """

    due_date: datetime | None = None
    energy_level: int | None = None
    project_id: str | None = None
    contexts: list["Context"] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation and setup."""
        super().__post_init__()

        # Validate energy level if provided
        if (
            self.energy_level is not None
            and (
                not isinstance(self.energy_level, int)
                or not (1 <= self.energy_level <= 5)
            )
        ):
                raise ValueError("Energy level must be an integer between 1 and 5")

    def add_context(self, context: "Context") -> None:
        """
        Add a context to this action.

        Args:
            context: The context to add
        """
        if context not in self.contexts:
            self.contexts.append(context)

    def remove_context(self, context: "Context") -> None:
        """
        Remove a context from this action.

        Args:
            context: The context to remove
        """
        if context in self.contexts:
            self.contexts.remove(context)
