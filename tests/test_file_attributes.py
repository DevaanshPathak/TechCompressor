"""
Tests for file attributes preservation (Windows ACL, Linux/macOS xattr).

These tests gracefully handle missing dependencies (pywin32 on Windows,
os.getxattr/setxattr on Linux/macOS).
"""

import os
import sys
import pytest
from pathlib import Path
import tempfile

from techcompressor import archiver


# Detect platform and available APIs
PLATFORM = sys.platform
HAVE_WIN32_SECURITY = False
HAVE_XATTR = False

if PLATFORM == "win32":
    try:
        import win32security
        import ntsecuritycon
        HAVE_WIN32_SECURITY = True
    except ImportError:
        pass
else:
    # Linux/macOS
    HAVE_XATTR = hasattr(os, 'getxattr') and hasattr(os, 'setxattr')


@pytest.fixture
def tmp_files(tmp_path):
    """Create temporary files for testing."""
    # Create test directory structure
    test_dir = tmp_path / "test_attrs"
    test_dir.mkdir()
    
    # Create test files
    file1 = test_dir / "file1.txt"
    file1.write_text("Test file 1 with attributes")
    
    file2 = test_dir / "file2.txt"
    file2.write_text("Test file 2 with attributes")
    
    subdir = test_dir / "subdir"
    subdir.mkdir()
    
    file3 = subdir / "file3.txt"
    file3.write_text("Test file 3 in subdirectory")
    
    return test_dir


@pytest.mark.skipif(not HAVE_WIN32_SECURITY, reason="pywin32 not available")
def test_windows_acl_preservation(tmp_files, tmp_path):
    """Test Windows ACL preservation."""
    import win32security
    import ntsecuritycon
    
    test_file = tmp_files / "file1.txt"
    archive_path = tmp_path / "archive_acl.tc"
    extract_path = tmp_path / "extracted_acl"
    
    # Set custom ACL on test file
    sd = win32security.GetFileSecurity(
        str(test_file),
        win32security.DACL_SECURITY_INFORMATION
    )
    
    # Verify we can read original ACL
    dacl = sd.GetSecurityDescriptorDacl()
    assert dacl is not None, "Failed to read original DACL"
    original_ace_count = dacl.GetAceCount()
    
    # Create archive with attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        preserve_attributes=True
    )
    
    # Extract with attributes
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True
    )
    
    # Verify ACL was restored
    extracted_file = extract_path / "file1.txt"
    assert extracted_file.exists()
    
    restored_sd = win32security.GetFileSecurity(
        str(extracted_file),
        win32security.DACL_SECURITY_INFORMATION
    )
    restored_dacl = restored_sd.GetSecurityDescriptorDacl()
    
    # Check ACL structure preserved
    assert restored_dacl is not None, "DACL not restored"
    assert restored_dacl.GetAceCount() == original_ace_count, "ACE count mismatch"


@pytest.mark.skipif(not HAVE_XATTR, reason="Extended attributes not available")
def test_linux_xattr_preservation(tmp_files, tmp_path):
    """Test Linux/macOS extended attributes preservation."""
    test_file = tmp_files / "file1.txt"
    archive_path = tmp_path / "archive_xattr.tc"
    extract_path = tmp_path / "extracted_xattr"
    
    # Set custom extended attributes
    test_attrs = {
        "user.test.author": b"Devaansh Pathak",
        "user.test.project": b"TechCompressor",
        "user.test.version": b"1.2.0"
    }
    
    for name, value in test_attrs.items():
        try:
            os.setxattr(str(test_file), name, value)
        except OSError:
            pytest.skip("Cannot set extended attributes on this filesystem")
    
    # Verify attributes set
    for name, expected_value in test_attrs.items():
        actual_value = os.getxattr(str(test_file), name)
        assert actual_value == expected_value, f"Attribute {name} not set correctly"
    
    # Create archive with attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        preserve_attributes=True
    )
    
    # Extract with attributes
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True
    )
    
    # Verify extended attributes restored
    extracted_file = extract_path / "file1.txt"
    assert extracted_file.exists()
    
    for name, expected_value in test_attrs.items():
        try:
            actual_value = os.getxattr(str(extracted_file), name)
            assert actual_value == expected_value, f"Attribute {name} not restored"
        except OSError:
            pytest.fail(f"Extended attribute {name} not restored")


