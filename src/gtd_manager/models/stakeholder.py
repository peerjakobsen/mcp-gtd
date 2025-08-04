"""
Stakeholder, Team, and Organization models for RACI relationship management.

This module provides models for managing people, teams, and organizations involved
in GTD items through the RACI responsibility assignment matrix.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from .enums import OrganizationType


@dataclass
class Organization:
    """
    Organization that teams and stakeholders belong to.

    Organizations classify the different types of entities that stakeholders
    work for (internal AWS teams, customer companies, partners, etc.).

    Attributes:
        name: Organization name
        type: Classification of organization (INTERNAL/CUSTOMER/PARTNER/OTHER)
        description: Optional description
        id: Unique identifier
        created_at: When the organization was created
        teams: List of teams belonging to this organization
        stakeholders: List of stakeholders belonging to this organization
    """

    name: str
    type: OrganizationType
    description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    teams: list["Team"] = field(default_factory=list)
    stakeholders: list["Stakeholder"] = field(default_factory=list)

    def add_team(self, team: "Team") -> None:
        """
        Add a team to this organization.

        Args:
            team: The team to add
        """
        if team not in self.teams:
            self.teams.append(team)
            team.organization_id = self.id

    def add_stakeholder(self, stakeholder: "Stakeholder") -> None:
        """
        Add a stakeholder to this organization.

        Args:
            stakeholder: The stakeholder to add
        """
        if stakeholder not in self.stakeholders:
            self.stakeholders.append(stakeholder)
            stakeholder.organization_id = self.id

    def remove_stakeholder(self, stakeholder: "Stakeholder") -> None:
        """
        Remove a stakeholder from this organization.

        Args:
            stakeholder: The stakeholder to remove
        """
        if stakeholder in self.stakeholders:
            self.stakeholders.remove(stakeholder)
            stakeholder.organization_id = None


@dataclass
class Team:
    """
    Team within an organization.

    Teams represent specific groups within organizations (e.g., EC2 team,
    S3 team within AWS, or Development team within a customer organization).

    Attributes:
        name: Team name
        organization_id: ID of the organization this team belongs to
        description: Optional description of the team's purpose
        id: Unique identifier
        created_at: When the team was created
        organization: Reference to the organization
        stakeholders: List of stakeholders on this team
    """

    name: str
    organization_id: str
    description: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    organization: Organization | None = None
    stakeholders: list["Stakeholder"] = field(default_factory=list)

    def add_stakeholder(self, stakeholder: "Stakeholder") -> None:
        """
        Add a stakeholder to this team.

        Args:
            stakeholder: The stakeholder to add
        """
        if stakeholder not in self.stakeholders:
            self.stakeholders.append(stakeholder)
            stakeholder.team_id = self.id

    def remove_stakeholder(self, stakeholder: "Stakeholder") -> None:
        """
        Remove a stakeholder from this team.

        Args:
            stakeholder: The stakeholder to remove
        """
        if stakeholder in self.stakeholders:
            self.stakeholders.remove(stakeholder)
            stakeholder.team_id = None


@dataclass
class Stakeholder:
    """
    Person involved in GTD items through RACI relationships.

    Stakeholders are people who have roles and responsibilities related
    to GTD items (actions, projects) through the RACI matrix.

    Attributes:
        name: Person's full name
        email: Contact email address
        organization_id: ID of the organization they belong to
        team_id: ID of the specific team within the organization
        role: Their role/title (optional)
        id: Unique identifier
        created_at: When the stakeholder was created
        organization: Reference to the organization (will be populated)
        team: Reference to the team (will be populated)
        gtd_items: List of GTD items they're involved with (via junction)
    """

    name: str
    email: str
    organization_id: str | None = None
    team_id: str | None = None
    role: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    organization: Organization | None = None
    team: Team | None = None
    gtd_items: list["GTDItemStakeholder"] = field(default_factory=list)

    def __post_init__(self):
        """Post-initialization validation."""
        # Validate email format using simple regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.email):
            raise ValueError(f"Invalid email format: {self.email}")

    def get_gtd_items_by_role(self, role: "RACIRole") -> list["GTDItem"]:
        """
        Get all GTD items where this stakeholder has a specific RACI role.

        Args:
            role: The RACI role to filter by

        Returns:
            List of GTD items where stakeholder has the specified role
        """
        # Will implement after GTDItemStakeholder is created
        return []

    def get_owned_items(self) -> list["GTDItem"]:
        """
        Get all GTD items where this stakeholder is Accountable (owner).

        Returns:
            List of GTD items where stakeholder is the owner
        """
        from .enums import RACIRole

        return self.get_gtd_items_by_role(RACIRole.ACCOUNTABLE)
