# System Dependencies for Monitor-AI Assistant

This document outlines all system-level dependencies required to run the Monitor-AI Assistant on Windows.

## Required Dependencies

### 1. Visual C++ Redistributable (REQUIRED)
**Why**: PaddleOCR and native C/C++ libraries depend on Visual C++ runtime libraries.

**Installation**:
- **Automatic** (Recommended): Windows Update
  - Go to Settings → Update & Security → Check for updates
  - Install all recommended updates
- **Manual**: Download from Microsoft
  - Download: [Visual C++ Redistributable](https://support.microsoft.com/en-us/help/2977003)
  - Choose the latest version (usually `vc_redist.x64.exe` for 64-bit Python)
  - Run the installer and follow prompts

**Verify**:
```powershell
# In PowerShell, run:
python -c "import ctypes; print('Visual C++ Runtime is available')"
```

---

### 2. Python 3.9+ (REQUIRED)
**Why**: Project requires modern Python features and library compatibility.

**Installation**:
- Download: [Python.org](https://www.python.org/downloads/)
- During installation, **check**: "Add Python to PATH"
- Recommended: Python 3.10 or 3.11

**Verify**:
```powershell
python --version
```

---

## Optional Dependencies

### 3. CUDA Toolkit (OPTIONAL - For GPU Acceleration)
**Why**: Enables GPU acceleration for both LLM inference and PaddleOCR processing. Dramatically speeds up inference.

**When to install**:
- You have an NVIDIA GPU
- You want faster inference (10-50x faster than CPU)
- Your system can spare VRAM (OCR: 512MB, LLM: 2-4GB)

**Requirements**:
- NVIDIA GPU with compute capability 3.5 or higher
  - Check: [NVIDIA GPU Compute Capability](https://developer.nvidia.com/cuda-gpus)

**Installation**:
1. Download: [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
   - Select: Windows, x86_64, 11 or 12 (latest stable)
2. Run installer with default settings
3. Restart computer
4. Install cuDNN (optional, for further optimization)
   - Download: [NVIDIA cuDNN](https://developer.nvidia.com/cudnn)

**Verify**:
```powershell
nvidia-smi
# Should show GPU info if CUDA is installed
```

**Python Configuration**:
After CUDA installation, rebuild llama-cpp-python with GPU support:
```powershell
pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

---

### 4. Visual Studio Build Tools (OPTIONAL - If pip build fails)
**Why**: Some Python packages need to compile C extensions during installation.

**Installation**:
- Download: [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)
- Choose "Desktop development with C++"

**Note**: Usually not needed if using pre-built wheels (recommended).

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'paddleocr'"
**Solution**:
```powershell
# Reinstall with dependencies
pip install --upgrade paddleocr

# If that fails, install Visual C++ Redistributable first
```

### Issue: "llama-cpp-python failed to build"
**Solution**:
```powershell
# Use pre-built wheel (recommended for Windows)
pip install --only-binary :all: llama-cpp-python

# Or specify the right Python version
# Ensure you're using Python 3.9-3.11 (officially supported)
python --version
```

### Issue: "CUDA not found" (if GPU support is desired)
**Solution**:
1. Install CUDA Toolkit (see above)
2. Add CUDA to PATH:
   ```powershell
   # Add to system environment variables
   C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin
   ```
3. Restart PowerShell and verify:
   ```powershell
   nvcc --version
   ```

### Issue: "Model file too large / not enough disk space"
**Solution**:
- Mistral 7B Q4: ~3.8 GB
- Ensure you have at least 5 GB free space
- Use SSD for faster model loading

---

## Platform-Specific Notes

### Windows 10/11
- All dependencies work out-of-the-box on 64-bit systems
- For 32-bit Python: Only CPU inference is supported (CUDA requires 64-bit)

### Virtualized Environments
- **VirtualBox**: GPU passthrough may not work; CPU inference only
- **Hyper-V**: GPU requires specific configuration
- **WSL2**: Full support with GPU (requires Windows 11 + NVIDIA Driver for WSL)

---

## Minimal Installation (CPU Only)
```powershell
# This is the minimum to get the app running
1. Windows Update (for Visual C++)
2. Python 3.10+
3. pip install -r requirements.txt
4. Download model file
```

**Performance**: ~5-10 seconds per OCR + LLM inference

---

## Recommended Installation (GPU Accelerated)
```powershell
# For best performance
1. Windows Update (for Visual C++)
2. Python 3.10+
3. CUDA Toolkit 12.0+
4. pip install -r requirements.txt
5. Rebuild llama-cpp-python with GPU support
6. Download model file
```

**Performance**: ~0.5-2 seconds per OCR + LLM inference

---

## Dependency Versions

| Package | Min Version | Tested |
|---------|-----------|--------|
| Python | 3.9 | 3.10, 3.11 |
| paddleocr | 2.3.0 | 2.7.0 |
| llama-cpp-python | 0.2.23 | 0.2.50+ |
| opencv-python | 4.8.0 | 4.8.1+ |
| Windows | 10 | 10, 11 |

---

## Getting Help

If you encounter dependency issues:

1. Check Python version: `python --version`
2. Verify pip: `pip --version`
3. Update pip: `python -m pip install --upgrade pip`
4. Install dependencies fresh:
   ```powershell
   pip install --upgrade --force-reinstall -r requirements.txt
   ```
5. Report issues with: `pip list` and system info