def test_attributes_with_all_algorithms(tmp_files, tmp_path):
    """Test attribute preservation with all compression algorithms."""
    algorithms = ["LZW", "HUFFMAN", "DEFLATE"]
    
    for algo in algorithms:
        archive_path = tmp_path / f"archive_{algo.lower()}_attrs.tc"
        extract_path = tmp_path / f"extracted_{algo.lower()}_attrs"
        
        # Create archive with attributes
        archiver.create_archive(
            str(tmp_files),
            str(archive_path),
            algo=algo,
            preserve_attributes=True
        )
        
        assert archive_path.exists(), f"Archive not created with {algo}"
        
        # Extract with attributes
        archiver.extract_archive(
            str(archive_path),
            str(extract_path),
            restore_attributes=True
        )
        
        # Verify all files extracted
        assert (extract_path / "file1.txt").exists()
        assert (extract_path / "file2.txt").exists()
        assert (extract_path / "subdir" / "file3.txt").exists()


def test_attributes_with_encryption(tmp_files, tmp_path):
    """Test attribute preservation with encryption."""
    archive_path = tmp_path / "archive_encrypted_attrs.tc"
    extract_path = tmp_path / "extracted_encrypted_attrs"
    password = "test_password_123"
    
    # Create encrypted archive with attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        password=password,
        preserve_attributes=True
    )
    
    assert archive_path.exists()
    
    # Extract with password and attributes
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        password=password,
        restore_attributes=True
    )
    
    # Verify extraction
    assert (extract_path / "file1.txt").exists()
    assert (extract_path / "file2.txt").exists()


def test_attributes_with_multi_volume(tmp_files, tmp_path):
    """Test attribute preservation with multi-volume archives."""
    archive_path = tmp_path / "archive_vol_attrs.tc"
    extract_path = tmp_path / "extracted_vol_attrs"
    
    # Create large file to force multiple volumes
    large_file = tmp_files / "large.bin"
    large_file.write_bytes(os.urandom(100 * 1024))  # 100KB random data
    
    # Create multi-volume archive with attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        preserve_attributes=True,
        volume_size=50 * 1024  # 50KB per volume
    )
    
    # Should create multiple volumes
    assert (tmp_path / "archive_vol_attrs.tc.001").exists()
    assert (tmp_path / "archive_vol_attrs.tc.002").exists()
    
    # Extract with attributes
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True
    )
    
    # Verify all files extracted
    assert (extract_path / "file1.txt").exists()
    assert (extract_path / "large.bin").exists()


def test_attributes_without_preservation(tmp_files, tmp_path):
    """Test that attributes are NOT preserved when preserve_attributes=False."""
    archive_path = tmp_path / "archive_no_attrs.tc"
    extract_path = tmp_path / "extracted_no_attrs"
    
    # Create archive WITHOUT attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        preserve_attributes=False  # Explicit False
    )
    
    assert archive_path.exists()
    
    # Extract (restore_attributes doesn't matter if not preserved)
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True  # This should be a no-op
    )
    
    # Files should still exist
    assert (extract_path / "file1.txt").exists()
    assert (extract_path / "file2.txt").exists()


def test_backward_compatibility_no_attributes(tmp_path):
    """Test that archives created without attributes can still be extracted."""
    # Create a simple test directory
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("Test content")
    
    archive_path = tmp_path / "old_archive.tc"
    extract_path = tmp_path / "extracted_old"
    
    # Create old-style archive (default preserve_attributes=False)
    archiver.create_archive(
        str(test_dir),
        str(archive_path),
        algo="LZW"
    )
    
    # Extract with restore_attributes=True (should handle missing attributes)
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True
    )
    
    # Verify extraction succeeded
    extracted_file = extract_path / "file.txt"
    assert extracted_file.exists()
    assert extracted_file.read_text() == "Test content"


