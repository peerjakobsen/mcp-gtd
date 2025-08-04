"""
Junction models for GTD entity relationships.

This module provides junction/association models that handle many-to-many
relationships between GTD entities, particularly the RACI stakeholder relationships.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .enums import RACIRole


# Global registry to track existing RACI relationships for validation
_raci_relationships: List['GTDItemStakeholder'] = []


@dataclass
class GTDItemStakeholder:
    """
    Junction model for RACI relationships between GTD items and stakeholders.
    
    This model implements the RACI (Responsible, Accountable, Consulted, Informed)
    responsibility assignment matrix for GTD items. It enforces the critical business
    rule that each GTD item has exactly one Accountable stakeholder.
    
    Attributes:
        gtd_item_id: ID of the GTD item
        stakeholder_id: ID of the stakeholder
        raci_role: The RACI role for this relationship
        created_at: When the relationship was created
        gtd_item: Reference to the GTD item (will be populated)
        stakeholder: Reference to the stakeholder (will be populated)
    """
    gtd_item_id: str
    stakeholder_id: str
    raci_role: RACIRole
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    gtd_item: Optional['GTDItem'] = None
    stakeholder: Optional['Stakeholder'] = None
    
    def __post_init__(self):
        """Post-initialization validation and business rule enforcement."""
        # Enforce exactly one Accountable per GTD item
        if self.raci_role == RACIRole.ACCOUNTABLE:
            # Check if there's already an Accountable for this GTD item
            existing_accountable = [
                rel for rel in _raci_relationships
                if (rel.gtd_item_id == self.gtd_item_id and 
                    rel.raci_role == RACIRole.ACCOUNTABLE and
                    rel.stakeholder_id != self.stakeholder_id)
            ]
            
            if existing_accountable:
                raise ValueError("Only one Accountable allowed per GTD item")
        
        # Add this relationship to the global registry
        _raci_relationships.append(self)
    
    def __del__(self):
        """Clean up when relationship is deleted."""
        if self in _raci_relationships:
            _raci_relationships.remove(self)
    
    @classmethod
    def get_relationships_for_item(cls, gtd_item_id: str) -> List['GTDItemStakeholder']:
        """
        Get all RACI relationships for a specific GTD item.
        
        Args:
            gtd_item_id: The GTD item ID to find relationships for
            
        Returns:
            List of GTDItemStakeholder relationships for the item
        """
        return [
            rel for rel in _raci_relationships
            if rel.gtd_item_id == gtd_item_id
        ]
    
    @classmethod
    def get_relationships_for_stakeholder(cls, stakeholder_id: str) -> List['GTDItemStakeholder']:
        """
        Get all RACI relationships for a specific stakeholder.
        
        Args:
            stakeholder_id: The stakeholder ID to find relationships for
            
        Returns:
            List of GTDItemStakeholder relationships for the stakeholder
        """
        return [
            rel for rel in _raci_relationships
            if rel.stakeholder_id == stakeholder_id
        ]
    
    @classmethod
    def get_stakeholders_by_role(cls, gtd_item_id: str, role: RACIRole) -> List['GTDItemStakeholder']:
        """
        Get all stakeholders with a specific RACI role for a GTD item.
        
        Args:
            gtd_item_id: The GTD item ID
            role: The RACI role to filter by
            
        Returns:
            List of relationships matching the role
        """
        return [
            rel for rel in _raci_relationships
            if rel.gtd_item_id == gtd_item_id and rel.raci_role == role
        ]
    
    @classmethod 
    def clear_registry(cls):
        """Clear the global registry (useful for testing)."""
        global _raci_relationships
        _raci_relationships.clear()