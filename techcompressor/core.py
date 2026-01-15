"""Core compression and decompression API for TechCompressor."""
import struct
from pathlib import Path
from techcompressor.utils import get_logger

logger = get_logger(__name__)

# LZW Configuration
MAGIC_HEADER_LZW = b"TCZ1"
MAX_DICT_SIZE = 4096
INITIAL_DICT_SIZE = 256

# Shared compression state for solid mode (dictionary persistence)
_solid_lzw_dict = None
_solid_lzw_next_code = None

# Huffman Configuration
MAGIC_HEADER_HUFFMAN = b"TCH1"

# DEFLATE Configuration
MAGIC_HEADER_DEFLATE = b"TCD1"
DEFAULT_WINDOW_SIZE = 32768  # 32 KB sliding window
DEFAULT_LOOKAHEAD = 258  # Maximum match length

# Zstandard Configuration (v2.0.0)
MAGIC_HEADER_ZSTD = b"TCS1"
ZSTD_DEFAULT_LEVEL = 3  # Balance of speed and ratio (1-22)

# Brotli Configuration (v2.0.0)
MAGIC_HEADER_BROTLI = b"TCB1"
BROTLI_DEFAULT_QUALITY = 6  # Balance of speed and ratio (0-11)

# File extensions that are already compressed (should use STORED mode)
COMPRESSED_EXTENSIONS = {
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif', '.jxl',
    # Videos
    '.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v',
    # Audio
    '.mp3', '.aac', '.ogg', '.opus', '.m4a', '.wma', '.flac',
    # Archives
    '.zip', '.rar', '.7z', '.gz', '.bz2', '.xz', '.tar.gz', '.tgz', '.tar.bz2',
    # Documents (compressed)
    '.pdf', '.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp',
    # Executables (often compressed)
    '.exe', '.dll', '.apk', '.ipa',
}


def is_likely_compressed(data: bytes, filename: str | None = None) -> bool:
    """
    Check if data is likely already compressed based on entropy and file extension.
    
    Args:
        data: Data to check
        filename: Optional filename to check extension
    
    Returns:
        True if data appears already compressed, False otherwise
    """
    # Check file extension first (fast)
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in COMPRESSED_EXTENSIONS:
            logger.debug(f"File {filename} has compressed extension {ext}")
            return True
    
    # Check entropy if we have enough data
    if len(data) < 1024:
        return False
    
    # Sample first 4KB to check for patterns
    sample_size = min(4096, len(data))
    sample = data[:sample_size]
    unique_bytes = len(set(sample))
    entropy_ratio = unique_bytes / 256.0  # 1.0 = perfectly random
    
    # If entropy > 0.9, data is likely already compressed/encrypted
    return entropy_ratio > 0.9


def _lzw_compress(data: bytes, persist_dict: bool = False) -> bytes:
    """
    Internal LZW compression implementation.
    
    Algorithm:
    1. Initialize dictionary with all single-byte values (0-255)
    2. Read input byte by byte, finding longest matching sequence
    3. Output code for matched sequence and add new sequence to dictionary
    4. Dictionary grows until MAX_DICT_SIZE, then resets
    
    Args:
        data: Bytes to compress
        persist_dict: If True, preserve dictionary state for next call (solid mode)
    
    Returns compressed codewords as packed bytes.
    """
    global _solid_lzw_dict, _solid_lzw_next_code
    
    if not data:
        return b""
    
    # Initialize or restore dictionary
    if persist_dict and _solid_lzw_dict is not None:
        # Continue with existing dictionary from previous file
        dictionary = _solid_lzw_dict.copy()
        next_code = _solid_lzw_next_code
    else:
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
    
    # Save dictionary state for next call if persisting
    if persist_dict:
        _solid_lzw_dict = dictionary.copy()
        _solid_lzw_next_code = next_code
    
    # Pack codes into bytes (each code is 2 bytes, big-endian)
    packed = b"".join(struct.pack(">H", code) for code in result)
    return packed


def reset_solid_compression_state() -> None:
    """Reset global dictionary state for solid compression. Call between archives."""
    global _solid_lzw_dict, _solid_lzw_next_code
    _solid_lzw_dict = None
    _solid_lzw_next_code = None


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


# ============================================================================
# Huffman Coding Implementation
# ============================================================================

class _HuffmanNode:
    """Node in the Huffman tree."""
    
    def __init__(self, byte: int | None = None, freq: int = 0, left=None, right=None):
        self.byte = byte  # Byte value (None for internal nodes)
        self.freq = freq  # Frequency count
        self.left = left  # Left child
        self.right = right  # Right child
    
    def __lt__(self, other):
        """Compare nodes by frequency for heap operations."""
        return self.freq < other.freq


