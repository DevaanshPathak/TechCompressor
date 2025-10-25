# TechCompressor AI Coding Assistant Instructions

## Project Overview

TechCompressor is a **production-ready (v1.0.0)** modular Python compression framework with three algorithms (LZW, Huffman, DEFLATE), AES-256-GCM encryption, TCAF archive format, CLI, and GUI. Development is complete with 137 passing tests.

## Architecture & Component Interaction

### Core Module (`techcompressor/core.py`) - Central API
All compression operations flow through two main functions with unified signatures:
```python
def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes
```

**Algorithm routing** (lines 771-828):
- `algo` parameter determines algorithm: "LZW" | "HUFFMAN" | "DEFLATE"
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
Implements **TCAF** (TechCompressor Archive Format) for folders/multiple files:
```python
create_archive(source_path, archive_path, algo="LZW", password=None, per_file=True, progress_callback=None)
extract_archive(archive_path, dest_path, password=None, progress_callback=None)
list_contents(archive_path) -> List[Dict]  # Returns metadata without extraction
```

**Two compression modes**:
- `per_file=True`: Compress each file separately (faster, parallel-friendly, better for mixed content)
- `per_file=False`: Single-stream compression (better ratio for similar files, smaller overhead)

**Security features** (lines 32-95):
- `_validate_path()`: Blocks symlinks to prevent infinite loops
- `_check_recursion()`: Prevents creating archive inside source directory
- `_sanitize_extract_path()`: Prevents path traversal attacks (e.g., `../../../etc/passwd`)

**Archive format** (header at line 17):
```
TCAF | version(1) | algo_id(1) | per_file_flag(1) | num_entries(4) | [entry metadata + data]...
```

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

### GUI (`techcompressor/gui.py`)
Tkinter multi-tab interface with **background threading** (lines 23-32):
- Uses `ThreadPoolExecutor` + `queue.Queue` for non-blocking operations
- Progress polling via `_poll_progress()` method (updates UI without freezing)
- Custom `GUILogHandler` (lines 30-46) redirects Python logging to GUI text widget
- Cancel support via `threading.Event` flag

**Tab structure**:
- Compress tab: File/folder selection, algorithm picker, password field
- Extract tab: Archive selection, destination picker
- Settings tab: Default algorithm, per-file mode toggle
- Logs tab: Real-time scrolled text with log output

## Development Workflow

### Environment & Testing
```bash
pip install -r requirements.txt  # cryptography, tqdm, pytest
pytest                            # Run 137 tests (all should pass)
python bench.py                   # Performance benchmarks with size/speed comparison
python -m techcompressor.cli --gui  # Launch GUI for manual testing
```

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
```python
def progress_callback(current: int, total: int, message: str) -> bool:
    """Return False to cancel operation."""
    print(f"{message}: {current}/{total}")
    return True  # Continue

create_archive(..., progress_callback=progress_callback)
```
Used in `archiver.py` and `gui.py` for responsive UIs during long operations.

## Performance Characteristics

**Algorithm selection guide** (from benchmarks):
- **DEFLATE**: Best compression ratio (~1% on repetitive data), moderate speed (6 MB/s)
- **LZW**: Fastest (3 MB/s), decent ratio (~9%), lowest memory
- **Huffman**: Middle ground (~44% ratio, 2.5 MB/s)

**Encryption overhead**: ~50-100ms for PBKDF2 key derivation (intentional security feature)

**Archive modes**:
- `per_file=False`: Better for text/source code (similar content benefits from shared dictionary)
- `per_file=True`: Better for mixed content, media files, or when parallel processing desired

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

## When Adding Features

1. **Maintain API stability**: `compress()` and `decompress()` signatures are public API
2. **Add tests first**: Follow TDD pattern - write test, implement, verify
3. **Update magic headers**: New formats need unique 4-byte identifiers
4. **Document algorithms**: Include Big-O complexity, trade-offs in docstrings
5. **Benchmark regressions**: Run `bench.py` before committing performance changes

## License & Contact
MIT License - Copyright (c) 2025 Devaansh Pathak  
Repository: https://github.com/DevaanshPathak/TechCompressor
