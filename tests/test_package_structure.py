"""
Tests for package import structure and organization.

These tests verify that the gtd_manager package is properly structured
and all imports work correctly.
"""

from pathlib import Path

import pytest


def test_package_directory_exists():
    """Test that the main package directory exists."""
    package_path = Path("src/gtd_manager")
    assert package_path.exists(), "src/gtd_manager directory should exist"
    assert package_path.is_dir(), "src/gtd_manager should be a directory"


def test_package_init_exists():
    """Test that the package __init__.py file exists."""
    init_path = Path("src/gtd_manager/__init__.py")
    assert init_path.exists(), "src/gtd_manager/__init__.py should exist"
    assert init_path.is_file(), "__init__.py should be a file"


def test_package_can_be_imported():
    """Test that the main package can be imported."""
    try:
        import gtd_manager  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Failed to import gtd_manager package: {e}")


def test_server_module_can_be_imported():
    """Test that the server module can be imported."""
    try:
        from gtd_manager import server  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Failed to import gtd_manager.server: {e}")


def test_server_module_exists():
    """Test that server.py module file exists."""
    server_path = Path("src/gtd_manager/server.py")
    assert server_path.exists(), "src/gtd_manager/server.py should exist"
    assert server_path.is_file(), "server.py should be a file"


def test_package_version_accessible():
    """Test that package version can be accessed."""
    try:
        import gtd_manager

        # Should have __version__ attribute
        assert hasattr(gtd_manager, "__version__"), (
            "Package should have __version__ attribute"
        )
        assert isinstance(gtd_manager.__version__, str), (
            "__version__ should be a string"
        )
    except ImportError as e:
        pytest.fail(f"Failed to import gtd_manager for version check: {e}")


def test_main_entry_point_exists():
    """Test that the main entry point function exists in server module."""
    try:
        from gtd_manager.server import main

        assert callable(main), "main function should be callable"
    except ImportError as e:
        pytest.fail(f"Failed to import main function from gtd_manager.server: {e}")


class TestPackageStructure:
    """Test class for verifying the overall package structure."""

    def test_src_directory_structure(self):
        """Test that the src directory has the correct structure."""
        src_path = Path("src")
        assert src_path.exists(), "src directory should exist"
        assert src_path.is_dir(), "src should be a directory"

        gtd_manager_path = src_path / "gtd_manager"
        assert gtd_manager_path.exists(), "gtd_manager package should exist in src"
        assert gtd_manager_path.is_dir(), "gtd_manager should be a directory"

    def test_package_modules_structure(self):
        """Test that expected module files exist in the package."""
        base_path = Path("src/gtd_manager")

        expected_files = [
            "__init__.py",
            "server.py",
        ]

        for filename in expected_files:
            file_path = base_path / filename
            assert file_path.exists(), f"{filename} should exist in gtd_manager package"
            assert file_path.is_file(), f"{filename} should be a file"
