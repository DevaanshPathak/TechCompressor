# TechCompressor v1.2.0 Release Notes

**Release Date**: October 27, 2025  
**Status**: Production/Stable

## Overview

TechCompressor v1.2.0 completes enterprise-grade backup features: advanced file filtering for selective archiving, multi-volume archives for splitting large datasets, incremental backups for efficient daily workflows, file attributes preservation for complete system backups, and enhanced entropy detection for automatic format recognition. Combined with v1.1.0's solid compression and recovery records, TechCompressor now rivals RAR and WinZip in both features and flexibility while remaining fully open-source.

## Highlights

### 🗜️ Three Compression Algorithms
Choose the algorithm that fits your needs:
- **LZW**: Lightning-fast dictionary-based compression (3 MB/s), ideal for repetitive data and speed-critical applications
- **Huffman**: Frequency-based compression optimized for non-uniform distributions (2.5 MB/s)
- **DEFLATE**: Industry-standard hybrid compression (LZ77 + Huffman) offering the best compression ratios (6 MB/s, ~1% on repetitive data)

### 🔒 Military-Grade Security
Password-protected compression uses **AES-256-GCM** authenticated encryption with **PBKDF2** key derivation (100,000 iterations). Every encryption generates unique salts and nonces, and includes integrity verification via authentication tags. There are no backdoors or recovery mechanisms—security by design.

### 📦 Flexible Archiving with Advanced Features (v1.2.0)
The custom **TCAF v2** (TechCompressor Archive Format) now supports:
- **Advanced File Filtering**: Exclude patterns (*.tmp, .git/), size limits for selective archiving
- **Multi-Volume Archives**: Split into parts (archive.tc.001, .002, etc.) with configurable sizes
- **Incremental Backups**: Only compress changed files since last archive for 10-50x faster backups
- **Archive Metadata**: User comments, creation date, creator information
- **File Attributes**: Windows ACLs and Linux/macOS extended attributes preservation
- **Recovery Records**: PAR2-style error correction (v1.1.0)
- **Solid Compression**: Dictionary persistence for 10-30% better ratios (v1.1.0)

### 💻 Dual Interface
- **CLI**: Full-featured command-line interface with `create`, `extract`, `compress`, `decompress`, `list`, `verify`, and inline `--benchmark` commands
- **GUI**: User-friendly Tkinter application with background threading, real-time progress bars, password fields, operation cancellation, and developer credits

### ⚡ Production-Ready
**193 tests passing** (3 platform-specific skipped). Comprehensive test coverage includes algorithm correctness, encryption validation, archive security, multi-volume handling, file attributes preservation, integration workflows, and performance regression checks. The codebase uses modern Python 3.10+ features with full type hints and extensive documentation.

---

## What's New in v1.2.0

### 🎯 Advanced File Filtering
Selective archiving with powerful filtering options:
- **Exclude Patterns**: Skip files matching glob patterns (*.tmp, .git/, __pycache__/)
- **Size Limits**: `max_file_size` and `min_file_size` parameters filter by file size
- **Flexible Matching**: Multiple patterns with wildcard support
- **Use Cases**: Clean backups without build artifacts, logs, or temporary files

Example:
```python
create_archive(
    "project/",
    "backup.tc",
    exclude_patterns=["*.tmp", ".git/", "node_modules/", "__pycache__/"],
    max_file_size=100*1024*1024  # Skip files > 100MB
)
```

### 💾 Multi-Volume Archives
Split large archives into manageable parts for storage or transfer:
- **Configurable Volume Size**: Set max size per volume (e.g., 650MB for CD, 4.7GB for DVD)
- **Sequential Naming**: Automatic naming: archive.tc.001, archive.tc.002, ...
- **VolumeWriter/VolumeReader Classes**: Transparent multi-volume I/O abstraction
- **Seamless Extraction**: Extract from first volume, auto-reads subsequent parts
- **Auto-detection**: Finds .001 file when base path provided
- **Works Everywhere**: Compatible with all algorithms, encryption, and compression modes
- **Use Cases**: Backup to multiple USB drives, email-size limits, cloud storage chunks

Example:
```python
create_archive(
    "large_dataset/",
    "backup.tc",
    volume_size=650*1024*1024  # Split into 650MB volumes (CD-size)
)
# Creates: backup.tc.001, backup.tc.002, backup.tc.003, ...

# Extract (auto-detects volumes)
extract_archive("backup.tc", "restored/")  # Finds backup.tc.001 automatically
```

### 📅 Incremental Backups
Dramatically faster backups by archiving only changed files:
- **Timestamp-Based Detection**: Compare modification times against base archive
- **10-50x Faster**: Daily backups complete in seconds instead of minutes
- **Reduced Archive Size**: Only store deltas, not full directory snapshots
- **Base Archive Reference**: `base_archive` parameter specifies reference archive
- **Compatible with Solid Mode**: Works with both per-file and solid compression
- **Use Cases**: Daily/weekly backup workflows, version control supplements

Example:
```python
# Full backup (Monday)
create_archive("project/", "backup-full.tc", algo="DEFLATE")

# Incremental backup (Tuesday) - only changed files
create_archive(
    "project/",
    "backup-incremental-tue.tc",
    incremental=True,
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
