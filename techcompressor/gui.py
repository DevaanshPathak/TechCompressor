"""
TechCompressor GUI - Tkinter-based graphical interface

Provides user-friendly compression/decompression with:
- Multi-tab interface (Compress, Extract, Settings, Logs)
- Background threading for non-blocking operations
- Real-time progress updates and logging
- Password protection and algorithm selection
- Cancel/error handling with graceful degradation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import queue
import threading
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable

# Use absolute imports for PyInstaller compatibility
from techcompressor.core import compress, decompress
from techcompressor.archiver import create_archive, extract_archive, list_contents
from techcompressor.utils import get_logger

logger = get_logger(__name__)


class GUILogHandler(logging.Handler):
    """Custom logging handler that sends logs to GUI text widget."""
    
    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
    
    def emit(self, record):
        msg = self.format(record)
        # Use try-except to safely handle threading issues
        try:
            # Check if we're in the main thread
            if threading.current_thread() is threading.main_thread():
                self._append_log(msg)
            else:
                # Schedule from background thread - may fail if GUI is closing
                try:
                    self.text_widget.after(0, self._append_log, msg)
                except RuntimeError:
                    # GUI may be closing or not in main loop - silently ignore
                    pass
        except Exception:
            # Failsafe: don't crash if GUI logging fails
            pass
    
    def _append_log(self, msg):
        try:
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        except Exception:
            # Widget may be destroyed
            pass


class TechCompressorApp:
    """Main TechCompressor GUI application."""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        """Initialize the GUI application.
        
        Args:
            root: Optional Tk root window. If None, creates new root.
        """
        self.root = root or tk.Tk()
        self.root.title("TechCompressor")
        self.root.geometry("800x600")
        
        # Threading infrastructure
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.progress_queue = queue.Queue()
        self.cancel_flag = threading.Event()
        self.current_task = None
        
        # Settings
        self.compression_level = tk.IntVar(value=6)
        self.default_per_file = tk.BooleanVar(value=True)
        
        # Setup UI
        self._create_widgets()
        self._setup_logging()
        self._setup_keyboard_shortcuts()
        
        # Start progress polling
        self._poll_progress()
        
        logger.info("TechCompressor GUI initialized")
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Header frame
        header = ttk.Frame(self.root, padding="10")
        header.pack(fill='x')
        
        title_label = ttk.Label(
            header,
            text="🗜️ TechCompressor",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(side='left')
        
        # Get version dynamically
        import techcompressor
        version_label = ttk.Label(header, text=f"v{techcompressor.__version__}")
        version_label.pack(side='left', padx=10)
        
        # Main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self._create_compress_tab()
        self._create_extract_tab()
        self._create_settings_tab()
        self._create_logs_tab()
        self._create_about_tab()
    
    def _create_compress_tab(self):
        """Create the Compress tab UI."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Compress")
        
        # Input selection
        input_frame = ttk.LabelFrame(tab, text="Input", padding="5")
        input_frame.pack(fill='x', pady=5)
        
        self.compress_input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.compress_input_var, width=60).pack(side='left', padx=5)
        ttk.Button(input_frame, text="Browse File", command=self._browse_compress_file).pack(side='left', padx=2)
        ttk.Button(input_frame, text="Browse Folder", command=self._browse_compress_folder).pack(side='left', padx=2)
        
        # Output selection
        output_frame = ttk.LabelFrame(tab, text="Output Archive", padding="5")
        output_frame.pack(fill='x', pady=5)
        
        self.compress_output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.compress_output_var, width=60).pack(side='left', padx=5)
        ttk.Button(output_frame, text="Browse", command=self._browse_compress_output).pack(side='left', padx=2)
        
        # Options frame
        options_frame = ttk.LabelFrame(tab, text="Options", padding="5")
        options_frame.pack(fill='x', pady=5)
        
        # Algorithm selection
        algo_frame = ttk.Frame(options_frame)
        algo_frame.pack(fill='x', pady=2)
        ttk.Label(algo_frame, text="Algorithm:").pack(side='left', padx=5)
        self.compress_algo_var = tk.StringVar(value="AUTO")
        algo_combo = ttk.Combobox(
            algo_frame,
            textvariable=self.compress_algo_var,
            values=["AUTO"],
            state='readonly',
            width=25
        )
        algo_combo.pack(side='left', padx=5)
        
        # Per-file checkbox
        self.compress_per_file_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            algo_frame,
            text="Per-file archive (folder mode)",
            variable=self.compress_per_file_var
        ).pack(side='left', padx=10)
        
        # Password entry
        pass_frame = ttk.Frame(options_frame)
        pass_frame.pack(fill='x', pady=2)
        ttk.Label(pass_frame, text="Password:").pack(side='left', padx=5)
        self.compress_password_var = tk.StringVar()
        self.compress_password_entry = ttk.Entry(
            pass_frame,
            textvariable=self.compress_password_var,
            show='*',
            width=30
        )
        self.compress_password_entry.pack(side='left', padx=5)
        
        self.compress_show_pass_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pass_frame,
            text="Show",
            variable=self.compress_show_pass_var,
            command=self._toggle_compress_password
        ).pack(side='left', padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(tab, text="Progress", padding="5")
        progress_frame.pack(fill='both', expand=True, pady=5)
        
        self.compress_progress_var = tk.DoubleVar(value=0)
        self.compress_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.compress_progress_var,
            maximum=100
        )
        self.compress_progress_bar.pack(fill='x', pady=5)
        
        self.compress_status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.compress_status_var).pack(anchor='w')
        
        # Log text
        self.compress_log = scrolledtext.ScrolledText(progress_frame, height=8, state='disabled')
        self.compress_log.pack(fill='both', expand=True, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill='x', pady=5)
        
        self.compress_button = ttk.Button(
            action_frame,
            text="Compress",
            command=self._start_compress
        )
        self.compress_button.pack(side='left', padx=5)
        
        self.compress_cancel_button = ttk.Button(
            action_frame,
            text="Cancel",
            command=self._cancel_operation,
            state='disabled'
        )
        self.compress_cancel_button.pack(side='left', padx=5)
    
    def _create_extract_tab(self):
        """Create the Extract tab UI."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Extract")
        
        # Archive selection
        archive_frame = ttk.LabelFrame(tab, text="Archive", padding="5")
        archive_frame.pack(fill='x', pady=5)
        
        self.extract_input_var = tk.StringVar()
        ttk.Entry(archive_frame, textvariable=self.extract_input_var, width=60).pack(side='left', padx=5)
        ttk.Button(archive_frame, text="Browse", command=self._browse_extract_input).pack(side='left', padx=2)
        
        # Destination selection
        dest_frame = ttk.LabelFrame(tab, text="Destination Folder", padding="5")
        dest_frame.pack(fill='x', pady=5)
        
        self.extract_output_var = tk.StringVar()
        ttk.Entry(dest_frame, textvariable=self.extract_output_var, width=60).pack(side='left', padx=5)
        ttk.Button(dest_frame, text="Browse", command=self._browse_extract_output).pack(side='left', padx=2)
        
        # Password entry
        pass_frame = ttk.LabelFrame(tab, text="Options", padding="5")
        pass_frame.pack(fill='x', pady=5)
        
        ttk.Label(pass_frame, text="Password:").pack(side='left', padx=5)
        self.extract_password_var = tk.StringVar()
        self.extract_password_entry = ttk.Entry(
            pass_frame,
            textvariable=self.extract_password_var,
            show='*',
            width=30
        )
        self.extract_password_entry.pack(side='left', padx=5)
        
        self.extract_show_pass_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            pass_frame,
            text="Show",
            variable=self.extract_show_pass_var,
            command=self._toggle_extract_password
        ).pack(side='left', padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(tab, text="Progress", padding="5")
        progress_frame.pack(fill='both', expand=True, pady=5)
        
        self.extract_progress_var = tk.DoubleVar(value=0)
        self.extract_progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.extract_progress_var,
            maximum=100
        )
        self.extract_progress_bar.pack(fill='x', pady=5)
        
        self.extract_status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.extract_status_var).pack(anchor='w')
        
        # Log text
        self.extract_log = scrolledtext.ScrolledText(progress_frame, height=8, state='disabled')
        self.extract_log.pack(fill='both', expand=True, pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill='x', pady=5)
        
        self.extract_button = ttk.Button(
            action_frame,
            text="Extract",
            command=self._start_extract
        )
        self.extract_button.pack(side='left', padx=5)
        
        self.extract_cancel_button = ttk.Button(
            action_frame,
            text="Cancel",
            command=self._cancel_operation,
            state='disabled'
        )
        self.extract_cancel_button.pack(side='left', padx=5)
    
    def _create_settings_tab(self):
        """Create the Settings tab UI."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Settings")
        
        # Compression level
        level_frame = ttk.LabelFrame(tab, text="Compression Level", padding="10")
        level_frame.pack(fill='x', pady=5)
        
        ttk.Label(level_frame, text="Level (1-9):").pack(anchor='w')
        level_scale = ttk.Scale(
            level_frame,
            from_=1,
            to=9,
            variable=self.compression_level,
            orient='horizontal'
        )
        level_scale.pack(fill='x', pady=5)
        
        level_label = ttk.Label(level_frame, textvariable=self.compression_level)
        level_label.pack(anchor='w')
        
        ttk.Label(
            level_frame,
            text="Note: Compression level is informational. Algorithm determines actual compression.",
            font=('Arial', 8)
        ).pack(anchor='w', pady=5)
        
        # Default per-file mode
        archive_frame = ttk.LabelFrame(tab, text="Archive Defaults", padding="10")
        archive_frame.pack(fill='x', pady=5)
        
        ttk.Checkbutton(
            archive_frame,
            text="Use per-file mode by default (better for random access)",
            variable=self.default_per_file
        ).pack(anchor='w', pady=5)
        
        ttk.Label(
            archive_frame,
            text="Per-file: Each file compressed separately (better for selective extraction)\n"
                 "Single-stream: All files compressed together (better compression ratio)",
            font=('Arial', 8),
            justify='left'
        ).pack(anchor='w', pady=5)
    
    def _create_logs_tab(self):
        """Create the Logs tab UI."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Logs")
        
        # Control frame
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="Clear Logs", command=self._clear_logs).pack(side='left', padx=5)
        
        # Log viewer
        log_frame = ttk.LabelFrame(tab, text="Application Logs", padding="5")
        log_frame.pack(fill='both', expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', wrap='word')
        self.log_text.pack(fill='both', expand=True)
    
    def _create_about_tab(self):
        """Create the About tab UI with developer credits."""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="About")
        
        # Center frame for content
        center_frame = ttk.Frame(tab)
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # App name and version
        import techcompressor
        title_label = ttk.Label(
            center_frame,
            text="TechCompressor",
            font=('Arial', 24, 'bold')
        )
        title_label.pack(pady=10)
        
        version_label = ttk.Label(
            center_frame,
            text=f"Version {techcompressor.__version__}",
            font=('Arial', 12)
        )
        version_label.pack(pady=5)
        
        # Description
        desc_label = ttk.Label(
            center_frame,
            text="Multi-algorithm compression framework with encryption and archiving",
            font=('Arial', 10),
            wraplength=500,
            justify='center'
        )
        desc_label.pack(pady=10)
        
        # Developer credits
        ttk.Separator(center_frame, orient='horizontal').pack(fill='x', pady=15)
        
        dev_label = ttk.Label(
            center_frame,
            text="Developed by",
            font=('Arial', 10)
        )
        dev_label.pack(pady=5)
        
        name_label = ttk.Label(
            center_frame,
            text="Devaansh Pathak",
            font=('Arial', 14, 'bold')
        )
        name_label.pack(pady=5)
        
        # GitHub link (as clickable text)
        github_link = ttk.Label(
            center_frame,
            text="GitHub: DevaanshPathak",
            font=('Arial', 10, 'underline'),
            foreground='blue',
            cursor='hand2'
        )
        github_link.pack(pady=5)
        github_link.bind('<Button-1>', lambda e: self._open_github())
        
        # License
        ttk.Separator(center_frame, orient='horizontal').pack(fill='x', pady=15)
        
        license_label = ttk.Label(
            center_frame,
            text="MIT License - Free for personal and commercial use",
            font=('Arial', 9)
        )
        license_label.pack(pady=5)
        
        # Features summary
        features_label = ttk.Label(
            center_frame,
            text="Features: LZW, Huffman, DEFLATE | AES-256-GCM Encryption\n"
                 "Solid Compression | Recovery Records | Multi-Volume Archives\n"
                 "Incremental Backups | Advanced File Filtering",
            font=('Arial', 8),
            wraplength=500,
            justify='center'
        )
        features_label.pack(pady=10)
    
    def _open_github(self):
        """Open GitHub profile in browser."""
        import webbrowser
        webbrowser.open('https://github.com/DevaanshPathak')
        logger.info("Opening GitHub profile in browser")
    
    def _setup_logging(self):
        """Setup logging handler to route logs to GUI."""
        gui_handler = GUILogHandler(self.log_text)
        gui_handler.setLevel(logging.INFO)
        
        # Add handler to root logger and GUI logger
        logging.getLogger('techcompressor').addHandler(gui_handler)
        logger.addHandler(gui_handler)
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.root.bind('<Control-Shift-C>', lambda e: self._start_compress())
        self.root.bind('<Control-Shift-E>', lambda e: self._start_extract())
    
    # Browse methods
    def _browse_compress_file(self):
        path = filedialog.askopenfilename(title="Select File to Compress")
        if path:
            self.compress_input_var.set(path)
    
    def _browse_compress_folder(self):
        path = filedialog.askdirectory(title="Select Folder to Compress")
        if path:
            self.compress_input_var.set(path)
    
    def _browse_compress_output(self):
        path = filedialog.asksaveasfilename(
            title="Save Archive As",
            defaultextension=".tc",
            filetypes=[("TechCompressor Archive", "*.tc"), ("All Files", "*.*")]
        )
        if path:
            self.compress_output_var.set(path)
    
    def _browse_extract_input(self):
        path = filedialog.askopenfilename(
            title="Select Archive to Extract",
            filetypes=[("TechCompressor Archive", "*.tc"), ("All Files", "*.*")]
        )
        if path:
            self.extract_input_var.set(path)
    
    def _browse_extract_output(self):
        path = filedialog.askdirectory(title="Select Destination Folder")
        if path:
            self.extract_output_var.set(path)
    
    # Password toggle methods
    def _toggle_compress_password(self):
        if self.compress_show_pass_var.get():
            self.compress_password_entry.config(show='')
        else:
            self.compress_password_entry.config(show='*')
    
    def _toggle_extract_password(self):
        if self.extract_show_pass_var.get():
            self.extract_password_entry.config(show='')
        else:
            self.extract_password_entry.config(show='*')
    
    # Operation methods
    def _start_compress(self):
        """Start compression operation in background thread."""
        input_path = self.compress_input_var.get().strip()
        output_path = self.compress_output_var.get().strip()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select input and output paths")
            return
        
        input_path_obj = Path(input_path)
        if not input_path_obj.exists():
            messagebox.showerror("Error", f"Input path does not exist: {input_path}")
            return
        
        # Confirm overwrite
        if Path(output_path).exists():
            if not messagebox.askyesno("Confirm", f"Output file exists. Overwrite?\n{output_path}"):
                return
        
        # Reset state
        self.cancel_flag.clear()
        self.compress_progress_var.set(0)
        self.compress_status_var.set("Starting...")
        self._clear_text_widget(self.compress_log)
        
        # Disable buttons
        self.compress_button.config(state='disabled')
        self.compress_cancel_button.config(state='normal')
        
        # Get parameters
        algo = self.compress_algo_var.get()
        password = self.compress_password_var.get() or None
        per_file = self.compress_per_file_var.get()
        
        # Submit task
        self.current_task = self.executor.submit(
            self._compress_worker,
            input_path,
            output_path,
            algo,
            password,
            per_file
        )
        
        logger.info(f"Compression started: {input_path} -> {output_path}")
    
    def _compress_worker(self, input_path: str, output_path: str, algo: str, password: Optional[str], per_file: bool):
        """Background worker for compression."""
        try:
            input_path_obj = Path(input_path)
            
            def progress_callback(current: int, total: int):
                """Archiver progress callback: receives (current_file, total_files)."""
                if self.cancel_flag.is_set():
                    raise InterruptedError("Operation cancelled by user")
                # Calculate percentage based on file progress
                # Reserve 0-5% for initialization, 5-95% for files, 95-100% for finalization
                if total > 0:
                    file_percent = (current / total) * 90  # 90% of progress bar
                    percent = int(5 + file_percent)  # Start at 5%, end at 95%
                else:
                    percent = 5
                message = f"Compressing file {current}/{total}"
                self.progress_queue.put(('compress', percent, message))
            
            if input_path_obj.is_dir():
                # Folder compression - use archiver
                self.progress_queue.put(('compress', 0, "Initializing archive..."))
                create_archive(
                    input_path,
                    output_path,
                    algo=algo,
                    password=password,
                    per_file=per_file,
                    progress_callback=progress_callback
                )
                self.progress_queue.put(('compress', 100, "Archive created successfully!"))
            else:
                # Single file compression
                self.progress_queue.put(('compress', 10, "Reading file..."))
                data = input_path_obj.read_bytes()
                
                self.progress_queue.put(('compress', 30, f"Compressing with {algo}..."))
                compressed = compress(data, algo=algo, password=password)
                
                self.progress_queue.put(('compress', 80, "Writing output..."))
                Path(output_path).write_bytes(compressed)
                
                ratio = (len(compressed) / max(len(data), 1)) * 100
                self.progress_queue.put(('compress', 100, f"Complete! Ratio: {ratio:.1f}%"))
            
            self.progress_queue.put(('done', 'compress', None))
            self.progress_queue.put(('done', 'compress', None))
        
        except InterruptedError as e:
            self.progress_queue.put(('error', 'compress', str(e)))
        except Exception as e:
            logger.exception("Compression failed")
            self.progress_queue.put(('error', 'compress', str(e)))
    
    def _start_extract(self):
        """Start extraction operation in background thread."""
        input_path = self.extract_input_var.get().strip()
        output_path = self.extract_output_var.get().strip()
        
        if not input_path or not output_path:
            messagebox.showerror("Error", "Please select archive and destination paths")
            return
        
        if not Path(input_path).exists():
            messagebox.showerror("Error", f"Archive does not exist: {input_path}")
            return
        
        # Confirm overwrite
        output_path_obj = Path(output_path)
        if output_path_obj.exists() and list(output_path_obj.iterdir()):
            if not messagebox.askyesno("Confirm", f"Destination is not empty. Continue?\n{output_path}"):
                return
        
        # Reset state
        self.cancel_flag.clear()
        self.extract_progress_var.set(0)
        self.extract_status_var.set("Starting...")
        self._clear_text_widget(self.extract_log)
        
        # Disable buttons
        self.extract_button.config(state='disabled')
        self.extract_cancel_button.config(state='normal')
        
        # Get parameters
        password = self.extract_password_var.get() or None
        
        # Submit task
        self.current_task = self.executor.submit(
            self._extract_worker,
            input_path,
            output_path,
            password
        )
        
        logger.info(f"Extraction started: {input_path} -> {output_path}")
    
    def _extract_worker(self, input_path: str, output_path: str, password: Optional[str]):
        """Background worker for extraction."""
        try:
            def progress_callback(current: int, total: int):
                """Archiver progress callback: receives (current_file, total_files)."""
                if self.cancel_flag.is_set():
                    raise InterruptedError("Operation cancelled by user")
                # Calculate percentage based on file progress
                # Reserve 0-5% for initialization, 5-95% for files, 95-100% for finalization
                if total > 0:
                    file_percent = (current / total) * 90  # 90% of progress bar
                    percent = int(5 + file_percent)  # Start at 5%, end at 95%
                else:
                    percent = 5
                message = f"Extracting file {current}/{total}"
                self.progress_queue.put(('extract', percent, message))
            
            self.progress_queue.put(('extract', 0, "Reading archive..."))
            
            # Check if it's an archive or compressed file
            with open(input_path, 'rb') as f:
                magic = f.read(4)
            
            if magic == b"TCAF":
                # Archive extraction
                self.progress_queue.put(('extract', 5, "Extracting archive..."))
                extract_archive(
                    input_path,
                    output_path,
                    password=password,
                    progress_callback=progress_callback
                )
                self.progress_queue.put(('extract', 100, "Archive extracted successfully!"))
            else:
                # Single file decompression
                self.progress_queue.put(('extract', 10, "Reading compressed file..."))
                compressed = Path(input_path).read_bytes()
                
                # Use AUTO decompression which detects format from header
                self.progress_queue.put(('extract', 30, "Decompressing (auto-detect)..."))
                data = decompress(compressed, algo="AUTO", password=password)
                
                self.progress_queue.put(('extract', 80, "Writing output..."))
                # Save to output folder with original name
                output_file = Path(output_path) / Path(input_path).stem
                output_file.write_bytes(data)
                
                self.progress_queue.put(('extract', 100, f"Complete! Decompressed: {len(data):,} bytes"))
            
            self.progress_queue.put(('done', 'extract', None))
            self.progress_queue.put(('done', 'extract', None))
        
        except InterruptedError as e:
            self.progress_queue.put(('error', 'extract', str(e)))
        except Exception as e:
            logger.exception("Extraction failed")
            self.progress_queue.put(('error', 'extract', str(e)))
    
    def _cancel_operation(self):
        """Cancel current operation."""
        if messagebox.askyesno("Confirm", "Cancel current operation?"):
            self.cancel_flag.set()
            logger.warning("Operation cancelled by user")
    
    def _poll_progress(self):
        """Poll progress queue and update UI."""
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                
                if msg[0] == 'compress':
                    percent, message = msg[1], msg[2]
                    self.compress_progress_var.set(percent)
                    self.compress_status_var.set(message)
                    self._append_to_text_widget(self.compress_log, message)
                
                elif msg[0] == 'extract':
                    percent, message = msg[1], msg[2]
                    self.extract_progress_var.set(percent)
                    self.extract_status_var.set(message)
                    self._append_to_text_widget(self.extract_log, message)
                
                elif msg[0] == 'done':
                    operation = msg[1]
                    if operation == 'compress':
                        self.compress_button.config(state='normal')
                        self.compress_cancel_button.config(state='disabled')
                        # Success status already shown in progress bar and status label
                    elif operation == 'extract':
                        self.extract_button.config(state='normal')
                        self.extract_cancel_button.config(state='disabled')
                        # Success status already shown in progress bar and status label
                
                elif msg[0] == 'error':
                    operation, error = msg[1], msg[2]
                    if operation == 'compress':
                        self.compress_button.config(state='normal')
                        self.compress_cancel_button.config(state='disabled')
                        self.compress_status_var.set(f"Error: {error}")
                    elif operation == 'extract':
                        self.extract_button.config(state='normal')
                        self.extract_cancel_button.config(state='disabled')
                        self.extract_status_var.set(f"Error: {error}")
                    
                    messagebox.showerror("Error", f"Operation failed:\n{error}")
        
        except queue.Empty:
            pass
        
        # Schedule next poll
        self.root.after(100, self._poll_progress)
    
    def _clear_text_widget(self, widget):
        """Clear text widget content."""
        widget.configure(state='normal')
        widget.delete('1.0', tk.END)
        widget.configure(state='disabled')
    
    def _append_to_text_widget(self, widget, text):
        """Append text to widget."""
        widget.configure(state='normal')
        widget.insert(tk.END, text + '\n')
        widget.see(tk.END)
        widget.configure(state='disabled')
    
    def _clear_logs(self):
        """Clear application logs."""
        self._clear_text_widget(self.log_text)
        logger.info("Logs cleared")
    
    def run(self):
        """Run the application main loop."""
        self.root.mainloop()
    
    def destroy(self):
        """Cleanup and destroy the application."""
        self.executor.shutdown(wait=False)
        self.root.destroy()


def main():
    """Entry point for GUI application."""
    app = TechCompressorApp()
    app.run()


if __name__ == '__main__':
    main()
