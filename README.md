# TechCompressor

**TechCompressor** is a modular, extensible, Python-based file and folder compression framework.

## 🎯 Purpose

TechCompressor aims to combine multiple classic and modern compression methods into a single intelligent compressor with optional encryption and GUI support. The project is designed with clean modular architecture, PEP 8 compliance, and maintainability in mind.

## 🚀 Future Roadmap

1. ✅ **Project setup & structure** *(Phase 1 - Complete)*
2. ✅ **LZW** algorithm implementation *(Phase 2 - Complete)*
3. ✅ **Huffman** coding implementation *(Phase 3 - Complete)*
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

## 📚 Phase 3 – Huffman Coding

### Overview

Phase 3 implements **Huffman coding**, a variable-length prefix coding algorithm that assigns shorter codes to more frequent bytes, achieving optimal compression for data with non-uniform frequency distributions.

### How Huffman Coding Works

**Compression:**
1. Build frequency table by counting occurrences of each byte
2. Construct binary tree using priority queue (min-heap):
   - Create leaf node for each unique byte with its frequency
   - Repeatedly combine two lowest-frequency nodes
   - Parent node has sum of children's frequencies
3. Generate prefix codes by traversing tree (left='0', right='1')
4. Encode input data using generated codes
5. Serialize tree structure for decompression
6. Pack bits into bytes with padding

**Decompression:**
1. Extract and deserialize Huffman tree from compressed data
2. Unpack compressed bits
3. Traverse tree using bits to decode original bytes
4. Reset to root after each decoded byte

### Special Cases

- **Single unique byte**: Tree is single node, code is "0"
- **Padding**: Last byte may have padding bits (stored in header)
- **Tree serialization**: Pre-order traversal with markers (0x01=leaf+byte, 0x00=internal)

### Output Format

Compressed files use the following format:
- **4 bytes**: Magic header `"TCH1"` (TechCompressor Huffman v1)
- **4 bytes**: Tree size (unsigned int, big-endian)
- **N bytes**: Serialized Huffman tree
- **1 byte**: Padding count (0-7 bits)
- **M bytes**: Huffman-encoded compressed data

### Usage Example

```python
from techcompressor.core import compress, decompress

# Compress data with Huffman
original = b"ABCABCABC"
compressed = compress(original, algo="HUFFMAN")

# Decompress data
restored = decompress(compressed, algo="HUFFMAN")

assert original == restored
```

### Algorithm Comparison

Both LZW and Huffman are now available:

```python
data = b"ABABABABAB" * 100

# LZW - good for repetitive patterns
lzw_result = compress(data, "LZW")

# Huffman - good for skewed frequency distributions
huffman_result = compress(data, "HUFFMAN")

# Both decompress correctly
assert decompress(lzw_result, "LZW") == data
assert decompress(huffman_result, "HUFFMAN") == data
```

### Testing

The test suite includes:
- ✅ Round-trip compression/decompression
- ✅ Empty and single-byte inputs
- ✅ Repetitive patterns (high compression ratio)
- ✅ Random binary data
- ✅ Large inputs
- ✅ Single unique byte (edge case)
- ✅ Error handling (corrupted headers, truncated data)
- ✅ Unicode text support
- ✅ Integration tests with LZW

Run Huffman tests: `pytest tests/test_huffman.py`  
Run integration tests: `pytest tests/test_integration.py`  
Run all tests: `pytest`

### Performance Characteristics

| Data Type | Huffman Compression | Notes |
|-----------|---------------------|-------|
| Highly repetitive (single byte) | ~12-15% | Excellent for uniform data |
| Text with skewed distribution | ~40-60% | Good compression |
| Random binary data | >100% | Expansion (expected) |
| English text | ~50-70% | Moderate compression |

**Next Phase**: Phase 4 will implement Arithmetic coding, which can achieve better compression than Huffman for certain data patterns.

## 📋 Requirements

- Python >= 3.10
- See `requirements.txt` for dependencies

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
