# Suggested Commands

## Environment Setup

```bash
# Install dependencies (development mode)
uv sync

# Install with all optional dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

## Development Commands

```bash
# Run the MCP server locally
uv run gtd-manager

# Alternative: Run via Python module
uv run python -m gtd_manager.server
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage reports
uv run pytest --cov=gtd_manager

# Run specific test file
uv run pytest tests/test_package_structure.py

# Run with coverage output
uv run pytest --cov=gtd_manager --cov-report=term-missing --cov-report=html
```

## Code Quality

```bash
# Format code with ruff
uv run ruff format .

# Lint code with ruff
uv run ruff check .

# Fix linting issues automatically
uv run ruff check . --fix

# Type checking with mypy
uv run mypy src/

# Run all pre-commit hooks manually
uv run pre-commit run --all-files
```

## Database Operations (Planned)

```bash
# Set up database (when implemented)
docker compose up -d postgres

# Run migrations (when implemented)
uv run alembic upgrade head

# Generate new migration (when implemented)
uv run alembic revision --autogenerate -m "Description"
```

## System Utilities (Darwin/macOS)

```bash
# List files
ls -la

# Find files by name
find . -name "*.py" -type f

# Search content in files
grep -r "pattern" src/

# Change directory
cd path/to/directory

# Git operations
git status
git add .
git commit -m "message"
git push origin main
```

## Package Management

```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --group dev package-name

# Update dependencies
uv sync --upgrade

# Show dependency tree
uv tree
```
