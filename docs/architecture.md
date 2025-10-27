# TechCompressor Architecture

## High-Level Overview

TechCompressor is designed as a modular compression framework with clear separation of concerns. Each module handles a specific aspect of the compression pipeline, making the codebase maintainable, testable, and extensible.

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                       │
│  ┌──────────────┐              ┌──────────────────┐    │
│  │   CLI (cli.py)   │              │   GUI (gui.py)     │    │
│  │  - argparse      │              │  - Tkinter         │    │
│  │  - commands      │              │  - threading       │    │
│  └────────┬─────────┘              └─────────┬──────────┘    │
└───────────┼────────────────────────────────────┼────────────┘
            │                                    │
            └─────────────────┬──────────────────┘
                              │
            ┌─────────────────▼─────────────────┐
            │      Core API (core.py)           │
            │  compress(data, algo, password)   │
            │  decompress(data, algo, password) │
            └─────────────────┬─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Algorithms  │     │  Encryption  │     │   Archiver   │
│  (core.py)   │     │  (crypto.py) │     │(archiver.py) │
│              │     │              │     │              │
│ - LZW        │     │ - AES-256    │     │ - TCAF v2    │
│ - Huffman    │     │ - PBKDF2     │     │ - Metadata   │
│ - DEFLATE    │     │ - GCM auth   │     │ - Security   │
│ - STORED     │     │              │     │ - Recovery   │
└──────────────┘     └──────────────┘     └──────┬───────┘
        │                     │                   │
        └─────────────────────┼───────────────────┘
                              │                   │
                      ┌───────▼────────┐   ┌──────▼────────┐
                      │  Utils (utils.py) │   │  Recovery     │
                      │  - Logging        │   │ (recovery.py) │
                      │  - Helpers        │   │  - Reed-Solomon│
                      └───────────────────┘   └───────────────┘
```

**v1.1.0 Architecture Additions:**
- `recovery.py` module for PAR2-style error correction
- Solid compression state management in `core.py` (global dictionary persistence)
- Multi-threading support in `archiver.py` (ThreadPoolExecutor)
- STORED algorithm for incompressible file detection

## Module Responsibilities

### 1. Core Module (`techcompressor/core.py`)
**Purpose**: Central compression/decompression API and algorithm implementations

**Key Functions**:
- `compress(data, algo, password)` - Unified compression entry point
- `decompress(data, algo, password)` - Unified decompression entry point

**Internal Implementations**:
- `_lzw_compress()` / `_lzw_decompress()` - LZW algorithm
- `_huffman_compress()` / `_huffman_decompress()` - Huffman coding
- `_compress_deflate()` / `_decompress_deflate()` - DEFLATE algorithm

**Data Flow**:
```
Input → Algorithm Selection → Compression → Add Magic Header → [Encryption] → Output
```

**Magic Headers**:
- `TCZ1` - LZW compressed data
- `TCH1` - Huffman compressed data
- `TCD1` - DEFLATE compressed data
- `TCE1` - Encrypted data (wraps any compressed format)

### 2. Crypto Module (`techcompressor/crypto.py`)
**Purpose**: Authenticated encryption for password-protected compression

**Key Functions**:
- `encrypt_aes_gcm(data, password)` - Encrypt with AES-256-GCM
- `decrypt_aes_gcm(data, password)` - Decrypt and verify authentication
- `derive_key(password, salt)` - PBKDF2 key derivation

**Security Properties**:
- AES-256-GCM provides confidentiality and authenticity
- PBKDF2-HMAC-SHA256 with 100,000 iterations resists brute-force
- Random salt and nonce per encryption (no key reuse)
- 16-byte authentication tag prevents tampering

**Encryption Format**:
```
[TCE1 magic][16B salt][12B nonce][ciphertext][16B auth_tag]
```

### 3. Archiver Module (`techcompressor/archiver.py`)
**Purpose**: Multi-file archives with metadata preservation

**Key Functions**:
- `create_archive(source, dest, algo, password, per_file, callback)` - Create TCAF archive
- `extract_archive(archive, dest, password, callback)` - Extract TCAF archive
- `list_contents(archive)` - List archive entries without extraction

**Archive Modes**:
1. **Per-file mode** (`per_file=True`):
   - Each file compressed independently
   - Better for selective extraction and random access
   - Slightly larger archive size

2. **Single-stream mode** (`per_file=False`):
   - All files compressed as one stream
   - Better compression ratio (shared dictionary)
   - Must extract all files to access one

**Security Features**:
- `_validate_path()` - Rejects symlinks, validates existence
- `_check_recursion()` - Prevents archive inside source directory
- `_sanitize_extract_path()` - Prevents path traversal attacks (e.g., `../../etc/passwd`)

**TCAF Format**:
```
[TCAF magic][version:1][algo_id:1][per_file:1][num_entries:4]
[entry_1_metadata][entry_1_data]
[entry_2_metadata][entry_2_data]
...
```

Entry metadata: `[name_len:4][name:utf8][is_dir:1][mtime:8][size:8][data_len:8]`

### 4. CLI Module (`techcompressor/cli.py`)
**Purpose**: Command-line interface with argparse

**Commands**:
- `create/c <source> <archive>` - Create archive
- `extract/x <archive> <dest>` - Extract archive
- `compress <input> <output>` - Single file compression
- `decompress <input> <output>` - Single file decompression
- `list/l <archive>` - List contents
- `verify <archive>` - Check integrity

**Global Flags**:
- `--gui` - Launch GUI
- `--benchmark` - Run inline performance tests
- `--version` - Show version

**Entry Points** (in `pyproject.toml`):
- `techcompressor` - Main command
- `techcmp` - Short alias
- `techcompressor-gui` - Direct GUI launch

### 5. GUI Module (`techcompressor/gui.py`)
**Purpose**: Tkinter-based graphical interface

**Architecture**:
- **Main Thread**: UI updates, event handling (Tkinter requirement)
- **Worker Threads**: Background compression/decompression (via `ThreadPoolExecutor`)
- **Communication**: `queue.Queue` for progress updates from workers to main thread

**Threading Pattern**:
```python
# Worker submits progress
progress_queue.put(('compress', percent, message))

