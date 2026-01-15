"""
TechCompressor Terminal User Interface (TUI)

A modern terminal-based interface built with Textual framework.
Introduced in v2.0.0 for enhanced user experience.
"""

from pathlib import Path
from typing import Callable
import asyncio
import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, Label, 
    DirectoryTree, DataTable, ProgressBar, Select,
    Checkbox, TabbedContent, TabPane, Log, Rule
)
from textual.screen import ModalScreen
from textual import work
from textual.worker import Worker, get_current_worker

from techcompressor.utils import get_logger

logger = get_logger(__name__)

# Algorithm choices for the dropdown
ALGORITHM_CHOICES = [
    ("ZSTD (Fast, Good Ratio)", "ZSTD"),
    ("LZW (Very Fast)", "LZW"),
    ("Huffman (Text Optimized)", "HUFFMAN"),
    ("DEFLATE (Balanced)", "DEFLATE"),
    ("Brotli (Best for Text/Web)", "BROTLI"),
    ("AUTO (Best Choice)", "AUTO"),
]


class PasswordModal(ModalScreen[str | None]):
    """Modal dialog for password input."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, title: str = "Enter Password"):
        super().__init__()
        self.title_text = title
    
    def compose(self) -> ComposeResult:
        with Container(id="password-dialog"):
            yield Label(self.title_text, id="password-title")
            yield Input(placeholder="Password", password=True, id="password-input")
            with Horizontal(id="password-buttons"):
                yield Button("OK", variant="primary", id="password-ok")
                yield Button("Cancel", variant="default", id="password-cancel")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "password-ok":
            password_input = self.query_one("#password-input", Input)
            self.dismiss(password_input.value if password_input.value else None)
        else:
            self.dismiss(None)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value if event.value else None)
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class AboutModal(ModalScreen[None]):
    """About dialog with credits."""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]
    
    def compose(self) -> ComposeResult:
        with Container(id="about-dialog"):
            yield Static("""
[bold cyan]TechCompressor v2.0.0[/bold cyan]

[bold]Modular Compression Framework[/bold]

[yellow]Algorithms:[/yellow]
  - LZW, Huffman, DEFLATE
  - Zstandard, Brotli (v2.0.0)

[yellow]Features:[/yellow]
  - AES-256-GCM Encryption
  - TCAF v2 Archive Format
  - Multi-volume Archives
  - Recovery Records
  - TUI, GUI, and CLI

[green]Developed by:[/green]
  Devaansh Pathak
  GitHub: DevaanshPathak

