"""
Tests for FastMCP server infrastructure.

These tests verify that the FastMCP server is properly configured,
tools are registered correctly, and the server responds to MCP commands.
"""

import sys
from io import StringIO
from unittest.mock import patch

import pytest
from fastmcp import Client


class TestFastMcpServerInitialization:
    """Test FastMCP server initialization and configuration."""

    def test_server_import_creates_fastmcp_instance(self):
        """Test that importing server module creates a FastMCP instance."""
        # Verify server is a FastMCP instance
        from fastmcp import FastMCP

        from gtd_manager.server import server

        assert isinstance(server, FastMCP)
        assert server.name == "gtd-manager"

    def test_server_has_logging_configured(self):
        """Test that server module configures logging properly."""
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            # Import server module which configures logging
            import gtd_manager.server  # noqa: F401

            # Verify no stdout contamination
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", (
                f"Server import contaminated stdout: {repr(stdout_content)}"
            )

    def test_server_metadata_configuration(self):
        """Test that server has proper metadata configuration."""
        from gtd_manager.server import server

        assert server.name == "gtd-manager"
        # FastMCP server should be properly configured
        assert hasattr(server, "name")
        assert hasattr(server, "tool")

    @pytest.mark.asyncio
    async def test_server_client_connection(self):
        """Test that FastMCP Client can connect to server."""
        from gtd_manager.server import server

        # Test client connection
        async with Client(server) as client:
            # Verify client connected successfully
            assert client is not None

            # Test basic server communication
            tools = await client.list_tools()
            assert tools is not None
            assert len(tools) > 0

    def test_server_main_function_exists(self):
        """Test that main function exists and is callable."""
        from gtd_manager.server import main

        assert callable(main)

    def test_server_graceful_error_handling(self):
        """Test that server handles initialization errors gracefully."""
        # This tests the try/catch block in main()
        from gtd_manager.server import main

        # Mock sys.exit to prevent actual exit during test
        with (
            patch("sys.exit") as mock_exit,
            patch("gtd_manager.server.server.run", side_effect=Exception("Test error")),
        ):
            main()
            # Verify sys.exit was called with error code
            mock_exit.assert_called_once_with(1)


class TestToolRegistration:
    """Test tool registration and discovery."""

    @pytest.mark.asyncio
    async def test_hello_world_tool_registered(self):
        """Test that hello_world tool is properly registered."""
        from gtd_manager.server import server

        async with Client(server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            assert "hello_world" in tool_names

    @pytest.mark.asyncio
    async def test_hello_world_tool_callable(self):
        """Test that hello_world tool can be called."""
        from gtd_manager.server import server

        async with Client(server) as client:
            result = await client.call_tool("hello_world", {"name": "TestUser"})
            assert result.data is not None
            assert "Hello, TestUser!" in result.data
            assert "GTD Manager MCP Server is running" in result.data

    @pytest.mark.asyncio
    async def test_hello_world_tool_default_parameter(self):
        """Test that hello_world tool works with default parameters."""
        from gtd_manager.server import server

        async with Client(server) as client:
            result = await client.call_tool("hello_world", {})
            assert result.data is not None
            assert "Hello, World!" in result.data

    @pytest.mark.asyncio
    async def test_tool_execution_maintains_protocol_compliance(self):
        """Test that tool execution doesn't contaminate stdout."""
        from gtd_manager.server import server

        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            async with Client(server) as client:
                await client.call_tool("hello_world", {"name": "TestProtocol"})

                # Verify stdout remains clean
                stdout_content = captured_stdout.getvalue()
                assert stdout_content == "", (
                    f"Tool execution contaminated stdout: {repr(stdout_content)}"
                )


class TestServerConfiguration:
    """Test server configuration and setup."""

    def test_server_uses_structured_logging(self):
        """Test that server is configured for structured logging."""
        import logging

        # Import server to trigger logging configuration
        import gtd_manager.server  # noqa: F401

        # Check that logging is configured
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

        # Verify handler streams to stderr
        stderr_handlers = [
            h
            for h in root_logger.handlers
            if hasattr(h, "stream") and h.stream == sys.stderr
        ]
        assert len(stderr_handlers) > 0

    def test_structlog_configuration(self):
        """Test that structlog is properly configured."""
        import structlog

        # Import server to trigger structlog configuration
        import gtd_manager.server  # noqa: F401

        # Get a logger and verify it works
        logger = structlog.get_logger("test")
        assert logger is not None

        # Test that we can log without stdout contamination
        captured_stdout = StringIO()
        with patch("sys.stdout", captured_stdout):
            logger.info("test message", test_key="test_value")
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", "Structlog contaminated stdout"

    @pytest.mark.asyncio
    async def test_server_tool_discovery(self):
        """Test that server can discover and list all registered tools."""
        from gtd_manager.server import server

        async with Client(server) as client:
            tools = await client.list_tools()

            # Should have at least the hello_world tool
            assert len(tools) >= 1

            # Verify tool structure
            hello_tool = next((t for t in tools if t.name == "hello_world"), None)
            assert hello_tool is not None
            assert hello_tool.description is not None
            assert len(hello_tool.description) > 0


# Integration test that runs the full server lifecycle
class TestServerIntegration:
    """Integration tests for complete server functionality."""

    @pytest.mark.asyncio
    async def test_full_server_client_interaction(self):
        """Test complete server-client interaction cycle."""
        from gtd_manager.server import server

        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            async with Client(server) as client:
                # Test 1: List tools
                tools = await client.list_tools()
                assert len(tools) >= 1

                # Test 2: Call a tool
                result = await client.call_tool("hello_world", {"name": "Integration"})
                assert "Hello, Integration!" in result.data

                # Test 3: Verify protocol compliance throughout
                stdout_content = captured_stdout.getvalue()
                assert stdout_content == "", (
                    f"Integration test contaminated stdout: {repr(stdout_content)}"
                )

    def test_server_module_import_idempotent(self):
        """Test that importing server module multiple times is safe."""
        # Import multiple times should not cause issues
        import gtd_manager.server as server1
        import gtd_manager.server as server2

        # Should be the same module
        assert server1 is server2
        assert server1.server is server2.server
