"""
TechCompressor Archive Module

Manages folder compression, multi-file archives, and metadata preservation.
"""

import os
import struct
import io
import tarfile
from pathlib import Path
from typing import List, Dict, Callable
from .core import compress, decompress
from .utils import get_logger

logger = get_logger(__name__)

# Archive format constants
MAGIC_HEADER_ARCHIVE = b"TCAF"  # TechCompressor Archive Format
ARCHIVE_VERSION = 2  # v2: Added STORED mode for incompressible files
CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB for streaming

# Algorithm ID mapping (0 = STORED for uncompressed data)
ALGO_MAP = {"STORED": 0, "LZW": 1, "HUFFMAN": 2, "DEFLATE": 3, "ARITHMETIC": 4}
ALGO_REVERSE = {v: k for k, v in ALGO_MAP.items()}


def _validate_path(path: Path, allow_symlink: bool = False) -> None:
    """
    Validate path for safety.
    
    Args:
        path: Path to validate
        allow_symlink: Whether to allow symlinks
    
    Raises:
        ValueError: If path is invalid or unsafe
    """
    if not allow_symlink and path.is_symlink():
        raise ValueError(f"Symlinks not allowed: {path}")
    
    # Check for path traversal attempts
    try:
        path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {path}") from e


def _check_recursion(source_path: Path, archive_path: Path) -> None:
    """
    Check if archive would be created inside source directory (recursion).
    
    Args:
        source_path: Source directory
        archive_path: Target archive path
    
    Raises:
        ValueError: If archive is inside source
    """
    try:
        archive_abs = archive_path.resolve()
        source_abs = source_path.resolve()
        
        # Check if archive is inside source tree
        try:
            archive_abs.relative_to(source_abs)
            # If relative_to succeeds, archive IS inside source - error!
            raise ValueError(
                f"Archive path {archive_path} is inside source directory {source_path}. "
                "This would cause infinite recursion."
            )
        except ValueError as e:
            # relative_to raises ValueError if not relative - this is good
            # But re-raise if it's our error message
            if "infinite recursion" in str(e):
                raise
            # Otherwise, archive is outside source, which is fine
            pass
    except (OSError, RuntimeError) as e:
        logger.warning(f"Could not check recursion: {e}")


def _sanitize_extract_path(entry_name: str, dest_path: Path) -> Path:
    """
    Sanitize extraction path to prevent directory traversal attacks.
    
    Args:
        entry_name: Entry name from archive
        dest_path: Destination base path
    
    Returns:
        Safe extraction path
    
    Raises:
        ValueError: If path attempts traversal
    """
    # Remove any leading slashes or drive letters
    entry_name = entry_name.lstrip('/\\')
    if len(entry_name) > 1 and entry_name[1] == ':':
        entry_name = entry_name[2:].lstrip('/\\')
    
    # Build target path
    target = (dest_path / entry_name).resolve()
    dest_resolved = dest_path.resolve()
    
    # Ensure target is inside destination
    try:
        target.relative_to(dest_resolved)
    except ValueError:
        raise ValueError(
            f"Path traversal attempt detected: {entry_name} "
            f"would extract outside destination {dest_path}"
        )
    
    return target


