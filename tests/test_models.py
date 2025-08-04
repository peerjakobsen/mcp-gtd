"""
Test suite for GTD Manager domain models with RACI stakeholder support.

This test file covers all domain models following TDD principles:
- GTDItem base class with workflow states
- Action, Project, Context entities
- Organization and Stakeholder entities
- GTDItemStakeholder RACI junction model

Tests are organized by subtask according to tasks.md specification.
"""

from contextlib import suppress
from datetime import UTC, datetime

import pytest

# These imports will fail initially (red phase) - that's expected in TDD

with suppress(ImportError):
    from gtd_manager.models import (
        Action,
        Context,
        GTDItem,
        GTDItemStakeholder,
        GTDStatus,
        Organization,
        OrganizationType,
        Project,
        RACIRole,
        Stakeholder,
        Team,
    )


class TestGTDItemBase:
    """Tests for subtasks 1.1-1.2: GTDItem base entity with workflow states and stakeholder relationships"""

    def test_gtd_item_creation_with_required_fields(self):
        """Test GTDItem can be created with required fields"""
        # This test will fail initially (red phase)
        item = GTDItem(
            title="Test Item", description="Test description", status=GTDStatus.INBOX
        )

        assert item.title == "Test Item"
        assert item.description == "Test description"
        assert item.status == GTDStatus.INBOX
        assert item.id is not None
        assert item.created_at is not None
        assert item.updated_at is not None
        assert item.completed_at is None

    def test_gtd_item_workflow_states(self):
        """Test GTDItem supports all GTD workflow states"""
        item = GTDItem(title="Test", status=GTDStatus.INBOX)

        # Test all valid status transitions
        valid_statuses = [
            GTDStatus.INBOX,
            GTDStatus.CLARIFIED,
            GTDStatus.ORGANIZED,
            GTDStatus.REVIEWING,
            GTDStatus.COMPLETE,
            GTDStatus.SOMEDAY,
        ]

        for status in valid_statuses:
            item.status = status
            assert item.status == status

    def test_gtd_item_timestamps_automatic_update(self):
        """Test that updated_at is automatically maintained"""
        item = GTDItem(title="Test", status=GTDStatus.INBOX)
        original_updated = item.updated_at

        # Simulate time passing and update
        item.title = "Updated Test"
        # updated_at should be refreshed (will implement this logic)

        assert item.updated_at >= original_updated

    def test_gtd_item_completion_timestamp(self):
        """Test completed_at is set when status becomes complete"""
        item = GTDItem(title="Test", status=GTDStatus.INBOX)
        assert item.completed_at is None

        item.status = GTDStatus.COMPLETE
        # Should automatically set completed_at (will implement this logic)
        assert item.completed_at is not None

    def test_gtd_item_stakeholder_access_methods(self):
        """Test GTDItem provides stakeholder relationship access methods"""
        item = GTDItem(title="Test", status=GTDStatus.INBOX)

        # These methods should exist (will implement)
        assert hasattr(item, "get_owner")
        assert hasattr(item, "get_responsible")
        assert hasattr(item, "get_consulted")
        assert hasattr(item, "get_informed")
        assert hasattr(item, "add_stakeholder")
        assert hasattr(item, "remove_stakeholder")


