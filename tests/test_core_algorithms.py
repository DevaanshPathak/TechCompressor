"""
Additional core tests for AUTO mode edge cases and algorithm-specific paths.
"""

import pytest
import struct
from unittest.mock import patch


class TestAutoModeEdgeCases:
    """Test AUTO mode edge cases and fallbacks."""
    
    def test_auto_mode_basic(self):
        """Test AUTO mode selects best algorithm."""
        from techcompressor.core import compress, decompress
        
        data = b"Test content " * 100
        compressed = compress(data, algo="AUTO")
        
        # Should compress successfully
        assert len(compressed) > 0
        
        # Should decompress with AUTO
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_mode_small_data(self):
        """Test AUTO mode with small data (may expand)."""
        from techcompressor.core import compress, decompress
        
        data = b"tiny"
        compressed = compress(data, algo="AUTO")
        
        # May expand but should still work
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_mode_medium_data(self):
        """Test AUTO mode with medium-sized data."""
        from techcompressor.core import compress, decompress
        
        data = b"X" * 10000
        compressed = compress(data, algo="AUTO")
        
        # Should compress well
        assert len(compressed) < len(data)
        
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_mode_random_data(self):
        """Test AUTO mode with random (incompressible) data."""
        from techcompressor.core import compress, decompress
        import os
        
        data = os.urandom(1000)  # Random data
        compressed = compress(data, algo="AUTO")
        
        # May expand but should still work
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data


class TestLZWEdgeCases:
    """Test LZW algorithm edge cases."""
    
    def test_lzw_empty_data(self):
        """Test LZW with empty data."""
        from techcompressor.core import compress, decompress
        
        data = b""
        compressed = compress(data, algo="LZW")
        decompressed = decompress(compressed, algo="LZW")
        assert decompressed == data
    
    def test_lzw_single_byte(self):
        """Test LZW with single byte."""
        from techcompressor.core import compress, decompress
        
        data = b"A"
        compressed = compress(data, algo="LZW")
        decompressed = decompress(compressed, algo="LZW")
        assert decompressed == data
    
    def test_lzw_all_same_bytes(self):
        """Test LZW with all same bytes (highly compressible)."""
        from techcompressor.core import compress, decompress
        
        data = b"A" * 10000
        compressed = compress(data, algo="LZW")
        
        # Should compress extremely well
        assert len(compressed) < len(data) / 10
        
        decompressed = decompress(compressed, algo="LZW")
        assert decompressed == data
    
    def test_lzw_binary_data(self):
        """Test LZW with binary data."""
        from techcompressor.core import compress, decompress
        
        data = bytes(range(256)) * 10
        compressed = compress(data, algo="LZW")
        decompressed = decompress(compressed, algo="LZW")
        assert decompressed == data
    
    def test_lzw_dictionary_reset(self):
        """Test LZW dictionary reset with large data."""
        from techcompressor.core import compress, decompress
        
        # Create data that will cause dictionary to fill and reset
        data = bytes(range(256)) * 100
        compressed = compress(data, algo="LZW")
        decompressed = decompress(compressed, algo="LZW")
        assert decompressed == data
    
    def test_lzw_solid_mode(self):
        """Test LZW with persist_dict=True."""
        from techcompressor.core import compress, decompress, reset_solid_compression_state
        
        reset_solid_compression_state()
        
        data1 = b"First file content"
        data2 = b"Second file content with similar words content"
        
        # Compress with solid mode
        compressed1 = compress(data1, algo="LZW", persist_dict=True)
        compressed2 = compress(data2, algo="LZW", persist_dict=True)
        
        # Should work
        assert len(compressed1) > 0
        assert len(compressed2) > 0
        
        reset_solid_compression_state()


