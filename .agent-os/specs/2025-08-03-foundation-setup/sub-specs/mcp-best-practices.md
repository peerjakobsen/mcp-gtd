# MCP Best Practices Specification

This document outlines the specific MCP server best practices that must be implemented in the foundation setup, derived from @/Users/peerjakobsen/projects/mcp_cdh/MCP_SERVER_BEST_PRACTICES.md

## Critical Protocol Requirements

### Stdout Cleanliness (CRITICAL)
**This is the #1 cause of MCP server failures and must be implemented correctly**

- Configure all logging to stderr using structlog with JSON output
- Never use print() statements or any stdout output in the server code
- Create comprehensive test to verify stdout remains clean during server initialization
- Use `logging.basicConfig(stream=sys.stderr, force=True)` pattern

### Structured Logging Implementation
- Implement structlog with stderr output and JSON formatting
- Include contextual information in all log messages (tool names, parameters, operation context)
- Use appropriate log levels: info for operations, warning for user errors, error for system errors
- Configure logging during server initialization before any other operations

## Parameter Handling and Serialization

### JSON String Preprocessing
**MCP clients sometimes send parameters as JSON strings instead of Python objects**

- Implement parameter preprocessing decorator to handle JSON string deserialization
- Detect when string parameters start with '[' or '{' and attempt JSON parsing
- Use function signature inspection to determine expected parameter types
- Gracefully fallback to original value if JSON parsing fails

### Business Domain Enums
- Replace free-text parameters with validated enums where appropriate
- Create enums that inherit from appropriate base types (str, int)
- Implement conversion methods for handling various input formats
- Use enums to prevent serialization issues and improve validation

## Error Handling Strategy

### Comprehensive Error Handling
- Implement safe tool execution decorator for consistent error handling across all tools
- Handle specific error types: database errors, parameter validation, resource exhaustion
- Create user-friendly error messages by sanitizing technical stack traces
- Return standardized error response format with success flags and error codes

### Input Validation and Security
- Implement input size limits to prevent resource exhaustion (1MB strings, 10k item collections)
- Sanitize user input by removing null bytes and limiting length
- Use parameterized database queries exclusively (never string formatting)
- Validate all user inputs before processing

## Tool Registration and Management

### Centralized Tool Registry
- Create global tool registry that accumulates tools before server initialization
- Implement registration decorator that applies preprocessing and error handling automatically
- Validate tool functions during registration (check for docstrings, type annotations)
- Set up automated tool registration with the FastMCP server instance

### Tool Function Standards
- Require comprehensive docstrings for all tools (they become MCP tool descriptions)
- Use type hints for all parameters and return values
- Follow consistent naming conventions (action_noun pattern)
- Include parameter validation and business logic separation

## Database Management

### Smart Path Detection
- Implement multi-environment database path detection (uvx, local development, system install)
- Use environment variable override as highest priority: `MCP_GTD_DB_PATH`
- Detect uvx execution by checking for .cache or site-packages in file paths
- Default to user data directory for uvx/system installs: `~/.local/share/gtd-manager/`
- Use project directory for local development environments

### Robust Connection Management
- Implement context manager for database connections with proper cleanup
- Enable foreign key constraints and configure row factory for easier access
- Handle database initialization automatically when database doesn't exist
- Implement proper transaction handling with rollback on exceptions

## Testing and Quality Assurance

### Critical Test Categories
- **Stdout cleanliness test**: Verify server creation produces no stdout output
- **Parameter serialization tests**: Test JSON string preprocessing works correctly
- **Error handling tests**: Verify user-friendly error messages for all error types
- **Database tests**: Test connection management and path detection logic

### Test Implementation Requirements
- Use pytest framework with comprehensive test coverage
- Capture stdout/stderr during tests to verify protocol compliance
- Test all error scenarios with mock failures
- Include integration tests for full MCP protocol communication

## Deployment and Distribution Support

### uvx Distribution Model
- Design database path detection to support uvx execution from any location
- Support environment variable configuration for deployment flexibility
- Ensure server works without local installation or setup
- Design for Claude Desktop configuration with uvx command

### Configuration Management
- Support multiple configuration sources: environment variables, config files
- Provide reasonable defaults for all configuration values
- Document all configuration options in README
- Support development, staging, and production environment configurations

## Implementation Priority

**Phase 1 (Foundation Setup - This Spec):**
1. Stdout cleanliness and structured logging
2. Basic parameter preprocessing
3. Centralized tool registry
4. Database path detection and connection management
5. Basic error handling framework

**Phase 2 (Future Specs):**
1. Advanced parameter validation with business enums
2. Comprehensive error handling for all scenarios
3. Full test suite with all MCP best practices covered
4. Performance optimizations and resource management

This foundation ensures we start with the most critical MCP best practices that prevent common failures and establish proper patterns for future development.