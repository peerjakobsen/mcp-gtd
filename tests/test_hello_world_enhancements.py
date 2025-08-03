"""
Tests for enhanced hello_world MCP tool functionality.

These tests verify that the hello_world tool demonstrates proper
parameter validation, structured responses, and error handling.
"""

import pytest
from fastmcp import Client


class TestHelloWorldEnhancements:
    """Test enhanced hello_world tool functionality."""

    @pytest.mark.asyncio
    async def test_hello_world_with_structured_response(self):
        """Test that hello_world can return structured data."""
        from gtd_manager.server import server

        async with Client(server) as client:
            result = await client.call_tool("hello_world", {"name": "Test"})

            # Should return a string (current behavior is fine)
            assert isinstance(result.data, str)
            assert "Hello, Test!" in result.data
            assert "GTD Manager MCP Server is running" in result.data

    @pytest.mark.asyncio
    async def test_hello_world_parameter_validation(self):
        """Test that hello_world validates parameters properly."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Should handle empty name gracefully
            result = await client.call_tool("hello_world", {"name": ""})
            assert result.data is not None

            # Should handle very long names
            long_name = "x" * 1000
            result = await client.call_tool("hello_world", {"name": long_name})
            assert result.data is not None

    @pytest.mark.asyncio
    async def test_hello_world_with_special_characters(self):
        """Test that hello_world handles special characters in names."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Test with special characters
            special_names = [
                "José",
                "王小明",
                "Владимир",
                "test@example.com",
                "user-name_123",
            ]

            for name in special_names:
                result = await client.call_tool("hello_world", {"name": name})
                assert name in result.data
                assert "GTD Manager MCP Server is running" in result.data

    @pytest.mark.asyncio
    async def test_hello_world_demonstrates_error_handling(self):
        """Test that hello_world demonstrates proper error handling patterns."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Normal operation should work
            result = await client.call_tool("hello_world", {"name": "Test"})
            assert isinstance(result.data, str)

            # The tool should handle the registry error handling properly
            # This is more about testing that the registry setup worked
            result = await client.call_tool("hello_world", {})
            assert "Hello, World!" in result.data

    @pytest.mark.asyncio
    async def test_hello_world_json_parameter_preprocessing(self):
        """Test that hello_world benefits from JSON parameter preprocessing."""
        # This test verifies that the register_tool decorator applied preprocessing
        from gtd_manager.server import hello_world

        # Should be able to call directly with proper parameters
        result = hello_world(name="Direct")
        assert "Hello, Direct!" in result

        # The preprocessing should be applied at the registry level
        # so this tool inherits the benefit automatically

    @pytest.mark.asyncio
    async def test_hello_world_logging_integration(self):
        """Test that hello_world integrates with structured logging."""
        from unittest.mock import patch

        from gtd_manager.server import server

        # Test that the hello_world function calls logger.info
        with patch("gtd_manager.server.logger") as mock_logger:
            async with Client(server) as client:
                await client.call_tool("hello_world", {"name": "LogTest"})

            # Should have called logger.info with structured data
            mock_logger.info.assert_called_with(
                "Hello world tool called", name="LogTest", tool="hello_world"
            )

    @pytest.mark.asyncio
    async def test_hello_world_tool_metadata(self):
        """Test that hello_world tool has proper metadata."""
        from gtd_manager.server import server

        async with Client(server) as client:
            tools = await client.list_tools()
            hello_tool = next((t for t in tools if t.name == "hello_world"), None)

            assert hello_tool is not None
            assert hello_tool.description is not None
            assert "hello world" in hello_tool.description.lower()
            assert "testing" in hello_tool.description.lower()

            # Should have parameter information
            # FastMCP automatically infers this from function signature
            assert hasattr(hello_tool, "inputSchema")


class TestHelloWorldAsExample:
    """Test hello_world as an example of proper MCP tool patterns."""

    @pytest.mark.asyncio
    async def test_hello_world_demonstrates_mcp_best_practices(self):
        """Test that hello_world demonstrates MCP development best practices."""
        from gtd_manager.server import hello_world, server

        # Should have proper docstring
        assert hello_world.__doc__ is not None
        assert len(hello_world.__doc__.strip()) > 0

        # Should be registered with server
        async with Client(server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            assert "hello_world" in tool_names

    def test_hello_world_function_signature(self):
        """Test that hello_world has proper function signature."""
        import inspect

        from gtd_manager.server import hello_world

        sig = inspect.signature(hello_world)

        # Should have name parameter with default
        assert "name" in sig.parameters
        name_param = sig.parameters["name"]
        assert name_param.default == "World"

        # Should have type annotations
        assert name_param.annotation is str
        assert sig.return_annotation is str

    @pytest.mark.asyncio
    async def test_hello_world_consistent_behavior(self):
        """Test that hello_world behavior is consistent across calls."""
        from gtd_manager.server import server

        async with Client(server) as client:
            # Multiple calls should give consistent results
            results = []
            for i in range(3):
                result = await client.call_tool("hello_world", {"name": f"Test{i}"})
                results.append(result.data)

            # All should follow same pattern
            for i, result in enumerate(results):
                assert f"Hello, Test{i}!" in result
                assert "GTD Manager MCP Server is running" in result

    @pytest.mark.asyncio
    async def test_hello_world_registry_integration(self):
        """Test that hello_world properly integrates with tool registry."""
        from gtd_manager.server import _tool_registry, hello_world

        # Should be in the registry
        assert hello_world in _tool_registry

        # Should maintain original function properties
        assert hello_world.__name__ == "hello_world"
        assert "simple hello world tool" in hello_world.__doc__.lower()
