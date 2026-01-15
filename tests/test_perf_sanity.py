"""
Performance sanity tests for TechCompressor

Ensures compression operations complete within reasonable time limits.
"""

import pytest
import time
import os
from techcompressor.core import compress, decompress


def test_lzw_performance():
    """Test LZW compression completes within time limit."""
    data = b"PERFORMANCE TEST " * 500
    
    start = time.perf_counter()
    compressed = compress(data, algo="LZW")
    decompressed = decompress(compressed, algo="LZW")
    elapsed = time.perf_counter() - start
    
    assert decompressed == data
    assert elapsed < 2.0, f"LZW took {elapsed:.3f}s (limit: 2.0s)"
    assert len(compressed) < len(data), "LZW should compress repetitive data"


def test_huffman_performance():
    """Test Huffman compression completes within time limit."""
    data = b"ABCABCABC" * 500
    
    start = time.perf_counter()
    compressed = compress(data, algo="HUFFMAN")
    decompressed = decompress(compressed, algo="HUFFMAN")
    elapsed = time.perf_counter() - start
    
    assert decompressed == data
    assert elapsed < 2.0, f"Huffman took {elapsed:.3f}s (limit: 2.0s)"
    assert len(compressed) < len(data), "Huffman should compress repetitive data"


def test_deflate_performance():
    """Test DEFLATE compression completes within time limit."""
    data = b"DEFLATE BENCHMARK " * 500
    
    start = time.perf_counter()
    compressed = compress(data, algo="DEFLATE")
    decompressed = decompress(compressed, algo="DEFLATE")
    elapsed = time.perf_counter() - start
    
    assert decompressed == data
    assert elapsed < 2.0, f"DEFLATE took {elapsed:.3f}s (limit: 2.0s)"


@pytest.mark.skipif(os.environ.get('CI') == 'true', reason="Skipped on CI - PBKDF2 timing varies too much")
def test_encryption_overhead():
    """Test that encryption adds reasonable overhead."""
    data = b"ENCRYPTION TEST " * 500
    password = "benchmark_pass"
    
    # Warmup to prime key derivation cache
    compress(data, algo="LZW", password=password)
    
    # Without encryption
    start = time.perf_counter()
    compress(data, algo="LZW")
    time_no_encrypt = time.perf_counter() - start
    
    # With encryption (after warmup)
    start = time.perf_counter()
    compress(data, algo="LZW", password=password)
    time_with_encrypt = time.perf_counter() - start
    
    # Encryption should add < 3000% overhead (PBKDF2 is intentionally slow for security)
    # The overhead varies significantly on different systems due to PBKDF2 key derivation
    overhead = ((time_with_encrypt - time_no_encrypt) / time_no_encrypt) * 100
    assert overhead < 3000, f"Encryption overhead {overhead:.1f}% exceeds 3000%"
    
    # Just verify it works correctly
    compressed = compress(data, algo="LZW", password=password)
    decompressed = decompress(compressed, algo="LZW", password=password)
    assert decompressed == data


def test_large_data_performance():
    """Test compression of larger data completes reasonably."""
    # 100KB of data
    data = b"LARGE DATA TEST " * 6250
    
    start = time.perf_counter()
    compressed = compress(data, algo="DEFLATE")
    decompressed = decompress(compressed, algo="DEFLATE")
    elapsed = time.perf_counter() - start
    
    assert decompressed == data
    assert elapsed < 5.0, f"Large data compression took {elapsed:.3f}s (limit: 5.0s)"


def test_compression_ratio():
    """Test that algorithms achieve reasonable compression ratios."""
    data = b"RATIO TEST " * 1000
    
    for algo in ['LZW', 'HUFFMAN', 'DEFLATE']:
        compressed = compress(data, algo=algo)
        ratio = (len(compressed) / len(data)) * 100
        
        # Repetitive data should compress well
        assert ratio < 80, f"{algo} ratio {ratio:.1f}% should be < 80% for repetitive data"
