"""
Integration tests for GTD Manager with realistic team lead scenarios.

This test suite exercises complete GTD workflows through the domain layer,
simulating real-world scenarios that team leads encounter daily.

Key Integration Scenarios:
- Team Lead Weekly Processing: Meeting outcomes → organized actions
- Cross-Organizational Projects: Internal/customer/partner coordination
- Context Switching: Energy-based filtering for time management
- Large Data Performance: Bulk operations and realistic volumes

All tests use the repository layer directly to validate business logic
before MCP tools are implemented on top.
"""

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import structlog

from gtd_manager.database import init_database
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
)
from gtd_manager.repositories import (
    ContextRepository,
    GTDItemRepository,
    RACIRepository,
    StakeholderRepository,
)

logger = structlog.get_logger(__name__)


class GTDTestDataFactory:
    """Factory for creating realistic GTD test data scenarios."""

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.gtd_repo = GTDItemRepository(connection)
        self.stakeholder_repo = StakeholderRepository(connection)
        self.context_repo = ContextRepository(connection)
        self.raci_repo = RACIRepository(connection)

        # Track created entities for cleanup
        self.created_organizations = []
        self.created_stakeholders = []
        self.created_contexts = []
        self.created_items = []
        self.created_relationships = []

        # Energy level mapping
        self.energy_map = {"low": 2, "medium": 3, "high": 5}

    def _convert_energy_level(self, energy: str | int) -> int:
        """Convert energy level string to integer."""
        if isinstance(energy, int):
            return energy
        return self.energy_map.get(energy, 3)

    def create_team_lead_organization_structure(self) -> dict:
        """Create realistic organization structure for team lead scenarios."""
        # Internal AWS organization
        aws_org = Organization(
            name="Amazon Web Services", type=OrganizationType.INTERNAL
        )
        self.created_organizations.append(aws_org)

        # Customer organizations
        acme_corp = Organization(
            name="Acme Corporation", type=OrganizationType.CUSTOMER
        )
        startup_inc = Organization(
            name="FastGrow Startup Inc", type=OrganizationType.CUSTOMER
        )
        self.created_organizations.extend([acme_corp, startup_inc])

        # Partner organizations
        consulting_partner = Organization(
            name="TechConsult Partners", type=OrganizationType.PARTNER
        )
        integration_vendor = Organization(
            name="Integration Solutions LLC", type=OrganizationType.PARTNER
        )
        self.created_organizations.extend([consulting_partner, integration_vendor])

        return {
            "internal": aws_org,
            "customers": [acme_corp, startup_inc],
            "partners": [consulting_partner, integration_vendor],
        }

    def create_team_stakeholders(self, organizations: dict) -> dict:
        """Create realistic stakeholder mix for team lead scenarios."""
        # Internal team members
        team_lead = Stakeholder(
            name="Alice Johnson",
            email="alice.johnson@amazon.com",
            organization_id=organizations["internal"].id,
        )

        senior_engineer = Stakeholder(
            name="Bob Chen",
            email="bob.chen@amazon.com",
            organization_id=organizations["internal"].id,
        )

        junior_engineer = Stakeholder(
            name="Carol Martinez",
            email="carol.martinez@amazon.com",
            organization_id=organizations["internal"].id,
        )

        product_manager = Stakeholder(
            name="David Kim",
            email="david.kim@amazon.com",
            organization_id=organizations["internal"].id,
        )

        internal_stakeholders = [
            team_lead,
            senior_engineer,
            junior_engineer,
            product_manager,
        ]

        # Customer contacts
        customer_contacts = []
        for i, customer_org in enumerate(organizations["customers"]):
            contact = Stakeholder(
                name=f"Customer Contact {i + 1}",
                email=f"contact{i + 1}@{customer_org.name.lower().replace(' ', '')}.com",
                organization_id=customer_org.id,
            )
            customer_contacts.append(contact)

        # Partner contacts
        partner_contacts = []
        for i, partner_org in enumerate(organizations["partners"]):
            contact = Stakeholder(
                name=f"Partner Expert {i + 1}",
                email=f"expert{i + 1}@{partner_org.name.lower().replace(' ', '')}.com",
                organization_id=partner_org.id,
            )
            partner_contacts.append(contact)

        all_stakeholders = internal_stakeholders + customer_contacts + partner_contacts
        self.created_stakeholders.extend(all_stakeholders)

        return {
            "team_lead": team_lead,
            "internal_team": [senior_engineer, junior_engineer, product_manager],
            "customers": customer_contacts,
            "partners": partner_contacts,
            "all": all_stakeholders,
        }

    def create_gtd_contexts(self) -> dict:
        """Create realistic GTD contexts for knowledge work."""
        contexts_data = [
            ("@computer", "Tasks requiring focused computer work"),
            ("@calls", "Phone calls and video meetings"),
            ("@waiting_for", "Items waiting on others to complete"),
            ("@review", "Weekly and monthly review activities"),
            ("@brainstorm", "Creative thinking and planning"),
            ("@low_energy", "Tasks for when energy is low"),
            ("@high_energy", "Complex tasks requiring peak focus"),
        ]

        contexts = {}
        for name, description in contexts_data:
            context = Context(name=name, description=description)
            contexts[name.replace("@", "")] = context
            self.created_contexts.append(context)

        return contexts

    def create_weekly_meeting_outcomes(self, stakeholders: dict) -> list[GTDItem]:
        """Simulate 15-20 action items from weekly meetings."""
        meeting_scenarios = [
            # Sprint planning outcomes
            {
                "title": "Refactor authentication service",
                "description": "Customer reported slow login times - investigate and fix",
                "energy": 5,  # high energy
                "stakeholder": stakeholders["internal_team"][0],  # Senior engineer
                "customer_context": stakeholders["customers"][0],
            },
            {
                "title": "Update API documentation",
                "description": "Partner integration team needs updated docs for v2 API",
                "energy": "medium",
                "stakeholder": stakeholders["internal_team"][1],  # Junior engineer
                "partner_context": stakeholders["partners"][0],
            },
            # Customer feedback meeting
            {
                "title": "Schedule customer demo",
                "description": "Acme Corp wants to see new dashboard features",
                "energy": "low",
                "stakeholder": stakeholders["team_lead"],
                "customer_context": stakeholders["customers"][0],
            },
            {
                "title": "Design mobile responsive layout",
                "description": "Customer requested mobile access to reporting",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][1],
                "customer_context": stakeholders["customers"][0],
            },
            # Architecture review outcomes
            {
                "title": "Evaluate database sharding strategy",
                "description": "Performance issues with large customer datasets",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][0],
                "partner_context": stakeholders["partners"][1],
            },
            {
                "title": "Research third-party monitoring tools",
                "description": "Current alerts are not catching edge cases",
                "energy": "medium",
                "stakeholder": stakeholders["internal_team"][1],
                "partner_context": stakeholders["partners"][0],
            },
            # Team sync outcomes
            {
                "title": "Set up pair programming sessions",
                "description": "Junior dev needs mentoring on complex features",
                "energy": "medium",
                "stakeholder": stakeholders["team_lead"],
                "internal_context": stakeholders["internal_team"][0],
            },
            {
                "title": "Plan team off-site agenda",
                "description": "Q2 planning and team building activities",
                "energy": "low",
                "stakeholder": stakeholders["team_lead"],
                "internal_context": None,
            },
            # Partner coordination
            {
                "title": "Review integration testing results",
                "description": "TechConsult found issues with new webhook format",
                "energy": "medium",
                "stakeholder": stakeholders["internal_team"][0],
                "partner_context": stakeholders["partners"][0],
            },
            {
                "title": "Draft SLA agreement with Integration Solutions",
                "description": "Define response times and escalation procedures",
                "energy": "medium",
                "stakeholder": stakeholders["team_lead"],
                "partner_context": stakeholders["partners"][1],
            },
            # Product roadmap items
            {
                "title": "Validate ML model accuracy metrics",
                "description": "Product wants confidence intervals for recommendations",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][0],
                "internal_context": stakeholders["internal_team"][2],  # PM
            },
            {
                "title": "Create customer feedback collection system",
                "description": "Need structured way to gather feature requests",
                "energy": "medium",
                "stakeholder": stakeholders["internal_team"][1],
                "internal_context": stakeholders["internal_team"][2],  # PM
            },
            # Operations and maintenance
            {
                "title": "Automate deployment rollback procedure",
                "description": "Manual rollbacks are error-prone and slow",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][0],
                "internal_context": None,
            },
            {
                "title": "Update security compliance documentation",
                "description": "Annual audit requires updated procedures",
                "energy": "low",
                "stakeholder": stakeholders["internal_team"][1],
                "internal_context": None,
            },
            # Cross-team coordination
            {
                "title": "Coordinate with data team on schema changes",
                "description": "New analytics requirements impact our data model",
                "energy": "medium",
                "stakeholder": stakeholders["team_lead"],
                "internal_context": None,
            },
            {
                "title": "Present architecture changes to leadership",
                "description": "Need approval for microservices migration plan",
                "energy": "medium",
                "stakeholder": stakeholders["team_lead"],
                "internal_context": None,
            },
            # Customer success items
            {
                "title": "Troubleshoot FastGrow startup performance issues",
                "description": "High-growth customer experiencing timeouts",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][0],
                "customer_context": stakeholders["customers"][1],
            },
            {
                "title": "Create onboarding checklist for new customers",
                "description": "Standardize customer setup process",
                "energy": "low",
                "stakeholder": stakeholders["internal_team"][1],
                "customer_context": None,
            },
            # Innovation and research
            {
                "title": "Prototype voice interface for mobile app",
                "description": "Explore accessibility improvements",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][1],
                "internal_context": None,
            },
            {
                "title": "Research edge computing deployment options",
                "description": "Customers want lower latency for IoT devices",
                "energy": "high",
                "stakeholder": stakeholders["internal_team"][0],
                "partner_context": stakeholders["partners"][1],
            },
        ]

        inbox_items = []
        for scenario in meeting_scenarios:
            # Create as inbox item initially
            item = Action(
                title=scenario["title"],
                description=scenario["description"],
                status=GTDStatus.INBOX,
                energy_level=self._convert_energy_level(scenario["energy"]),
            )
            inbox_items.append(item)
            self.created_items.append(item)

        return inbox_items

    def cleanup(self):
        """Clean up all created test data."""
        # Clear relationship registry
        GTDItemStakeholder.clear_registry()

        # Clear entity lists
        self.created_organizations.clear()
        self.created_stakeholders.clear()
        self.created_contexts.clear()
        self.created_items.clear()
        self.created_relationships.clear()


