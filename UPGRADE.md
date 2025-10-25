# Upgrade Guide

## Upgrading to v1.0.0

### For New Users

v1.0.0 is the first production release of TechCompressor. If you're installing for the first time, follow the standard installation process:

```bash
# Clone repository
git clone https://github.com/DevaanshPathak/TechCompressor.git
cd TechCompressor

# Install dependencies
pip install -r requirements.txt

# Run tests to verify installation
pytest
```

### For Beta/Development Users

If you used pre-release versions of TechCompressor, this guide will help you migrate to the stable v1.0.0 release.

## Breaking Changes

**None** - This is the initial production release.

## What's New

See [CHANGELOG.md](CHANGELOG.md) and [RELEASE_NOTES.md](RELEASE_NOTES.md) for complete feature list.

**Key Highlights**:
- ✅ Three compression algorithms (LZW, Huffman, DEFLATE)
- ✅ AES-256-GCM encryption
- ✅ TCAF archive format
- ✅ CLI and GUI interfaces
- ✅ 137 passing tests

## API Compatibility

### Public API (Stable)

These APIs are considered **stable** and will maintain backward compatibility in future 1.x releases:

**Core Module**:
```python
from techcompressor.core import compress, decompress

# Signatures guaranteed stable
compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
```

**Archiver Module**:
```python
from techcompressor.archiver import create_archive, extract_archive, list_contents

# Signatures guaranteed stable
create_archive(source_path, archive_path, algo="LZW", password=None, per_file=True, progress_callback=None)
extract_archive(archive_path, dest_path, password=None, progress_callback=None)
list_contents(archive_path) -> List[Dict]
```

**Crypto Module**:
```python
from techcompressor.crypto import encrypt_aes_gcm, decrypt_aes_gcm

# Signatures guaranteed stable
encrypt_aes_gcm(data: bytes, password: str) -> bytes
decrypt_aes_gcm(data: bytes, password: str) -> bytes
```

### Internal APIs (Unstable)

Private functions (prefixed with `_`) are **not** part of the public API and may change without notice:
- `_lzw_compress()`, `_lzw_decompress()`
- `_huffman_compress()`, `_huffman_decompress()`
- `_compress_deflate()`, `_decompress_deflate()`
- `_validate_path()`, `_check_recursion()`, `_sanitize_extract_path()`
- `_HuffmanNode` class

**Do not** rely on these in your code. Use the public API instead.

## File Format Compatibility

### Archive Format (TCAF)

**Version**: 1
**Compatibility**: Forward-compatible

- Archives created with v1.0.0 will be readable by future versions
- Future versions may introduce TCAF version 2+ with new features
- TechCompressor will always read TCAF version 1 archives

**Migration**: None required - this is the initial format version.

### Compression Formats

**Formats**: TCZ1 (LZW), TCH1 (Huffman), TCD1 (DEFLATE), TCE1 (Encrypted)
**Compatibility**: Stable

- Magic headers will not change
- Format structures are frozen for v1.x
- Future algorithms will use new magic headers (e.g., TCA1, TCB1)

## Command-Line Interface

### CLI Commands (Stable)

These commands are stable and will maintain backward compatibility:

```bash
# Core commands
techcompressor create <source> <archive> [options]
techcompressor extract <archive> <dest> [options]
techcompressor compress <input> <output> [options]
techcompressor decompress <input> <output> [options]
techcompressor list <archive>
techcompressor verify <archive>

# Global flags
techcompressor --version
techcompressor --gui
techcompressor --benchmark
```

### Entry Points

```bash
techcompressor        # Main command (stable)
techcmp              # Short alias (stable)
techcompressor-gui   # GUI launcher (new in v1.0.0)
```

## Configuration

### Settings

TechCompressor v1.0.0 does not use configuration files. All settings are passed as command-line arguments or API parameters.

**Future versions** may introduce:
- `~/.techcompressor/config.yaml` for default settings
- Environment variables for algorithm/encryption defaults

When introduced, these will be **opt-in** and will not affect existing workflows.

## Deprecation Policy

### v1.x Series

- **No breaking changes** in 1.x minor/patch releases (1.1.0, 1.2.0, 1.0.1, etc.)
- New features may be added (new algorithms, new options)
- Deprecations will be announced with **2 minor versions** notice
- Example: Feature deprecated in 1.2.0 → removed in 1.4.0 (min 6 months)

### v2.0.0 and Beyond

- Breaking changes will only occur in major versions (2.0.0, 3.0.0)
- Migration guides will be provided before major releases
- Old APIs will be deprecated before removal (with warnings)

## Known Migration Patterns

### Pattern 1: Hardcoded Algorithms

**Before** (if you used internal constants):
```python
# DON'T DO THIS - internal constant
from techcompressor.core import MAGIC_HEADER_LZW
```

**After**:
```python
# Use public API instead
from techcompressor.core import compress
compressed = compress(data, algo="LZW")
# Magic header is internal implementation detail
```

### Pattern 2: Direct Archive Format Parsing

**Before** (if you parsed archives manually):
```python
# DON'T DO THIS - format is internal
with open('archive.tc', 'rb') as f:
    magic = f.read(4)
    # ... manual parsing ...
```

**After**:
```python
# Use public API
from techcompressor.archiver import list_contents
contents = list_contents('archive.tc')
for entry in contents:
    print(entry['name'], entry['size'])
```

### Pattern 3: Password Handling

**v1.0.0 Best Practice**:
```python
# Always use string passwords
password = "my_secure_password"
compressed = compress(data, algo="DEFLATE", password=password)

# Never use bytes (not supported)
# password = b"password"  # ❌ ValueError
```

## Testing Your Upgrade

After upgrading to v1.0.0, run these checks:

```bash
# 1. Verify installation
python -c "import techcompressor; print(techcompressor.__version__)"
# Should print: 1.0.0

# 2. Run tests
pytest

# 3. Test CLI
techcompressor --version
techcompressor --benchmark

# 4. Test GUI
techcompressor-gui

# 5. Test API
python -c "
from techcompressor.core import compress, decompress
data = b'test'
compressed = compress(data, 'DEFLATE')
assert decompress(compressed, 'DEFLATE') == data
print('✓ API working')
"
```

## Getting Help

If you encounter issues upgrading:

1. **Check Known Issues**: [RELEASE_NOTES.md](RELEASE_NOTES.md#known-issues)
2. **Read Documentation**: [README.md](README.md), [docs/](docs/)
3. **Search Issues**: [GitHub Issues](https://github.com/DevaanshPathak/TechCompressor/issues)
4. **Ask Community**: [GitHub Discussions](https://github.com/DevaanshPathak/TechCompressor/discussions)
5. **Report Bugs**: [New Issue](https://github.com/DevaanshPathak/TechCompressor/issues/new)

## Future Upgrade Guides

This section will be updated for future releases:

### Planned for v1.1.0
- Arithmetic coding algorithm
- Performance improvements
- Additional CLI options

### Planned for v1.2.0
- Configuration file support
- Plugin system for custom algorithms
- Parallel compression for archives

### Planned for v2.0.0
- API refinements based on v1.x feedback
- Breaking changes (if any) will be documented here

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0
