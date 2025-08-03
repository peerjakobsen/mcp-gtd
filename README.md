# GTD Manager MCP Server

> AI-native Getting Things Done system with SOP-driven meeting management

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-latest-orange.svg)](https://github.com/jlowin/fastmcp)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

## Overview

GTD Manager is a Model Context Protocol (MCP) server that implements Getting Things Done methodology specifically designed for team leads and engineering managers dealing with extreme context switching. Unlike traditional GTD applications, it integrates seamlessly with AI assistants and allows complete workflow customization through markdown-based Standard Operating Procedures (SOPs).

**Perfect for:** Team leads managing 15-20 meetings per week who need a trusted system that adapts to their unique organizational processes.

## Key Features

### Core GTD Workflow

- **Universal Capture**: Add items from any MCP-enabled AI assistant
- **Smart Clarification**: Process inbox items into actionable projects and tasks
- **Context Organization**: GTD contexts optimized for knowledge work
- **Comprehensive Reviews**: Daily and weekly review workflows

### Meeting Management

- **Custom SOPs**: Create markdown templates for different meeting types
- **Action Extraction**: Automatically identify and track action items from notes
- **Stakeholder Tracking**: Maintain relationships and context over time
- **Pre-meeting Preparation**: Automated checklists based on meeting type

### Flexible Storage

- **Quip Integration**: Full CRUD operations via Quip API
- **Local Markdown**: File-based storage with frontmatter metadata
- **Hybrid Approach**: Mix and match storage backends per workflow

### AI Assistant Integration

- **MCP Protocol**: Native integration with Claude Desktop, Cursor, and other MCP clients
- **Natural Language**: Capture and process items using conversational commands
- **Zero Context Switching**: Manage tasks without leaving your development environment

## Installation

### Prerequisites

- Python 3.13+
- PostgreSQL 17+ (with JSONB support)
- MCP-compatible client (Claude Desktop, Cursor, etc.)

### Quick Install (Recommended)

```bash
# Install via uvx (no local setup required)
uvx --from git+https://github.com/peerjakobsen/gtd-manager-mcp gtd-manager
```

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/peerjakobsen/gtd-manager-mcp.git
cd gtd-manager-mcp

# Install with uv
uv sync

# Set up database
docker compose up -d postgres

# Initialize database
uv run alembic upgrade head

# Start the MCP server
uv run gtd-manager
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/gtd_manager

# Storage Backend (choose one or both)
QUIP_API_TOKEN=your_quip_api_token_here
LOCAL_STORAGE_PATH=~/.gtd-manager/data

# MCP Settings
MCP_TRANSPORT=stdio
LOG_LEVEL=INFO
```

### MCP Client Configuration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "gtd-manager": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/peerjakobsen/gtd-manager-mcp", "gtd-manager"],
      "env": {
        "DATABASE_URL": "postgresql://localhost/gtd_manager",
        "QUIP_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Usage

### Basic Workflow

1. **Capture Everything**

   ```
   @gtd capture "Follow up with Sarah about project timeline"
   @gtd quick-capture "Buy birthday gift for Mom"
   ```

2. **Process Your Inbox**

   ```
   @gtd inbox-review
   @gtd clarify-item "Follow up with Sarah about project timeline"
   ```

3. **Organize by Context**

   ```
   @gtd next-actions @computer
   @gtd next-actions @meeting
   ```

4. **Review and Plan**

   ```
   @gtd daily-review
   @gtd weekly-review
   ```

### Custom Meeting SOPs

Create a markdown file in your SOPs directory:

```markdown
---
type: meeting
name: "Team Standup"
duration: 15
contexts: ["@team_meeting"]
stakeholders:
  required: ["team_lead", "developers"]
  optional: ["product_manager"]
---

# Daily Team Standup SOP

## Pre-Meeting Checklist
- [ ] Review yesterday's commitments
- [ ] Check for blockers in task board
- [ ] Prepare status updates

## Meeting Agenda
### 1. What did you accomplish yesterday? (5 min)
### 2. What will you work on today? (5 min)
### 3. Any blockers or help needed? (5 min)

## Post-Meeting Actions
- [ ] Update task board with new commitments
- [ ] Schedule follow-up sessions for blockers
- [ ] Send summary to absent team members
```

### Available MCP Tools

- `capture_item` - Add item to GTD inbox
- `clarify_item` - Process inbox item into action/project
- `create_meeting` - Schedule meeting with SOP
- `inbox_review` - View and process inbox items
- `next_actions` - List actions by context
- `weekly_review` - Comprehensive GTD review
- `daily_review` - Quick morning planning
- `create_project` - Multi-step outcome planning

## Development

### Project Structure

```
gtd-manager-mcp/
├── src/gtd_manager/
│   ├── server.py          # FastMCP server setup
│   ├── domain/            # GTD domain models
│   ├── services/          # Business logic
│   ├── repositories/      # Data access
│   └── sops/             # SOP processing
├── tests/                # Test suite
├── migrations/           # Database migrations
├── examples/            # Example SOPs
└── docs/               # Documentation
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/gtd_manager

# Run specific test
uv run pytest tests/test_capture.py
```

### Database Migrations

```bash
# Generate migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Storage Backends

### Quip Integration

When configured with a Quip API token, the system can:

- Create and update documents for projects and meeting notes
- Sync action items between GTD system and Quip documents
- Maintain folder structure aligned with GTD contexts

### Local Markdown

Files are stored in a structured directory:

```
~/.gtd-manager/
├── inbox/
├── projects/
├── contexts/
│   ├── computer/
│   ├── meeting/
│   └── phone/
├── meetings/
└── sops/
```

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

**You are free to:**

- Use this software for personal, educational, and non-commercial purposes
- Study and learn from the source code
- Modify and create derivative works for non-commercial use

**You may not:**

- Use this software for commercial purposes without explicit permission
- Sell or monetize this software or derivative works

For commercial licensing inquiries, please contact: <support@gtdmanager.dev>

See the [LICENSE](LICENSE) file for full details or visit: <https://creativecommons.org/licenses/by-nc/4.0/>

## Support

For questions or issues, contact: <peer.jakobsen@gmail.com>

---

*Built with [FastMCP](https://github.com/jlowin/fastmcp) and the [Model Context Protocol](https://modelcontextprotocol.io/)*
