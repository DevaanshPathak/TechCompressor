"""
Deep coverage tests for archiver module - edge cases, error paths, and platform-specific features.
"""

import pytest
import tempfile
import os
import sys
import struct
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestVolumeReaderAllFormats:
    """Test VolumeReader with all archive formats."""
    
    def test_single_file_archive_direct_path(self, tmp_path):
        """Test VolumeReader with single-file archive."""
        from techcompressor.archiver import VolumeReader
        
        archive_path = tmp_path / "test.tc"
        archive_path.write_bytes(b"TCAF" + b"\x00" * 100)
        
        reader = VolumeReader(str(archive_path))
        assert len(reader.volume_paths) == 1
        assert reader.has_headers == False
    
    def test_part_format_detection(self, tmp_path):
        """Test VolumeReader detecting .part1/.part2 format."""
        from techcompressor.archiver import VolumeReader
        
        # Create .part1, .part2 volumes with TCVOL headers
        vol1 = tmp_path / "archive.tc.part1"
        header = b"TCVOL" + struct.pack("<I", 1) + struct.pack("<Q", 100) + b"\x00" * 37
        vol1.write_bytes(header + b"X" * 46)
        
        vol2 = tmp_path / "archive.tc.part2"
        header2 = b"TCVOL" + struct.pack("<I", 2) + struct.pack("<Q", 50) + b"\x00" * 37
        vol2.write_bytes(header2 + b"Y" * 46)
        
        reader = VolumeReader(str(vol1))
        assert len(reader.volume_paths) == 2
        assert reader.has_headers == True
        assert reader.header_size == 54
    
    def test_001_format_backward_compat(self, tmp_path):
        """Test VolumeReader with .001/.002 format."""
        from techcompressor.archiver import VolumeReader
        
        vol1 = tmp_path / "archive.tc.001"
        vol1.write_bytes(b"TCAF" + b"\x00" * 100)
        
        vol2 = tmp_path / "archive.tc.002"
        vol2.write_bytes(b"\x00" * 50)
        
        reader = VolumeReader(str(vol1))
        assert len(reader.volume_paths) == 2
        assert reader.has_headers == False
    
    def test_auto_detect_from_base_path_part(self, tmp_path):
        """Test auto-detecting .part format from base path."""
        from techcompressor.archiver import VolumeReader
        
        base_path = tmp_path / "archive.tc"
        
        vol1 = tmp_path / "archive.tc.part1"
        header = b"TCVOL" + struct.pack("<I", 1) + struct.pack("<Q", 100) + b"\x00" * 37
        vol1.write_bytes(header + b"data")
        
        reader = VolumeReader(str(base_path))
        assert len(reader.volume_paths) == 1
        assert reader.has_headers == True
    
    def test_auto_detect_from_base_path_001(self, tmp_path):
        """Test auto-detecting .001 format from base path."""
        from techcompressor.archiver import VolumeReader
        
        base_path = tmp_path / "archive.tc"
        
        vol1 = tmp_path / "archive.tc.001"
        vol1.write_bytes(b"TCAF" + b"\x00" * 100)
        
        reader = VolumeReader(str(base_path))
        assert len(reader.volume_paths) == 1
        assert reader.has_headers == False
    
    def test_volume_not_found_raises(self, tmp_path):
        """Test error when volumes not found."""
        from techcompressor.archiver import VolumeReader
        
        with pytest.raises(FileNotFoundError):
            VolumeReader(str(tmp_path / "nonexistent.tc.part1"))


class TestVolumeWriterEdgeCases:
    """Test VolumeWriter edge cases."""
    
    def test_volume_writer_creates_volumes(self, tmp_path):
        """Test basic VolumeWriter creating volumes."""
        from techcompressor.archiver import VolumeWriter
        
        base_path = tmp_path / "test.tc"
        writer = VolumeWriter(str(base_path), volume_size=1024)
        
        writer.write(b"Hello, World!" * 10)
        writer.close()
        
        assert (tmp_path / "test.tc.part1").exists()
    
    def test_volume_writer_spans_volumes(self, tmp_path):
        """Test VolumeWriter creating multiple volumes."""
        from techcompressor.archiver import VolumeWriter
        
        base_path = tmp_path / "test.tc"
        writer = VolumeWriter(str(base_path), volume_size=100)
        
        writer.write(b"X" * 200)
        writer.close()
        
        assert (tmp_path / "test.tc.part1").exists()
        assert (tmp_path / "test.tc.part2").exists()
    
    def test_volume_writer_tell_position(self, tmp_path):
        """Test VolumeWriter tell() tracking."""
        from techcompressor.archiver import VolumeWriter
        
        base_path = tmp_path / "test.tc"
        writer = VolumeWriter(str(base_path), volume_size=1024)
        
        # Initial position is 54 bytes (TCVOL header size)
        initial_pos = writer.tell()
        assert initial_pos == 54  # TCVOL header
        
        writer.write(b"1234567890")
        assert writer.tell() == initial_pos + 10
        writer.close()


