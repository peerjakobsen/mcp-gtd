"""
GTD Manager Domain Models

This package contains the core domain models for Getting Things Done workflow
with full RACI stakeholder relationship support.

The models follow a dataclass-based inheritance hierarchy:
- GTDItem: Base class for all GTD items (actions, projects)
- Action: Specific tasks with contexts, due dates, energy levels
- Project: Multi-step outcomes with success criteria
- Context: GTD contexts for organizing actions (@phone, @computer, etc.)
- Organization: Companies/groups that stakeholders belong to
- Team: Specific teams within organizations
- Stakeholder: People involved in GTD items with contact info
- GTDItemStakeholder: RACI relationship junction model

RACI Model Support:
- Responsible: People who do the work
- Accountable: Single person ultimately responsible (exactly one per item)
- Consulted: People who provide input and expertise
- Informed: People who need to know about outcomes
"""

from .action import Action
from .base import GTDItem
from .context import Context
from .enums import GTDStatus, OrganizationType, RACIRole
from .project import Project
from .relationships import GTDItemStakeholder
from .stakeholder import Organization, Stakeholder, Team

__all__ = [
    # Core entities
    "GTDItem",
    "Action", 
    "Project",
    "Context",
    # Stakeholder entities
    "Organization",
    "Team",
    "Stakeholder", 
    "GTDItemStakeholder",
    # Enums
    "GTDStatus",
    "RACIRole",
    "OrganizationType",
]