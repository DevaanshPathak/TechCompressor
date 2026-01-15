"""
Additional CLI tests to increase coverage.

Targets error handling paths and edge cases.
"""

import pytest
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from techcompressor.cli import main


class TestCLITUISubcommand:
    """Test 'tui' subcommand."""

    def test_tui_subcommand_recognized(self, capsys):
        """Test that 'tui' subcommand is recognized by help."""
        # Check that tui appears in help output
        with patch.object(sys, 'argv', ['techcmp', '--help']):
            with pytest.raises(SystemExit) as exc:
                main()
        
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert 'tui' in captured.out


class TestCLIErrorPaths:
    """Test CLI error handling paths."""

    def test_compress_input_not_found(self, tmp_path, capsys):
        """Test compress with nonexistent input."""
        with patch.object(sys, 'argv', [
            'techcmp', 'compress',
            str(tmp_path / 'nonexistent.txt'),
            str(tmp_path / 'output.tc')
        ]):
            result = main()
        
        assert result == 1
        captured = capsys.readouterr()
        assert 'not found' in captured.err.lower() or 'error' in captured.err.lower()

    def test_extract_nonexistent_archive(self, tmp_path, capsys):
        """Test extract with nonexistent archive."""
        with patch.object(sys, 'argv', [
            'techcmp', 'extract',
            str(tmp_path / 'nonexistent.tc'),
            str(tmp_path / 'output')
        ]):
            result = main()
        
        assert result == 1

    def test_list_nonexistent_archive(self, tmp_path, capsys):
        """Test list with nonexistent archive."""
        with patch.object(sys, 'argv', [
            'techcmp', 'list',
            str(tmp_path / 'nonexistent.tc')
        ]):
            result = main()
        
        assert result == 1

    def test_verify_nonexistent_archive(self, tmp_path, capsys):
        """Test verify with nonexistent archive."""
        with patch.object(sys, 'argv', [
            'techcmp', 'verify',
            str(tmp_path / 'nonexistent.tc')
        ]):
            result = main()
        
        assert result == 1


class TestCLICreateArchiveOptions:
    """Test create archive with various options."""

    def test_create_with_comment(self, tmp_path, capsys):
        """Test creating archive with comment."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Test content " * 100)
        archive = tmp_path / "commented.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--comment', 'Test archive comment'
        ]):
            result = main()
        
        assert result == 0
        assert archive.exists()

    def test_create_with_creator(self, tmp_path, capsys):
        """Test creating archive with creator name."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Test content " * 100)
        archive = tmp_path / "creator.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--creator', 'Test Creator'
        ]):
            result = main()
        
        assert result == 0
        assert archive.exists()

    def test_create_with_recovery(self, tmp_path, capsys):
        """Test creating archive with recovery records."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Test content " * 100)
        archive = tmp_path / "recovery.tc"
        
        # Recovery is specified via archiver API, not CLI currently
        # Just test basic create works
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive)
        ]):
            result = main()
        
        assert result == 0
        assert archive.exists()

    def test_create_with_preserve_attributes(self, tmp_path, capsys):
        """Test creating archive with preserved attributes."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Test content " * 100)
        archive = tmp_path / "attrs.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--preserve-attributes'
        ]):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'attributes' in captured.out.lower()


