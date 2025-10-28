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

# UPX compression (v1.3.0 optimization for size reduction)
Write-Host ""
Write-Host "[4.5/6] Compressing executable with UPX..." -ForegroundColor Yellow
$exePath = "dist\TechCompressor.exe"
$originalSize = (Get-Item $exePath).Length / 1MB

# Check if UPX is available
try {
    $upxCheck = & upx --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Running UPX --best --lzma (this may take 30-60 seconds)..." -ForegroundColor Gray
        & upx --best --lzma $exePath 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $compressedSize = (Get-Item $exePath).Length / 1MB
            $reduction = (($originalSize - $compressedSize) / $originalSize) * 100
            Write-Host "✓ UPX compression successful" -ForegroundColor Green
            Write-Host "  Before: $($originalSize.ToString('F2')) MB" -ForegroundColor Gray
            Write-Host "  After:  $($compressedSize.ToString('F2')) MB" -ForegroundColor Gray
            Write-Host "  Saved:  $($reduction.ToString('F1'))% reduction" -ForegroundColor Green
        } else {
            Write-Host "⚠ UPX compression failed, continuing with uncompressed executable" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ UPX not found - skipping compression" -ForegroundColor Yellow
        Write-Host "  Install UPX for 40-60% size reduction:" -ForegroundColor Gray
        Write-Host "  choco install upx" -ForegroundColor Gray
        Write-Host "  or download from: https://upx.github.io/" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠ UPX not available - skipping compression" -ForegroundColor Yellow
    Write-Host "  Install with: choco install upx" -ForegroundColor Gray
}

# Test the executable
Write-Host ""
Write-Host "[5/6] Testing executable..." -ForegroundColor Yellow
$exePath = "dist\TechCompressor.exe"
if (Test-Path $exePath) {
    $fileSize = (Get-Item $exePath).Length / 1MB
    Write-Host "✓ Executable created: $($fileSize.ToString('F2')) MB" -ForegroundColor Green
    
    # Quick validation - check if it starts
    Write-Host "  Validating executable (this may take a moment)..." -ForegroundColor Gray
    # Note: Can't easily test GUI startup in automated script
    Write-Host "  ⚠ Manual testing required: Launch TechCompressor.exe to verify GUI" -ForegroundColor Yellow
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

# Copy executable
Copy-Item $exePath "$tempDir\"

# Copy documentation
Copy-Item "README.md" "$tempDir\"
Copy-Item "LICENSE" "$tempDir\"
Copy-Item "CHANGELOG.md" "$tempDir\"
Copy-Item "SECURITY.md" "$tempDir\"

# Create release README
$releaseReadme = @"
# TechCompressor v$VERSION - Standalone Release

## What's Included

- **TechCompressor.exe** - Standalone GUI application (no installation needed)
- **README.md** - Full documentation and usage guide
- **LICENSE** - MIT License
- **CHANGELOG.md** - Version history and release notes
- **SECURITY.md** - Security information and reporting

## Quick Start

1. Double-click `TechCompressor.exe` to launch the GUI
2. Select files/folders to compress
3. Choose your compression algorithm (AUTO recommended)
4. Optionally add a password for encryption
5. Click "Compress" or "Create Archive"

## System Requirements

- Windows 10/11 (64-bit)
- No additional dependencies required - fully standalone!

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
Write-Host "  • Standalone EXE: dist\TechCompressor.exe" -ForegroundColor White
Write-Host "  • GitHub release ZIP: $zipPath" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the executable: dist\TechCompressor.exe" -ForegroundColor White
Write-Host "  2. Create GitHub release and upload: $zipPath" -ForegroundColor White
Write-Host "  3. Update version tags in repository" -ForegroundColor White
Write-Host ""
