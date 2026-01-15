# TechCompressor v2.0.0 Release Notes

**Release Date**: January 15, 2026  
**Status**: Production/Stable

## Overview

TechCompressor v2.0.0 is a major release introducing two new high-performance compression algorithms (Zstandard and Brotli) and a modern Terminal User Interface (TUI) built with Textual. This release dramatically expands TechCompressor's capabilities with industry-leading compression speeds and web-optimized compression ratios.

## Highlights

### Five Compression Algorithms
Choose the algorithm that fits your needs:
- **Zstandard (NEW)**: Ultra-fast compression at 400-600 MB/s with excellent ratios, developed by Meta
- **Brotli (NEW)**: Web-optimized compression, 20-30% better than DEFLATE on text/HTML/JSON, developed by Google
- **DEFLATE**: Industry-standard hybrid compression (LZ77 + Huffman), best compatibility
- **LZW**: Lightning-fast dictionary-based compression, ideal for repetitive data
- **Huffman**: Frequency-based compression optimized for non-uniform distributions

### Modern Terminal User Interface (TUI)
A rich, interactive terminal interface powered by Textual:
- **File Browser**: Navigate and select files/folders visually
- **Algorithm Selection**: Choose from all 5 algorithms via dropdown
- **Encryption Support**: Toggle encryption with secure password modal
- **Multi-Volume Support**: Create split archives with custom volume sizes
- **Archive Inspector**: View archive contents without extraction
- **Real-time Progress**: Live progress bars and operation status
- **Keyboard Shortcuts**: Power-user friendly navigation
- Launch with: `techcompressor --tui` or `techcompressor-tui`

### Military-Grade Security
Password-protected compression uses **AES-256-GCM** authenticated encryption with **PBKDF2** key derivation (100,000 iterations). Every encryption generates unique salts and nonces, and includes integrity verification via authentication tags. There are no backdoors or recovery mechanisms - security by design.

### Flexible Archiving with Advanced Features
The custom **TCAF v2** (TechCompressor Archive Format) supports:
- **Advanced File Filtering**: Exclude patterns (*.tmp, .git/), size limits
- **Multi-Volume Archives**: Split into parts (archive.tc.part1, .part2, etc.)
- **Incremental Backups**: Only compress changed files since last archive
- **Archive Metadata**: User comments, creation date, creator information
- **File Attributes**: Windows ACLs and Linux/macOS extended attributes
- **Recovery Records**: PAR2-style error correction
- **Solid Compression**: Dictionary persistence for 10-30% better ratios

### Triple Interface
- **CLI**: Full-featured command-line with all algorithms and features
- **GUI**: User-friendly Tkinter application with background threading
- **TUI (NEW)**: Modern Textual-based terminal interface with rich widgets

### Production-Ready
**228 tests passing** (4 platform-specific skipped). Comprehensive test coverage includes algorithm correctness, encryption validation, archive security, multi-volume handling, new algorithm validation, TUI imports, and performance regression checks.

---

## What's New in v2.0.0

### Zstandard Compression Algorithm
Ultra-fast compression developed by Meta/Facebook:
- **Speed**: 400-600 MB/s compression, 800+ MB/s decompression
- **Ratio**: Comparable to DEFLATE with 10-100x faster speed
- **Magic Header**: `TCS1`
- **Algorithm ID**: 5
- **Default Level**: 3 (balanced speed/ratio)
- **Use Cases**: Large file compression, real-time streaming, backup operations

```python
from techcompressor import compress, decompress

# Zstandard compression (fastest)
compressed = compress(data, algo="ZSTD")
original = decompress(compressed, algo="ZSTD")

# With encryption
compressed = compress(data, algo="ZSTD", password="secret")
```

### Brotli Compression Algorithm
Web-optimized compression developed by Google:
- **Ratio**: 20-30% better than DEFLATE on text content
- **Optimized For**: HTML, JSON, CSS, JavaScript, APIs
- **Magic Header**: `TCB1`
- **Algorithm ID**: 6
- **Default Quality**: 6 (balanced speed/ratio)
- **Use Cases**: Web content, API responses, text-heavy archives

