# Publishing Guide for TechCompressor

This document describes the process for building, signing, and publishing TechCompressor releases to PyPI and GitHub Releases.

## Prerequisites

### Required Tools

```bash
# Install build tools
pip install --upgrade pip
pip install build twine

# Optional: Install signing tools
# gpg --version  # Verify GPG installed
```

### Required Credentials

1. **PyPI Account**: https://pypi.org/account/register/
2. **PyPI API Token**: https://pypi.org/manage/account/token/
   - Scope: Entire account or specific to techcompressor project
   - Store in `~/.pypirc` (see below)

3. **GitHub Personal Access Token**: https://github.com/settings/tokens
   - Scope: `repo` (full repository access)
   - For creating releases via API

### Configure PyPI Credentials

Create or edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgE...  # Your PyPI API token

[testpypi]
username = __token__
password = pypi-AgE...  # Your TestPyPI API token (for testing)
```

**Security**: Set appropriate permissions:
```bash
chmod 600 ~/.pypirc
```

## Pre-Release Checklist

Before building release artifacts:

### 1. Version Update

- [ ] Update version in `techcompressor/__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Verify both match: `grep -r "1.0.0" techcompressor/__init__.py pyproject.toml`

### 2. Documentation

- [ ] Update `CHANGELOG.md` with release notes
- [ ] Update `RELEASE_NOTES.md` with highlights
- [ ] Verify `README.md` is current
- [ ] Check all docs in `docs/` are up-to-date

### 3. Code Quality

- [ ] Run full test suite: `pytest`
- [ ] Run smoke tests: `pytest tests/test_release_smoke.py`
- [ ] Check test coverage: `pytest --cov=techcompressor --cov-report=term-missing`
- [ ] Run benchmark: `python bench.py --quick`
- [ ] Verify no TODOs or FIXME comments: `grep -r "TODO\|FIXME" techcompressor/`

### 4. Dependencies

- [ ] Verify `requirements.txt` is current
- [ ] Check for security vulnerabilities: `pip-audit` (optional)
- [ ] Test with minimum dependency versions
- [ ] Test with latest dependency versions

### 5. Clean Repository

```bash
# Remove build artifacts
rm -rf dist/ build/ *.egg-info

# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Check git status
git status  # Should be clean (no uncommitted changes)
```

## Building Release Artifacts

### Step 1: Build Distribution Packages

```bash
# Build wheel and source distribution
python -m build

# Output will be in dist/:
# - techcompressor-1.0.0-py3-none-any.whl (wheel)
# - techcompressor-1.0.0.tar.gz (source distribution)
```

### Step 2: Verify Build

```bash
# Check package contents
tar -tzf dist/techcompressor-1.0.0.tar.gz
unzip -l dist/techcompressor-1.0.0-py3-none-any.whl

# Verify metadata
twine check dist/*

# Output should be:
# Checking dist/techcompressor-1.0.0-py3-none-any.whl: PASSED
# Checking dist/techcompressor-1.0.0.tar.gz: PASSED
```

### Step 3: Test Installation

```bash
# Create clean virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from built wheel
pip install dist/techcompressor-1.0.0-py3-none-any.whl

# Test installation
python -c "import techcompressor; print(techcompressor.__version__)"
techcompressor --version
pytest  # Run tests

# Cleanup
deactivate
rm -rf test_env
```

## Signing Releases (Optional but Recommended)

### Generate GPG Signature

```bash
# Sign distribution files
gpg --detach-sign -a dist/techcompressor-1.0.0.tar.gz
gpg --detach-sign -a dist/techcompressor-1.0.0-py3-none-any.whl

# Verify signatures
gpg --verify dist/techcompressor-1.0.0.tar.gz.asc dist/techcompressor-1.0.0.tar.gz
gpg --verify dist/techcompressor-1.0.0-py3-none-any.whl.asc dist/techcompressor-1.0.0-py3-none-any.whl
```

### Publish GPG Public Key

```bash
# Export public key
gpg --armor --export your-email@example.com > techcompressor-signing-key.asc

# Upload to keyserver (optional)
gpg --send-keys YOUR_KEY_ID
```

## Publishing to TestPyPI (Testing)

Before publishing to production PyPI, test with TestPyPI:

### Step 1: Upload to TestPyPI

```bash
# Upload to test repository
twine upload --repository testpypi dist/*

# Or with explicit URL
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

### Step 2: Test Installation from TestPyPI

```bash
# Create clean environment
python -m venv test_testpypi
source test_testpypi/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    techcompressor

# Test
python -c "import techcompressor; print(techcompressor.__version__)"
techcompressor --version

# Cleanup
deactivate
rm -rf test_testpypi
```

## Publishing to PyPI (Production)

**⚠️ WARNING: This step is irreversible. You cannot delete or overwrite releases on PyPI.**

### Step 1: Final Verification

- [ ] All tests pass
- [ ] Version is correct
- [ ] CHANGELOG is updated
- [ ] TestPyPI installation works
- [ ] No uncommitted changes in git

### Step 2: Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Verify tag
git tag -l v1.0.0
git show v1.0.0

# Push tag to GitHub
git push origin v1.0.0
```

