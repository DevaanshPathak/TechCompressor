"""TechCompressor - Modular Compression Framework (Release 2.0.0).

v2.0.0 introduces:
- Textual TUI (Terminal User Interface)
- Zstandard (zstd) compression algorithm
- Brotli compression algorithm
"""
__version__ = "2.0.0"

from .core import reset_solid_compression_state, compress, decompress, is_likely_compressed

__all__ = ["reset_solid_compression_state", "compress", "decompress", "is_likely_compressed"]
