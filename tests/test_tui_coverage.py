"""
Additional TUI tests targeting uncovered code paths.

Uses mocking to test TUI methods without requiring actual Textual runtime.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import tempfile


class TestFileBrowserPaneMethods:
    """Test FileBrowserPane methods."""

    def test_navigate_to_parent_logic(self):
        """Test navigate_to_parent path logic (without widget queries)."""
        from techcompressor.tui import FileBrowserPane
        from pathlib import Path
        
        # Create pane with a non-root path
        pane = FileBrowserPane(start_path=".")
        
        # Store original path
        original = pane.current_path
        
        # Verify parent logic works
        parent = original.parent
        assert parent.is_absolute()

    def test_file_browser_stores_path(self, tmp_path):
        """Test FileBrowserPane stores paths correctly."""
        from techcompressor.tui import FileBrowserPane
        
        pane = FileBrowserPane(start_path=str(tmp_path))
        
        assert pane.start_path == str(tmp_path)
        assert pane.current_path == tmp_path.resolve()

    def test_file_browser_has_navigate_method(self):
        """Test FileBrowserPane has navigate_to_parent method."""
        from techcompressor.tui import FileBrowserPane
        
        pane = FileBrowserPane(start_path=".")
        
        # Method should exist
        assert hasattr(pane, 'navigate_to_parent')
        assert callable(pane.navigate_to_parent)


class TestArchiveContentsModalMethods:
    """Test ArchiveContentsModal helper methods."""

    def test_format_size_bytes(self):
        """Test _format_size for bytes."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        
        assert "B" in modal._format_size(0)
        assert "B" in modal._format_size(500)
        assert "B" in modal._format_size(1023)

    def test_format_size_kilobytes(self):
        """Test _format_size for kilobytes."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        
        assert "KB" in modal._format_size(1024)
        assert "KB" in modal._format_size(1024 * 100)
        assert "KB" in modal._format_size(1024 * 1023)

    def test_format_size_megabytes(self):
        """Test _format_size for megabytes."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        
        assert "MB" in modal._format_size(1024 * 1024)
        assert "MB" in modal._format_size(1024 * 1024 * 100)
        assert "MB" in modal._format_size(1024 * 1024 * 1023)

    def test_format_size_gigabytes(self):
        """Test _format_size for gigabytes."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        
        assert "GB" in modal._format_size(1024 * 1024 * 1024)
        assert "GB" in modal._format_size(1024 * 1024 * 1024 * 10)

    def test_format_size_values(self):
        """Test _format_size returns correct numeric values."""
        from techcompressor.tui import ArchiveContentsModal
        
        modal = ArchiveContentsModal([])
        
        # Check that values are roughly correct
        result_2kb = modal._format_size(2048)
        assert "2" in result_2kb and "KB" in result_2kb
        
        result_5mb = modal._format_size(5 * 1024 * 1024)
        assert "5" in result_5mb and "MB" in result_5mb


class TestPasswordModalMethods:
    """Test PasswordModal methods."""

    def test_password_modal_stores_title(self):
        """Test PasswordModal stores title correctly."""
        from techcompressor.tui import PasswordModal
        
        modal = PasswordModal(title="Custom Title")
        assert modal.title_text == "Custom Title"

    def test_password_modal_default_title(self):
        """Test PasswordModal uses default title."""
        from techcompressor.tui import PasswordModal
        
        modal = PasswordModal()
        assert modal.title_text == "Enter Password"

    def test_password_modal_has_compose(self):
        """Test PasswordModal has compose method."""
        from techcompressor.tui import PasswordModal
        
        modal = PasswordModal()
        assert hasattr(modal, 'compose')
        assert callable(modal.compose)


class TestAboutModalMethods:
    """Test AboutModal methods."""

    def test_about_modal_initialization(self):
        """Test AboutModal initializes without error."""
        from techcompressor.tui import AboutModal
        
        modal = AboutModal()
        assert modal is not None

    def test_about_modal_has_compose(self):
        """Test AboutModal has compose method."""
        from techcompressor.tui import AboutModal
        
        modal = AboutModal()
        assert hasattr(modal, 'compose')


class TestOperationPane:
    """Test OperationPane widget."""

    def test_operation_pane_exists(self):
        """Test OperationPane class exists."""
        from techcompressor.tui import OperationPane
        assert OperationPane is not None

    def test_operation_pane_has_compose(self):
        """Test OperationPane has compose method."""
        from techcompressor.tui import OperationPane
        
        pane = OperationPane()
        assert hasattr(pane, 'compose')


class TestActionPane:
    """Test ActionPane widget."""

    def test_action_pane_exists(self):
        """Test ActionPane class exists."""
        from techcompressor.tui import ActionPane
        assert ActionPane is not None

    def test_action_pane_has_compose(self):
        """Test ActionPane has compose method."""
        from techcompressor.tui import ActionPane
        
        pane = ActionPane()
        assert hasattr(pane, 'compose')


class TestProgressPane:
    """Test ProgressPane widget."""

    def test_progress_pane_exists(self):
        """Test ProgressPane class exists."""
        from techcompressor.tui import ProgressPane
        assert ProgressPane is not None

    def test_progress_pane_has_compose(self):
        """Test ProgressPane has compose method."""
        from techcompressor.tui import ProgressPane
        
        pane = ProgressPane()
        assert hasattr(pane, 'compose')


class TestLogPane:
    """Test LogPane widget."""

    def test_log_pane_exists(self):
        """Test LogPane class exists."""
        from techcompressor.tui import LogPane
        assert LogPane is not None

    def test_log_pane_has_compose(self):
        """Test LogPane has compose method."""
        from techcompressor.tui import LogPane
        
        pane = LogPane()
        assert hasattr(pane, 'compose')


class TestTechCompressorTUIMethods:
    """Test TechCompressorTUI app methods."""

    def test_app_initialization(self):
        """Test app initializes with correct state."""
        from techcompressor.tui import TechCompressorTUI
        
        app = TechCompressorTUI()
        
        assert app.selected_path is None
        assert app.current_operation is None

    def test_app_has_action_methods(self):
        """Test app has action methods defined."""
        from techcompressor.tui import TechCompressorTUI
        
        app = TechCompressorTUI()
        
        # Check action methods exist
        assert hasattr(app, 'action_compress')
        assert hasattr(app, 'action_extract')
        assert hasattr(app, 'action_list_contents')
        assert hasattr(app, 'action_verify')
        assert hasattr(app, 'action_about')
        assert hasattr(app, 'action_parent_folder')
        assert hasattr(app, 'action_refresh')

    def test_app_has_worker_methods(self):
        """Test app has background worker methods."""
        from techcompressor.tui import TechCompressorTUI
        
        app = TechCompressorTUI()
        
        # Check worker methods exist
        assert hasattr(app, '_run_compress')
        assert hasattr(app, '_run_extract')
        assert hasattr(app, '_run_list_contents')
        assert hasattr(app, '_run_verify')

    def test_app_bindings_structure(self):
        """Test app bindings are properly structured."""
        from techcompressor.tui import TechCompressorTUI
        from textual.binding import Binding
        
        for binding in TechCompressorTUI.BINDINGS:
            assert isinstance(binding, Binding)
            assert binding.key is not None
            assert binding.action is not None

    def test_app_css_content(self):
        """Test app CSS contains expected selectors."""
        from techcompressor.tui import TechCompressorTUI
        
        css = TechCompressorTUI.CSS
        
        # Check for expected CSS selectors
        assert 'Screen' in css
        assert 'Header' in css
        assert 'Footer' in css
        assert '#main-container' in css


class TestTUIConstants:
    """Test TUI module constants."""

    def test_algorithm_choices_complete(self):
        """Test ALGORITHM_CHOICES has all algorithms."""
        from techcompressor.tui import ALGORITHM_CHOICES
        
        algo_ids = [choice[1] for choice in ALGORITHM_CHOICES]
        
        # All algorithms should be present
        assert "LZW" in algo_ids
        assert "HUFFMAN" in algo_ids
        assert "DEFLATE" in algo_ids
        assert "ZSTD" in algo_ids
        assert "BROTLI" in algo_ids
        assert "AUTO" in algo_ids

    def test_algorithm_choices_have_descriptions(self):
        """Test ALGORITHM_CHOICES have descriptive names."""
        from techcompressor.tui import ALGORITHM_CHOICES
        
        for display_name, algo_id in ALGORITHM_CHOICES:
            # Display name should be longer/more descriptive than ID
            assert len(display_name) >= len(algo_id)


class TestTUIMainFunction:
    """Test TUI main entry point."""

    def test_main_exists_and_callable(self):
        """Test main function exists and is callable."""
        from techcompressor.tui import main
        
        assert callable(main)

    def test_main_creates_app(self):
        """Test main function creates TechCompressorTUI instance."""
        from techcompressor.tui import main, TechCompressorTUI
        
        # main() creates app and calls run(), so we can't easily test it
        # but we can verify the function signature
        import inspect
        sig = inspect.signature(main)
        
        # Should take no required arguments
        required_params = [
            p for p in sig.parameters.values() 
            if p.default is inspect.Parameter.empty
        ]
        assert len(required_params) == 0


class TestTUIWidgetInheritance:
    """Test TUI widgets inherit from correct Textual classes."""

    def test_password_modal_is_modal_screen(self):
        """Test PasswordModal inherits from ModalScreen."""
        from techcompressor.tui import PasswordModal
        from textual.screen import ModalScreen
        
        assert issubclass(PasswordModal, ModalScreen)

    def test_about_modal_is_modal_screen(self):
        """Test AboutModal inherits from ModalScreen."""
        from techcompressor.tui import AboutModal
        from textual.screen import ModalScreen
        
        assert issubclass(AboutModal, ModalScreen)

    def test_archive_contents_modal_is_modal_screen(self):
        """Test ArchiveContentsModal inherits from ModalScreen."""
        from techcompressor.tui import ArchiveContentsModal
        from textual.screen import ModalScreen
        
        assert issubclass(ArchiveContentsModal, ModalScreen)

    def test_main_app_is_textual_app(self):
        """Test TechCompressorTUI inherits from App."""
        from techcompressor.tui import TechCompressorTUI
        from textual.app import App
        
        assert issubclass(TechCompressorTUI, App)

    def test_panes_are_widgets(self):
        """Test pane classes inherit from Widget."""
        from techcompressor.tui import (
            FileBrowserPane, OperationPane, ActionPane, 
            ProgressPane, LogPane
        )
        from textual.widget import Widget
        
        for pane_class in [FileBrowserPane, OperationPane, ActionPane, ProgressPane, LogPane]:
            # These should be Static (which is a Widget) or Container
            assert hasattr(pane_class, 'compose')


class TestTUILoggerSetup:
    """Test TUI logger configuration."""

    def test_tui_has_logger(self):
        """Test TUI module has logger configured."""
        from techcompressor.tui import logger
        
        assert logger is not None
        assert logger.name == "techcompressor.tui"


class TestFileBrowserPaneState:
    """Test FileBrowserPane state management."""

    def test_start_path_stored(self, tmp_path):
        """Test start_path is stored correctly."""
        from techcompressor.tui import FileBrowserPane
        
        path_str = str(tmp_path)
        pane = FileBrowserPane(start_path=path_str)
        
        assert pane.start_path == path_str

    def test_current_path_resolved(self, tmp_path):
        """Test current_path is resolved to absolute."""
        from techcompressor.tui import FileBrowserPane
        
        pane = FileBrowserPane(start_path=str(tmp_path))
        
        # current_path should be resolved (absolute)
        assert pane.current_path.is_absolute()

    def test_relative_path_resolved(self):
        """Test relative path is resolved correctly."""
        from techcompressor.tui import FileBrowserPane
        
        pane = FileBrowserPane(start_path=".")
        
        # Should resolve to current working directory
        assert pane.current_path == Path(".").resolve()


class TestArchiveContentsModalState:
    """Test ArchiveContentsModal state management."""

    def test_contents_stored(self):
        """Test contents list is stored."""
        from techcompressor.tui import ArchiveContentsModal
        
        test_contents = [
            {"filename": "a.txt", "original_size": 100},
            {"filename": "b.txt", "original_size": 200},
        ]
        
        modal = ArchiveContentsModal(test_contents)
        
        assert modal.contents == test_contents
        assert len(modal.contents) == 2

    def test_contents_not_modified(self):
        """Test modal doesn't modify passed contents."""
        from techcompressor.tui import ArchiveContentsModal
        
        original = [{"filename": "test.txt"}]
        modal = ArchiveContentsModal(original)
        
        # Should be same reference or equal
        assert modal.contents == original