def _build_frequency_table(data: bytes) -> dict[int, int]:
    """
    Build frequency table from input data.
    
    Args:
        data: Input bytes to analyze
    
    Returns:
        Dictionary mapping byte values to their frequencies
    """
    freq_table = {}
    for byte in data:
        freq_table[byte] = freq_table.get(byte, 0) + 1
    return freq_table


def _build_huffman_tree(freq_table: dict[int, int]) -> _HuffmanNode | None:
    """
    Build Huffman tree from frequency table using priority queue.
    
    Algorithm:
    1. Create leaf node for each byte with its frequency
    2. Build min-heap from all nodes
    3. Repeatedly extract two minimum nodes and combine
    4. Insert combined node back into heap
    5. Root of tree is final node
    
    Args:
        freq_table: Dictionary of byte frequencies
    
    Returns:
        Root node of Huffman tree, or None if empty
    """
    import heapq
    
    if not freq_table:
        return None
    
    # Create leaf nodes for each byte
    heap = [_HuffmanNode(byte=byte, freq=freq) for byte, freq in freq_table.items()]
    heapq.heapify(heap)
    
    # Build tree by combining nodes
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        # Create internal node with combined frequency
        parent = _HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, parent)
    
    return heap[0] if heap else None


def _generate_huffman_codes(root: _HuffmanNode | None) -> dict[int, str]:
    """
    Generate Huffman codes by traversing tree.
    
    Traverse tree depth-first, building binary code strings:
    - Left edge = '0'
    - Right edge = '1'
    
    Special case: single-node tree (only one unique byte) uses code "0"
    
    Args:
        root: Root of Huffman tree
    
    Returns:
        Dictionary mapping byte values to their binary code strings
    """
    if root is None:
        return {}
    
    # Special case: single node tree (only one unique byte)
    if root.byte is not None:
        return {root.byte: "0"}
    
    codes = {}
    
    def traverse(node: _HuffmanNode, code: str):
        """Recursively traverse tree to build codes."""
        if node.byte is not None:
            # Leaf node - store code
            codes[node.byte] = code
        else:
            # Internal node - traverse children
            if node.left:
                traverse(node.left, code + "0")
            if node.right:
                traverse(node.right, code + "1")
    
    traverse(root, "")
    return codes


def _serialize_huffman_tree(root: _HuffmanNode | None) -> bytes:
    """
    Serialize Huffman tree to bytes for storage.
    
    Format: Pre-order traversal with markers:
    - 0x01 + value (2 bytes, big-endian) for leaf nodes
    - 0x00 for internal nodes
    
    Args:
        root: Root of Huffman tree
    
    Returns:
        Serialized tree as bytes
    """
    if root is None:
        return b""
    
    result = bytearray()
    
    def serialize(node: _HuffmanNode):
        """Recursively serialize tree."""
        if node.byte is not None:
            # Leaf node: marker + value (2 bytes for DEFLATE symbols)
            result.append(0x01)
            result.extend(struct.pack(">H", node.byte))  # 2-byte big-endian
        else:
            # Internal node: marker only
            result.append(0x00)
            if node.left:
                serialize(node.left)
            if node.right:
                serialize(node.right)
    
    serialize(root)
    return bytes(result)


def _deserialize_huffman_tree(data: bytes) -> tuple[_HuffmanNode | None, int]:
    """
    Deserialize Huffman tree from bytes.
    
    Args:
        data: Serialized tree data
    
    Returns:
        Tuple of (root node, bytes consumed)
    """
    if not data:
        return None, 0
    
    pos = [0]  # Use list to allow modification in nested function
    
    def deserialize() -> _HuffmanNode | None:
        """Recursively deserialize tree."""
        if pos[0] >= len(data):
            return None
        
        marker = data[pos[0]]
        pos[0] += 1
        
        if marker == 0x01:
            # Leaf node
            if pos[0] + 1 >= len(data):
                raise ValueError("Corrupted Huffman tree: incomplete leaf node")
            # Read 2-byte value (for DEFLATE symbols)
            byte_val = struct.unpack(">H", data[pos[0]:pos[0]+2])[0]
            pos[0] += 2
            return _HuffmanNode(byte=byte_val)
        else:
            # Internal node
            node = _HuffmanNode()
            node.left = deserialize()
            node.right = deserialize()
            return node
    
    root = deserialize()
    return root, pos[0]


