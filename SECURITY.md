# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of GTD Manager MCP Server seriously. If you discover a
security vulnerability, please report it to us as described below.

### Where to Report

Please report security vulnerabilities by emailing
**<peer.jakobsen@gmail.com>** with:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (if available)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report
  within 48 hours
- **Initial Assessment**: We will provide an initial assessment within
  5 business days
- **Updates**: We will keep you informed of our progress at least every 7 days
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### Responsible Disclosure

We follow responsible disclosure practices:

- We will work with you to understand and resolve the issue
- We ask that you do not publicly disclose the vulnerability until we have
  had a chance to address it
- We will credit you in our security advisory (unless you prefer to remain
  anonymous)

### Security Considerations

This MCP server:

- Operates over stdio using JSON-RPC protocol
- Has minimal external dependencies (FastMCP, structlog)
- Does not handle sensitive user data by default
- Logs to stderr only to maintain MCP protocol compliance

### Scope

This security policy applies to:

- The main GTD Manager MCP Server codebase
- Published releases on PyPI
- Official GitHub Actions workflows

### Out of Scope

- Issues in third-party dependencies (please report to respective maintainers)
- General configuration or deployment issues
- Features working as designed

Thank you for helping keep GTD Manager MCP Server secure!
