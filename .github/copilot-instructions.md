# TechCompressor AI Coding Assistant Instructions

## Project Overview

TechCompressor is a **production-ready (v1.0.0)** modular Python compression framework with three algorithms (LZW, Huffman, DEFLATE), AES-256-GCM encryption, TCAF archive format, CLI, and GUI. Development is complete with 152 passing tests (2 skipped).

## Architecture & Component Interaction

### Core Module (`techcompressor/core.py`) - Central API
All compression operations flow through two main functions with unified signatures:
```python
def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
```

**Algorithm routing** (lines 771-828):
- `algo` parameter determines algorithm: "LZW" | "HUFFMAN" | "DEFLATE" | "AUTO" | "STORED"
- STORED (algorithm ID 0): No compression, direct storage for incompressible files (v2 archives only)
- AUTO mode uses smart heuristics:
  - Files > 5MB: Skip DEFLATE (too slow), try only LZW + Huffman
  - Files > 50MB: Skip Huffman, use only LZW
  - High entropy files (>0.9): Skip all trials, use LZW only (likely already compressed/encrypted)
  - Entropy check: samples first 4KB, calculates unique_bytes/256 ratio
- Each algorithm has private implementation: `_lzw_compress()`, `_huffman_compress()`, `_compress_deflate()`
- Magic headers identify format: `TCZ1` (LZW), `TCH1` (Huffman), `TCD1` (DEFLATE), `TCE1` (encrypted)
- **Critical**: Decompression validates magic headers to prevent wrong-algorithm errors

**Encryption integration** (lines 823-827, 853-858):
- When `password` is provided, `crypto.encrypt_aes_gcm()` wraps compressed data
- Decompression auto-detects `TCE1` header and decrypts before algorithm processing
- No double encryption - encryption only happens at top level

### Compression Algorithm Details

**LZW (lines 20-136)**: Dictionary-based, fast, good for repetitive data
- Dictionary size: 4096 entries (configurable via `MAX_DICT_SIZE`)
- Auto-resets dictionary when full (supports unlimited input)
- Output format: 2-byte big-endian codes (`struct.pack(">H", code)`)

**Huffman (lines 139-363)**: Frequency-based, optimal for non-uniform distributions
- Uses heap-based tree construction with `_HuffmanNode` class
- Serializes tree structure in compressed output for decompression
- Handles single-unique-byte edge case (assigns code "0")

**DEFLATE (lines 366-766)**: Hybrid LZ77 + Huffman
- LZ77 sliding window: 32KB (`DEFAULT_WINDOW_SIZE`), max match: 258 bytes
- Two-pass: LZ77 finds matches → Huffman encodes results
- Best compression ratio but slower than LZW

### Archiver Module (`techcompressor/archiver.py`)
Implements **TCAF v2** (TechCompressor Archive Format) for folders/multiple files:
```python
create_archive(source_path, archive_path, algo="LZW", password=None, per_file=True, progress_callback=None)
extract_archive(archive_path, dest_path, password=None, progress_callback=None)
list_contents(archive_path) -> List[Dict]  # Returns metadata without extraction
```

**Two compression modes**:
- `per_file=True`: Compress each file separately (faster, parallel-friendly, better for mixed content)
- `per_file=False`: Single-stream compression (better ratio for similar files, smaller overhead)

**STORED mode (v2 feature)**:
- When compression expands data (ratio >= 100%), files are stored uncompressed
- Algorithm ID 0 = STORED (no compression, direct storage)
- Only used when `password=None` - encrypted archives always compress even if expansion occurs
- Dramatically reduces archive size for incompressible files (PNG, JPG, MP4, ZIP, etc.)
- Example: 354KB directory with PNGs → 350KB archive (vs 599KB in v1)

**Security features** (lines 32-95):
- `_validate_path()`: Blocks symlinks to prevent infinite loops
- `_check_recursion()`: Prevents creating archive inside source directory
- `_sanitize_extract_path()`: Prevents path traversal attacks (e.g., `../../../etc/passwd`)

**Archive format** (TCAF v2 header):
```
TCAF | version(1) | algo_id(1) | per_file_flag(1) | num_entries(4) | [entry metadata + data]...

Entry table format (v2):
  num_entries(4)
  For each entry:
    filename_len(2) | filename(utf-8) | original_size(8) | compressed_size(8) | 
    mtime(8) | mode(4) | offset(8) | algo_id(1)
```
Version: 2 (supports STORED mode + algo in entry table), backward compatible with v1 archives

