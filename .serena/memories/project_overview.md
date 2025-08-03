# GTD Manager MCP Server - Project Overview

## Purpose

GTD Manager is a Model Context Protocol (MCP) server that implements Getting Things Done methodology specifically designed for team leads and engineering managers dealing with extreme context switching. It provides AI assistant integration for GTD workflows through MCP-compatible clients like Claude Desktop and Cursor.

## Key Features (Planned)

- **Universal Capture**: Add items from any MCP-enabled AI assistant
- **Smart Clarification**: Process inbox items into actionable projects and tasks
- **Context Organization**: GTD contexts optimized for knowledge work
- **Meeting Management**: Custom SOPs with markdown templates
- **Action Extraction**: Automatically identify and track action items from notes
- **Flexible Storage**: Quip integration and local markdown support

## Current Implementation Status

- ✅ Basic FastMCP server setup with MCP protocol compliance
- ✅ Package structure and build configuration
- ✅ Hello world tool for connectivity testing
- ✅ Structured logging to stderr (critical for MCP protocol)
- ⚠️ GTD business logic not yet implemented

## Target Users

Team leads managing 15-20 meetings per week who need a trusted system that adapts to their unique organizational processes.

## License

Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)

- Personal, educational, and non-commercial use allowed
- Commercial use requires explicit permission

## Distribution

- Primary: uvx installation from git repository (no local setup required)
- Development: uv sync for local development
- Entry point: `gtd-manager` console script