def create_archive(
    source_path: str | Path,
    archive_path: str | Path,
    algo: str = "LZW",
    password: str | None = None,
    per_file: bool = True,
    progress_callback: Callable[[int, int], None] | None = None
) -> None:
    """
    Create compressed archive from directory or file.
    
    Args:
        source_path: Path to file or directory to compress
        archive_path: Path for output archive
        algo: Compression algorithm ("LZW", "HUFFMAN", "DEFLATE")
        password: Optional password for encryption
        per_file: If True, compress each file separately (random access).
                  If False, compress entire stream (better ratio).
        progress_callback: Optional callback(current, total) for progress
    
    Raises:
        ValueError: If paths are invalid or recursion detected
        FileNotFoundError: If source doesn't exist
    """
    source_path = Path(source_path)
    archive_path = Path(archive_path)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source path not found: {source_path}")
    
    # Check for recursion
    if source_path.is_dir():
        _check_recursion(source_path, archive_path)
    
    # Gather files to archive
    files_to_archive = []
    
    if source_path.is_file():
        files_to_archive.append((source_path, source_path.name))
    else:
        # Walk directory
        for root, dirs, files in os.walk(source_path):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                
                # Skip symlinks
                if file_path.is_symlink():
                    logger.warning(f"Skipping symlink: {file_path}")
                    continue
                
                # Calculate relative path
                rel_path = file_path.relative_to(source_path)
                files_to_archive.append((file_path, str(rel_path)))
    
    if not files_to_archive:
        raise ValueError(f"No files found to archive in {source_path}")
    
    logger.info(f"Creating archive with {len(files_to_archive)} files using {algo}")
    logger.info(f"Mode: {'per-file' if per_file else 'single-stream'} compression")
    if password:
        logger.info("Encryption enabled")
    
    # Try to import tqdm for progress
    tqdm = None
    try:
        from tqdm import tqdm as tqdm_cls
        tqdm = tqdm_cls
    except ImportError:
        pass
    
    total_original_size = 0
    total_compressed_size = 0
    
    # Create archive
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(archive_path, 'wb') as f:
        # Write header
        f.write(MAGIC_HEADER_ARCHIVE)
        f.write(struct.pack('B', ARCHIVE_VERSION))
        f.write(struct.pack('B', 1 if per_file else 0))  # per_file flag
        f.write(struct.pack('B', 1 if password else 0))  # encrypted flag
        
        # Reserve space for entry table offset (will update later)
        entry_table_offset_pos = f.tell()
        f.write(struct.pack('>Q', 0))  # 8 bytes for offset
        
        entries = []
        
        if per_file:
            # Per-file compression mode
            iterator = tqdm(files_to_archive, desc="Archiving", unit="file") if tqdm else files_to_archive
            
            for file_path, rel_name in iterator:
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size
                    mtime = int(stat.st_mtime)
                    mode = stat.st_mode & 0o777  # Permission bits only
                    
                    # Read and compress file
                    with open(file_path, 'rb') as in_f:
                        file_data = in_f.read()
                    
                    compressed_data = compress(file_data, algo=algo, password=password)
                    
                    # Choose between compressed or stored based on size
                    # Note: Never use STORED with encryption - encrypted data must be decrypted
                    actual_algo = algo.upper()
                    actual_data = compressed_data
                    
                    if not password and len(compressed_data) >= len(file_data) and len(file_data) > 0:
                        # Compression failed and no encryption - store original data uncompressed
                        actual_data = file_data
                        actual_algo = "STORED"
                        ratio = len(compressed_data) / len(file_data)
                        logger.info(
                            f"File {rel_name}: compression expanded data "
                            f"({len(file_data)} → {len(compressed_data)} bytes, {ratio*100:.1f}%) - "
                            f"storing uncompressed instead"
                        )
                    
                    # Write entry header
                    entry_offset = f.tell()
                    rel_name_bytes = rel_name.encode('utf-8')
                    
                    f.write(struct.pack('>H', len(rel_name_bytes)))  # filename length
                    f.write(rel_name_bytes)  # filename
                    f.write(struct.pack('>Q', file_size))  # original size
                    f.write(struct.pack('>Q', mtime))  # modification time
                    f.write(struct.pack('>I', mode))  # file mode
                    f.write(struct.pack('>Q', len(actual_data)))  # stored size
                    f.write(struct.pack('B', ALGO_MAP.get(actual_algo, 1)))  # algo ID
                    
                    # Write data (compressed or stored)
                    f.write(actual_data)
                    
                    entries.append({
                        'name': rel_name,
                        'size': file_size,
                        'compressed_size': len(actual_data),
                        'algo': actual_algo,
                        'mtime': mtime,
                        'mode': mode,
                        'offset': entry_offset
                    })
                    
                    total_original_size += file_size
                    total_compressed_size += len(actual_data)
                    
                    if progress_callback:
                        progress_callback(len(entries), len(files_to_archive))
                
                except Exception as e:
                    logger.error(f"Failed to archive {file_path}: {e}")
                    raise
        
        else:
            # Single-stream compression mode
            logger.info("Creating combined data stream")
            
            # Build in-memory tar-like structure
            stream = io.BytesIO()
            
            iterator = tqdm(files_to_archive, desc="Building stream", unit="file") if tqdm else files_to_archive
            
            for file_path, rel_name in iterator:
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size
                    mtime = int(stat.st_mtime)
                    mode = stat.st_mode & 0o777
                    
                    # Write file header to stream
                    rel_name_bytes = rel_name.encode('utf-8')
                    stream.write(struct.pack('>H', len(rel_name_bytes)))
                    stream.write(rel_name_bytes)
                    stream.write(struct.pack('>Q', file_size))
                    stream.write(struct.pack('>Q', mtime))
                    stream.write(struct.pack('>I', mode))
                    
                    # Write file data
                    with open(file_path, 'rb') as in_f:
                        file_data = in_f.read()
                        stream.write(file_data)
                    
                    entries.append({
                        'name': rel_name,
                        'size': file_size,
                        'compressed_size': 0,  # Will update after compression
                        'mtime': mtime,
                        'mode': mode,
                        'offset': 0
                    })
                    
                    total_original_size += file_size
                
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    raise
            
            # Compress entire stream
            logger.info(f"Compressing stream: {total_original_size} bytes")
            stream_data = stream.getvalue()
            compressed_stream = compress(stream_data, algo=algo, password=password)
            
            # Choose between compressed or stored based on size
            # Note: Never use STORED with encryption - encrypted data must be decrypted
            actual_algo = algo.upper()
            actual_data = compressed_stream
            
            if not password and len(compressed_stream) >= len(stream_data) and len(stream_data) > 0:
                # Compression failed and no encryption - store original stream uncompressed
                actual_data = stream_data
                actual_algo = "STORED"
                ratio = len(compressed_stream) / len(stream_data)
                logger.info(
                    f"Stream compression expanded data "
                    f"({len(stream_data)} → {len(compressed_stream)} bytes, {ratio*100:.1f}%) - "
                    f"storing uncompressed instead"
                )
            
            total_compressed_size = len(actual_data)
            
            # Write single entry for entire stream
            entry_offset = f.tell()
            f.write(struct.pack('>Q', len(actual_data)))  # stored size
            f.write(struct.pack('B', ALGO_MAP.get(actual_algo, 1)))  # algo ID
            f.write(actual_data)
            
            # Update compressed sizes in entries
            for entry in entries:
                entry['compressed_size'] = total_compressed_size
                entry['offset'] = entry_offset
                entry['algo'] = actual_algo
        
        # Write entry table
        entry_table_offset = f.tell()
        f.write(struct.pack('>I', len(entries)))  # number of entries
        
        for entry in entries:
            name_bytes = entry['name'].encode('utf-8')
            f.write(struct.pack('>H', len(name_bytes)))
            f.write(name_bytes)
            f.write(struct.pack('>Q', entry['size']))
            f.write(struct.pack('>Q', entry['compressed_size']))
            f.write(struct.pack('>Q', entry['mtime']))
            f.write(struct.pack('>I', entry['mode']))
            f.write(struct.pack('>Q', entry['offset']))
            # v2 format: include algorithm ID in entry table
            algo_id = ALGO_MAP.get(entry.get('algo', 'LZW'), 1)
            f.write(struct.pack('B', algo_id))
        
        # Update entry table offset in header
        f.seek(entry_table_offset_pos)
        f.write(struct.pack('>Q', entry_table_offset))
    
    archive_size = archive_path.stat().st_size
    ratio = (total_compressed_size / max(total_original_size, 1)) * 100
    
    logger.info(f"Archive created: {archive_path}")
    logger.info(f"Original size: {total_original_size:,} bytes")
    logger.info(f"Compressed size: {total_compressed_size:,} bytes ({ratio:.1f}%)")
    logger.info(f"Archive size: {archive_size:,} bytes")
    logger.info(f"Files archived: {len(entries)}")