def _huffman_compress(data: bytes) -> bytes:
    """
    Internal Huffman compression implementation.
    
    Algorithm:
    1. Build frequency table from input
    2. Construct Huffman tree from frequencies
    3. Generate binary codes for each byte
    4. Encode data using codes
    5. Pack bits into bytes
    
    Returns:
        Compressed data with serialized tree prefix
    """
    if not data:
        return b""
    
    # Build frequency table and Huffman tree
    freq_table = _build_frequency_table(data)
    root = _build_huffman_tree(freq_table)
    
    # Generate codes
    codes = _generate_huffman_codes(root)
    
    # Serialize tree for decompression
    tree_data = _serialize_huffman_tree(root)
    tree_size = struct.pack(">I", len(tree_data))
    
    # Encode data as bit string
    bit_string = "".join(codes[byte] for byte in data)
    
    # Pack bits into bytes
    padding = (8 - len(bit_string) % 8) % 8
    bit_string += "0" * padding  # Add padding to make multiple of 8
    
    compressed_bytes = []
    for i in range(0, len(bit_string), 8):
        byte_bits = bit_string[i:i+8]
        compressed_bytes.append(int(byte_bits, 2))
    
    # Format: tree_size (4 bytes) + tree_data + padding (1 byte) + compressed_data
    result = tree_size + tree_data + bytes([padding]) + bytes(compressed_bytes)
    return result


def _huffman_decompress(compressed: bytes) -> bytes:
    """
    Internal Huffman decompression implementation.
    
    Algorithm:
    1. Deserialize Huffman tree from prefix
    2. Unpack compressed bits
    3. Traverse tree using bits to decode original bytes
    
    Returns:
        Decompressed original bytes
    """
    if not compressed:
        return b""
    
    # Extract tree size
    if len(compressed) < 4:
        raise ValueError("Corrupted Huffman data: too short")
    
    tree_size = struct.unpack(">I", compressed[:4])[0]
    pos = 4
    
    # Deserialize tree
    if pos + tree_size > len(compressed):
        raise ValueError("Corrupted Huffman data: invalid tree size")
    
    tree_data = compressed[pos:pos + tree_size]
    root, _ = _deserialize_huffman_tree(tree_data)
    pos += tree_size
    
    # Extract padding info
    if pos >= len(compressed):
        raise ValueError("Corrupted Huffman data: missing padding byte")
    
    padding = compressed[pos]
    pos += 1
    
    # Extract compressed data
    compressed_data = compressed[pos:]
    
    # Convert bytes to bit string
    bit_string = "".join(f"{byte:08b}" for byte in compressed_data)
    
    # Remove padding
    if padding > 0:
        bit_string = bit_string[:-padding]
    
    # Decode using Huffman tree
    result = []
    current = root
    
    # Special case: single-node tree (only one unique byte)
    if root.byte is not None:
        # All bits represent the same byte
        result = [root.byte] * len(bit_string)
    else:
        # Normal tree traversal
        for bit in bit_string:
            # Traverse tree based on bit
            if bit == "0":
                current = current.left if current else None
            else:
                current = current.right if current else None
            
            if current is None:
                raise ValueError("Corrupted Huffman data: invalid bit sequence")
            
            # Check if we reached a leaf
            if current.byte is not None:
                result.append(current.byte)
                current = root  # Reset to root for next byte
    
    return bytes(result)


# ============================================================================
# DEFLATE Implementation (LZ77 + Huffman)
# ============================================================================

def _lz77_find_matches(data: bytes, window_size: int = DEFAULT_WINDOW_SIZE, 
                       lookahead: int = DEFAULT_LOOKAHEAD):
    """
    Find matches in data using LZ77 sliding window algorithm.
    
    Yields (offset, length, next_byte) tuples:
    - offset: distance back to start of match (0 if no match)
    - length: length of match (0 if no match)
    - next_byte: next literal byte after match (or current byte if no match)
    
    Algorithm:
    1. Maintain sliding window of previous data
    2. For each position, search window for longest match
    3. Output (distance, length) pair and next literal
    4. Advance by match length + 1
    
    Args:
        data: Input bytes to compress
        window_size: Maximum size of sliding window
        lookahead: Maximum match length to search for
    
    Yields:
        Tuples of (offset, length, next_byte)
    """
    i = 0
    data_len = len(data)
    
    while i < data_len:
        best_offset = 0
        best_length = 0
        
        # Define search window (data before current position)
        window_start = max(0, i - window_size)
        
        # Search for longest match in window
        max_match_len = min(lookahead, data_len - i)
        
        for match_len in range(max_match_len, 2, -1):  # Start from longest possible
            # Pattern to match
            pattern = data[i:i + match_len]
            
            # Search in window
            search_area = data[window_start:i]
            pos = search_area.rfind(pattern)  # Find last occurrence
            
            if pos != -1:
                best_offset = i - (window_start + pos)
                best_length = match_len
                break
        
        # Output match or literal
        if best_length >= 3:  # Only use match if length >= 3 (DEFLATE convention)
            # Output match (next_byte will be processed in next iteration)
            yield (best_offset, best_length, 0)
            i += best_length
        else:
            # Output literal
            yield (0, 0, data[i])
            i += 1


