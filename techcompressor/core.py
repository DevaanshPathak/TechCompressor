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
    - 0x01 + byte value (1 byte) for leaf nodes
    - 0x00 for internal nodes
    
    Args:
        root: Root of Huffman tree
    
    Returns:
        Serialized tree as bytes
    """
    if root is None:
        return b""
    
    result = []
    
    def serialize(node: _HuffmanNode):
        """Recursively serialize tree."""
        if node.byte is not None:
            # Leaf node: marker + byte value
            result.append(0x01)
            result.append(node.byte)
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
            if pos[0] >= len(data):
                raise ValueError("Corrupted Huffman tree: incomplete leaf node")
            byte_val = data[pos[0]]
            pos[0] += 1
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


def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """
    Compress input data using the specified algorithm.
    
    Args:
        data: Raw bytes to compress
        algo: Compression algorithm ("LZW" or "HUFFMAN" currently supported)
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
    """
    algo_upper = algo.upper()
    
    if algo_upper not in ("LZW", "HUFFMAN"):
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    if password is not None:
        logger.info("Password protection will be added in Phase 6")
    
    logger.info(f"Starting {algo_upper} compression of {len(data)} bytes")
    
    if algo_upper == "LZW":
        # Perform LZW compression
        compressed_data = _lzw_compress(data)
        header = MAGIC_HEADER_LZW + struct.pack(">H", MAX_DICT_SIZE)
        result = header + compressed_data
    else:  # HUFFMAN
        # Perform Huffman compression
        compressed_data = _huffman_compress(data)
        result = MAGIC_HEADER_HUFFMAN + compressed_data
    
    logger.info(f"Compression complete: {len(data)} → {len(result)} bytes "
                f"({100 * len(result) / max(len(data), 1):.1f}%)")
    
    return result


def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """
    Decompress data using the specified algorithm.
    
    Args:
        data: Compressed bytes with header
        algo: Compression algorithm ("LZW" or "HUFFMAN" currently supported)
        password: Optional password for decryption (Phase 6 feature)
    
    Returns:
        Decompressed original bytes
    
    Raises:
        ValueError: If data is corrupted or header is invalid
    """
    algo_upper = algo.upper()
    
    if algo_upper not in ("LZW", "HUFFMAN"):
        raise NotImplementedError(f"Algorithm {algo} not implemented yet.")
    
    if password is not None:
        logger.info("Password protection will be added in Phase 6")
    
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
    
    else:  # HUFFMAN
        if magic != MAGIC_HEADER_HUFFMAN:
            raise ValueError(f"Invalid magic header: expected {MAGIC_HEADER_HUFFMAN}, got {magic}")
        
        # Decompress
        compressed_data = data[4:]
        result = _huffman_decompress(compressed_data)
    
    logger.info(f"Decompression complete: {len(data)} → {len(result)} bytes")
    
    return result
