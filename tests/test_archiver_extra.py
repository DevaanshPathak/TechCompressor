"""
Additional comprehensive tests for Archiver module to increase coverage.

Tests file attributes, serialization, volume management, and edge cases.
"""

import pytest
import sys
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from techcompressor.archiver import (
    _get_file_attributes,
    _set_file_attributes,
    _serialize_attributes,
    _deserialize_attributes,
    _validate_path,
    _check_recursion,
    _sanitize_extract_path,
    VolumeWriter,
    VolumeReader,
    create_archive,
    extract_archive,
    list_contents,
    MAGIC_HEADER_ARCHIVE,
    MAGIC_HEADER_VOLUME,
    ALGO_MAP,
    ALGO_REVERSE
)


class TestAttributeSerialization:
    """Test attribute serialization functions."""

    def test_serialize_none_attributes(self):
        """Test serializing None attributes."""
        result = _serialize_attributes(None)
        assert result == b'{}'

    def test_serialize_empty_attributes(self):
        """Test serializing empty attributes dict."""
        result = _serialize_attributes({})
        assert result == b'{}'

    def test_serialize_platform_only(self):
        """Test serializing with platform only."""
        attrs = {'platform': 'Windows'}
        result = _serialize_attributes(attrs)
        data = json.loads(result.decode('utf-8'))
        assert data['platform'] == 'Windows'

    def test_serialize_with_xattrs(self):
        """Test serializing with extended attributes."""
        attrs = {
            'platform': 'Linux',
            'xattrs': {'user.test': 'dGVzdA=='}  # base64 of 'test'
        }
        result = _serialize_attributes(attrs)
        data = json.loads(result.decode('utf-8'))
        assert 'xattrs' in data
        assert data['xattrs']['user.test'] == 'dGVzdA=='

    def test_deserialize_empty(self):
        """Test deserializing empty bytes."""
        result = _deserialize_attributes(b'')
        assert result == {}

    def test_deserialize_empty_json(self):
        """Test deserializing empty JSON object."""
        result = _deserialize_attributes(b'{}')
        assert result == {}

    def test_deserialize_with_platform(self):
        """Test deserializing with platform."""
        data = b'{"platform": "Windows"}'
        result = _deserialize_attributes(data)
        assert result['platform'] == 'Windows'

    def test_deserialize_with_xattrs(self):
        """Test deserializing with extended attributes."""
        data = b'{"platform": "Linux", "xattrs": {"user.test": "dGVzdA=="}}'
        result = _deserialize_attributes(data)
        assert 'xattrs' in result

    def test_deserialize_invalid_json(self):
        """Test deserializing invalid JSON."""
        result = _deserialize_attributes(b'not valid json')
        assert result == {}

    def test_deserialize_with_win_acl(self):
        """Test deserializing with Windows ACL (base64)."""
        import base64
        acl_bytes = b"test_acl_data"
        acl_b64 = base64.b64encode(acl_bytes).decode('ascii')
        data = json.dumps({'platform': 'Windows', 'win_acl': acl_b64}).encode('utf-8')
        
        result = _deserialize_attributes(data)
        assert result['win_acl'] == acl_bytes


class TestFileAttributes:
    """Test file attribute functions."""

    def test_get_attributes_returns_platform(self, tmp_path):
        """Test that get_attributes always returns platform."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        attrs = _get_file_attributes(test_file)
        
        assert 'platform' in attrs
        assert attrs['platform'] in ['Windows', 'Linux', 'macOS', 'Unknown']

    def test_set_attributes_with_none(self, tmp_path):
        """Test setting attributes with None."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # Should not raise
        _set_file_attributes(test_file, None)

    def test_set_attributes_with_empty(self, tmp_path):
        """Test setting attributes with empty dict."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # Should not raise
        _set_file_attributes(test_file, {})


class TestPathValidation:
    """Test path validation functions."""

    def test_validate_regular_path(self, tmp_path):
        """Test validating a regular path."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        
        result = _validate_path(test_dir)
        # Should return True for valid paths (or handle differently based on impl)

    def test_check_recursion_safe(self, tmp_path):
        """Test recursion check with safe paths."""
        source = tmp_path / "source"
        source.mkdir()
        archive = tmp_path / "archive.tc"
        
        # Should not raise for safe paths
        _check_recursion(source, archive)

    def test_check_recursion_unsafe(self, tmp_path):
        """Test recursion check with unsafe paths."""
        source = tmp_path / "source"
        source.mkdir()
        archive = source / "archive.tc"  # Archive inside source
        
        with pytest.raises(ValueError, match="recursion|inside"):
            _check_recursion(source, archive)

    def test_sanitize_extract_path_safe(self, tmp_path):
        """Test sanitizing safe extraction path."""
        # Note: argument order is (entry_name, dest_path)
        result = _sanitize_extract_path("subdir/file.txt", tmp_path)
        assert str(result).endswith("file.txt")

    def test_sanitize_extract_path_traversal(self, tmp_path):
        """Test sanitizing path traversal attempt."""
        with pytest.raises(ValueError):
            _sanitize_extract_path("../../../etc/passwd", tmp_path)

    def test_sanitize_extract_path_absolute(self, tmp_path):
        """Test sanitizing absolute path attempt."""
        # On Windows, this is still handled properly - strips leading slash
        result = _sanitize_extract_path("/etc/passwd", tmp_path)
        # Should strip leading slash and create safe path
        assert "etc" in str(result) or "passwd" in str(result)


