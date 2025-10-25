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


def test_deflate_basic_roundtrip():
    """Basic DEFLATE integration test."""
    data = b"ABABABABAB"
    compressed = compress(data, "DEFLATE")
    decompressed = decompress(compressed, "DEFLATE")
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
    
    # DEFLATE on text
    deflate_text = decompress(compress(text_data, "DEFLATE"), "DEFLATE")
    assert deflate_text == text_data
    
    # DEFLATE on binary
    deflate_binary = decompress(compress(binary_data, "DEFLATE"), "DEFLATE")
    assert deflate_binary == binary_data


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
    
    # Compress with DEFLATE
    deflate_compressed = compress(data, "DEFLATE")
    
    # Try to decompress with LZW (should fail due to magic header)
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(deflate_compressed, "LZW")
    
    # Try to decompress with Huffman (should fail due to magic header)
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(deflate_compressed, "HUFFMAN")


def test_same_data_different_results():
    """Verify different algorithms produce different compressed outputs."""
    data = b"TESTDATA" * 100
    
    lzw_result = compress(data, "LZW")
    huffman_result = compress(data, "HUFFMAN")
    deflate_result = compress(data, "DEFLATE")
    
    # Different magic headers
    assert lzw_result[:4] == b"TCZ1"
    assert huffman_result[:4] == b"TCH1"
    assert deflate_result[:4] == b"TCD1"
    
    # Different compressed data
    assert lzw_result != huffman_result
    assert lzw_result != deflate_result
    assert huffman_result != deflate_result
    
    # But all decompress to same original
    assert decompress(lzw_result, "LZW") == data
    assert decompress(huffman_result, "HUFFMAN") == data
    assert decompress(deflate_result, "DEFLATE") == data


def test_compression_ratio_comparison():
    """Compare compression ratios for different data types."""
    # Repetitive data (favors LZW and DEFLATE)
    repetitive = b"ABABAB" * 1000
    
    lzw_compressed = compress(repetitive, "LZW")
    huffman_compressed = compress(repetitive, "HUFFMAN")
    deflate_compressed = compress(repetitive, "DEFLATE")
    
    # All should compress, verify decompression works
    assert decompress(lzw_compressed, "LZW") == repetitive
    assert decompress(huffman_compressed, "HUFFMAN") == repetitive
    assert decompress(deflate_compressed, "DEFLATE") == repetitive
    
    # All should achieve compression
    assert len(lzw_compressed) < len(repetitive)
    assert len(huffman_compressed) < len(repetitive)
    assert len(deflate_compressed) < len(repetitive)


def test_empty_input_both_algorithms():
    """Test that all algorithms handle empty input correctly."""
    data = b""
    
    lzw_result = decompress(compress(data, "LZW"), "LZW")
    huffman_result = decompress(compress(data, "HUFFMAN"), "HUFFMAN")
    deflate_result = decompress(compress(data, "DEFLATE"), "DEFLATE")
    
    assert lzw_result == data
    assert huffman_result == data
    assert deflate_result == data


def test_large_data_both_algorithms():
    """Test all algorithms on larger data."""
    data = b"Large test data with various patterns. " * 10000
    
    # LZW
    lzw_compressed = compress(data, "LZW")
    lzw_decompressed = decompress(lzw_compressed, "LZW")
    assert lzw_decompressed == data
    
    # Huffman
    huffman_compressed = compress(data, "HUFFMAN")
    huffman_decompressed = decompress(huffman_compressed, "HUFFMAN")
    assert huffman_decompressed == data
    
    # DEFLATE
    deflate_compressed = compress(data, "DEFLATE")
    deflate_decompressed = decompress(deflate_compressed, "DEFLATE")
    assert deflate_decompressed == data


def test_binary_data_both_algorithms():
    """Test all algorithms preserve binary data integrity."""
    data = bytes(range(256)) * 20
    
    lzw_roundtrip = decompress(compress(data, "LZW"), "LZW")
    huffman_roundtrip = decompress(compress(data, "HUFFMAN"), "HUFFMAN")
    deflate_roundtrip = decompress(compress(data, "DEFLATE"), "DEFLATE")
    
    assert lzw_roundtrip == data
    assert huffman_roundtrip == data
    assert deflate_roundtrip == data


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


# Password Protection Tests

def test_password_encryption_lzw():
    """Test LZW compression with password encryption."""
    data = b"CONFIDENTIALDATA12345"
    password = "pass123"
    
    compressed = compress(data, "LZW", password=password)
    
    # Verify encrypted data starts with TCE1 magic
    assert compressed[:4] == b"TCE1"
    
    # Decrypt and decompress
    decompressed = decompress(compressed, "LZW", password=password)
    assert decompressed == data


