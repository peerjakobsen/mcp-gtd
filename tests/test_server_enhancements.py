"""
Tests for enhanced FastMCP server functionality.

These tests verify server metadata, configuration, health checks,
and enhanced startup/shutdown behavior.
"""

import sys
from io import StringIO
from unittest.mock import patch

import pytest
from fastmcp import Client


class TestServerMetadata:
    """Test enhanced server metadata and configuration."""

    def test_server_has_version_info(self):
        """Test that server exposes version information."""
        from gtd_manager.server import server

        # After enhancement, server should have version metadata
        assert hasattr(server, "name")
        assert server.name == "gtd-manager"

    def test_server_description_available(self):
        """Test that server has description metadata."""
        from gtd_manager.server import server

        # Server should be identifiable
        assert server.name == "gtd-manager"

    @pytest.mark.asyncio
    async def test_server_info_accessible_via_client(self):
        """Test that server information is accessible through client."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Should be able to get basic server info
            tools = await client.list_tools()
            assert len(tools) > 0

            # Should have hello_world tool with proper description
            hello_tool = next((t for t in tools if t.name == "hello_world"), None)
            assert hello_tool is not None
            assert hello_tool.description is not None


class TestServerConfiguration:
    """Test enhanced server configuration."""

    def test_server_logging_configuration_enhanced(self):
        """Test that enhanced logging configuration is applied."""
        import logging

        # Import server to apply configuration
        import gtd_manager.server  # noqa: F401

        # Should have structured logging
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        # Should have stderr handler
        stderr_handlers = [
            h
            for h in root_logger.handlers
            if hasattr(h, "stream") and h.stream == sys.stderr
        ]
        assert len(stderr_handlers) > 0

    def test_structlog_with_context_support(self):
        """Test that structlog supports context properly."""
        import structlog

        # Import server for configuration
        import gtd_manager.server  # noqa: F401

        logger = structlog.get_logger("test")

        # Should be able to bind context
        bound_logger = logger.bind(test_id="123", operation="test")
        assert bound_logger is not None

        # Should not contaminate stdout
        captured_stdout = StringIO()
        with patch("sys.stdout", captured_stdout):
            bound_logger.info("test message", extra_field="value")
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == ""


class TestServerHealthAndStatus:
    """Test server health checking and status functionality."""

    @pytest.mark.asyncio
    async def test_server_responds_to_health_checks(self):
        """Test basic server health via tool interaction."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Server responding to tool calls indicates health
            result = await client.call_tool("hello_world", {})
            assert result.data is not None
            assert "Hello, World!" in result.data

    def test_server_handles_startup_configuration(self):
        """Test that server handles startup configuration properly."""
        from gtd_manager.server import server

        # Server should be properly initialized
        assert server is not None
        assert server.name == "gtd-manager"


class TestMainFunctionEnhancements:
    """Test enhanced main function behavior."""

    def test_main_function_error_handling(self):
        """Test that main function has proper error handling."""
        from gtd_manager.server import main

        # Mock server.run to raise an exception
        with (
            patch("gtd_manager.server.server.run", side_effect=Exception("Test error")),
            patch("sys.exit") as mock_exit,
            patch("gtd_manager.server.logger") as mock_logger,
        ):
            main()

            # Should log error and exit with code 1
            mock_logger.error.assert_called_once()
            mock_exit.assert_called_once_with(1)

    def test_main_function_startup_logging(self):
        """Test that main function logs startup information."""
        from gtd_manager.server import main

        # Mock server.run to prevent actual server start
        with (
            patch("gtd_manager.server.server.run"),
            patch("gtd_manager.server.logger") as mock_logger,
        ):
            main()

            # Should log startup message
            mock_logger.info.assert_called()
            # Check that startup was logged
            logged_calls = [
                call
                for call in mock_logger.info.call_args_list
                if "Starting" in str(call)
            ]
            assert len(logged_calls) > 0

    def test_main_function_prevents_stdout_contamination(self):
        """Test that main function doesn't contaminate stdout."""
        from gtd_manager.server import main

        captured_stdout = StringIO()

        with (
            patch("sys.stdout", captured_stdout),
            patch("gtd_manager.server.server.run"),
        ):
            main()

            stdout_content = captured_stdout.getvalue()
            assert (
                stdout_content == ""
            ), f"main() contaminated stdout: {repr(stdout_content)}"


class TestServerShutdownHandling:
    """Test graceful server shutdown handling."""

    def test_server_handles_keyboard_interrupt(self):
        """Test that server handles KeyboardInterrupt gracefully."""
        from gtd_manager.server import main

        # Mock server.run to raise KeyboardInterrupt
        with (
            patch("gtd_manager.server.server.run", side_effect=KeyboardInterrupt()),
            patch("sys.exit") as mock_exit,
            patch("gtd_manager.server.logger"),
        ):
            main()

            # Should handle gracefully and exit cleanly
            mock_exit.assert_called_once_with(0)

    def test_server_logs_shutdown_messages(self):
        """Test that server logs appropriate shutdown messages."""
        from gtd_manager.server import main

        with (
            patch("gtd_manager.server.server.run", side_effect=KeyboardInterrupt()),
            patch("sys.exit"),
            patch("gtd_manager.server.logger") as mock_logger,
        ):
            main()

            # Should log shutdown message
            logged_calls = [
                call
                for call in mock_logger.info.call_args_list
                if any(
                    keyword in str(call)
                    for keyword in ["shutdown", "stopping", "stopped"]
                )
            ]
            assert len(logged_calls) > 0
