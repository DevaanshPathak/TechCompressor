# AI Agent Development Guide for TechCompressor

**Last Updated**: October 30, 2025  
**Project Version**: v1.3.0 (in development - Week 2 complete)  
**For**: AI Coding Assistants (GitHub Copilot, Cursor, etc.)

---

## 🤖 Purpose of This Document

This guide helps AI coding assistants understand TechCompressor's architecture, development workflow, and best practices. It's designed to enable agents to:
- Make safe, contextual code changes
- Follow established patterns and conventions
- Avoid common pitfalls and breaking changes
- Contribute effectively without human oversight

---

## ⚠️ CRITICAL: First Steps

### 1. Virtual Environment Activation (ALWAYS REQUIRED)

**Before ANY terminal command, activate the virtual environment:**

```powershell
# Windows PowerShell (PRIMARY)
D:\TechCompressor\.venv\Scripts\Activate.ps1

# Verify activation - should see (.venv) prefix
# Correct: (.venv) PS D:\TechCompressor>
# Wrong:   PS D:\TechCompressor>
```

**Why this is critical:**
- Using global Python packages creates bloated, broken builds
- Dependencies may be wrong versions or missing
- Build scripts (`build_release.ps1`) will fail
- Tests may pass locally but fail in production

**Enforcement checklist:**
- ✅ Check for `(.venv)` prefix in terminal prompt
- ✅ If missing, run activation script before proceeding
- ✅ NEVER run `pip`, `pytest`, or `python` commands without venv
- ✅ Document this requirement when suggesting terminal commands

### 2. Read the Copilot Instructions

**Before making any code changes:**
```bash
# Read the main instructions
cat .github/copilot-instructions.md
```

This file contains:
- Architecture overview
- API contracts (DO NOT BREAK)
- Code conventions
- Testing patterns
- Common workflows

---

## 📐 Project Architecture

### Component Hierarchy
```
techcompressor/
├── core.py          # 🎯 CENTRAL API - compress/decompress routing
├── archiver.py      # 📦 TCAF format, multi-volume, attributes
├── crypto.py        # 🔒 AES-256-GCM encryption
├── recovery.py      # 🛡️ PAR2-style error correction
├── cli.py           # 💻 Command-line interface
├── gui.py           # 🎨 Tkinter GUI
└── utils.py         # 🔧 Logging, shared utilities
```

### Data Flow
```
User Input → CLI/GUI → core.compress() → Algorithm → crypto.encrypt_aes_gcm() → Output
                               ↓
                         archiver.create_archive() (for folders)
                               ↓
                         VolumeWriter (multi-volume)
```

---

## 🚨 NEVER BREAK These APIs

### Public API Contract (Stable Since v1.0.0)

#### `techcompressor.core`
```python
# ✅ STABLE - Do not change signatures
def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
```

#### `techcompressor.archiver`
```python
# ✅ STABLE - Only add optional parameters with defaults
def create_archive(
    source_path: str | Path,
    archive_path: str | Path,
    algo: str = "LZW",
    password: str | None = None,
    per_file: bool = True,
    # ... more optional params ...
) -> None

def extract_archive(
    archive_path: str | Path,
    dest_path: str | Path,
    password: str | None = None,
    # ... more optional params ...
) -> None

def list_contents(archive_path: str | Path) -> List[Dict]
```

**Rules:**
- ✅ Can add new optional parameters (with defaults)
- ✅ Can add new functions
- ❌ NEVER change existing parameter names
- ❌ NEVER change existing parameter types
- ❌ NEVER remove parameters
- ❌ NEVER change return types

---

## 🎯 Development Workflow

### Before Starting Work
```powershell
# 1. Activate venv
D:\TechCompressor\.venv\Scripts\Activate.ps1

# 2. Update dependencies (if needed)
pip install -r requirements.txt

# 3. Run tests to establish baseline
pytest -q

# 4. Check current version
python -c "import techcompressor; print(techcompressor.__version__)"
```

### Making Changes
```powershell
# 1. Make your edits (follow conventions below)

# 2. Run smoke tests (fast verification)
pytest tests/test_release_smoke.py -v

# 3. Run full test suite
pytest

# 4. Check for errors
pytest --tb=short

# 5. Verify imports work
python -c "import techcompressor.archiver; print('OK')"
```

### Before Committing
```bash
# All tests must pass
pytest -q

# Check test count hasn't decreased
# Expected: 193 passed, 3-4 skipped (platform-specific)
```

---

## 📝 Code Conventions