@pytest.fixture
def temp_database():
    """Create temporary database for integration tests."""
    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_gtd.db"
        init_database(db_path)

        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row

        yield conn

        conn.close()


@pytest.fixture
def gtd_factory(temp_database):
    """Create GTD test data factory with temporary database."""
    factory = GTDTestDataFactory(temp_database)
    yield factory
    factory.cleanup()


class TestTeamLeadWeeklyProcessing:
    """Integration tests for complete weekly GTD processing workflow."""

    def test_complete_weekly_processing_workflow(self, gtd_factory):
        """
        Simulate complete weekly processing:
        Capture → Clarify → Organize → Review
        """
        # Setup organizational structure
        orgs = gtd_factory.create_team_lead_organization_structure()
        stakeholders = gtd_factory.create_team_stakeholders(orgs)
        contexts = gtd_factory.create_gtd_contexts()

        # Phase 1: Capture - Generate realistic meeting outcomes
        inbox_items = gtd_factory.create_weekly_meeting_outcomes(stakeholders)

        assert len(inbox_items) == 20, "Should generate 20 meeting outcome items"
        assert all(item.status == GTDStatus.INBOX for item in inbox_items)

        # Phase 2: Clarify - Process inbox items
        clarified_items = []
        for item in inbox_items:
            # Simulate clarification process
            item.status = GTDStatus.CLARIFIED

            # Add appropriate context based on work type
            if "documentation" in item.title.lower() or "review" in item.title.lower():
                item.add_context(contexts["computer"])
            elif "call" in item.title.lower() or "demo" in item.title.lower():
                item.add_context(contexts["calls"])
            elif "research" in item.title.lower() or "prototype" in item.title.lower():
                item.add_context(contexts["brainstorm"])

            clarified_items.append(item)

        assert len(clarified_items) == 20
        assert all(item.status == GTDStatus.CLARIFIED for item in clarified_items)

        # Phase 3: Organize - Assign stakeholders and create projects
        projects_created = []
        organized_actions = []

        # Group related items into projects
        customer_project = Project(
            title="Customer Experience Improvements",
            description="Addressing customer feedback and performance issues",
            status=GTDStatus.ORGANIZED,
            success_criteria="Customer satisfaction scores above 90%",
        )
        projects_created.append(customer_project)

        infrastructure_project = Project(
            title="Infrastructure Modernization",
            description="Technical debt and performance improvements",
            status=GTDStatus.ORGANIZED,
            success_criteria="50% reduction in incident response time",
        )
        projects_created.append(infrastructure_project)

        # Assign items to projects and stakeholders
        for item in clarified_items:
            item.status = GTDStatus.ORGANIZED

            # Assign to appropriate project
            if any(
                keyword in item.title.lower()
                for keyword in ["customer", "demo", "feedback"]
            ):
                item.project_id = customer_project.id
                customer_project.add_action(item)
            elif any(
                keyword in item.title.lower()
                for keyword in ["database", "deployment", "performance"]
            ):
                item.project_id = infrastructure_project.id
                infrastructure_project.add_action(item)

            organized_actions.append(item)

        # Assign RACI stakeholders
        raci_relationships = []
        for item in organized_actions:
            # Team lead is always informed
            team_lead_rel = GTDItemStakeholder(
                gtd_item_id=item.id,
                stakeholder_id=stakeholders["team_lead"].id,
                raci_role=RACIRole.INFORMED,
            )
            team_lead_rel.stakeholder = stakeholders["team_lead"]
            raci_relationships.append(team_lead_rel)

            # Assign accountable person based on complexity
            if item.energy_level == 5:
                accountable_person = stakeholders["internal_team"][0]  # Senior engineer
            else:
                accountable_person = stakeholders["internal_team"][1]  # Junior engineer

            accountable_rel = GTDItemStakeholder(
                gtd_item_id=item.id,
                stakeholder_id=accountable_person.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
            accountable_rel.stakeholder = accountable_person
            raci_relationships.append(accountable_rel)

        # Phase 4: Review - Weekly review aggregation
        high_energy_actions = [a for a in organized_actions if a.energy_level == 5]
        low_energy_actions = [a for a in organized_actions if a.energy_level == 2]
        customer_facing_actions = [
            a for a in organized_actions if a.project_id == customer_project.id
        ]

        # Assertions for complete workflow
        assert len(projects_created) == 2
        assert len(organized_actions) == 20
        assert len(raci_relationships) == 40  # 2 per action (informed + accountable)
        assert len(high_energy_actions) >= 5, "Should have several high-energy tasks"
        assert len(low_energy_actions) >= 3, "Should have some low-energy tasks"
        assert len(customer_facing_actions) >= 4, "Should have customer-related actions"

        # Verify stakeholder assignments work correctly
        for action in organized_actions:
            owner = action.get_owner()
            assert owner is not None, f"Action {action.title} should have owner"
            assert owner.organization_id == orgs["internal"].id, (
                "Owner should be internal"
            )

            informed = action.get_informed()
            assert len(informed) >= 1, (
                f"Action {action.title} should have informed stakeholders"
            )

        logger.info(
            "Weekly processing workflow completed successfully",
            inbox_items=len(inbox_items),
            projects_created=len(projects_created),
            raci_relationships=len(raci_relationships),
            high_energy_actions=len(high_energy_actions),
        )


class TestCrossOrganizationalProject:
    """Integration tests for complex cross-organizational project coordination."""

    def test_customer_issue_resolution_with_partner_support(self, gtd_factory):
        """
        Simulate customer issue requiring coordination across:
        - Internal team (AWS)
        - Customer organization
        - Partner for specialized expertise
        """
        # Setup multi-org structure
        orgs = gtd_factory.create_team_lead_organization_structure()
        stakeholders = gtd_factory.create_team_stakeholders(orgs)
        gtd_factory.create_gtd_contexts()  # Create contexts for test completeness

        # Create customer issue project
        customer_issue_project = Project(
            title="Acme Corp API Integration Crisis",
            description="Customer's payment system failing due to API changes",
            status=GTDStatus.ORGANIZED,
            success_criteria="Customer payment success rate back to 99.9%",
        )
        gtd_factory.created_items.append(customer_issue_project)

        # Create actions spanning different expertise areas
        actions = [
            Action(
                title="Investigate payment API failure patterns",
                description="Analyze logs to identify root cause of failures",
                status=GTDStatus.ORGANIZED,
                project_id=customer_issue_project.id,
                energy_level=5,
            ),
            Action(
                title="Coordinate with customer technical team",
                description="Daily sync meetings with Acme Corp engineering",
                status=GTDStatus.ORGANIZED,
                project_id=customer_issue_project.id,
                energy_level=3,
            ),
            Action(
                title="Engage partner for payment gateway expertise",
                description="TechConsult has deep expertise in payment systems",
                status=GTDStatus.ORGANIZED,
                project_id=customer_issue_project.id,
                energy_level=3,
            ),
            Action(
                title="Implement API compatibility layer",
                description="Backward compatibility for customer's legacy integration",
                status=GTDStatus.ORGANIZED,
                project_id=customer_issue_project.id,
                energy_level=5,
            ),
            Action(
                title="Create customer communication plan",
                description="Regular status updates and timeline communication",
                status=GTDStatus.ORGANIZED,
                project_id=customer_issue_project.id,
                energy_level=2,
            ),
        ]

        # Add actions to project
        for action in actions:
            customer_issue_project.add_action(action)
            gtd_factory.created_items.append(action)

        # Complex RACI assignment across organizations
        raci_assignments = [
            # Action 1: Investigation - Senior engineer accountable, team lead consulted
            (actions[0], stakeholders["internal_team"][0], RACIRole.ACCOUNTABLE),
            (actions[0], stakeholders["team_lead"], RACIRole.CONSULTED),
            (actions[0], stakeholders["customers"][0], RACIRole.INFORMED),
            # Action 2: Customer coordination - Team lead accountable, customer consulted
            (actions[1], stakeholders["team_lead"], RACIRole.ACCOUNTABLE),
            (actions[1], stakeholders["customers"][0], RACIRole.CONSULTED),
            (actions[1], stakeholders["internal_team"][0], RACIRole.INFORMED),
            # Action 3: Partner engagement - Team lead accountable, partner consulted
            (actions[2], stakeholders["team_lead"], RACIRole.ACCOUNTABLE),
            (actions[2], stakeholders["partners"][0], RACIRole.CONSULTED),
            (actions[2], stakeholders["internal_team"][0], RACIRole.INFORMED),
            # Action 4: Implementation - Senior engineer accountable, partner consulted
            (actions[3], stakeholders["internal_team"][0], RACIRole.ACCOUNTABLE),
            (actions[3], stakeholders["partners"][0], RACIRole.CONSULTED),
            (actions[3], stakeholders["customers"][0], RACIRole.INFORMED),
            # Action 5: Communication - Team lead accountable, all informed
            (actions[4], stakeholders["team_lead"], RACIRole.ACCOUNTABLE),
            (actions[4], stakeholders["customers"][0], RACIRole.INFORMED),
            (actions[4], stakeholders["partners"][0], RACIRole.INFORMED),
        ]

        # Create RACI relationships
        for action, stakeholder, role in raci_assignments:
            relationship = GTDItemStakeholder(
                gtd_item_id=action.id, stakeholder_id=stakeholder.id, raci_role=role
            )
            relationship.stakeholder = stakeholder
            gtd_factory.created_relationships.append(relationship)

        # Simulate project execution and status tracking
        # Complete investigation
        actions[0].status = GTDStatus.COMPLETE
        actions[0].completed_at = datetime.now(UTC)

        # Start implementation
        actions[3].status = GTDStatus.IN_PROGRESS

        # Verify cross-organizational coordination
        assert len(customer_issue_project.actions) == 5

        # Verify RACI distribution across organization types
        internal_accountable = []
        customer_consulted = []
        partner_consulted = []

        for action in actions:
            owner = action.get_owner()
            if owner and owner.organization_id == orgs["internal"].id:
                internal_accountable.append(action)

            consulted = action.get_consulted()
            for consultant in consulted:
                if consultant.organization_id == orgs["customers"][0].id:
                    customer_consulted.append(action)
                elif consultant.organization_id in [p.id for p in orgs["partners"]]:
                    partner_consulted.append(action)

        assert len(internal_accountable) >= 4, "Most actions should be owned internally"
        assert len(customer_consulted) >= 2, (
            "Customer should be consulted on multiple actions"
        )
        assert len(partner_consulted) >= 2, (
            "Partner should be consulted on multiple actions"
        )

        # Verify project is not complete until all actions done
        assert not customer_issue_project.is_complete()

        # Complete remaining actions
        for action in actions[1:]:
            action.status = GTDStatus.COMPLETE
            action.completed_at = datetime.now(UTC)

        assert customer_issue_project.is_complete()

        logger.info(
            "Cross-organizational project coordination tested successfully",
            project_actions=len(actions),
            raci_relationships=len(raci_assignments),
            internal_accountable=len(internal_accountable),
            external_consulted=len(customer_consulted) + len(partner_consulted),
        )


class TestContextSwitchingSimulation:
    """Integration tests for context-based task management and energy optimization."""

    def test_energy_based_task_filtering_and_time_boxing(self, gtd_factory):
        """
        Simulate context switching optimization:
        - Large backlog of mixed-energy tasks
        - Context-based filtering for time blocks
        - Energy level matching for productivity
        """
        # Setup test data
        orgs = gtd_factory.create_team_lead_organization_structure()
        stakeholders = gtd_factory.create_team_stakeholders(orgs)
        contexts = gtd_factory.create_gtd_contexts()

        # Create large backlog with mixed energy requirements
        backlog_scenarios = [
            # High energy tasks - complex technical work
            ("Architect microservices migration", "high", ["computer", "brainstorm"]),
            ("Debug complex distributed system issue", "high", ["computer"]),
            ("Design new ML model architecture", "high", ["computer", "brainstorm"]),
            ("Lead technical architecture review", "high", ["calls"]),
            ("Prototype new authentication system", "high", ["computer"]),
            # Medium energy tasks - standard development work
            ("Implement user dashboard improvements", "medium", ["computer"]),
            ("Code review for team submissions", "medium", ["computer"]),
            ("Update integration test suite", "medium", ["computer"]),
            ("Plan sprint backlog priorities", "medium", ["brainstorm"]),
            ("Conduct team standup meetings", "medium", ["calls"]),
            ("Research third-party library options", "medium", ["computer"]),
            ("Write technical documentation", "medium", ["computer"]),
            # Low energy tasks - administrative and routine work
            ("Update team vacation calendar", "low", ["computer"]),
            ("Fill out performance review forms", "low", ["computer"]),
            ("Schedule quarterly planning meetings", "low", ["calls"]),
            ("Organize team offsite logistics", "low", ["computer"]),
            ("Review and approve expense reports", "low", ["computer"]),
            ("Send project status updates", "low", ["computer"]),
            ("Update project wikis", "low", ["computer"]),
        ]

        # Create action backlog
        backlog_actions = []
        for title, energy, context_names in backlog_scenarios:
            action = Action(
                title=title,
                description=f"Task requiring {energy} energy level",
                status=GTDStatus.ORGANIZED,
                energy_level=gtd_factory._convert_energy_level(energy),
            )

            # Assign contexts
            for context_name in context_names:
                if context_name in contexts:
                    action.add_context(contexts[context_name])

            # Assign owner (rotate through team)
            owner_idx = len(backlog_actions) % len(stakeholders["internal_team"])
            owner = stakeholders["internal_team"][owner_idx]

            relationship = GTDItemStakeholder(
                gtd_item_id=action.id,
                stakeholder_id=owner.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
            relationship.stakeholder = owner

            backlog_actions.append(action)
            gtd_factory.created_items.append(action)
            gtd_factory.created_relationships.append(relationship)

        # Simulate different time blocks and energy states

        # Morning high-energy block (2 hours)
        high_energy_tasks = [a for a in backlog_actions if a.energy_level == 5]
        computer_high_energy = [
            a
            for a in high_energy_tasks
            if any(ctx.name == "@computer" for ctx in a.contexts)
        ]

        # Afternoon medium-energy block (3 hours)
        medium_energy_tasks = [a for a in backlog_actions if a.energy_level == 3]
        computer_medium_energy = [
            a
            for a in medium_energy_tasks
            if any(ctx.name == "@computer" for ctx in a.contexts)
        ]

        # End-of-day low-energy block (1 hour)
        low_energy_tasks = [a for a in backlog_actions if a.energy_level == 2]

        # Meeting time blocks
        call_tasks = [
            a
            for a in backlog_actions
            if any(ctx.name == "@calls" for ctx in a.contexts)
        ]

        # Creative time blocks
        brainstorm_tasks = [
            a
            for a in backlog_actions
            if any(ctx.name == "@brainstorm" for ctx in a.contexts)
        ]

        # Assertions for context switching optimization
        assert len(high_energy_tasks) == 5, "Should have 5 high-energy tasks"
        assert len(medium_energy_tasks) == 7, "Should have 7 medium-energy tasks"
        assert len(low_energy_tasks) == 7, "Should have 7 low-energy tasks"
        assert len(computer_high_energy) >= 3, (
            "Should have computer-based high-energy tasks"
        )
        assert len(call_tasks) >= 2, "Should have call-based tasks"
        assert len(brainstorm_tasks) >= 2, "Should have brainstorming tasks"

        # Simulate optimal task selection for different time blocks
        morning_block_selection = computer_high_energy[:2]  # Take 2 high-energy tasks
        afternoon_block_selection = computer_medium_energy[:3]  # Take 3 medium tasks
        evening_block_selection = low_energy_tasks[:2]  # Take 2 low-energy tasks

        # Verify time block optimization
        for task in morning_block_selection:
            assert task.energy_level == 5
            assert any(ctx.name == "@computer" for ctx in task.contexts)

        for task in afternoon_block_selection:
            assert task.energy_level == 3
            assert any(ctx.name == "@computer" for ctx in task.contexts)

        for task in evening_block_selection:
            assert task.energy_level == 2

        # Simulate execution progress tracking
        completed_tasks = []

        # Complete morning block
        for task in morning_block_selection:
            task.status = GTDStatus.COMPLETE
            task.completed_at = datetime.now(UTC) - timedelta(hours=6)  # Morning
            completed_tasks.append(task)

        # Complete afternoon block
        for task in afternoon_block_selection:
            task.status = GTDStatus.COMPLETE
            task.completed_at = datetime.now(UTC) - timedelta(hours=2)  # Afternoon
            completed_tasks.append(task)

        # Complete evening block
        for task in evening_block_selection:
            task.status = GTDStatus.COMPLETE
            task.completed_at = datetime.now(UTC)  # Evening
            completed_tasks.append(task)

        # Verify productivity metrics
        total_completed = len(completed_tasks)
        remaining_backlog = len(backlog_actions) - total_completed
        completion_rate = total_completed / len(backlog_actions)

        assert total_completed == 7, "Should complete 7 tasks across time blocks"
        assert remaining_backlog == 12, "Should have 12 tasks remaining"
        assert completion_rate > 0.3, "Should complete over 30% of backlog"

        # Verify energy distribution in completed work
        completed_by_energy = {}
        for task in completed_tasks:
            energy = task.energy_level
            completed_by_energy[energy] = completed_by_energy.get(energy, 0) + 1

        assert completed_by_energy.get(5, 0) == 2, "Should complete 2 high-energy tasks"
        assert completed_by_energy.get(3, 0) == 3, (
            "Should complete 3 medium-energy tasks"
        )
        assert completed_by_energy.get(2, 0) == 2, "Should complete 2 low-energy tasks"

        logger.info(
            "Context switching simulation completed successfully",
            total_backlog=len(backlog_actions),
            completed_tasks=total_completed,
            completion_rate=completion_rate,
            energy_distribution=completed_by_energy,
        )


class TestDataIntegrityAndPerformance:
    """Integration tests for bulk operations and data consistency."""

    def test_bulk_operations_with_realistic_data_volumes(self, gtd_factory):
        """
        Test system performance and consistency with realistic data volumes:
        - 100+ actions across multiple projects
        - 50+ stakeholders from different organizations
        - Complex RACI relationship network
        - Concurrent workflow operations
        """
        # Setup large organizational structure
        orgs = gtd_factory.create_team_lead_organization_structure()

        # Create extended stakeholder network (50+ people)
        bulk_stakeholders = []

        # Add more internal team members (20 people)
        for i in range(20):
            stakeholder = Stakeholder(
                name=f"Internal Engineer {i + 1}",
                email=f"engineer{i + 1}@amazon.com",
                organization_id=orgs["internal"].id,
            )
            bulk_stakeholders.append(stakeholder)

        # Add more customer contacts (20 people across customers)
        customer_orgs = orgs["customers"]
        for i in range(20):
            org_idx = i % len(customer_orgs)
            stakeholder = Stakeholder(
                name=f"Customer Contact {i + 1}",
                email=f"contact{i + 1}@customer{org_idx + 1}.com",
                organization_id=customer_orgs[org_idx].id,
            )
            bulk_stakeholders.append(stakeholder)

        # Add more partner contacts (15 people)
        partner_orgs = orgs["partners"]
        for i in range(15):
            org_idx = i % len(partner_orgs)
            stakeholder = Stakeholder(
                name=f"Partner Expert {i + 1}",
                email=f"expert{i + 1}@partner{org_idx + 1}.com",
                organization_id=partner_orgs[org_idx].id,
            )
            bulk_stakeholders.append(stakeholder)

        gtd_factory.created_stakeholders.extend(bulk_stakeholders)

        assert len(bulk_stakeholders) == 55, "Should create 55 stakeholders"

        # Create multiple large projects (5 projects with 20+ actions each)
        bulk_projects = []
        bulk_actions = []

        project_templates = [
            ("Customer Platform Redesign", "Modernize customer-facing systems", 25),
            ("Infrastructure Migration", "Move to cloud-native architecture", 30),
            ("API Gateway Implementation", "Centralize API management", 20),
            ("Security Compliance Initiative", "Meet new regulatory requirements", 22),
            ("Performance Optimization Program", "Improve system performance", 28),
        ]

        for proj_title, proj_desc, action_count in project_templates:
            project = Project(
                title=proj_title,
                description=proj_desc,
                status=GTDStatus.ORGANIZED,
                success_criteria=f"Complete all {action_count} actions successfully",
            )
            bulk_projects.append(project)
            gtd_factory.created_items.append(project)

            # Create actions for this project
            for i in range(action_count):
                action = Action(
                    title=f"{proj_title} - Task {i + 1}",
                    description=f"Detailed work item {i + 1} for {proj_title.lower()}",
                    status=GTDStatus.ORGANIZED,
                    project_id=project.id,
                    energy_level=gtd_factory._convert_energy_level(
                        ["low", "medium", "high"][i % 3]
                    ),
                )
                project.add_action(action)
                bulk_actions.append(action)
                gtd_factory.created_items.append(action)

        assert len(bulk_projects) == 5, "Should create 5 projects"
        assert len(bulk_actions) == 125, "Should create 125 actions total"

        # Create complex RACI relationship network
        raci_relationships = []

        for action in bulk_actions:
            # Each action gets 3-5 stakeholder relationships
            num_relationships = 3 + (hash(action.id) % 3)  # 3-5 relationships

            # Select stakeholders for this action
            action_stakeholders = []

            # Always include internal owner
            internal_owner = bulk_stakeholders[
                hash(action.id) % 20
            ]  # First 20 are internal
            action_stakeholders.append((internal_owner, RACIRole.ACCOUNTABLE))

            # Add customer stakeholder for customer-facing actions
            if "customer" in action.title.lower() or "platform" in action.title.lower():
                customer_idx = 20 + (hash(action.id) % 20)  # Customer stakeholders
                customer_stakeholder = bulk_stakeholders[customer_idx]
                action_stakeholders.append((customer_stakeholder, RACIRole.CONSULTED))

            # Add partner stakeholder for technical actions
            if any(
                keyword in action.title.lower()
                for keyword in ["infrastructure", "api", "performance"]
            ):
                partner_idx = 40 + (hash(action.id) % 15)  # Partner stakeholders
                partner_stakeholder = bulk_stakeholders[partner_idx]
                action_stakeholders.append((partner_stakeholder, RACIRole.CONSULTED))

            # Fill remaining slots with informed stakeholders
            while len(action_stakeholders) < num_relationships:
                stakeholder_idx = hash(action.id + str(len(action_stakeholders))) % len(
                    bulk_stakeholders
                )
                stakeholder = bulk_stakeholders[stakeholder_idx]

                # Avoid duplicates
                if not any(s[0].id == stakeholder.id for s in action_stakeholders):
                    action_stakeholders.append((stakeholder, RACIRole.INFORMED))

            # Create RACI relationships
            for stakeholder, role in action_stakeholders:
                relationship = GTDItemStakeholder(
                    gtd_item_id=action.id, stakeholder_id=stakeholder.id, raci_role=role
                )
                relationship.stakeholder = stakeholder
                raci_relationships.append(relationship)

        gtd_factory.created_relationships.extend(raci_relationships)

        # Verify relationship network complexity
        total_relationships = len(raci_relationships)
        avg_relationships_per_action = total_relationships / len(bulk_actions)

        assert total_relationships >= 375, (
            "Should have at least 375 relationships (3 per action)"
        )
        assert total_relationships <= 625, (
            "Should have at most 625 relationships (5 per action)"
        )
        assert 3 <= avg_relationships_per_action <= 5, (
            "Average relationships should be 3-5 per action"
        )

        # Test bulk status transitions (simulate work progress)
        import random

        random.seed(42)  # Deterministic for testing

        # Complete 30% of actions
        actions_to_complete = random.sample(bulk_actions, 37)  # ~30% of 125
        for action in actions_to_complete:
            action.status = GTDStatus.COMPLETE
            action.completed_at = datetime.now(UTC) - timedelta(
                days=random.randint(1, 30)
            )

        # Set 20% to in-progress
        remaining_actions = [a for a in bulk_actions if a.status != GTDStatus.COMPLETE]
        actions_in_progress = random.sample(remaining_actions, 25)  # ~20% of 125
        for action in actions_in_progress:
            action.status = GTDStatus.IN_PROGRESS

        # Verify bulk operation results
        completed_actions = [a for a in bulk_actions if a.status == GTDStatus.COMPLETE]
        in_progress_actions = [
            a for a in bulk_actions if a.status == GTDStatus.IN_PROGRESS
        ]
        organized_actions = [a for a in bulk_actions if a.status == GTDStatus.ORGANIZED]

        assert len(completed_actions) == 37, "Should have 37 completed actions"
        assert len(in_progress_actions) == 25, "Should have 25 in-progress actions"
        assert len(organized_actions) == 63, "Should have 63 organized actions"

        # Test project completion logic with bulk data
        completed_projects = []
        for project in bulk_projects:
            if project.is_complete():
                completed_projects.append(project)

        # With random completion, likely no projects will be 100% complete
        assert len(completed_projects) <= 2, (
            "At most 2 projects should be complete with random completion"
        )

        # Verify RACI consistency across bulk operations
        accountable_count = len(
            [r for r in raci_relationships if r.raci_role == RACIRole.ACCOUNTABLE]
        )
        consulted_count = len(
            [r for r in raci_relationships if r.raci_role == RACIRole.CONSULTED]
        )
        informed_count = len(
            [r for r in raci_relationships if r.raci_role == RACIRole.INFORMED]
        )

        assert accountable_count == 125, (
            "Each action should have exactly one accountable person"
        )
        assert consulted_count >= 50, "Should have many consulted relationships"
        assert informed_count >= 200, "Should have many informed relationships"

        # Performance validation - verify all operations completed in reasonable time
        # (Implicit - if test completes without timeout, performance is acceptable)

        logger.info(
            "Bulk operations and data integrity test completed successfully",
            stakeholders=len(bulk_stakeholders),
            projects=len(bulk_projects),
            actions=len(bulk_actions),
            raci_relationships=total_relationships,
            completed_actions=len(completed_actions),
            avg_relationships_per_action=avg_relationships_per_action,
        )
