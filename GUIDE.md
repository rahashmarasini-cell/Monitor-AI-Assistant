# Monitor AI Assistant — Core Guide

A dual-monitor productivity tool that continuously captures your screen, extracts text via OCR, and displays AI-generated answers on a second monitor.

---

## How It Works

```
Monitor 1 (source)                              Monitor 2 (display)
┌──────────────┐                               ┌──────────────────┐
│  Your screen │ → capture → OCR → LLM →       │  AI answer (UI)  │
└──────────────┘                               └──────────────────┘
```

Every 2 seconds (configurable):
1. **screen_capture.py** grabs a screenshot from Monitor 1
2. **ocr_processor.py** extracts text from the image
3. **ai_processor.py** builds a prompt and queries the local LLM
4. **local_llm.py** runs inference on-device (CPU, Mistral 7B)
5. **answer_window.py** displays the response fullscreen on Monitor 2

The background worker thread runs steps 1–4; the Tkinter main thread runs step 5. Updates cross threads via `root.after(0, ...)`.

---

## Entry Point — [src/main.py](src/main.py)

Starts the app:
- Creates `AnswerWindow` on the main thread
- Launches a daemon worker thread that loops the capture pipeline
- On window close, signals a stop event and joins the worker (5s timeout)

```
python src/main.py
```

---

## Configuration — [src/config.py](src/config.py)

All tuneable settings live here. Edit this file to change behavior.

| Setting | Default | What it does |
|---|---|---|
| `CAPTURE_MONITOR_INDEX` | `0` | Source monitor (0-based) |
| `ANSWER_MONITOR_INDEX` | `1` | Display monitor for answers |
| `CAPTURE_INTERVAL` | `2.0` | Seconds between captures |
| `LOCAL_MODEL_PATH` | `MONITOR-AI-ASSISTANT/models/mistral-7b-v0.1.Q4_0.gguf` | Path to GGUF model |
| `LOCAL_N_CTX` | `2048` | LLM context window (tokens) |
| `LOCAL_N_BATCH` | `512` | Prompt batch size |
| `LOCAL_TEMPERATURE` | `0.2` | Lower = more focused/deterministic |
| `TESSERACT_CMD_PATH` | `C:/Program Files/Tesseract-OCR/tesseract.exe` | Tesseract binary path |
| `TESSERACT_LANGUAGES` | `"eng"` | OCR language(s); use `"eng+fra"` for multi |
| `PROMPT_TEMPLATE` | See file | Wraps extracted text before sending to LLM |

Override `LOCAL_MODEL_PATH` via environment variable: `set LOCAL_MODEL_PATH=path\to\model.gguf`

---

## Screen Capture — [src/screen_capture.py](src/screen_capture.py)

Thin wrapper around `mss`. Grabs the monitor at `CAPTURE_MONITOR_INDEX` and saves it to `data/last_capture.png`.

- Fast (< 100ms per capture)
- Returns the file path for downstream use

---

## OCR Processor — [src/ocr_processor.py](src/ocr_processor.py)

The most complex module (~567 lines). Preprocesses the screenshot and runs Tesseract.

**Default function used by the pipeline**: `extract_text_from_image(path)` — applies the full enhancement pipeline.

**Preprocessing steps** (in `enhance_for_ocr()`):
1. Convert to grayscale
2. CLAHE (contrast enhancement)
3. Bilateral filtering (edge-preserving denoise)
4. Adaptive thresholding

**Other available modes:**

| Function | When to use |
|---|---|
| `extract_text_basic()` | Fast, no preprocessing |
| `extract_text_enhanced()` | Default; best for most screens |
| `extract_text_with_confidence()` | Returns word-level confidence scores |
| `extract_text_multi_mode()` | Unknown document layouts; tries multiple PSMs |
| `ocr_batch_process()` | Multiple images at once |

**Diagnostics**: `verify_tesseract_installation()` and `get_ocr_status()` report Tesseract availability.

---

## AI Processor — [src/ai_processor.py](src/ai_processor.py)

Bridges OCR output and the local LLM.

1. `build_prompt(extracted_text)` — wraps text in `PROMPT_TEMPLATE` from config
2. `query_llm(text)` — calls `LocalLLM.generate()`, then `clean_llm_response()`
3. Integrates with `graph_analyzer` when the screenshot contains charts

Returned string is what gets displayed in the UI.

---

## Local LLM — [src/local_llm.py](src/local_llm.py)

Wraps `llama-cpp-python` for on-device inference.

- **Windows-only** (enforced at runtime)
- **CPU inference** (`n_gpu_layers=0`; rebuild wheel for GPU/DirectML)
- **Lazy loading** — model loads on first `generate()` call (~5–10s)
- **Model**: Mistral 7B Instruct Q4_0 GGUF (~3.8 GB); place at the path in config
- **Max output**: 512 tokens per call

```python
llm = LocalLLM()
answer = llm.generate(prompt, max_tokens=512)
```

---

## Answer Window — [src/answer_window.py](src/answer_window.py)

Tkinter fullscreen window on Monitor 2.

- Green text `#00FF00` on black background
- Scrolled text widget (read-only)
- Auto-positions using `screeninfo.get_monitors()` with `ANSWER_MONITOR_INDEX`
- Thread-safe updates via `root.after(0, update_text)`

---

## Quick Setup

1. Install [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) to `C:\Program Files\Tesseract-OCR\`
2. Download `mistral-7b-v0.1.Q4_0.gguf` and place it under `MONITOR-AI-ASSISTANT/models/`
3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Verify the setup:
   ```
   python verify_setup.py
   ```
5. Run:
   ```
   python src/main.py
   ```

---

## Performance (CPU)

| Step | Approx. time |
|---|---|
| Screen capture | < 100ms |
| OCR | 2–5s |
| LLM inference | 5–10s (first call slower) |
| Graph detection | < 1s |

At the default 2s capture interval, cycles overlap slightly. GPU support via DirectML can bring total cycle time to ~2–4s.
