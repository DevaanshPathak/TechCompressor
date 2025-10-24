"""Integration tests to verify multiple algorithms work together correctly."""
import os
import pytest
from techcompressor.core import compress, decompress


def test_lzw_and_huffman_independence():
    """Verify LZW and Huffman can be used independently."""
    data = b"ABCABCABC"
    
    # Test LZW
    lzw_compressed = compress(data, "LZW")
    lzw_decompressed = decompress(lzw_compressed, "LZW")
    assert lzw_decompressed == data
    
    # Test Huffman
    huffman_compressed = compress(data, "HUFFMAN")
    huffman_decompressed = decompress(huffman_compressed, "HUFFMAN")
    assert huffman_decompressed == data


def test_lzw_basic_roundtrip():
    """Basic LZW integration test."""
    data = b"HELLOHELLO"
    compressed = compress(data, "LZW")
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data


def test_huffman_basic_roundtrip():
    """Basic Huffman integration test."""
    data = b"ABCABCABC"
    compressed = compress(data, "HUFFMAN")
    decompressed = decompress(compressed, "HUFFMAN")
    assert decompressed == data


def test_different_data_different_algorithms():
    """Test both algorithms on different data types."""
    text_data = b"The quick brown fox jumps over the lazy dog."
    binary_data = os.urandom(100)
    
    # LZW on text
    lzw_text = decompress(compress(text_data, "LZW"), "LZW")
    assert lzw_text == text_data
    
    # Huffman on text
    huffman_text = decompress(compress(text_data, "HUFFMAN"), "HUFFMAN")
    assert huffman_text == text_data
    
    # LZW on binary
    lzw_binary = decompress(compress(binary_data, "LZW"), "LZW")
    assert lzw_binary == binary_data
    
    # Huffman on binary
    huffman_binary = decompress(compress(binary_data, "HUFFMAN"), "HUFFMAN")
    assert huffman_binary == binary_data


def test_wrong_algorithm_detection():
    """Test that using wrong decompression algorithm fails gracefully."""
    data = b"test data"
    
    # Compress with LZW
    lzw_compressed = compress(data, "LZW")
    
    # Try to decompress with Huffman (should fail due to magic header)
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(lzw_compressed, "HUFFMAN")
    
    # Compress with Huffman
    huffman_compressed = compress(data, "HUFFMAN")
    
    # Try to decompress with LZW (should fail due to magic header)
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(huffman_compressed, "LZW")


def test_same_data_different_results():
    """Verify different algorithms produce different compressed outputs."""
    data = b"TESTDATA" * 100
    
    lzw_result = compress(data, "LZW")
    huffman_result = compress(data, "HUFFMAN")
    
    # Different magic headers
    assert lzw_result[:4] == b"TCZ1"
    assert huffman_result[:4] == b"TCH1"
    
    # Different compressed data
    assert lzw_result != huffman_result
    
    # But both decompress to same original
    assert decompress(lzw_result, "LZW") == data
    assert decompress(huffman_result, "HUFFMAN") == data


def test_compression_ratio_comparison():
    """Compare compression ratios for different data types."""
    # Repetitive data (favors LZW)
    repetitive = b"ABABAB" * 1000
    
    lzw_compressed = compress(repetitive, "LZW")
    huffman_compressed = compress(repetitive, "HUFFMAN")
    
    # Both should compress, verify decompression works
    assert decompress(lzw_compressed, "LZW") == repetitive
    assert decompress(huffman_compressed, "HUFFMAN") == repetitive
    
    # Both should achieve compression
    assert len(lzw_compressed) < len(repetitive)
    assert len(huffman_compressed) < len(repetitive)


def test_empty_input_both_algorithms():
    """Test that both algorithms handle empty input correctly."""
    data = b""
    
    lzw_result = decompress(compress(data, "LZW"), "LZW")
    huffman_result = decompress(compress(data, "HUFFMAN"), "HUFFMAN")
    
    assert lzw_result == data
    assert huffman_result == data


def test_large_data_both_algorithms():
    """Test both algorithms on larger data."""
    data = b"Large test data with various patterns. " * 10000
    
    # LZW
    lzw_compressed = compress(data, "LZW")
    lzw_decompressed = decompress(lzw_compressed, "LZW")
    assert lzw_decompressed == data
    
    # Huffman
    huffman_compressed = compress(data, "HUFFMAN")
    huffman_decompressed = decompress(huffman_compressed, "HUFFMAN")
    assert huffman_decompressed == data


def test_binary_data_both_algorithms():
    """Test both algorithms preserve binary data integrity."""
    data = bytes(range(256)) * 20
    
    lzw_roundtrip = decompress(compress(data, "LZW"), "LZW")
    huffman_roundtrip = decompress(compress(data, "HUFFMAN"), "HUFFMAN")
    
    assert lzw_roundtrip == data
    assert huffman_roundtrip == data


def test_password_parameter_both_algorithms():
    """Test that password parameter works with both algorithms."""
    data = b"sensitive data"
    password = "secret123"
    
    # Both should accept password parameter (logged, not yet implemented)
    lzw_compressed = compress(data, "LZW", password=password)
    huffman_compressed = compress(data, "HUFFMAN", password=password)
    
    lzw_result = decompress(lzw_compressed, "LZW", password=password)
    huffman_result = decompress(huffman_compressed, "HUFFMAN", password=password)
    
    assert lzw_result == data
    assert huffman_result == data


def test_algorithm_name_case_insensitive():
    """Test that algorithm names are case-insensitive for both."""
    data = b"test"
    
    # LZW variations
    assert decompress(compress(data, "lzw"), "LZW") == data
    assert decompress(compress(data, "LZW"), "lzw") == data
    assert decompress(compress(data, "Lzw"), "LzW") == data
    
    # Huffman variations
    assert decompress(compress(data, "huffman"), "HUFFMAN") == data
    assert decompress(compress(data, "HUFFMAN"), "huffman") == data
    assert decompress(compress(data, "Huffman"), "HuFfMaN") == data


def test_unicode_text_both_algorithms():
    """Test both algorithms with Unicode text."""
    text = "Hello 世界! Привет мир! 🌍"
    data = text.encode("utf-8")
    
    lzw_result = decompress(compress(data, "LZW"), "LZW")
    huffman_result = decompress(compress(data, "HUFFMAN"), "HUFFMAN")
    
    assert lzw_result == data
    assert huffman_result == data
    assert lzw_result.decode("utf-8") == text
    assert huffman_result.decode("utf-8") == text


def test_stress_test_multiple_compressions():
    """Stress test with multiple sequential compressions."""
    original_data = b"Stress test data with patterns. " * 100
    
    # Compress and decompress multiple times
    for _ in range(5):
        # LZW
        compressed_lzw = compress(original_data, "LZW")
        decompressed_lzw = decompress(compressed_lzw, "LZW")
        assert decompressed_lzw == original_data
        
        # Huffman
        compressed_huffman = compress(original_data, "HUFFMAN")
        decompressed_huffman = decompress(compressed_huffman, "HUFFMAN")
        assert decompressed_huffman == original_data
