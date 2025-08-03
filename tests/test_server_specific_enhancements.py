"""
Tests for specific server enhancements that need implementation.

These tests are designed to fail initially and drive the implementation
of specific enhancements to the server.
"""

from unittest.mock import patch

import pytest


class TestServerEnhancementsNeeded:
    """Tests for specific enhancements needed in server.py."""

    def test_main_function_handles_keyboard_interrupt_gracefully(self):
        """Test that main function handles KeyboardInterrupt with proper logging."""
        from gtd_manager.server import main

        # This should fail initially - we need to add KeyboardInterrupt handling
        with (
            patch("gtd_manager.server.server.run", side_effect=KeyboardInterrupt()),
            patch("sys.exit") as mock_exit,
            patch("gtd_manager.server.logger") as mock_logger,
        ):
            try:
                main()
            except KeyboardInterrupt:
                # If KeyboardInterrupt isn't handled, this test should fail
                pytest.fail("KeyboardInterrupt was not handled gracefully by main()")

            # Should handle KeyboardInterrupt and exit with 0 (not 1)
            mock_exit.assert_called_once_with(0)

            # Should log graceful shutdown message
            shutdown_logged = any(
                "shutdown" in str(call) or "stopping" in str(call)
                for call in mock_logger.info.call_args_list
            )
            assert shutdown_logged, "Should log graceful shutdown message"

    def test_server_has_enhanced_version_logging(self):
        """Test that server logs version information on startup."""
        from gtd_manager.server import main

        with (
            patch("gtd_manager.server.server.run"),
            patch("gtd_manager.server.logger") as mock_logger,
        ):
            main()

            # Should log version information
            version_logged = any(
                "version" in str(call).lower()
                for call in mock_logger.info.call_args_list
            )
            assert version_logged, "Should log version information on startup"

    def test_server_startup_includes_server_name_in_logs(self):
        """Test that startup logs include the server name."""
        from gtd_manager.server import main

        with (
            patch("gtd_manager.server.server.run"),
            patch("gtd_manager.server.logger") as mock_logger,
        ):
            main()

            # Should mention GTD Manager in startup logs
            startup_calls = [str(call) for call in mock_logger.info.call_args_list]
            gtd_mentioned = any("GTD" in call for call in startup_calls)
            assert gtd_mentioned, "Should mention GTD Manager in startup logs"