def _compress_deflate(data: bytes) -> bytes:
    """
    Internal DEFLATE-style compression implementation.
    
    Algorithm:
    1. Run LZ77 to find repeated sequences
    2. Encode output as literals and (length, distance) pairs
    3. Build frequency table for all symbols
    4. Create Huffman codes for literals and length/distance pairs
    5. Encode using Huffman and pack bits
    
    Returns:
        Compressed data with header and Huffman table
    """
    if not data:
        return b""
    
    logger.info("Running LZ77 sliding window compression")
    
    # Step 1: Run LZ77 to find matches
    lz77_output = list(_lz77_find_matches(data))
    
    # Step 2: Encode LZ77 output as symbol stream
    # Symbols 0-255: literals
    # Symbol 256: end-of-block
    # Symbols 257-512: length codes (mapping to actual lengths)
    # Distance codes are separate (0-32767)
    
    symbols = []
    distances = []
    
    for offset, length, next_byte in lz77_output:
        if length == 0:
            # Literal byte
            symbols.append(next_byte)
        else:
            # Length-distance pair
            # Encode length as symbol 257+ (257 = length 3, 258 = length 4, etc.)
            length_symbol = 257 + (length - 3)
            symbols.append(length_symbol)
            distances.append(offset)
            # Note: next_byte is handled in the next iteration as we advance past it in LZ77
    
    # Add end-of-block marker
    symbols.append(256)
    
    logger.info(f"LZ77 produced {len(symbols)} symbols from {len(data)} bytes")
    
    # Step 3: Build frequency tables for Huffman encoding
    symbol_freqs = {}
    for sym in symbols:
        symbol_freqs[sym] = symbol_freqs.get(sym, 0) + 1
    
    dist_freqs = {}
    for dist in distances:
        dist_freqs[dist] = dist_freqs.get(dist, 0) + 1
    
    # Step 4: Build Huffman trees and generate codes
    symbol_tree = _build_huffman_tree(symbol_freqs)
    symbol_codes = _generate_huffman_codes(symbol_tree)
    
    dist_tree = None
    dist_codes = {}
    if distances:
        dist_tree = _build_huffman_tree(dist_freqs)
        dist_codes = _generate_huffman_codes(dist_tree)
    
    # Step 5: Serialize Huffman trees
    symbol_tree_data = _serialize_huffman_tree(symbol_tree)
    dist_tree_data = _serialize_huffman_tree(dist_tree) if dist_tree else b""
    
    # Step 6: Encode symbols using Huffman codes
    bit_string = ""
    dist_idx = 0
    
    for sym in symbols:
        bit_string += symbol_codes[sym]
        # If this is a length code, also encode distance
        if 257 <= sym <= 512 and dist_idx < len(distances):
            dist = distances[dist_idx]
            bit_string += dist_codes.get(dist, "0")
            dist_idx += 1
    
    logger.info(f"Huffman encoded to {len(bit_string)} bits")
    
    # Step 7: Pack bits into bytes
    padding = (8 - len(bit_string) % 8) % 8
    bit_string += "0" * padding
    
    compressed_bytes = []
    for i in range(0, len(bit_string), 8):
        byte_bits = bit_string[i:i+8]
        compressed_bytes.append(int(byte_bits, 2))
    
    # Step 8: Build output format
    # Format: window_size (2B) + orig_len (4B) + 
    #         symbol_tree_size (4B) + symbol_tree + 
    #         dist_tree_size (4B) + dist_tree + 
    #         padding (1B) + compressed_data
    
    header = struct.pack(">H", DEFAULT_WINDOW_SIZE)
    header += struct.pack(">I", len(data))
    header += struct.pack(">I", len(symbol_tree_data))
    header += symbol_tree_data
    header += struct.pack(">I", len(dist_tree_data))
    header += dist_tree_data
    header += bytes([padding])
    
    result = header + bytes(compressed_bytes)
    return result


