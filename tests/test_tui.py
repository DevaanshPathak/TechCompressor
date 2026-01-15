"""
Tests for TUI module (Terminal User Interface).

v2.0.0: Added Textual-based TUI for modern terminal experience.
"""

import pytest


class TestTUIImports:
    """Test that TUI module imports correctly."""

    def test_tui_module_imports(self):
        """Test that TUI module can be imported."""
        from techcompressor import tui
        assert hasattr(tui, 'main')
        assert hasattr(tui, 'TechCompressorTUI')

    def test_tui_app_class_exists(self):
        """Test that TUI app class exists and has expected attributes."""
        from techcompressor.tui import TechCompressorTUI
        
        # Check class exists
        assert TechCompressorTUI is not None
        
        # Check it's a Textual App subclass
        from textual.app import App
        assert issubclass(TechCompressorTUI, App)

    def test_tui_constants(self):
        """Test TUI module constants."""
        from techcompressor.tui import ALGORITHM_CHOICES
        
        # Should have all supported algorithms
        algo_values = [choice[1] for choice in ALGORITHM_CHOICES]
        assert "ZSTD" in algo_values
        assert "LZW" in algo_values
        assert "HUFFMAN" in algo_values
        assert "DEFLATE" in algo_values
        assert "BROTLI" in algo_values
        assert "AUTO" in algo_values


class TestTUIWidgets:
    """Test TUI widget classes."""

    def test_password_modal_exists(self):
        """Test PasswordModal class exists."""
        from techcompressor.tui import PasswordModal
        assert PasswordModal is not None

    def test_about_modal_exists(self):
        """Test AboutModal class exists."""
        from techcompressor.tui import AboutModal
        assert AboutModal is not None

    def test_archive_contents_modal_exists(self):
        """Test ArchiveContentsModal class exists."""
        from techcompressor.tui import ArchiveContentsModal
        assert ArchiveContentsModal is not None


class TestTUIEntry:
    """Test TUI entry point."""

    def test_main_function_exists(self):
        """Test that main() entry function exists."""
        from techcompressor.tui import main
        assert callable(main)
