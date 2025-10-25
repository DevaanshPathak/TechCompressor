# TechCompressor

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DevaanshPathak/TechCompressor)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-137%20passed-brightgreen.svg)](#testing)

**TechCompressor** is a production-ready, modular Python compression framework featuring multiple algorithms, military-grade encryption, and both CLI and GUI interfaces. Built for performance, security, and ease of use.

---

## ✨ Features

### 🗜️ Multiple Compression Algorithms
- **LZW (Lempel-Ziv-Welch)**: Fast dictionary-based compression, ideal for repetitive data
- **Huffman Coding**: Optimal for data with non-uniform frequency distributions
- **DEFLATE**: Industry-standard hybrid (LZ77 + Huffman), best overall compression

### 🔒 Military-Grade Encryption
- **AES-256-GCM**: Authenticated encryption with integrity verification
- **PBKDF2**: 100,000 iterations for brute-force resistance
- Password-protected compression with seamless integration
- No backdoors or recovery mechanisms

### 📦 Archive Management
- **TCAF Format**: Custom TechCompressor Archive Format
- Compress entire folders with metadata preservation
- Supports both per-file and single-stream compression
- Path traversal protection and security validation
- Preserves timestamps, permissions, and relative paths

### 💻 Dual Interface
- **CLI**: Full-featured command-line with benchmarking and verification
- **GUI**: User-friendly Tkinter interface with background threading
- **Python API**: Direct module imports for automation scripts

### ⚡ Performance Optimized
- Encryption overhead < 10% for typical use cases
- Streaming support for large files (>16MB)
- Optimized I/O operations and buffer handling
- Multi-threaded GUI operations (non-blocking)

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/DevaanshPathak/TechCompressor.git
cd TechCompressor

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Launch GUI
python -m techcompressor.cli --gui
```

### Basic Usage

**Command Line:**
```bash
# Compress a file
techcompressor compress input.txt output.tc --algo DEFLATE

# Create encrypted archive
techcompressor create folder/ archive.tc --algo DEFLATE --password mypassword

# Extract archive
techcompressor extract archive.tc output/ --password mypassword

# Verify archive integrity
techcompressor verify archive.tc

# Run performance benchmark
techcompressor --benchmark
```

**Python API:**
```python
from techcompressor.core import compress, decompress
from techcompressor.archiver import create_archive, extract_archive

# Simple compression
data = b"Hello, World!"
compressed = compress(data, algo="DEFLATE")
original = decompress(compressed, algo="DEFLATE")

# With encryption
compressed = compress(data, algo="DEFLATE", password="secret")
original = decompress(compressed, algo="DEFLATE", password="secret")

# Archive folder
create_archive(
    source_path="my_folder/",
    archive_path="backup.tc",
    algo="DEFLATE",
    password="secret",
    per_file=False  # Single-stream for best compression
)

# Extract archive
extract_archive("backup.tc", "restored/", password="secret")
```

**GUI Application:**
```bash
# Launch GUI
python -m techcompressor.gui

# Or via CLI flag
techcompressor --gui
```

---

## 📊 Performance & Benchmarks

### Algorithm Comparison

| Algorithm | Best For | Speed | Compression | Memory | Notes |
|-----------|----------|-------|-------------|--------|-------|
| **DEFLATE** | General purpose | ★★★★☆ | ★★★★★ | Medium | Recommended default |
| **LZW** | Repetitive data | ★★★★★ | ★★★☆☆ | Low | Fastest compression |
| **Huffman** | Frequency-skewed | ★★★★☆ | ★★★☆☆ | Low | Good for text |

### Typical Performance
*Tested on 10KB repetitive text data:*

```
Algorithm    Time         Ratio      Speed
--------------------------------------------------
DEFLATE      2.33 ms      1.0%       6.14 MB/s    ⭐ Best
LZW          4.72 ms      8.9%       3.03 MB/s    ⭐ Fastest
HUFFMAN      5.82 ms     43.7%       2.46 MB/s
```

### Recommendations by File Type

| File Type | Algorithm | Archive Mode | Reason |
|-----------|-----------|--------------|--------|
| **Text/Source Code** | DEFLATE | Single-stream | Best compression for similar content |
| **Office Documents** | DEFLATE | Per-file | Mixed content with metadata |
| **Binary/Executables** | LZW | Per-file | Fast, handles binary well |
| **Media Files** | LZW | Per-file | Already compressed, skip re-compression |
| **Large Files (>100MB)** | DEFLATE | Single-stream | Streaming support, best ratio |

### Run Your Own Benchmarks

```bash
# Full benchmark suite
python bench.py

# Quick performance check
python bench.py --quick

# CLI benchmark
techcompressor --benchmark
```

---

## 🔐 Security Features

### Encryption Details
- **Algorithm**: AES-256-GCM (Galois/Counter Mode)
- **Key Derivation**: PBKDF2-HMAC-SHA256
- **Iterations**: 100,000 (adjustable, default for security)
- **Key Size**: 256 bits
- **Salt**: 16 bytes (random per encryption)
- **Nonce**: 12 bytes (random per encryption)
- **Authentication Tag**: 16 bytes

### Security Best Practices
✅ Use strong, unique passwords (12+ characters)  
✅ Store passwords in a password manager  
✅ No password = permanent data loss (no recovery)  
✅ Encrypted archives include integrity verification  
✅ Path traversal protection prevents malicious archives  
✅ Symlinks rejected to avoid infinite loops  

### Security Warnings
⚠️ **Password Loss = Data Loss**: No backdoors or recovery mechanisms  
⚠️ **Compression Leaks Info**: Data patterns visible despite encryption  
⚠️ **PBKDF2 Intentionally Slow**: ~50-100ms for key derivation (security feature)  

---

## 📖 Documentation

### Command-Line Interface

**Global Options:**
```bash
techcompressor --version           # Show version
techcompressor --benchmark         # Run performance test
techcompressor --gui               # Launch GUI
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

**Examples:**
```bash
# Compress with DEFLATE
techcompressor compress file.txt file.tc --algo DEFLATE

# Create encrypted archive (single-stream)
techcompressor create project/ backup.tc --algo DEFLATE --password "secure123"

# Extract with password
techcompressor extract backup.tc restored/ --password "secure123"

# Verify archive
techcompressor verify backup.tc
✅ Valid TCAF archive
✅ Contains 42 file(s)
   Original: 1,234,567 bytes
   Compressed: 345,678 bytes (28.0%)
✅ Archive verification passed!
```

### Python API

**Core Compression:**
```python
from techcompressor.core import compress, decompress

# Basic compression
compressed = compress(data, algo="LZW")
original = decompress(compressed, algo="LZW")

# With password
compressed = compress(data, algo="DEFLATE", password="secret")
original = decompress(compressed, algo="DEFLATE", password="secret")

# Available algorithms: "LZW", "HUFFMAN", "DEFLATE"
```

**Archiver:**
```python
from techcompressor.archiver import create_archive, extract_archive, list_contents

# Create archive
create_archive(
    source_path="folder/",
    archive_path="backup.tc",
    algo="DEFLATE",           # Compression algorithm
    password="secret",        # Optional encryption
    per_file=False,           # False = single-stream (better compression)
    progress_callback=None    # Optional callback(percent, message)
)

# Extract archive
extract_archive(
    archive_path="backup.tc",
    dest_path="output/",
    password="secret",
    progress_callback=None
)

# List contents (no extraction)
contents = list_contents("backup.tc")
for entry in contents:
    print(f"{entry['name']}: {entry['size']} bytes")
```

**GUI Application:**
```python
from techcompressor.gui import TechCompressorApp

# Launch GUI programmatically
app = TechCompressorApp()
app.run()
```

### GUI Features

**Compress Tab:**
- Browse file or folder to compress
- Choose output archive location
- Select algorithm (LZW, Huffman, DEFLATE)
- Toggle per-file archive mode
- Enter password with show/hide
- Real-time progress bar and log

**Extract Tab:**
- Browse archive to extract
- Choose destination folder
- Enter decryption password
- Progress tracking with file list
- Cancel support

**Settings Tab:**
- Compression level adjustment
- Default archive mode selection
- Help text and tooltips

**Logs Tab:**
- View all application logs
- Auto-scroll to latest
- Clear logs button

**Keyboard Shortcuts:**
- `Ctrl+Shift+C`: Quick compress
- `Ctrl+Shift+E`: Quick extract

---

## 🧪 Testing

### Test Suite

**Coverage:**
- ✅ 137 tests passing (1 skipped on some systems)
- ✅ Core compression algorithms (LZW, Huffman, DEFLATE)
- ✅ Encryption and key derivation
- ✅ Archive creation and extraction
- ✅ GUI components (headless mode)
- ✅ Performance and timing
- ✅ Integration tests
- ✅ Edge cases and error handling

**Run Tests:**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_lzw.py -v

# With coverage
pytest --cov=techcompressor --cov-report=html

# Performance tests only
pytest tests/test_perf_sanity.py -v

# Quick test
pytest -q
```

**Test Categories:**
- `test_lzw.py`: LZW compression (16 tests)
- `test_huffman.py`: Huffman coding (20 tests)
- `test_deflate.py`: DEFLATE compression (21 tests)
- `test_crypto.py`: Encryption and security (15 tests)
- `test_archiver.py`: Archive management (17 tests)
- `test_integration.py`: Cross-algorithm tests (24 tests)
- `test_gui_basic.py`: GUI components (11 tests)
- `test_perf_sanity.py`: Performance checks (6 tests)

---

## ❓ FAQ

### General Questions

**Q: Which algorithm should I use?**
- **General purpose**: DEFLATE (best compression ratio)
- **Speed priority**: LZW (fastest compression)
- **Text/code projects**: DEFLATE with single-stream
- **Binary/media files**: LZW with per-file mode

**Q: What's the difference between per-file and single-stream?**
- **Per-file**: Each file compressed independently (good for random access)
- **Single-stream**: All files concatenated then compressed (better compression)
- Use per-file for mixed content, single-stream for similar files

**Q: Can I use this in production?**
- Yes! Version 1.0.0 is production-ready
- Extensively tested (137 tests)
- Used for personal and commercial projects
- MIT licensed (see LICENSE file)

### Security Questions

**Q: Why is encryption slow?**
- PBKDF2 uses 100,000 iterations for security
- First encryption takes ~50-100ms for key derivation
- This protects against brute-force attacks
- Subsequent operations are faster

**Q: How do I recover a lost password?**
- **You cannot**. This is by design for security
- No backdoors or recovery mechanisms
- Always store passwords securely
- Consider keeping unencrypted backups of critical data

**Q: Is TechCompressor secure?**
- Uses industry-standard AES-256-GCM
- PBKDF2 with 100,000 iterations
- Authenticated encryption prevents tampering
- However, compression can leak some data patterns

### Technical Questions

**Q: Why does the GUI freeze?**
- It shouldn't! All operations run in background threads
- If frozen, it's a bug - please report with reproduction steps
- Check Logs tab for error messages

**Q: Can I cancel a long operation?**
- **GUI**: Click "Cancel" button (graceful shutdown in 1-2 seconds)
- **CLI**: Press `Ctrl+C` (immediate termination)
- Partial files may remain (safe to delete)

**Q: How do I install Tkinter?**
- **Windows/macOS**: Included with Python by default
- **Linux (Debian/Ubuntu)**: `sudo apt-get install python3-tk`
- **Linux (Fedora)**: `sudo dnf install python3-tkinter`

**Q: What file formats are supported?**
- **Input**: Any file type (binary safe)
- **Output**: `.tc` (TechCompressor format)
- Archives use TCAF (TechCompressor Archive Format)
- Compressed files have format-specific headers

---

## 🛠️ Development

### Project Structure

```
TechCompressor/
├── techcompressor/          # Main package
│   ├── __init__.py         # Version and exports
│   ├── core.py             # Compression algorithms
│   ├── crypto.py           # Encryption (AES-256-GCM)
│   ├── archiver.py         # Archive management (TCAF)
│   ├── cli.py              # Command-line interface
│   ├── gui.py              # Tkinter GUI
│   └── utils.py            # Logging and utilities
├── tests/                   # Test suite (137 tests)
├── bench.py                 # Benchmark tool
├── requirements.txt         # Dependencies
├── pyproject.toml          # Package configuration
├── LICENSE                  # MIT License
└── README.md               # This file
```

### Requirements

- **Python**: >= 3.10
- **Dependencies**:
  - `cryptography>=41.0.0` - AES encryption
  - `tqdm>=4.65.0` - Progress bars
- **Optional**: Tkinter (GUI, included with most Python installations)

### Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

### Building from Source

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Run benchmarks
python bench.py

# Build wheel
python -m build
```

---

## 📋 Roadmap

### Version 1.0.0 (Current) ✅
- ✅ LZW, Huffman, DEFLATE algorithms
- ✅ AES-256-GCM encryption
- ✅ TCAF archive format
- ✅ CLI and GUI interfaces
- ✅ Comprehensive test suite
- ✅ Performance benchmarks
- ✅ Cross-platform support

### Future Enhancements 🔮
- Arithmetic coding algorithm
- Brotli/Zstandard integration
- Parallel compression for multi-core
- Cloud storage integration
- Python package on PyPI
- Standalone executables (PyInstaller)

---

## 📄 License

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

## 🙏 Acknowledgments

- **LZW Algorithm**: Terry Welch (1984)
- **Huffman Coding**: David A. Huffman (1952)
- **DEFLATE Format**: Phil Katz, RFC 1951 (1996)
- **Cryptography**: Python `cryptography` library
- **Testing**: pytest framework
- **GUI**: Python Tkinter

---

## 📞 Contact & Support

- **GitHub**: [DevaanshPathak/TechCompressor](https://github.com/DevaanshPathak/TechCompressor)
- **Issues**: [Report bugs or request features](https://github.com/DevaanshPathak/TechCompressor/issues)
- **License**: MIT (see LICENSE file)

---

<div align="center">

**TechCompressor 1.0.0** - Built with ❤️ for efficient, secure compression

[![Star on GitHub](https://img.shields.io/github/stars/DevaanshPathak/TechCompressor?style=social)](https://github.com/DevaanshPathak/TechCompressor)

</div>