def _decompress_deflate(compressed: bytes) -> bytes:
    """
    Internal DEFLATE-style decompression implementation.
    
    Algorithm:
    1. Extract header and Huffman trees
    2. Deserialize Huffman trees for literals and distances
    3. Decode bit stream using Huffman codes
    4. Reconstruct original data from literals and matches
    
    Returns:
        Decompressed original bytes
    """
    if not compressed:
        return b""
    
    pos = 0
    
    # Extract window size
    if len(compressed) < 2:
        raise ValueError("Corrupted DEFLATE data: too short for header")
    
    window_size = struct.unpack(">H", compressed[pos:pos+2])[0]
    pos += 2
    
    # Extract original length
    if pos + 4 > len(compressed):
        raise ValueError("Corrupted DEFLATE data: missing original length")
    
    orig_len = struct.unpack(">I", compressed[pos:pos+4])[0]
    pos += 4
    
    # Extract symbol tree
    if pos + 4 > len(compressed):
        raise ValueError("Corrupted DEFLATE data: missing symbol tree size")
    
    symbol_tree_size = struct.unpack(">I", compressed[pos:pos+4])[0]
    pos += 4
    
    if pos + symbol_tree_size > len(compressed):
        raise ValueError("Corrupted DEFLATE data: invalid symbol tree size")
    
    symbol_tree_data = compressed[pos:pos+symbol_tree_size]
    symbol_tree, _ = _deserialize_huffman_tree(symbol_tree_data)
    pos += symbol_tree_size
    
    # Extract distance tree
    if pos + 4 > len(compressed):
        raise ValueError("Corrupted DEFLATE data: missing distance tree size")
    
    dist_tree_size = struct.unpack(">I", compressed[pos:pos+4])[0]
    pos += 4
    
    dist_tree = None
    if dist_tree_size > 0:
        if pos + dist_tree_size > len(compressed):
            raise ValueError("Corrupted DEFLATE data: invalid distance tree size")
        
        dist_tree_data = compressed[pos:pos+dist_tree_size]
        dist_tree, _ = _deserialize_huffman_tree(dist_tree_data)
        pos += dist_tree_size
    
    # Extract padding
    if pos >= len(compressed):
        raise ValueError("Corrupted DEFLATE data: missing padding byte")
    
    padding = compressed[pos]
    pos += 1
    
    # Extract compressed data
    compressed_data = compressed[pos:]
    
    # Convert to bit string
    bit_string = "".join(f"{byte:08b}" for byte in compressed_data)
    if padding > 0:
        bit_string = bit_string[:-padding]
    
    # Decode bit stream
    result = []
    bit_pos = 0
    current_node = symbol_tree
    
    # Build reverse lookup for faster decoding
    symbol_codes = _generate_huffman_codes(symbol_tree)
    dist_codes = _generate_huffman_codes(dist_tree) if dist_tree else {}
    
    # Invert dictionaries for decoding
    code_to_symbol = {v: k for k, v in symbol_codes.items()}
    code_to_dist = {v: k for k, v in dist_codes.items()}
    
    def decode_symbol(start_pos):
        """Decode next symbol from bit string starting at start_pos."""
        code = ""
        pos = start_pos
        while pos < len(bit_string):
            code += bit_string[pos]
            pos += 1
            if code in code_to_symbol:
                return code_to_symbol[code], pos
        raise ValueError("Corrupted DEFLATE data: invalid symbol code")
    
    def decode_distance(start_pos):
        """Decode next distance from bit string starting at start_pos."""
        if not code_to_dist:
            return 0, start_pos
        code = ""
        pos = start_pos
        while pos < len(bit_string):
            code += bit_string[pos]
            pos += 1
            if code in code_to_dist:
                return code_to_dist[code], pos
        raise ValueError("Corrupted DEFLATE data: invalid distance code")
    
    # Decode symbols
    bit_pos = 0
    while bit_pos < len(bit_string):
        sym, bit_pos = decode_symbol(bit_pos)
        
        if sym == 256:  # End of block
            break
        elif sym < 256:  # Literal
            result.append(sym)
        else:  # Length code (257-512)
            length = sym - 257 + 3
            # Decode distance
            dist, bit_pos = decode_distance(bit_pos)
            
            # Copy from history
            if dist > len(result):
                raise ValueError(f"Corrupted DEFLATE data: invalid distance {dist}")
            
            start_pos = len(result) - dist
            for _ in range(length):
                result.append(result[start_pos])
                start_pos += 1
    
    logger.info(f"Decompressed {len(compressed)} → {len(result)} bytes")
    
    return bytes(result)