def test_password_encryption_huffman():
    """Test Huffman compression with password encryption."""
    data = b"SECRET MESSAGE FOR HUFFMAN"
    password = "secure_pass_456"
    
    compressed = compress(data, "HUFFMAN", password=password)
    
    # Verify encrypted
    assert compressed[:4] == b"TCE1"
    
    # Decrypt and decompress
    decompressed = decompress(compressed, "HUFFMAN", password=password)
    assert decompressed == data


def test_password_encryption_deflate():
    """Test DEFLATE compression with password encryption."""
    data = b"DEFLATE WITH PASSWORD" * 100
    password = "deflate_pass_789"
    
    compressed = compress(data, "DEFLATE", password=password)
    
    # Verify encrypted
    assert compressed[:4] == b"TCE1"
    
    # Decrypt and decompress
    decompressed = decompress(compressed, "DEFLATE", password=password)
    assert decompressed == data


def test_password_wrong_password():
    """Test that wrong password raises error for all algorithms."""
    data = b"SECRET DATA"
    correct_password = "correct_pass"
    wrong_password = "wrong_pass"
    
    # LZW
    compressed_lzw = compress(data, "LZW", password=correct_password)
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decompress(compressed_lzw, "LZW", password=wrong_password)
    
    # Huffman
    compressed_huffman = compress(data, "HUFFMAN", password=correct_password)
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decompress(compressed_huffman, "HUFFMAN", password=wrong_password)
    
    # DEFLATE
    compressed_deflate = compress(data, "DEFLATE", password=correct_password)
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decompress(compressed_deflate, "DEFLATE", password=wrong_password)


def test_password_missing_on_encrypted():
    """Test that encrypted data without password raises error."""
    data = b"ENCRYPTED DATA"
    password = "password123"
    
    # Compress with password
    compressed = compress(data, "LZW", password=password)
    
    # Try to decompress without password
    with pytest.raises(ValueError, match="Data is encrypted but no password provided"):
        decompress(compressed, "LZW")


def test_password_empty_data():
    """Test password encryption with empty data."""
    data = b""
    password = "empty_pass"
    
    # All algorithms should handle empty data with password
    for algo in ["LZW", "HUFFMAN", "DEFLATE"]:
        compressed = compress(data, algo, password=password)
        decompressed = decompress(compressed, algo, password=password)
        assert decompressed == data


def test_password_large_data():
    """Test password encryption with large data."""
    data = b"LARGE DATA PATTERN " * 10000  # ~200 KB
    password = "large_data_pass"
    
    for algo in ["LZW", "HUFFMAN", "DEFLATE"]:
        compressed = compress(data, algo, password=password)
        decompressed = decompress(compressed, algo, password=password)
        assert decompressed == data


def test_password_different_per_compression():
    """Test that same data with same password produces different ciphertext."""
    data = b"SAME DATA"
    password = "same_pass"
    
    # Encrypt twice with same password
    compressed1 = compress(data, "LZW", password=password)
    compressed2 = compress(data, "LZW", password=password)
    
    # Ciphertexts should be different (due to random salt/nonce)
    assert compressed1 != compressed2
    
    # But both should decrypt to same data
    assert decompress(compressed1, "LZW", password=password) == data
    assert decompress(compressed2, "LZW", password=password) == data


def test_password_cross_algorithm():
    """Test that password works correctly across different algorithms."""
    data = b"CROSS ALGORITHM TEST DATA"
    password = "cross_algo_pass"
    
    # Compress with different algorithms
    lzw_enc = compress(data, "LZW", password=password)
    huffman_enc = compress(data, "HUFFMAN", password=password)
    deflate_enc = compress(data, "DEFLATE", password=password)
    
    # All should decrypt correctly
    assert decompress(lzw_enc, "LZW", password=password) == data
    assert decompress(huffman_enc, "HUFFMAN", password=password) == data
    assert decompress(deflate_enc, "DEFLATE", password=password) == data


def test_password_unicode():
    """Test password encryption with Unicode passwords."""
    data = b"UNICODE PASSWORD TEST"
    password = "пароль密码🔐"  # Russian, Chinese, emoji
    
    compressed = compress(data, "LZW", password=password)
    decompressed = decompress(compressed, "LZW", password=password)
    
    assert decompressed == data


def test_password_backward_compatibility():
    """Test that non-encrypted data still works without password."""
    data = b"UNENCRYPTED DATA"
    
    # Compress without password (old behavior)
    compressed = compress(data, "LZW")
    
    # Should not start with TCE1
    assert compressed[:4] != b"TCE1"
    
    # Should decompress without password
    decompressed = decompress(compressed, "LZW")
    assert decompressed == data
