# GitHub Environment Setup

This document outlines the GitHub environment configuration for secure PyPI publishing.

## PyPI Environment

### Required Secrets
- `PYPI_API_TOKEN` - Your PyPI API token for publishing packages

### Environment Protection Rules (Recommended)

To set up the `pypi` environment with protection rules:

1. **Navigate to Environment Settings**
   - Go to your repository → Settings → Environments
   - Click "New environment"
   - Name: `pypi`

2. **Configure Protection Rules**
   - ✅ **Required reviewers**: Add yourself as a reviewer
   - ✅ **Wait timer**: 0 minutes (optional: add 5-10 minutes for safety)
   - ✅ **Deployment branches**: Only allow `main` and tags matching `v*`

3. **Environment Secrets**
   - The `PYPI_API_TOKEN` is available as a repository secret
   - No additional environment-specific secrets needed

### Benefits of Environment Protection

- **Manual Approval**: Requires approval before publishing to PyPI
- **Branch Restrictions**: Only allows publishing from protected branches/tags
- **Audit Trail**: Complete log of who approved each release
- **Rollback Protection**: Prevents accidental overwrites

### Publishing Workflow

1. **Create Release Tag**: `git tag v0.1.0 && git push origin v0.1.0`
2. **Automatic Build**: GitHub Actions builds and tests the package
3. **Review Request**: If environment protection is enabled, approval required
4. **Automatic Publish**: Upon approval, package is published to PyPI
5. **GitHub Release**: Release is created with artifacts and PyPI links

## Current Status

- ✅ Repository secret `PYPI_API_TOKEN` configured
- ✅ Release workflow includes PyPI publishing job
- ✅ Environment `pypi` configured in workflow
- ⏳ Environment protection rules (optional, set up manually)

## Testing Your Setup

**First Release Test:**
```bash
# Tag your first release
git tag v0.1.0
git push origin v0.1.0

# Monitor the workflow at:
# https://github.com/[username]/mcp-gtd/actions
```

**Verify Publication:**
- Check PyPI: https://pypi.org/project/gtd-manager/
- Install test: `pip install gtd-manager`
- GitHub release: Check your repository's releases page

## Troubleshooting

**Common Issues:**
- **Missing Token**: Ensure `PYPI_API_TOKEN` is set in repository secrets
- **Invalid Token**: Regenerate token on PyPI if expired
- **Package Name Conflict**: Choose a different name if `gtd-manager` becomes taken
- **Build Failures**: Check CI workflow logs before PyPI publishing

**Security Notes:**
- Never commit tokens to your repository
- Rotate tokens periodically (every 6-12 months)
- Use project-scoped tokens when possible after first release
- Monitor PyPI for unauthorized releases
