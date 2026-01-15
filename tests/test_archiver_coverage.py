"""
Additional archiver tests targeting uncovered lines.

Focuses on:
- Attribute serialization edge cases
- Volume reader/writer edge cases  
- Path validation
- Archive metadata handling
"""

import pytest
import tempfile
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from techcompressor.archiver import (
    create_archive, extract_archive, list_contents,
    _serialize_attributes, _deserialize_attributes,
    _get_file_attributes, _set_file_attributes,
    _validate_path, _sanitize_extract_path, _check_recursion,
    VolumeWriter, VolumeReader,
    MAGIC_HEADER_ARCHIVE, MAGIC_HEADER_VOLUME,
    ALGO_MAP, ALGO_REVERSE
)


class TestAlgoMaps:
    """Test algorithm ID mappings."""

    def test_algo_map_contains_all_algorithms(self):
        """Test ALGO_MAP has all expected algorithms."""
        expected = ["LZW", "HUFFMAN", "DEFLATE", "STORED", "ZSTD", "BROTLI"]
        for algo in expected:
            assert algo in ALGO_MAP, f"{algo} not in ALGO_MAP"

    def test_reverse_algo_map_matches(self):
        """Test ALGO_REVERSE is inverse of ALGO_MAP."""
        for name, id_ in ALGO_MAP.items():
            if id_ in ALGO_REVERSE:
                assert ALGO_REVERSE[id_] == name

    def test_algo_ids_unique(self):
        """Test that algorithm IDs are unique."""
        ids = list(ALGO_MAP.values())
        assert len(ids) == len(set(ids)), "Duplicate algorithm IDs"


class TestAttributeSerializationAdvanced:
    """Advanced tests for attribute serialization."""

    def test_serialize_with_platform_only(self):
        """Test serialization with only platform attribute."""
        attrs = {"platform": "Windows"}
        result = _serialize_attributes(attrs)
        
        # Should be valid JSON
        parsed = json.loads(result.decode('utf-8'))
        assert parsed["platform"] == "Windows"

    def test_serialize_with_xattrs(self):
        """Test serialization with extended attributes."""
        attrs = {
            "platform": "Linux",
            "xattrs": {
                "user.test": "dGVzdA==",  # base64 encoded "test"
                "user.other": "b3RoZXI="  # base64 encoded "other"
            }
        }
        result = _serialize_attributes(attrs)
        
        parsed = json.loads(result.decode('utf-8'))
        assert "xattrs" in parsed
        assert parsed["xattrs"]["user.test"] == "dGVzdA=="

    def test_deserialize_empty_json(self):
        """Test deserialization of empty JSON object."""
        result = _deserialize_attributes(b'{}')
        assert result == {}

    def test_deserialize_invalid_json(self):
        """Test deserialization of invalid JSON returns empty dict."""
        result = _deserialize_attributes(b'not json')
        assert result == {}

    def test_deserialize_with_win_acl(self):
        """Test deserialization with Windows ACL data."""
        import base64
        acl_data = b"test_acl_binary_data"
        attrs = {"win_acl": base64.b64encode(acl_data).decode('ascii')}
        serialized = json.dumps(attrs).encode('utf-8')
        
        result = _deserialize_attributes(serialized)
        # ACL should be decoded from base64
        assert "win_acl" in result
        assert result["win_acl"] == acl_data

    def test_roundtrip_serialization(self):
        """Test serialize then deserialize returns equivalent data."""
        original = {
            "platform": "Windows",
            "xattrs": {"user.key": "dmFsdWU="}
        }
        
        serialized = _serialize_attributes(original)
        deserialized = _deserialize_attributes(serialized)
        
        assert deserialized["platform"] == original["platform"]
        assert deserialized["xattrs"] == original["xattrs"]


