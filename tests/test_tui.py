"""
Tests for TUI module (Terminal User Interface).

v2.0.0: Added Textual-based TUI for modern terminal experience.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


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

    def test_file_browser_pane_exists(self):
        """Test FileBrowserPane class exists."""
        from techcompressor.tui import FileBrowserPane
        assert FileBrowserPane is not None

    def test_operation_pane_exists(self):
        """Test OperationPane class exists."""
        from techcompressor.tui import OperationPane
        assert OperationPane is not None

    def test_action_pane_exists(self):
        """Test ActionPane class exists."""
        from techcompressor.tui import ActionPane
        assert ActionPane is not None

    def test_progress_pane_exists(self):
        """Test ProgressPane class exists."""
        from techcompressor.tui import ProgressPane
        assert ProgressPane is not None

    def test_log_pane_exists(self):
        """Test LogPane class exists."""
        from techcompressor.tui import LogPane
        assert LogPane is not None


class TestTUIEntry:
    """Test TUI entry point."""

    def test_main_function_exists(self):
        """Test that main() entry function exists."""
        from techcompressor.tui import main
        assert callable(main)


class TestPasswordModal:
    """Test PasswordModal class functionality."""

    def test_password_modal_init(self):
        """Test PasswordModal initialization."""
        from techcompressor.tui import PasswordModal
        
        modal = PasswordModal(title="Test Password")
        assert modal.title_text == "Test Password"

    def test_password_modal_default_title(self):
        """Test PasswordModal default title."""
        from techcompressor.tui import PasswordModal
        
        modal = PasswordModal()
        assert modal.title_text == "Enter Password"

    def test_password_modal_has_bindings(self):
        """Test PasswordModal has expected key bindings."""
        from techcompressor.tui import PasswordModal
        
        # Check BINDINGS class attribute exists
        assert hasattr(PasswordModal, 'BINDINGS')
        assert len(PasswordModal.BINDINGS) > 0


class TestAboutModal:
    """Test AboutModal class functionality."""

    def test_about_modal_init(self):
        """Test AboutModal initialization."""
        from techcompressor.tui import AboutModal
        
        modal = AboutModal()
        assert modal is not None

    def test_about_modal_has_bindings(self):
        """Test AboutModal has expected key bindings."""
        from techcompressor.tui import AboutModal
        
        assert hasattr(AboutModal, 'BINDINGS')


class TestArchiveContentsModal:
    """Test ArchiveContentsModal class functionality."""

    def test_archive_contents_modal_init(self):
        """Test ArchiveContentsModal initialization with contents."""
        from techcompressor.tui import ArchiveContentsModal
        
        contents = [
            {"filename": "test.txt", "original_size": 1000, "compressed_size": 500, "algorithm": "LZW"}
        ]
        modal = ArchiveContentsModal(contents)
        assert modal.contents == contents

    def test_archive_contents_modal_empty_contents(self):
        """Test ArchiveContentsModal with empty contents."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        assert modal.contents == []

    def test_archive_contents_modal_format_size(self):
        """Test ArchiveContentsModal _format_size method."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        
        # Test various size formats
        assert "B" in modal._format_size(100)
        assert "KB" in modal._format_size(2048)
        assert "MB" in modal._format_size(1024 * 1024 * 2)
        assert "GB" in modal._format_size(1024 * 1024 * 1024 * 2)


class TestFileBrowserPane:
    """Test FileBrowserPane class functionality."""

    def test_file_browser_pane_init(self):
        """Test FileBrowserPane initialization."""
        from techcompressor.tui import FileBrowserPane
        
        pane = FileBrowserPane(start_path=".")
        assert pane.start_path == "."
        assert pane.current_path == Path(".").resolve()

    def test_file_browser_pane_custom_path(self):
        """Test FileBrowserPane with custom start path."""
        from techcompressor.tui import FileBrowserPane
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmp:
            pane = FileBrowserPane(start_path=tmp)
            assert pane.start_path == tmp


class TestTechCompressorTUI:
    """Test TechCompressorTUI app class."""

    def test_tui_app_title(self):
        """Test TUI app has correct title."""
        from techcompressor.tui import TechCompressorTUI
        
        assert TechCompressorTUI.TITLE == "TechCompressor v2.0.0"

    def test_tui_app_subtitle(self):
        """Test TUI app has subtitle."""
        from techcompressor.tui import TechCompressorTUI
        
        assert TechCompressorTUI.SUB_TITLE == "Modern Compression Framework"

    def test_tui_app_css(self):
        """Test TUI app has CSS styling."""
        from techcompressor.tui import TechCompressorTUI
        
        assert hasattr(TechCompressorTUI, 'CSS')
        assert len(TechCompressorTUI.CSS) > 0

    def test_tui_app_bindings(self):
        """Test TUI app has key bindings."""
        from techcompressor.tui import TechCompressorTUI
        
        assert hasattr(TechCompressorTUI, 'BINDINGS')
        # Check for expected bindings
        binding_keys = [b.key for b in TechCompressorTUI.BINDINGS]
        assert "q" in binding_keys  # Quit
        assert "c" in binding_keys  # Compress
        assert "x" in binding_keys  # Extract

    def test_tui_app_init(self):
        """Test TUI app initialization."""
        from techcompressor.tui import TechCompressorTUI
        
        app = TechCompressorTUI()
        assert app.selected_path is None
        assert app.current_operation is None


class TestTUIAlgorithmChoices:
    """Test algorithm choices configuration."""

    def test_algorithm_choices_format(self):
        """Test algorithm choices have correct format."""
        from techcompressor.tui import ALGORITHM_CHOICES
        
        for choice in ALGORITHM_CHOICES:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            assert isinstance(choice[0], str)  # Display name
            assert isinstance(choice[1], str)  # Algorithm ID

    def test_algorithm_choices_display_names(self):
        """Test algorithm choices have descriptive display names."""
        from techcompressor.tui import ALGORITHM_CHOICES
        
        display_names = [choice[0] for choice in ALGORITHM_CHOICES]
        
        # Check that display names are descriptive
        for name in display_names:
            assert len(name) > 3  # Not just algorithm code
            assert "(" in name or len(name) > 5  # Has description or is descriptive

    def test_algorithm_choices_ids(self):
        """Test all expected algorithm IDs are present."""
        from techcompressor.tui import ALGORITHM_CHOICES
        
        algo_ids = [choice[1] for choice in ALGORITHM_CHOICES]
        
        expected_algos = ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI", "AUTO"]
        for algo in expected_algos:
            assert algo in algo_ids, f"Algorithm {algo} not found in choices"


class TestTUIModuleStructure:
    """Test TUI module structure and exports."""

    def test_logger_exists(self):
        """Test that logger is configured."""
        from techcompressor.tui import logger
        assert logger is not None

    def test_all_widget_classes_importable(self):
        """Test all widget classes can be imported."""
        from techcompressor.tui import (
            PasswordModal,
            AboutModal,
            FileBrowserPane,
            OperationPane,
            ActionPane,
            ProgressPane,
            LogPane,
            ArchiveContentsModal,
            TechCompressorTUI
        )
        
        # All imports successful
        assert True

    def test_main_function_signature(self):
        """Test main function can be called without args."""
        from techcompressor.tui import main
        import inspect
        
        sig = inspect.signature(main)
        # main() should take no required arguments
        for param in sig.parameters.values():
            if param.default is inspect.Parameter.empty:
                pytest.fail(f"main() has required parameter: {param.name}")