### Step 3: Upload to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Output:
# Uploading distributions to https://upload.pypi.org/legacy/
# Uploading techcompressor-1.0.0-py3-none-any.whl
# Uploading techcompressor-1.0.0.tar.gz
```

### Step 4: Verify Publication

```bash
# Check PyPI page
# https://pypi.org/project/techcompressor/1.0.0/

# Test installation
pip install techcompressor==1.0.0

# Verify
python -c "import techcompressor; print(techcompressor.__version__)"
```

## Creating GitHub Release

### Step 1: Draft Release on GitHub

1. Go to: https://github.com/DevaanshPathak/TechCompressor/releases/new
2. **Tag**: Select `v1.0.0` (created earlier)
3. **Title**: `TechCompressor v1.0.0`
4. **Description**: Copy from `RELEASE_NOTES.md`

### Step 2: Attach Artifacts

Upload to the release:
- `techcompressor-1.0.0-py3-none-any.whl`
- `techcompressor-1.0.0.tar.gz`
- `techcompressor-1.0.0.tar.gz.asc` (signature, if created)
- `techcompressor-1.0.0-py3-none-any.whl.asc` (signature, if created)

### Step 3: Publish Release

- [ ] Check "Set as the latest release"
- [ ] Uncheck "This is a pre-release" (unless beta)
- Click **Publish release**

### Alternative: GitHub CLI

```bash
# Install GitHub CLI: https://cli.github.com/

# Create release
gh release create v1.0.0 \
    --title "TechCompressor v1.0.0" \
    --notes-file RELEASE_NOTES.md \
    dist/techcompressor-1.0.0-py3-none-any.whl \
    dist/techcompressor-1.0.0.tar.gz

# Or interactive
gh release create v1.0.0 --generate-notes
```

## Post-Release Tasks

### 1. Verify Installation

```bash
# Fresh install
pip install --upgrade techcompressor

# Test
techcompressor --version
techcompressor --benchmark
techcompressor-gui  # Verify GUI launches
```

### 2. Update Documentation

- [ ] Update README badges (version, downloads, etc.)
- [ ] Update documentation sites (if applicable)
- [ ] Announce release in GitHub Discussions

### 3. Social Media Announcement (Optional)

Example tweet/post:

```
🎉 TechCompressor v1.0.0 is now available!

Multi-algorithm compression (LZW, Huffman, DEFLATE)
🔒 AES-256-GCM encryption
📦 Custom archive format
💻 CLI & GUI interfaces
🧪 137 passing tests

pip install techcompressor

Docs: https://github.com/DevaanshPathak/TechCompressor
#Python #Compression #OpenSource
```

### 4. Monitor Issues

- Watch for installation issues
- Monitor PyPI download stats
- Check GitHub issues/discussions

## Hotfix Releases

For urgent bug fixes (e.g., v1.0.1):

### Quick Process

```bash
# 1. Fix bug on main branch
# 2. Update version to 1.0.1
# 3. Run smoke tests
pytest tests/test_release_smoke.py

# 4. Build and publish
rm -rf dist/
python -m build
twine check dist/*
twine upload dist/*

# 5. Tag and release
git tag -a v1.0.1 -m "Hotfix v1.0.1: Fix XYZ"
git push origin v1.0.1
gh release create v1.0.1 --notes "Hotfix for XYZ issue" dist/*
```

## Troubleshooting

### Build Fails

```bash
# Clean everything
rm -rf dist/ build/ *.egg-info
find . -type d -name __pycache__ -exec rm -rf {} +

# Reinstall build tools
pip install --upgrade build twine

# Retry
python -m build
```

### Twine Upload Fails

```bash
# Check credentials
cat ~/.pypirc

# Check network
curl https://upload.pypi.org/legacy/

# Verbose mode
twine upload --verbose dist/*
```

### Wrong Version Published

**Cannot delete or replace on PyPI!**

Options:
1. Publish hotfix version (e.g., 1.0.1)
2. Mark version as "yanked" on PyPI (prevents new installs, allows existing)
3. Contact PyPI support for special cases

## Security Considerations

### Protect Credentials

- **Never commit** `~/.pypirc` to git
- Use API tokens, not passwords
- Rotate tokens periodically
- Use different tokens for TestPyPI and PyPI

### Verify Uploads

- Check file hashes after upload
- Verify signatures
- Test installation from PyPI immediately

### Audit Trail

- Document who published (maintainer name)
- Keep build logs
- Archive signed artifacts

## Automation (Future)

Consider GitHub Actions for automated releases:

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install build twine
      - name: Build
        run: python -m build
      - name: Publish
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## References

- PyPI Packaging Guide: https://packaging.python.org/
- Twine Documentation: https://twine.readthedocs.io/
- GitHub Releases: https://docs.github.com/en/repositories/releasing-projects-on-github
- PEP 440 (Versioning): https://peps.python.org/pep-0440/

---

**Last Updated**: October 25, 2025  
**Document Version**: 1.0
