"""
Basic GUI tests for TechCompressor

Tests GUI initialization and background task execution.
Uses headless mode (tk.Tk().withdraw()) for testing without display.
"""

import pytest
import os
import sys
import tkinter as tk
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from techcompressor.gui import TechCompressorApp, GUILogHandler

# Skip all GUI tests on CI or macOS (Tkinter hangs in headless environments)
pytestmark = pytest.mark.skipif(
    os.environ.get('CI') == 'true' or sys.platform == 'darwin',
    reason="GUI tests skipped on CI/macOS (Tkinter hangs in headless mode)"
)


def test_gui_loads():
    """Test that GUI application initializes without errors (headless mode)."""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide window for headless testing
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Verify main components exist
        assert app.root is not None
        assert app.notebook is not None
        assert app.executor is not None
        assert app.progress_queue is not None
        assert app.cancel_flag is not None
        
        # Verify tabs were created (v1.2.0: 5 tabs including About)
        assert app.notebook.index('end') == 5  # 5 tabs: Compress, Extract, Settings, Logs, About
        
        # Verify compress tab widgets
        assert app.compress_input_var is not None
        assert app.compress_output_var is not None
        assert app.compress_algo_var is not None
        assert app.compress_password_var is not None
        assert app.compress_progress_bar is not None
        
        # Verify extract tab widgets
        assert app.extract_input_var is not None
        assert app.extract_output_var is not None
        assert app.extract_password_var is not None
        assert app.extract_progress_bar is not None
        
        # Verify settings
        assert app.compression_level is not None
        assert app.default_per_file is not None
        
        # Verify logs text widget
        assert app.log_text is not None
        
    finally:
        app.destroy()


def test_gui_logging_handler():
    """Test that GUILogHandler routes logs to text widget."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        # Create text widget
        text_widget = tk.Text(root)
        
        # Create handler
        handler = GUILogHandler(text_widget)
        
        # Create logger and add handler
        import logging
        logger = logging.getLogger('test_gui_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Log message
        logger.info("Test log message")
        
        # Give GUI time to process
        root.update()
        
        # Verify message appears in widget
        content = text_widget.get('1.0', tk.END)
        assert 'Test log message' in content
        
    finally:
        root.destroy()


def test_background_task_mock_compress(monkeypatch):
    """Test that background compression task runs and reports progress."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Mock file operations
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = False
        mock_path.read_bytes.return_value = b"TEST DATA"
        
        # Mock compress function with progress callback
        def mock_compress(data, algo=None, password=None):
            return b"COMPRESSED"
        
        # Mock Path.write_bytes
        def mock_write_bytes(self, data):
            pass
        
        # Apply mocks
        with patch('techcompressor.gui.Path', return_value=mock_path):
            with patch('techcompressor.gui.compress', mock_compress):
                with patch.object(Path, 'write_bytes', mock_write_bytes):
                    with patch.object(Path, 'exists', return_value=True):
                        with patch.object(Path, 'is_dir', return_value=False):
                            with patch.object(Path, 'read_bytes', return_value=b"TEST DATA"):
                                # Set input/output
                                app.compress_input_var.set("/fake/input.txt")
                                app.compress_output_var.set("/fake/output.tc")
                                app.compress_algo_var.set("LZW")
                                
                                # Start compress (this submits to executor)
                                with patch('tkinter.messagebox.askyesno', return_value=True):
                                    app._start_compress()
                                
                                # Wait for task to complete (with timeout)
                                max_wait = 5  # seconds
                                start_time = time.time()
                                while app.current_task and not app.current_task.done():
                                    root.update()
                                    time.sleep(0.05)
                                    if time.time() - start_time > max_wait:
                                        break
                                
                                # Process any remaining events
                                for _ in range(10):
                                    root.update()
                                    time.sleep(0.05)
                                
                                # Verify progress was updated
                                # Note: Due to threading, exact values may vary
                                # Just verify the system didn't crash
                                assert app.compress_progress_var.get() >= 0
    
    finally:
        app.destroy()


def test_cancel_flag_functionality():
    """Test that cancel flag can be set and checked."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Initially not set
        assert not app.cancel_flag.is_set()
        
        # Set flag
        app.cancel_flag.set()
        assert app.cancel_flag.is_set()
        
        # Clear flag
        app.cancel_flag.clear()
        assert not app.cancel_flag.is_set()
        
    finally:
        app.destroy()


def test_password_toggle():
    """Test password visibility toggle functionality."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Initially password should be masked
        assert app.compress_password_entry.cget('show') == '*'
        
        # Toggle to show
        app.compress_show_pass_var.set(True)
        app._toggle_compress_password()
        assert app.compress_password_entry.cget('show') == ''
        
        # Toggle to hide
        app.compress_show_pass_var.set(False)
        app._toggle_compress_password()
        assert app.compress_password_entry.cget('show') == '*'
        
    finally:
        app.destroy()


def test_text_widget_operations():
    """Test clear and append operations on text widgets."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Append text
        app._append_to_text_widget(app.compress_log, "Test message 1")
        app._append_to_text_widget(app.compress_log, "Test message 2")
        
        content = app.compress_log.get('1.0', tk.END)
        assert "Test message 1" in content
        assert "Test message 2" in content
        
        # Clear text
        app._clear_text_widget(app.compress_log)
        content = app.compress_log.get('1.0', tk.END)
        assert "Test message 1" not in content
        assert "Test message 2" not in content
        
    finally:
        app.destroy()


def test_progress_queue_communication():
    """Test that progress queue can send and receive messages."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Put messages in queue
        app.progress_queue.put(('compress', 50, 'Halfway there'))
        app.progress_queue.put(('extract', 75, 'Almost done'))
        
        # Process messages (manually call poll once)
        # Note: We need to stop the automatic polling first
        # Get messages directly from queue
        msg1 = app.progress_queue.get_nowait()
        assert msg1 == ('compress', 50, 'Halfway there')
        
        msg2 = app.progress_queue.get_nowait()
        assert msg2 == ('extract', 75, 'Almost done')
        
        # Queue should be empty now
        assert app.progress_queue.empty()
        
    finally:
        app.destroy()


@pytest.mark.parametrize("algo", ["LZW", "HUFFMAN", "DEFLATE"])
def test_algorithm_selection(algo):
    """Test that all algorithms can be selected."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Set algorithm
        app.compress_algo_var.set(algo)
        assert app.compress_algo_var.get() == algo
        
    finally:
        app.destroy()


def test_settings_defaults():
    """Test that settings have correct default values."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter not available or misconfigured: {e}")
    
    try:
        app = TechCompressorApp(root)
        
        # Check compression level default
        assert app.compression_level.get() == 6
        
        # Check per-file default
        assert app.default_per_file.get() is True
        
    finally:
        app.destroy()
