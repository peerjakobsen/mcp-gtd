# Task Completion Checklist

When completing development tasks, follow this checklist to ensure code quality and compliance:

## Pre-Commit Checks
- [ ] **Format code**: `uv run ruff format .`
- [ ] **Lint code**: `uv run ruff check . --fix`
- [ ] **Type check**: `uv run mypy src/`
- [ ] **Run tests**: `uv run pytest`
- [ ] **Coverage check**: Ensure test coverage is maintained

## Pre-Commit Hooks
The project uses comprehensive pre-commit hooks that will automatically run:
- Trailing whitespace removal
- End-of-file fixing
- YAML/TOML/JSON validation
- Ruff formatting and linting
- MyPy type checking
- Bandit security linting
- Markdown linting
- Secrets detection

## Testing Requirements
- [ ] All existing tests pass
- [ ] New functionality has appropriate tests
- [ ] Test coverage maintained (pytest-cov configured)
- [ ] Integration tests for MCP tools

## MCP Protocol Compliance
- [ ] **Critical**: No stdout contamination (all output to stderr)
- [ ] Proper structured logging with structlog
- [ ] Tool functions have descriptive docstrings
- [ ] Error handling follows MCP patterns

## Documentation
- [ ] Update docstrings for new/modified functions
- [ ] Add type hints to all new functions
- [ ] Update README.md if adding new features
- [ ] Update CLAUDE.md if changing development practices

## Git Workflow
- [ ] Commit with descriptive message
- [ ] Push to feature branch
- [ ] Create pull request with proper description
- [ ] Ensure CI/CD passes (when configured)

## Manual Testing for MCP
- [ ] Test MCP server startup: `uv run gtd-manager`
- [ ] Verify tools are discoverable in MCP client
- [ ] Test tool functionality through MCP protocol
- [ ] Check logs for proper stderr output only

## Final Verification
- [ ] Run full test suite one more time
- [ ] Verify all pre-commit hooks pass: `uv run pre-commit run --all-files`
- [ ] Check that package can be imported: `python -c "import gtd_manager; print(gtd_manager.__version__)"`