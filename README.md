# Monitor-AI-Assistant

## Local‑LLM (no OpenAI needed)

The assistant now runs a **local LLM** via `llama-cpp-python`.  
Follow these steps once:

1. **Install system dependencies** (Windows):
   - **Visual C++ Redistributable**: Required for PaddleOCR and native libraries
     - Download: [Visual C++ Redistributable (latest)](https://support.microsoft.com/en-us/help/2977003)
     - Or install via Windows Update
   - **Optional: CUDA Toolkit** (for GPU acceleration)
     - Only needed if you want GPU support for the LLM or OCR
     - Download: [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)
     - Requires NVIDIA GPU with compute capability 3.5+

2. **Install the Python dependencies** (the `requirements.txt` already includes `llama-cpp-python`):

   ```powershell
   pip install -r requirements.txt
   ```

3. **Download a GGML quantised model** – e.g. Mistral‑7B‑Instruct:

   ```powershell
   mkdir models
   cd models
   curl -L -o mistral-7b-instruct.Q4_0.ggmlv3.bin ^
     https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGML/resolve/main/mistral-7b-instruct-v0.1.Q4_0.ggmlv3.bin
   cd ..

## Building a Standalone Executable

To create a standalone Windows executable for distribution:

```powershell
# Simple build
.\build.ps1

# Clean and rebuild
.\build.ps1 -clean

# Build with debug output
.\build.ps1 -debug
```

Output: `dist/MonitorAI.exe` (~200-300 MB, includes all dependencies + model)

**Requirements for building:**
- PyInstaller: `pip install pyinstaller`
- Model file downloaded to `models/`

**For running the built exe:**
- Windows 10/11 (64-bit)
- Visual C++ Redistributable

See [BUILD.md](BUILD.md) and [BUILD_SUMMARY.md](BUILD_SUMMARY.md) for detailed build documentation.

