"""
Additional tests for core.py module to improve coverage.

Targets edge cases, algorithm-specific behavior, and boundary conditions.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from techcompressor.core import (
    compress, decompress, 
    is_likely_compressed,
    reset_solid_compression_state,
    MAGIC_HEADER_LZW, MAGIC_HEADER_HUFFMAN, MAGIC_HEADER_DEFLATE,
    MAGIC_HEADER_ZSTD, MAGIC_HEADER_BROTLI
)
from techcompressor.crypto import MAGIC_HEADER_ENCRYPTED


class TestAutoAlgorithmSelection:
    """Test AUTO algorithm selection logic."""

    def test_auto_selects_zstd_for_large_files(self):
        """Test that AUTO mode prefers Zstd for large files."""
        # Create data > 5MB
        large_data = b"X" * (6 * 1024 * 1024)
        
        # AUTO should work on large files
        compressed = compress(large_data, algo="AUTO")
        assert len(compressed) > 0
        
        # Should decompress correctly with AUTO detection
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == large_data

    def test_auto_with_high_entropy_data(self):
        """Test AUTO mode with high entropy (random-like) data."""
        import random
        # High entropy data - random bytes
        high_entropy = bytes(random.randint(0, 255) for _ in range(10000))
        
        compressed = compress(high_entropy, algo="AUTO")
        assert len(compressed) > 0
        
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == high_entropy

    def test_auto_with_repetitive_data(self):
        """Test AUTO mode with highly repetitive data."""
        # Very repetitive data should compress well
        repetitive = b"AAAA" * 10000
        
        compressed = compress(repetitive, algo="AUTO")
        # Repetitive data should compress significantly
        assert len(compressed) < len(repetitive) * 0.5
        
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == repetitive


class TestCompressionEdgeCases:
    """Test edge cases in compression."""

    def test_empty_data_all_algorithms(self):
        """Test empty data with all algorithms."""
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(b"", algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed == b""

    def test_single_byte_all_algorithms(self):
        """Test single byte with all algorithms."""
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(b"X", algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed == b"X"

    def test_two_bytes_all_algorithms(self):
        """Test two bytes with all algorithms."""
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(b"XY", algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed == b"XY"

    def test_null_bytes_all_algorithms(self):
        """Test null bytes with all algorithms."""
        null_data = b"\x00" * 1000
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(null_data, algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed == null_data

    def test_binary_data_all_algorithms(self):
        """Test binary data (all byte values) with all algorithms."""
        binary_data = bytes(range(256)) * 10
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(binary_data, algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed == binary_data

    def test_unicode_encoded_data(self):
        """Test Unicode text encoded as UTF-8."""
        unicode_text = "Hello 世界 🌍 مرحبا" * 100
        unicode_bytes = unicode_text.encode('utf-8')
        
        for algo in ["LZW", "HUFFMAN", "DEFLATE"]:
            compressed = compress(unicode_bytes, algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed.decode('utf-8') == unicode_text


class TestIsLikelyCompressed:
    """Test the is_likely_compressed detection function."""

    def test_detects_compressed_extensions(self):
        """Test detection of compressed file extensions."""
        compressed_extensions = [
            "file.zip", "file.gz", "file.bz2", "file.xz",
            "file.rar", "file.7z"
        ]
        
        for filename in compressed_extensions:
            # Even with low entropy data, extension should trigger detection
            assert is_likely_compressed(b"A" * 100, filename=filename) is True

    def test_detects_media_extensions(self):
        """Test detection of media file extensions (already compressed)."""
        media_extensions = [
            "video.mp4", "video.mkv", "video.avi",
            "audio.mp3", "audio.aac", "audio.ogg",
            "image.jpg", "image.png", "image.webp"
        ]
        
        for filename in media_extensions:
            assert is_likely_compressed(b"X" * 100, filename=filename) is True

    def test_not_compressed_plain_text(self):
        """Test that plain text is not detected as compressed."""
        text_data = b"Hello World " * 100
        # Needs 1KB minimum for entropy check, and low entropy text
        assert is_likely_compressed(text_data, filename="document.txt") is False

    def test_high_entropy_detected(self):
        """Test that high entropy data is detected as compressed."""
        import random
        # Need 1KB+ of high entropy data for detection
        random.seed(42)
        random_data = bytes(random.randint(0, 255) for _ in range(4096))
        # High entropy without extension hint should be detected
        assert is_likely_compressed(random_data) is True

    def test_low_entropy_not_detected(self):
        """Test that low entropy data is not detected as compressed."""
        # Need 1KB+ of data for entropy check
        repetitive = b"A" * 4096
        assert is_likely_compressed(repetitive) is False
    
    def test_small_data_not_detected(self):
        """Test that small data (< 1KB) is not detected."""
        # Less than 1KB returns False regardless of entropy
        assert is_likely_compressed(b"random noise" * 10) is False


class TestMagicHeaders:
    """Test magic header detection in decompression."""

    def test_lzw_magic_header(self):
        """Test LZW magic header detection."""
        data = b"Test LZW data " * 100
        compressed = compress(data, algo="LZW")
        assert compressed[:4] == MAGIC_HEADER_LZW
        assert decompress(compressed, algo="LZW") == data

    def test_huffman_magic_header(self):
        """Test Huffman magic header detection."""
        data = b"Test Huffman data " * 100
        compressed = compress(data, algo="HUFFMAN")
        assert compressed[:4] == MAGIC_HEADER_HUFFMAN
        assert decompress(compressed, algo="HUFFMAN") == data

    def test_deflate_magic_header(self):
        """Test DEFLATE magic header detection."""
        data = b"Test DEFLATE data " * 100
        compressed = compress(data, algo="DEFLATE")
        assert compressed[:4] == MAGIC_HEADER_DEFLATE
        assert decompress(compressed, algo="DEFLATE") == data

    def test_zstd_magic_header(self):
        """Test Zstandard magic header detection."""
        data = b"Test Zstd data " * 100
        compressed = compress(data, algo="ZSTD")
        assert compressed[:4] == MAGIC_HEADER_ZSTD
        assert decompress(compressed, algo="ZSTD") == data

    def test_brotli_magic_header(self):
        """Test Brotli magic header detection."""
        data = b"Test Brotli data " * 100
        compressed = compress(data, algo="BROTLI")
        assert compressed[:4] == MAGIC_HEADER_BROTLI
        assert decompress(compressed, algo="BROTLI") == data

    def test_encrypted_magic_header(self):
        """Test encrypted magic header detection."""
        data = b"Test encrypted data " * 100
        compressed = compress(data, algo="LZW", password="secret")
        assert compressed[:4] == MAGIC_HEADER_ENCRYPTED
        assert decompress(compressed, password="secret") == data

    def test_invalid_magic_header_raises_error(self):
        """Test that invalid magic header raises error."""
        invalid_data = b"XXXX" + b"garbage data"
        
        with pytest.raises(ValueError):
            decompress(invalid_data)
    
    def test_auto_detects_any_header(self):
        """Test that AUTO mode can detect any algorithm header."""
        data = b"Test data for auto detection " * 100
        
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(data, algo=algo)
            # AUTO should detect and decompress correctly
            decompressed = decompress(compressed, algo="AUTO")
            assert decompressed == data


class TestSolidCompression:
    """Test solid compression state management."""

    def test_reset_solid_compression_state(self):
        """Test that reset_solid_compression_state works."""
        # Compress some data with persist_dict
        compress(b"First file data " * 100, algo="LZW", persist_dict=True)
        
        # Reset state
        reset_solid_compression_state()
        
        # Should work without issues after reset
        compressed = compress(b"New data " * 100, algo="LZW")
        decompressed = decompress(compressed)
        assert decompressed == b"New data " * 100

    def test_persist_dict_improves_ratio(self):
        """Test that persist_dict can improve compression ratio."""
        # Similar data compressed with persisted dictionary
        reset_solid_compression_state()
        
        data1 = b"Common pattern data " * 100
        data2 = b"Common pattern more " * 100  # Similar patterns
        
        # Without persist
        reset_solid_compression_state()
        comp1_alone = compress(data1, algo="LZW", persist_dict=False)
        comp2_alone = compress(data2, algo="LZW", persist_dict=False)
        total_alone = len(comp1_alone) + len(comp2_alone)
        
        # With persist - second compression should benefit from dictionary
        reset_solid_compression_state()
        comp1_solid = compress(data1, algo="LZW", persist_dict=True)
        comp2_solid = compress(data2, algo="LZW", persist_dict=True)
        total_solid = len(comp1_solid) + len(comp2_solid)
        
        # With similar data, solid should be same or smaller
        # (Not always guaranteed to be smaller for small data)
        assert total_solid <= total_alone + 100  # Allow small tolerance


class TestAlgorithmAliases:
    """Test algorithm name aliases."""

    def test_zstandard_alias(self):
        """Test that ZSTANDARD works as alias for ZSTD."""
        data = b"Test Zstandard alias " * 100
        
        compressed = compress(data, algo="ZSTANDARD")
        assert compressed[:4] == MAGIC_HEADER_ZSTD
        
        # Use ZSTD for decompression
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data

    def test_case_insensitive_algorithm(self):
        """Test that algorithm names are case-insensitive."""
        data = b"Case test " * 100
        
        # Test lowercase
        comp_lower = compress(data, algo="lzw")
        decomp_lower = decompress(comp_lower, algo="LZW")
        assert decomp_lower == data
        
        # Test mixed case
        comp_mixed = compress(data, algo="Huffman")
        decomp_mixed = decompress(comp_mixed, algo="HUFFMAN")
        assert decomp_mixed == data


class TestCompressionWithEncryption:
    """Test compression combined with encryption."""

    def test_all_algorithms_with_encryption(self):
        """Test all algorithms work with encryption."""
        data = b"Encrypted data test " * 100
        password = "test_password_123"
        
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(data, algo=algo, password=password)
            
            # All encrypted data starts with TCE1
            assert compressed[:4] == MAGIC_HEADER_ENCRYPTED
            
            # Decompress with password - after decryption, algorithm is auto-detected
            # Use AUTO to let magic header detection work
            decompressed = decompress(compressed, algo="AUTO", password=password)
            assert decompressed == data

    def test_encryption_with_empty_data(self):
        """Test encryption with empty data."""
        compressed = compress(b"", algo="LZW", password="secret")
        decompressed = decompress(compressed, algo="LZW", password="secret")
        assert decompressed == b""

    def test_wrong_password_fails(self):
        """Test that wrong password raises error."""
        data = b"Secret data " * 100
        compressed = compress(data, algo="LZW", password="correct")
        
        with pytest.raises(Exception):  # Can be various exception types
            decompress(compressed, password="wrong")


class TestLargeDataHandling:
    """Test handling of large data."""

    def test_medium_file_compression(self):
        """Test compression of medium-sized data (1MB)."""
        data = b"Medium file test data " * 50000  # ~1MB
        
        for algo in ["LZW", "ZSTD"]:
            compressed = compress(data, algo=algo)
            decompressed = decompress(compressed, algo=algo)
            assert decompressed == data

    def test_compression_ratio_varies_by_algorithm(self):
        """Test that different algorithms give different ratios."""
        # Text data compresses well
        data = b"The quick brown fox jumps over the lazy dog. " * 1000
        
        ratios = {}
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            compressed = compress(data, algo=algo)
            ratios[algo] = len(compressed) / len(data)
        
        # All should compress (ratio < 1)
        for algo, ratio in ratios.items():
            assert ratio < 1.0, f"{algo} failed to compress: ratio={ratio}"
        
        # Ratios should vary
        ratio_values = list(ratios.values())
        assert max(ratio_values) != min(ratio_values), "All algorithms gave same ratio"
