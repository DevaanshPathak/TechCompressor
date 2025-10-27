# TechCompressor AI Coding Assistant Instructions

## Project Overview

TechCompressor is a **production-ready (v1.2.0)** modular Python compression framework with three algorithms (LZW, Huffman, DEFLATE), AES-256-GCM encryption, TCAF v2 archive format with recovery records, advanced file filtering, multi-volume archives, and incremental backups. Developed by **Devaansh Pathak** ([GitHub](https://github.com/DevaanshPathak)).

**Target**: Python 3.10+ | **Status**: Production/Stable | **License**: MIT | **Tests**: 168 passing

## New in v1.2.0
- **Advanced File Filtering**: Exclude patterns (*.tmp, .git/), size limits, date ranges for selective archiving
- **Multi-Volume Archives**: Split large archives into parts (archive.tc.001, .002, etc.) with configurable volume sizes
- **Incremental Backups**: Only compress changed files since last archive creation (timestamp-based)
- **Enhanced Entropy Detection**: Automatically skip compression on already-compressed formats (JPG, PNG, MP4, ZIP, etc.)
- **Archive Metadata**: User comments, creation date, and creator information in archive headers
- **File Attributes Preservation**: Windows ACLs and Linux extended attributes support

## Architecture & Component Interaction

### Core Module (`techcompressor/core.py`) - Central API (1059 lines)
All compression operations flow through these main functions:
```python
def compress(data: bytes, algo: str = "LZW", password: str | None = None, persist_dict: bool = False) -> bytes
def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
def reset_solid_compression_state() -> None  # Reset dictionary state between archives
def is_likely_compressed(data: bytes, filename: str | None = None) -> bool  # Entropy + extension check
```

**Algorithm routing** (core.py lines 771-828):
- `algo` parameter: "LZW" | "HUFFMAN" | "DEFLATE" | "AUTO" | "STORED"
- STORED (algorithm ID 0): No compression, direct storage for incompressible files
- AUTO mode smart heuristics (see `compress()` function):
  - Files > 5MB: Skip DEFLATE (too slow), try only LZW + Huffman
  - Files > 50MB: Skip Huffman, use only LZW
  - High entropy (>0.9) or compressed extension: Use LZW only (already compressed/encrypted)
  - Entropy check: samples first 4KB, calculates `unique_bytes/256` ratio
  - Extension check: detects 40+ compressed formats (JPG, PNG, MP4, ZIP, PDF, etc.)
- Each algorithm has private implementation: `_lzw_compress()`, `_huffman_compress()`, `_compress_deflate()`
- **Magic headers** (4 bytes): `TCZ1` (LZW), `TCH1` (Huffman), `TCD1` (DEFLATE), `TCE1` (encrypted), `TCAF` (archive)
- **Critical**: Decompression validates magic headers to prevent wrong-algorithm errors

**Encryption integration** (core.py lines 823-827, 853-858):
- When `password` is provided, `crypto.encrypt_aes_gcm()` wraps compressed data
- Decompression auto-detects `TCE1` header and decrypts before algorithm processing
- No double encryption - encryption only happens at top level

### Compression Algorithm Details

**LZW** (core.py lines 20-136): Dictionary-based, fast, good for repetitive data
- Dictionary size: 4096 entries (configurable via `MAX_DICT_SIZE`)
- Auto-resets dictionary when full (supports unlimited input)
- Output format: 2-byte big-endian codes (`struct.pack(">H", code)`)
- **Solid compression**: `persist_dict=True` preserves dictionary between files (10-30% better ratios)
- **Global state**: `_solid_lzw_dict` and `_solid_lzw_next_code` - reset with `reset_solid_compression_state()`

**Huffman** (core.py lines 139-363): Frequency-based, optimal for non-uniform distributions
- Uses heap-based tree construction with `_HuffmanNode` class
- Serializes tree structure in compressed output for decompression
- Handles single-unique-byte edge case (assigns code "0")

**DEFLATE** (core.py lines 366-766): Hybrid LZ77 + Huffman
- LZ77 sliding window: 32KB (`DEFAULT_WINDOW_SIZE`), max match: 258 bytes
- Two-pass: LZ77 finds matches → Huffman encodes results
- Best compression ratio but slower than LZW

### Archiver Module (`techcompressor/archiver.py` - 858 lines)
Implements **TCAF v2** (TechCompressor Archive Format) for folders/multiple files:
```python
create_archive(source_path, archive_path, algo="LZW", password=None, per_file=True, 
               recovery_percent=0.0, max_workers=None, progress_callback=None,
               exclude_patterns=None, max_file_size=None, min_file_size=None,
               volume_size=None, incremental=False, base_archive=None,
               comment=None, creator=None)
extract_archive(archive_path, dest_path, password=None, progress_callback=None)
list_contents(archive_path) -> List[Dict]  # Returns metadata without extraction
```

**Two compression modes**:
- `per_file=True`: Compress each file separately (faster, parallel-friendly, better for mixed content)
- `per_file=False`: Single-stream compression (better ratio for similar files, smaller overhead, enables solid mode)

**STORED mode (v2 feature)**:
- When compression expands data (ratio >= 100%), files are stored uncompressed
- Algorithm ID 0 = STORED (no compression, direct storage)
- Only used when `password=None` - encrypted archives always compress even if expansion occurs
- Dramatically reduces archive size for incompressible files (PNG, JPG, MP4, ZIP, etc.)
- Example: 354KB directory with PNGs → 350KB archive (vs 599KB in v1)

**Security features** (archiver.py lines 32-95):
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

### Crypto Module (`techcompressor/crypto.py` - 120 lines)
**AES-256-GCM** with PBKDF2 key derivation:
- Iterations: 100,000 (line 20) - intentionally slow to resist brute-force
- Random salt (16 bytes) and nonce (12 bytes) per encryption
- Authenticated encryption: ciphertext + 16-byte authentication tag
- Output format: `TCE1 | salt | nonce | ciphertext | tag`

**Critical**: Encryption is **one-way only** - no password recovery mechanism. Data loss is permanent without password.

### CLI (`techcompressor/cli.py` - 380 lines)
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

### Recovery Module (`techcompressor/recovery.py` - 304 lines)
PAR2-style error correction for archive repair:
- **Reed-Solomon Implementation**: `ReedSolomonSimple` class with XOR-based parity
- **Block-based Recovery**: 64KB blocks with configurable parity (0-10% redundancy)
- **Archive Integration**: Recovery footer appended to TCAF v2 archives (TCRR marker)
- **Functions**: `generate_recovery_records()`, `apply_recovery()`, `verify_recovery()`
- **Critical**: Can recover from single-block corruption; multi-block requires more parity

### GUI (`techcompressor/gui.py` - 750 lines)
Tkinter multi-tab interface with **background threading** (lines 23-32):
- Uses `ThreadPoolExecutor` + `queue.Queue` for non-blocking operations
- Progress polling via `_poll_progress()` method (updates UI without freezing)
- **Thread-safety rule**: ALL widget updates MUST use `.after(0, callback)` - never modify widgets from worker threads
- Progress callbacks: GUI expects `(percent: float, message: str)` format, archiver provides `(current: int, total: int)` - GUI adapts these
- Keyboard shortcuts: Ctrl+Shift+C (compress), Ctrl+Shift+E (extract)


## AI Contributor Quick Guide

This repository is a production Python compression tool (LZW, Huffman, DEFLATE) with AES-256-GCM encryption, a TCAF v2 archive format, CLI and Tkinter GUI. Tests (168) are in `tests/` and must remain green for releases.

### Critical APIs - DO NOT BREAK
- **Primary API**: `techcompressor/core.py` exposes `compress(data, algo, password, persist_dict)` and `decompress(data, algo, password)`. Public signature must remain stable.
- **Archiver**: `techcompressor/archiver.py` implements TCAF v2. `per_file` vs single-stream affects compression ratio and behavior (STORED mode used when expansion occurs).
- **Crypto**: `techcompressor/crypto.py` uses AES-256-GCM + PBKDF2 (100k iterations). Do NOT weaken iterations or alter header format (`TCE1 | salt | nonce | ciphertext | tag`).
- **CLI/GUI**: `techcompressor/cli.py` and `techcompressor/gui.py` are entry points. GUI must keep thread-safety (use `.after()` for widget updates); progress callbacks are `(current:int, total:int)` and GUI adapts them to `(percent, message)`.

### Code Conventions & Gotchas
- **Magic headers** are 4 bytes (e.g. `TCZ1`, `TCH1`, `TCD1`, `TCE1`, `TCAF`, `TCRR`) — decompression validates them
- **LZW format**: 2-byte big-endian words (`struct.pack(">H", code)`) — maintain packing conventions
- **Type hints**: Use PEP 604 (`str | None`) not `Optional[str]` — project targets Python 3.10+
- **Logging**: Use `from techcompressor.utils import get_logger`; follow existing message format
- **Test patterns**: Add tests before feature code; follow patterns in `tests/*_*.py`:
  - Edge cases: empty input, single byte, large input (>1MB), boundary conditions
  - Security: wrong magic header, password mismatch, path traversal attempts
  - Roundtrip: compress → decompress → verify equality
- **Global state**: Only LZW dictionary (`_solid_lzw_dict`) has global state - reset with `reset_solid_compression_state()`
- **Error handling**: Raise `ValueError` for user input errors, `RuntimeError` for internal errors

### Common Developer Workflows (exact commands)
```powershell
# ⚠️ CRITICAL: ALWAYS activate virtual environment FIRST before any command
# This prevents building with global packages (creates bloated builds)
D:/TechCompressor/.venv/Scripts/Activate.ps1

# Setup (after venv activation)
pip install -r requirements.txt

# Run all tests (must pass before commits)
pytest

# Quick smoke test (20 seconds vs 2+ minutes full suite)
pytest tests/test_release_smoke.py -v

# Test with coverage report
pytest --cov=techcompressor --cov-report=html

# Benchmarks (standalone script)
python bench.py

# GUI development (hot-reload friendly)
python -m techcompressor.cli --gui
# OR
techcompressor-gui

# Windows release build (runs tests automatically, REQUIRES venv activation)
.\build_release.ps1
```

### File Organization & Responsibilities
```
techcompressor/
├── core.py          # Algorithm routing, compress/decompress API (1059 lines)
├── archiver.py      # TCAF format, multi-file archives, security (858 lines)
├── crypto.py        # AES-256-GCM, PBKDF2 key derivation (120 lines)
├── recovery.py      # PAR2-style Reed-Solomon error correction (304 lines)
├── cli.py           # Argument parsing, command dispatch (380 lines)
├── gui.py           # Tkinter interface, threading, progress (750 lines)
└── utils.py         # Logging configuration, shared utilities (50 lines)

tests/
├── test_release_smoke.py    # 20s sanity checks for releases
├── test_lzw.py              # LZW edge cases + roundtrip
├── test_huffman.py          # Huffman tree construction + serialization
├── test_deflate.py          # DEFLATE LZ77 + Huffman integration
├── test_crypto.py           # Encryption, key derivation, authentication
├── test_archiver.py         # Archive creation, security, metadata
└── test_integration.py      # Cross-module workflows, end-to-end
```

### When Changing Behavior - Pre-Commit Checklist
1. ✅ Keep public API signatures stable (`core.compress/decompress`, `archiver.create_archive/extract_archive`)
2. ✅ Update/extend unit tests in `tests/` and run `pytest` locally (all must pass)
3. ✅ Preserve magic header checks and crypto header layout (4-byte headers are part of file format spec)
4. ✅ If adding new archive format or magic bytes, register a unique 4-byte header and add tests
5. ✅ Update `techcompressor/__init__.py` and `pyproject.toml` together when bumping versions
6. ✅ For new public functions, add to `__all__` in `__init__.py`
7. ✅ Run `pytest tests/test_release_smoke.py -v` for fast validation before pushing

---

## CRITICAL: Release Documentation Checklist

**BEFORE suggesting a release or running build_release.ps1, ALWAYS update these files:**

**IMPORTANT**: Do NOT create RELEASE_CHECKLIST_*.md or RELEASE_SUMMARY_*.md files - these are excluded from the repository.

1. **README.md**:
   - Version badge (line 3): `[![Version](https://img.shields.io/badge/version-X.X.X-blue.svg)]`
   - Test count badge (line 6): `[![Tests](https://img.shields.io/badge/tests-XXX%20passed-brightgreen.svg)]`
   - Feature descriptions (add new v1.X.X features under "Features")
   - Python API examples (update function signatures with new parameters)
   - Comparison table (update with new features vs competitors)
   - **NO EMOJIS**: README.md must not contain any emoji characters

2. **RELEASE_NOTES.md**:
   - Update version in title: `# TechCompressor vX.X.X Release Notes`
   - Update release date: `**Release Date**: Month DD, YYYY`
   - Add "What's New in vX.X.X" section with all new features
   - Update "Migration from vX.Y.Z to vX.X.X" section
   - Update "Recommended Usage" section with new parameters/features
   - Update code examples with new function signatures

3. **CHANGELOG.md**:
   - Add new version section at top with release date
   - List all Added/Changed/Fixed items in detail
   - Include performance metrics if applicable
   - Reference related issue numbers if available

4. **SECURITY.md** (if applicable):
   - Update security policy if new features affect security model
   - Update supported versions table
   - Add any new security considerations

5. **pyproject.toml**:
   - Update `version = "X.X.X"` (line 7)

6. **techcompressor/__init__.py**:
   - Update `__version__ = "X.X.X"`
   - Update `__all__` exports if new public functions added

7. **tests/test_release_smoke.py**:
   - Update version assertion: `assert techcompressor.__version__ == "X.X.X"`

8. **.github/copilot-instructions.md** (this file):
   - Update "Project Overview" version number
   - Update "New in vX.X.X" section
   - Update API signatures in examples

8. **GUI Credits**:
   - Ensure GUI displays developer credits: "Developed by Devaansh Pathak (GitHub: DevaanshPathak)"

**DO NOT:**
- Suggest building or releasing without updating ALL documentation first
- Tell user "ready for release" until all markdown files are updated
- Skip updating comparison tables or feature lists
- Forget to update test count badges after adding new tests

---

## Quick Reference for Common Tasks

**Files to inspect first for most tasks**: `techcompressor/core.py`, `archiver.py`, `crypto.py`, `cli.py`, `gui.py`, `utils.py`, `bench.py`, `build_release.ps1`, and `tests/`.

**Example: Adding a new compression algorithm**:
1. Implement `_myalgo_compress(data: bytes) -> bytes` and `_myalgo_decompress(data: bytes) -> bytes` in `core.py`
2. Register magic header: `MAGIC_HEADER_MYALGO = b"TCM1"` (4 bytes, unique)
3. Add to `ALGO_MAP` in `archiver.py`: `{"MYALGO": 5}`
4. Update `compress()` and `decompress()` routing logic in `core.py`
5. Add tests in `tests/test_myalgo.py` following existing patterns
6. Update CLI help text in `cli.py` to include new algorithm
7. Add to GUI algorithm dropdown in `gui.py`
8. Run full test suite: `pytest`

**Example: Adding a new CLI command**:
1. Add argument parser in `cli.py` under `main()` function
2. Implement command handler function (e.g., `def handle_mycommand(args):`)
3. Add tests in `tests/test_cli.py` (if exists) or `test_integration.py`
4. Update README.md CLI usage section
5. Verify with: `techcompressor mycommand --help`

If anything above is unclear or you want more examples (small patch + tests), ask which area to expand and I will add concrete examples with test patterns.
