"""Core compression and decompression API for TechCompressor."""
import struct
from techcompressor.utils import get_logger

logger = get_logger(__name__)

# LZW Configuration
MAGIC_HEADER_LZW = b"TCZ1"
MAX_DICT_SIZE = 4096
INITIAL_DICT_SIZE = 256

# Huffman Configuration
MAGIC_HEADER_HUFFMAN = b"TCH1"

# DEFLATE Configuration
MAGIC_HEADER_DEFLATE = b"TCD1"
DEFAULT_WINDOW_SIZE = 32768  # 32 KB sliding window
DEFAULT_LOOKAHEAD = 258  # Maximum match length


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


def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """
    Compress input data using the specified algorithm.
    
    Args:
        data: Raw bytes to compress
        algo: Compression algorithm ("LZW", "HUFFMAN", or "DEFLATE" currently supported)
        password: Optional password for encryption (Phase 6 feature)
    
    Returns:
        Compressed bytes with header
    
    Format (LZW):
        - 4 bytes: Magic header "TCZ1"
        - 2 bytes: Max dictionary size (4096)
        - N bytes: LZW compressed codewords
    
    Format (Huffman):
        - 4 bytes: Magic header "TCH1"
        - N bytes: Huffman compressed data with tree
    
    Format (DEFLATE):
        - 4 bytes: Magic header "TCD1"
        - N bytes: DEFLATE compressed data (LZ77 + Huffman)
    """
    algo_upper = algo.upper()
    
    if algo_upper not in ("LZW", "HUFFMAN", "DEFLATE"):
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    logger.info(f"Starting {algo_upper} compression of {len(data)} bytes")
    
    if algo_upper == "LZW":
        # Perform LZW compression
        compressed_data = _lzw_compress(data)
        header = MAGIC_HEADER_LZW + struct.pack(">H", MAX_DICT_SIZE)
        result = header + compressed_data
    elif algo_upper == "HUFFMAN":
        # Perform Huffman compression
        compressed_data = _huffman_compress(data)
        result = MAGIC_HEADER_HUFFMAN + compressed_data
    else:  # DEFLATE
        # Perform DEFLATE compression (LZ77 + Huffman)
        compressed_data = _compress_deflate(data)
        result = MAGIC_HEADER_DEFLATE + compressed_data
    
    logger.info(f"Compression complete: {len(data)} → {len(result)} bytes "
                f"({100 * len(result) / max(len(data), 1):.1f}%)")
    
    # Apply encryption if password is provided (Phase 6)
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
        algo: Compression algorithm ("LZW", "HUFFMAN", or "DEFLATE" currently supported)
        password: Optional password for decryption (Phase 6 feature)
    
    Returns:
        Decompressed original bytes
    
    Raises:
        ValueError: If data is corrupted or header is invalid
    """
    # Check if data is encrypted (Phase 6)
    if len(data) >= 4 and data[:4] == b"TCE1":
        if password is None:
            raise ValueError("Data is encrypted but no password provided")
        from .crypto import decrypt_aes_gcm
        logger.info("Encrypted data detected - decrypting with AES-256-GCM")
        data = decrypt_aes_gcm(data, password)
    
    algo_upper = algo.upper()
    
    if algo_upper not in ("LZW", "HUFFMAN", "DEFLATE"):
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    logger.info(f"Starting {algo_upper} decompression of {len(data)} bytes")
    
    # Validate minimum size
    if len(data) < 4:
        raise ValueError("Corrupted data: too short for valid TechCompressor format")
    
    # Check magic header to determine algorithm
    magic = data[:4]
    
    if algo_upper == "LZW":
        if magic != MAGIC_HEADER_LZW:
            raise ValueError(f"Invalid magic header: expected {MAGIC_HEADER_LZW}, got {magic}")
        
        if len(data) < 6:
            raise ValueError("Corrupted LZW data: too short")
        
        # Extract dictionary size (for validation)
        dict_size = struct.unpack(">H", data[4:6])[0]
        if dict_size != MAX_DICT_SIZE:
            logger.warning(f"Dictionary size mismatch: expected {MAX_DICT_SIZE}, got {dict_size}")
        
        # Decompress
        compressed_data = data[6:]
        result = _lzw_decompress(compressed_data)
    
    elif algo_upper == "HUFFMAN":
        if magic != MAGIC_HEADER_HUFFMAN:
            raise ValueError(f"Invalid magic header: expected {MAGIC_HEADER_HUFFMAN}, got {magic}")
        
        # Decompress
        compressed_data = data[4:]
        result = _huffman_decompress(compressed_data)
    
    else:  # DEFLATE
        if magic != MAGIC_HEADER_DEFLATE:
            raise ValueError(f"Invalid magic header: expected {MAGIC_HEADER_DEFLATE}, got {magic}")
        
        # Decompress
        compressed_data = data[4:]
        result = _decompress_deflate(compressed_data)
    
    logger.info(f"Decompression complete: {len(data)} → {len(result)} bytes")
    
    return result