### Type Hints (Python 3.10+ Style)
```python
# ✅ Correct - PEP 604 union types
def process(data: bytes | None) -> str | None:
    pass

# ❌ Wrong - Old-style Optional
from typing import Optional
def process(data: Optional[bytes]) -> Optional[str]:
    pass
```

### Magic Headers (4 Bytes, Immutable)
```python
# ✅ Existing headers - DO NOT CHANGE
MAGIC_HEADER_LZW = b"TCZ1"
MAGIC_HEADER_HUFFMAN = b"TCH1"
MAGIC_HEADER_DEFLATE = b"TCD1"
MAGIC_HEADER_ENCRYPTED = b"TCE1"
MAGIC_HEADER_ARCHIVE = b"TCAF"
MAGIC_HEADER_RECOVERY = b"TCRR"

# ✅ Adding new algorithm? Register unique 4-byte header
MAGIC_HEADER_ZSTD = b"TCS1"  # Example for v2.0.0
```

### Logging
```python
# ✅ Use project logger
from techcompressor.utils import get_logger
logger = get_logger(__name__)

logger.debug("Detailed debug info")
logger.info("User-facing information")
logger.warning("Non-fatal issues")
logger.error("Errors that need attention")

# ❌ Don't use print() except in CLI output
```

### Error Handling
```python
# ✅ User input errors
if not file.exists():
    raise ValueError(f"File not found: {file}")

# ✅ Internal errors
if len(data) < 4:
    raise RuntimeError("Invalid data format")

# ✅ Always provide context in error messages
raise ValueError(f"Invalid algorithm '{algo}'. Must be one of: LZW, HUFFMAN, DEFLATE")
```

---

## 🧪 Testing Patterns

### Test File Naming
```
tests/
├── test_lzw.py          # Algorithm-specific tests
├── test_archiver.py     # Archive functionality tests
├── test_integration.py  # Cross-module tests
└── test_release_smoke.py # Pre-release sanity checks
```

### Test Structure
```python
def test_feature_description():
    """Clear docstring explaining what's being tested."""
    # Arrange
    input_data = b"test data"
    
    # Act
    result = compress(input_data, algo="LZW")
    
    # Assert
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Roundtrip verification
    decompressed = decompress(result, algo="LZW")
    assert decompressed == input_data
```

### Edge Cases to Always Test
```python
# ✅ Empty input
def test_empty_input():
    assert compress(b"") == b"..."

# ✅ Single byte
def test_single_byte():
    assert decompress(compress(b"A")) == b"A"

# ✅ Large input (>1MB)
def test_large_input():
    data = b"X" * (2 * 1024 * 1024)
    assert decompress(compress(data)) == data

# ✅ Wrong password
def test_wrong_password():
    compressed = compress(b"data", password="correct")
    with pytest.raises(Exception):
        decompress(compressed, password="wrong")

# ✅ Corrupted data
def test_corrupted_data():
    with pytest.raises(ValueError):
        decompress(b"INVALID")
```

---

## 🔒 Security Considerations

### Path Validation (Archive Extraction)
```python
# ✅ Always validate paths in archiver.py
def _sanitize_extract_path(base: Path, filename: str) -> Path:
    """Prevent path traversal attacks."""
    # Block: ../../../etc/passwd
    # Block: /absolute/paths
    # Block: C:\Windows\System32
    
# ✅ Check symlinks
def _validate_path(path: Path) -> bool:
    """Reject symlinks to prevent infinite loops."""
    if path.is_symlink():
        return False
```

### Encryption Best Practices
```python
# ✅ Encryption is one-way - no password recovery
# ✅ Use random salt and nonce per encryption
# ✅ Verify authentication tags
# ❌ NEVER weaken PBKDF2 iterations (100,000 minimum)
# ❌ NEVER store passwords in logs or error messages
```

---

## 📦 Archive Format (TCAF v2)

### Format Structure
```
TCAF v2 Archive:
  Header:
    Magic: "TCAF" (4 bytes)
    Version: 2 (1 byte)
    Per-file flag: 0/1 (1 byte)
    Encrypted flag: 0/1 (1 byte)
    Metadata: creation_date, comment, creator
    Entry table offset: (8 bytes)
  
  Entry Table:
    num_entries (4 bytes)
    For each entry:
      filename_len (2) | filename (utf-8)
      original_size (8) | compressed_size (8)
      mtime (8) | mode (4) | offset (8)
      algo_id (1) | attrs_len (4) | attributes (JSON)
  
  File Data:
    Entry 1 data
    Entry 2 data
    ...
```