def extract_archive(
    archive_path: str | Path,
    dest_path: str | Path,
    password: str | None = None,
    progress_callback: Callable[[int, int], None] | None = None
) -> None:
    """
    Extract compressed archive to directory.
    
    Args:
        archive_path: Path to archive file
        dest_path: Destination directory for extraction
        password: Optional password for decryption
        progress_callback: Optional callback(current, total) for progress
    
    Raises:
        ValueError: If archive is corrupted or password incorrect
        FileNotFoundError: If archive doesn't exist
    """
    archive_path = Path(archive_path)
    dest_path = Path(dest_path)
    
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    logger.info(f"Extracting archive: {archive_path}")
    
    # Try to import tqdm
    tqdm = None
    try:
        from tqdm import tqdm as tqdm_cls
        tqdm = tqdm_cls
    except ImportError:
        pass
    
    with open(archive_path, 'rb') as f:
        # Read and validate header
        magic = f.read(4)
        if magic != MAGIC_HEADER_ARCHIVE:
            raise ValueError(f"Invalid archive magic: {magic}")
        
        version = struct.unpack('B', f.read(1))[0]
        if version not in (1, 2):
            raise ValueError(f"Unsupported archive version: {version}")
        
        # Note: v1 archives don't support STORED mode, all files are compressed
        supports_stored = (version >= 2)
        
        per_file = struct.unpack('B', f.read(1))[0] == 1
        encrypted = struct.unpack('B', f.read(1))[0] == 1
        
        if encrypted and not password:
            raise ValueError("Archive is encrypted but no password provided")
        
        entry_table_offset = struct.unpack('>Q', f.read(8))[0]
        
        logger.info(f"Archive mode: {'per-file' if per_file else 'single-stream'}")
        if encrypted:
            logger.info("Archive is encrypted")
        
        # Read entry table
        f.seek(entry_table_offset)
        num_entries = struct.unpack('>I', f.read(4))[0]
        
        entries = []
        for _ in range(num_entries):
            name_len = struct.unpack('>H', f.read(2))[0]
            name = f.read(name_len).decode('utf-8')
            size = struct.unpack('>Q', f.read(8))[0]
            compressed_size = struct.unpack('>Q', f.read(8))[0]
            mtime = struct.unpack('>Q', f.read(8))[0]
            mode = struct.unpack('>I', f.read(4))[0]
            offset = struct.unpack('>Q', f.read(8))[0]
            
            # v2 format: read algorithm ID from entry table
            algo_id = None
            algo_name = None
            if supports_stored:  # v2+ format includes algo in entry table
                algo_id = struct.unpack('B', f.read(1))[0]
                algo_name = ALGO_REVERSE.get(algo_id, "LZW")
            
            entries.append({
                'name': name,
                'size': size,
                'compressed_size': compressed_size,
                'mtime': mtime,
                'mode': mode,
                'offset': offset,
                'algo_id': algo_id,
                'algo': algo_name
            })
        
        logger.info(f"Extracting {num_entries} files")
        
        # Create destination directory
        dest_path.mkdir(parents=True, exist_ok=True)
        
        if per_file:
            # Extract per-file compressed entries
            iterator = tqdm(entries, desc="Extracting", unit="file") if tqdm else entries
            
            for idx, entry in enumerate(iterator):
                # Sanitize path
                target_path = _sanitize_extract_path(entry['name'], dest_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Read entry header and data
                f.seek(entry['offset'])
                
                # Skip to compressed data (read past metadata)
                name_len = struct.unpack('>H', f.read(2))[0]
                f.read(name_len)  # filename
                f.read(8)  # original size
                f.read(8)  # mtime
                f.read(4)  # mode
                compressed_size = struct.unpack('>Q', f.read(8))[0]
                algo_id = struct.unpack('B', f.read(1))[0]
                
                # Read compressed data
                compressed_data = f.read(compressed_size)
                
                # Decompress (or use stored data directly)
                algo = ALGO_REVERSE.get(algo_id, "LZW")
                if algo == "STORED":
                    # Data is stored uncompressed
                    file_data = compressed_data
                else:
                    # Data is compressed - decompress it with AUTO to detect format
                    file_data = decompress(compressed_data, algo="AUTO", password=password)
                
                # Write file
                with open(target_path, 'wb') as out_f:
                    out_f.write(file_data)
                
                # Restore mtime and mode
                try:
                    os.utime(target_path, (entry['mtime'], entry['mtime']))
                    os.chmod(target_path, entry['mode'])
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not restore metadata for {target_path}: {e}")
                
                if progress_callback:
                    progress_callback(idx + 1, num_entries)
        
        else:
            # Single-stream mode: decompress entire stream then extract files
            logger.info("Decompressing stream")
            
            # Read compressed stream
            f.seek(entries[0]['offset'])
            compressed_size = struct.unpack('>Q', f.read(8))[0]
            algo_id = struct.unpack('B', f.read(1))[0]
            compressed_stream = f.read(compressed_size)
            
            algo = ALGO_REVERSE.get(algo_id, "LZW")
            if algo == "STORED":
                # Stream is stored uncompressed
                stream_data = compressed_stream
            else:
                # Stream is compressed - decompress it with AUTO to detect format
                stream_data = decompress(compressed_stream, algo="AUTO", password=password)
            
            # Parse stream and extract files
            stream = io.BytesIO(stream_data)
            
            iterator = tqdm(entries, desc="Extracting", unit="file") if tqdm else entries
            
            for idx, entry in enumerate(iterator):
                # Read file header from stream
                name_len = struct.unpack('>H', stream.read(2))[0]
                name = stream.read(name_len).decode('utf-8')
                file_size = struct.unpack('>Q', stream.read(8))[0]
                mtime = struct.unpack('>Q', stream.read(8))[0]
                mode = struct.unpack('>I', stream.read(4))[0]
                
                # Read file data
                file_data = stream.read(file_size)
                
                # Sanitize path
                target_path = _sanitize_extract_path(name, dest_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(target_path, 'wb') as out_f:
                    out_f.write(file_data)
                
                # Restore metadata
                try:
                    os.utime(target_path, (mtime, mtime))
                    os.chmod(target_path, mode)
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not restore metadata for {target_path}: {e}")
                
                if progress_callback:
                    progress_callback(idx + 1, num_entries)
    
    logger.info(f"Extraction complete: {num_entries} files extracted to {dest_path}")


def list_contents(archive_path: str | Path) -> List[Dict]:
    """
    List contents of archive without extracting.
    
    Args:
        archive_path: Path to archive file
    
    Returns:
        List of dicts with keys: name, size, compressed_size, mtime, mode
    
    Raises:
        ValueError: If archive is corrupted
        FileNotFoundError: If archive doesn't exist
    """
    archive_path = Path(archive_path)
    
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    with open(archive_path, 'rb') as f:
        # Read and validate header
        magic = f.read(4)
        if magic != MAGIC_HEADER_ARCHIVE:
            raise ValueError(f"Invalid archive magic: {magic}")
        
        version = struct.unpack('B', f.read(1))[0]
        if version not in (1, 2):
            raise ValueError(f"Unsupported archive version: {version}")
        
        supports_stored = (version >= 2)
        
        per_file = struct.unpack('B', f.read(1))[0] == 1
        encrypted = struct.unpack('B', f.read(1))[0] == 1
        entry_table_offset = struct.unpack('>Q', f.read(8))[0]
        
        # Read entry table
        f.seek(entry_table_offset)
        num_entries = struct.unpack('>I', f.read(4))[0]
        
        entries = []
        for _ in range(num_entries):
            name_len = struct.unpack('>H', f.read(2))[0]
            name = f.read(name_len).decode('utf-8')
            size = struct.unpack('>Q', f.read(8))[0]
            compressed_size = struct.unpack('>Q', f.read(8))[0]
            mtime = struct.unpack('>Q', f.read(8))[0]
            mode = struct.unpack('>I', f.read(4))[0]
            offset = struct.unpack('>Q', f.read(8))[0]
            
            # v2 format: read algorithm from entry table
            algo_name = None
            if supports_stored:  # v2+ format includes algo in entry table
                algo_id = struct.unpack('B', f.read(1))[0]
                algo_name = ALGO_REVERSE.get(algo_id, "LZW")
            
            entry_dict = {
                'name': name,
                'size': size,
                'compressed_size': compressed_size,
                'mtime': mtime,
                'mode': mode
            }
            if algo_name:
                entry_dict['algo'] = algo_name
            
            entries.append(entry_dict)
    
    return entries