class TestActionEntity:
    """Tests for subtasks 1.3-1.4: Action entity with contexts, due dates, energy levels, and stakeholders"""

    def test_action_creation_inherits_from_gtd_item(self):
        """Test Action inherits from GTDItem"""
        action = Action(
            title="Call client",
            description="Follow up on project status",
            status=GTDStatus.ORGANIZED,
            due_date=datetime.now(UTC),
            energy_level=3,
        )

        # Should inherit GTDItem properties
        assert isinstance(action, GTDItem)
        assert action.title == "Call client"
        assert action.status == GTDStatus.ORGANIZED

        # Should have Action-specific properties
        assert action.due_date is not None
        assert action.energy_level == 3

    def test_action_contexts_relationship(self):
        """Test Action can have multiple contexts"""
        action = Action(title="Research competitors", status=GTDStatus.ORGANIZED)

        # Should support multiple contexts
        assert hasattr(action, "contexts")
        # Will implement context relationship

    def test_action_project_relationship(self):
        """Test Action can belong to a Project"""
        action = Action(title="Write proposal", status=GTDStatus.ORGANIZED)

        # Should support project relationship
        assert hasattr(action, "project_id")
        # project_id can be None for standalone actions

    def test_action_energy_level_validation(self):
        """Test Action energy level is validated (1-5 scale)"""
        # Valid energy levels should work
        for level in [1, 2, 3, 4, 5]:
            action = Action(title="Test", status=GTDStatus.INBOX, energy_level=level)
            assert action.energy_level == level

        # Invalid energy levels should raise validation error
        with pytest.raises(ValueError):
            Action(title="Test", status=GTDStatus.INBOX, energy_level=0)

        with pytest.raises(ValueError):
            Action(title="Test", status=GTDStatus.INBOX, energy_level=6)


class TestProjectEntity:
    """Tests for subtasks 1.5-1.6: Project entity with success criteria, action collections, and stakeholders"""

    def test_project_creation_inherits_from_gtd_item(self):
        """Test Project inherits from GTDItem"""
        project = Project(
            title="Launch new product",
            description="Complete product launch",
            status=GTDStatus.ORGANIZED,
            success_criteria="Product is live and first customer onboarded",
        )

        # Should inherit GTDItem properties
        assert isinstance(project, GTDItem)
        assert project.title == "Launch new product"
        assert project.status == GTDStatus.ORGANIZED

        # Should have Project-specific properties
        assert (
            project.success_criteria == "Product is live and first customer onboarded"
        )

    def test_project_actions_collection(self):
        """Test Project can contain multiple Actions"""
        project = Project(title="Website redesign", status=GTDStatus.ORGANIZED)

        # Should support actions collection
        assert hasattr(project, "actions")
        # Will implement actions relationship

    def test_project_success_criteria_required(self):
        """Test Project requires success criteria to be organized"""
        # Project without success criteria should not be organizable
        project = Project(title="Vague project", status=GTDStatus.INBOX)

        # Should validate success criteria when status changes to organized
        with pytest.raises(ValueError):
            project.status = GTDStatus.ORGANIZED
            # Should raise error if success_criteria is empty


class TestContextEntity:
    """Tests for subtasks 1.7-1.8: Context entity with name validation and relationships"""

    def test_context_creation_with_validation(self):
        """Test Context can be created with proper validation"""
        context = Context(name="@computer", description="Tasks requiring computer work")

        assert context.name == "@computer"
        assert context.description == "Tasks requiring computer work"
        assert context.id is not None
        assert context.created_at is not None

    def test_context_name_validation(self):
        """Test Context name follows GTD conventions"""
        # Valid context names
        valid_names = ["@computer", "@phone", "@errands", "@waiting-for", "@someday"]
        for name in valid_names:
            context = Context(name=name)
            assert context.name == name

        # Invalid context names should raise validation error
        with pytest.raises(ValueError):
            Context(name="")  # Empty name

        with pytest.raises(ValueError):
            Context(name="computer")  # Missing @ prefix

    def test_context_actions_relationship(self):
        """Test Context can be associated with multiple Actions"""
        context = Context(name="@computer")

        # Should support actions relationship (many-to-many)
        assert hasattr(context, "actions")
        # Will implement relationship


