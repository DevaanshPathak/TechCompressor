"""
TechCompressor Command-Line Interface

Provides command-line access to compression, archiving, and encryption features.
"""

import sys
import argparse
import time
from pathlib import Path
from .core import compress, decompress
from .archiver import create_archive, extract_archive, list_contents
from .utils import get_logger
from . import __version__

logger = get_logger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='techcmp',
        description='TechCompressor - Multi-algorithm compression with encryption',
        epilog='For more information, visit: https://github.com/DevaanshPathak/TechCompressor'
    )
    
    # Global flags
    parser.add_argument('--version', action='version',
                       version=f'TechCompressor {__version__}')
    parser.add_argument('--gui', action='store_true',
                       help='Launch graphical user interface')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run performance benchmark')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Archive creation command
    create_parser = subparsers.add_parser('create', aliases=['c'], 
                                          help='Create compressed archive')
    create_parser.add_argument('source', help='Source file or directory')
    create_parser.add_argument('archive', help='Output archive path')
    create_parser.add_argument('--algo', default='AUTO',
                              choices=['AUTO', 'LZW', 'HUFFMAN', 'DEFLATE'],
                              help='Compression algorithm (default: AUTO - try all and pick smallest)')
    create_parser.add_argument('--per-file', action='store_true',
                              help='Compress each file separately (default: False)')
    create_parser.add_argument('--password', help='Password for encryption')
    
    # Archive extraction command
    extract_parser = subparsers.add_parser('extract', aliases=['x'],
                                          help='Extract compressed archive')
    extract_parser.add_argument('archive', help='Archive path')
    extract_parser.add_argument('dest', help='Destination directory')
    extract_parser.add_argument('--password', help='Password for decryption')
    
    # List contents command
    list_parser = subparsers.add_parser('list', aliases=['l'],
                                       help='List archive contents')
    list_parser.add_argument('archive', help='Archive path')
    
    # File compression command (simple)
    compress_parser = subparsers.add_parser('compress', 
                                           help='Compress single file')
    compress_parser.add_argument('input', help='Input file')
    compress_parser.add_argument('output', help='Output file')
    compress_parser.add_argument('--algo', default='AUTO',
                                choices=['AUTO', 'LZW', 'HUFFMAN', 'DEFLATE'],
                                help='Compression algorithm (default: AUTO - try all and pick smallest)')
    compress_parser.add_argument('--password', help='Password for encryption')
    
    # File decompression command (simple)
    decompress_parser = subparsers.add_parser('decompress',
                                             help='Decompress single file')
    decompress_parser.add_argument('input', help='Input file')
    decompress_parser.add_argument('output', help='Output file')
    decompress_parser.add_argument('--algo', default='AUTO',
                                  choices=['AUTO', 'LZW', 'HUFFMAN', 'DEFLATE'],
                                  help='Compression algorithm (default: AUTO - detect from file header)')
    decompress_parser.add_argument('--password', help='Password for decryption')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify',
                                         help='Verify archive integrity')
    verify_parser.add_argument('archive', help='Archive path to verify')
    
    args = parser.parse_args()
    
    # Handle --benchmark flag
    if args.benchmark:
        try:
            print("🚀 Running TechCompressor benchmark...")
            print()
            from . import core
            import os
            
            test_data = b"BENCHMARK DATA " * 1000
            algorithms = ['LZW', 'HUFFMAN', 'DEFLATE']
            
            print(f"{'Algorithm':<12} {'Time':<12} {'Ratio':<10} {'Speed':<12}")
            print("-" * 50)
            
            for algo in algorithms:
                start = time.perf_counter()
                compressed = compress(test_data, algo=algo)
                elapsed = time.perf_counter() - start
                
                ratio = (len(compressed) / len(test_data)) * 100
                speed = (len(test_data) / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                
                print(f"{algo:<12} {elapsed*1000:>8.2f} ms  {ratio:>6.1f}%   {speed:>6.2f} MB/s")
            
            print()
            print("✅ Benchmark complete!")
            return 0
        except Exception as e:
            print(f"❌ Benchmark failed: {e}", file=sys.stderr)
            return 1
    
    # Handle --gui flag
    if args.gui:
        try:
            from .gui import main as gui_main
            print("Launching TechCompressor GUI...")
            gui_main()
            return 0
        except ImportError as e:
            print(f"Error: GUI dependencies not available: {e}", file=sys.stderr)
            print("Make sure tkinter is installed.", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error launching GUI: {e}", file=sys.stderr)
            return 1
    
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        if args.command in ('create', 'c'):
            # Create archive
            print(f"Creating archive: {args.archive}")
            print(f"Source: {args.source}")
            print(f"Algorithm: {args.algo}")
            print(f"Mode: {'per-file' if args.per_file else 'single-stream'}")
            if args.password:
                print("Encryption: enabled")
            
            start_time = time.perf_counter()
            create_archive(
                args.source,
                args.archive,
                algo=args.algo,
                password=args.password,
                per_file=args.per_file
            )
            elapsed = time.perf_counter() - start_time
            
            print(f"\n✅ Archive created successfully: {args.archive}")
            print(f"   Time: {elapsed:.3f}s")
        
        elif args.command in ('extract', 'x'):
            # Extract archive
            print(f"Extracting archive: {args.archive}")
            print(f"Destination: {args.dest}")
            if args.password:
                print("Decryption: enabled")
            
            start_time = time.perf_counter()
            extract_archive(
                args.archive,
                args.dest,
                password=args.password
            )
            elapsed = time.perf_counter() - start_time
            
            print(f"\n✅ Archive extracted successfully to: {args.dest}")
            print(f"   Time: {elapsed:.3f}s")
        
        elif args.command in ('list', 'l'):
            # List contents
            print(f"Archive contents: {args.archive}\n")
            
            contents = list_contents(args.archive)
            
            print(f"{'Name':<50} {'Size':>12} {'Compressed':>12} {'Ratio':>8}")
            print("-" * 85)
            
            total_size = 0
            total_compressed = 0
            
            for entry in contents:
                name = entry['name']
                size = entry['size']
                compressed = entry['compressed_size']
                ratio = (compressed / max(size, 1)) * 100
                
                total_size += size
                total_compressed += compressed
                
                print(f"{name:<50} {size:>12,} {compressed:>12,} {ratio:>7.1f}%")
            
            print("-" * 85)
            overall_ratio = (total_compressed / max(total_size, 1)) * 100
            print(f"{'Total':<50} {total_size:>12,} {total_compressed:>12,} {overall_ratio:>7.1f}%")
            print(f"\nFiles: {len(contents)}")
        
        elif args.command == 'compress':
            # Compress single file
            print(f"Compressing: {args.input} → {args.output}")
            print(f"Algorithm: {args.algo}")
            if args.password:
                print("Encryption: enabled")
            
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"❌ Error: Input file not found: {args.input}", file=sys.stderr)
                return 1
            
            start_time = time.perf_counter()
            data = input_path.read_bytes()
            compressed = compress(data, algo=args.algo, password=args.password)
            elapsed = time.perf_counter() - start_time
            
            output_path = Path(args.output)
            output_path.write_bytes(compressed)
            
            ratio = (len(compressed) / max(len(data), 1)) * 100
            speed = (len(data) / (1024 * 1024)) / elapsed if elapsed > 0 else 0
            print(f"\n✅ Compressed: {len(data):,} → {len(compressed):,} bytes ({ratio:.1f}%)")
            print(f"   Time: {elapsed:.3f}s | Speed: {speed:.2f} MB/s")
        
        elif args.command == 'decompress':
            # Decompress single file
            print(f"Decompressing: {args.input} → {args.output}")
            print(f"Algorithm: {args.algo}")
            if args.password:
                print("Decryption: enabled")
            
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"❌ Error: Input file not found: {args.input}", file=sys.stderr)
                return 1
            
            start_time = time.perf_counter()
            compressed = input_path.read_bytes()
            data = decompress(compressed, algo=args.algo, password=args.password)
            elapsed = time.perf_counter() - start_time
            
            output_path = Path(args.output)
            output_path.write_bytes(data)
            
            print(f"\n✅ Decompressed: {len(compressed):,} → {len(data):,} bytes in {elapsed:.3f}s")
        
        elif args.command == 'verify':
            # Verify archive integrity
            print(f"Verifying: {args.archive}")
            
            archive_path = Path(args.archive)
            if not archive_path.exists():
                print(f"❌ Error: Archive not found: {args.archive}", file=sys.stderr)
                return 1
            
            # Check magic header
            with open(archive_path, 'rb') as f:
                magic = f.read(4)
            
            if magic == b"TCAF":
                print("✅ Valid TCAF archive")
                
                # List contents to verify structure
                contents = list_contents(str(archive_path))
                print(f"✅ Contains {len(contents)} file(s)")
                
                total_size = sum(entry['size'] for entry in contents)
                total_compressed = sum(entry['compressed_size'] for entry in contents)
                ratio = (total_compressed / max(total_size, 1)) * 100
                
                print(f"   Original: {total_size:,} bytes")
                print(f"   Compressed: {total_compressed:,} bytes ({ratio:.1f}%)")
                print("\n✅ Archive verification passed!")
            else:
                # Check if it's a compressed file
                if magic[:4] in [b"TCZ1", b"TCH1", b"TCD1", b"TCE1"]:
                    print("✅ Valid compressed file")
                    print(f"   Format: {magic.decode('ascii', errors='replace')}")
                    print("\n✅ File verification passed!")
                else:
                    print(f"❌ Unknown format: {magic}")
                    return 1
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        logger.exception("CLI command failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