```python
# Brotli compression (best for text)
compressed = compress(html_content, algo="BROTLI")
original = decompress(compressed, algo="BROTLI")
```

### Textual Terminal User Interface
Modern, interactive terminal interface:
- **Rich Text Rendering**: Colors, styling, and Unicode support
- **Mouse Support**: Click to select files and buttons
- **File Browser Pane**: Visual navigation of filesystem
- **Operation Pane**: Algorithm selection, encryption toggle, volume size
- **Progress Pane**: Real-time progress bars with status messages
- **Log Pane**: Operation history and status messages
- **Modals**: Password input, archive contents viewer, about dialog

```bash
# Launch TUI
techcompressor --tui
techcompressor-tui
techcompressor tui
```

---

## Migration from v1.x to v2.0.0

### No Breaking Changes
v2.0.0 is fully backward compatible with v1.x archives and API. No code changes required.

### New Algorithm Support
To use new algorithms, simply specify them:
```python
# Before (still works)
compressed = compress(data, algo="DEFLATE")

# New options
compressed = compress(data, algo="ZSTD")    # Fastest
compressed = compress(data, algo="BROTLI")  # Best for text
```

### New Dependencies
v2.0.0 requires additional dependencies:
```bash
pip install textual>=0.75.0 zstandard>=0.22.0 brotli>=1.1.0
```

---

## Algorithm Comparison

| Algorithm | Speed | Ratio | Best For |
|-----------|-------|-------|----------|
| **Zstandard** | 400-600 MB/s | Excellent | Large files, backups, streaming |
| **Brotli** | 20-50 MB/s | Excellent | HTML, JSON, CSS, web content |
| **DEFLATE** | 6 MB/s | Excellent | General purpose, compatibility |
| **LZW** | 3 MB/s | Good | Repetitive data, speed-critical |
| **Huffman** | 2.5 MB/s | Good | Text, frequency-skewed data |

---

## What Was New in v1.4.0

### Enhanced Stability
This release focuses on refinement and stability:
- Fixed minor edge cases in multi-volume archive extraction
- Improved error messages for common failure scenarios
- Better progress reporting with more accurate estimates
- Enhanced GUI responsiveness during large operations

### Performance Improvements
- Optimized memory usage for large archive operations
- Reduced startup time through lazy imports
- Improved entropy detection accuracy for mixed content

### Bug Fixes
- Improved compatibility with older Python 3.10 versions
- Fixed rare race condition in parallel compression mode
- Refined multi-volume handling for edge cases

---

## What Was New in v1.3.0

### TCVOL Multi-Volume Headers
Volume files now include structured metadata headers to improve reliability and reduce antivirus false positives:
- Magic header `TCVOL` with version, volume number, and total volumes
- Changed naming from `.001/.002` to `.part1/.part2` format
- I/O throttling (10ms delay) between volume writes

### Optional pywin32 Dependency
Windows ACL operations are now opt-in only:
- Default builds exclude pywin32, significantly reducing executable size
- Install with `pip install techcompressor[windows-acls]` for ACL features
- Graceful degradation when pywin32 not available

---

## Migration from v1.3.0 to v1.4.0

### No Breaking Changes
v1.4.0 is fully backward compatible with v1.3.0. No code changes required.

### Recommended Actions
1. Update via pip: `pip install --upgrade techcompressor`
2. Existing archives remain fully compatible
3. Multi-volume archives created with v1.2.0 (.001/.002) are still readable

---

## API Reference

### Core Functions
```python
from techcompressor import compress, decompress

# Basic compression
compressed = compress(data, algo="LZW")
original = decompress(compressed, algo="LZW")

# With encryption
compressed = compress(data, algo="DEFLATE", password="secret")
original = decompress(compressed, algo="DEFLATE", password="secret")
```

### Archive Functions
```python
from techcompressor.archiver import create_archive, extract_archive, list_contents

# Create archive with filtering
create_archive(
    "project/",
    "backup.tc",
    algo="DEFLATE",
    password="secret",
    exclude_patterns=["*.tmp", ".git/", "__pycache__/"],
    volume_size=650*1024*1024,  # Multi-volume: 650MB parts
    comment="Weekly backup"
)

# Extract archive
extract_archive("backup.tc", "restored/", password="secret")

# List contents
contents = list_contents("backup.tc")
```