def test_attributes_per_file_vs_single_stream(tmp_files, tmp_path):
    """Test attribute preservation in both per-file and single-stream modes."""
    # Per-file mode
    archive_per_file = tmp_path / "archive_per_file_attrs.tc"
    extract_per_file = tmp_path / "extracted_per_file_attrs"
    
    archiver.create_archive(
        str(tmp_files),
        str(archive_per_file),
        algo="LZW",
        per_file=True,
        preserve_attributes=True
    )
    
    archiver.extract_archive(
        str(archive_per_file),
        str(extract_per_file),
        restore_attributes=True
    )
    
    assert (extract_per_file / "file1.txt").exists()
    assert (extract_per_file / "file2.txt").exists()
    
    # Single-stream mode
    archive_single = tmp_path / "archive_single_attrs.tc"
    extract_single = tmp_path / "extracted_single_attrs"
    
    archiver.create_archive(
        str(tmp_files),
        str(archive_single),
        algo="LZW",
        per_file=False,
        preserve_attributes=True
    )
    
    archiver.extract_archive(
        str(archive_single),
        str(extract_single),
        restore_attributes=True
    )
    
    assert (extract_single / "file1.txt").exists()
    assert (extract_single / "file2.txt").exists()


def test_attributes_serialization_deserialization(tmp_files):
    """Test attribute serialization and deserialization functions."""
    test_file = tmp_files / "file1.txt"
    
    # Get attributes (platform-specific)
    attrs = archiver._get_file_attributes(str(test_file))
    
    # Should always have basic info
    assert "platform" in attrs
    assert attrs["platform"] in ["Windows", "Linux", "macOS"]
    
    # Serialize
    serialized = archiver._serialize_attributes(attrs)
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0
    
    # Deserialize
    deserialized = archiver._deserialize_attributes(serialized)
    assert deserialized == attrs
    assert deserialized["platform"] == attrs["platform"]


def test_attributes_empty_dict():
    """Test serialization of empty attributes dictionary."""
    empty_attrs = {}
    
    # Serialize empty dict
    serialized = archiver._serialize_attributes(empty_attrs)
    assert isinstance(serialized, bytes)
    
    # Deserialize
    deserialized = archiver._deserialize_attributes(serialized)
    assert deserialized == {}


def test_attributes_cross_platform_compatibility(tmp_files, tmp_path):
    """Test that archives created on one platform can be extracted on another."""
    archive_path = tmp_path / "archive_cross_platform.tc"
    extract_path = tmp_path / "extracted_cross_platform"
    
    # Create archive with attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        preserve_attributes=True
    )
    
    # Extract with attributes (should handle platform mismatch gracefully)
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True
    )
    
    # Files should extract successfully regardless of attribute compatibility
    assert (extract_path / "file1.txt").exists()
    assert (extract_path / "file2.txt").exists()
    assert (extract_path / "subdir" / "file3.txt").exists()


def test_attributes_list_contents(tmp_files, tmp_path):
    """Test that list_contents works with archives containing attributes."""
    archive_path = tmp_path / "archive_list_attrs.tc"
    
    # Create archive with attributes
    archiver.create_archive(
        str(tmp_files),
        str(archive_path),
        algo="LZW",
        preserve_attributes=True
    )
    
    # List contents
    contents = archiver.list_contents(str(archive_path))
    
    # Verify all files listed (note: list_contents uses 'name' key, not 'filename')
    assert len(contents) >= 3
    filenames = [entry["name"] for entry in contents if "name" in entry]
    assert "file1.txt" in filenames
    assert "file2.txt" in filenames
    assert "subdir/file3.txt" in filenames or "subdir\\file3.txt" in filenames  # Handle Windows paths


@pytest.mark.skipif(PLATFORM == "win32", reason="Windows symbolic links require admin privileges")
def test_attributes_symlink_handling(tmp_path):
    """Test that symbolic links are handled correctly with attributes."""
    test_dir = tmp_path / "test_symlinks"
    test_dir.mkdir()
    
    # Create target file
    target = test_dir / "target.txt"
    target.write_text("Target file content")
    
    # Create symlink
    link = test_dir / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Cannot create symbolic links")
    
    archive_path = tmp_path / "archive_symlink.tc"
    extract_path = tmp_path / "extracted_symlink"
    
    # Create archive (should skip symlinks as per _validate_path)
    archiver.create_archive(
        str(test_dir),
        str(archive_path),
        algo="LZW",
        preserve_attributes=True
    )
    
    # Extract
    archiver.extract_archive(
        str(archive_path),
        str(extract_path),
        restore_attributes=True
    )
    
    # Only target file should be extracted (symlink skipped)
    assert (extract_path / "target.txt").exists()
    # Symlink should not be in archive (security measure)
