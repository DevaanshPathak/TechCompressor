"""
Tests for Zstandard (zstd) compression algorithm.

v2.0.0: Added Zstandard support for fast compression with excellent ratios.
"""

import pytest
from techcompressor.core import compress, decompress, MAGIC_HEADER_ZSTD


class TestZstdBasic:
    """Basic Zstandard compression tests."""

    def test_zstd_roundtrip(self):
        """Test basic Zstandard compress/decompress roundtrip."""
        data = b"Hello, Zstandard compression!" * 100
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data

    def test_zstd_magic_header(self):
        """Test that Zstandard output has correct magic header."""
        data = b"Test data for Zstandard"
        compressed = compress(data, algo="ZSTD")
        assert compressed[:4] == MAGIC_HEADER_ZSTD

    def test_zstd_compression_ratio(self):
        """Test that Zstandard achieves compression on repetitive data."""
        data = b"REPETITIVE DATA " * 1000  # 16KB of repetitive data
        compressed = compress(data, algo="ZSTD")
        # Zstandard should significantly compress repetitive data
        assert len(compressed) < len(data) * 0.5

    def test_zstd_empty_data(self):
        """Test Zstandard with empty input."""
        data = b""
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data

    def test_zstd_single_byte(self):
        """Test Zstandard with single byte input."""
        data = b"X"
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data

    def test_zstd_large_data(self):
        """Test Zstandard with larger data (1MB)."""
        data = b"Large data block " * 65536  # ~1MB
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data

    def test_zstd_binary_data(self):
        """Test Zstandard with binary data."""
        data = bytes(range(256)) * 100
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data

    def test_zstd_random_data(self):
        """Test Zstandard with random-looking data (low compressibility)."""
        import os
        data = os.urandom(10000)
        compressed = compress(data, algo="ZSTD")
        decompressed = decompress(compressed, algo="ZSTD")
        assert decompressed == data


class TestZstdWithEncryption:
    """Test Zstandard with AES-256-GCM encryption."""

    def test_zstd_encrypted_roundtrip(self):
        """Test Zstandard compression with encryption."""
        data = b"Secret data for Zstandard encryption test" * 50
        password = "test_password_123"
        
        compressed = compress(data, algo="ZSTD", password=password)
        decompressed = decompress(compressed, algo="ZSTD", password=password)
        
        assert decompressed == data

    def test_zstd_encrypted_wrong_password(self):
        """Test that wrong password fails decryption."""
        data = b"Secret data"
        compressed = compress(data, algo="ZSTD", password="correct")
        
        with pytest.raises(Exception):
            decompress(compressed, algo="ZSTD", password="wrong")

    def test_zstd_encrypted_no_password(self):
        """Test that encrypted data fails without password."""
        data = b"Secret data"
        compressed = compress(data, algo="ZSTD", password="secret")
        
        with pytest.raises(ValueError):
            decompress(compressed, algo="ZSTD", password=None)


class TestZstdAutoMode:
    """Test Zstandard in AUTO mode selection."""

    def test_zstd_available_in_auto(self):
        """Test that AUTO mode can select Zstandard."""
        # Use data that Zstandard handles well
        data = b"Auto mode test data " * 500
        compressed = compress(data, algo="AUTO")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data


class TestZstdAlgorithmAlias:
    """Test Zstandard algorithm name variants."""

    def test_zstd_alias_lowercase(self):
        """Test 'zstd' lowercase works."""
        data = b"Test data"
        compressed = compress(data, algo="zstd")
        decompressed = decompress(compressed, algo="zstd")
        assert decompressed == data

    def test_zstd_alias_zstandard(self):
        """Test 'ZSTANDARD' full name works."""
        data = b"Test data"
        compressed = compress(data, algo="ZSTANDARD")
        decompressed = decompress(compressed, algo="ZSTANDARD")
        assert decompressed == data