### Crypto Module (`techcompressor/crypto.py`)
**AES-256-GCM** with PBKDF2 key derivation:
- Iterations: 100,000 (line 20) - intentionally slow to resist brute-force
- Random salt (16 bytes) and nonce (12 bytes) per encryption
- Authenticated encryption: ciphertext + 16-byte authentication tag
- Output format: `TCE1 | salt | nonce | ciphertext | tag`

**Critical**: Encryption is **one-way only** - no password recovery mechanism. Data loss is permanent without password.

### CLI (`techcompressor/cli.py`)
Command structure: `techcompressor [--gui|--benchmark] <command> [args]`
- `create/c` - Create archive from file/folder
- `extract/x` - Extract archive
- `compress` - Single file compression (no archive overhead)
- `decompress` - Single file decompression
- `list/l` - Show archive contents
- `verify` - Check archive integrity
- `--benchmark` - Run performance tests inline (lines 93-124)

**Entry points** (defined in `pyproject.toml`):
- `techcompressor` - Main command
- `techcmp` - Short alias
- `techcompressor-gui` - Direct GUI launcher (alternative to `--gui` flag)

### Benchmarking (`bench.py`)
Standalone performance testing script with multiple data types:
- **Test data generators**: repetitive, text, random, structured, binary
- **Metrics tracked**: compression ratio, speed (MB/s), encryption overhead
- **Output format**: Pretty-printed tables with size/time comparisons
- Run directly: `python bench.py` (no CLI integration needed)

### GUI (`techcompressor/gui.py`)
Tkinter multi-tab interface with **background threading** (lines 23-32):
- Uses `ThreadPoolExecutor` + `queue.Queue` for non-blocking operations
- Progress polling via `_poll_progress()` method (updates UI without freezing)
- Custom `GUILogHandler` (lines 30-46) redirects Python logging to GUI text widget
- Cancel support via `threading.Event` flag
- **No blocking dialogs**: Success/completion shown via progress bar and status labels only (no `messagebox.showinfo` popups)

**Tab structure**:
- Compress tab: File/folder selection, algorithm picker, password field
- Extract tab: Archive selection, destination picker
- Settings tab: Default algorithm, per-file mode toggle
- Logs tab: Real-time scrolled text with log output

**Recent fixes**:
- Oct 26, 2025: Fixed progress callback signature mismatch between GUI workers and archiver module. GUI now properly adapts `(current, total)` callbacks to `(percent, message)` format for UI updates.
- Oct 26, 2025: Removed blocking success dialogs; operations complete silently with visual feedback in progress bars and status labels.
- Oct 26, 2025: Enhanced progress bar calculation - now shows 0-5% for initialization, 5-95% for file processing (proportional to files processed), and 95-100% for finalization. Status text shows "Compressing/Extracting file X/Y" with actual file counts.
- Oct 26, 2025: Fixed GUILogHandler thread-safety issue - now safely handles logging from background threads without crashing when GUI is closing or not in main loop.
- Oct 26, 2025: Added compression expansion warnings - logs warning when compressed file is larger than original (common for small/incompressible files).
- Oct 26, 2025: Optimized AUTO mode with smart heuristics - entropy detection (>0.9 uses fast LZW-only), size-based algorithm skipping (DEFLATE >5MB, Huffman >50MB). Reduces compression time by 3-10x on large/incompressible files while maintaining quality for compressible data.

## Development Workflow

### Environment & Testing
```bash
pip install -r requirements.txt  # cryptography, tqdm, pytest
pytest                            # Run 152 tests (all should pass, 2 skipped)
python bench.py                   # Performance benchmarks with size/speed comparison
python -m techcompressor.cli --gui  # Launch GUI for manual testing
# OR use entry point:
techcompressor-gui                # Alternative GUI launcher (defined in pyproject.toml)
```

**Platform compatibility**: Cross-platform (Windows/Linux/macOS) with no platform-specific code. Uses `pathlib.Path` for path handling. Tkinter GUI requires Python's built-in `tkinter` module (included on Windows/macOS, may need `python3-tk` package on Linux).

