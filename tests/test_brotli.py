"""
Tests for Brotli compression algorithm.

v2.0.0: Added Brotli support for web-optimized compression.
"""

import pytest
from techcompressor.core import compress, decompress, MAGIC_HEADER_BROTLI


class TestBrotliBasic:
    """Basic Brotli compression tests."""

    def test_brotli_roundtrip(self):
        """Test basic Brotli compress/decompress roundtrip."""
        data = b"Hello, Brotli compression!" * 100
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data

    def test_brotli_magic_header(self):
        """Test that Brotli output has correct magic header."""
        data = b"Test data for Brotli"
        compressed = compress(data, algo="BROTLI")
        assert compressed[:4] == MAGIC_HEADER_BROTLI

    def test_brotli_compression_ratio(self):
        """Test that Brotli achieves compression on repetitive data."""
        data = b"REPETITIVE DATA " * 1000  # 16KB of repetitive data
        compressed = compress(data, algo="BROTLI")
        # Brotli should significantly compress repetitive data
        assert len(compressed) < len(data) * 0.5

    def test_brotli_empty_data(self):
        """Test Brotli with empty input."""
        data = b""
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data

    def test_brotli_single_byte(self):
        """Test Brotli with single byte input."""
        data = b"X"
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data

    def test_brotli_large_data(self):
        """Test Brotli with larger data (1MB)."""
        data = b"Large data block " * 65536  # ~1MB
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data

    def test_brotli_binary_data(self):
        """Test Brotli with binary data."""
        data = bytes(range(256)) * 100
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data

    def test_brotli_random_data(self):
        """Test Brotli with random-looking data (low compressibility)."""
        import os
        data = os.urandom(10000)
        compressed = compress(data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        assert decompressed == data


class TestBrotliTextOptimization:
    """Test Brotli's text/web content optimization."""

    def test_brotli_html_compression(self):
        """Test Brotli on HTML-like content."""
        html = b"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Test Page</title>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to TechCompressor</h1>
                <p>This is a test paragraph with some text content.</p>
            </div>
        </body>
        </html>
        """ * 100
        
        compressed = compress(html, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        
        assert decompressed == html
        # Brotli should compress HTML well
        assert len(compressed) < len(html) * 0.2

    def test_brotli_json_compression(self):
        """Test Brotli on JSON-like content."""
        json_data = b"""
        {
            "name": "TechCompressor",
            "version": "2.0.0",
            "features": ["compression", "encryption", "archiving"],
            "algorithms": ["LZW", "Huffman", "DEFLATE", "Zstandard", "Brotli"]
        }
        """ * 100
        
        compressed = compress(json_data, algo="BROTLI")
        decompressed = decompress(compressed, algo="BROTLI")
        
        assert decompressed == json_data


class TestBrotliWithEncryption:
    """Test Brotli with AES-256-GCM encryption."""

    def test_brotli_encrypted_roundtrip(self):
        """Test Brotli compression with encryption."""
        data = b"Secret data for Brotli encryption test" * 50
        password = "test_password_123"
        
        compressed = compress(data, algo="BROTLI", password=password)
        decompressed = decompress(compressed, algo="BROTLI", password=password)
        
        assert decompressed == data

    def test_brotli_encrypted_wrong_password(self):
        """Test that wrong password fails decryption."""
        data = b"Secret data"
        compressed = compress(data, algo="BROTLI", password="correct")
        
        with pytest.raises(Exception):
            decompress(compressed, algo="BROTLI", password="wrong")

    def test_brotli_encrypted_no_password(self):
        """Test that encrypted data fails without password."""
        data = b"Secret data"
        compressed = compress(data, algo="BROTLI", password="secret")
        
        with pytest.raises(ValueError):
            decompress(compressed, algo="BROTLI", password=None)


class TestBrotliAutoMode:
    """Test Brotli in AUTO mode selection."""

    def test_brotli_available_in_auto(self):
        """Test that AUTO mode can select Brotli."""
        # Use data that Brotli handles well
        data = b"Auto mode test data " * 500
        compressed = compress(data, algo="AUTO")
        decompressed = decompress(compressed, algo="AUTO")
        assert decompressed == data


class TestBrotliAlgorithmName:
    """Test Brotli algorithm name variants."""

    def test_brotli_lowercase(self):
        """Test 'brotli' lowercase works."""
        data = b"Test data"
        compressed = compress(data, algo="brotli")
        decompressed = decompress(compressed, algo="brotli")
        assert decompressed == data

    def test_brotli_mixed_case(self):
        """Test 'Brotli' mixed case works."""
        data = b"Test data"
        compressed = compress(data, algo="Brotli")
        decompressed = decompress(compressed, algo="Brotli")
        assert decompressed == data
