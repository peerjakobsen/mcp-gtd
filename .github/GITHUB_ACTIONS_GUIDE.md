# GitHub Actions Guide

This document explains the CI/CD setup for the GTD Manager MCP Server project.

## Workflows Overview

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push to `main`/`develop`, Pull Requests

**Jobs**:
- **Quality**: Runs Ruff linting/formatting, mypy type checking, bandit security analysis
- **Test**: Cross-platform testing (Ubuntu, macOS, Windows) with coverage reporting
- **Build**: Package building and installation testing
- **Integration**: MCP protocol compliance and FastMCP server startup tests

**Key Features**:
- ✅ Matrix builds across operating systems
- ✅ MCP protocol compliance verification (stdout cleanliness)
- ✅ Coverage reporting to Codecov
- ✅ Artifact uploads for security reports
- ✅ uv package manager for fast dependency installation

### 2. Release Workflow (`.github/workflows/release.yml`)

**Triggers**: Version tags (`v*`)

**Jobs**:
- **Build**: Test and build release packages
- **GitHub Release**: Create GitHub release with built artifacts
- **Documentation Update**: Auto-update installation instructions

**Key Features**:
- ✅ Automatic changelog generation
- ✅ Wheel and source distribution artifacts
- ✅ uvx installation instructions
- ✅ Optional PyPI publishing (commented out)
- ✅ Pre-release detection (alpha, beta, rc)

### 3. PR Workflow (`.github/workflows/pr.yml`)

**Triggers**: Pull request events

**Jobs**:
- **Quick Check**: Fast linting with auto-fixes
- **Fast Test**: Unit tests only (excludes slow/integration tests)
- **Build Test**: Package building verification
- **Security**: Bandit security analysis
- **PR Comment**: Automated status updates on PRs

**Key Features**:
- ⚡ Fast feedback (skips slow tests)
- 🔧 Auto-fixes formatting issues
- 💬 PR status comments with results summary
- 🚫 Concurrency control (cancels outdated runs)

### 4. CodeQL Security Analysis (`.github/workflows/codeql.yml`)

**Triggers**: Push to main branches, scheduled weekly

**Features**:
- 🔒 Advanced security query suite
- 📊 Security vulnerability detection
- 📅 Weekly scheduled scans
- 📁 Result artifacts for review

## Dependabot Configuration

**File**: `.github/dependabot.yml`

**Features**:
- 📦 Python dependency updates (weekly)
- 🔄 GitHub Actions updates (monthly)
- 👥 Automatic assignment and review requests
- 🏷️ Organized dependency groups
- 🚨 Priority security updates

## Issue Templates

**Bug Reports**: `.github/ISSUE_TEMPLATE/bug_report.yml`
- MCP client information collection
- Version tracking
- Structured reproduction steps

**Feature Requests**: `.github/ISSUE_TEMPLATE/feature_request.yml`
- GTD methodology alignment
- Feature type categorization
- Problem/solution framework

## Development Workflow

### For Contributors

1. **Fork and Clone**: Standard GitHub workflow
2. **Create Feature Branch**: `git checkout -b feature/your-feature`
3. **Make Changes**: Follow code quality standards
4. **Push Changes**: PR workflow runs automatically
5. **Review Feedback**: Auto-fixes applied, manual fixes if needed
6. **Merge**: Full CI runs on merge to main

### For Maintainers

1. **Review PRs**: PR workflow provides automated feedback
2. **Merge to Main**: Full CI validation
3. **Create Release**: Tag with `v*` format triggers release workflow
4. **Monitor**: Dependabot PRs, security alerts, weekly CodeQL scans

## Quality Gates

### Required Checks
- ✅ Ruff linting passes
- ✅ mypy type checking passes
- ✅ All tests pass
- ✅ Package builds successfully
- ✅ MCP protocol compliance verified

### Optional Checks
- 📊 Coverage reporting (informational)
- 🔒 Security analysis (warnings only)
- 🏗️ Integration tests (full CI only)

## MCP-Specific Testing

### Protocol Compliance
The workflows include specific tests for MCP protocol compliance:

```python
# Verifies stdout cleanliness (critical for MCP)
from gtd_manager.server import create_server
server = create_server()  # Must not write to stdout
```

### FastMCP Integration
- Server startup verification
- Tool registration testing
- uvx installation simulation

## Performance Optimizations

- **uv Package Manager**: 10x faster than pip for dependency installation
- **Dependency Caching**: Automatic caching between workflow runs
- **Concurrency Control**: Cancels outdated PR runs
- **Matrix Optimization**: Selective cross-platform testing

## Security Features

- **Bandit Analysis**: Python security linting
- **CodeQL Scanning**: Advanced vulnerability detection
- **Dependabot**: Automated security updates
- **Secrets Detection**: Pre-commit hook integration
- **Least Privilege**: Minimal permissions for workflows

## Monitoring and Alerts

- **Coverage Reports**: Codecov integration
- **Security Alerts**: GitHub Security Advisories
- **Dependency Updates**: Weekly Dependabot PRs
- **Workflow Failures**: GitHub notifications

## Getting Started

1. **Enable Workflows**: Workflows are enabled by default in forks
2. **Configure Secrets**: Optional PyPI token for publishing
3. **Set Up Codecov**: Add repository to Codecov for coverage reports
4. **Review Settings**: Branch protection rules recommended for main branch

## Troubleshooting

### Common Issues

**MCP Protocol Violations**: Check stdout contamination in logs
```bash
# Local testing
PYTHONPATH=src python -c "from gtd_manager.server import create_server; create_server()"
```

**Type Checking Failures**: Ensure all functions have type annotations
```bash
# Local mypy run
uv run mypy src/
```

**Test Failures**: Run tests locally with same environment
```bash
# Match CI environment
PYTHONPATH=src uv run pytest
```

### Workflow Debugging

- Check workflow logs in GitHub Actions tab
- Review artifact uploads for detailed reports
- Use local pre-commit hooks to catch issues early

## Next Steps

Consider additional enhancements:
- 📚 Documentation generation (MkDocs)
- 🐳 Docker image publishing
- 🌍 Multi-language support testing
- 📈 Performance benchmarking
- 🔄 Automated dependency security scanning
