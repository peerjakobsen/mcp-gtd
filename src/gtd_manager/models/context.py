"""
Context model for GTD action organization.

Contexts represent the tools, locations, or situations needed to complete actions,
following GTD methodology (@computer, @phone, @errands, etc.).
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Context:
    """
    GTD context for organizing actions by tools, location, or situation.

    Contexts help organize actions based on the resources or situations
    needed to complete them (e.g., @computer, @phone, @errands).

    Attributes:
        name: Context name (should start with @ by GTD convention)
        description: Optional description of the context
        id: Unique identifier
        created_at: When the context was created
        actions: List of actions associated with this context
    """

    name: str
    description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    actions: list["Action"] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation."""
        # Validate context name follows GTD conventions
        if not self.name:
            raise ValueError("Context name cannot be empty")

        if not self.name.startswith("@"):
            raise ValueError("Context name should start with @ (GTD convention)")

    def add_action(self, action: "Action") -> None:
        """
        Add an action to this context.

        Args:
            action: The action to associate with this context
        """
        if action not in self.actions:
            self.actions.append(action)
            # Also add this context to the action's contexts list
            if self not in action.contexts:
                action.contexts.append(self)

    def remove_action(self, action: "Action") -> None:
        """
        Remove an action from this context.

        Args:
            action: The action to remove from this context
        """
        if action in self.actions:
            self.actions.remove(action)
            # Also remove this context from the action's contexts list
            if self in action.contexts:
                action.contexts.remove(self)

    def get_actionable_items(self) -> list["Action"]:
        """
        Get all actionable items in this context.

        Returns:
            List of actions that are organized and ready to be worked on
        """
        from .enums import GTDStatus

        return [
            action
            for action in self.actions
            if action.status in (GTDStatus.ORGANIZED, GTDStatus.REVIEWING)
        ]
