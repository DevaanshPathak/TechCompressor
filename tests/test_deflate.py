"""Comprehensive test suite for DEFLATE compression implementation."""
import os
import pytest
from techcompressor.core import compress, decompress


def test_deflate_roundtrip_small():
    """Test simple text round-trip compression and decompression."""
    data = b"Hello, DEFLATE compression world!"
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_random_bytes():
    """Test compression of random binary data."""
    data = os.urandom(1024)
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_repetitive():
    """Test compression of large repetitive input."""
    # DEFLATE should achieve excellent compression on repetitive data
    data = b"ABABABABAB" * 1000
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data
    # Verify good compression ratio
    assert len(compressed) < len(data) * 0.1  # Should compress to less than 10%


def test_deflate_truncated():
    """Test that truncated data raises descriptive exception."""
    data = b"Test data for truncation"
    compressed = compress(data, "DEFLATE")
    
    # Truncate the compressed data
    truncated = compressed[:len(compressed) // 2]
    
    with pytest.raises(ValueError, match="Corrupted DEFLATE data"):
        decompress(truncated, "DEFLATE")


def test_deflate_empty_input():
    """Test compression of empty input."""
    data = b""
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_single_byte():
    """Test compression of single byte."""
    data = b"A"
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_repeated_pattern():
    """Test compression of repeated pattern."""
    data = b"TOBEORNOTTOBEORTOBEORNOT" * 50
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data
    # Should compress well
    assert len(compressed) < len(data) * 0.3


def test_deflate_natural_text():
    """Test compression of natural text."""
    data = b"The quick brown fox jumps over the lazy dog. " * 100
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_all_bytes():
    """Test compression with all possible byte values."""
    data = bytes(range(256)) * 10
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_corrupted_header():
    """Test detection of corrupted header."""
    data = b"Test data"
    compressed = compress(data, "DEFLATE")
    
    # Corrupt the magic header
    corrupted = b"XXXX" + compressed[4:]
    
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(corrupted, "DEFLATE")


def test_deflate_wrong_algorithm():
    """Test that wrong algorithm is detected."""
    data = b"TEST"
    compressed = compress(data, "LZW")
    
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(compressed, "DEFLATE")


def test_deflate_case_insensitive():
    """Test that algorithm name is case-insensitive."""
    data = b"Test123"
    
    c1 = compress(data, "DEFLATE")
    c2 = compress(data, "deflate")
    c3 = compress(data, "Deflate")
    
    assert decompress(c1, "DEFLATE") == data
    assert decompress(c2, "deflate") == data
    assert decompress(c3, "Deflate") == data


def test_deflate_unicode_text():
    """Test compression of UTF-8 encoded text."""
    text = "Hello 世界! Ça va? 🚀 Testing DEFLATE"
    data = text.encode("utf-8")
    
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    
    assert decompressed == data
    assert decompressed.decode("utf-8") == text


def test_deflate_compression_ratio():
    """Test that DEFLATE achieves reasonable compression."""
    # Repetitive data should compress very well
    data = b"TOBEORNOTTOBEORTOBEORNOT" * 100
    compressed = compress(data, "DEFLATE")
    
    # Should achieve better than 20% of original size
    ratio = len(compressed) / len(data)
    assert ratio < 0.2, f"Compression ratio {ratio:.2%} should be < 20%"


def test_deflate_handles_password_parameter():
    """Test that password parameter is accepted (but not yet used)."""
    data = b"SECRET DATA"
    # Should not raise an error, just log a message
    compressed = compress(data, "DEFLATE", password="test123")
    decompressed = decompress(compressed, "DEFLATE", password="test123")
    assert decompressed == data


def test_deflate_large_input():
    """Test compression of larger input."""
    data = b"Large test data with various patterns and repeated sequences. " * 500
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_binary_patterns():
    """Test various binary data patterns."""
    patterns = [
        b"\x00" * 1000,  # All zeros
        b"\xFF" * 1000,  # All ones
        b"\x00\xFF" * 500,  # Alternating
        bytes(range(256)) * 4,  # Sequential
        b"ABCD" * 250,  # Short repeating pattern
    ]
    
    for pattern in patterns:
        compressed = compress(pattern, "DEFLATE")
        decompressed = decompress(compressed, "DEFLATE")
        assert decompressed == pattern


def test_deflate_mixed_content():
    """Test compression of mixed text and binary data."""
    data = b"Hello\x00\x01\x02World\xFF\xFE\xFD" * 100
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data


def test_deflate_preserves_byte_order():
    """Test that compression preserves exact byte ordering."""
    data = bytes(range(256)) + bytes(reversed(range(256)))
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
    assert decompressed == data
    # Verify exact ordering
    for i, byte in enumerate(decompressed):
        assert byte == data[i]


def test_deflate_too_short_data():
    """Test that too-short data is rejected."""
    with pytest.raises(ValueError, match="too short"):
        decompress(b"TC", "DEFLATE")


def test_deflate_vs_other_algorithms():
    """Compare DEFLATE with other algorithms on repetitive data."""
    data = b"ABABABABAB" * 500
    
    deflate_size = len(compress(data, "DEFLATE"))
    lzw_size = len(compress(data, "LZW"))
    huffman_size = len(compress(data, "HUFFMAN"))
    
    # DEFLATE should perform competitively
    assert deflate_size < len(data)
    # All algorithms should compress well on this data
    assert lzw_size < len(data)
    assert huffman_size < len(data)
