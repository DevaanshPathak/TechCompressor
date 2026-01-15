"""
Release smoke tests - Quick validation for release candidates.

These tests provide fast sanity checks to ensure core functionality works
without running the full test suite. Run before building release artifacts.
"""

import os
import tempfile
from pathlib import Path
import pytest
from techcompressor.core import compress, decompress
from techcompressor.archiver import create_archive, extract_archive


def test_smoke_lzw_roundtrip():
    """Quick LZW compression roundtrip test."""
    data = b"SMOKE TEST DATA" * 10
    compressed = compress(data, algo="LZW")
    decompressed = decompress(compressed, algo="LZW")
    assert decompressed == data
    assert len(compressed) < len(data)  # Should compress


def test_smoke_huffman_roundtrip():
    """Quick Huffman compression roundtrip test."""
    data = b"AAABBBCCC" * 10
    compressed = compress(data, algo="HUFFMAN")
    decompressed = decompress(compressed, algo="HUFFMAN")
    assert decompressed == data


def test_smoke_deflate_roundtrip():
    """Quick DEFLATE compression roundtrip test."""
    data = b"DEFLATE TEST" * 20
    compressed = compress(data, algo="DEFLATE")
    decompressed = decompress(compressed, algo="DEFLATE")
    assert decompressed == data
    assert len(compressed) < len(data)  # Should compress


def test_smoke_zstd_roundtrip():
    """Quick Zstandard compression roundtrip test (v2.0.0)."""
    data = b"ZSTD TEST DATA" * 20
    compressed = compress(data, algo="ZSTD")
    decompressed = decompress(compressed, algo="ZSTD")
    assert decompressed == data
    assert len(compressed) < len(data)  # Should compress


def test_smoke_brotli_roundtrip():
    """Quick Brotli compression roundtrip test (v2.0.0)."""
    data = b"BROTLI TEST DATA" * 20
    compressed = compress(data, algo="BROTLI")
    decompressed = decompress(compressed, algo="BROTLI")
    assert decompressed == data
    assert len(compressed) < len(data)  # Should compress


def test_smoke_encryption():
    """Quick encryption roundtrip test."""
    data = b"SECRET DATA" * 5
    password = "test_password_123"
    
    # Compress and encrypt
    compressed = compress(data, algo="LZW", password=password)
    
    # Verify encrypted (TCE1 header)
    assert compressed[:4] == b"TCE1"
    
    # Decrypt and decompress
    decompressed = decompress(compressed, algo="LZW", password=password)
    assert decompressed == data


def test_smoke_wrong_password():
    """Quick test for wrong password detection."""
    data = b"test data"
    password = "correct_password"
    wrong_password = "wrong_password"
    
    compressed = compress(data, algo="LZW", password=password)
    
    with pytest.raises(ValueError, match="Invalid password or corrupted data"):
        decompress(compressed, algo="LZW", password=wrong_password)


def test_smoke_magic_header_validation():
    """Quick test for magic header validation."""
    data = b"test"
    
    # LZW compressed data
    lzw_data = compress(data, algo="LZW")
    
    # Try to decompress with wrong algorithm
    with pytest.raises(ValueError, match="Invalid magic header"):
        decompress(lzw_data, algo="HUFFMAN")


def test_smoke_archive_creation():
    """Quick archive creation and extraction test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test files
        source_dir = tmpdir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("File 1 content")
        (source_dir / "file2.txt").write_text("File 2 content")
        
        # Create archive
        archive_path = tmpdir / "test.tc"
        create_archive(
            str(source_dir),
            str(archive_path),
            algo="LZW",
            per_file=True
        )
        
        assert archive_path.exists()
        assert archive_path.stat().st_size > 0
        
        # Extract archive
        dest_dir = tmpdir / "dest"
        dest_dir.mkdir()
        extract_archive(str(archive_path), str(dest_dir))
        
        # Verify extracted files
        assert (dest_dir / "file1.txt").read_text() == "File 1 content"
        assert (dest_dir / "file2.txt").read_text() == "File 2 content"


def test_smoke_encrypted_archive():
    """Quick encrypted archive test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test file
        source_dir = tmpdir / "source"
        source_dir.mkdir()
        (source_dir / "secret.txt").write_text("Secret content")
        
        # Create encrypted archive
        archive_path = tmpdir / "encrypted.tc"
        password = "secure_password"
        create_archive(
            str(source_dir),
            str(archive_path),
            algo="DEFLATE",
            password=password,
            per_file=True
        )
        
        # Extract with correct password
        dest_dir = tmpdir / "dest"
        dest_dir.mkdir()
        extract_archive(str(archive_path), str(dest_dir), password=password)
        
        assert (dest_dir / "secret.txt").read_text() == "Secret content"


def test_smoke_empty_data():
    """Quick test for edge case: empty data."""
    data = b""
    compressed = compress(data, algo="LZW")
    decompressed = decompress(compressed, algo="LZW")
    assert decompressed == data


def test_smoke_single_byte():
    """Quick test for edge case: single byte."""
    data = b"X"
    compressed = compress(data, algo="HUFFMAN")
    decompressed = decompress(compressed, algo="HUFFMAN")
    assert decompressed == data


def test_smoke_large_data():
    """Quick test with moderately large data (1MB)."""
    data = b"X" * (1024 * 1024)  # 1MB
    compressed = compress(data, algo="DEFLATE")
    decompressed = decompress(compressed, algo="DEFLATE")
    assert decompressed == data
    # Should compress very well (repetitive data)
    assert len(compressed) < len(data) / 100  # < 1% of original


def test_smoke_all_algorithms():
    """Quick test ensuring all algorithms work."""
    data = b"Test all algorithms" * 10
    algorithms = ["LZW", "HUFFMAN", "DEFLATE"]
    
    for algo in algorithms:
        compressed = compress(data, algo=algo)
        decompressed = decompress(compressed, algo=algo)
        assert decompressed == data, f"{algo} failed"


def test_smoke_version():
    """Quick test that version is accessible."""
    import techcompressor
    assert hasattr(techcompressor, '__version__')
    assert techcompressor.__version__ == "2.0.0"


def test_smoke_cli_imports():
    """Quick test that CLI modules import without errors."""
    from techcompressor import cli
    from techcompressor import gui
    
    assert hasattr(cli, 'main')
    assert hasattr(gui, 'main')


if __name__ == '__main__':
    # Run smoke tests directly
    pytest.main([__file__, '-v', '--tb=short'])
