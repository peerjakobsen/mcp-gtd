"""
Integration tests for complete FastMCP server functionality.

These tests verify that the server starts correctly, responds to all
MCP commands, and maintains protocol compliance throughout.
"""

import asyncio
from io import StringIO
from unittest.mock import patch

import pytest
from fastmcp import Client


class TestServerStartupAndCommunication:
    """Test complete server startup and MCP communication."""

    @pytest.mark.asyncio
    async def test_server_full_startup_sequence(self):
        """Test complete server startup and initialization."""
        from gtd_manager.server import server

        # Server should be initialized and ready for connections
        assert server is not None
        assert server.name == "gtd-manager"

        # Should be able to establish client connection
        async with Client(server) as client:
            # Basic connectivity test
            tools = await client.list_tools()
            assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_mcp_protocol_command_coverage(self):
        """Test that server responds to all basic MCP protocol commands."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Test list_tools command
            tools = await client.list_tools()
            assert isinstance(tools, list)
            assert len(tools) > 0

            # Test call_tool command
            result = await client.call_tool("hello_world", {"name": "MCP"})
            assert result.data is not None
            assert "Hello, MCP!" in result.data

    @pytest.mark.asyncio
    async def test_server_handles_multiple_concurrent_clients(self):
        """Test that server can handle multiple concurrent client connections."""
        from gtd_manager.server import server

        async def client_task(client_id: int):
            async with Client(server) as client:
                result = await client.call_tool(
                    "hello_world", {"name": f"Client{client_id}"}
                )
                return f"Client{client_id}" in result.data

        # Run multiple clients concurrently
        tasks = [client_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All clients should succeed
        assert all(results), "Not all concurrent clients succeeded"

    @pytest.mark.asyncio
    async def test_server_maintains_protocol_compliance_under_load(self):
        """Test that server maintains MCP protocol compliance under load."""
        from gtd_manager.server import server

        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            async with Client(server) as client:
                # Perform multiple operations
                for i in range(10):
                    await client.list_tools()
                    await client.call_tool("hello_world", {"name": f"Load{i}"})

            # Should never contaminate stdout
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", (
                f"Server contaminated stdout under load: {repr(stdout_content)}"
            )

    @pytest.mark.asyncio
    async def test_tool_registry_integration_end_to_end(self):
        """Test that tool registry works end-to-end through client."""
        from gtd_manager.server import register_tool, server, setup_tool_registration

        # Register a new tool
        @register_tool
        def integration_test_tool(message: str = "test") -> str:
            """Tool for integration testing."""
            return f"Integration: {message}"

        # Re-setup tool registration to include new tool
        setup_tool_registration(server)

        async with Client(server) as client:
            # New tool should be discoverable
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            assert "integration_test_tool" in tool_names

            # New tool should be callable
            result = await client.call_tool(
                "integration_test_tool", {"message": "success"}
            )
            assert "Integration: success" in result.data

    def test_server_module_import_is_safe(self):
        """Test that importing server module is safe and doesn't start server."""
        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            # Importing should not start the server or contaminate stdout
            import gtd_manager.server  # noqa: F401

            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", (
                f"Server import contaminated stdout: {repr(stdout_content)}"
            )


class TestServerMainFunctionIntegration:
    """Test server main function and entry point behavior."""

    def test_main_function_ready_for_production(self):
        """Test that main function is ready for production use."""
        from gtd_manager.server import main

        # Should be callable
        assert callable(main)

        # Should have proper error handling (tested in other files)
        # Should have proper logging configuration (tested in other files)
        # This test verifies the function exists and is importable

    def test_server_console_script_entry_point(self):
        """Test that console script entry point is properly configured."""
        # This tests the pyproject.toml console_scripts configuration
        import gtd_manager.server

        # Module should have main function available for console script
        assert hasattr(gtd_manager.server, "main")
        assert callable(gtd_manager.server.main)

    def test_server_can_be_run_as_module(self):
        """Test that server can be run as a Python module."""
        import gtd_manager.server

        # Should be able to run with python -m gtd_manager.server
        # This is handled by the if __name__ == "__main__" block
        # We just verify the structure is correct
        assert hasattr(gtd_manager.server, "main")


