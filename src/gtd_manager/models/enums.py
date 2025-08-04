"""
Enums for GTD Manager domain models.

This module defines all enumeration types used across the GTD system:
- GTDStatus: Workflow states for GTD items
- RACIRole: Stakeholder responsibility types
- OrganizationType: Classification of organizations
"""

from enum import Enum


class GTDStatus(str, Enum):
    """
    GTD workflow states for items progressing through the system.

    Based on Getting Things Done methodology:
    - INBOX: Newly captured, not yet processed
    - CLARIFIED: Processed and understood what it is
    - ORGANIZED: Categorized and placed in appropriate system
    - REVIEWING: Being actively worked on or reviewed
    - COMPLETE: Finished and closed
    - SOMEDAY: Parked for potential future action
    """

    INBOX = "inbox"
    CLARIFIED = "clarified"
    ORGANIZED = "organized"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    SOMEDAY = "someday"


class RACIRole(str, Enum):
    """
    RACI responsibility assignment matrix roles for stakeholder relationships.

    - RESPONSIBLE: Person who does the work to complete the task
    - ACCOUNTABLE: Person who is ultimately answerable for completion (exactly one per item)
    - CONSULTED: Person who provides expertise and is consulted before decisions
    - INFORMED: Person who needs to be informed about progress and outcomes
    """

    RESPONSIBLE = "responsible"
    ACCOUNTABLE = "accountable"
    CONSULTED = "consulted"
    INFORMED = "informed"


class OrganizationType(str, Enum):
    """
    Classification types for organizations that stakeholders belong to.

    - INTERNAL: AWS internal teams and employees
    - CUSTOMER: External customer organizations
    - PARTNER: Technology partners and vendors
    - OTHER: Government agencies, contractors, or other external entities
    """

    INTERNAL = "internal"
    CUSTOMER = "customer"
    PARTNER = "partner"
    OTHER = "other"