---

## System Requirements

- **Python**: 3.10 or higher
- **Dependencies**: cryptography>=41.0.0, tqdm>=4.65.0
- **Optional**: pywin32>=306 (for Windows ACL preservation)
- **OS**: Windows, Linux, macOS

---

## Credits

**Developed by**: Devaansh Pathak  
**GitHub**: [DevaanshPathak](https://github.com/DevaanshPathak)  
**License**: MIT
    base_archive="backup-full.tc"
)
```

### 🔍 Enhanced Entropy Detection
Smarter automatic format recognition for incompressible files:
- **40+ Formats Detected**: JPG, PNG, GIF, MP4, MP3, ZIP, RAR, 7Z, PDF, DOCX, and more
- **Extension-Based Detection**: Fast file type checks before content analysis
- **Auto STORED Mode**: Incompressible files stored directly (no wasted compression)
- **20-30% Faster**: Reduced processing time by skipping futile compression attempts
- **Entropy Sampling**: Analyzes first 4KB to calculate compression potential

### 📝 Archive Metadata
User-defined metadata for documentation and provenance:
- **Comment Field**: Add notes to archives (e.g., "Monthly backup - Q4 2025")
- **Creator Information**: Track who created the archive
- **Creation Date**: Automatic timestamp recording
- **Retrievable via list_contents()**: Read metadata without full extraction
- **Use Cases**: Backup notes, version tracking, audit trails, compliance

Example:
```python
create_archive(
    "documents/",
    "docs-backup.tc",
    comment="Q4 2025 Financial Records - Audited",
    creator="Devaansh Pathak"
)
```

### 🔐 File Attributes Preservation
Complete file restoration with security attributes:
- **Windows ACLs**: Access Control Lists preserved and restored (via pywin32)
- **Linux/macOS Extended Attributes**: xattrs support for Unix systems (via os.getxattr)
- **Platform Detection**: Automatic detection with graceful degradation
- **Cross-Platform Safe**: Archives created on Windows extract on Linux (attributes ignored gracefully)
- **Optional Dependency**: pywin32 not required for basic operation
- **JSON Serialization**: Base64 encoding for binary attribute data
- **Backward Compatible**: Old archives without attributes extract normally
- **Use Cases**: System backups, secure document archiving, permission-critical files

Example:
```python
# Create archive with attributes
create_archive(
    "secure_docs/",
    "backup.tc",
    preserve_attributes=True  # Captures ACLs/xattrs
)

# Extract with attributes
extract_archive(
    "backup.tc",
    "restored/",
    restore_attributes=True  # Restores ACLs/xattrs
)
```

---

## Migration from v1.1.0 to v1.2.0

**No breaking changes** - v1.2.0 is fully backward compatible with v1.1.0 and v1.0.0. All new features are optional parameters with sensible defaults.

### Updated API Signatures

```python
# v1.2.0 - New optional parameters (all backward compatible)
create_archive(
    source_path,
    archive_path,
    algo="LZW",
    password=None,
    per_file=True,
    recovery_percent=0.0,  # v1.1.0
    max_workers=None,  # v1.1.0
    exclude_patterns=None,  # v1.2.0 - NEW: File filtering
    max_file_size=None,  # v1.2.0 - NEW: Max file size filter
    min_file_size=None,  # v1.2.0 - NEW: Min file size filter
    incremental=False,  # v1.2.0 - NEW: Incremental backup mode
    base_archive=None,  # v1.2.0 - NEW: Base for incremental
    volume_size=None,  # v1.2.0 - NEW: Multi-volume split size
    preserve_attributes=False,  # v1.2.0 - NEW: Windows ACLs / Linux xattrs
    comment=None,  # v1.2.0 - NEW: Archive comment
    creator=None,  # v1.2.0 - NEW: Creator info
    progress_callback=None
)