### Version Compatibility
- **v1 archives**: Readable by v1.2.0+ (backward compatible)
- **v2 archives**: Include STORED mode, attributes, metadata
- **v3 (future)**: Will include new algorithms (Zstandard, Brotli)

---

## � Recent Bug Fixes & Known Issues

### ✅ FIXED: Multi-Volume Space Calculation Bug (Oct 30, 2025)

**Issue**: When creating multi-volume archives with attributes, volumes would exceed their target size by 54 bytes (the TCVOL header size), causing position calculation mismatches during extraction.

**Symptoms**:
- `UnicodeDecodeError` when extracting multi-volume archives with attributes enabled
- Error occurred specifically when reading entry table: "utf-8 codec can't decode byte"
- Only manifested with combination: multi-volume + attributes + STORED mode (incompressible data)

**Root Cause**:
In `VolumeWriter.write()` (archiver.py line 382), after opening a new volume with a 54-byte TCVOL header, the code incorrectly set:
```python
space_left = self.volume_size  # WRONG - ignored header already written
```

This caused each volume after the first to be 54 bytes larger than intended, breaking the position calculations used by `VolumeWriter.tell()` and `VolumeReader.seek()`.

**Fix**:
Changed to recalculate space_left accounting for the header:
```python
space_left = self.volume_size - self.current_size  # Correct - accounts for header
```

**Location**: `techcompressor/archiver.py`, line 382 in `VolumeWriter.write()`

**Test Coverage**: `tests/test_file_attributes.py::test_attributes_with_multi_volume`

**Lesson for Agents**:
- Always recalculate size/space values after state changes (like opening new volumes)
- Multi-volume logic must account for headers in EVERY volume, not just the first
- Position calculations must be consistent between writer and reader
- Test edge cases: multi-volume + features that add metadata/headers

---

## �🚀 Performance Guidelines

### Memory Management
```python
# ✅ Stream large files (>16MB)
def process_large_file(path: Path):
    with open(path, 'rb') as f:
        while chunk := f.read(16 * 1024 * 1024):  # 16MB chunks
            yield compress(chunk)

# ❌ Don't load entire file into memory
def bad_approach(path: Path):
    return compress(path.read_bytes())  # OOM for large files
```

### Algorithm Selection
```python
# Fast but lower ratio
compress(data, algo="LZW")  # 3 MB/s

# Balanced
compress(data, algo="DEFLATE")  # 6 MB/s, better ratio

# Text-optimized
compress(data, algo="HUFFMAN")  # 2.5 MB/s

# v2.0.0 Future
compress(data, algo="ZSTD")  # 400-600 MB/s (planned)
```

---

## 🎨 GUI Development (Tkinter)

### Thread Safety (CRITICAL)
```python
# ✅ Always update widgets from main thread
self.root.after(0, self._update_progress, percent, message)

# ❌ NEVER modify widgets from worker threads
def worker():
    self.progress_bar.set(50)  # WRONG - will crash
```

### Background Operations
```python
# ✅ Use ThreadPoolExecutor for long operations
self.executor.submit(self._compress_worker, args)

# ✅ Provide cancel mechanism
if self.cancel_flag.is_set():
    raise InterruptedError("Cancelled by user")

# ✅ Use progress queues for status updates
self.progress_queue.put(('compress', 50, "Compressing..."))
```

---

## 🆕 Adding New Features

### Checklist for New Algorithm
```bash
# 1. Implement in core.py
def _myalgo_compress(data: bytes) -> bytes:
    # Implementation

def _myalgo_decompress(data: bytes) -> bytes:
    # Implementation

# 2. Register magic header
MAGIC_HEADER_MYALGO = b"TCM1"

# 3. Add to ALGO_MAP in archiver.py
ALGO_MAP = {"MYALGO": 5}

# 4. Update compress() and decompress() routing

# 5. Write tests in tests/test_myalgo.py
def test_myalgo_roundtrip():
    assert decompress(compress(data, algo="MYALGO"), algo="MYALGO") == data

# 6. Update CLI help text in cli.py

# 7. Add to GUI algorithm dropdown in gui.py

# 8. Update documentation (README.md, CHANGELOG.md)

# 9. Run full test suite
pytest
```

### Checklist for New Archive Feature
```bash
# 1. Update create_archive() signature with optional parameter
def create_archive(..., new_feature: bool = False):

# 2. Update extract_archive() if extraction changes
def extract_archive(..., new_feature: bool = False):

# 3. Update TCAF format if needed (increment version?)

# 4. Write comprehensive tests
tests/test_new_feature.py

# 5. Update CLI parameters in cli.py

# 6. Update GUI controls in gui.py

# 7. Update documentation (README, RELEASE_NOTES, CHANGELOG)

# 8. Verify backward compatibility
# Can old archives still be extracted?

# 9. Run full test suite
pytest
```