class TestGetFileAttributesPlatform:
    """Test _get_file_attributes on current platform."""

    def test_get_attributes_returns_platform(self, tmp_path):
        """Test that _get_file_attributes always returns platform."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        attrs = _get_file_attributes(test_file)
        
        # Should always have platform key
        assert "platform" in attrs
        assert attrs["platform"] in ["Windows", "Linux", "macOS", "Unknown"]

    def test_get_attributes_nonexistent_file(self, tmp_path):
        """Test _get_file_attributes on nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"
        
        # Should not crash, returns platform at minimum
        attrs = _get_file_attributes(nonexistent)
        assert "platform" in attrs


class TestSetFileAttributesEdgeCases:
    """Test _set_file_attributes edge cases."""

    def test_set_empty_attributes(self, tmp_path):
        """Test setting empty attributes does nothing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # Should not crash
        _set_file_attributes(test_file, {})
        _set_file_attributes(test_file, None)

    def test_set_attributes_cross_platform(self, tmp_path):
        """Test setting attributes from different platform."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # Try to set Linux xattrs on any platform
        attrs = {
            "platform": "Linux",
            "xattrs": {"user.test": "dGVzdA=="}
        }
        
        # Should not crash even if not applicable
        _set_file_attributes(test_file, attrs)


class TestPathValidationAdvanced:
    """Advanced path validation tests."""

    def test_validate_regular_file(self, tmp_path):
        """Test validation of regular file doesn't raise."""
        test_file = tmp_path / "regular.txt"
        test_file.write_text("content")
        
        # _validate_path expects Path object, returns None if valid
        # Should not raise for valid file
        _validate_path(test_file)

    def test_validate_directory(self, tmp_path):
        """Test validation of directory doesn't raise."""
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()
        
        # Should not raise for valid directory
        _validate_path(test_dir)

    def test_validate_nonexistent(self, tmp_path):
        """Test validation of nonexistent path doesn't raise."""
        # Implementation validates symlinks, not existence
        nonexistent = tmp_path / "nonexistent"
        # Should not raise for nonexistent (no symlink check needed)
        _validate_path(nonexistent)


class TestSanitizeExtractPathAdvanced:
    """Advanced tests for path sanitization."""

    def test_sanitize_normal_path(self, tmp_path):
        """Test sanitization of normal path."""
        result = _sanitize_extract_path("file.txt", tmp_path)
        assert result == tmp_path / "file.txt"

    def test_sanitize_nested_path(self, tmp_path):
        """Test sanitization of nested path."""
        result = _sanitize_extract_path("dir/subdir/file.txt", tmp_path)
        assert result == tmp_path / "dir" / "subdir" / "file.txt"

    def test_sanitize_blocks_traversal(self, tmp_path):
        """Test that path traversal is blocked."""
        with pytest.raises(ValueError):
            _sanitize_extract_path("../../../etc/passwd", tmp_path)

    def test_sanitize_strips_leading_slash(self, tmp_path):
        """Test that leading slashes are stripped."""
        # On Windows, /etc/passwd is not absolute, so it gets stripped
        result = _sanitize_extract_path("/etc/passwd", tmp_path)
        # The leading slash is stripped
        assert result == tmp_path / "etc" / "passwd"

    def test_sanitize_strips_drive_letter(self, tmp_path):
        """Test that drive letters are stripped."""
        result = _sanitize_extract_path("C:\\Windows\\System32\\file", tmp_path)
        # Drive letter is stripped
        assert "Windows" in str(result)
        assert result.is_relative_to(tmp_path)

    def test_sanitize_backslash_in_filename(self, tmp_path):
        """Test handling of backslashes in filename."""
        # Backslashes should be normalized
        result = _sanitize_extract_path("dir\\file.txt", tmp_path)
        assert tmp_path in result.parents or result.parent == tmp_path

    def test_sanitize_embedded_traversal(self, tmp_path):
        """Test embedded path traversal attempt."""
        with pytest.raises(ValueError):
            _sanitize_extract_path("dir/../../../etc/passwd", tmp_path)


