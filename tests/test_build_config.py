"""
Test build configuration for antivirus false positive mitigation

Validates that PyInstaller spec file and related configuration files
are properly set up to minimize antivirus false positives.
"""

import pytest
from pathlib import Path


def test_spec_file_exists():
    """Verify techcompressor.spec exists."""
    spec_path = Path("techcompressor.spec")
    assert spec_path.exists(), "techcompressor.spec not found"


def test_spec_file_upx_disabled():
    """Verify UPX compression is disabled (primary AV trigger)."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    # Should appear at least twice (in EXE and COLLECT sections)
    assert content.count("upx=False") >= 2, "UPX should be disabled in spec file"


def test_spec_file_onedir_mode():
    """Verify onedir mode is used (more transparent than onefile)."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    assert "exclude_binaries=True" in content, "Should use onedir mode"


def test_spec_file_no_stripping():
    """Verify code stripping is disabled (reduces obfuscation)."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    assert "strip=False" in content, "Code stripping should be disabled"


def test_spec_file_gui_mode():
    """Verify console is disabled for GUI application."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    assert "console=False" in content, "Should be GUI application"


def test_spec_file_has_version_info():
    """Verify Windows version metadata is included."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    assert "version='file_version_info.txt'" in content, \
        "Should include version metadata"


def test_spec_file_has_crypto_imports():
    """Verify cryptography library is properly imported."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    assert "cryptography" in content, \
        "Should explicitly import cryptography modules"


def test_spec_file_has_tkinter_imports():
    """Verify Tkinter modules are properly imported."""
    with open("techcompressor.spec") as f:
        content = f.read()
    
    assert "tkinter" in content, "Should explicitly import tkinter modules"


def test_version_info_file_exists():
    """Verify Windows version info file exists."""
    version_path = Path("file_version_info.txt")
    assert version_path.exists(), "file_version_info.txt not found"


def test_version_info_has_required_fields():
    """Verify version info file has all required fields."""
    with open("file_version_info.txt") as f:
        content = f.read()
    
    required_fields = [
        "VSVersionInfo",
        "FileVersion",
        "ProductName",
        "LegalCopyright",
        "FileDescription",
        "CompanyName",
    ]
    
    for field in required_fields:
        assert field in content, f"Version info should contain {field}"


def test_version_info_has_product_details():
    """Verify version info contains proper product information."""
    with open("file_version_info.txt") as f:
        content = f.read()
    
    assert "TechCompressor" in content, "Should mention TechCompressor"
    assert "Devaansh Pathak" in content, "Should credit author"
    assert "MIT" in content, "Should mention MIT license"


def test_false_positive_docs_exist():
    """Verify antivirus false positive documentation exists."""
    doc_path = Path("docs/antivirus_false_positives.md")
    assert doc_path.exists(), "AV false positive docs not found"


def test_false_positive_docs_comprehensive():
    """Verify documentation covers key topics."""
    with open("docs/antivirus_false_positives.md") as f:
        content = f.read()
    
    key_topics = [
        "UPX",  # Explains UPX compression issue
        "PyInstaller",  # Mentions PyInstaller
        "cryptography",  # Explains crypto library flagging
        "VirusTotal",  # Mentions VirusTotal for scanning
        "false positive",  # Clear that these are false positives
    ]
    
    for topic in key_topics:
        assert topic.lower() in content.lower(), \
            f"Documentation should cover {topic}"


def test_readme_mentions_av_warning():
    """Verify README warns users about potential AV flags."""
    with open("README.md") as f:
        content = f.read()
    
    # Should mention antivirus or false positives
    content_lower = content.lower()
    assert "antivirus" in content_lower or "false positive" in content_lower, \
        "README should warn about antivirus issues"


def test_readme_links_to_av_docs():
    """Verify README links to AV false positive documentation."""
    with open("README.md") as f:
        content = f.read()
    
    assert "antivirus_false_positives.md" in content, \
        "README should link to AV documentation"


def test_build_script_uses_spec_file():
    """Verify build script uses the spec file."""
    with open("build_release.ps1") as f:
        content = f.read()
    
    assert "techcompressor.spec" in content, \
        "Build script should reference spec file"


def test_build_script_handles_onedir():
    """Verify build script handles onedir output structure."""
    with open("build_release.ps1") as f:
        content = f.read()
    
    # Should reference the TechCompressor directory, not just .exe
    assert "TechCompressor" in content, \
        "Build script should handle TechCompressor folder"


def test_gitignore_tracks_spec_file():
    """Verify .gitignore is configured to track our spec file."""
    # The spec file should not be ignored
    spec_path = Path("techcompressor.spec")
    assert spec_path.exists(), "Spec file should exist"
    
    # Read gitignore to verify pattern
    with open(".gitignore") as f:
        content = f.read()
    
    # Should have a comment about tracking our spec file
    assert "techcompressor.spec" in content.lower() or \
           "explicitly track" in content.lower(), \
           ".gitignore should document spec file tracking"
