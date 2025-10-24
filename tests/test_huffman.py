"""Comprehensive test suite for Huffman coding implementation."""
import os
import pytest
from techcompressor.core import compress, decompress


def test_huffman_roundtrip():
    """Test basic round-trip compression and decompression."""
    data = b"ABCABCABC"
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_empty_input():
    """Test compression of empty input."""
    data = b""
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_single_byte():
    """Test compression of single byte."""
    data = b"A"
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_repeated_pattern():
    """Test compression of highly repetitive data (should compress well)."""
    data = b"AAAAAAAAAA" * 100
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data
    # Verify compression actually happened
    assert len(compressed) < len(data)


def test_huffman_random_binary():
    """Test compression of random binary data."""
    data = os.urandom(256)
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_large_input():
    """Test compression of large input."""
    data = b"The quick brown fox jumps over the lazy dog. " * 500
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_all_bytes():
    """Test compression with all possible byte values."""
    data = bytes(range(256)) * 10
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_text_compression():
    """Test that text with non-uniform distribution compresses well."""
    # Text with skewed frequency distribution
    text = b"e" * 1000 + b"t" * 800 + b"a" * 600 + b"o" * 500 + b"i" * 400 + b"n" * 300
    compressed = compress(text, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == text
    # Should compress well due to skewed distribution
    assert len(compressed) < len(text) * 0.5


def test_huffman_compressibility():
    """Verify that non-uniform data compresses better than uniform data."""
    # Highly skewed distribution
    skewed = b"A" * 900 + b"B" * 90 + b"C" * 10
    
    # Uniform distribution
    uniform = b"ABC" * 333 + b"A"
    
    compressed_skewed = compress(skewed, "HUFFMAN")
    compressed_uniform = compress(uniform, "HUFFMAN")
    
    # Skewed should compress better (smaller size)
    assert len(compressed_skewed) < len(compressed_uniform)


def test_huffman_invalid_algorithm():
    """Test that unsupported algorithms raise NotImplementedError."""
    data = b"test"
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        compress(data, "ARITHMETIC")
    
    compressed = compress(data, "HUFFMAN")
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        decompress(compressed, "ARITHMETIC")


def test_huffman_corrupted_header():
    """Test that corrupted magic header raises ValueError."""
    data = b"test data"
    compressed = compress(data, "HUFFMAN")
    
    # Corrupt the magic header
    corrupted = b"XXXX" + compressed[4:]
    
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(corrupted, "HUFFMAN")


def test_huffman_truncated_data():
    """Test that truncated data raises ValueError."""
    data = b"test data"
    compressed = compress(data, "HUFFMAN")
    
    # Truncate to less than header size
    truncated = compressed[:2]
    
    with pytest.raises(ValueError, match="too short"):
        decompress(truncated, "HUFFMAN")


def test_huffman_password_placeholder():
    """Test that password parameter is accepted but logged as future feature."""
    data = b"secret data"
    
    # Should not raise error, just log warning
    compressed = compress(data, "HUFFMAN", password="mypassword")
    decompressed = decompress(compressed, "HUFFMAN", password="mypassword")
    
    assert decompressed == data


def test_huffman_case_insensitive_algo():
    """Test that algorithm name is case-insensitive."""
    data = b"test"
    
    compressed_lower = compress(data, "huffman")
    compressed_upper = compress(data, "HUFFMAN")
    compressed_mixed = compress(data, "Huffman")
    
    # All should decompress correctly
    assert decompress(compressed_lower, "HUFFMAN") == data
    assert decompress(compressed_upper, "huffman") == data
    assert decompress(compressed_mixed, "HuFfMaN") == data


def test_huffman_unicode_text():
    """Test compression of UTF-8 encoded text."""
    text = "Hello, 世界! 🌍 Testing Huffman with Unicode."
    data = text.encode("utf-8")
    
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    
    assert decompressed == data
    assert decompressed.decode("utf-8") == text


def test_huffman_binary_data_patterns():
    """Test various binary data patterns."""
    patterns = [
        b"\x00" * 1000,  # All zeros
        b"\xFF" * 1000,  # All ones
        b"\x00\xFF" * 500,  # Alternating
        bytes(range(256)) * 4,  # Sequential
        b"ABCD" * 250,  # Short repeating pattern
    ]
    
    for pattern in patterns:
        compressed = compress(pattern, "HUFFMAN")
        decompressed = decompress(compressed, "HUFFMAN")
        assert decompressed == pattern


def test_huffman_two_unique_bytes():
    """Test compression with only two unique byte values."""
    data = b"AB" * 500
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_mixed_text_and_binary():
    """Test compression of mixed text and binary data."""
    data = b"Hello\x00\x01\x02World\xFF\xFE\xFD" * 100
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_huffman_preserves_byte_order():
    """Test that compression preserves exact byte ordering."""
    data = bytes(range(256)) + bytes(reversed(range(256)))
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data
    # Verify exact ordering
    for i, byte in enumerate(decompressed):
        assert byte == data[i]


def test_huffman_single_repeated_byte():
    """Test compression of data with single repeated byte."""
    data = b"X" * 10000
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data
    # Should compress very well (better than 20%)
    assert len(compressed) < len(data) * 0.2