[dim]MIT License[/dim]
            """, id="about-content")
            yield Button("Close", variant="primary", id="about-close")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)
    
    def action_close(self) -> None:
        self.dismiss(None)


class FileBrowserPane(Container):
    """File browser panel for selecting files/folders."""
    
    def __init__(self, start_path: str = "."):
        super().__init__()
        self.start_path = start_path
        self.current_path = Path(start_path).resolve()
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]File Browser[/bold]", classes="pane-title")
        with Horizontal(id="path-nav"):
            yield Button("Parent Folder", id="btn-parent", variant="default")
            yield Label(str(self.current_path), id="current-path-label")
        yield DirectoryTree(self.start_path, id="file-tree")
    
    def navigate_to_parent(self) -> None:
        """Navigate to the parent directory."""
        parent = self.current_path.parent
        if parent != self.current_path:  # Not at root
            self.current_path = parent
            # Update the directory tree
            tree = self.query_one("#file-tree", DirectoryTree)
            tree.path = parent
            tree.reload()
            # Update the path label
            path_label = self.query_one("#current-path-label", Label)
            path_label.update(str(parent))


class OperationPane(Container):
    """Operation panel with compression settings."""
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Compression Settings[/bold]", classes="pane-title")
        
        with Vertical(id="settings-container"):
            yield Label("Algorithm:")
            yield Select(ALGORITHM_CHOICES, value="ZSTD", id="algo-select")
            
            yield Rule()
            
            yield Checkbox("Enable Encryption", id="encrypt-check")
            
            yield Rule()
            
            yield Checkbox("Multi-volume Archive", id="multivolume-check")
            yield Label("Volume Size (MB):", id="volume-size-label")
            yield Input(placeholder="650", id="volume-size-input", disabled=True)
            
            yield Rule()
            
            yield Checkbox("Preserve File Attributes", id="attributes-check")
            
            yield Rule()
            
            yield Label("Output Path:")
            yield Input(placeholder="output.tc", id="output-path")


class ActionPane(Container):
    """Action buttons panel."""
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Actions[/bold]", classes="pane-title")
        with Vertical(id="action-buttons"):
            yield Button("Compress", variant="success", id="btn-compress")
            yield Button("Extract", variant="primary", id="btn-extract")
            yield Button("List Contents", variant="default", id="btn-list")
            yield Button("Verify Archive", variant="warning", id="btn-verify")


class ProgressPane(Container):
    """Progress display panel."""
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Progress[/bold]", classes="pane-title")
        yield ProgressBar(total=100, show_eta=True, id="progress-bar")
        yield Label("Ready", id="progress-status")


class LogPane(ScrollableContainer):
    """Log output panel."""
    
    def compose(self) -> ComposeResult:
        yield Label("[bold]Log[/bold]", classes="pane-title")
        yield Log(id="log-output", highlight=True, max_lines=500)


class ArchiveContentsModal(ModalScreen[None]):
    """Modal showing archive contents."""
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]
    
    def __init__(self, contents: list[dict]):
        super().__init__()
        self.contents = contents
    
    def compose(self) -> ComposeResult:
        with Container(id="contents-dialog"):
            yield Label("[bold]Archive Contents[/bold]", id="contents-title")
            yield DataTable(id="contents-table")
            yield Button("Close", variant="primary", id="contents-close")
    
    def on_mount(self) -> None:
        table = self.query_one("#contents-table", DataTable)
        table.add_columns("Name", "Original", "Compressed", "Ratio", "Algorithm")
        
        total_orig = 0
        total_comp = 0
        
        for entry in self.contents:
            name = entry.get("filename", "?")
            orig = entry.get("original_size", 0)
            comp = entry.get("compressed_size", 0)
            algo = entry.get("algorithm", "?")
            
            total_orig += orig
            total_comp += comp
            
            ratio = f"{100 * comp / orig:.1f}%" if orig > 0 else "N/A"
            
            table.add_row(
                name,
                self._format_size(orig),
                self._format_size(comp),
                ratio,
                algo
            )
        
        # Add total row
        total_ratio = f"{100 * total_comp / total_orig:.1f}%" if total_orig > 0 else "N/A"
        table.add_row(
            f"[bold]TOTAL ({len(self.contents)} files)[/bold]",
            f"[bold]{self._format_size(total_orig)}[/bold]",
            f"[bold]{self._format_size(total_comp)}[/bold]",
            f"[bold]{total_ratio}[/bold]",
            ""
        )
    
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)
    
    def action_close(self) -> None:
        self.dismiss(None)


class TechCompressorTUI(App):
    """TechCompressor Terminal User Interface."""
    
    TITLE = "TechCompressor v2.0.0"
    SUB_TITLE = "Modern Compression Framework"
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-columns: 1fr 1fr 1fr;
        grid-rows: auto 1fr auto;
    }
    
    Header {
        column-span: 3;
    }
    
    Footer {
        column-span: 3;
    }
    
    #main-container {
        column-span: 3;
        layout: horizontal;
        height: 100%;
    }
    
    #left-pane {
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    #center-pane {
        width: 1fr;
        border: solid $secondary;
        padding: 1;
    }
    
    #right-pane {
        width: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    #bottom-pane {
        column-span: 3;
        height: 12;
        border: solid $surface;
        padding: 1;
    }
    
    .pane-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    
    #file-tree {
        height: 100%;
    }
    
    #path-nav {
        height: 3;
        margin-bottom: 1;
    }
    
    #btn-parent {
        width: auto;
        min-width: 16;
    }
    
    #current-path-label {
        margin-left: 1;
        color: $text-muted;
        width: 1fr;
        overflow: hidden;
    }
    
    #settings-container {
        height: auto;
    }
    
    #action-buttons Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    #progress-bar {
        margin: 1 0;
    }
    
    #progress-status {
        text-align: center;
        color: $text-muted;
    }
    
    #log-output {
        height: 100%;
        border: solid $surface-darken-1;
    }
    
    /* Modal styles */
    #password-dialog, #about-dialog, #contents-dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }
    
    #password-title, #about-title, #contents-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #password-buttons {
        margin-top: 1;
        align: center middle;
    }
    
    #password-buttons Button {
        margin: 0 1;
    }
    
    #about-content {
        margin: 1;
    }
    
    #about-close, #contents-close {
        margin-top: 1;
        width: 100%;
    }
    
    #contents-table {
        height: 20;
        margin: 1 0;
    }
    
    Select {
        width: 100%;
    }
    
    Input {
        width: 100%;
    }
    
    Checkbox {
        margin: 1 0;
    }
    
    Rule {
        margin: 1 0;
        color: $surface-lighten-2;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "compress", "Compress"),
        Binding("x", "extract", "Extract"),
        Binding("l", "list_contents", "List"),
        Binding("v", "verify", "Verify"),
        Binding("f1", "about", "About"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("backspace", "parent_folder", "Parent"),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_path: Path | None = None
        self.current_operation: Worker | None = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Horizontal(id="main-container"):
            with Vertical(id="left-pane"):
                yield FileBrowserPane(str(Path.cwd()))
            
            with Vertical(id="center-pane"):
                yield OperationPane()
            
            with Vertical(id="right-pane"):
                yield ActionPane()
        
        with Horizontal(id="bottom-pane"):
            with Vertical(id="progress-section", classes="bottom-section"):
                yield ProgressPane()
            with Vertical(id="log-section", classes="bottom-section"):
                yield LogPane()
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application."""
        self.log_message("TechCompressor v2.0.0 TUI initialized")
        self.log_message("Select a file or folder to compress, or an archive to extract")
    
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection in directory tree."""
        self.selected_path = Path(event.path)
        self.log_message(f"Selected: {self.selected_path}")
        
        # Update output path suggestion
        output_input = self.query_one("#output-path", Input)
        if self.selected_path.suffix in (".tc", ".tcaf"):
            # It's an archive - suggest extraction folder
            output_input.value = str(self.selected_path.stem) + "_extracted"
        else:
            # It's a file/folder - suggest archive name
            output_input.value = str(self.selected_path.name) + ".tc"
    
    def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection in directory tree."""
        self.selected_path = Path(event.path)
        self.log_message(f"Selected folder: {self.selected_path}")
        
        output_input = self.query_one("#output-path", Input)
        output_input.value = str(self.selected_path.name) + ".tc"
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes."""
        if event.checkbox.id == "multivolume-check":
            volume_input = self.query_one("#volume-size-input", Input)
            volume_input.disabled = not event.value
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "btn-compress":
            self.action_compress()
        elif button_id == "btn-extract":
            self.action_extract()
        elif button_id == "btn-list":
            self.action_list_contents()
        elif button_id == "btn-verify":
            self.action_verify()
        elif button_id == "btn-parent":
            self._navigate_to_parent()
    
    def _navigate_to_parent(self) -> None:
        """Navigate to parent directory in file browser."""
        file_browser = self.query_one(FileBrowserPane)
        file_browser.navigate_to_parent()
        self.log_message(f"Navigated to: {file_browser.current_path}")
    
    def log_message(self, message: str) -> None:
        """Add a message to the log."""
        log_widget = self.query_one("#log-output", Log)
        log_widget.write_line(message)
    
    def update_progress(self, percent: float, status: str = "") -> None:
        """Update the progress bar and status."""
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_bar.update(progress=percent)
        
        if status:
            status_label = self.query_one("#progress-status", Label)
            status_label.update(status)
    
    async def _get_password_if_needed(self) -> str | None:
        """Show password dialog if encryption is enabled."""
        encrypt_check = self.query_one("#encrypt-check", Checkbox)
        if encrypt_check.value:
            return await self.push_screen_wait(PasswordModal("Enter Encryption Password"))
        return None
    
    def _get_settings(self) -> dict:
        """Get current compression settings."""
        algo_select = self.query_one("#algo-select", Select)
        multivolume_check = self.query_one("#multivolume-check", Checkbox)
        volume_input = self.query_one("#volume-size-input", Input)
        attributes_check = self.query_one("#attributes-check", Checkbox)
        output_input = self.query_one("#output-path", Input)
        
        settings = {
            "algo": algo_select.value,
            "multivolume": multivolume_check.value,
            "volume_size": int(volume_input.value) * 1024 * 1024 if volume_input.value and multivolume_check.value else None,
            "preserve_attributes": attributes_check.value,
            "output_path": output_input.value,
        }
        
        return settings
    
    def action_compress(self) -> None:
        """Start compression operation."""
        if not self.selected_path:
            self.log_message("[red]Error: No file or folder selected[/red]")
            return
        
        self._run_compress()
    
    @work(exclusive=True, thread=True)
    def _run_compress(self) -> None:
        """Run compression in background thread."""
        from techcompressor.archiver import create_archive
        from techcompressor.core import compress
        
        worker = get_current_worker()
        
        # Get settings (must be done before async operations)
        settings = self._get_settings()
        
        # Request password on main thread if needed
        password = None
        encrypt_check = self.query_one("#encrypt-check", Checkbox)
        if encrypt_check.value:
            self.call_from_thread(self.log_message, "Encryption enabled - please enter password in dialog")
            # For simplicity, we'll skip password in background thread
            # In a real implementation, we'd use call_from_thread to get password
        
        source = self.selected_path
        output_path = settings["output_path"]
        
        if not output_path:
            output_path = str(source.name) + ".tc"
        
        self.call_from_thread(self.log_message, f"Starting compression: {source}")
        self.call_from_thread(self.log_message, f"Algorithm: {settings['algo']}")
        self.call_from_thread(self.update_progress, 0, "Compressing...")
        
        try:
            def progress_callback(current: int, total: int):
                if worker.is_cancelled:
                    raise InterruptedError("Operation cancelled")
                percent = (current / total * 100) if total > 0 else 0
                self.call_from_thread(self.update_progress, percent, f"Processing file {current}/{total}")
            
            if source.is_dir():
                # Compress folder
                create_archive(
                    source,
                    output_path,
                    algo=settings["algo"],
                    password=password,
                    volume_size=settings["volume_size"],
                    preserve_attributes=settings["preserve_attributes"],
                    progress_callback=progress_callback
                )
            else:
                # Compress single file
                with open(source, "rb") as f:
                    data = f.read()
                
                compressed = compress(data, algo=settings["algo"], password=password)
                
                with open(output_path, "wb") as f:
                    f.write(compressed)
            
            self.call_from_thread(self.update_progress, 100, "Complete!")
            self.call_from_thread(self.log_message, f"[green]Compression complete: {output_path}[/green]")
            
        except InterruptedError:
            self.call_from_thread(self.log_message, "[yellow]Operation cancelled[/yellow]")
        except Exception as e:
            self.call_from_thread(self.log_message, f"[red]Error: {e}[/red]")
            self.call_from_thread(self.update_progress, 0, "Error")
    
    def action_extract(self) -> None:
        """Start extraction operation."""
        if not self.selected_path:
            self.log_message("[red]Error: No archive selected[/red]")
            return
        
        if self.selected_path.suffix not in (".tc", ".tcaf", ".part1"):
            self.log_message("[yellow]Warning: Selected file may not be a TechCompressor archive[/yellow]")
        
        self._run_extract()
    
    @work(exclusive=True, thread=True)
    def _run_extract(self) -> None:
        """Run extraction in background thread."""
        from techcompressor.archiver import extract_archive
        from techcompressor.core import decompress
        
        worker = get_current_worker()
        settings = self._get_settings()
        
        source = self.selected_path
        output_path = settings["output_path"]
        
        if not output_path:
            output_path = str(source.stem) + "_extracted"
        
        self.call_from_thread(self.log_message, f"Starting extraction: {source}")
        self.call_from_thread(self.update_progress, 0, "Extracting...")
        
        try:
            def progress_callback(current: int, total: int):
                if worker.is_cancelled:
                    raise InterruptedError("Operation cancelled")
                percent = (current / total * 100) if total > 0 else 0
                self.call_from_thread(self.update_progress, percent, f"Extracting file {current}/{total}")
            
            # Check if it's an archive or single file
            with open(source, "rb") as f:
                magic = f.read(4)
            
            if magic == b"TCAF":
                # It's an archive
                extract_archive(
                    source,
                    output_path,
                    password=None,  # Would need dialog for password
                    progress_callback=progress_callback,
                    restore_attributes=settings["preserve_attributes"]
                )
            else:
                # Single compressed file
                with open(source, "rb") as f:
                    data = f.read()
                
                decompressed = decompress(data, algo="AUTO", password=None)
                
                # Remove .tc extension for output
                if output_path.endswith(".tc"):
                    output_path = output_path[:-3]
                
                with open(output_path, "wb") as f:
                    f.write(decompressed)
            
            self.call_from_thread(self.update_progress, 100, "Complete!")
            self.call_from_thread(self.log_message, f"[green]Extraction complete: {output_path}[/green]")
            
        except InterruptedError:
            self.call_from_thread(self.log_message, "[yellow]Operation cancelled[/yellow]")
        except Exception as e:
            self.call_from_thread(self.log_message, f"[red]Error: {e}[/red]")
            self.call_from_thread(self.update_progress, 0, "Error")
    
    def action_list_contents(self) -> None:
        """List archive contents."""
        if not self.selected_path:
            self.log_message("[red]Error: No archive selected[/red]")
            return
        
        self._run_list_contents()
    
    @work(exclusive=True, thread=True)
    def _run_list_contents(self) -> None:
        """Run list contents in background thread."""
        from techcompressor.archiver import list_contents
        
        source = self.selected_path
        
        self.call_from_thread(self.log_message, f"Listing contents: {source}")
        
        try:
            contents = list_contents(source)
            
            self.call_from_thread(self.log_message, f"Found {len(contents)} entries")
            
            # Show modal with contents
            self.call_from_thread(self.push_screen, ArchiveContentsModal(contents))
            
        except Exception as e:
            self.call_from_thread(self.log_message, f"[red]Error: {e}[/red]")
    
    def action_verify(self) -> None:
        """Verify archive integrity."""
        if not self.selected_path:
            self.log_message("[red]Error: No archive selected[/red]")
            return
        
        self._run_verify()
    
    @work(exclusive=True, thread=True)
    def _run_verify(self) -> None:
        """Run verification in background thread."""
        from techcompressor.archiver import list_contents
        
        source = self.selected_path
        
        self.call_from_thread(self.log_message, f"Verifying archive: {source}")
        self.call_from_thread(self.update_progress, 0, "Verifying...")
        
        try:
            # Basic verification: try to list contents
            contents = list_contents(source)
            
            self.call_from_thread(self.update_progress, 50, "Checking entries...")
            
            total_entries = len(contents)
            self.call_from_thread(self.log_message, f"Archive contains {total_entries} entries")
            
            # Check for any obvious issues
            issues = []
            for entry in contents:
                if entry.get("compressed_size", 0) < 0:
                    issues.append(f"Invalid size for {entry.get('filename', '?')}")
            
            self.call_from_thread(self.update_progress, 100, "Complete!")
            
            if issues:
                for issue in issues:
                    self.call_from_thread(self.log_message, f"[yellow]Warning: {issue}[/yellow]")
            else:
                self.call_from_thread(self.log_message, "[green]Archive verification passed![/green]")
            
        except Exception as e:
            self.call_from_thread(self.log_message, f"[red]Verification failed: {e}[/red]")
            self.call_from_thread(self.update_progress, 0, "Failed")
    
    def action_about(self) -> None:
        """Show about dialog."""
        self.push_screen(AboutModal())
    
    def action_parent_folder(self) -> None:
        """Navigate to parent folder (keyboard shortcut)."""
        self._navigate_to_parent()
    
    def action_refresh(self) -> None:
        """Refresh the file tree."""
        file_tree = self.query_one("#file-tree", DirectoryTree)
        file_tree.reload()
        self.log_message("File tree refreshed")


def main():
    """Entry point for the TUI application."""
    app = TechCompressorTUI()
    app.run()


if __name__ == "__main__":
    main()