---

## 🐛 Debugging Tips

### Common Issues

**Import errors:**
```powershell
# Check venv is activated
# Look for (.venv) prefix

# Reinstall dependencies
pip install -r requirements.txt

# Check for circular imports
python -c "import techcompressor"
```

**Test failures:**
```powershell
# See detailed error
pytest tests/test_file.py::test_name -v --tb=long

# Run single test
pytest tests/test_lzw.py::test_lzw_roundtrip -v

# See print statements
pytest -s
```

**Archive corruption:**
```python
# Check magic header
with open("archive.tc", "rb") as f:
    magic = f.read(4)
    print(f"Magic: {magic}")  # Should be b"TCAF"

# List contents without extraction
from techcompressor.archiver import list_contents
contents = list_contents("archive.tc")
print(contents)
```

---

## 📚 Documentation Standards

### Docstring Format
```python
def function_name(param: type) -> return_type:
    """Brief one-line description.
    
    Detailed explanation if needed. Explain what the function does,
    not how it does it (code speaks for itself).
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When and why
        RuntimeError: When and why
        
    Example:
        >>> function_name(value)
        expected_result
    """
```

### Comment Style
```python
# ✅ Explain WHY, not WHAT
# Using 100k iterations for brute-force resistance
iterations = 100_000

# ❌ Don't state the obvious
# Set iterations to 100000
iterations = 100_000
```

---

## 🎯 v2.0.0 Roadmap Context

**See `ROADMAP_v2.0.0.md` for full details**

### Planned Features
1. **Textual TUI**: Modern terminal interface (Months 3-6)
2. **Zstandard Algorithm**: Fast compression (Months 1-2)
3. **Brotli Algorithm**: Web-optimized (Months 1-2)

### Preparation Tasks
- Keep architecture modular for easy algorithm addition
- Maintain backward compatibility with v1.x archives
- Document API contracts clearly
- Write extensible tests

---

## ✅ Agent Self-Check Checklist

Before submitting changes, verify:

- [ ] Virtual environment was activated before all commands
- [ ] All 190 tests passing (3 skipped platform-specific)
- [ ] No changes to public API signatures
- [ ] New features have comprehensive tests
- [ ] Error messages are clear and actionable
- [ ] Documentation updated (if adding features)
- [ ] Logging uses project logger (not print)
- [ ] Type hints follow PEP 604 (Python 3.10+)
- [ ] Code follows existing patterns
- [ ] No security vulnerabilities introduced

---

## 🤝 Contributing Philosophy

**As an AI agent, you should:**
- ✅ Follow established patterns religiously
- ✅ Write tests before implementation
- ✅ Preserve backward compatibility
- ✅ Document your changes clearly
- ✅ Think about edge cases
- ✅ Respect the existing architecture

**Avoid:**
- ❌ Breaking changes without major version bump
- ❌ Clever code that's hard to understand
- ❌ Skipping tests "because it's simple"
- ❌ Ignoring conventions for personal preference
- ❌ Global state (except LZW dictionary)
- ❌ Platform-specific code without fallbacks

---

## 📞 Getting Help

**Resources:**
- `README.md` - User documentation
- `.github/copilot-instructions.md` - Detailed architecture
- `CHANGELOG.md` - Version history
- `RELEASE_NOTES.md` - Feature descriptions
- `ROADMAP_v2.0.0.md` - Future plans
- Test files - Practical examples

**When stuck:**
1. Read related test files for patterns
2. Check existing similar features
3. Review error messages carefully
4. Use `git log` to see how similar changes were made
5. Run `pytest -v` to see which tests are failing

---

## 📊 Project Statistics (v1.3.0)

- **Lines of Code**: ~5,200 (excluding tests)
- **Test Files**: 12 files
- **Test Count**: 190 passing, 3 skipped (platform-specific)
- **Test Coverage**: >85%
- **Algorithms**: 3 (LZW, Huffman, DEFLATE) + STORED mode
- **Archive Format**: TCAF v2
- **Multi-Volume**: v1.3.0+ with TCVOL headers (.part1/.part2 naming)
- **Security**: AES-256-GCM, PBKDF2 (100K iterations)
- **Python Version**: 3.10+
- **Dependencies**: cryptography, pyinstaller, pytest, coverage

---

**Remember**: You're working on production code used by real users. Every change should be thoughtful, tested, and backward compatible. When in doubt, preserve existing behavior and add new features as opt-in.

**Happy coding! 🚀**