# ============================================================================
# Zstandard (zstd) Compression Implementation (v2.0.0)
# ============================================================================

def _zstd_compress(data: bytes, level: int = ZSTD_DEFAULT_LEVEL) -> bytes:
    """
    Internal Zstandard compression implementation.
    
    Zstandard is a modern compression algorithm developed by Facebook/Meta
    that provides excellent compression ratios with very fast speeds.
    
    Args:
        data: Bytes to compress
        level: Compression level (1-22, default 3)
            - 1-3: Fast compression, good for real-time
            - 4-9: Balanced (default range)
            - 10-19: High compression
            - 20-22: Ultra compression (slower)
    
    Returns:
        Compressed bytes
    """
    import zstandard as zstd
    
    if not data:
        return b""
    
    # Clamp level to valid range
    level = max(1, min(22, level))
    
    compressor = zstd.ZstdCompressor(level=level)
    compressed = compressor.compress(data)
    
    logger.debug(f"Zstandard compressed {len(data)} → {len(compressed)} bytes (level {level})")
    
    return compressed


def _zstd_decompress(compressed: bytes) -> bytes:
    """
    Internal Zstandard decompression implementation.
    
    Args:
        compressed: Zstandard compressed bytes
    
    Returns:
        Original uncompressed bytes
    """
    import zstandard as zstd
    
    if not compressed:
        return b""
    
    decompressor = zstd.ZstdDecompressor()
    decompressed = decompressor.decompress(compressed)
    
    logger.debug(f"Zstandard decompressed {len(compressed)} → {len(decompressed)} bytes")
    
    return decompressed


# ============================================================================
# Brotli Compression Implementation (v2.0.0)
# ============================================================================

def _brotli_compress(data: bytes, quality: int = BROTLI_DEFAULT_QUALITY) -> bytes:
    """
    Internal Brotli compression implementation.
    
    Brotli is a modern compression algorithm developed by Google, optimized
    for web content (HTML, CSS, JavaScript) with excellent text compression.
    
    Args:
        data: Bytes to compress
        quality: Compression quality (0-11, default 6)
            - 0-4: Fast compression
            - 5-9: Balanced (default range)
            - 10-11: Maximum compression (slower)
    
    Returns:
        Compressed bytes
    """
    import brotli
    
    if not data:
        return b""
    
    # Clamp quality to valid range
    quality = max(0, min(11, quality))
    
    compressed = brotli.compress(data, quality=quality)
    
    logger.debug(f"Brotli compressed {len(data)} → {len(compressed)} bytes (quality {quality})")
    
    return compressed


def _brotli_decompress(compressed: bytes) -> bytes:
    """
    Internal Brotli decompression implementation.
    
    Args:
        compressed: Brotli compressed bytes
    
    Returns:
        Original uncompressed bytes
    """
    import brotli
    
    if not compressed:
        return b""
    
    decompressed = brotli.decompress(compressed)
    
    logger.debug(f"Brotli decompressed {len(compressed)} → {len(decompressed)} bytes")
    
    return decompressed


