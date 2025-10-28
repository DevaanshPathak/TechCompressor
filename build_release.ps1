# TechCompressor Release Build Script
# Builds standalone executable and creates release package

Write-Host "================================" -ForegroundColor Cyan
Write-Host "TechCompressor Release Builder" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Extract version from pyproject.toml
Write-Host "Reading version from pyproject.toml..." -ForegroundColor Yellow
$pyprojectContent = Get-Content "pyproject.toml" -Raw
if ($pyprojectContent -match 'version\s*=\s*"([^"]+)"') {
    $VERSION = $matches[1]
    Write-Host "✓ Building version: $VERSION" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to extract version from pyproject.toml" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if PyInstaller is installed
Write-Host "[1/6] Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
        pip install pyinstaller
    }
    Write-Host "✓ PyInstaller ready" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to check/install PyInstaller" -ForegroundColor Red
    exit 1
}

# Clean previous builds
Write-Host ""
Write-Host "[2/6] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Write-Host "✓ Cleaned" -ForegroundColor Green

# Run tests
Write-Host ""
Write-Host "[3/6] Running test suite..." -ForegroundColor Yellow
python -m pytest tests/ -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Tests failed! Aborting build." -ForegroundColor Red
    exit 1
}
Write-Host "✓ All tests passed" -ForegroundColor Green

# Build executable with PyInstaller
Write-Host ""
Write-Host "[4/6] Building executable with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller techcompressor.spec --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Executable built" -ForegroundColor Green

# Test the executable
Write-Host ""
Write-Host "[5/6] Testing executable..." -ForegroundColor Yellow
$appDir = "dist\TechCompressor"
$exePath = "$appDir\TechCompressor.exe"
if (Test-Path $exePath) {
    $fileSize = (Get-Item $exePath).Length / 1MB
    Write-Host "✓ Executable created: $($fileSize.ToString('F2')) MB" -ForegroundColor Green
    
    # Calculate total directory size
    $totalSize = (Get-ChildItem $appDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "  Total application size: $($totalSize.ToString('F2')) MB" -ForegroundColor Gray
    
    # Quick validation - check if it starts
    Write-Host "  Validating executable (this may take a moment)..." -ForegroundColor Gray
    # Note: Can't easily test GUI startup in automated script
    Write-Host "  ⚠ Manual testing required: Launch TechCompressor\TechCompressor.exe to verify GUI" -ForegroundColor Yellow
} else {
    Write-Host "✗ Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

# Create release ZIP package
Write-Host ""
Write-Host "[6/6] Creating release ZIP..." -ForegroundColor Yellow

# Create temporary staging directory
$tempDir = "dist\temp_release"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

# Copy entire application folder (onedir mode includes all dependencies)
Copy-Item -Recurse "$appDir" "$tempDir\TechCompressor"

# Copy documentation
Copy-Item "README.md" "$tempDir\"
Copy-Item "LICENSE" "$tempDir\"
Copy-Item "CHANGELOG.md" "$tempDir\"
Copy-Item "SECURITY.md" "$tempDir\"

# Create release README
$releaseReadme = @"
# TechCompressor v$VERSION - Standalone Release

## What's Included

- **TechCompressor/** - Application folder with all dependencies
  - **TechCompressor.exe** - Main GUI application (run this)
  - Supporting libraries and dependencies
- **README.md** - Full documentation and usage guide
- **LICENSE** - MIT License
- **CHANGELOG.md** - Version history and release notes
- **SECURITY.md** - Security information and reporting

## Quick Start

1. Extract the entire ZIP archive to your desired location
2. Navigate to the **TechCompressor** folder
3. Double-click **TechCompressor.exe** to launch the GUI
4. Select files/folders to compress
5. Choose your compression algorithm (AUTO recommended)
6. Optionally add a password for encryption
7. Click "Compress" or "Create Archive"

## System Requirements

- Windows 10/11 (64-bit)
- No installation required - fully portable!
- Keep all files in the TechCompressor folder together

## About This Build

This release uses a **directory-based executable** (onedir mode) instead of a 
single-file executable. This approach:

- **Reduces false positives** from antivirus software significantly
- Makes the application more transparent and trustworthy
- Loads faster and uses less memory
- All dependencies are visible and can be verified

**Note on Antivirus Warnings**: If you still see antivirus warnings, this is a 
known false positive with PyInstaller applications that use cryptography. The 
application is open-source and can be verified at our GitHub repository. You may 
need to add an exception in your antivirus software.

## Features

- **3 Compression Algorithms**: LZW, Huffman, DEFLATE
- **Smart AUTO Mode**: Automatically selects best algorithm
- **STORED Mode**: Skips compression for incompressible files (PNGs, JPEGs, etc.)
- **AES-256-GCM Encryption**: Military-grade password protection
- **Archive Format (TCAF v2)**: Compress entire folders with metadata
- **Cross-platform Archives**: Create on Windows, extract anywhere

## Support

- GitHub: https://github.com/DevaanshPathak/TechCompressor
- Issues: https://github.com/DevaanshPathak/TechCompressor/issues
- False Positive Reports: See SECURITY.md for reporting guidelines

## License

MIT License - Free for personal and commercial use
Copyright (c) 2025 Devaansh Pathak
"@

$releaseReadme | Out-File -FilePath "$tempDir\README_RELEASE.txt" -Encoding UTF8

# Create ZIP for distribution
$zipName = "TechCompressor-v$VERSION-Windows-x64.zip"
$zipPath = "dist\$zipName"
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force

# Clean up temp directory
Remove-Item -Recurse -Force $tempDir

if (Test-Path $zipPath) {
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Host "✓ Release ZIP created: $zipPath ($($zipSize.ToString('F2')) MB)" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create ZIP" -ForegroundColor Red
    exit 1
}

# Final summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Release files:" -ForegroundColor White
Write-Host "  • Application folder: dist\TechCompressor\" -ForegroundColor White
Write-Host "  • Main executable: dist\TechCompressor\TechCompressor.exe" -ForegroundColor White
Write-Host "  • GitHub release ZIP: $zipPath" -ForegroundColor White
Write-Host ""
Write-Host "Antivirus False Positive Mitigation:" -ForegroundColor Yellow
Write-Host "  ✓ UPX compression disabled (primary trigger)" -ForegroundColor Green
Write-Host "  ✓ Onedir mode for transparency" -ForegroundColor Green
Write-Host "  ✓ Windows version metadata included" -ForegroundColor Green
Write-Host "  ✓ Minimal binary obfuscation" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the executable: dist\TechCompressor\TechCompressor.exe" -ForegroundColor White
Write-Host "  2. Scan with VirusTotal: https://www.virustotal.com" -ForegroundColor White
Write-Host "  3. Create GitHub release and upload: $zipPath" -ForegroundColor White
Write-Host "  4. Report false positives to AV vendors if needed" -ForegroundColor White
Write-Host ""
