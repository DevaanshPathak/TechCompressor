# TechCompressor File Format Specification

## Overview

TechCompressor uses custom binary formats for compressed data and archives. Each format is identified by a unique 4-byte magic header to enable automatic format detection and prevent wrong-algorithm decompression errors.

## Compressed Data Formats

### LZW Format (`TCZ1`)

**Structure**:
```
[Magic: 4 bytes] [Dict Size: 2 bytes] [Compressed Data: variable]
```

**Details**:
- **Magic Header**: `TCZ1` (0x54 0x43 0x5A 0x31)
- **Dictionary Size**: 2-byte big-endian unsigned integer (typically 4096)
- **Compressed Data**: Stream of 2-byte big-endian code words

**Code Word Format**:
- Each code is a 2-byte big-endian unsigned integer
- Range: 0-4095 (for 4096-entry dictionary)
- Codes 0-255 represent literal bytes
- Codes 256+ represent dictionary sequences

**Dictionary Behavior**:
- Initialized with single-byte values (0-255)
- Grows dynamically up to MAX_DICT_SIZE (4096)
- Automatically resets when full (enables unlimited input size)

**Example**:
```
Input:  "TOBEORNOTTOBEORTOBEORNOT" (25 bytes)
Output: TCZ1 [10 00] [00 54] [00 4F] [00 42] ... (compressed codes)
```

### Huffman Format (`TCH1`)

**Structure**:
```
[Magic: 4 bytes] [Tree Size: 4 bytes] [Tree Data: variable] [Compressed Data: variable]
```

**Details**:
- **Magic Header**: `TCH1` (0x54 0x43 0x48 0x31)
- **Tree Size**: 4-byte big-endian unsigned integer (length of serialized tree in bytes)
- **Tree Data**: Serialized Huffman tree structure (preorder traversal)
- **Compressed Data**: Bit-packed Huffman codes

**Tree Serialization Format**:
- Preorder traversal of binary tree
- Internal nodes: `0` bit
- Leaf nodes: `1` bit followed by 8-bit byte value
- Example: `1[01000001]` = leaf node with byte 'A' (0x41)

**Compressed Data**:
- Variable-length codes packed into bytes
- Padding bits added to align to byte boundary
- Padding size stored in last byte

**Special Case**:
- Single unique byte: code = "0", tree stores single leaf

**Example**:
```
Input:  "AAB" (3 bytes, frequencies: A=2, B=1)
Tree:   Internal→(Left=A, Right=B)
Codes:  A="0", B="1"
Output: TCH1 [tree_size] [tree_data] [compressed: "001"]
```

### DEFLATE Format (`TCD1`)

**Structure**:
```
[Magic: 4 bytes] [Window Size: 2 bytes] [Compressed Data: variable]
```

**Details**:
- **Magic Header**: `TCD1` (0x54 0x43 0x44 0x31)
- **Window Size**: 2-byte big-endian unsigned integer (typically 32768 = 32KB)
- **Compressed Data**: Two-stage encoded data (LZ77 tokens + Huffman codes)

**LZ77 Token Format**:
- **Literal**: `(0, byte_value)`
- **Match**: `(distance, length)` where distance is offset back in window, length is match size

**Encoding Process**:
1. LZ77 pass: Find matches in sliding window, emit tokens
2. Huffman pass: Build frequency table from tokens, encode with Huffman

**Window Parameters**:
- Window size: 32768 bytes (32KB)
- Max match length: 258 bytes
- Min match length: 3 bytes

**Example**:
```
Input:  "ABABAB" (6 bytes)
LZ77:   [(0, 'A'), (0, 'B'), (2, 4)]  # "AB" + match 2 bytes back, length 4
Huffman: Encode tokens with Huffman tree
Output: TCD1 [80 00] [huffman_tree] [encoded_tokens]
```

## Encrypted Format (`TCE1`)

**Structure**:
```
[Magic: 4 bytes] [Salt: 16 bytes] [Nonce: 12 bytes] [Ciphertext: variable] [Auth Tag: 16 bytes]
```

**Details**:
- **Magic Header**: `TCE1` (0x54 0x43 0x45 0x31)
- **Salt**: 16-byte random salt for PBKDF2 key derivation
- **Nonce**: 12-byte random nonce for AES-GCM (recommended size)
- **Ciphertext**: AES-256-GCM encrypted data (can be any compressed format)
- **Auth Tag**: 16-byte GCM authentication tag (integrity verification)

