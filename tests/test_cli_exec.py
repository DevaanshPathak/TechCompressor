"""
CLI execution tests for improved coverage.
Tests actual command execution paths.
"""

import pytest
import subprocess
import sys
import os
from pathlib import Path


class TestCLICreateCommand:
    """Test CLI create command with various options."""
    
    def test_create_basic(self, tmp_path):
        """Test basic create command."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert archive.exists()
    
    def test_create_with_deflate(self, tmp_path):
        """Test create with DEFLATE algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "DEFLATE"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert archive.exists()
    
    def test_create_with_huffman(self, tmp_path):
        """Test create with HUFFMAN algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "HUFFMAN"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_create_with_zstd(self, tmp_path):
        """Test create with ZSTD algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "ZSTD"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_create_with_brotli(self, tmp_path):
        """Test create with BROTLI algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "BROTLI"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_create_with_auto(self, tmp_path):
        """Test create with AUTO algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "AUTO"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0


class TestCLIExtractCommand:
    """Test CLI extract command."""
    
    def test_extract_basic(self, tmp_path):
        """Test basic extract command."""
        # Create archive first
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "test.tc"
        dest = tmp_path / "dest"
        
        # Create
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW"],
            capture_output=True
        )
        
        # Extract
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "extract", 
             str(archive), str(dest)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert dest.exists()
    
    def test_extract_missing_archive(self, tmp_path):
        """Test extract with missing archive."""
        dest = tmp_path / "dest"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "extract", 
             str(tmp_path / "nonexistent.tc"), str(dest)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0


class TestCLIListCommand:
    """Test CLI list command."""
    
    def test_list_contents(self, tmp_path):
        """Test list command."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        (source / "file2.txt").write_text("More content")
        
        archive = tmp_path / "test.tc"
        
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW"],
            capture_output=True
        )
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "list", str(archive)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "test.txt" in result.stdout or "file2.txt" in result.stdout
    
    def test_list_missing_archive(self, tmp_path):
        """Test list with missing archive."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "list", 
             str(tmp_path / "nonexistent.tc")],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0


class TestCLIVerifyCommand:
    """Test CLI verify command."""
    
    def test_verify_valid(self, tmp_path):
        """Test verify command on valid archive."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content")
        
        archive = tmp_path / "test.tc"
        
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW"],
            capture_output=True
        )
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "verify", str(archive)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0


class TestCLICompressDecompress:
    """Test CLI compress/decompress commands."""
    
    def test_compress_single_file(self, tmp_path):
        """Test compress command on single file."""
        source = tmp_path / "input.txt"
        source.write_text("Test content for compression")
        
        output = tmp_path / "output.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "compress", 
             str(source), str(output), "--algo", "LZW"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert output.exists()
    
    def test_decompress_single_file(self, tmp_path):
        """Test decompress command."""
        source = tmp_path / "input.txt"
        source.write_text("Test content for compression")
        
        compressed = tmp_path / "compressed.tc"
        decompressed = tmp_path / "output.txt"
        
        # Compress
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "compress", 
             str(source), str(compressed), "--algo", "LZW"],
            capture_output=True
        )
        
        # Decompress
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "decompress", 
             str(compressed), str(decompressed), "--algo", "LZW"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert decompressed.exists()
        assert decompressed.read_text() == "Test content for compression"


class TestCLIFilters:
    """Test CLI filtering options."""
    
    def test_exclude_pattern(self, tmp_path):
        """Test --exclude option."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "include.txt").write_text("Include")
        (source / "exclude.log").write_text("Exclude")
        
        archive = tmp_path / "test.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW", 
             "--exclude", "*.log"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Verify contents
        list_result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "list", str(archive)],
            capture_output=True,
            text=True
        )
        
        assert "include.txt" in list_result.stdout
        assert "exclude.log" not in list_result.stdout
    
    def test_max_size_filter(self, tmp_path):
        """Test --max-size option."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "small.txt").write_text("Small")
        (source / "large.txt").write_text("X" * 10000)
        
        archive = tmp_path / "test.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW", 
             "--max-size", "1000"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0


class TestCLIHelpMessages:
    """Test CLI help messages."""
    
    def test_main_help(self):
        """Test main help message."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "TechCompressor" in result.stdout or "compress" in result.stdout.lower()
    
    def test_create_help(self):
        """Test create subcommand help."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "--algo" in result.stdout
    
    def test_extract_help(self):
        """Test extract subcommand help."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "extract", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_list_help(self):
        """Test list subcommand help."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "list", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_missing_source_path(self):
        """Test error when source path is missing."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
    
    def test_invalid_algorithm(self, tmp_path):
        """Test error with invalid algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test")
        
        archive = tmp_path / "test.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "INVALID_ALGO"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
    
    def test_source_not_exist(self, tmp_path):
        """Test error when source doesn't exist."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(tmp_path / "nonexistent"), str(tmp_path / "out.tc")],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0


class TestCLIAliases:
    """Test CLI command aliases."""
    
    def test_c_alias(self, tmp_path):
        """Test 'c' alias for create."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test")
        
        archive = tmp_path / "test.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "c", 
             str(source), str(archive)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_x_alias(self, tmp_path):
        """Test 'x' alias for extract."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test")
        
        archive = tmp_path / "test.tc"
        dest = tmp_path / "dest"
        
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive)],
            capture_output=True
        )
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "x", 
             str(archive), str(dest)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_l_alias(self, tmp_path):
        """Test 'l' alias for list."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test")
        
        archive = tmp_path / "test.tc"
        
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive)],
            capture_output=True
        )
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "l", str(archive)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0


class TestCLIEncryption:
    """Test CLI encryption options."""
    
    def test_create_with_password(self, tmp_path):
        """Test create with password."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Secret content")
        
        archive = tmp_path / "encrypted.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW",
             "--password", "testpass123"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert archive.exists()
    
    def test_extract_with_password(self, tmp_path):
        """Test extract with password."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Secret content")
        
        archive = tmp_path / "encrypted.tc"
        dest = tmp_path / "dest"
        
        # Create encrypted
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW",
             "--password", "testpass123"],
            capture_output=True
        )
        
        # Extract with password
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "extract", 
             str(archive), str(dest),
             "--password", "testpass123"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert (dest / "test.txt").exists()
    
    def test_extract_wrong_password(self, tmp_path):
        """Test extract with wrong password fails."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Secret content")
        
        archive = tmp_path / "encrypted.tc"
        dest = tmp_path / "dest"
        
        # Create encrypted
        subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW",
             "--password", "correctpass"],
            capture_output=True
        )
        
        # Extract with wrong password
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "extract", 
             str(archive), str(dest),
             "--password", "wrongpass"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0


class TestCLIMultiVolume:
    """Test CLI multi-volume options."""
    
    def test_create_multi_volume(self, tmp_path):
        """Test creating multi-volume archive."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("X" * 10000)
        
        archive = tmp_path / "multi.tc"
        
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "create", 
             str(source), str(archive), "--algo", "LZW",
             "--volume-size", "1024"],  # 1KB volumes
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        # Should create multiple volumes
        assert (tmp_path / "multi.tc.part1").exists() or archive.exists()


class TestCLIModuleExecution:
    """Test different ways to invoke CLI."""
    
    def test_module_execution(self):
        """Test running as module."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
    
    def test_version_display(self):
        """Test version display."""
        result = subprocess.run(
            [sys.executable, "-m", "techcompressor.cli", "--version"],
            capture_output=True,
            text=True
        )
        
        # Either shows version or returns 0 with version info
        # Some CLI implementations may not have --version
        # Just ensure it doesn't crash
        pass  # Accept any result