extract_archive(
    archive_path,
    dest_path,
    password=None,
    restore_attributes=False,  # v1.2.0 - NEW: Restore file attributes
    progress_callback=None
)
```

### Upgrading Archives
- Existing TCAF v1 and v2 archives extract without modification
- New metadata fields optional—old archives lack them but remain valid
- Multi-volume archives require extraction from .001 file or base path (auto-detected)
- File attributes backward compatible—archives without attributes extract normally

---

## Recommended Usage

### Daily Backup Workflow (Incremental)
```python
from techcompressor.archiver import create_archive
from datetime import datetime

# Monday: Full backup
create_archive(
    "project/",
    f"backup-full-{datetime.now().strftime('%Y%m%d')}.tc",
    algo="DEFLATE",
    password="secure123",
    per_file=False,  # Solid mode
    persist_dict=True,
    recovery_percent=5.0,
    exclude_patterns=["*.tmp", ".git/", "__pycache__/"],
    comment="Weekly full backup"
)

# Tuesday-Sunday: Incremental backups
create_archive(
    "project/",
    f"backup-incr-{datetime.now().strftime('%Y%m%d')}.tc",
    incremental=True,
    base_archive="backup-full-20251027.tc",
    password="secure123",
    exclude_patterns=["*.tmp", ".git/"],
    comment="Daily incremental"
)
```

### Large Dataset Backup (Multi-Volume)
```python
create_archive(
    "/data/large_dataset/",
    "dataset-backup.tc",
    algo="DEFLATE",
    volume_size=4.7*1024*1024*1024,  # 4.7GB (DVD-size)
    recovery_percent=10.0,  # High redundancy
    max_workers=8,  # Parallel compression
    comment="Research dataset - 2025 Q4"
)
# Creates: dataset-backup.tc.001, .002, .003, ...
```

### Clean Source Code Archive
```python
create_archive(
    "my_project/",
    "project-release.tc",
    algo="DEFLATE",
    per_file=False,  # Solid compression
    persist_dict=True,
    exclude_patterns=[
        "*.pyc", "__pycache__/", ".git/", ".venv/",
        "node_modules/", "*.log", "*.tmp", ".DS_Store"
    ],
    max_file_size=10*1024*1024,  # Skip files > 10MB
    comment="v1.2.0 Release Source Code",
    creator="Devaansh Pathak"
)
```

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Quick compress with filtering
techcompressor compress input.txt output.tc --algo DEFLATE

# Create archive with file filtering and metadata
techcompressor create my_folder/ backup.tc \
  --algo DEFLATE \
  --password mypassword \
  --exclude "*.tmp" --exclude ".git/" \
  --comment "Monthly backup" \
  --recovery-percent 5

# Create multi-volume archive
techcompressor create large_data/ backup.tc \
  --algo DEFLATE \
  --volume-size 650MB

# Create incremental backup
techcompressor create project/ backup-incr.tc \
  --incremental \
  --base backup-full.tc

# Extract archive
techcompressor extract backup.tc restored/ --password mypassword

# Launch GUI
techcompressor --gui
```

---

## Performance Metrics (v1.2.0)

### Incremental Backup Performance
- **Daily Backup (1% changed)**: 50x faster (2min → 2.4sec)
- **Weekly Backup (10% changed)**: 10x faster (5min → 30sec)
- **Archive Size Reduction**: 90-99% smaller for typical daily deltas

### Enhanced Entropy Detection
- **Mixed Content Archives**: 20-30% faster creation (skips PNGs, JPGs, MP4s)
- **Already-Compressed Data**: Near-instant STORED mode selection
- **Archive Size Improvement**: 15-25% smaller (avoids expansion artifacts)

### Multi-Volume Archives
- **Streaming Overhead**: <2% performance impact
- **Volume Write Speed**: ~6 MB/s (DEFLATE, SSD)
- **Extraction Speed**: Same as single-file archives

---

## Developer Information

