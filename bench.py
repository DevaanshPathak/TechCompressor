#!/usr/bin/env python3
"""
TechCompressor Benchmark Suite

Compares speed and compression ratios across all algorithms.
Measures encryption overhead and provides performance insights.
"""

import time
import os
import sys
from pathlib import Path
from techcompressor.core import compress, decompress
from techcompressor.archiver import create_archive, extract_archive
import tempfile
import shutil


def format_size(bytes_val):
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_time(seconds):
    """Format time to human-readable string."""
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f} μs"
    elif seconds < 1.0:
        return f"{seconds * 1000:.2f} ms"
    else:
        return f"{seconds:.3f} s"


def generate_test_data():
    """Generate various types of test data."""
    return {
        'repetitive': b'A' * 10000,
        'text': (b"The quick brown fox jumps over the lazy dog. " * 200),
        'random': os.urandom(10000),
        'structured': (b'{"name":"test","value":123,"active":true}' * 100),
        'binary': bytes(range(256)) * 40,
    }


def benchmark_algorithm(name, data, algo, with_password=False):
    """Benchmark a single algorithm."""
    password = "test_password_123" if with_password else None
    
    # Compression
    start = time.perf_counter()
    compressed = compress(data, algo=algo, password=password)
    compress_time = time.perf_counter() - start
    
    # Decompression
    start = time.perf_counter()
    decompressed = decompress(compressed, algo=algo, password=password)
    decompress_time = time.perf_counter() - start
    
    # Verify correctness
    assert decompressed == data, f"Data mismatch for {algo}"
    
    original_size = len(data)
    compressed_size = len(compressed)
    ratio = (compressed_size / original_size) * 100
    speed_mbps = (original_size / (1024 * 1024)) / compress_time if compress_time > 0 else 0
    
    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'ratio': ratio,
        'compress_time': compress_time,
        'decompress_time': decompress_time,
        'speed_mbps': speed_mbps,
    }


def benchmark_all():
    """Run complete benchmark suite."""
    print("=" * 80)
    print("TechCompressor Benchmark Suite".center(80))
    print("=" * 80)
    print()
    
    test_data = generate_test_data()
    algorithms = ['LZW', 'HUFFMAN', 'DEFLATE']
    
    for data_type, data in test_data.items():
        print(f"\n📊 {data_type.upper()} DATA ({format_size(len(data))})")
        print("-" * 80)
        print(f"{'Algorithm':<12} {'Ratio':<10} {'Compressed':<15} {'Comp Time':<12} {'Decomp Time':<12} {'Speed':<12}")
        print("-" * 80)
        
        for algo in algorithms:
            result = benchmark_algorithm(data_type, data, algo, with_password=False)
            
            print(f"{algo:<12} "
                  f"{result['ratio']:>6.1f}%   "
                  f"{format_size(result['compressed_size']):<15} "
                  f"{format_time(result['compress_time']):<12} "
                  f"{format_time(result['decompress_time']):<12} "
                  f"{result['speed_mbps']:.2f} MB/s")
    
    # Encryption overhead test
    print("\n\n🔒 ENCRYPTION OVERHEAD TEST")
    print("-" * 80)
    print(f"{'Algorithm':<12} {'No Pass':<12} {'With Pass':<12} {'Overhead':<12}")
    print("-" * 80)
    
    test_data_crypto = b"SECRET DATA " * 1000
    for algo in algorithms:
        # Without password
        start = time.perf_counter()
        compress(test_data_crypto, algo=algo)
        time_no_pass = time.perf_counter() - start
        
        # With password
        start = time.perf_counter()
        compress(test_data_crypto, algo=algo, password="test123")
        time_with_pass = time.perf_counter() - start
        
        overhead = ((time_with_pass - time_no_pass) / time_no_pass) * 100 if time_no_pass > 0 else 0
        
        print(f"{algo:<12} "
              f"{format_time(time_no_pass):<12} "
              f"{format_time(time_with_pass):<12} "
              f"{overhead:>6.1f}%")
    
    # Archive benchmark
    print("\n\n📦 ARCHIVE PERFORMANCE")
    print("-" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test directory structure
        test_dir = Path(tmpdir) / "test_data"
        test_dir.mkdir()
        
        for i in range(10):
            (test_dir / f"file{i}.txt").write_bytes(b"Test content " * 100)
        
        archive_path = Path(tmpdir) / "test.tc"
        extract_path = Path(tmpdir) / "extracted"
        
        print(f"{'Mode':<15} {'Algorithm':<12} {'Time':<12} {'Size':<15}")
        print("-" * 80)
        
        for algo in algorithms:
            for per_file in [True, False]:
                mode = "Per-file" if per_file else "Single-stream"
                
                # Create archive
                start = time.perf_counter()
                create_archive(str(test_dir), str(archive_path), algo=algo, per_file=per_file)
                create_time = time.perf_counter() - start
                
                archive_size = archive_path.stat().st_size
                
                print(f"{mode:<15} "
                      f"{algo:<12} "
                      f"{format_time(create_time):<12} "
                      f"{format_size(archive_size):<15}")
                
                # Cleanup
                archive_path.unlink()
    
    print("\n" + "=" * 80)
    print("✅ Benchmark complete!".center(80))
    print("=" * 80)


def quick_bench():
    """Quick performance sanity check."""
    print("🚀 Quick Performance Check...")
    data = b"BENCHMARK DATA " * 1000
    
    for algo in ['LZW', 'HUFFMAN', 'DEFLATE']:
        start = time.perf_counter()
        compressed = compress(data, algo=algo)
        elapsed = time.perf_counter() - start
        
        ratio = (len(compressed) / len(data)) * 100
        print(f"  {algo:<10} {format_time(elapsed):<12} Ratio: {ratio:>6.1f}%")
    
    print("✅ Performance check passed!")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_bench()
    else:
        benchmark_all()