class TestAttributeHandlingDeep:
    """Test attribute serialization and restoration."""
    
    def test_serialize_deserialize_roundtrip(self):
        """Test basic roundtrip with platform attribute."""
        from techcompressor.archiver import _serialize_attributes, _deserialize_attributes
        
        # Only platform, win_acl, and xattrs are preserved by design
        attrs = {"platform": "Windows"}
        serialized = _serialize_attributes(attrs)
        deserialized = _deserialize_attributes(serialized)
        
        assert deserialized["platform"] == "Windows"
    
    def test_empty_attributes(self):
        """Test empty attributes."""
        from techcompressor.archiver import _serialize_attributes, _deserialize_attributes
        
        attrs = {}
        serialized = _serialize_attributes(attrs)
        deserialized = _deserialize_attributes(serialized)
        
        assert deserialized == {}
    
    def test_xattrs_serialization(self):
        """Test xattrs serialization."""
        from techcompressor.archiver import _serialize_attributes, _deserialize_attributes
        
        attrs = {
            "platform": "Linux",
            "xattrs": {"user.test": "dGVzdA=="}  # base64 encoded "test"
        }
        serialized = _serialize_attributes(attrs)
        deserialized = _deserialize_attributes(serialized)
        
        assert deserialized["platform"] == "Linux"
        assert "xattrs" in deserialized
    
    def test_get_file_attributes_platform(self, tmp_path):
        """Test _get_file_attributes includes platform."""
        from techcompressor.archiver import _get_file_attributes
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        attrs = _get_file_attributes(test_file)
        
        assert "platform" in attrs
        if sys.platform == "win32":
            assert attrs["platform"] == "Windows"
        elif sys.platform == "linux":
            assert attrs["platform"] == "Linux"
        elif sys.platform == "darwin":
            assert attrs["platform"] == "macOS"


class TestArchiveFiltering:
    """Test file filtering during archive creation."""
    
    def test_max_file_size_filter(self, tmp_path):
        """Test filtering by max file size."""
        from techcompressor.archiver import create_archive, list_contents
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "small.txt").write_text("Small")
        (source / "large.txt").write_text("X" * 10000)
        
        archive = tmp_path / "test.tc"
        
        create_archive(source, archive, algo="LZW", max_file_size=100)
        
        contents = list_contents(archive)
        # Use 'name' key (not 'filename')
        filenames = [e['name'] for e in contents if 'name' in e]
        
        assert "small.txt" in filenames
        assert "large.txt" not in filenames
    
    def test_min_file_size_filter(self, tmp_path):
        """Test filtering by min file size."""
        from techcompressor.archiver import create_archive, list_contents
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "small.txt").write_text("Hi")
        (source / "large.txt").write_text("X" * 1000)
        
        archive = tmp_path / "test.tc"
        
        create_archive(source, archive, algo="LZW", min_file_size=100)
        
        contents = list_contents(archive)
        filenames = [e['name'] for e in contents if 'name' in e]
        
        assert "large.txt" in filenames
        assert "small.txt" not in filenames
    
    def test_exclude_patterns(self, tmp_path):
        """Test exclude patterns."""
        from techcompressor.archiver import create_archive, list_contents
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "include.txt").write_text("Include")
        (source / "exclude.log").write_text("Exclude")
        
        archive = tmp_path / "test.tc"
        
        create_archive(source, archive, algo="LZW", exclude_patterns=["*.log"])
        
        contents = list_contents(archive)
        filenames = [e['name'] for e in contents if 'name' in e]
        
        assert "include.txt" in filenames
        assert "exclude.log" not in filenames