**TechCompressor** is developed by **Devaansh Pathak**  
GitHub: [https://github.com/DevaanshPathak](https://github.com/DevaanshPathak)  
Project: [https://github.com/DevaanshPathak/TechCompressor](https://github.com/DevaanshPathak/TechCompressor)

MIT License - Free for personal and commercial use

---

## Support & Contributing

- **Documentation**: Full API docs in README.md
- **Bug Reports**: [GitHub Issues](https://github.com/DevaanshPathak/TechCompressor/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/DevaanshPathak/TechCompressor/discussions)
- **Security**: See SECURITY.md for vulnerability reporting

---

## Previous Releases

### v1.1.0 (October 27, 2025)
techcompressor-gui
```

## Migration from v1.0.0 to v1.1.0

**API Changes**: None required - all v1.0.0 code works unchanged.

**New Features** (optional adoption):
```python
from techcompressor import compress, reset_solid_compression_state
from techcompressor.archiver import create_archive
from techcompressor.recovery import generate_recovery_records

# Use solid compression for better ratios
create_archive("source/", "output.tc", persist_dict=True)

# Add recovery records (5% redundancy)
create_archive("source/", "output.tc", recovery_percent=5.0)

# Parallel compression
create_archive("source/", "output.tc", max_workers=4)

# Reset state between archives
reset_solid_compression_state()
```

**Archive Format**: TCAF v2 is backward compatible with v1 archives. Old archives decompress correctly. New features (STORED mode, recovery records) are only used in newly created archives.

## Known Issues

1. **Compression Pattern Leakage**: Compressed data reveals patterns even with encryption enabled. This is an inherent limitation of compress-then-encrypt approaches and is not a bug. For maximum security, consider encrypt-then-compress workflows in security-critical applications.

2. **Intentional Key Derivation Delay**: PBKDF2 with 100,000 iterations introduces a ~50-100ms delay during encryption/decryption. This is a deliberate security feature to resist brute-force attacks and should not be "optimized away."

3. **No Password Recovery**: There is no password recovery mechanism. Data encrypted with a forgotten password is permanently irrecoverable. This is by design—we do not store password hints or backdoors.

4. **Tkinter GUI Platform Limitations**: The GUI requires a display server (X11, Wayland, or Windows). Headless servers should use the CLI interface.

## Recommended Usage

**Algorithm Selection**:
- **General purpose**: DEFLATE (best overall compression)
- **Speed-critical**: LZW (fastest, lowest memory)
- **Text/source code**: DEFLATE with single-stream mode + solid compression
- **Mixed content**: LZW with per-file mode
- **Media files**: STORED mode automatically used for incompressible data

**Archive Modes**:
- **Per-file mode** (`per_file=True`): Better for random access, selective extraction, mixed content
- **Single-stream mode** (`per_file=False`): Better compression ratio for similar files
- **Solid compression** (`persist_dict=True`): 10-30% better ratios, use with per_file=True

**Recovery Records**:
- Use 2-5% redundancy for normal archives
- Use 5-10% for critical backups or unreliable media
- Recovery records add minimal overhead but enable corruption repair

**Security**:
- Use strong passwords (12+ characters, mixed case, numbers, symbols)
- Store passwords in a password manager, never in code
- Verify password before long compression operations
- Consider the compression pattern leakage limitation for highly sensitive data

## System Requirements

- Python 3.10 or higher
- `cryptography>=41.0.0` (AES-GCM, PBKDF2)
- `tqdm>=4.65.0` (progress bars)
- `pytest>=7.0.0` (development/testing)

## Acknowledgments

TechCompressor is built on battle-tested cryptography libraries and implements well-established compression algorithms. Special thanks to the open-source community for cryptography, pytest, and Python ecosystem tools.

## Support & Contributing

- **Issues**: [GitHub Issues](https://github.com/DevaanshPathak/TechCompressor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DevaanshPathak/TechCompressor/discussions)
- **Security**: See SECURITY.md for vulnerability reporting
- **Contributing**: See README.md for development setup and guidelines

## License

MIT License - See LICENSE file for details.

---

**Full Changelog**: [CHANGELOG.md](CHANGELOG.md)  
**Download**: [GitHub Releases](https://github.com/DevaanshPathak/TechCompressor/releases/tag/v1.0.0)