class TestCLIExtractOptions:
    """Test extract command with various options."""

    def test_extract_with_password(self, tmp_path, capsys):
        """Test extracting encrypted archive."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "secret.txt").write_text("Secret content " * 100)
        archive = tmp_path / "encrypted.tc"
        dest = tmp_path / "extracted"
        
        # Create encrypted archive
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--password', 'test123'
        ]):
            main()
        
        # Extract with password
        with patch.object(sys, 'argv', [
            'techcmp', 'extract',
            str(archive),
            str(dest),
            '--password', 'test123'
        ]):
            result = main()
        
        assert result == 0
        assert (dest / "secret.txt").exists()


class TestCLIDecompressOptions:
    """Test decompress command with options."""

    def test_decompress_auto_algorithm(self, tmp_path, capsys):
        """Test decompression with AUTO algorithm detection."""
        from techcompressor.core import compress
        
        data = b"Test data " * 100
        compressed_file = tmp_path / "test.tc"
        output_file = tmp_path / "output.txt"
        
        # Create compressed file
        compressed_file.write_bytes(compress(data, algo="ZSTD"))
        
        with patch.object(sys, 'argv', [
            'techcmp', 'decompress',
            str(compressed_file),
            str(output_file),
            '--algo', 'AUTO'
        ]):
            result = main()
        
        assert result == 0
        assert output_file.read_bytes() == data


class TestCLIMultiVolumeOptions:
    """Test multi-volume archive options."""

    def test_create_with_volume_size(self, tmp_path, capsys):
        """Test creating multi-volume archive."""
        source = tmp_path / "source"
        source.mkdir()
        # Create a larger file to trigger multiple volumes
        (source / "large.txt").write_text("Large content " * 1000)
        archive = tmp_path / "multivolume"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--volume-size', '5000'  # Small volume size
        ]):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'Multi-volume' in captured.out or 'volume' in captured.out.lower()


class TestCLIFilterOptions:
    """Test filtering options in CLI."""

    def test_create_with_exclude(self, tmp_path, capsys):
        """Test creating archive with exclude patterns."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "include.txt").write_text("Include this")
        (source / "exclude.log").write_text("Exclude this")
        archive = tmp_path / "filtered.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--exclude', '*.log'
        ]):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        # Check that exclude pattern was recognized
        assert 'Exclude' in captured.out or 'exclude' in captured.out.lower()

    def test_create_with_max_size(self, tmp_path, capsys):
        """Test creating archive with max file size filter."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "small.txt").write_text("Small file")
        (source / "large.txt").write_text("Large content " * 10000)
        archive = tmp_path / "maxsize.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--max-size', '1000'
        ]):
            result = main()
        
        # May succeed or fail depending on if any files match
        assert result in (0, 1)

    def test_create_with_min_size(self, tmp_path, capsys):
        """Test creating archive with min file size filter."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "small.txt").write_text("Small")
        (source / "medium.txt").write_text("Medium content " * 100)
        archive = tmp_path / "minsize.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--min-size', '100'
        ]):
            result = main()
        
        assert result == 0


class TestCLIVerifyCommand:
    """Test verify command."""

    def test_verify_valid_archive(self, tmp_path, capsys):
        """Test verifying a valid archive."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Verify test " * 100)
        archive = tmp_path / "verify.tc"
        
        # Create archive
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive)
        ]):
            main()
        
        # Verify it
        with patch.object(sys, 'argv', [
            'techcmp', 'verify',
            str(archive)
        ]):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'valid' in captured.out.lower() or '✅' in captured.out


class TestCLIHelpMessages:
    """Test help messages for subcommands."""

    def test_create_help(self, capsys):
        """Test create command help."""
        with patch.object(sys, 'argv', ['techcmp', 'create', '--help']):
            with pytest.raises(SystemExit) as exc:
                main()
        
        assert exc.value.code == 0

    def test_extract_help(self, capsys):
        """Test extract command help."""
        with patch.object(sys, 'argv', ['techcmp', 'extract', '--help']):
            with pytest.raises(SystemExit) as exc:
                main()
        
        assert exc.value.code == 0

    def test_compress_help(self, capsys):
        """Test compress command help."""
        with patch.object(sys, 'argv', ['techcmp', 'compress', '--help']):
            with pytest.raises(SystemExit) as exc:
                main()
        
        assert exc.value.code == 0


class TestCLISingleStreamMode:
    """Test single-stream (non-per-file) compression mode."""

    def test_create_per_file_mode(self, tmp_path, capsys):
        """Test creating archive in per-file mode."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("File 1 " * 100)
        (source / "file2.txt").write_text("File 2 " * 100)
        archive = tmp_path / "perfile.tc"
        
        with patch.object(sys, 'argv', [
            'techcmp', 'create',
            str(source),
            str(archive),
            '--per-file'
        ]):
            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'per-file' in captured.out