**Encryption Process**:
1. Generate random 16-byte salt
2. Derive 256-bit key using PBKDF2-HMAC-SHA256 (100,000 iterations)
3. Generate random 12-byte nonce
4. Encrypt plaintext with AES-256-GCM
5. Append authentication tag

**Decryption Process**:
1. Extract salt from encrypted data
2. Derive key from password and salt (same PBKDF2 parameters)
3. Extract nonce and authentication tag
4. Decrypt and verify authentication tag
5. Return plaintext (which may be compressed data with its own magic header)

**Example**:
```
Input:  Compressed LZW data "TCZ1..."
Encrypt: TCE1 [16B salt] [12B nonce] [AES(TCZ1...)] [16B tag]
Decrypt: Verify tag → AES decrypt → "TCZ1..." (original compressed data)
```

## Archive Format (TCAF)

### TCAF Header

**Structure**:
```
[Magic: 4 bytes] [Version: 1 byte] [Algorithm: 1 byte] [Per-File: 1 byte] [Entry Count: 4 bytes]
```

**Details**:
- **Magic Header**: `TCAF` (0x54 0x43 0x41 0x46) - TechCompressor Archive Format
- **Version**: 1 byte (current version = 1)
- **Algorithm**: 1 byte algorithm ID
  - `1` = LZW
  - `2` = HUFFMAN
  - `3` = DEFLATE
  - `4` = ARITHMETIC (reserved)
- **Per-File Flag**: 1 byte boolean (0 = single-stream, 1 = per-file)
- **Entry Count**: 4-byte big-endian unsigned integer (number of files/folders)

### Entry Format

**Entry Metadata**:
```
[Name Length: 4 bytes] [Name: UTF-8] [Is Dir: 1 byte] [Mod Time: 8 bytes] [Original Size: 8 bytes] [Data Length: 8 bytes]
```

**Details**:
- **Name Length**: 4-byte big-endian unsigned integer
- **Name**: UTF-8 encoded relative path (forward slashes, no leading slash)
- **Is Dir**: 1 byte boolean (0 = file, 1 = directory)
- **Mod Time**: 8-byte big-endian integer (Unix timestamp in seconds)
- **Original Size**: 8-byte big-endian unsigned integer (uncompressed size)
- **Data Length**: 8-byte big-endian unsigned integer (compressed data size, 0 for directories)

**Entry Data**:
```
[Compressed Data: Data Length bytes]
```

- **Per-file mode**: Each entry's data is independently compressed (has its own magic header)
- **Single-stream mode**: Only the first file entry contains compressed data; subsequent files are encoded within that stream

### Archive Modes

#### Per-File Mode (`per_file=True`)

**Structure**:
```
TCAF Header
Entry 1 Metadata
Entry 1 Data: [TCZ1/TCH1/TCD1...] (independently compressed)
Entry 2 Metadata
Entry 2 Data: [TCZ1/TCH1/TCD1...] (independently compressed)
...
```

**Advantages**:
- Random access to individual files
- Selective extraction (no need to decompress entire archive)
- Better for mixed content types
- Fault tolerance (corruption affects only one file)

**Disadvantages**:
- Slightly larger archive size (metadata overhead per file)
- No cross-file dictionary sharing

#### Single-Stream Mode (`per_file=False`)

**Structure**:
```
TCAF Header
Entry 1 Metadata (file 1)
Entry 2 Metadata (file 2)
...
Entry N Metadata (file N)
Combined Data: [TCZ1/TCH1/TCD1...] (all files compressed together)
```

**Advantages**:
- Better compression ratio (shared dictionary across files)
- Smaller archive size (single compression overhead)
- Ideal for similar files (source code, text documents)

**Disadvantages**:
- Must decompress entire archive to extract any file
- Corruption may affect multiple files
- Sequential access only

### Security Features

**Path Sanitization**:
- Entry names must be relative paths (no leading `/` or drive letters)
- No `..` components allowed (prevents directory traversal)
- No absolute paths
- Symlinks are rejected during archive creation

**Validation**:
- Entry names validated during creation
- Extraction paths sanitized to prevent traversal attacks
- Symlinks resolved before archiving (prevented by default)

