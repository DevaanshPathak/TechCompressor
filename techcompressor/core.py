"""Core compression and decompression API for TechCompressor."""
import struct
from techcompressor.utils import get_logger

logger = get_logger(__name__)

# LZW Configuration
MAGIC_HEADER = b"TCZ1"
MAX_DICT_SIZE = 4096
INITIAL_DICT_SIZE = 256


def _lzw_compress(data: bytes) -> bytes:
    """
    Internal LZW compression implementation.
    
    Algorithm:
    1. Initialize dictionary with all single-byte values (0-255)
    2. Read input byte by byte, finding longest matching sequence
    3. Output code for matched sequence and add new sequence to dictionary
    4. Dictionary grows until MAX_DICT_SIZE, then resets
    
    Returns compressed codewords as packed bytes.
    """
    if not data:
        return b""
    
    # Initialize dictionary with single bytes
    dictionary = {bytes([i]): i for i in range(INITIAL_DICT_SIZE)}
    next_code = INITIAL_DICT_SIZE
    
    result = []
    current_sequence = b""
    
    for byte in data:
        next_sequence = current_sequence + bytes([byte])
        
        if next_sequence in dictionary:
            # Sequence exists, keep building
            current_sequence = next_sequence
        else:
            # Output code for current sequence
            result.append(dictionary[current_sequence])
            
            # Add new sequence to dictionary if space available
            if next_code < MAX_DICT_SIZE:
                dictionary[next_sequence] = next_code
                next_code += 1
            else:
                # Reset dictionary when full
                dictionary = {bytes([i]): i for i in range(INITIAL_DICT_SIZE)}
                next_code = INITIAL_DICT_SIZE
            
            current_sequence = bytes([byte])
    
    # Output code for remaining sequence
    if current_sequence:
        result.append(dictionary[current_sequence])
    
    # Pack codes into bytes (each code is 2 bytes, big-endian)
    packed = b"".join(struct.pack(">H", code) for code in result)
    return packed


def _lzw_decompress(compressed: bytes) -> bytes:
    """
    Internal LZW decompression implementation.
    
    Algorithm:
    1. Initialize dictionary with all single-byte values (0-255)
    2. Read codes from compressed data
    3. Reconstruct original data by looking up codes in dictionary
    4. Rebuild dictionary using same logic as compression
    
    Returns original uncompressed bytes.
    """
    if not compressed:
        return b""
    
    # Validate compressed data length (must be even for 2-byte codes)
    if len(compressed) % 2 != 0:
        raise ValueError("Corrupted LZW data: invalid length")
    
    # Unpack codes from bytes
    codes = []
    for i in range(0, len(compressed), 2):
        code = struct.unpack(">H", compressed[i:i+2])[0]
        codes.append(code)
    
    # Initialize dictionary with single bytes
    dictionary = {i: bytes([i]) for i in range(INITIAL_DICT_SIZE)}
    next_code = INITIAL_DICT_SIZE
    
    result = []
    
    # First code must be in initial dictionary
    if not codes:
        return b""
    
    previous_code = codes[0]
    if previous_code >= INITIAL_DICT_SIZE:
        raise ValueError("Corrupted LZW data: invalid first code")
    
    result.append(dictionary[previous_code])
    
    for code in codes[1:]:
        # Handle special case where code is not yet in dictionary
        if code in dictionary:
            entry = dictionary[code]
        elif code == next_code:
            # Code refers to sequence we're about to add
            entry = dictionary[previous_code] + dictionary[previous_code][:1]
        else:
            raise ValueError(f"Corrupted LZW data: invalid code {code}")
        
        result.append(entry)
        
        # Add new sequence to dictionary
        if next_code < MAX_DICT_SIZE:
            dictionary[next_code] = dictionary[previous_code] + entry[:1]
            next_code += 1
        else:
            # Reset dictionary when full
            dictionary = {i: bytes([i]) for i in range(INITIAL_DICT_SIZE)}
            next_code = INITIAL_DICT_SIZE
        
        previous_code = code
    
    return b"".join(result)


def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """
    Compress input data using the specified algorithm (Phase 2 implements LZW).
    
    Args:
        data: Raw bytes to compress
        algo: Compression algorithm ("LZW" currently supported)
        password: Optional password for encryption (Phase 6 feature)
    
    Returns:
        Compressed bytes with header
    
    Format:
        - 4 bytes: Magic header "TCZ1"
        - 2 bytes: Max dictionary size (4096)
        - N bytes: LZW compressed codewords
    """
    if algo.upper() != "LZW":
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    if password is not None:
        logger.info("Password protection will be added in Phase 6")
    
    logger.info(f"Starting LZW compression of {len(data)} bytes")
    
    # Perform LZW compression
    compressed_data = _lzw_compress(data)
    
    # Build output with header
    header = MAGIC_HEADER + struct.pack(">H", MAX_DICT_SIZE)
    result = header + compressed_data
    
    logger.info(f"Compression complete: {len(data)} → {len(result)} bytes "
                f"({100 * len(result) / max(len(data), 1):.1f}%)")
    
    return result


def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """
    Decompress data using the specified algorithm (Phase 2 implements LZW).
    
    Args:
        data: Compressed bytes with header
        algo: Compression algorithm ("LZW" currently supported)
        password: Optional password for decryption (Phase 6 feature)
    
    Returns:
        Decompressed original bytes
    
    Raises:
        ValueError: If data is corrupted or header is invalid
    """
    if algo.upper() != "LZW":
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    if password is not None:
        logger.info("Password protection will be added in Phase 6")
    
    logger.info(f"Starting LZW decompression of {len(data)} bytes")
    
    # Validate minimum size
    if len(data) < 6:
        raise ValueError("Corrupted data: too short for valid TechCompressor format")
    
    # Validate magic header
    if data[:4] != MAGIC_HEADER:
        raise ValueError(f"Invalid magic header: expected {MAGIC_HEADER}, got {data[:4]}")
    
    # Extract dictionary size (for validation)
    dict_size = struct.unpack(">H", data[4:6])[0]
    if dict_size != MAX_DICT_SIZE:
        logger.warning(f"Dictionary size mismatch: expected {MAX_DICT_SIZE}, got {dict_size}")
    
    # Decompress
    compressed_data = data[6:]
    result = _lzw_decompress(compressed_data)
    
    logger.info(f"Decompression complete: {len(data)} → {len(result)} bytes")
    
    return result
