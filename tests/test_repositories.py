"""
Test suite for GTD Manager repository pattern and domain model persistence.

This test file covers Task 3.1-3.2: Repository pattern with database operations.
Following TDD principles - these tests will fail initially until implementation.

Tests are organized by repository type and operation:
- Base repository interface and common operations
- GTDItem repository for actions and projects
- Context repository for GTD contexts
- Stakeholder repository with organization relationships
- RACI relationship repository for GTDItemStakeholder junction
"""

from contextlib import suppress
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

# Database connection handling
from gtd_manager.database import get_db_connection, init_database

# These imports will fail initially (red phase) - that's expected in TDD
with suppress(ImportError):
    from gtd_manager.models import (
        Action,
        Context,
        GTDItemStakeholder,
        GTDStatus,
        Project,
        RACIRole,
        Stakeholder,
    )

# Repository imports that don't exist yet
with suppress(ImportError):
    from gtd_manager.repositories import (
        BaseRepository,
        ContextRepository,
        GTDItemRepository,
        RACIRepository,
        StakeholderRepository,
    )

# Error handling imports
with suppress(ImportError):
    from gtd_manager.errors import (
        GTDDuplicateError,
        GTDNotFoundError,
    )


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide temporary database path for testing"""
    db_path = tmp_path / "test.db"
    return db_path


@pytest.fixture
def db_connection(temp_db_path):
    """Provide database connection with full schema for testing"""
    # Initialize database
    init_database(temp_db_path)

    # Patch the database path for all operations
    with (
        patch("gtd_manager.database.get_database_path", return_value=temp_db_path),
        get_db_connection() as conn,
    ):
        # Create schema directly for testing (simpler than migration system)
        conn.execute("""
                CREATE TABLE gtd_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'inbox',
                    item_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    project_id TEXT,
                    due_date TIMESTAMP,
                    energy_level INTEGER,
                    success_criteria TEXT,
                    FOREIGN KEY (project_id) REFERENCES gtd_items(id) ON DELETE SET NULL,
                    CHECK (status IN ('inbox', 'clarified', 'organized', 'reviewing', 'complete', 'someday')),
                    CHECK (item_type IN ('action', 'project')),
                    CHECK (energy_level IS NULL OR (energy_level >= 1 AND energy_level <= 5))
                )
            """)

        conn.execute("""
                CREATE TABLE contexts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.execute("""
                CREATE TABLE stakeholders (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    organization_id TEXT,
                    team_id TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.execute("""
                CREATE TABLE gtd_item_stakeholders (
                    gtd_item_id TEXT NOT NULL,
                    stakeholder_id TEXT NOT NULL,
                    raci_role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (gtd_item_id, stakeholder_id, raci_role),
                    FOREIGN KEY (gtd_item_id) REFERENCES gtd_items(id) ON DELETE CASCADE,
                    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
                    CHECK (raci_role IN ('responsible', 'accountable', 'consulted', 'informed'))
                )
            """)

        conn.commit()
        yield conn


class TestBaseRepository:
    """Tests for base repository interface and common CRUD operations"""

    def test_base_repository_abstract_interface(self):
        """Test BaseRepository defines abstract interface for all repositories"""
        # BaseRepository should be abstract base class
        with pytest.raises(TypeError):
            BaseRepository()  # Cannot instantiate abstract class

    def test_base_repository_crud_methods_required(self):
        """Test BaseRepository requires implementation of CRUD methods"""
        # All concrete repositories must implement these methods
        required_methods = ["create", "read", "update", "delete", "list_all", "exists"]

        for method in required_methods:
            assert hasattr(BaseRepository, method)

    def test_base_repository_validation_integration(self):
        """Test BaseRepository integrates with validation system"""
        # Should support validation decorators
        assert hasattr(BaseRepository, "validate_before_save")
        assert hasattr(BaseRepository, "validate_business_rules")


class TestGTDItemRepository:
    """Tests for GTDItem repository with Action and Project persistence"""

    def test_gtd_item_repository_creation(self, db_connection):
        """Test GTDItemRepository can be instantiated with database connection"""
        repo = GTDItemRepository(db_connection)
        assert repo.connection == db_connection

    def test_create_action_with_database_persistence(self, db_connection):
        """Test creating Action saves to database correctly"""
        repo = GTDItemRepository(db_connection)

        action = Action(
            title="Call customer",
            description="Follow up on requirements",
            status=GTDStatus.INBOX,
            due_date=datetime.now(UTC),
            energy_level=3,
        )

        # Should save to database and return saved entity with generated ID
        saved_action = repo.create(action)

        assert saved_action.id is not None
        assert saved_action.title == "Call customer"
        assert saved_action.status == GTDStatus.INBOX
        assert saved_action.created_at is not None

    def test_create_project_with_database_persistence(self, db_connection):
        """Test creating Project saves to database correctly"""
        repo = GTDItemRepository(db_connection)

        project = Project(
            title="Launch new feature",
            description="Complete feature launch",
            status=GTDStatus.ORGANIZED,
            success_criteria="Feature is live and metrics are positive",
        )

        # Should save to database
        saved_project = repo.create(project)

        assert saved_project.id is not None
        assert saved_project.title == "Launch new feature"
        assert (
            saved_project.success_criteria == "Feature is live and metrics are positive"
        )

    def test_read_gtd_item_by_id(self, db_connection):
        """Test reading GTDItem from database by ID"""
        repo = GTDItemRepository(db_connection)

        # Create and save an action
        action = Action(title="Test action", status=GTDStatus.INBOX)
        saved_action = repo.create(action)

        # Should be able to read it back
        retrieved_action = repo.read(saved_action.id)

        assert retrieved_action is not None
        assert retrieved_action.id == saved_action.id
        assert retrieved_action.title == "Test action"
        assert isinstance(retrieved_action, Action)

    def test_read_nonexistent_gtd_item_raises_error(self, db_connection):
        """Test reading non-existent GTDItem raises appropriate error"""
        repo = GTDItemRepository(db_connection)

        with pytest.raises(GTDNotFoundError):
            repo.read("nonexistent-id")

    def test_update_gtd_item_in_database(self, db_connection):
        """Test updating GTDItem updates database record"""
        repo = GTDItemRepository(db_connection)

        # Create original action
        action = Action(title="Original title", status=GTDStatus.INBOX)
        saved_action = repo.create(action)

        # Update the action
        saved_action.title = "Updated title"
        saved_action.status = GTDStatus.ORGANIZED

        updated_action = repo.update(saved_action)

        # Should update database
        assert updated_action.title == "Updated title"
        assert updated_action.status == GTDStatus.ORGANIZED
        assert updated_action.updated_at > saved_action.created_at

    def test_delete_gtd_item_from_database(self, db_connection):
        """Test deleting GTDItem removes from database"""
        repo = GTDItemRepository(db_connection)

        # Create and save action
        action = Action(title="To be deleted", status=GTDStatus.INBOX)
        saved_action = repo.create(action)

        # Should exist initially
        assert repo.exists(saved_action.id)

        # Delete should remove from database
        repo.delete(saved_action.id)

        # Should no longer exist
        assert not repo.exists(saved_action.id)

        with pytest.raises(GTDNotFoundError):
            repo.read(saved_action.id)

    def test_list_gtd_items_by_status(self, db_connection):
        """Test listing GTDItems filtered by status"""
        repo = GTDItemRepository(db_connection)

        # Create items with different statuses
        inbox_action = Action(title="Inbox item", status=GTDStatus.INBOX)
        organized_action = Action(title="Organized item", status=GTDStatus.ORGANIZED)
        complete_action = Action(title="Complete item", status=GTDStatus.COMPLETE)

        repo.create(inbox_action)
        repo.create(organized_action)
        repo.create(complete_action)

        # Should filter by status
        inbox_items = repo.list_by_status(GTDStatus.INBOX)
        organized_items = repo.list_by_status(GTDStatus.ORGANIZED)

        assert len(inbox_items) == 1
        assert len(organized_items) == 1
        assert inbox_items[0].title == "Inbox item"
        assert organized_items[0].title == "Organized item"

    def test_list_actions_by_project(self, db_connection):
        """Test listing Actions that belong to specific Project"""
        repo = GTDItemRepository(db_connection)

        # Create project
        project = Project(
            title="Test project", status=GTDStatus.ORGANIZED, success_criteria="Success"
        )
        saved_project = repo.create(project)

        # Create actions in project
        action1 = Action(
            title="Project action 1",
            status=GTDStatus.ORGANIZED,
            project_id=saved_project.id,
        )
        action2 = Action(
            title="Project action 2",
            status=GTDStatus.ORGANIZED,
            project_id=saved_project.id,
        )
        standalone_action = Action(
            title="Standalone action", status=GTDStatus.ORGANIZED
        )

        repo.create(action1)
        repo.create(action2)
        repo.create(standalone_action)

        # Should return only actions from specific project
        project_actions = repo.list_actions_by_project(saved_project.id)

        assert len(project_actions) == 2
        assert all(action.project_id == saved_project.id for action in project_actions)

    def test_list_next_actions_workflow_query(self, db_connection):
        """Test GTD workflow query for next actions (organized, not complete)"""
        repo = GTDItemRepository(db_connection)

        # Create actions in different states
        next_action1 = Action(title="Next action 1", status=GTDStatus.ORGANIZED)
        next_action2 = Action(title="Next action 2", status=GTDStatus.ORGANIZED)
        inbox_action = Action(title="Inbox action", status=GTDStatus.INBOX)
        complete_action = Action(title="Complete action", status=GTDStatus.COMPLETE)

        repo.create(next_action1)
        repo.create(next_action2)
        repo.create(inbox_action)
        repo.create(complete_action)

        # Should return only organized actions (next actions)
        next_actions = repo.list_next_actions()

        assert len(next_actions) == 2
        assert all(action.status == GTDStatus.ORGANIZED for action in next_actions)
        assert all("Next action" in action.title for action in next_actions)


class TestContextRepository:
    """Tests for Context repository with GTD context management"""

    def test_context_repository_creation(self, db_connection):
        """Test ContextRepository can be instantiated"""
        repo = ContextRepository(db_connection)
        assert repo.connection == db_connection

    def test_create_context_with_validation(self, db_connection):
        """Test creating Context validates name format and saves to database"""
        repo = ContextRepository(db_connection)

        context = Context(name="@computer", description="Computer-based tasks")
        saved_context = repo.create(context)

        assert saved_context.id is not None
        assert saved_context.name == "@computer"
        assert saved_context.description == "Computer-based tasks"

    def test_create_context_duplicate_name_raises_error(self, db_connection):
        """Test creating Context with duplicate name raises error"""
        repo = ContextRepository(db_connection)

        # Create first context
        context1 = Context(name="@phone")
        repo.create(context1)

        # Duplicate should raise error
        with pytest.raises(GTDDuplicateError):
            context2 = Context(name="@phone")
            repo.create(context2)

    def test_list_contexts_alphabetically(self, db_connection):
        """Test listing contexts returns alphabetically sorted results"""
        repo = ContextRepository(db_connection)

        # Create contexts out of order
        repo.create(Context(name="@errands"))
        repo.create(Context(name="@computer"))
        repo.create(Context(name="@phone"))

        contexts = repo.list_all()

        # Should be alphabetically sorted
        context_names = [ctx.name for ctx in contexts]
        assert context_names == ["@computer", "@errands", "@phone"]

    def test_find_context_by_name(self, db_connection):
        """Test finding context by exact name match"""
        repo = ContextRepository(db_connection)

        context = Context(name="@waiting-for")
        saved_context = repo.create(context)

        found_context = repo.find_by_name("@waiting-for")

        assert found_context is not None
        assert found_context.id == saved_context.id

    def test_find_context_by_name_not_found(self, db_connection):
        """Test finding non-existent context returns None"""
        repo = ContextRepository(db_connection)

        found_context = repo.find_by_name("@nonexistent")
        assert found_context is None


class TestStakeholderRepository:
    """Tests for Stakeholder repository with organization relationships"""

    def test_stakeholder_repository_creation(self, db_connection):
        """Test StakeholderRepository can be instantiated"""
        repo = StakeholderRepository(db_connection)
        assert repo.connection == db_connection

    def test_create_stakeholder_with_organization(self, db_connection):
        """Test creating Stakeholder with organization relationship"""
        repo = StakeholderRepository(db_connection)

        stakeholder = Stakeholder(
            name="John Doe",
            email="john@example.com",
            organization_id="org123",
            role="Engineer",
        )

        saved_stakeholder = repo.create(stakeholder)

        assert saved_stakeholder.id is not None
        assert saved_stakeholder.name == "John Doe"
        assert saved_stakeholder.email == "john@example.com"
        assert saved_stakeholder.organization_id == "org123"

    def test_create_stakeholder_validates_email_format(self, db_connection):
        """Test creating Stakeholder validates email format"""
        with pytest.raises(ValueError):  # Domain model validation
            Stakeholder(
                name="Invalid Email", email="not-an-email", organization_id="org123"
            )

    def test_list_stakeholders_by_organization(self, db_connection):
        """Test listing stakeholders filtered by organization"""
        repo = StakeholderRepository(db_connection)

        # Create stakeholders in different organizations
        aws_stakeholder = Stakeholder(
            name="AWS Person", email="aws@amazon.com", organization_id="aws-org"
        )
        customer_stakeholder = Stakeholder(
            name="Customer Person",
            email="customer@acme.com",
            organization_id="customer-org",
        )

        repo.create(aws_stakeholder)
        repo.create(customer_stakeholder)

        # Should filter by organization
        aws_stakeholders = repo.list_by_organization("aws-org")

        assert len(aws_stakeholders) == 1
        assert aws_stakeholders[0].name == "AWS Person"

    def test_find_stakeholder_by_email(self, db_connection):
        """Test finding stakeholder by email address"""
        repo = StakeholderRepository(db_connection)

        stakeholder = Stakeholder(
            name="Test User", email="unique@example.com", organization_id="org123"
        )
        saved_stakeholder = repo.create(stakeholder)

        found_stakeholder = repo.find_by_email("unique@example.com")

        assert found_stakeholder is not None
        assert found_stakeholder.id == saved_stakeholder.id


class TestRACIRepository:
    """Tests for RACI relationship repository with constraint validation"""

    def setup_method(self):
        """Clear RACI registry before each test to ensure test isolation."""
        GTDItemStakeholder.clear_registry()

    def test_raci_repository_creation(self, db_connection):
        """Test RACIRepository can be instantiated"""
        repo = RACIRepository(db_connection)
        assert repo.connection == db_connection

    def test_add_raci_relationship(self, db_connection):
        """Test adding RACI relationship between GTDItem and Stakeholder"""
        # First create the required entities that will be referenced
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create GTD item and stakeholder first
        action = Action(title="Test action", status=GTDStatus.INBOX)
        saved_action = gtd_repo.create(action)

        stakeholder = Stakeholder(
            name="Test Stakeholder", email="test@example.com", organization_id="org123"
        )
        saved_stakeholder = stakeholder_repo.create(stakeholder)

        # Create relationship with valid foreign keys
        relationship = GTDItemStakeholder(
            gtd_item_id=saved_action.id,
            stakeholder_id=saved_stakeholder.id,
            raci_role=RACIRole.RESPONSIBLE,
        )

        saved_relationship = raci_repo.create(relationship)

        assert saved_relationship.gtd_item_id == saved_action.id
        assert saved_relationship.stakeholder_id == saved_stakeholder.id
        assert saved_relationship.raci_role == RACIRole.RESPONSIBLE

    def test_raci_exactly_one_accountable_constraint_enforced(self, db_connection):
        """Test database enforces exactly one Accountable per GTD item"""
        # Create required entities first
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create GTD item and stakeholders
        action = Action(title="Test action", status=GTDStatus.INBOX)
        saved_action = gtd_repo.create(action)

        stakeholder1 = Stakeholder(
            name="First Stakeholder",
            email="first@example.com",
            organization_id="org123",
        )
        saved_stakeholder1 = stakeholder_repo.create(stakeholder1)

        stakeholder2 = Stakeholder(
            name="Second Stakeholder",
            email="second@example.com",
            organization_id="org123",
        )
        saved_stakeholder2 = stakeholder_repo.create(stakeholder2)

        # First accountable should succeed
        relationship1 = GTDItemStakeholder(
            gtd_item_id=saved_action.id,
            stakeholder_id=saved_stakeholder1.id,
            raci_role=RACIRole.ACCOUNTABLE,
        )
        raci_repo.create(relationship1)

        # Second accountable for same item should fail during object construction
        with pytest.raises(
            ValueError, match="Only one Accountable allowed per GTD item"
        ):
            GTDItemStakeholder(
                gtd_item_id=saved_action.id,  # Same item
                stakeholder_id=saved_stakeholder2.id,  # Different stakeholder
                raci_role=RACIRole.ACCOUNTABLE,  # But also Accountable
            )

    def test_raci_multiple_other_roles_allowed(self, db_connection):
        """Test multiple Responsible/Consulted/Informed are allowed"""
        # Create required entities first
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create GTD item and stakeholders
        action = Action(title="Test action", status=GTDStatus.INBOX)
        saved_action = gtd_repo.create(action)

        stakeholder1 = Stakeholder(
            name="First Stakeholder",
            email="first@example.com",
            organization_id="org123",
        )
        saved_stakeholder1 = stakeholder_repo.create(stakeholder1)

        stakeholder2 = Stakeholder(
            name="Second Stakeholder",
            email="second@example.com",
            organization_id="org123",
        )
        saved_stakeholder2 = stakeholder_repo.create(stakeholder2)

        # Multiple responsible should work
        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=saved_action.id,
                stakeholder_id=saved_stakeholder1.id,
                raci_role=RACIRole.RESPONSIBLE,
            )
        )

        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=saved_action.id,
                stakeholder_id=saved_stakeholder2.id,
                raci_role=RACIRole.RESPONSIBLE,
            )
        )

        # Should not raise any errors
        responsible_relationships = raci_repo.list_by_gtd_item_and_role(
            saved_action.id, RACIRole.RESPONSIBLE
        )
        assert len(responsible_relationships) == 2

    def test_list_stakeholders_by_raci_role(self, db_connection):
        """Test listing stakeholders by RACI role for specific GTD item"""
        # Create required entities first
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create GTD item
        action = Action(title="Test action", status=GTDStatus.INBOX)
        saved_action = gtd_repo.create(action)

        # Create stakeholders for different roles
        responsible_stakeholder = Stakeholder(
            name="Responsible Person",
            email="responsible@example.com",
            organization_id="org123",
        )
        saved_responsible = stakeholder_repo.create(responsible_stakeholder)

        accountable_stakeholder = Stakeholder(
            name="Accountable Person",
            email="accountable@example.com",
            organization_id="org123",
        )
        saved_accountable = stakeholder_repo.create(accountable_stakeholder)

        consulted_stakeholder = Stakeholder(
            name="Consulted Person",
            email="consulted@example.com",
            organization_id="org123",
        )
        saved_consulted = stakeholder_repo.create(consulted_stakeholder)

        # Create relationships
        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=saved_action.id,
                stakeholder_id=saved_responsible.id,
                raci_role=RACIRole.RESPONSIBLE,
            )
        )

        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=saved_action.id,
                stakeholder_id=saved_accountable.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
        )

        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=saved_action.id,
                stakeholder_id=saved_consulted.id,
                raci_role=RACIRole.CONSULTED,
            )
        )

        # Should filter by role
        responsible = raci_repo.list_by_gtd_item_and_role(
            saved_action.id, RACIRole.RESPONSIBLE
        )
        accountable = raci_repo.list_by_gtd_item_and_role(
            saved_action.id, RACIRole.ACCOUNTABLE
        )
        consulted = raci_repo.list_by_gtd_item_and_role(
            saved_action.id, RACIRole.CONSULTED
        )

        assert len(responsible) == 1
        assert len(accountable) == 1
        assert len(consulted) == 1

    def test_remove_stakeholder_from_gtd_item(self, db_connection):
        """Test removing stakeholder relationship from GTD item"""
        # Create required entities first
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create GTD item and stakeholder
        action = Action(title="Test action", status=GTDStatus.INBOX)
        saved_action = gtd_repo.create(action)

        stakeholder = Stakeholder(
            name="Test Stakeholder", email="test@example.com", organization_id="org123"
        )
        saved_stakeholder = stakeholder_repo.create(stakeholder)

        # Create relationship
        relationship = GTDItemStakeholder(
            gtd_item_id=saved_action.id,
            stakeholder_id=saved_stakeholder.id,
            raci_role=RACIRole.INFORMED,
        )
        raci_repo.create(relationship)

        # Should exist initially
        relationships = raci_repo.list_by_gtd_item_and_role(
            saved_action.id, RACIRole.INFORMED
        )
        assert len(relationships) == 1

        # Remove relationship
        raci_repo.delete_by_gtd_item_and_stakeholder(
            saved_action.id, saved_stakeholder.id
        )

        # Should be removed
        relationships = raci_repo.list_by_gtd_item_and_role(
            saved_action.id, RACIRole.INFORMED
        )
        assert len(relationships) == 0


class TestRepositoryComplexQueries:
    """Tests for complex queries and relationships across repositories"""

    def setup_method(self):
        """Clear RACI registry before each test to ensure test isolation."""
        GTDItemStakeholder.clear_registry()

    def test_gtd_workflow_queries_with_stakeholder_filtering(self, db_connection):
        """Test complex GTD workflow queries with stakeholder relationships"""
        # Setup repositories
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create stakeholders
        alice = stakeholder_repo.create(
            Stakeholder(
                name="Alice Engineer",
                email="alice@company.com",
                organization_id="internal-org",
            )
        )
        bob = stakeholder_repo.create(
            Stakeholder(
                name="Bob Manager",
                email="bob@company.com",
                organization_id="internal-org",
            )
        )

        # Create mixed actions and projects
        high_priority_action = gtd_repo.create(
            Action(title="Critical bug fix", status=GTDStatus.ORGANIZED, energy_level=5)
        )

        medium_priority_action = gtd_repo.create(
            Action(
                title="Update documentation", status=GTDStatus.ORGANIZED, energy_level=2
            )
        )

        project = gtd_repo.create(
            Project(
                title="Major refactoring",
                status=GTDStatus.ORGANIZED,
                success_criteria="Code is 50% more maintainable",
            )
        )

        # Add RACI relationships
        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=high_priority_action.id,
                stakeholder_id=alice.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
        )
        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=medium_priority_action.id,
                stakeholder_id=bob.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
        )
        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=project.id,
                stakeholder_id=bob.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
        )

        # Test query: Get all next actions for Alice
        alice_actions = self._get_next_actions_for_stakeholder(db_connection, alice.id)
        assert len(alice_actions) == 1
        assert alice_actions[0]["title"] == "Critical bug fix"

        # Test query: Get all items (actions + projects) for Bob
        bob_items = self._get_all_items_for_stakeholder(db_connection, bob.id)
        assert len(bob_items) == 2

        # Test query: Get high-energy actions
        high_energy_actions = self._get_actions_by_energy_level(
            db_connection, min_energy=4
        )
        assert len(high_energy_actions) == 1
        assert high_energy_actions[0]["energy_level"] == 5

    def test_project_hierarchy_queries(self, db_connection):
        """Test complex queries for project hierarchies and action relationships"""
        gtd_repo = GTDItemRepository(db_connection)

        # Create project with multiple actions
        project = gtd_repo.create(
            Project(
                title="Website Redesign",
                status=GTDStatus.ORGANIZED,
                success_criteria="New site increases conversion by 20%",
            )
        )

        # Create actions within project
        actions = []
        for i, title in enumerate(
            ["Design mockups", "Implement frontend", "Write tests", "Deploy"]
        ):
            action = gtd_repo.create(
                Action(
                    title=title,
                    status=GTDStatus.ORGANIZED if i < 2 else GTDStatus.INBOX,
                    project_id=project.id,
                    energy_level=3,
                )
            )
            actions.append(action)

        # Create standalone action
        gtd_repo.create(
            Action(title="Standalone task", status=GTDStatus.ORGANIZED, energy_level=2)
        )

        # Test query: Get project completion stats
        project_stats = self._get_project_completion_stats(db_connection, project.id)
        assert project_stats["total_actions"] == 4
        assert project_stats["organized_actions"] == 2
        assert project_stats["completion_percentage"] == 50.0

        # Test query: Get actions grouped by project
        project_groups = self._get_actions_grouped_by_project(db_connection)
        assert len(project_groups) == 2  # One project + None for standalone
        assert project_groups[project.id]["action_count"] == 4
        assert project_groups[None]["action_count"] == 1

    def test_stakeholder_workload_analysis_queries(self, db_connection):
        """Test complex queries for stakeholder workload analysis"""
        # Setup data
        gtd_repo = GTDItemRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create stakeholders in different organizations
        internal_stakeholder = stakeholder_repo.create(
            Stakeholder(
                name="Internal Dev",
                email="dev@company.com",
                organization_id="internal-org",
            )
        )
        external_stakeholder = stakeholder_repo.create(
            Stakeholder(
                name="External Consultant",
                email="consultant@external.com",
                organization_id="external-org",
            )
        )

        # Create various actions with different energy levels
        actions = []
        for i in range(5):
            action = gtd_repo.create(
                Action(
                    title=f"Task {i + 1}",
                    status=GTDStatus.ORGANIZED,
                    energy_level=(i % 5) + 1,  # 1-5 energy levels
                )
            )
            actions.append(action)

        # Assign different workloads
        for i, action in enumerate(actions):
            stakeholder = internal_stakeholder if i < 3 else external_stakeholder
            role = RACIRole.ACCOUNTABLE if i % 2 == 0 else RACIRole.RESPONSIBLE
            raci_repo.create(
                GTDItemStakeholder(
                    gtd_item_id=action.id, stakeholder_id=stakeholder.id, raci_role=role
                )
            )

        # Test query: Get workload by stakeholder
        workloads = self._get_stakeholder_workloads(db_connection)
        assert len(workloads) == 2

        internal_workload = next(
            w for w in workloads if w["stakeholder_id"] == internal_stakeholder.id
        )
        assert internal_workload["total_tasks"] == 3
        assert internal_workload["avg_energy_level"] == 2.0  # (1+2+3)/3

        # Test query: Get cross-organizational collaboration
        collaboration_stats = self._get_cross_org_collaboration_stats(db_connection)
        assert collaboration_stats["total_organizations"] == 2
        assert collaboration_stats["collaborative_tasks"] >= 0

    # Helper methods for complex queries
    def _get_next_actions_for_stakeholder(self, connection, stakeholder_id):
        """Get next actions assigned to specific stakeholder"""
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT g.id, g.title, g.energy_level, g.status
            FROM gtd_items g
            JOIN gtd_item_stakeholders gis ON g.id = gis.gtd_item_id
            WHERE gis.stakeholder_id = ?
              AND g.status = 'organized'
              AND g.item_type = 'action'
              AND gis.raci_role IN ('accountable', 'responsible')
            ORDER BY g.energy_level DESC, g.created_at ASC
        """,
            (stakeholder_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_all_items_for_stakeholder(self, connection, stakeholder_id):
        """Get all GTD items (actions + projects) for stakeholder"""
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT g.id, g.title, g.item_type, g.status, gis.raci_role
            FROM gtd_items g
            JOIN gtd_item_stakeholders gis ON g.id = gis.gtd_item_id
            WHERE gis.stakeholder_id = ?
            ORDER BY g.item_type, g.created_at
        """,
            (stakeholder_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_actions_by_energy_level(self, connection, min_energy):
        """Get actions with minimum energy level"""
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, title, energy_level, status
            FROM gtd_items
            WHERE item_type = 'action' AND energy_level >= ?
            ORDER BY energy_level DESC
        """,
            (min_energy,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_project_completion_stats(self, connection, project_id):
        """Get completion statistics for a project"""
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) as total_actions,
                SUM(CASE WHEN status IN ('organized', 'reviewing') THEN 1 ELSE 0 END) as organized_actions,
                SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as completed_actions,
                ROUND(
                    (SUM(CASE WHEN status IN ('organized', 'reviewing') THEN 1 ELSE 0 END) * 100.0) / COUNT(*),
                    1
                ) as completion_percentage
            FROM gtd_items
            WHERE project_id = ? AND item_type = 'action'
        """,
            (project_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else {}

    def _get_actions_grouped_by_project(self, connection):
        """Get actions grouped by project"""
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                project_id,
                COUNT(*) as action_count,
                AVG(energy_level) as avg_energy_level
            FROM gtd_items
            WHERE item_type = 'action'
            GROUP BY project_id
        """)
        return {row["project_id"]: dict(row) for row in cursor.fetchall()}

    def _get_stakeholder_workloads(self, connection):
        """Get workload analysis by stakeholder"""
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                gis.stakeholder_id,
                s.name as stakeholder_name,
                s.organization_id,
                COUNT(*) as total_tasks,
                AVG(CAST(g.energy_level AS FLOAT)) as avg_energy_level,
                SUM(CASE WHEN gis.raci_role = 'accountable' THEN 1 ELSE 0 END) as accountable_count,
                SUM(CASE WHEN gis.raci_role = 'responsible' THEN 1 ELSE 0 END) as responsible_count
            FROM gtd_item_stakeholders gis
            JOIN stakeholders s ON gis.stakeholder_id = s.id
            JOIN gtd_items g ON gis.gtd_item_id = g.id
            WHERE g.status IN ('organized', 'reviewing')
            GROUP BY gis.stakeholder_id, s.name, s.organization_id
        """)
        return [dict(row) for row in cursor.fetchall()]

    def _get_cross_org_collaboration_stats(self, connection):
        """Get statistics on cross-organizational collaboration"""
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                COUNT(DISTINCT s.organization_id) as total_organizations,
                COUNT(DISTINCT CASE
                    WHEN EXISTS (
                        SELECT 1 FROM gtd_item_stakeholders gis2
                        JOIN stakeholders s2 ON gis2.stakeholder_id = s2.id
                        WHERE gis2.gtd_item_id = gis.gtd_item_id
                        AND s2.organization_id != s.organization_id
                    ) THEN gis.gtd_item_id
                END) as collaborative_tasks
            FROM gtd_item_stakeholders gis
            JOIN stakeholders s ON gis.stakeholder_id = s.id
        """)
        row = cursor.fetchone()
        return dict(row) if row else {}