**Windows development**:
- Default shell: PowerShell (pwsh.exe)
- Build script: `build_release.ps1` - automated PyInstaller build with tests
- Commands use PowerShell syntax: `Remove-Item`, `Get-ChildItem`, etc.
- PyInstaller creates standalone `TechCompressor.exe` (~15.4MB in clean venv)
- **Critical**: Use clean virtual environment for builds to avoid bloat from global packages
- **Critical**: `techcompressor.spec` uses `SPECPATH` not `__file__` (PyInstaller limitation)
- **Critical**: GUI must use absolute imports (`from techcompressor.x import y`) not relative imports (`from .x import y`) for PyInstaller compatibility

**Test organization** (`tests/`):
- `test_lzw.py`, `test_huffman.py`, `test_deflate.py` - Algorithm-specific tests
- `test_crypto.py` - Encryption/decryption + password validation
- `test_archiver.py` - Archive creation/extraction + security validation
- `test_integration.py` - Cross-algorithm, end-to-end workflows
- `test_perf_sanity.py` - Performance regression checks

**Critical test patterns**:
- Always test empty input, single byte, large input (triggers dictionary resets)
- Test wrong magic header detection (`ValueError: Invalid magic header`)
- Test password mismatch (`ValueError: Decryption failed - wrong password`)
- Verify compression actually reduces size on repetitive data

### Versioning & Releases
- **Single source of truth**: `techcompressor/__init__.py` defines `__version__`
- Must update **both** `__init__.py` and `pyproject.toml` version fields
- Current: `1.0.0` (Production/Stable)

### Release Workflow
Complete process documented in `publish.md`:

