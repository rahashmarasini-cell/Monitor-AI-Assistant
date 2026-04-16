# Building Monitor-AI Assistant

This document explains how to build Monitor-AI Assistant into a standalone Windows executable using PyInstaller.

## Quick Start

### PowerShell (Recommended)
```powershell
# Simple build
.\build.ps1

# Build with clean (removes previous builds)
.\build.ps1 -clean

# Build with debug output
.\build.ps1 -debug

# Build with all options
.\build.ps1 -clean -debug -version "1.0.0"
```

### Command Prompt
```batch
# Simple build
build.bat

# Build with clean
build.bat clean

# Build with debug
build.bat debug
```

## Build Pipeline Overview

```
build.ps1 / build.bat
    ↓
PyInstaller (MonitorAI.spec)
    ├── Collects Python code from src/
    ├── Includes data files (models, hooks)
    ├── Resolves hidden dependencies
    └── Outputs: dist/MonitorAI.exe
```

## Build Output

After a successful build:
```
dist/
└── MonitorAI.exe          (~200-300 MB, includes model and all dependencies)
```

The executable is self-contained and can be:
- Run on any Windows 10/11 machine (with Visual C++ Redistributable)
- Distributed to users
- No Python installation required on target machine

## Files Involved

| File | Purpose |
|------|---------|
| `MonitorAI.spec` | PyInstaller configuration (main, hidden imports, data files) |
| `build.ps1` | PowerShell build script with options |
| `build.bat` | Batch build script for Command Prompt |
| `hooks/hook-paddleocr.py` | PyInstaller hook for PaddleOCR data files |

## Build Options

### PowerShell Parameters

```powershell
-clean        # Remove previous build artifacts (build/, dist/, *.spec)
-debug        # Include debug symbols and verbose logging
-one_file     # Build single executable (default: $true)
-sign         # Code sign executable (requires certificate)
-version      # Set version string (default: "1.0.0")
```

### Example Commands

```powershell
# Production build
.\build.ps1 -clean

# Development build with debug info
.\build.ps1 -debug

# Fresh build for distribution
.\build.ps1 -clean -debug

# Build directory-based distribution (useful for large projects)
.\build.ps1 -clean -one_file:$false
```

## Prerequisites

Before building, ensure:

1. **Python environment activated**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **PyInstaller installed**
   ```powershell
   pip install pyinstaller
   ```

3. **Model file downloaded**
   ```powershell
   # Verify exists
   ls models/mistral-7b-instruct.Q4_0.ggmlv3.bin
   ```

4. **All dependencies installed**
   ```powershell
   pip install -r requirements.txt
   ```

## Build Process Details

### 1. Dependency Collection
- Scans `src/main.py` entry point
- Resolves all imports recursively
- Collects hidden imports (paddleocr, llama_cpp, etc.)
- Includes data files from packages

### 2. Spec File Processing
The `MonitorAI.spec` file specifies:
- **Entry point**: `src/main.py`
- **Hidden imports**: PaddleOCR, llama-cpp-python, screeninfo, etc.
- **Data files**: Model files, hooks directory
- **Console mode**: Disabled (no console window)
- **Single-file mode**: Creates one executable with all dependencies

### 3. Executable Generation
- Bundles Python interpreter
- Includes all dependencies
- Includes model file (3.8 GB)
- Creates bootloader for runtime environment

### 4. Output
```
dist/MonitorAI.exe (200-300 MB depending on options)
```

## Troubleshooting

### Build Fails with "Module not found"
**Problem**: PyInstaller can't find a module
```
ModuleNotFoundError: No module named 'paddleocr'
```

**Solution**:
1. Verify module is installed: `pip list | grep paddleocr`
2. Check Python version: `python --version` (should be 3.9+)
3. Rebuild and check `MonitorAI.spec` hidden imports

```python
# In MonitorAI.spec, ensure module is in hidden_imports:
hidden_imports = [
    'paddleocr',
    'paddleocr.paddle_ocr',
    'llama_cpp',
    # ... etc
]
```

### Build Takes Too Long
**Problem**: Building is slow (~5-10 minutes)

**Causes**:
- First build always takes longer (collecting all imports)
- Model file is large (3.8 GB)
- Disk I/O bottleneck (use SSD)

**Solutions**:
- Use SSD instead of HDD
- Run on machine with more RAM
- Use directory distribution (remove `--onefile`)