class TestHuffmanEdgeCases:
    """Test Huffman algorithm edge cases."""
    
    def test_huffman_empty_data(self):
        """Test Huffman with empty data."""
        from techcompressor.core import compress, decompress
        
        data = b""
        compressed = compress(data, algo="HUFFMAN")
        decompressed = decompress(compressed, algo="HUFFMAN")
        assert decompressed == data
    
    def test_huffman_single_byte(self):
        """Test Huffman with single byte."""
        from techcompressor.core import compress, decompress
        
        data = b"A"
        compressed = compress(data, algo="HUFFMAN")
        decompressed = decompress(compressed, algo="HUFFMAN")
        assert decompressed == data
    
    def test_huffman_uniform_frequency(self):
        """Test Huffman with all bytes having same frequency."""
        from techcompressor.core import compress, decompress
        
        # Each byte appears exactly once
        data = bytes(range(256))
        compressed = compress(data, algo="HUFFMAN")
        decompressed = decompress(compressed, algo="HUFFMAN")
        assert decompressed == data
    
    def test_huffman_skewed_frequency(self):
        """Test Huffman with highly skewed frequency."""
        from techcompressor.core import compress, decompress
        
        # One byte appears much more than others
        data = b"A" * 1000 + b"B" * 10 + b"C"
        compressed = compress(data, algo="HUFFMAN")
        
        # Should compress well
        assert len(compressed) < len(data)
        
        decompressed = decompress(compressed, algo="HUFFMAN")
        assert decompressed == data


class TestDEFLATEEdgeCases:
    """Test DEFLATE algorithm edge cases."""
    
    def test_deflate_empty_data(self):
        """Test DEFLATE with empty data."""
        from techcompressor.core import compress, decompress
        
        data = b""
        compressed = compress(data, algo="DEFLATE")
        decompressed = decompress(compressed, algo="DEFLATE")
        assert decompressed == data
    
    def test_deflate_single_byte(self):
        """Test DEFLATE with single byte."""
        from techcompressor.core import compress, decompress
        
        data = b"X"
        compressed = compress(data, algo="DEFLATE")
        decompressed = decompress(compressed, algo="DEFLATE")
        assert decompressed == data
    
    def test_deflate_repetitive_data(self):
        """Test DEFLATE with repetitive data (good for LZ77)."""
        from techcompressor.core import compress, decompress
        
        data = b"ABCDEFGHIJ" * 1000
        compressed = compress(data, algo="DEFLATE")
        
        # Should compress well due to LZ77
        assert len(compressed) < len(data) / 5
        
        decompressed = decompress(compressed, algo="DEFLATE")
        assert decompressed == data


class TestZstandardEdgeCases:
    """Test Zstandard algorithm edge cases."""
    
    def test_zstd_empty_data(self):
        """Test ZSTD with empty data."""
        from techcompressor.core import compress, decompress
        
        data = b""
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data
    
    def test_zstd_single_byte(self):
        """Test ZSTD with single byte."""
        from techcompressor.core import compress, decompress
        
        data = b"Z"
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data
    
    def test_zstd_large_data(self):
        """Test ZSTD with larger data."""
        from techcompressor.core import compress, decompress
        
        data = b"ZSTD is fast " * 10000
        compressed = compress(data, algo="ZSTD")
        
        # Should compress well
        assert len(compressed) < len(data) / 5
        
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data
    
    def test_zstd_alias(self):
        """Test ZSTANDARD alias."""
        from techcompressor.core import compress, decompress
        
        data = b"Test ZSTANDARD alias"
        compressed = compress(data, algo="ZSTANDARD")
        decompressed = decompress(compressed, algo="ZSTANDARD")
        assert decompressed == data


class TestBrotliEdgeCases:
    """Test Brotli algorithm edge cases."""
    
    def test_brotli_empty_data(self):
        """Test BROTLI with empty data."""
        from techcompressor.core import compress, decompress
        
        data = b""
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data
    
    def test_brotli_single_byte(self):
        """Test BROTLI with single byte."""
        from techcompressor.core import compress, decompress
        
        data = b"B"
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data
    
    def test_brotli_text_data(self):
        """Test BROTLI with text data (optimal case)."""
        from techcompressor.core import compress, decompress
        
        data = b"Brotli is great for text content and web compression" * 100
        compressed = compress(data, algo="BROTLI")
        
        # Should compress well
        assert len(compressed) < len(data)
        
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data


class TestAutoDecompression:
    """Test AUTO decompression with different formats."""
    
    def test_auto_decompress_lzw(self):
        """Test AUTO decompression of LZW data."""
        from techcompressor.core import compress, decompress
        
        data = b"LZW test data"
        compressed = compress(data, algo="LZW")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_decompress_huffman(self):
        """Test AUTO decompression of Huffman data."""
        from techcompressor.core import compress, decompress
        
        data = b"Huffman test data"
        compressed = compress(data, algo="HUFFMAN")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_decompress_deflate(self):
        """Test AUTO decompression of DEFLATE data."""
        from techcompressor.core import compress, decompress
        
        data = b"DEFLATE test data"
        compressed = compress(data, algo="DEFLATE")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_decompress_zstd(self):
        """Test AUTO decompression of ZSTD data."""
        from techcompressor.core import compress, decompress
        
        data = b"ZSTD test data"
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data
    
    def test_auto_decompress_brotli(self):
        """Test AUTO decompression of Brotli data."""
        from techcompressor.core import compress, decompress
        
        data = b"Brotli test data"
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data