class TestOrganizationEntity:
    """Tests for subtasks 1.9-1.10: Organization entity with type validation (INTERNAL/CUSTOMER/PARTNER/OTHER)"""

    def test_organization_creation(self):
        """Test Organization can be created with required fields"""
        org = Organization(
            name="Amazon Web Services",
            type=OrganizationType.INTERNAL,
            description="Internal AWS organization",
        )

        assert org.name == "Amazon Web Services"
        assert org.type == OrganizationType.INTERNAL
        assert org.description == "Internal AWS organization"
        assert org.id is not None
        assert org.created_at is not None

    def test_organization_type_validation(self):
        """Test Organization supports all four organization types"""
        # Test all valid organization types
        internal_org = Organization(name="AWS", type=OrganizationType.INTERNAL)
        assert internal_org.type == OrganizationType.INTERNAL

        customer_org = Organization(name="Acme Corp", type=OrganizationType.CUSTOMER)
        assert customer_org.type == OrganizationType.CUSTOMER

        partner_org = Organization(
            name="Tech Partner Inc", type=OrganizationType.PARTNER
        )
        assert partner_org.type == OrganizationType.PARTNER

        other_org = Organization(name="Government Agency", type=OrganizationType.OTHER)
        assert other_org.type == OrganizationType.OTHER

    def test_organization_stakeholders_relationship(self):
        """Test Organization can have multiple Stakeholders"""
        org = Organization(name="AWS", type=OrganizationType.INTERNAL)

        # Should support stakeholders relationship
        assert hasattr(org, "stakeholders")
        # Will implement relationship


class TestTeamEntity:
    """Tests for Team entity with organization relationships"""

    def test_team_creation_with_organization(self):
        """Test Team can be created with organization relationship"""
        team = Team(
            name="EC2 Team",
            organization_id="org123",
            description="Elastic Compute Cloud team",
        )

        assert team.name == "EC2 Team"
        assert team.organization_id == "org123"
        assert team.description == "Elastic Compute Cloud team"
        assert team.id is not None
        assert team.created_at is not None

    def test_team_stakeholders_relationship(self):
        """Test Team can have multiple Stakeholders"""
        team = Team(name="S3 Team", organization_id="org123")

        # Should support stakeholders relationship
        assert hasattr(team, "stakeholders")
        # Will implement relationship

    def test_team_organization_relationship(self):
        """Test Team belongs to an Organization"""
        team = Team(name="Lambda Team", organization_id="org123")

        # Should support organization relationship
        assert hasattr(team, "organization")
        # Will implement relationship


class TestStakeholderEntity:
    """Tests for subtasks 1.11-1.12: Stakeholder entity with organization relationships and RACI roles"""

    def test_stakeholder_creation_with_organization_and_team(self):
        """Test Stakeholder can be created with organization and team relationships"""
        stakeholder = Stakeholder(
            name="John Doe",
            email="john.doe@amazon.com",
            organization_id="org123",  # Reference to Organization
            team_id="team456",  # Reference to Team
            role="Senior Engineer",
        )

        assert stakeholder.name == "John Doe"
        assert stakeholder.email == "john.doe@amazon.com"
        assert stakeholder.organization_id == "org123"
        assert stakeholder.team_id == "team456"
        assert stakeholder.role == "Senior Engineer"
        assert stakeholder.id is not None
        assert stakeholder.created_at is not None

    def test_stakeholder_email_validation(self):
        """Test Stakeholder email is properly validated"""
        # Valid email should work
        stakeholder = Stakeholder(
            name="Jane Smith", email="jane.smith@customer.com", organization_id="org123"
        )
        assert stakeholder.email == "jane.smith@customer.com"

        # Invalid email should raise validation error
        with pytest.raises(ValueError):
            Stakeholder(name="Test", email="invalid-email", organization_id="org123")

    def test_stakeholder_organization_relationship(self):
        """Test Stakeholder belongs to an Organization"""
        stakeholder = Stakeholder(
            name="Test User", email="test@example.com", organization_id="org123"
        )

        # Should support organization relationship
        assert hasattr(stakeholder, "organization")
        # Will implement relationship

    def test_stakeholder_team_relationship(self):
        """Test Stakeholder belongs to a Team"""
        stakeholder = Stakeholder(
            name="Test User",
            email="test@example.com",
            organization_id="org123",
            team_id="team456",
        )

        # Should support team relationship
        assert hasattr(stakeholder, "team")
        # Will implement relationship

    def test_stakeholder_gtd_items_relationship(self):
        """Test Stakeholder can be associated with multiple GTD items"""
        stakeholder = Stakeholder(
            name="Test User", email="test@example.com", organization_id="org123"
        )

        # Should support GTD items relationship through junction
        assert hasattr(stakeholder, "gtd_items")
        # Will implement relationship through GTDItemStakeholder