### Output File Too Large
**Problem**: `MonitorAI.exe` is 200+ MB

**Expected**: Yes, includes:
- Python interpreter: ~50 MB
- All dependencies: ~100 MB
- Model file: ~3.8 GB (only if building with model)

**To reduce**:
1. Exclude model from executable, download at runtime
2. Use UPX compression: `pyinstaller --upx-dir="C:\path\to\upx"` (saves 30%)
3. Build directory distribution instead of one-file

### "model file not found at models/mistral-7b-instruct.Q4_0.ggmlv3.bin"
**Solution**:
```powershell
# Download the model
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download(
    repo_id='TheBloke/Mistral-7B-Instruct-v0.1-GGUF',
    filename='mistral-7b-instruct-v0.1.Q4_0.gguf',
    local_dir='models',
    local_dir_use_symlinks=False
)
"
```

### Build succeeds but executable won't run
**Problem**: `MonitorAI.exe` crashes on startup

**Check**:
1. **Visual C++ Redistributable**: Install from Windows Update or [Microsoft](https://support.microsoft.com/help/2977003)
2. **Run with error output**: 
   ```powershell
   cd dist
   .\MonitorAI.exe 2>&1 | Out-String
   ```
3. **Try debug build**:
   ```powershell
   .\build.ps1 -debug
   ```

### "Access denied" when cleaning build directory
**Solution**: Close any programs using the directory, then:
```powershell
# Manual cleanup
Remove-Item -Recurse -Force build, dist
```

## Testing the Build

After successful build:

```powershell
# 1. Navigate to dist directory
cd dist

# 2. Run executable
.\MonitorAI.exe

# 3. Test functionality
# - Check if answer window appears on second monitor
# - Test screen capture and OCR
# - Verify LLM inference works

# 4. Check logs
# - Look for error messages in console/event log
```

## Advanced Customization

### Custom Icon
Add application icon to executable:

1. Create or obtain `icon.ico` (256×256 recommended)
2. Place in project root
3. Uncomment in `MonitorAI.spec`:
   ```python
   icon='icon.ico' if os.path.exists('icon.ico') else None,
   ```
4. Rebuild

### Code Signing
For production distribution, sign the executable:

```powershell
# Requires code signing certificate
signtool sign /f certificate.pfx /p password ^
    /t http://timestamp.comodoca.com/authenticode ^
    dist/MonitorAI.exe
```

### One-File vs. Directory Distribution

**One-File (default)**
- Pros: Single executable, easy to distribute
- Cons: Takes longer to start (extracts to temp)
- Use for: End-user distribution

**Directory (optional)**
- Pros: Faster startup, easier debugging
- Cons: More files to distribute
- Use for: Developer/insider builds

To use directory distribution:
```python
# Uncomment in MonitorAI.spec:
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='MonitorAI'
)
```

## CI/CD Integration

To automate builds in GitHub Actions or Azure Pipelines:

```yaml
- name: Build Monitor-AI
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyinstaller
    .\build.ps1 -clean
```

## Performance Metrics

| Metric | Value |
|--------|-------|
| Build time (first) | 5-10 minutes |
| Build time (incremental) | 2-5 minutes |
| Executable size | 200-300 MB |
| Runtime startup | 3-5 seconds (one-file) |
| First inference | 2-3 seconds (model loading) |
| Subsequent inference | 5-10 seconds (CPU) / 1-2 seconds (GPU) |

## Distribution

After building and testing:

1. **Create distribution package**:
   ```powershell
   # Copy exe and necessary files
   mkdir -p "MonitorAI-release/bin"
   Copy-Item "dist/MonitorAI.exe" "MonitorAI-release/bin/"
   Copy-Item "README.md" "MonitorAI-release/"
   Copy-Item "DEPENDENCIES.md" "MonitorAI-release/"
   ```

2. **Create installer** (optional):
   - Use NSIS or Inno Setup
   - Bundle Visual C++ Redistributable
   - Set registry entries if needed

3. **Upload to release channel**:
   - GitHub Releases
   - Azure Artifacts
   - Distribution server

## Further Reading

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Hooks](https://github.com/pyinstaller/pyinstaller-hooks-contrib)
- [Windows Deployment Best Practices](https://docs.microsoft.com/windows/win32/msi/deployment-best-practices)