class TestCheckRecursion:
    """Test recursion detection."""

    def test_no_recursion_different_paths(self, tmp_path):
        """Test no recursion when paths are different."""
        source = tmp_path / "source"
        source.mkdir()
        archive = tmp_path / "archive.tc"
        
        # Should not raise
        _check_recursion(source, archive)

    def test_recursion_detected_archive_in_source(self, tmp_path):
        """Test recursion detected when archive is inside source."""
        source = tmp_path / "source"
        source.mkdir()
        archive = source / "archive.tc"
        
        with pytest.raises(ValueError):
            _check_recursion(source, archive)

    def test_recursion_detected_nested(self, tmp_path):
        """Test recursion detected in nested directory."""
        source = tmp_path / "source"
        nested = source / "subdir"
        nested.mkdir(parents=True)
        archive = nested / "archive.tc"
        
        with pytest.raises(ValueError):
            _check_recursion(source, archive)


class TestVolumeWriterEdgeCases:
    """Edge case tests for VolumeWriter."""

    def test_volume_writer_write_exact_volume_size(self, tmp_path):
        """Test writing data exactly equal to volume size."""
        base_path = tmp_path / "exact"
        volume_size = 1000
        
        writer = VolumeWriter(base_path, volume_size)
        
        # Write exactly volume_size bytes (minus header if any)
        data = b"X" * 900  # Leave room for header
        writer.write(data)
        writer.close()
        
        # Should have created at least one volume
        assert (tmp_path / "exact.part1").exists()

    def test_volume_writer_multiple_small_writes(self, tmp_path):
        """Test multiple small writes to volume."""
        base_path = tmp_path / "small_writes"
        volume_size = 500
        
        writer = VolumeWriter(base_path, volume_size)
        
        # Multiple small writes
        for i in range(20):
            writer.write(b"Small chunk ")
        
        writer.close()
        
        # Verify at least one volume exists
        assert (tmp_path / "small_writes.part1").exists()

    def test_volume_writer_tell_position(self, tmp_path):
        """Test tell() returns correct position."""
        base_path = tmp_path / "tell_test"
        volume_size = 10000
        
        writer = VolumeWriter(base_path, volume_size)
        
        initial_pos = writer.tell()
        
        writer.write(b"X" * 100)
        after_write_pos = writer.tell()
        
        assert after_write_pos >= initial_pos + 100
        
        writer.close()


class TestVolumeReaderEdgeCases:
    """Edge case tests for VolumeReader."""

    def test_volume_reader_single_file(self, tmp_path):
        """Test VolumeReader with single-file archive."""
        # Create a simple archive
        archive_path = tmp_path / "single.tc"
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("Test content " * 100)
        
        create_archive(source_dir, archive_path, algo="LZW")
        
        reader = VolumeReader(archive_path)
        
        # Should detect single volume
        assert len(reader.volume_paths) == 1
        
        reader.close()

    def test_volume_reader_seek_and_read(self, tmp_path):
        """Test seek and read operations."""
        archive_path = tmp_path / "seektest.tc"
        
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("Seek test content " * 100)
        
        create_archive(source_dir, archive_path, algo="LZW")
        
        reader = VolumeReader(archive_path)
        
        # Read some data
        initial_data = reader.read(10)
        assert len(initial_data) == 10
        
        # Seek back
        reader.seek(0)
        
        # Read same data
        same_data = reader.read(10)
        assert same_data == initial_data
        
        reader.close()


