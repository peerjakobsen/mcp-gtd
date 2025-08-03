# Code Style and Conventions

## Formatting and Linting
- **Tool**: Ruff (replaces Black, flake8, isort, etc.)
- **Line Length**: 88 characters (Black default)
- **Target Python**: 3.13
- **Import Style**: `gtd_manager` as known first-party package

## Ruff Configuration
```toml
[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings  
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
    "TCH", # flake8-type-checking
]
```

## Type Checking
- **Tool**: MyPy with strict configuration
- **Requirements**: Type hints required for all functions
- **Configuration**: Strict mode enabled with comprehensive warnings

## MyPy Settings
```toml
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_return_any = true
```

## Docstring Style
- **Format**: Google-style docstrings
- **Requirements**: All public functions must have docstrings
- **Tool descriptions**: Docstrings become MCP tool descriptions

## Naming Conventions
- **Functions/Variables**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **MCP Tools**: descriptive names with underscores (e.g., `capture_item`)

## Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- `gtd_manager` recognized as first-party package