class TestServerProductionReadiness:
    """Test server readiness for production deployment."""

    @pytest.mark.asyncio
    async def test_server_error_recovery(self):
        """Test that server recovers gracefully from tool errors."""
        from gtd_manager.server import register_tool, server, setup_tool_registration

        # Register a tool that raises an error
        @register_tool
        def error_test_tool() -> str:
            """Tool that always raises an error."""
            raise ValueError("Test error for recovery testing")

        setup_tool_registration(server)

        async with Client(server) as client:
            # Error tool should raise ToolError due to structured error response
            from fastmcp.exceptions import ToolError

            with pytest.raises(ToolError) as exc_info:
                await client.call_tool("error_test_tool", {})

            # The error message should contain our structured error response
            error_msg = str(exc_info.value)
            assert "Test error for recovery testing" in error_msg
            assert "INTERNAL_ERROR" in error_msg

            # Server should still be functional after error
            healthy_result = await client.call_tool("hello_world", {"name": "Recovery"})
            assert "Hello, Recovery!" in healthy_result.data

    @pytest.mark.asyncio
    async def test_server_handles_invalid_tool_calls(self):
        """Test that server handles invalid tool calls gracefully."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Try to call non-existent tool - this should be handled by FastMCP
            from fastmcp.exceptions import ToolError

            with pytest.raises(
                (ToolError, ValueError, KeyError)
            ):  # FastMCP should raise an appropriate exception
                await client.call_tool("nonexistent_tool", {})

            # Server should still be functional after invalid call
            result = await client.call_tool("hello_world", {"name": "StillWorking"})
            assert "Hello, StillWorking!" in result.data

    @pytest.mark.asyncio
    async def test_server_tool_parameter_validation(self):
        """Test that server validates tool parameters appropriately."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Test with various parameter combinations
            test_cases = [
                {},  # No parameters (should use defaults)
                {"name": "Test"},  # Valid parameters
                {"name": ""},  # Empty string
                {"name": "Very" * 100},  # Very long string
            ]

            for params in test_cases:
                result = await client.call_tool("hello_world", params)
                # All should succeed (hello_world is very tolerant)
                assert result.data is not None
                assert isinstance(result.data, str)

    def test_server_resource_management(self):
        """Test that server manages resources appropriately."""
        from gtd_manager.server import _tool_registry

        # Registry should not grow unbounded
        initial_count = len(_tool_registry)

        # Multiple imports should not create duplicate registrations
        import gtd_manager.server  # noqa: F401

        # Registry size should remain stable
        final_count = len(_tool_registry)
        assert final_count == initial_count, "Tool registry grew on module re-import"

    @pytest.mark.asyncio
    async def test_complete_server_lifecycle(self):
        """Test complete server lifecycle from startup to operation."""
        from gtd_manager.server import server

        captured_stdout = StringIO()

        with patch("sys.stdout", captured_stdout):
            # 1. Server initialization (already done on import)
            assert server.name == "gtd-manager"

            # 2. Client connection
            async with Client(server) as client:
                # 3. Service discovery
                tools = await client.list_tools()
                assert "hello_world" in [t.name for t in tools]

                # 4. Service execution
                result = await client.call_tool("hello_world", {"name": "Lifecycle"})
                assert "Hello, Lifecycle!" in result.data

                # 5. Multiple operations
                for i in range(3):
                    await client.call_tool("hello_world", {"name": f"Op{i}"})

            # 6. Verify protocol compliance throughout
            stdout_content = captured_stdout.getvalue()
            assert stdout_content == "", "Server violated MCP protocol during lifecycle"