class TestCreateArchiveEdgeCases:
    """Edge case tests for create_archive."""

    def test_create_archive_empty_directory_raises_error(self, tmp_path):
        """Test creating archive from empty directory raises error."""
        source = tmp_path / "empty"
        source.mkdir()
        archive = tmp_path / "empty.tc"
        
        # Empty directory should raise ValueError
        with pytest.raises(ValueError, match="No files found"):
            create_archive(source, archive, algo="LZW")

    def test_create_archive_with_comment(self, tmp_path):
        """Test creating archive with comment."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Comment test " * 50)
        archive = tmp_path / "commented.tc"
        
        create_archive(
            source, archive, 
            algo="LZW",
            comment="This is a test archive",
            creator="Test Suite"
        )
        
        assert archive.exists()

    def test_create_archive_with_recovery(self, tmp_path):
        """Test creating archive with recovery records."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Recovery test " * 100)
        archive = tmp_path / "recovery.tc"
        
        create_archive(
            source, archive,
            algo="LZW",
            recovery_percent=5.0
        )
        
        assert archive.exists()
        # Archive should be larger due to recovery records

    def test_create_archive_per_file_vs_single_stream(self, tmp_path):
        """Test per-file vs single-stream compression."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("File 1 " * 100)
        (source / "file2.txt").write_text("File 2 " * 100)
        
        archive_per_file = tmp_path / "per_file.tc"
        archive_single = tmp_path / "single.tc"
        
        create_archive(source, archive_per_file, per_file=True)
        create_archive(source, archive_single, per_file=False)
        
        assert archive_per_file.exists()
        assert archive_single.exists()
        
        # Both should extract correctly
        dest1 = tmp_path / "extracted1"
        dest2 = tmp_path / "extracted2"
        
        extract_archive(archive_per_file, dest1)
        extract_archive(archive_single, dest2)
        
        assert (dest1 / "file1.txt").exists()
        assert (dest2 / "file1.txt").exists()


class TestExtractArchiveEdgeCases:
    """Edge case tests for extract_archive."""

    def test_extract_with_progress_callback(self, tmp_path):
        """Test extraction with progress callback."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Progress test " * 100)
        archive = tmp_path / "progress.tc"
        
        create_archive(source, archive, per_file=True)
        
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        dest = tmp_path / "extracted"
        extract_archive(archive, dest, progress_callback=progress_callback)
        
        # Should have called progress at least once
        assert len(progress_calls) > 0

    def test_extract_creates_directories(self, tmp_path):
        """Test that extraction creates necessary directories."""
        source = tmp_path / "source" / "subdir"
        source.mkdir(parents=True)
        (source / "nested.txt").write_text("Nested file " * 50)
        
        archive = tmp_path / "nested.tc"
        create_archive(source.parent, archive)
        
        dest = tmp_path / "extracted"
        extract_archive(archive, dest)
        
        # Nested structure should be recreated
        assert (dest / "subdir" / "nested.txt").exists()


class TestListContentsAdvanced:
    """Advanced tests for list_contents."""

    def test_list_contents_returns_metadata(self, tmp_path):
        """Test that list_contents returns file metadata."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("Content " * 100)
        archive = tmp_path / "list_test.tc"
        
        create_archive(source, archive, per_file=True)
        
        contents = list_contents(archive)
        
        # Find actual file entry (not metadata)
        file_entries = [c for c in contents if 'filename' in c or 'name' in c]
        assert len(file_entries) > 0
        
        # Should have size info
        entry = file_entries[0]
        if 'original_size' in entry:
            assert entry['original_size'] >= 0
        if 'compressed_size' in entry:
            assert entry['compressed_size'] >= 0

    def test_list_contents_multiple_files(self, tmp_path):
        """Test listing archive with multiple files."""
        source = tmp_path / "source"
        source.mkdir()
        
        # Create multiple files
        for i in range(5):
            (source / f"file{i}.txt").write_text(f"Content {i} " * 50)
        
        archive = tmp_path / "multi.tc"
        create_archive(source, archive, per_file=True)
        
        contents = list_contents(archive)
        
        # Should list all files
        filenames = [c.get('filename', c.get('name', '')) for c in contents]
        filenames = [f for f in filenames if f]  # Filter empty
        
        assert len(filenames) >= 5


class TestArchiveWithAllAlgorithms:
    """Test archive creation with all algorithms."""

    def test_archive_all_algorithms(self, tmp_path):
        """Test creating archives with each algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Algorithm test " * 100)
        
        for algo in ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]:
            archive = tmp_path / f"archive_{algo.lower()}.tc"
            dest = tmp_path / f"extracted_{algo.lower()}"
            
            create_archive(source, archive, algo=algo)
            assert archive.exists(), f"Archive creation failed for {algo}"
            
            extract_archive(archive, dest)
            assert (dest / "test.txt").exists(), f"Extraction failed for {algo}"
            
            extracted_content = (dest / "test.txt").read_text()
            assert extracted_content == "Algorithm test " * 100
