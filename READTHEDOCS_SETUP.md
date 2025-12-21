# ReadTheDocs Setup Guide for Lynguine

## Current Status

✅ **Local Documentation Build**: Successfully builds with 48 warnings
✅ **Configuration Files**: `.readthedocs.yml` and `docs/conf.py` are ready
✅ **Dependencies**: Poetry with docs group properly configured
✅ **Security Documentation**: Comprehensive security section included (~1MB of HTML)

## ReadTheDocs Registration Steps

These steps require **GitHub repository owner access**.

### Step 1: Create ReadTheDocs Account

1. Go to https://readthedocs.org/
2. Click "Sign Up" and choose "Sign up with GitHub"
3. Authorize ReadTheDocs to access your GitHub account

### Step 2: Import the Project

1. Once logged in, click "Import a Project"
2. Click "Import Manually" or find `lawrennd/lynguine` in your repository list
3. Fill in project details:
   - **Name**: `lynguine`
   - **Repository URL**: `https://github.com/lawrennd/lynguine`
   - **Repository type**: Git
   - **Default branch**: `main`
   - **Default version**: `latest`
   - **Programming language**: Python

### Step 3: Configure Advanced Settings

1. Go to **Admin** → **Advanced Settings**
2. Verify these settings:
   - **Python interpreter**: CPython 3.x
   - **Use system packages**: Unchecked
   - **Install your project**: Checked (via Poetry)
   - **Requirements file**: Leave empty (using Poetry)
   - **Documentation type**: Sphinx HTML
   - **Sphinx configuration file**: `docs/conf.py`

### Step 4: Trigger First Build

1. Go to **Builds** tab
2. Click "Build Version: latest"
3. Monitor the build log for any errors
4. Build should complete successfully (expect ~48 warnings, which is normal)

### Step 5: Verify Documentation

Once the build completes:

1. Visit your documentation at: `https://lynguine.readthedocs.io/`
2. Verify these sections are accessible:
   - Home page
   - API Reference
   - Security section
   - User guides

### Step 6: Enable Version Control

1. Go to **Admin** → **Versions**
2. Activate the versions you want to host (e.g., `latest`, `stable`, version tags)
3. ReadTheDocs will automatically build docs for each activated version

### Step 7: Set Up Webhooks (Automatic)

ReadTheDocs should automatically set up a webhook in your GitHub repository to trigger builds on push. Verify this:

1. Go to GitHub repo → **Settings** → **Webhooks**
2. You should see a webhook for `https://readthedocs.org/api/v2/webhook/...`
3. This enables automatic documentation rebuilds on every commit

## Post-Registration Tasks

After ReadTheDocs is set up and building successfully:

### Update README.md Badge

Add the ReadTheDocs badge to the README.md after line 5:

```markdown
![Tests](https://github.com/lawrennd/lynguine/actions/workflows/python-tests.yml/badge.svg)
[![Documentation](https://github.com/lawrennd/lynguine/actions/workflows/docs.yml/badge.svg)](https://lawrennd.github.io/lynguine/)
[![ReadTheDocs](https://readthedocs.org/projects/lynguine/badge/?version=latest)](https://lynguine.readthedocs.io/en/latest/)
```

### Update Quick Links Section

Update the documentation link in README.md to point to ReadTheDocs:

```markdown
## Quick Links

- [Documentation](https://lynguine.readthedocs.io/)
- [GitHub Pages (Mirror)](https://lawrennd.github.io/lynguine/)
- [Code Improvement Plans](cip/)
- [Project Backlog](backlog/)
- [Security Documentation](https://lynguine.readthedocs.io/en/latest/security/)
```

### Update CIP-0001

Mark ReadTheDocs integration as completed in `cip/cip0001.md`.

### Update Backlog Item

Update `backlog/documentation/2025-05-05_readthedocs-setup.md`:
- Change status to "completed"
- Mark all acceptance criteria as done
- Add completion date and notes

## Troubleshooting

### Build Failures

**Issue**: Poetry installation fails
**Solution**: Verify Poetry version in `.readthedocs.yml` is compatible (currently 1.5.1)

**Issue**: Missing dependencies
**Solution**: Ensure `pyproject.toml` includes all required packages in `[tool.poetry.group.docs.dependencies]`

**Issue**: Sphinx warnings causing failure
**Solution**: Check build logs. Warnings are normal, but errors will fail the build. Our current 48 warnings are acceptable.

### Configuration Issues

**Issue**: Can't find `conf.py`
**Solution**: Verify `sphinx.configuration` in `.readthedocs.yml` points to `docs/conf.py`

**Issue**: Theme not rendering correctly
**Solution**: Ensure `sphinx-rtd-theme` is in docs dependencies (it is)

## Expected Build Time

- First build: ~5-10 minutes (installs all dependencies)
- Subsequent builds: ~2-3 minutes (uses cached dependencies)

## Documentation URL

Once set up, documentation will be available at:
- **Latest**: https://lynguine.readthedocs.io/en/latest/
- **Stable**: https://lynguine.readthedocs.io/en/stable/

## Support

If issues arise during registration:
- ReadTheDocs support: https://docs.readthedocs.io/
- Community forum: https://github.com/readthedocs/readthedocs.org/issues