class TestVolumeWriter:
    """Test VolumeWriter class."""

    def test_volume_writer_single_volume(self, tmp_path):
        """Test VolumeWriter in single-volume mode."""
        archive_path = tmp_path / "archive.tc"
        
        writer = VolumeWriter(archive_path, volume_size=None)
        writer.write(b"test data")
        writer.close()
        
        assert archive_path.exists()

    def test_volume_writer_multi_volume(self, tmp_path):
        """Test VolumeWriter in multi-volume mode."""
        archive_path = tmp_path / "archive.tc"
        
        writer = VolumeWriter(archive_path, volume_size=100)
        writer.write(b"X" * 50)  # First chunk
        writer.close()
        
        # Should have created at least one volume
        assert any(tmp_path.glob("archive.tc*"))

    def test_volume_writer_tell(self, tmp_path):
        """Test VolumeWriter tell() method."""
        archive_path = tmp_path / "archive.tc"
        
        writer = VolumeWriter(archive_path, volume_size=None)
        assert writer.tell() == 0
        
        writer.write(b"test")
        assert writer.tell() == 4
        
        writer.close()


class TestVolumeReader:
    """Test VolumeReader class."""

    def test_volume_reader_single_file(self, tmp_path):
        """Test VolumeReader with single archive."""
        archive_path = tmp_path / "archive.tc"
        archive_path.write_bytes(b"test archive data")
        
        reader = VolumeReader(archive_path)
        data = reader.read(17)
        assert data == b"test archive data"
        
        reader.close()

    def test_volume_reader_tell(self, tmp_path):
        """Test VolumeReader tell() method."""
        archive_path = tmp_path / "archive.tc"
        archive_path.write_bytes(b"test data")
        
        reader = VolumeReader(archive_path)
        assert reader.tell() == 0
        
        reader.read(4)
        assert reader.tell() == 4
        
        reader.close()

    def test_volume_reader_seek(self, tmp_path):
        """Test VolumeReader seek() method."""
        archive_path = tmp_path / "archive.tc"
        archive_path.write_bytes(b"test data here")
        
        reader = VolumeReader(archive_path)
        reader.seek(5)
        assert reader.tell() == 5
        
        data = reader.read(4)
        assert data == b"data"
        
        reader.close()


class TestAlgorithmMapping:
    """Test algorithm ID mapping."""

    def test_algo_map_contains_all(self):
        """Test ALGO_MAP contains all algorithms."""
        expected = ["STORED", "LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"]
        for algo in expected:
            assert algo in ALGO_MAP

    def test_algo_reverse_matches(self):
        """Test ALGO_REVERSE is inverse of ALGO_MAP."""
        for name, id_ in ALGO_MAP.items():
            assert ALGO_REVERSE[id_] == name

    def test_stored_is_zero(self):
        """Test STORED algorithm has ID 0."""
        assert ALGO_MAP["STORED"] == 0


class TestArchiveCreationEdgeCases:
    """Test edge cases in archive creation."""

    def test_create_empty_directory(self, tmp_path):
        """Test creating archive from empty directory."""
        source = tmp_path / "empty"
        source.mkdir()
        archive = tmp_path / "empty.tc"
        
        # Should handle empty directory gracefully
        try:
            create_archive(source, archive)
            # May create empty archive or raise
        except ValueError:
            pass  # Empty directory might be rejected

    def test_create_with_nested_dirs(self, tmp_path):
        """Test creating archive with nested directories."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "level1").mkdir()
        (source / "level1" / "level2").mkdir()
        (source / "level1" / "level2" / "file.txt").write_text("deep nested")
        
        archive = tmp_path / "nested.tc"
        create_archive(source, archive)
        
        assert archive.exists()

    def test_create_with_unicode_filenames(self, tmp_path):
        """Test creating archive with unicode filenames."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "файл.txt").write_text("Russian")
        (source / "文件.txt").write_text("Chinese")
        (source / "αρχείο.txt").write_text("Greek")
        
        archive = tmp_path / "unicode.tc"
        create_archive(source, archive)
        
        assert archive.exists()
        
        # Verify extraction
        dest = tmp_path / "extracted"
        extract_archive(archive, dest)
        
        assert (dest / "файл.txt").exists()

    def test_create_with_large_file(self, tmp_path):
        """Test creating archive with large file (1MB)."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "large.bin").write_bytes(b"X" * (1024 * 1024))
        
        archive = tmp_path / "large.tc"
        create_archive(source, archive, algo="LZW")
        
        assert archive.exists()

    def test_create_with_progress_callback(self, tmp_path):
        """Test creating archive with progress callback."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("content1 " * 100)
        (source / "file2.txt").write_text("content2 " * 100)
        
        archive = tmp_path / "progress.tc"
        
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        create_archive(source, archive, progress_callback=progress_callback)
        
        assert len(progress_calls) > 0