class TestGTDItemStakeholderJunction:
    """Tests for subtasks 1.13-1.14: GTDItemStakeholder junction with RACI constraint validation"""

    def test_raci_relationship_creation(self):
        """Test RACI relationship can be created"""
        relationship = GTDItemStakeholder(
            gtd_item_id=1, stakeholder_id=1, raci_role=RACIRole.RESPONSIBLE
        )

        assert relationship.gtd_item_id == 1
        assert relationship.stakeholder_id == 1
        assert relationship.raci_role == RACIRole.RESPONSIBLE
        assert relationship.created_at is not None

    def test_raci_role_validation(self):
        """Test all RACI roles are supported"""
        valid_roles = [
            RACIRole.RESPONSIBLE,
            RACIRole.ACCOUNTABLE,
            RACIRole.CONSULTED,
            RACIRole.INFORMED,
        ]

        for role in valid_roles:
            relationship = GTDItemStakeholder(
                gtd_item_id=1, stakeholder_id=1, raci_role=role
            )
            assert relationship.raci_role == role

    def test_exactly_one_accountable_constraint(self):
        """Test business rule: exactly one Accountable per GTD item"""
        # This test validates the critical RACI constraint
        # Will implement validation logic to ensure only one ACCOUNTABLE per gtd_item_id

        # First accountable should be allowed
        GTDItemStakeholder(
            gtd_item_id=1, stakeholder_id=1, raci_role=RACIRole.ACCOUNTABLE
        )

        # Second accountable for same item should raise validation error
        with pytest.raises(
            ValueError, match="Only one Accountable allowed per GTD item"
        ):
            GTDItemStakeholder(
                gtd_item_id=1,  # Same GTD item
                stakeholder_id=2,  # Different stakeholder
                raci_role=RACIRole.ACCOUNTABLE,  # But also Accountable
            )

    def test_multiple_other_roles_allowed(self):
        """Test multiple Responsible, Consulted, Informed are allowed"""
        gtd_item_id = 1

        # Multiple responsible stakeholders should be allowed
        relationship1 = GTDItemStakeholder(
            gtd_item_id=gtd_item_id, stakeholder_id=1, raci_role=RACIRole.RESPONSIBLE
        )

        relationship2 = GTDItemStakeholder(
            gtd_item_id=gtd_item_id, stakeholder_id=2, raci_role=RACIRole.RESPONSIBLE
        )

        # Should not raise any errors
        assert relationship1.raci_role == RACIRole.RESPONSIBLE
        assert relationship2.raci_role == RACIRole.RESPONSIBLE

    def test_foreign_key_relationships(self):
        """Test junction model properly references GTDItem and Stakeholder"""
        relationship = GTDItemStakeholder(
            gtd_item_id=1, stakeholder_id=1, raci_role=RACIRole.CONSULTED
        )

        # Should support navigation to related entities
        assert hasattr(relationship, "gtd_item")
        assert hasattr(relationship, "stakeholder")
        # Will implement relationships


