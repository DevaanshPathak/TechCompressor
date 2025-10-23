"""Sanity tests for TechCompressor setup."""


def test_imports():
    """Test that the techcompressor package can be imported."""
    import techcompressor
    assert hasattr(techcompressor, "__version__")