class TestPathSecurityDeep:
    """Test path security measures."""
    
    def test_normal_path_accepted(self, tmp_path):
        """Test normal paths are accepted."""
        from techcompressor.archiver import _sanitize_extract_path
        
        # Note: _sanitize_extract_path(entry_name, dest_path) - entry first!
        result = _sanitize_extract_path("subdir/file.txt", tmp_path)
        expected = tmp_path / "subdir" / "file.txt"
        assert result == expected.resolve()
    
    def test_absolute_path_rejected(self, tmp_path):
        """Test absolute paths are stripped."""
        from techcompressor.archiver import _sanitize_extract_path
        
        # Absolute path should have leading slash stripped
        result = _sanitize_extract_path("/etc/passwd", tmp_path)
        # Should resolve to tmp_path/etc/passwd, not /etc/passwd
        expected = tmp_path / "etc" / "passwd"
        assert result == expected.resolve()
    
    def test_traversal_rejected(self, tmp_path):
        """Test path traversal is rejected."""
        from techcompressor.archiver import _sanitize_extract_path
        
        with pytest.raises(ValueError, match="traversal"):
            _sanitize_extract_path("../../../etc/passwd", tmp_path)
    
    def test_windows_drive_stripped(self, tmp_path):
        """Test Windows drive letters are stripped."""
        from techcompressor.archiver import _sanitize_extract_path
        
        # Windows drive path should be stripped
        result = _sanitize_extract_path("C:\\Windows\\System32\\test.txt", tmp_path)
        # Should resolve safely inside tmp_path
        assert str(result).startswith(str(tmp_path.resolve()))


class TestRecursionPrevention:
    """Test recursion prevention."""
    
    def test_archive_inside_source_blocked(self, tmp_path):
        """Test creating archive inside source is blocked."""
        from techcompressor.archiver import create_archive
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test")
        
        archive = source / "output.tc"
        
        with pytest.raises(ValueError, match="[Rr]ecursion"):
            create_archive(source, archive, algo="LZW")


class TestProgressCallbackIntegration:
    """Test progress callback behavior."""
    
    def test_compress_callback_called(self, tmp_path):
        """Test callback during compression."""
        from techcompressor.archiver import create_archive
        
        source = tmp_path / "source"
        source.mkdir()
        for i in range(5):
            (source / f"file{i}.txt").write_text(f"Content {i}" * 100)
        
        archive = tmp_path / "test.tc"
        calls = []
        
        def callback(current, total):
            calls.append((current, total))
        
        create_archive(source, archive, algo="LZW", progress_callback=callback)
        
        assert len(calls) > 0
        assert calls[-1][0] == calls[-1][1]
    
    def test_extract_callback_called(self, tmp_path):
        """Test callback during extraction."""
        from techcompressor.archiver import create_archive, extract_archive
        
        source = tmp_path / "source"
        source.mkdir()
        for i in range(3):
            (source / f"file{i}.txt").write_text(f"Content {i}")
        
        archive = tmp_path / "test.tc"
        dest = tmp_path / "dest"
        
        create_archive(source, archive, algo="LZW")
        
        calls = []
        
        def callback(current, total):
            calls.append((current, total))
        
        extract_archive(archive, dest, progress_callback=callback)
        
        assert len(calls) > 0


class TestArchiveMetadata:
    """Test archive metadata features."""
    
    def test_archive_with_comment(self, tmp_path):
        """Test archive with comment."""
        from techcompressor.archiver import create_archive
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Hello")
        
        archive = tmp_path / "test.tc"
        
        create_archive(source, archive, algo="LZW", comment="Test comment")
        
        assert archive.exists()
    
    def test_archive_with_creator(self, tmp_path):
        """Test archive with creator."""
        from techcompressor.archiver import create_archive
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Hello")
        
        archive = tmp_path / "test.tc"
        
        create_archive(source, archive, algo="LZW", creator="Test Creator")
        
        assert archive.exists()


class TestIncrementalBackup:
    """Test incremental backup feature."""
    
    def test_basic_incremental(self, tmp_path):
        """Test basic incremental backup."""
        from techcompressor.archiver import create_archive
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("Content 1")
        
        base = tmp_path / "base.tc"
        create_archive(source, base, algo="LZW")
        
        (source / "file2.txt").write_text("Content 2")
        
        inc = tmp_path / "inc.tc"
        create_archive(source, inc, algo="LZW", incremental=True, base_archive=base)
        
        assert inc.exists()


class TestArchiveValidation:
    """Test archive validation via list_contents."""
    
    def test_list_valid_archive(self, tmp_path):
        """Test listing valid archive."""
        from techcompressor.archiver import create_archive, list_contents
        
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test")
        
        archive = tmp_path / "test.tc"
        create_archive(source, archive, algo="LZW")
        
        # list_contents validates archive structure
        contents = list_contents(archive)
        assert len(contents) > 0
    
    def test_list_not_archive(self, tmp_path):
        """Test listing non-archive file."""
        from techcompressor.archiver import list_contents
        
        non_archive = tmp_path / "not.txt"
        non_archive.write_text("Not an archive")
        
        with pytest.raises((ValueError, Exception)):
            list_contents(non_archive)