### Encrypted Archives

Archives can be encrypted by wrapping the entire TCAF structure:

**Structure**:
```
TCE1 [Salt] [Nonce] [Encrypted TCAF Archive] [Auth Tag]
```

- Password protects the entire archive (metadata and data)
- Authentication tag verifies archive integrity
- Decryption must succeed before archive can be parsed

**Example**:
```
Unencrypted: TCAF [version][algo][per_file][count][entries...]
Encrypted:   TCE1 [salt][nonce][AES(TCAF...)][tag]
```

## Format Detection

TechCompressor automatically detects formats by reading the 4-byte magic header:

```python
with open(file, 'rb') as f:
    magic = f.read(4)
    
if magic == b'TCZ1':
    format = 'LZW'
elif magic == b'TCH1':
    format = 'Huffman'
elif magic == b'TCD1':
    format = 'DEFLATE'
elif magic == b'TCE1':
    format = 'Encrypted'
elif magic == b'TCAF':
    format = 'Archive'
else:
    raise ValueError(f'Unknown format: {magic}')
```

## Byte Order

All multi-byte integers use **big-endian** (network byte order):
- Dictionary size: `struct.pack(">H", size)`
- Entry count: `struct.pack(">I", count)`
- Timestamps: `struct.pack(">Q", timestamp)`

## Version Compatibility

**Current Version**: 1.0.0 (TCAF version 1)

**Future Compatibility**:
- Magic headers are fixed and will not change
- TCAF version byte allows format evolution
- Future versions will read older archives
- Breaking changes will increment major version

## Format Extensions

**Reserved Magic Headers**:
- `TCA1` - Reserved for Arithmetic coding
- `TCB1` - Reserved for BWT (Burrows-Wheeler Transform)
- `TCS1` - Reserved for Snappy algorithm
- `TCR1` - Reserved for custom/research algorithms

**Archive Extensions**:
- Metadata can be extended with new fields (version byte controls parsing)
- Custom attributes (permissions, extended attributes) can be added
- Compression settings (dictionary size, window size) can be stored

## Implementation Notes

### Performance Optimization
- Use buffered I/O for reading/writing archives
- Chunk size: 16MB for streaming large files
- Memory-map large archives for random access (future)

### Error Handling
- Magic header mismatch: `ValueError("Invalid magic header")`
- Corrupted data: `ValueError("Corrupted {format} data")`
- Wrong password: `ValueError("Decryption failed - wrong password")`
- Invalid archive: `ValueError("Invalid TCAF archive")`

### Testing
- Test all magic headers with valid and invalid data
- Test encryption with correct and incorrect passwords
- Test archive modes with various file structures
- Test path traversal prevention (e.g., `../../etc/passwd`)

## Examples

### Example 1: Simple LZW Compressed File
```
Hex dump:
54 43 5A 31  10 00  00 54 00 4F 00 42 ...
|T |C |Z |1| 4096 | T  | O  | B  |...
```

### Example 2: Encrypted Huffman File
```
Hex dump:
54 43 45 31  [16 bytes salt]  [12 bytes nonce]  [ciphertext]  [16 bytes tag]
|T |C |E |1|  ...              ...                ...           ...
```

### Example 3: TCAF Archive (Per-File Mode)
```
Hex dump:
54 43 41 46  01  03  01  00 00 00 02
|T |C |A |F| v1 |DEFL|pfil| 2 files |

00 00 00 08  66 69 6C 65 2E 74 78 74  00  [timestamp]  [size]  [data_len]
| name_len  | f  i  l  e  .  t  x  t | file| ...       | ...  | ...      |

[TCD1...compressed data for file.txt...]

00 00 00 09  66 6F 6C 64 2F 66 32 2E 74 78  00  [timestamp]  [size]  [data_len]
| name_len  | f  o  l  d  /  f  2  .  t  x | file| ...       | ...  | ...      |

[TCD1...compressed data for fold/f2.tx...]
```

## Conclusion

TechCompressor's format design prioritizes:
1. **Simplicity**: Easy to parse and implement
2. **Extensibility**: Version bytes and magic headers allow evolution
3. **Security**: Path sanitization, authentication tags, no backdoors
4. **Performance**: Streaming support, chunked I/O, efficient encoding
5. **Interoperability**: Well-documented formats enable third-party tools
