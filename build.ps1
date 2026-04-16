# Build script for Monitor-AI Assistant using PyInstaller
# Usage: .\build.ps1 [--clean] [--one-file] [--sign] [--version VERSION]

param(
    [switch]$clean = $false,
    [switch]$one_file = $true,
    [switch]$sign = $false,
    [string]$version = "1.0.0",
    [switch]$debug = $false
)

# Color output
function Write-Info { Write-Host "[INFO]" -ForegroundColor Cyan -NoNewline; Write-Host " $args" }
function Write-Success { Write-Host "[SUCCESS]" -ForegroundColor Green -NoNewline; Write-Host " $args" }
function Write-Error-Custom { Write-Host "[ERROR]" -ForegroundColor Red -NoNewline; Write-Host " $args" }
function Write-Warning-Custom { Write-Host "[WARNING]" -ForegroundColor Yellow -NoNewline; Write-Host " $args" }

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Verify PyInstaller is installed
Write-Info "Checking PyInstaller installation..."
try {
    $pyinstallerVersion = python -m PyInstaller --version 2>$null
    Write-Success "PyInstaller found: $pyinstallerVersion"
} catch {
    Write-Error-Custom "PyInstaller not found. Installing..."
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to install PyInstaller"
        exit 1
    }
}

# Verify model file exists
if (-not (Test-Path "models/mistral-7b-instruct.Q4_0.ggmlv3.bin")) {
    Write-Error-Custom "Model file not found at models/mistral-7b-instruct.Q4_0.ggmlv3.bin"
    Write-Info "Please download the model first"
    exit 1
}
Write-Success "Model file verified"

# Clean previous builds if requested
if ($clean) {
    Write-Info "Cleaning previous builds..."
    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build" | Out-Null
        Write-Success "Removed build/ directory"
    }
    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist" | Out-Null
        Write-Success "Removed dist/ directory"
    }
    if (Test-Path "MonitorAI.spec") {
        Remove-Item "MonitorAI.spec" | Out-Null
        Write-Success "Removed MonitorAI.spec"
    }
}

# Build command
$buildArgs = @(
    "MonitorAI.spec",
    "--distpath", "dist",
    "--buildpath", "build",
    "--specpath", ".",
    "--noconfirm",
    "--log-level", $(if ($debug) { "DEBUG" } else { "INFO" })
)

if ($one_file) {
    $buildArgs += "--onefile"
    Write-Info "Building one-file executable..."
} else {
    Write-Info "Building directory-based distribution..."
}

# Run PyInstaller
Write-Info "Starting build process..."
Write-Info "Command: pyinstaller $($buildArgs -join ' ')"
Write-Host ""

python -m PyInstaller $buildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error-Custom "Build failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Success "Build completed successfully!"

# Output location
if ($one_file) {
    $outputFile = "dist/MonitorAI.exe"
    if (Test-Path $outputFile) {
        $size = [math]::Round((Get-Item $outputFile).Length / 1MB, 2)
        Write-Success "Executable created: $outputFile ($size MB)"
    }
} else {
    $outputDir = "dist/MonitorAI"
    if (Test-Path $outputDir) {
        Write-Success "Distribution directory created: $outputDir"
        $fileCount = (Get-ChildItem $outputDir -Recurse).Count
        Write-Info "Total files: $fileCount"
    }
}

# Code signing (optional)
if ($sign) {
    Write-Info "Code signing not yet configured"
    Write-Info "To enable code signing, set up certificate and uncomment signing code"
}

# Build summary
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Build Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Info "Version: $version"
Write-Info "Build type: $(if ($one_file) { 'Single-file' } else { 'Directory' })"
Write-Info "Debug mode: $debug"
Write-Host ""

Write-Success "Build pipeline completed!"
Write-Info "Next steps:"
Write-Info "  1. Test the executable: dist/MonitorAI.exe"
Write-Info "  2. Verify model loading and OCR functionality"
Write-Info "  3. Package for distribution if satisfied"
Write-Host ""