class TestIntegrationScenarios:
    """Tests for subtask 1.15: Integration testing with RACI stakeholder scenarios"""

    def setup_method(self):
        """Clear RACI registry before each test."""
        from gtd_manager.models.relationships import GTDItemStakeholder

        GTDItemStakeholder.clear_registry()

    def test_complete_gtd_workflow_with_stakeholders(self):
        """Test complete GTD workflow from inbox to completion with stakeholders"""
        # Create organizations of different types
        aws_org = Organization(name="AWS", type=OrganizationType.INTERNAL)
        customer_org = Organization(name="Acme Corp", type=OrganizationType.CUSTOMER)
        partner_org = Organization(name="Tech Partner", type=OrganizationType.PARTNER)
        Organization(name="Government Agency", type=OrganizationType.OTHER)

        # Create stakeholders from different organization types
        engineer = Stakeholder(
            name="Alice Engineer", email="alice@amazon.com", organization_id=aws_org.id
        )

        customer_contact = Stakeholder(
            name="Bob Customer", email="bob@acme.com", organization_id=customer_org.id
        )

        partner_contact = Stakeholder(
            name="Charlie Partner",
            email="charlie@techpartner.com",
            organization_id=partner_org.id,
        )

        # Create GTD item in inbox
        action = Action(
            title="Resolve customer issue",
            description="Fix authentication bug reported by customer",
            status=GTDStatus.INBOX,
        )

        # Clarify and organize with stakeholders
        action.status = GTDStatus.CLARIFIED

        # Add RACI stakeholders from different organization types
        accountable_rel = GTDItemStakeholder(
            gtd_item_id=action.id,
            stakeholder_id=engineer.id,
            raci_role=RACIRole.ACCOUNTABLE,  # Alice owns the work (INTERNAL)
        )
        accountable_rel.stakeholder = engineer

        informed_rel = GTDItemStakeholder(
            gtd_item_id=action.id,
            stakeholder_id=customer_contact.id,
            raci_role=RACIRole.INFORMED,  # Bob should be informed (CUSTOMER)
        )
        informed_rel.stakeholder = customer_contact

        consulted_rel = GTDItemStakeholder(
            gtd_item_id=action.id,
            stakeholder_id=partner_contact.id,
            raci_role=RACIRole.CONSULTED,  # Charlie provides expertise (PARTNER)
        )
        consulted_rel.stakeholder = partner_contact

        action.status = GTDStatus.ORGANIZED

        # Complete the work
        action.status = GTDStatus.COMPLETE

        # Verify final state
        assert action.status == GTDStatus.COMPLETE
        assert action.completed_at is not None

        # Verify stakeholder relationships across organization types
        owner = action.get_owner()
        assert owner.name == "Alice Engineer"

        informed = action.get_informed()
        assert len(informed) == 1
        assert informed[0].name == "Bob Customer"

        consulted = action.get_consulted()
        assert len(consulted) == 1
        assert consulted[0].name == "Charlie Partner"

    def test_project_with_multiple_actions_and_stakeholders(self):
        """Test project containing multiple actions with different stakeholders"""
        # Create project
        project = Project(
            title="Customer Onboarding System",
            description="Build new customer onboarding flow",
            status=GTDStatus.ORGANIZED,
            success_criteria="New customers can onboard in under 5 minutes",
        )

        # Create actions within project
        action1 = Action(
            title="Design UI mockups", status=GTDStatus.ORGANIZED, project_id=project.id
        )

        action2 = Action(
            title="Implement backend API",
            status=GTDStatus.ORGANIZED,
            project_id=project.id,
        )

        # Add actions to project
        project.add_action(action1)
        project.add_action(action2)

        # Different stakeholders for different actions
        designer = Stakeholder(
            name="Carol Designer", email="carol@amazon.com", organization_id="org123"
        )
        developer = Stakeholder(
            name="Dave Developer", email="dave@amazon.com", organization_id="org123"
        )
        pm = Stakeholder(
            name="Eve PM", email="eve@amazon.com", organization_id="org123"
        )

        # Project-level stakeholder (PM is accountable for overall project)
        project_rel = GTDItemStakeholder(
            gtd_item_id=project.id, stakeholder_id=pm.id, raci_role=RACIRole.ACCOUNTABLE
        )
        project_rel.stakeholder = pm

        # Action-level stakeholders
        action1_rel = GTDItemStakeholder(
            gtd_item_id=action1.id,
            stakeholder_id=designer.id,
            raci_role=RACIRole.ACCOUNTABLE,
        )
        action1_rel.stakeholder = designer

        action2_rel = GTDItemStakeholder(
            gtd_item_id=action2.id,
            stakeholder_id=developer.id,
            raci_role=RACIRole.ACCOUNTABLE,
        )
        action2_rel.stakeholder = developer

        # Verify project structure
        assert len(project.actions) == 2
        assert project.get_owner().name == "Eve PM"
        assert action1.get_owner().name == "Carol Designer"
        assert action2.get_owner().name == "Dave Developer"