class TestMagicHeaderDetection:
    """Test magic header detection in decompress."""
    
    def test_invalid_magic_header(self):
        """Test that invalid magic header raises error."""
        from techcompressor.core import decompress
        
        invalid_data = b"XXXX" + b"\x00" * 100
        
        with pytest.raises(ValueError):
            decompress(invalid_data, algo="AUTO")
    
    def test_truncated_data(self):
        """Test truncated data raises error."""
        from techcompressor.core import decompress
        
        truncated = b"TCZ"  # Incomplete magic
        
        with pytest.raises((ValueError, Exception)):
            decompress(truncated, algo="AUTO")


class TestEncryptionWithAlgorithms:
    """Test encryption combined with different algorithms."""
    
    def test_lzw_with_encryption(self):
        """Test LZW with encryption."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret LZW data"
        password = "testpass123"
        
        compressed = compress(data, algo="LZW", password=password)
        decompressed = decompress(compressed, algo="LZW", password=password)
        
        assert decompressed == data
    
    def test_huffman_with_encryption(self):
        """Test Huffman with encryption."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret Huffman data"
        password = "testpass456"
        
        compressed = compress(data, algo="HUFFMAN", password=password)
        decompressed = decompress(compressed, algo="HUFFMAN", password=password)
        
        assert decompressed == data
    
    def test_deflate_with_encryption(self):
        """Test DEFLATE with encryption."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret DEFLATE data"
        password = "testpass789"
        
        compressed = compress(data, algo="DEFLATE", password=password)
        decompressed = decompress(compressed, algo="DEFLATE", password=password)
        
        assert decompressed == data
    
    def test_zstd_with_encryption(self):
        """Test ZSTD with encryption."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret ZSTD data"
        password = "testpassABC"
        
        compressed = compress(data, algo="ZSTD", password=password)
        decompressed = decompress(compressed, algo="ZSTD", password=password)
        
        assert decompressed == data
    
    def test_brotli_with_encryption(self):
        """Test BROTLI with encryption."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret Brotli data"
        password = "testpassDEF"
        
        compressed = compress(data, algo="BROTLI", password=password)
        decompressed = decompress(compressed, algo="BROTLI", password=password)
        
        assert decompressed == data
    
    def test_auto_with_encryption(self):
        """Test AUTO with encryption."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret AUTO data " * 100
        password = "testpassGHI"
        
        compressed = compress(data, algo="AUTO", password=password)
        decompressed = decompress(compressed, algo="AUTO", password=password)
        
        assert decompressed == data


class TestWrongPassword:
    """Test wrong password handling."""
    
    def test_wrong_password_fails(self):
        """Test that wrong password raises error."""
        from techcompressor.core import compress, decompress
        
        data = b"Secret data"
        compressed = compress(data, algo="LZW", password="correct")
        
        with pytest.raises(Exception):
            decompress(compressed, algo="LZW", password="wrong")


class TestIsLikelyCompressed:
    """Test is_likely_compressed function."""
    
    def test_compressed_extension(self):
        """Test detection by file extension."""
        from techcompressor.core import is_likely_compressed
        
        assert is_likely_compressed(b"anything", "file.zip") == True
        assert is_likely_compressed(b"anything", "file.jpg") == True
        assert is_likely_compressed(b"anything", "file.png") == True
        assert is_likely_compressed(b"anything", "file.mp4") == True
        assert is_likely_compressed(b"anything", "file.pdf") == True
    
    def test_uncompressed_extension(self):
        """Test uncompressed file detection."""
        from techcompressor.core import is_likely_compressed
        
        # Text file with low entropy
        data = b"hello world " * 100
        assert is_likely_compressed(data, "file.txt") == False
    
    def test_random_data_high_entropy(self):
        """Test high entropy data detection."""
        from techcompressor.core import is_likely_compressed
        import os
        
        # Random data has high entropy
        data = os.urandom(4096)
        result = is_likely_compressed(data, "file.bin")
        # May or may not trigger entropy check depending on implementation
        # Just ensure it doesn't crash
        assert isinstance(result, bool)
