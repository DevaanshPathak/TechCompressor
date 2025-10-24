"""Comprehensive test suite for LZW compression implementation."""
import os
import pytest
from techcompressor.core import compress, decompress


def test_lzw_roundtrip():
    """Test basic round-trip compression and decompression."""
    data = b"TOBEORNOTTOBEORTOBEORNOT"
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_lzw_empty_input():
    """Test compression of empty input."""
    data = b""
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_lzw_single_byte():
    """Test compression of single byte."""
    data = b"A"
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_lzw_repeated_pattern():
    """Test compression of highly repetitive data (should compress well)."""
    data = b"AAAAAAAAAA" * 100
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data
    # Verify compression actually happened
    assert len(compressed) < len(data)


def test_lzw_random_binary():
    """Test compression of random binary data."""
    data = os.urandom(256)
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_lzw_large_input():
    """Test compression of large input to ensure dictionary reset works."""
    # Create large repetitive text to trigger dictionary resets
    data = (b"The quick brown fox jumps over the lazy dog. " * 500)
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_lzw_all_bytes():
    """Test compression with all possible byte values."""
    data = bytes(range(256)) * 10
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_lzw_compressibility():
    """Verify that repetitive data compresses better than random data."""
    repetitive = b"ABCABC" * 1000
    random_data = os.urandom(6000)
    
    compressed_rep = compress(repetitive, "LZW")
    compressed_rand = compress(random_data, "LZW")
    
    # Repetitive should compress better (smaller ratio)
    rep_ratio = len(compressed_rep) / len(repetitive)
    rand_ratio = len(compressed_rand) / len(random_data)
    
    assert rep_ratio < rand_ratio


def test_lzw_invalid_algorithm():
    """Test that unsupported algorithms raise NotImplementedError."""
    data = b"test"
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        compress(data, "HUFFMAN")
    
    compressed = compress(data, "LZW")
    with pytest.raises(NotImplementedError, match="not implemented yet"):
        decompress(compressed, "HUFFMAN")


def test_lzw_corrupted_header():
    """Test that corrupted magic header raises ValueError."""
    data = b"test data"
    compressed = compress(data, "LZW")
    
    # Corrupt the magic header
    corrupted = b"XXXX" + compressed[4:]
    
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(corrupted, "LZW")


def test_lzw_truncated_data():
    """Test that truncated data raises ValueError."""
    data = b"test data"
    compressed = compress(data, "LZW")
    
    # Truncate to less than header size
    truncated = compressed[:3]
    
    with pytest.raises(ValueError, match="too short"):
        decompress(truncated, "LZW")


def test_lzw_odd_length_compressed():
    """Test that odd-length compressed data raises ValueError."""
    # Create data with valid header but odd-length payload
    header = b"TCZ1\x10\x00"  # Valid header
    invalid_payload = b"ABC"  # Odd length (not multiple of 2)
    
    with pytest.raises(ValueError, match="invalid length"):
        decompress(header + invalid_payload, "LZW")


def test_lzw_password_placeholder():
    """Test that password parameter is accepted but logged as future feature."""
    data = b"secret data"
    
    # Should not raise error, just log warning
    compressed = compress(data, "LZW", password="mypassword")
    decompressed = decompress(compressed, "LZW", password="mypassword")
    
    assert decompressed == data


def test_lzw_case_insensitive_algo():
    """Test that algorithm name is case-insensitive."""
    data = b"test"
    
    compressed_lower = compress(data, "lzw")
    compressed_upper = compress(data, "LZW")
    compressed_mixed = compress(data, "LzW")
    
    # All should produce identical results
    assert decompress(compressed_lower, "LZW") == data
    assert decompress(compressed_upper, "lzw") == data
    assert decompress(compressed_mixed, "Lzw") == data


def test_lzw_unicode_text():
    """Test compression of UTF-8 encoded text."""
    text = "Hello, 世界! 🌍"
    data = text.encode("utf-8")
    
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    
    assert decompressed == data
    assert decompressed.decode("utf-8") == text


def test_lzw_binary_data_patterns():
    """Test various binary data patterns."""
    patterns = [
        b"\x00" * 1000,  # All zeros
        b"\xFF" * 1000,  # All ones
        b"\x00\xFF" * 500,  # Alternating
        bytes(range(256)) * 4,  # Sequential
    ]
    
    for pattern in patterns:
        compressed = compress(pattern, "LZW")
        decompressed = decompress(compressed, "LZW")
        assert decompressed == pattern
