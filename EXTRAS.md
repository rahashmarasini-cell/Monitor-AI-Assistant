# Monitor AI Assistant — Extras

Supplementary reference for non-core parts of the project. See [GUIDE.md](GUIDE.md) for the main pipeline.

---

## Graph Analyzer — [src/graph_analyzer.py](src/graph_analyzer.py)

Detects and analyzes charts/graphs in screenshots using OpenCV.

**`GraphData`** dataclass — what each analysis returns:

| Field | Type | Description |
|---|---|---|
| `title` | str | Detected graph title |
| `x_axis_label` | str | X-axis label |
| `y_axis_label` | str | Y-axis label |
| `data_points` | List[Tuple] | Detected (x, y) coordinates |
| `extracted_values` | Dict | Text/values found in the graph |
| `description` | str | Human-readable summary |
| `confidence` | float | Score 0–1 |

**Detection heuristics**: Canny edge detection + contour analysis. Accepts contours covering 10–70% of image area, aspect ratio 0.5–2.0. Data points identified by HSV color ranges (red, blue, green markers).

`ai_processor.py` calls this automatically when a graph is detected in the screenshot.

---

## Tests — [tests/](tests/)

| File | Status | What it covers |
|---|---|---|
| `test_graph_analyzer.py` | Current | 32 tests: init, detection, data points, file errors, performance (<1s target) |
| `test_ai.py` | Outdated | References old module names; needs update |
| `test_ocr.py` | Outdated | References old module names; needs update |

Run tests:
```
python -m pytest tests/
```

---

## Build — [MonitorAI.spec](MonitorAI.spec) / [build.ps1](build.ps1)

Packages the app into a single `dist/MonitorAI.exe` using PyInstaller.

```
.\build.ps1          # PowerShell
build.bat            # or batch
```

- Bundles Python interpreter, all deps, and optionally the model file
- Build time: 5–10 min first run, 2–5 min incremental
- Output size: ~200–300 MB without model; ~4 GB with model included

The spec file includes hidden imports for `paddleocr`, `llama_cpp`, `mss`, `cv2`, `screeninfo`, and `tkinter`.

---

## CI/CD — [.github/workflows/build.yml](.github/workflows/build.yml)

Runs on push to `main`/`develop`, pull requests, tags, and manual dispatch.

Matrix: Python 3.10 and 3.11 on Windows.

Steps: checkout → install deps → build with PyInstaller → upload artifact (30-day retention) → create GitHub release on tag push.

---

## Setup Utilities

| File | Purpose |
|---|---|
| [verify_setup.py](verify_setup.py) | Checks Tesseract path, model file, and Python deps; run before first launch |
| [install_tesseract.py](install_tesseract.py) | Helper script for Tesseract installation guidance |

---

## Placeholder Files

`src/assistant.py` and `src/config_window.py` are empty. Intended for a future interactive query interface and a settings GUI respectively.

---

## Existing Docs

These files are still around but mostly covered by this guide:

| File | Content |
|---|---|
| `README.md` | Original overview and install steps |
| `BUILD.md` | Detailed PyInstaller build guide |
| `DEPENDENCIES.md` | System dependency notes (VC++, CUDA) |
| `IMPLEMENTATION_SUMMARY.md` | Architecture and design pattern notes |
| `TESSERACT_SETUP.md` | Tesseract install walkthrough |
| `GRAPH_ANALYSIS.md` | Graph detection algorithm details |
