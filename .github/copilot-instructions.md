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
## TechCompressor — AI contributor quick guide

This repository is a production Python compression tool (LZW, Huffman, DEFLATE) with
AES-256-GCM encryption, a TCAF v2 archive format, a CLI and a Tkinter GUI. Tests (~152)
are in `tests/` and must remain green for releases.

What matters for an AI editing this repo (short):
- Primary API: `techcompressor/core.py` exposes compress(data, algo, password) and
  decompress(data, algo, password). Do not change the public signature.
- Archiver: `techcompressor/archiver.py` implements TCAF v2. `per_file` vs single-stream
  affects compression ratio and behavior (STORED mode used when expansion occurs).
- Crypto: `techcompressor/crypto.py` uses AES-256-GCM + PBKDF2 (100k iterations).
  Do NOT weaken iterations or alter header format (`TCE1 | salt | nonce | ciphertext | tag`).
- CLI/GUI: `techcompressor/cli.py` and `techcompressor/gui.py` are entry points. GUI must
  keep thread-safety (use `.after()` for widget updates); progress callbacks are
  `(current:int, total:int)` and GUI adapts them to `(percent, message)`.

Conventions & gotchas to preserve:
- Magic headers are 4 bytes (e.g. `TCZ1`,`TCH1`,`TCD1`,`TCE1`) — decompression validates them.
- LZW code format: 2-byte big-endian words — keep packing/unpacking conventions.
- Type hints use PEP 604 (`str | None`) — project targets Python 3.10+.
- Logging: use `from techcompressor.utils import get_logger`; follow existing message format.
- Tests: add tests before feature code; follow patterns in `tests/*_*.py` (empty input, single byte,
  large input, wrong magic header, password mismatch).

Common developer workflows (use these exact commands):
- Setup: `pip install -r requirements.txt`
- Tests: `pytest` (or `pytest tests/test_release_smoke.py -v` for quick smoke)
- Benchmarks: `python bench.py`
- GUI dev: `python -m techcompressor.cli --gui` or `techcompressor-gui`
- Windows release: run PowerShell script `.uild_release.ps1` (uses PyInstaller; note `SPECPATH` use).

When changing behavior, follow this checklist:
1. Keep public API signatures stable (`core.compress/decompress`).
2. Update/extend unit tests in `tests/` and run `pytest` locally.
3. Preserve magic header checks and crypto header layout.
4. If adding new archive format or magic bytes, register a unique 4-byte header and add tests.
5. Update `techcompressor/__init__.py` and `pyproject.toml` together when bumping versions.

Files to inspect first for most tasks: `techcompressor/core.py`, `archiver.py`, `crypto.py`,
`cli.py`, `gui.py`, `utils.py`, `bench.py`, `build_release.ps1`, and `tests/`.

If anything above is unclear or you want more examples (small patch + tests), tell me which
area to expand and I will add a short, concrete example change and its tests.
- `test_archiver.py` - Archive creation/extraction + security validation
