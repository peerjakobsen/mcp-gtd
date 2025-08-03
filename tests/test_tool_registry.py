"""
Tests for centralized tool registry with decorator pattern.

These tests verify that tools can be registered centrally and
automatically discovered by the FastMCP server.
"""

from unittest.mock import Mock

import pytest
from fastmcp import Client


class TestToolRegistry:
    """Test centralized tool registry functionality."""

    def test_register_tool_decorator_exists(self):
        """Test that register_tool decorator exists."""
        from gtd_manager.server import register_tool

        assert callable(register_tool)

    def test_register_tool_decorator_registers_function(self):
        """Test that register_tool decorator adds function to registry."""
        # Reset registry state
        from gtd_manager.server import _tool_registry

        initial_count = len(_tool_registry)

        from gtd_manager.server import register_tool

        @register_tool
        def test_tool(message: str = "test") -> str:
            """A test tool for registry testing."""
            return f"Test: {message}"

        # Should have added one tool to registry
        assert len(_tool_registry) == initial_count + 1
        assert test_tool in _tool_registry

    def test_register_tool_preserves_function_metadata(self):
        """Test that register_tool preserves original function metadata."""
        from gtd_manager.server import register_tool

        @register_tool
        def test_tool_with_metadata(param: str) -> str:
            """Test tool with specific metadata."""
            return param

        # Should preserve function name and docstring
        assert test_tool_with_metadata.__name__ == "test_tool_with_metadata"
        assert "Test tool with specific metadata" in test_tool_with_metadata.__doc__

    def test_register_tool_with_preprocessing_enabled(self):
        """Test that register_tool applies preprocessing by default."""
        from gtd_manager.server import register_tool

        @register_tool
        def test_tool_preprocessing(data: list[str]) -> str:
            """Test tool that expects list parameter."""
            return f"Processed: {len(data)} items"

        # Should be able to handle JSON string input (simulating MCP client)
        json_input = '["item1", "item2", "item3"]'
        result = test_tool_preprocessing(data=json_input)
        assert "Processed: 3 items" in result

    def test_register_tool_with_preprocessing_disabled(self):
        """Test that register_tool can disable preprocessing."""
        from gtd_manager.server import register_tool

        @register_tool(enable_preprocessing=False)
        def test_tool_no_preprocessing(data: str) -> str:
            """Test tool without preprocessing."""
            return f"Raw: {data}"

        # Should receive raw string without JSON deserialization
        json_input = '["item1", "item2"]'
        result = test_tool_no_preprocessing(data=json_input)
        assert 'Raw: ["item1", "item2"]' in result

    def test_register_tool_applies_error_handling(self):
        """Test that register_tool applies error handling."""
        from gtd_manager.server import register_tool

        @register_tool
        def test_tool_with_error() -> str:
            """Test tool that raises an error."""
            raise ValueError("Test error")

        # Should handle error gracefully and return error response
        result = test_tool_with_error()

        # Should be a standardized error response
        assert isinstance(result, dict)
        assert result.get("success") is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_setup_tool_registration_function_exists(self):
        """Test that setup_tool_registration function exists."""
        from gtd_manager.server import setup_tool_registration

        assert callable(setup_tool_registration)

    def test_setup_tool_registration_registers_with_server(self):
        """Test that setup_tool_registration registers tools with FastMCP server."""
        from gtd_manager.server import register_tool, setup_tool_registration

        # Create a mock FastMCP server
        mock_server = Mock()

        # Register a test tool
        @register_tool
        def registry_test_tool(value: str = "default") -> str:
            """Test tool for registry setup."""
            return f"Registry: {value}"

        # Setup tool registration
        setup_tool_registration(mock_server)

        # Should have called server.tool() with our function
        mock_server.tool.assert_called()

        # Should have called server.tool() at least once (for our test tool + existing tools)
        assert mock_server.tool.call_count >= 1

    @pytest.mark.asyncio
    async def test_registered_tools_available_via_client(self):
        """Test that registered tools are available through FastMCP client."""
        from gtd_manager.server import register_tool, server

        # Register a new test tool
        @register_tool
        def client_test_tool(greeting: str = "Hello") -> str:
            """Test tool for client access."""
            return f"{greeting} from registry!"

        # Re-setup tool registration to include our new tool
        from gtd_manager.server import setup_tool_registration

        setup_tool_registration(server)

        async with Client(server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]

            # Should include our newly registered tool
            assert "client_test_tool" in tool_names

            # Should be able to call the tool
            result = await client.call_tool("client_test_tool", {"greeting": "Hi"})
            assert "Hi from registry!" in result.data


class TestToolRegistryIntegration:
    """Test integration between tool registry and existing server functionality."""

    def test_hello_world_tool_uses_registry(self):
        """Test that hello_world tool is registered through the registry."""
        from gtd_manager.server import _tool_registry, hello_world

        # hello_world should be in the registry
        assert hello_world in _tool_registry

    @pytest.mark.asyncio
    async def test_all_registered_tools_discoverable(self):
        """Test that all tools in registry are discoverable via client."""
        from gtd_manager.server import _tool_registry, server

        async with Client(server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]

            # Should have at least as many tools as in registry
            # (There might be additional tools registered directly with FastMCP)
            assert len(tool_names) >= len(_tool_registry)

            # Should include hello_world which we know is registered
            assert "hello_world" in tool_names

    def test_registry_state_management(self):
        """Test that registry state is properly managed."""
        from gtd_manager.server import _tool_registry, register_tool

        initial_count = len(_tool_registry)

        # Register multiple tools
        @register_tool
        def registry_tool_1() -> str:
            return "tool1"

        @register_tool
        def registry_tool_2() -> str:
            return "tool2"

        # Should have added exactly 2 tools
        assert len(_tool_registry) == initial_count + 2

        # Should contain both tools
        tool_names = [tool.__name__ for tool in _tool_registry]
        assert "registry_tool_1" in tool_names
        assert "registry_tool_2" in tool_names