**Pre-release verification**:
```bash
# 1. Update version in __init__.py and pyproject.toml
# 2. Update CHANGELOG.md and RELEASE_NOTES.md
# 3. Run full test suite
pytest                                       # Must pass all tests
pytest tests/test_release_smoke.py -v        # Quick validation (14 tests)
python bench.py                              # Performance check

# 4. Clean build artifacts (PowerShell on Windows)
Remove-Item -Recurse -Force dist/, build/, *.egg-info -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

**Build and publish**:
```bash
# 1. Build packages
python -m build                              # Creates wheel + source dist
twine check dist/*                           # Verify package metadata

# 2. Test in clean environment (PowerShell on Windows)
python -m venv test_env
.\test_env\Scripts\Activate.ps1             # Linux/Mac: source test_env/bin/activate
pip install dist/techcompressor-*.whl
python -c "import techcompressor; print(techcompressor.__version__)"
deactivate

# 3. Publish to TestPyPI (optional but recommended)
twine upload --repository testpypi dist/*

# 4. Create Git tag and publish to PyPI
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
twine upload dist/*                          # ⚠️ Irreversible!
```

**Windows executable build** (PyInstaller):
```powershell
# Automated via build_release.ps1 script
.\build_release.ps1                          # Runs tests, builds EXE, creates release package

# Manual build (if needed)
python -m PyInstaller techcompressor.spec --clean
# Output: dist\TechCompressor.exe (standalone GUI executable)
```

**Critical release requirements**:
- Version must be updated in BOTH `__init__.py` and `pyproject.toml`
- All 152 tests must pass (2 skipped is expected) before tagging
- TestPyPI validation recommended for major releases
- Git tag format: `v{major}.{minor}.{patch}` (e.g., `v1.0.0`)
- PyInstaller spec file (`techcompressor.spec`) includes all dependencies and data files
- **PyInstaller gotcha**: Use `SPECPATH` variable, not `__file__` (not defined in spec context)
- **PyInstaller gotcha**: Use absolute imports in entry point files (gui.py) not relative imports

## Critical Patterns & Conventions

### Logging Pattern
```python
from techcompressor.utils import get_logger
logger = get_logger(__name__)  # Returns pre-configured logger with standard format
```
Format: `[INFO] techcompressor.core: Starting LZW compression of 1024 bytes`

### Type Hints (PEP 604 unions with `|`)
```python
def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
```
**Requires Python 3.10+** - don't use `Optional[str]` or `Union[str, None]`

### Error Handling Philosophy
- `NotImplementedError`: For unsupported algorithms (e.g., "ARITHMETIC")
- `ValueError`: For corrupted data, wrong passwords, invalid paths
- **No silent failures**: Always raise exceptions for unrecoverable errors
- Magic header validation is **mandatory** - prevents algorithm mismatch bugs

### Progress Callbacks (for GUI/CLI integration)
**Archiver signature**: `progress_callback(current: int, total: int)` - receives file count progress
**GUI adaptation**: Converts to `(percent, message)` format internally for UI updates

```python
# Archiver calls with (current_file, total_files)
def progress_callback(current: int, total: int):
    percent = int((current / max(total, 1)) * 100)
    message = f"Processing file {current}/{total}"
    # Send to GUI queue...
```

Used in `archiver.py` for file-by-file progress during archive creation/extraction.

## Performance Characteristics

**Algorithm selection guide** (from benchmarks):
- **DEFLATE**: Best compression ratio (~1% on repetitive data), moderate speed (6 MB/s) - SLOW on large files, skipped in AUTO >5MB
- **LZW**: Fastest (3 MB/s), decent ratio (~9%), lowest memory - AUTO's default fallback
- **Huffman**: Middle ground (~44% ratio, 2.5 MB/s) - skipped in AUTO >50MB
- **AUTO mode optimizations**:
  - Entropy detection: samples first 4KB, calculates unique_bytes/256
  - High entropy (>0.9) = incompressible → fast LZW-only path
  - Size-based algorithm skipping reduces compression time by 3-10x on large files
  - Random 1MB: ~1.2s (entropy-optimized)
  - Repetitive 10MB: ~10s with 99.9% compression (DEFLATE skipped)

**Encryption overhead**: ~50-100ms for PBKDF2 key derivation (intentional security feature)

**Archive modes**:
- `per_file=False`: Better for text/source code (similar content benefits from shared dictionary)
- `per_file=True`: Better for mixed content, media files, or when parallel processing desired

**Memory considerations**:
- LZW dictionary: ~32KB (4096 entries × 8 bytes)
- Huffman tree: ~512 bytes worst case (256 leaf nodes)
- DEFLATE sliding window: 32KB
- All algorithms support streaming for files >16MB (no full-memory load)

**When compression doesn't help** (important):
- **Small files** (< 500 bytes): Compression overhead (headers, metadata) often exceeds savings
- **Already compressed**: JPG, PNG, MP4, ZIP, EXE files are already compressed - will expand!
- **Encrypted/Random data**: No patterns to compress - will expand!
- **Expected behavior**: AUTO mode logs WARNING when output > input, archiver logs expansion ratio
- **Solution**: For archives with mixed content, this is normal - compressed files expand slightly, text files shrink significantly, overall archive still benefits

## Security Considerations

**Path safety** (`archiver.py`):
- Always call `_validate_path()` before file operations
- Use `_sanitize_extract_path()` when extracting archives
- Reject symlinks by default (prevents traversal outside expected boundaries)

**Encryption notes**:
- Password loss = permanent data loss (no backdoors)
- PBKDF2 intentionally slow (~50-100ms) - don't "optimize" iteration count
- Compression reveals patterns even with encryption (semantic security limitation)

## Common Pitfalls

1. **Don't use terminal commands for Python execution in tests** - use `pytest` directly
2. **Magic headers are 4 bytes** - always check `len(data) >= 4` before slicing
3. **LZW codes are 2 bytes** - compressed data length must be even (validation at line 96)
4. **Huffman tree serialization** - tree format is tightly coupled to decompression logic
5. **GUI threading** - all Tkinter widget updates must use `.after()` or run in main thread
6. **Archive recursion** - always check output path not inside source path
7. **PyInstaller spec files** - use `SPECPATH` not `__file__` (undefined in spec execution context)
8. **PyInstaller entry points** - use absolute imports (`from techcompressor.x`) not relative (`from .x`) in files run as main entry points

## When Adding Features

1. **Maintain API stability**: `compress()` and `decompress()` signatures are public API
2. **Add tests first**: Follow TDD pattern - write test, implement, verify
3. **Update magic headers**: New formats need unique 4-byte identifiers
4. **Document algorithms**: Include Big-O complexity, trade-offs in docstrings
5. **Benchmark regressions**: Run `bench.py` before committing performance changes

## License & Contact
MIT License - Copyright (c) 2025 Devaansh Pathak  
Repository: https://github.com/DevaanshPathak/TechCompressor