def compress(data: bytes, algo: str = "LZW", password: str | None = None, persist_dict: bool = False) -> bytes:
    """
    Compress input data using the specified algorithm.
    
    Args:
        data: Raw bytes to compress
        algo: Compression algorithm - one of:
            - "LZW": Fast dictionary-based compression
            - "HUFFMAN": Frequency-based compression
            - "DEFLATE": LZ77 + Huffman (best ratio for general data)
            - "ZSTD": Zstandard - very fast with excellent ratio (v2.0.0)
            - "BROTLI": Brotli - best for text/web content (v2.0.0)
            - "AUTO": Automatically select best algorithm
        password: Optional password for encryption
        persist_dict: If True, preserve compression dictionary for next call (solid mode)
    
    Returns:
        Compressed bytes with header
    
    Format varies by algorithm:
        - LZW: "TCZ1" + dict_size(2) + compressed data
        - HUFFMAN: "TCH1" + compressed data with tree
        - DEFLATE: "TCD1" + LZ77+Huffman compressed data
        - ZSTD: "TCS1" + zstd compressed data
        - BROTLI: "TCB1" + brotli compressed data
    """
    algo_upper = algo.upper()

    # Support an "AUTO" mode which tries all supported algorithms and picks
    # the smallest compressed result. This usually gives the best compressed
    # size for arbitrary input without the user choosing an algorithm.
    supported = ("LZW", "HUFFMAN", "DEFLATE", "ZSTD", "ZSTANDARD", "BROTLI", "AUTO")
    if algo_upper not in supported:
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    # Normalize algorithm names
    if algo_upper == "ZSTANDARD":
        algo_upper = "ZSTD"

    logger.info(f"Starting {algo_upper} compression of {len(data)} bytes")

    if algo_upper == "AUTO":
        # Smart AUTO mode: use heuristics to avoid slow compression on large/incompressible files
        # v2.0.0: Added Zstandard as the preferred fast algorithm
        
        # For files larger than 5MB, skip DEFLATE (too slow) and only try fast algorithms
        skip_deflate = len(data) > 5 * 1024 * 1024
        
        # Enhanced entropy check using helper function
        if is_likely_compressed(data):
            logger.info("Data appears already compressed - using fast ZSTD only")
            skip_deflate = True
            skip_huffman = True
            skip_brotli = True
        else:
            skip_huffman = False
            skip_brotli = False
        
        # For very large files (>50MB), skip Huffman and Brotli (memory intensive / slow)
        if len(data) > 50 * 1024 * 1024:
            logger.info(f"Large file ({len(data) / (1024*1024):.1f} MB) - using ZSTD only")
            skip_deflate = True
            skip_huffman = True
            skip_brotli = True
        
        # If we're skipping all advanced algorithms, use Zstandard (fastest with good ratio)
        if skip_deflate and skip_huffman and skip_brotli:
            zstd_payload = MAGIC_HEADER_ZSTD + _zstd_compress(data)
            result = zstd_payload
            best_algo = "ZSTD"
        else:
            # Try each algorithm and pick the smallest result (before encryption)
            candidates: list[tuple[str, bytes]] = []

            # Zstandard candidate (v2.0.0 - always try, very fast)
            try:
                zstd_payload = MAGIC_HEADER_ZSTD + _zstd_compress(data)
                candidates.append(("ZSTD", zstd_payload))
            except Exception:
                logger.exception("ZSTD pass failed during AUTO mode")

            # LZW candidate (always try - fast)
            try:
                lzw_payload = MAGIC_HEADER_LZW + struct.pack(">H", MAX_DICT_SIZE) + _lzw_compress(data, persist_dict=persist_dict)
                candidates.append(("LZW", lzw_payload))
            except Exception:
                logger.exception("LZW pass failed during AUTO mode")

            # Huffman candidate (try for small-medium files)
            if not skip_huffman:
                try:
                    huff_payload = MAGIC_HEADER_HUFFMAN + _huffman_compress(data)
                    candidates.append(("HUFFMAN", huff_payload))
                except Exception:
                    logger.exception("Huffman pass failed during AUTO mode")

            # Brotli candidate (v2.0.0 - great for text, skip for large files)
            if not skip_brotli:
                try:
                    brotli_payload = MAGIC_HEADER_BROTLI + _brotli_compress(data)
                    candidates.append(("BROTLI", brotli_payload))
                except Exception:
                    logger.exception("Brotli pass failed during AUTO mode")

            # DEFLATE candidate (skip for large files)
            if not skip_deflate:
                try:
                    deflate_payload = MAGIC_HEADER_DEFLATE + _compress_deflate(data)
                    candidates.append(("DEFLATE", deflate_payload))
                except Exception:
                    logger.exception("DEFLATE pass failed during AUTO mode")
            else:
                logger.info(f"Skipping DEFLATE for large file ({len(data)} bytes)")

            if not candidates:
                raise ValueError("AUTO compression failed: no successful algorithm passes")

            # Pick smallest by length
            best_algo, result = min(candidates, key=lambda x: len(x[1]))
        
        # Check if compression actually helped
        ratio = len(result) / max(len(data), 1)
        if ratio > 1.0:
            logger.warning(
                f"AUTO selected {best_algo} but data expanded to {len(result)} bytes "
                f"({ratio*100:.1f}%) - file may be incompressible or too small"
            )
        else:
            logger.info(f"AUTO selected {best_algo} with size {len(result)} bytes ({ratio*100:.1f}%)")


    elif algo_upper == "LZW":
        # Perform LZW compression
        compressed_data = _lzw_compress(data, persist_dict=persist_dict)
        header = MAGIC_HEADER_LZW + struct.pack(">H", MAX_DICT_SIZE)
        result = header + compressed_data
    elif algo_upper == "HUFFMAN":
        # Perform Huffman compression
        compressed_data = _huffman_compress(data)
        result = MAGIC_HEADER_HUFFMAN + compressed_data
    elif algo_upper == "DEFLATE":
        # Perform DEFLATE compression (LZ77 + Huffman)
        compressed_data = _compress_deflate(data)
        result = MAGIC_HEADER_DEFLATE + compressed_data
    elif algo_upper == "ZSTD":
        # Perform Zstandard compression (v2.0.0)
        compressed_data = _zstd_compress(data)
        result = MAGIC_HEADER_ZSTD + compressed_data
    elif algo_upper == "BROTLI":
        # Perform Brotli compression (v2.0.0)
        compressed_data = _brotli_compress(data)
        result = MAGIC_HEADER_BROTLI + compressed_data
    
    logger.info(f"Compression complete: {len(data)} → {len(result)} bytes "
                f"({100 * len(result) / max(len(data), 1):.1f}%)")
    
    # Apply encryption if password is provided
    if password is not None:
        from .crypto import encrypt_aes_gcm
        logger.info("Encryption enabled - applying AES-256-GCM")
        result = encrypt_aes_gcm(result, password)
    
    return result


