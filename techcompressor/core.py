"""Core compression and decompression API for TechCompressor."""


def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """Placeholder compression entry point."""
    raise NotImplementedError("Phase 2 will implement compression.")


def decompress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
    """Placeholder decompression entry point."""
    raise NotImplementedError("Phase 2 will implement decompression.")
