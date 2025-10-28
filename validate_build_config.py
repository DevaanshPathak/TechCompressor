#!/usr/bin/env python3
"""
Validation script for techcompressor.spec

Verifies the spec file is properly configured without requiring a full build.
"""

import sys
from pathlib import Path

def validate_spec_file():
    """Validate spec file configuration."""
    spec_path = Path("techcompressor.spec")
    
    if not spec_path.exists():
        print("❌ ERROR: techcompressor.spec not found!")
        return False
    
    print("✓ Found techcompressor.spec")
    
    # Read spec file
    with open(spec_path) as f:
        spec_content = f.read()
    
    # Check critical configurations
    checks = {
        "UPX disabled in EXE": "upx=False" in spec_content,
        "UPX disabled in COLLECT": spec_content.count("upx=False") >= 2,
        "Onedir mode (exclude_binaries=True)": "exclude_binaries=True" in spec_content,
        "Version info included": "version='file_version_info.txt'" in spec_content,
        "Console disabled for GUI": "console=False" in spec_content,
        "No code stripping": "strip=False" in spec_content,
        "Cryptography imports": "cryptography" in spec_content,
        "Tkinter imports": "tkinter" in spec_content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def validate_version_info():
    """Validate version info file."""
    version_path = Path("file_version_info.txt")
    
    if not version_path.exists():
        print("❌ ERROR: file_version_info.txt not found!")
        return False
    
    print("\n✓ Found file_version_info.txt")
    
    with open(version_path) as f:
        version_content = f.read()
    
    checks = {
        "Has VSVersionInfo": "VSVersionInfo" in version_content,
        "Has FileVersion": "FileVersion" in version_content,
        "Has ProductName": "ProductName" in version_content,
        "Has LegalCopyright": "LegalCopyright" in version_content,
        "Has FileDescription": "FileDescription" in version_content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def validate_documentation():
    """Validate false positive documentation exists."""
    doc_path = Path("docs/antivirus_false_positives.md")
    
    if not doc_path.exists():
        print("\n❌ ERROR: docs/antivirus_false_positives.md not found!")
        return False
    
    print("\n✓ Found docs/antivirus_false_positives.md")
    
    with open(doc_path) as f:
        doc_content = f.read()
    
    checks = {
        "Explains UPX issue": "UPX" in doc_content,
        "Mentions onedir mode": "onedir" in doc_content or "onedir" in doc_content.lower(),
        "Mentions cryptography": "cryptography" in doc_content.lower(),
        "Provides VirusTotal link": "virustotal" in doc_content.lower(),
        "Explains reporting process": "report" in doc_content.lower(),
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    """Run all validations."""
    print("=" * 60)
    print("TechCompressor Build Configuration Validation")
    print("=" * 60)
    print()
    
    spec_valid = validate_spec_file()
    version_valid = validate_version_info()
    doc_valid = validate_documentation()
    
    print()
    print("=" * 60)
    
    if spec_valid and version_valid and doc_valid:
        print("✅ All validations passed!")
        print()
        print("Build configuration is properly set up to reduce AV false positives:")
        print("  • UPX compression disabled")
        print("  • Onedir mode for transparency")
        print("  • Windows version metadata included")
        print("  • Comprehensive documentation provided")
        print()
        print("The build can be tested on Windows with: .\\build_release.ps1")
        return 0
    else:
        print("❌ Some validations failed!")
        print("Please fix the issues above before building.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
