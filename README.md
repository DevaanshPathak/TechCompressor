# TechCompressor

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/DevaanshPathak/TechCompressor)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-228%20passed-brightgreen.svg)](#testing)

**TechCompressor** is a production-ready, modular Python compression framework featuring five compression algorithms (LZW, Huffman, DEFLATE, Zstandard, Brotli), military-grade encryption, a modern Terminal User Interface (TUI), solid compression with dictionary persistence, PAR2-style recovery records, advanced file filtering, multi-volume archives, incremental backups, and CLI/GUI/TUI interfaces.

---

## Features

### Multiple Compression Algorithms
- **LZW (Lempel-Ziv-Welch)**: Fast dictionary-based compression, ideal for repetitive data
- **Huffman Coding**: Optimal for data with non-uniform frequency distributions
- **DEFLATE**: Industry-standard hybrid (LZ77 + Huffman), best overall compression
- **Zstandard (v2.0.0)**: Ultra-fast compression (400-600 MB/s) with excellent ratios, developed by Meta
- **Brotli (v2.0.0)**: Web-optimized compression, 20-30% better than DEFLATE for text content
- **STORED**: Automatic detection and direct storage of incompressible files

### Advanced Archive Features
- **Solid Compression**: Dictionary persistence across files for 10-30% better ratios
- **Recovery Records**: PAR2-style Reed-Solomon error correction (0-10% redundancy)
- **Multi-threaded**: Parallel per-file compression for 2-4x faster archives
- **Smart AUTO mode**: Entropy detection and algorithm selection heuristics
- **Advanced File Filtering**: Exclude patterns (*.tmp, .git/), size limits, date ranges
- **Multi-Volume Archives**: Split large archives into parts (archive.tc.part1, .part2, etc.)
- **Incremental Backups**: Only compress changed files since last archive
- **Enhanced Entropy Detection**: Auto-skip compression on JPG, PNG, MP4, ZIP, etc.

### Modern Terminal User Interface (v2.0.0)
- **Textual TUI**: Rich, interactive terminal interface with mouse support
- **File Browser**: Navigate and select files/folders visually
- **Archive Inspector**: View archive contents without extraction
- **Real-time Progress**: Live progress bars and operation status
- **Keyboard Shortcuts**: Efficient navigation and operations
- Launch with: `techcompressor --tui` or `techcompressor-tui`

### Military-Grade Encryption
- **AES-256-GCM**: Authenticated encryption with integrity verification
- **PBKDF2**: 100,000 iterations for brute-force resistance
- Password-protected compression with seamless integration
- No backdoors or recovery mechanisms

### Archive Management
- **TCAF v2 Format**: Custom TechCompressor Archive Format with backward compatibility
- Compress entire folders with metadata preservation
- Supports both per-file and single-stream compression
- Path traversal protection and security validation
- Preserves timestamps, permissions, and relative paths
- Recovery records for archive repair and corruption detection
- Archive metadata: User comments, creation date, creator information
- File attributes: Windows ACLs and Linux extended attributes preservation

### Triple Interface
- **CLI**: Full-featured command-line with benchmarking and verification
- **GUI**: User-friendly Tkinter interface with background threading
- **TUI (v2.0.0)**: Modern Textual-based terminal interface with rich widgets
- **Python API**: Direct module imports for automation scripts

### Performance Optimized
- Encryption overhead less than 10% for typical use cases
- Streaming support for large files (>16MB)
- Optimized I/O operations and buffer handling
- Multi-threaded GUI/TUI operations (non-blocking)
- **Zstandard**: 400-600 MB/s compression speed
- **Brotli**: 20-30% better ratios on web content

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/DevaanshPathak/TechCompressor.git
cd TechCompressor

# Install dependencies
pip install -r requirements.txt

# Install the package (enables CLI commands)
pip install -e .

# Run tests
pytest

# Launch GUI
techcompressor --gui

# Launch TUI (v2.0.0)
techcompressor --tui
```

### Basic Usage

**Command Line:**
```bash
# Compress a file with Zstandard (fastest)
techcompressor compress input.txt output.tc --algo ZSTD

# Compress with Brotli (best for web content)
techcompressor compress input.html output.tc --algo BROTLI

# Create encrypted archive with DEFLATE
techcompressor create folder/ archive.tc --algo DEFLATE --password mypassword

# Extract archive
techcompressor extract archive.tc output/ --password mypassword

# Verify archive integrity
techcompressor verify archive.tc

# Run performance benchmark
techcompressor --benchmark

# Launch TUI
techcompressor --tui
```

**Python API:**
```python
from techcompressor.core import compress, decompress
from techcompressor.archiver import create_archive, extract_archive

# Simple compression with different algorithms
data = b"Hello, World!"
compressed_zstd = compress(data, algo="ZSTD")      # Fastest
compressed_brotli = compress(data, algo="BROTLI")  # Best for text
compressed_deflate = compress(data, algo="DEFLATE")  # Industry standard

# Decompress
original = decompress(compressed_zstd, algo="ZSTD")

# With encryption
compressed = compress(data, algo="ZSTD", password="secret")
original = decompress(compressed, algo="ZSTD", password="secret")

# Archive folder with all features
create_archive(
    source_path="my_folder/",
    archive_path="backup.tc",
    algo="ZSTD",
    password="secret",
    per_file=False,
    recovery_percent=5.0,
    max_workers=4,
    exclude_patterns=["*.tmp", ".git/", "__pycache__/"],
    volume_size=650*1024*1024,
    preserve_attributes=True,
    comment="Monthly backup",
    creator="Backup Script v2.0"
)

# Extract archive
extract_archive("backup.tc", "restored/", password="secret", restore_attributes=True)
```

**TUI Application (v2.0.0):**
```bash
# Launch the modern terminal user interface
techcompressor --tui

# Or via direct command
techcompressor-tui
```

---

## Comparison with Other Archivers

### Feature Comparison

| Feature | TechCompressor | ZIP | RAR | 7-Zip |
|---------|----------------|-----|-----|-------|
| Open Source | Yes (MIT) | Yes | No | Yes (LGPL) |
| Algorithms | 5 + AUTO | 1 | 1 | 3 |
| Solid Compression | Yes | No | Yes | Yes |
| Recovery Records | Yes | No | Yes | No |
| AES-256 Encryption | Yes (GCM) | Yes (weak) | Yes | Yes |
| Multi-Volume | Yes | Yes | Yes | Yes |
| Incremental Backup | Yes | No | Limited | No |
| File Attributes | Yes | Limited | Yes | Limited |
| Python API | Native | Via zipfile | No | Via py7zr |
| Terminal UI | Yes | No | No | No |
| GUI Included | Yes | No | Yes | Yes |

### Speed Comparison

| Algorithm | Compression Speed | Decompression Speed | Ratio |
|-----------|-------------------|---------------------|-------|
| Zstandard | 400-600 MB/s | 800+ MB/s | Excellent |
| Brotli | 20-50 MB/s | 300+ MB/s | Best for text |
| DEFLATE | 6 MB/s | 200+ MB/s | Excellent |
| LZW | 3 MB/s | 50+ MB/s | Good |
| Huffman | 2.5 MB/s | 50+ MB/s | Good |

### When to Use TechCompressor

**Best For:**
- Python applications needing compression
- Automated backup scripts
- Web content compression (use Brotli)
- High-speed compression needs (use Zstandard)
- Development and testing compression algorithms
- Scenarios requiring strong encryption
- Mixed content archives

**Not Ideal For:**
- Maximum compression ratio (use 7-Zip LZMA2)
- Universal format compatibility (use ZIP)
- Extremely large files over 10GB

---

## Algorithm Performance

| Algorithm | Best For | Speed | Ratio | Memory |
|-----------|----------|-------|-------|--------|
| Zstandard | Speed + ratio | Excellent | Excellent | Medium |
| Brotli | Web/text content | Good | Excellent | Medium |
| DEFLATE | General purpose | Good | Excellent | Medium |
| LZW | Repetitive data | Excellent | Good | Low |
| Huffman | Frequency-skewed | Good | Good | Low |

### Recommendations by File Type

| File Type | Recommended Algorithm | Archive Mode |
|-----------|----------------------|--------------|
| Text/Source Code | Brotli or DEFLATE | Single-stream |
| HTML/JSON/CSS | Brotli | Single-stream |
| Office Documents | DEFLATE | Per-file |
| Binary/Executables | Zstandard or LZW | Per-file |
| Media Files | STORED (AUTO mode) | Per-file |
| Large Files (>100MB) | Zstandard | Single-stream |

---

## Security Features

### Encryption Details
- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Derivation**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000 (adjustable)
- **Key Size**: 256 bits
- **Salt**: 16 bytes (random per encryption)
- **Nonce**: 12 bytes (random per encryption)
- **Authentication Tag**: 16 bytes

### Security Best Practices
- Use strong, unique passwords (12+ characters)
- Store passwords in a password manager
- No password recovery - keep backups of critical data
- Encrypted archives include integrity verification
- Path traversal protection prevents malicious archives

### Security Warnings
- **Password Loss = Data Loss**: No backdoors or recovery mechanisms
- **Compression Leaks Info**: Data patterns visible despite encryption
- **PBKDF2 Intentionally Slow**: ~50-100ms for key derivation (security feature)

---

## Documentation

### Command-Line Interface

**Global Options:**
```bash
techcompressor --version           # Show version
techcompressor --benchmark         # Run performance test
techcompressor --gui               # Launch GUI
techcompressor --tui               # Launch TUI
techcompressor --help              # Show help
```

**Compression Commands:**
```bash
# Compress single file
techcompressor compress INPUT OUTPUT [--algo ALGO] [--password PASS]

# Decompress single file
techcompressor decompress INPUT OUTPUT [--algo ALGO] [--password PASS]
```

**Archive Commands:**
```bash
# Create archive
techcompressor create SOURCE ARCHIVE [--algo ALGO] [--password PASS] [--per-file]

# Extract archive
techcompressor extract ARCHIVE DEST [--password PASS]

# List contents
techcompressor list ARCHIVE

# Verify integrity
techcompressor verify ARCHIVE
```

### Python API

**Core Compression:**
```python
from techcompressor.core import compress, decompress

# Basic compression
compressed = compress(data, algo="ZSTD")
original = decompress(compressed, algo="ZSTD")

# With password
compressed = compress(data, algo="DEFLATE", password="secret")
original = decompress(compressed, algo="DEFLATE", password="secret")

# Available algorithms: "LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI", "AUTO"
```

**Archiver:**
```python
from techcompressor.archiver import create_archive, extract_archive, list_contents

# Create archive
create_archive(
    source_path="folder/",
    archive_path="backup.tc",
    algo="ZSTD",
    password="secret",
    per_file=False,
    recovery_percent=5.0,
    max_workers=4,
    exclude_patterns=["*.tmp"],
    volume_size=650*1024*1024,
    preserve_attributes=True,
    comment="Backup description",
    creator="Script name"
)

# Extract archive
extract_archive("backup.tc", "output/", password="secret", restore_attributes=True)

# List contents
contents = list_contents("backup.tc")
```

---

## Testing

### Test Suite

**Coverage:**
- 228 tests passing (4 skipped on some platforms)
- Core compression algorithms (LZW, Huffman, DEFLATE, Zstandard, Brotli)
- Encryption and key derivation
- Archive creation and extraction
- Multi-volume archives
- File attributes preservation
- TUI components
- Performance validation
- Integration tests

**Run Tests:**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_lzw.py -v

# With coverage
pytest --cov=techcompressor --cov-report=html

# Quick test
pytest -q
```

---

## Development

### Project Structure

```
TechCompressor/
|-- techcompressor/          # Main package
|   |-- __init__.py          # Version and exports
|   |-- core.py              # Compression algorithms
|   |-- crypto.py            # Encryption (AES-256-GCM)
|   |-- archiver.py          # Archive management (TCAF)
|   |-- cli.py               # Command-line interface
|   |-- gui.py               # Tkinter GUI
|   |-- tui.py               # Textual TUI
|   |-- recovery.py          # Recovery records
|   +-- utils.py             # Logging and utilities
|-- tests/                   # Test suite (228 tests)
|-- bench.py                 # Benchmark tool
|-- requirements.txt         # Dependencies
|-- pyproject.toml           # Package configuration
|-- LICENSE                  # MIT License
+-- README.md                # This file
```

### Requirements

- **Python**: 3.10 or higher
- **Dependencies**:
  - cryptography>=41.0.0 - AES encryption
  - tqdm>=4.65.0 - Progress bars
  - textual>=0.75.0 - TUI framework
  - zstandard>=0.22.0 - Zstandard compression
  - brotli>=1.1.0 - Brotli compression

### Building from Source

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Run benchmarks
python bench.py

# Build executable
.\build_release.ps1
```

---

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2025 Devaansh Pathak

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Acknowledgments

- **LZW Algorithm**: Terry Welch (1984)
- **Huffman Coding**: David A. Huffman (1952)
- **DEFLATE Format**: Phil Katz, RFC 1951 (1996)
- **Zstandard**: Yann Collet, Meta/Facebook
- **Brotli**: Google
- **Textual**: Textualize team
- **Cryptography**: Python cryptography library

---

## Contact and Support

- **GitHub**: [DevaanshPathak/TechCompressor](https://github.com/DevaanshPathak/TechCompressor)
- **Issues**: [Report bugs or request features](https://github.com/DevaanshPathak/TechCompressor/issues)
- **Developer**: Devaansh Pathak

---

**TechCompressor v2.0.0** - Efficient, secure compression for Python

[![Star on GitHub](https://img.shields.io/github/stars/DevaanshPathak/TechCompressor?style=social)](https://github.com/DevaanshPathak/TechCompressor)