def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """
    Decompress data using the specified algorithm.
    
    Args:
        data: Compressed bytes with header
        algo: Compression algorithm - one of:
            - "LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI", "AUTO"
        password: Optional password for decryption
    
    Returns:
        Decompressed original bytes
    
    Raises:
        ValueError: If data is corrupted or header is invalid
    """
    # Check if data is encrypted
    if len(data) >= 4 and data[:4] == b"TCE1":
        if password is None:
            raise ValueError("Data is encrypted but no password provided")
        from .crypto import decrypt_aes_gcm
        logger.info("Encrypted data detected - decrypting with AES-256-GCM")
        data = decrypt_aes_gcm(data, password)

    algo_upper = algo.upper()
    supported = ("LZW", "HUFFMAN", "DEFLATE", "ZSTD", "ZSTANDARD", "BROTLI", "AUTO")
    if algo_upper not in supported:
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    # Normalize algorithm names
    if algo_upper == "ZSTANDARD":
        algo_upper = "ZSTD"

    logger.info(f"Starting {algo_upper} decompression of {len(data)} bytes")

    # Validate minimum size
    if len(data) < 4:
        raise ValueError("Corrupted data: too short for valid TechCompressor format")

    # Determine algorithm from magic header - decompression always detects the
    # format from the header. If user supplied a specific algorithm that
    # disagrees with the detected format, log a warning but continue.
    magic = data[:4]
    detected = None
    if magic == MAGIC_HEADER_LZW:
        detected = "LZW"
    elif magic == MAGIC_HEADER_HUFFMAN:
        detected = "HUFFMAN"
    elif magic == MAGIC_HEADER_DEFLATE:
        detected = "DEFLATE"
    elif magic == MAGIC_HEADER_ZSTD:
        detected = "ZSTD"
    elif magic == MAGIC_HEADER_BROTLI:
        detected = "BROTLI"
    else:
        raise ValueError(f"Invalid magic header: unknown format {magic}")

    if algo_upper != "AUTO" and algo_upper != detected:
        # Maintain previous behavior: when user requests a specific algorithm
        # and the data does not match that algorithm's magic header, this
        # should be considered an error to avoid silent mis-decompression.
        raise ValueError(f"Invalid magic header: expected {globals().get('MAGIC_HEADER_' + algo_upper)} for {algo_upper}")

    # Route to appropriate decompressor
    if detected == "LZW":
        if len(data) < 6:
            raise ValueError("Corrupted LZW data: too short")

        # Extract dictionary size (for validation)
        dict_size = struct.unpack(">H", data[4:6])[0]
        if dict_size != MAX_DICT_SIZE:
            logger.warning(f"Dictionary size mismatch: expected {MAX_DICT_SIZE}, got {dict_size}")

        # Decompress
        compressed_data = data[6:]
        result = _lzw_decompress(compressed_data)
    elif detected == "HUFFMAN":
        compressed_data = data[4:]
        result = _huffman_decompress(compressed_data)
    elif detected == "DEFLATE":
        compressed_data = data[4:]
        result = _decompress_deflate(compressed_data)
    elif detected == "ZSTD":
        compressed_data = data[4:]
        result = _zstd_decompress(compressed_data)
    elif detected == "BROTLI":
        compressed_data = data[4:]
        result = _brotli_decompress(compressed_data)
    
    logger.info(f"Decompression complete: {len(data)} → {len(result)} bytes")
    
    return result