# Main thread polls queue
def _poll_progress():
    while True:
        msg = progress_queue.get_nowait()
        # Update UI (safe in main thread)
```

**Tabs**:
1. **Compress**: Source selection, algorithm picker, password, progress
2. **Extract**: Archive selection, destination, password, progress
3. **Settings**: Default algorithm, compression level, per-file mode
4. **Logs**: Real-time application logs via custom `GUILogHandler`

### 6. Utils Module (`techcompressor/utils.py`)
**Purpose**: Shared utilities and logging configuration

**Key Functions**:
- `get_logger(name)` - Returns pre-configured logger with standard format

**Logging Format**:
```
[LEVEL] module_name: message
```

## Data Flow Examples

### Example 1: Simple Compression
```
User → CLI → compress(data, "LZW", None)
         ↓
    _lzw_compress(data)
         ↓
    Add TCZ1 header + compressed_data
         ↓
    Return to user
```

### Example 2: Encrypted Archive
```
User → GUI → create_archive(folder, "archive.tc", "DEFLATE", "password")
         ↓
    For each file:
      compress(file_data, "DEFLATE", None)
         ↓
    Build TCAF structure
         ↓
    encrypt_aes_gcm(archive_data, "password")
         ↓
    Write to archive.tc
```

### Example 3: Extraction with Progress
```
User → CLI → extract_archive(archive, dest, password, progress_callback)
         ↓
    Read TCAF header
         ↓
    decrypt_aes_gcm(data, password) if encrypted
         ↓
    For each entry:
      progress_callback(current, total, message)
      decompress(entry_data, detected_algo, None)
      Write to dest/entry_path
```

## Design Principles

### 1. Separation of Concerns
- Algorithms are pure functions (no I/O, no side effects)
- Encryption is orthogonal to compression
- Archive format is independent of algorithms
- UI layers don't know algorithm internals

### 2. Magic Header Pattern
Every format has a unique 4-byte identifier:
- Enables automatic format detection
- Prevents wrong-algorithm decompression errors
- Supports future format extensions

### 3. Progress Callbacks
All long-running operations accept optional callbacks:
```python
def progress_callback(current: int, total: int, message: str) -> bool:
    """Return False to cancel."""
    return True  # Continue
```
This pattern enables:
- GUI progress bars
- CLI tqdm integration
- Operation cancellation
- Unified API across interfaces

### 4. Security by Default
- All path operations are validated
- Symlinks are rejected by default
- Archive extraction is sanitized
- Encryption uses best practices (no shortcuts)

### 5. Testability
- Pure functions for algorithms (easy unit testing)
- Mocked I/O for archive tests
- Integration tests verify end-to-end flows
- Performance regression tests prevent slowdowns

## Extension Points

### Adding New Algorithms
1. Implement `_algo_compress(data)` and `_algo_decompress(data)` in `core.py`
2. Add magic header constant (e.g., `MAGIC_HEADER_ALGO = b"TCA1"`)
3. Update `compress()` and `decompress()` routing logic
4. Add algorithm to CLI choices and GUI combo boxes
5. Write tests in `tests/test_algo.py`

### Adding New Archive Formats
1. Implement `create_custom_archive()` and `extract_custom_archive()` in `archiver.py`
2. Define format magic header and structure
3. Reuse existing compression and encryption infrastructure
4. Add CLI commands and GUI options
5. Write integration tests

### Adding New Interfaces
1. Import `core` module functions
2. Implement UI-specific logic (CLI flags, GUI widgets, web endpoints, etc.)
3. Use progress callbacks for long operations
4. Handle errors with user-friendly messages
5. Test with real user workflows

## Performance Considerations

### Algorithm Selection
- **LZW**: O(n) time, O(dictionary_size) space, best for speed
- **Huffman**: O(n log n) time (tree building), O(n) space, good for entropy
- **DEFLATE**: O(n * window_size) time, O(window_size) space, best compression

### Memory Management
- Streaming for large files (16MB chunks)
- Dictionary resets in LZW prevent unbounded growth
- Generator patterns for archive iteration (future optimization)

### Threading Model
- GUI uses ThreadPoolExecutor with max_workers=2
- I/O-bound operations benefit from threading
- CPU-bound compression could use ProcessPoolExecutor (future)

## Dependencies Graph

```
gui.py, cli.py
    ↓
archiver.py ──→ core.py ──→ crypto.py
                  ↓             ↓
               utils.py ←──────┘
```

**External Dependencies**:
- `cryptography`: AES-GCM, PBKDF2 (crypto.py)
- `tqdm`: Progress bars (cli.py, archiver.py)
- `tkinter`: GUI (gui.py, standard library)

## Future Architecture Considerations

1. **Plugin System**: Load algorithms dynamically
2. **Streaming API**: Process data in chunks without loading all into memory
3. **Parallel Compression**: Multi-threaded per-file compression in archives
4. **Format Versioning**: Support reading older TCAF versions
5. **Cloud Integration**: S3/Azure Blob storage backends