class TestRepositoryIntegration:
    """Integration tests combining multiple repositories"""

    def test_complete_gtd_workflow_with_repositories(self, db_connection):
        """Test complete GTD workflow using repository pattern"""
        # Initialize repositories
        gtd_repo = GTDItemRepository(db_connection)
        context_repo = ContextRepository(db_connection)
        stakeholder_repo = StakeholderRepository(db_connection)
        raci_repo = RACIRepository(db_connection)

        # Create contexts
        context_repo.create(Context(name="@computer"))
        context_repo.create(Context(name="@phone"))

        # Create stakeholders
        engineer = stakeholder_repo.create(
            Stakeholder(
                name="Alice Engineer",
                email="alice@company.com",
                organization_id="internal-org",
            )
        )

        customer = stakeholder_repo.create(
            Stakeholder(
                name="Bob Customer",
                email="bob@customer.com",
                organization_id="customer-org",
            )
        )

        # Create GTD item
        action = gtd_repo.create(
            Action(
                title="Fix customer bug",
                description="Resolve authentication issue",
                status=GTDStatus.ORGANIZED,
                energy_level=4,
            )
        )

        # Add RACI relationships
        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=action.id,
                stakeholder_id=engineer.id,
                raci_role=RACIRole.ACCOUNTABLE,
            )
        )

        raci_repo.create(
            GTDItemStakeholder(
                gtd_item_id=action.id,
                stakeholder_id=customer.id,
                raci_role=RACIRole.INFORMED,
            )
        )

        # Verify complete workflow
        next_actions = gtd_repo.list_next_actions()
        assert len(next_actions) == 1
        assert next_actions[0].title == "Fix customer bug"

        # Verify stakeholder relationships
        accountable_rels = raci_repo.list_by_gtd_item_and_role(
            action.id, RACIRole.ACCOUNTABLE
        )
        informed_rels = raci_repo.list_by_gtd_item_and_role(
            action.id, RACIRole.INFORMED
        )

        assert len(accountable_rels) == 1
        assert len(informed_rels) == 1

    def test_repository_transaction_rollback_on_error(self, db_connection):
        """Test repository operations rollback on database errors"""
        context_repo = ContextRepository(db_connection)

        # This test will verify transaction handling
        # Should rollback on constraint violations or other database errors

        # Create context that will succeed
        context1 = Context(name="@computer", description="Computer tasks")
        saved_context1 = context_repo.create(context1)
        assert saved_context1.id is not None

        # Attempt operation that should fail due to unique constraint violation
        with pytest.raises(GTDDuplicateError):
            # This should fail due to unique constraint on context name
            duplicate_context = Context(
                name="@computer", description="Duplicate computer"
            )
            context_repo.create(duplicate_context)

        # Original context should still exist (transaction isolation)
        retrieved_context = context_repo.read(saved_context1.id)
        assert retrieved_context.name == "@computer"
