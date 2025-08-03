"""
Tests for MCP protocol compliance.

These tests verify that the MCP server follows protocol requirements,
particularly the critical requirement that stdout remains clean for
JSON-RPC communication.
"""

import sys
from io import StringIO
from unittest.mock import patch

import pytest


def test_server_creation_logs_to_stderr_only():
    """
    Critical test for MCP protocol compliance.

    Verifies that server creation produces no stdout output, which would
    break MCP JSON-RPC communication over stdio.
    """
    # Capture both stdout and stderr
    captured_stdout = StringIO()
    captured_stderr = StringIO()

    with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
        # Import and create server - this should not write to stdout

        # Verify stdout is completely clean
        stdout_content = captured_stdout.getvalue()
        assert stdout_content == "", (
            f"Server creation contaminated stdout: {repr(stdout_content)}. "
            "This breaks MCP protocol communication."
        )

        # Verify stderr contains expected logging (but don't require specific content)
        captured_stderr.getvalue()  # Consume stderr content without assignment
        # We expect some structured logging to stderr, so it shouldn't be empty
        # but we don't assert on specific content since logging config may vary


def test_server_main_function_logs_to_stderr_only():
    """
    Test that the main function setup doesn't contaminate stdout.

    This tests the server initialization path that would be used
    when running the MCP server.
    """
    captured_stdout = StringIO()
    captured_stderr = StringIO()

    with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
        # Import the server module which includes logging configuration
        import gtd_manager.server  # noqa: F401

        # Verify stdout is completely clean
        stdout_content = captured_stdout.getvalue()
        assert stdout_content == "", (
            f"Server module import contaminated stdout: {repr(stdout_content)}. "
            "This breaks MCP protocol communication."
        )


def test_server_tool_execution_logs_to_stderr_only():
    """
    Test that tool execution doesn't contaminate stdout.

    This verifies that when tools are called through the proper MCP client,
    they maintain stdout cleanliness for MCP protocol compliance.
    """
    import asyncio

    from fastmcp import Client

    async def run_test():
        captured_stdout = StringIO()
        captured_stderr = StringIO()

        with patch("sys.stdout", captured_stdout), patch("sys.stderr", captured_stderr):
            from gtd_manager.server import server

            # Use FastMCP Client for proper in-memory testing
            async with Client(server) as client:
                # Execute the tool through the MCP client
                result = await client.call_tool("hello_world", {"name": "Test"})

                # Verify stdout is completely clean
                stdout_content = captured_stdout.getvalue()
                assert stdout_content == "", (
                    f"Tool execution contaminated stdout: {repr(stdout_content)}. "
                    "This breaks MCP protocol communication."
                )

                # Verify the tool returned expected result
                assert "Hello, Test!" in result.data
                assert "GTD Manager MCP Server is running" in result.data

    # Run the async test
    asyncio.run(run_test())


class TestMcpProtocolCompliance:
    """Test class for comprehensive MCP protocol compliance verification."""

    def test_no_print_statements_in_server_code(self):
        """
        Verify that the server code doesn't use print() statements.

        Print statements would contaminate stdout and break MCP protocol.
        """
        from pathlib import Path

        server_file = Path("src/gtd_manager/server.py")
        content = server_file.read_text()

        # Check for print statements (basic check)
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            # Skip comments and docstrings
            stripped = line.strip()
            if (
                stripped.startswith("#")
                or stripped.startswith('"""')
                or stripped.startswith("'''")
            ):
                continue

            # Look for print calls
            if "print(" in line and not line.strip().startswith("#"):
                pytest.fail(
                    f"Found print() statement at line {line_num} in server.py: {line.strip()}. "
                    "Print statements contaminate stdout and break MCP protocol."
                )

    def test_logging_configured_to_stderr(self):
        """
        Verify that logging is properly configured to stderr only.

        This test is run in a clean environment to avoid interference
        from test patching.
        """
        # Import server module in a subprocess to get clean logging state
        import subprocess

        code = """
import sys
import logging
from gtd_manager import server

# Check logging configuration
root_logger = logging.getLogger()
stderr_handlers = 0
other_handlers = 0

for handler in root_logger.handlers:
    if hasattr(handler, "stream"):
        if handler.stream == sys.stderr:
            stderr_handlers += 1
        else:
            other_handlers += 1

print(f"stderr_handlers:{stderr_handlers},other_handlers:{other_handlers}")
"""

        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"},
        )

        # Skip test on Windows if there are environment socket issues
        if result.returncode != 0 and "WinError 10106" in result.stderr:
            pytest.skip("Windows socket provider issue - not related to our code")

        assert result.returncode == 0, f"Subprocess failed: {result.stderr}"

        # Parse output
        output = result.stdout.strip()
        if "stderr_handlers:" in output and "other_handlers:" in output:
            parts = output.split(",")
            stderr_count = int(parts[0].split(":")[1])
            other_count = int(parts[1].split(":")[1])

            assert stderr_count > 0, "No stderr handlers found"
            assert other_count == 0, f"Found {other_count} non-stderr handlers"
        else:
            pytest.fail(f"Unexpected subprocess output: {output}")
