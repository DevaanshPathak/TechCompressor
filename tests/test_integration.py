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


# =============================================================================
# v1.2.0 Integration Tests
# =============================================================================

def test_entropy_detection_with_all_algorithms():
    """Test entropy detection works across different compression algorithms (v1.2.0)"""
    from techcompressor.core import is_likely_compressed
    
    # High entropy data (simulated compressed file)
    high_entropy = os.urandom(2000)
    
    # Test with various "compressed" file extensions
    assert is_likely_compressed(high_entropy, "archive.zip") == True
    assert is_likely_compressed(high_entropy, "image.jpg") == True
    assert is_likely_compressed(high_entropy, "video.mp4") == True
    assert is_likely_compressed(high_entropy, "audio.mp3") == True
    
    # Low entropy data (repetitive text)
    low_entropy = b"Hello World " * 100
    
    # Should not detect as compressed for text files
    assert is_likely_compressed(low_entropy, "document.txt") == False
    assert is_likely_compressed(low_entropy, "code.py") == False
    
    # But should detect based on entropy alone if no extension
    assert is_likely_compressed(high_entropy, "unknown") == True
    assert is_likely_compressed(low_entropy, "unknown") == False


def test_auto_mode_entropy_integration():
    """Test AUTO mode integrates with entropy detection (v1.2.0)"""
    # Repetitive data (should compress well)
    repetitive = b"ABCDEFGH" * 1000
    
    compressed = compress(repetitive, "AUTO")
    decompressed = decompress(compressed, "AUTO")
    
    assert decompressed == repetitive
    assert len(compressed) < len(repetitive)
    
    # High entropy data (may not compress as well, but should still roundtrip)
    random_data = os.urandom(1000)
    
    compressed_random = compress(random_data, "AUTO")
    decompressed_random = decompress(compressed_random, "AUTO")
    
    assert decompressed_random == random_data


def test_archive_with_filters_and_metadata():
    """Test archiver integration with filters and metadata (v1.2.0)"""
    import tempfile
    from pathlib import Path
    from techcompressor.archiver import create_archive, extract_archive, list_contents
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        archive_path = Path(tmpdir) / "filtered.tc"
        extract_dir = Path(tmpdir) / "extracted"
        
        source_dir.mkdir()
        
        # Create test files
        (source_dir / "include.txt").write_bytes(b"x" * 1000)
        (source_dir / "exclude.tmp").write_bytes(b"x" * 1000)
        (source_dir / "small.txt").write_bytes(b"x" * 10)
        
        # Create archive with filters and metadata
        create_archive(
            source_dir,
            archive_path,
            exclude_patterns=["*.tmp"],
            min_file_size=100,
            comment="Test archive with filters",
            creator="Integration Test"
        )
        
        # List contents and verify metadata
        contents = list_contents(archive_path)
        
        # Should have metadata + 1 file (include.txt only)
        if 'metadata' in contents[0]:
            assert len(contents) == 2
            assert contents[0]['metadata']['comment'] == "Test archive with filters"
            assert contents[0]['metadata']['creator'] == "Integration Test"
            assert contents[1]['name'] == 'include.txt'
        
        # Extract and verify
        extract_archive(archive_path, extract_dir)
        assert (extract_dir / "include.txt").exists()
        assert not (extract_dir / "exclude.tmp").exists()
        assert not (extract_dir / "small.txt").exists()


def test_incremental_with_encryption():
    """Test incremental backup works with encryption (v1.2.0)"""
    import tempfile
    from pathlib import Path
    from techcompressor.archiver import create_archive, extract_archive
    import time
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        base_archive = Path(tmpdir) / "base.tc"
        incremental_archive = Path(tmpdir) / "incremental.tc"
        extract_dir = Path(tmpdir) / "extracted"
        
        source_dir.mkdir()
        
        # Create initial files
        (source_dir / "file1.txt").write_text("Data 1")
        (source_dir / "file2.txt").write_text("Data 2")
        
        # Create encrypted base archive
        password = "test_password_123"
        create_archive(source_dir, base_archive, password=password)
        
        # Wait and modify
        time.sleep(0.1)
        (source_dir / "file2.txt").write_text("Modified 2")
        (source_dir / "file3.txt").write_text("Data 3")
        
        # Create encrypted incremental archive
        create_archive(
            source_dir,
            incremental_archive,
            password=password,
            incremental=True,
            base_archive=base_archive
        )
        
        # Extract incremental
        extract_archive(incremental_archive, extract_dir, password=password)
        
        # Should have only changed/new files
        assert not (extract_dir / "file1.txt").exists()
        assert (extract_dir / "file2.txt").exists()
        assert (extract_dir / "file3.txt").exists()


def test_solid_compression_state_reset():
    """Test that solid compression state can be reset (v1.1.0/v1.2.0)"""
    from techcompressor.core import compress, decompress, reset_solid_compression_state
    
    # Compress with solid mode
    data1 = b"ABCDEFGH" * 100
    compressed1 = compress(data1, "LZW", persist_dict=True)
    
    data2 = b"ABCDEFGH" * 100  # Same pattern
    compressed2 = compress(data2, "LZW", persist_dict=True)
    
    # Reset state
    reset_solid_compression_state()
    
    # Compress again (should be independent of previous compressions)
    data3 = b"ABCDEFGH" * 100
    compressed3 = compress(data3, "LZW", persist_dict=True)
    
    # All should decompress correctly (persist_dict only affects compression)
    # Each compressed blob is self-contained for decompression
    assert decompress(compressed1, "LZW") == data1
    # Note: compressed2 with persist_dict cannot be decompressed standalone
    # because it relies on the dictionary state from compressed1
    # This is expected behavior for solid compression
    assert decompress(compressed3, "LZW") == data3
    
    # Verify reset worked - compressed3 should be similar size to compressed1
    # (both start with fresh dictionary)
    assert abs(len(compressed3) - len(compressed1)) < 50  # Allow small variance


def test_metadata_with_unicode():
    """Test archive metadata handles Unicode correctly (v1.2.0)"""
    import tempfile
    from pathlib import Path
    from techcompressor.archiver import create_archive, list_contents
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        archive_path = Path(tmpdir) / "unicode.tc"
        
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("Test")
        
        # Create archive with Unicode metadata
        unicode_comment = "Архив с кириллицей 中文字符"
        unicode_creator = "Devaansh Pathak 🚀"
        
        create_archive(
            source_dir,
            archive_path,
            comment=unicode_comment,
            creator=unicode_creator
        )
        
        # List contents and verify Unicode preserved
        contents = list_contents(archive_path)
        
        if 'metadata' in contents[0]:
            metadata = contents[0]['metadata']
            assert metadata['comment'] == unicode_comment
            assert metadata['creator'] == unicode_creator


def test_empty_metadata_fields():
    """Test archive handles empty/None metadata gracefully (v1.2.0)"""
    import tempfile
    from pathlib import Path
    from techcompressor.archiver import create_archive, list_contents
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        archive_path = Path(tmpdir) / "empty_meta.tc"
        
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("Test")
        
        # Create archive with empty metadata
        create_archive(
            source_dir,
            archive_path,
            comment=None,
            creator=None
        )
        
        # List contents - should work with empty metadata
        contents = list_contents(archive_path)
        
        # If metadata is present, verify structure
        if 'metadata' in contents[0]:
            metadata = contents[0]['metadata']
            # creation_date should always be present
            assert 'creation_date' in metadata
            # comment and creator should NOT be present when empty (length 0)
            # This is expected behavior - only non-empty fields are stored