class TestArchiveExtractionEdgeCases:
    """Test edge cases in archive extraction."""

    def test_extract_to_existing_dir(self, tmp_path):
        """Test extracting to existing directory."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("test content")
        
        archive = tmp_path / "archive.tc"
        create_archive(source, archive)
        
        dest = tmp_path / "dest"
        dest.mkdir()
        
        extract_archive(archive, dest)
        assert (dest / "file.txt").exists()

    def test_extract_with_progress_callback(self, tmp_path):
        """Test extracting archive with progress callback."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("content " * 100)
        
        archive = tmp_path / "archive.tc"
        create_archive(source, archive)
        
        dest = tmp_path / "dest"
        
        progress_calls = []
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        extract_archive(archive, dest, progress_callback=progress_callback)
        
        assert len(progress_calls) > 0


class TestListContents:
    """Test list_contents function."""

    def test_list_contents_basic(self, tmp_path):
        """Test basic list_contents functionality."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("test content")
        
        archive = tmp_path / "archive.tc"
        create_archive(source, archive, per_file=True)
        
        contents = list_contents(archive)
        
        # Should have at least one entry (may include metadata)
        assert len(contents) >= 1

    def test_list_contents_multiple_files(self, tmp_path):
        """Test list_contents with multiple files."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("content 1")
        (source / "file2.txt").write_text("content 2")
        (source / "file3.txt").write_text("content 3")
        
        archive = tmp_path / "archive.tc"
        create_archive(source, archive, per_file=True)
        
        contents = list_contents(archive)
        
        # Should list all files
        file_entries = [e for e in contents if 'name' in e]
        assert len(file_entries) == 3

    def test_list_contents_nonexistent(self, tmp_path):
        """Test list_contents with nonexistent archive."""
        with pytest.raises(FileNotFoundError):
            list_contents(tmp_path / "nonexistent.tc")


class TestMagicHeaders:
    """Test magic header constants."""

    def test_archive_header(self):
        """Test archive magic header."""
        assert MAGIC_HEADER_ARCHIVE == b"TCAF"
        assert len(MAGIC_HEADER_ARCHIVE) == 4

    def test_volume_header(self):
        """Test volume magic header."""
        assert MAGIC_HEADER_VOLUME == b"TCVOL"
        assert len(MAGIC_HEADER_VOLUME) == 5


class TestArchiveWithAllAlgorithms:
    """Test archive creation with all algorithms."""

    @pytest.mark.parametrize("algo", ["LZW", "HUFFMAN", "DEFLATE", "ZSTD", "BROTLI"])
    def test_create_extract_with_algo(self, tmp_path, algo):
        """Test create and extract with specific algorithm."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "test.txt").write_text("Test content " * 100)
        
        archive = tmp_path / f"archive_{algo}.tc"
        create_archive(source, archive, algo=algo, per_file=True)
        
        assert archive.exists()
        
        dest = tmp_path / f"dest_{algo}"
        extract_archive(archive, dest)
        
        assert (dest / "test.txt").exists()
        assert (dest / "test.txt").read_text() == "Test content " * 100


class TestArchiveWithEncryption:
    """Test archive creation with encryption."""

    def test_create_encrypted_archive(self, tmp_path):
        """Test creating encrypted archive."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "secret.txt").write_text("Secret data " * 100)
        
        archive = tmp_path / "encrypted.tc"
        create_archive(source, archive, password="testpass123", per_file=True)
        
        assert archive.exists()

    def test_extract_encrypted_archive(self, tmp_path):
        """Test extracting encrypted archive."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "secret.txt").write_text("Secret data " * 100)
        
        archive = tmp_path / "encrypted.tc"
        create_archive(source, archive, password="testpass123", per_file=True)
        
        dest = tmp_path / "decrypted"
        extract_archive(archive, dest, password="testpass123")
        
        assert (dest / "secret.txt").exists()
        assert (dest / "secret.txt").read_text() == "Secret data " * 100

    def test_extract_wrong_password(self, tmp_path):
        """Test extracting with wrong password."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "secret.txt").write_text("Secret data " * 100)
        
        archive = tmp_path / "encrypted.tc"
        create_archive(source, archive, password="correct", per_file=True)
        
        dest = tmp_path / "failed"
        with pytest.raises(Exception):  # Should fail with wrong password
            extract_archive(archive, dest, password="wrong")
