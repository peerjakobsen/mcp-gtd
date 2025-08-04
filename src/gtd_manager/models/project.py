"""
Project model for multi-step GTD outcomes.

Projects represent desired outcomes that require multiple actions to complete,
with clear success criteria and collections of related actions.
"""

from dataclasses import dataclass, field

from .base import GTDItem
from .enums import GTDStatus


@dataclass
class Project(GTDItem):
    """
    Multi-step outcome within the GTD system.

    Projects represent desired outcomes that require more than one action
    to complete. They have clear success criteria and contain collections
    of related actions.

    Attributes:
        success_criteria: Clear definition of what "done" looks like
        actions: List of actions that belong to this project
    """

    success_criteria: str | None = None
    actions: list["Action"] = field(default_factory=list)

    def __setattr__(self, name: str, value) -> None:
        """Override setattr to validate business rules."""
        # Validate that projects have success criteria when organized
        # Skip validation during initial dataclass construction
        if (
            name == "status"
            and value == GTDStatus.ORGANIZED
            and hasattr(self, "_initialized")
            and self._initialized
        ) and not getattr(self, "success_criteria", None):
            raise ValueError("Project must have success criteria to be organized")

        super().__setattr__(name, value)

    def __post_init__(self):
        """Post-initialization setup."""
        super().__post_init__()
        # Mark as initialized so validation can run
        self._initialized = True

    def add_action(self, action: "Action") -> None:
        """
        Add an action to this project.

        Args:
            action: The action to add to this project
        """
        if action not in self.actions:
            self.actions.append(action)
            # Set the action's project_id to link it back
            action.project_id = self.id

    def remove_action(self, action: "Action") -> None:
        """
        Remove an action from this project.

        Args:
            action: The action to remove from this project
        """
        if action in self.actions:
            self.actions.remove(action)
            # Clear the action's project_id
            action.project_id = None

    def get_completed_actions(self) -> list["Action"]:
        """
        Get all completed actions in this project.

        Returns:
            List of actions with COMPLETE status
        """
        return [
            action for action in self.actions if action.status == GTDStatus.COMPLETE
        ]

    def get_pending_actions(self) -> list["Action"]:
        """
        Get all pending (non-complete) actions in this project.

        Returns:
            List of actions that are not yet complete
        """
        return [
            action for action in self.actions if action.status != GTDStatus.COMPLETE
        ]

    def is_complete(self) -> bool:
        """
        Check if all actions in the project are complete.

        Returns:
            True if all actions are complete, False otherwise
        """
        return len(self.get_pending_actions()) == 0
