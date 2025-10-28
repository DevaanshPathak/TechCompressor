"""TechCompressor – Modular Compression Framework (Release 1.3.0)."""
__version__ = "1.3.0"

from .core import reset_solid_compression_state, compress, decompress, is_likely_compressed

__all__ = ["reset_solid_compression_state", "compress", "decompress", "is_likely_compressed"]
