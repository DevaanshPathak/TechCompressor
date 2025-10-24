# TechCompressor

**TechCompressor** is a modular, extensible, Python-based file and folder compression framework.

## 🎯 Purpose

TechCompressor aims to combine multiple classic and modern compression methods into a single intelligent compressor with optional encryption and GUI support. The project is designed with clean modular architecture, PEP 8 compliance, and maintainability in mind.

## 🚀 Future Roadmap

1. ✅ **Project setup & structure** *(Phase 1 - Complete)*
2. ✅ **LZW** algorithm implementation *(Phase 2 - Complete)*
3. **Huffman** coding implementation
4. **Arithmetic** coding implementation
5. **DEFLATE** integration (LZ77 + Huffman)
6. **AES-based password protection** for compressed data
7. **Folder & multi-file archiving** system
8. **Tkinter GUI** for user-friendly compression/decompression
9. **Command-line interface (CLI)** with rich argument parsing
10. **Optimization, profiling, and finalization**

## 📦 Installation

To set up the development environment:

```bash
pip install -r requirements.txt
```

## 🧪 Running Tests

To run the test suite:

```bash
pytest
```

To run only LZW tests:

```bash
pytest tests/test_lzw.py -v
```

## 📚 Phase 2 – LZW Compression

### Overview

Phase 2 implements the **Lempel-Ziv-Welch (LZW)** compression algorithm, a dictionary-based lossless compression method that builds a code table during compression.

### How LZW Works

**Compression:**
1. Initialize dictionary with all single-byte values (0-255)
2. Read input byte by byte, finding the longest matching sequence in the dictionary
3. Output the code for the matched sequence
4. Add the new sequence (match + next byte) to the dictionary
5. Dictionary grows to 4096 entries, then resets to prevent memory overflow

**Decompression:**
1. Initialize the same dictionary with single-byte values
2. Read codes from compressed data
3. Look up each code in the dictionary to reconstruct original data
4. Rebuild dictionary using the same logic as compression

### Output Format

Compressed files use the following format:
- **4 bytes**: Magic header `"TCZ1"` (TechCompressor v1)
- **2 bytes**: Maximum dictionary size (4096)
- **N bytes**: LZW-compressed codewords (2 bytes per code, big-endian)

### Usage Example

```python
from techcompressor.core import compress, decompress

# Compress data
original = b"TOBEORNOTTOBEORTOBEORNOT"
compressed = compress(original, algo="LZW")

# Decompress data
restored = decompress(compressed, algo="LZW")

assert original == restored
```

### Testing

The test suite includes:
- ✅ Round-trip compression/decompression
- ✅ Empty and single-byte inputs
- ✅ Repetitive patterns (high compression ratio)
- ✅ Random binary data
- ✅ Large inputs (dictionary reset validation)
- ✅ Error handling (corrupted headers, truncated data)
- ✅ Unicode text support
- ✅ All byte value coverage

Run with: `pytest tests/test_lzw.py`

## 📋 Requirements

- Python >= 3.10
- See `requirements.txt` for dependencies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
