"""
Two-phase vision pipeline via Ollama.

Phase 1 — llava-llama3  : reads the screenshot, extracts question + choices as plain text.
Phase 2 — deepseek-r1:7b: receives clean text, solves step-by-step with chain-of-thought.

Separating reading from reasoning eliminates the core failure mode where a single
vision model both misreads the image AND makes algebra errors.
"""

import base64
import io
import json
import os
import subprocess
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable, Optional

OLLAMA_URL = "http://localhost:11434"
VISION_MODEL  = "llava-llama3"   # reads the image only
MATH_MODEL    = "deepseek-r1:7b" # solves the extracted problem
_FALLBACK_VISION = "llava:7b"
TIMEOUT = 360  # deepseek-r1 chain-of-thought on CPU can take 3-4 minutes

_OLLAMA_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"

_EXTRACT_SYSTEM = (
    "You are a precise text extractor for exam screenshots. "
    "Your ONLY job is to read the screen and output the question and answer choices verbatim. "
    "Do NOT solve anything. Do NOT explain. Output the text exactly as it appears."
)

_SOLVE_SYSTEM = (
    "You are a math tutor. Solve the multiple-choice problem step by step. "
    "Show all working. Apply these rules without exception:\n"
    "• i² = -1\n"
    "• Powers of i cycle every 4: i¹=i, i²=-1, i³=-i, i⁴=1\n"
    "• FOIL: (A+Bi)(C+Di) = A·C + A·Di + Bi·C + Bi·Di = (AC-BD)+(AD+BC)i\n"
    "• Preserve every negative sign inside parentheses\n"
    "End your response with: Answer: X.) [value]"
)


# ---------------------------------------------------------------------------
# Ollama helpers
# ---------------------------------------------------------------------------

def _available_models() -> list[str]:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3) as r:
            return [m.get("name", "") for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return []


def _resolve_vision_model() -> str:
    names = _available_models()
    if any(VISION_MODEL in n for n in names):
        return VISION_MODEL
    if any(_FALLBACK_VISION in n for n in names):
        return _FALLBACK_VISION
    return VISION_MODEL


def _math_model_available() -> bool:
    return any(MATH_MODEL in n for n in _available_models())


def _try_start_ollama() -> None:
    if _OLLAMA_EXE.exists():
        subprocess.Popen(
            [str(_OLLAMA_EXE), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )


def is_ollama_running() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        return True
    except Exception:
        pass
    _try_start_ollama()
    time.sleep(4)
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Image preparation
# ---------------------------------------------------------------------------

def _crop_to_question(image_path: Path):
    """
    Remove browser chrome (top 13%), taskbar (bottom 8%), and right sidebar (37%).
    Returns a PIL Image of the question area only.
    """
    from PIL import Image
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    return img.crop((0, int(h * 0.13), int(w * 0.63), int(h * 0.92)))


def _encode_image(image_path: Path) -> str:
    """Crop to question area and encode as lossless PNG (preserves math notation)."""
    buf = io.BytesIO()
    _crop_to_question(image_path).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------------------------------------------------------------------------
# Math OCR cleanup
# ---------------------------------------------------------------------------

def _fix_math_ocr(text: str) -> str:
    """Fix character substitutions Tesseract makes in italic math fonts."""
    import re
    # Italic "7" misread as "T" when adjacent to i or operators
    text = re.sub(r'(?<=[+\-*(,\s(])T(?=i\b)', '7', text)
    text = re.sub(r'\bTi\b', '7i', text)
    text = re.sub(r'(?<=\d)Ti\b', '7i', text)
    # S→5, Z→2 in math context
    text = re.sub(r'(?<=[+\-*(,\s(])S(?=[i\d])', '5', text)
    text = re.sub(r'(?<=[+\-*(,\s(])Z(?=[i\d])', '2', text)
    # Trailing ) or / after digit at end of line → i  (italic i misread)
    text = re.sub(r'(\d)[)/](\s*)$', r'\1i\2', text, flags=re.MULTILINE)
    # Isolated | or ! between operators → i
    text = re.sub(r'(?<=\d)[|!](?=\s*[+\-)])', 'i', text)
    # i2 at end of term → i²
    text = re.sub(r'\bi2\b', 'i²', text)
    text = re.sub(r'i2(?=\s*[+\-)]|$)', 'i²', text, flags=re.MULTILINE)
    return text


def _ocr_extract(image_path: Path) -> str:
    """OCR the cropped question area; returns cleaned text."""
    import re
    try:
        import pytesseract
        from PIL import ImageEnhance, ImageFilter, ImageOps, Image as _Img
        import numpy as np
        img = _crop_to_question(image_path).convert("L")
        arr = np.array(img)
        if arr.mean() < 128:
            img = ImageOps.invert(img)
        img = img.resize((img.width * 2, img.height * 2), _Img.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = img.filter(ImageFilter.SHARPEN)
        raw = pytesseract.image_to_string(img, config="--psm 6 --oem 1 -l eng")
        raw = _fix_math_ocr(raw)
        _noise = re.compile(r'https?://|HEIEIE|^[^a-zA-Z0-9()\-+.]*$')
        lines = [
            l.strip() for l in raw.splitlines()
            if l.strip() and len(l.strip()) >= 3 and not _noise.search(l)
        ]
        return "\n".join(lines)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Phase 1 — vision extraction (non-streaming, unloads model after)
# ---------------------------------------------------------------------------

def _extract_question(image_path: Path, ocr_hint: str) -> str:
    """
    Ask the vision model to read the question and answer choices verbatim.
    Sets keep_alive=0 so VRAM is freed immediately for the math model.
    """
    prompt = (
        "Read this exam screenshot carefully.\n"
        "Output EXACTLY:\n"
        "- The question text (word for word)\n"
        "- Each answer choice labeled a/b/c/d (word for word)\n"
        "Do NOT solve. Do NOT add commentary."
    )
    if ocr_hint:
        prompt += f"\n\nOCR reading (may have character errors — verify against image):\n{ocr_hint}"

    payload = json.dumps({
        "model": _resolve_vision_model(),
        "system": _EXTRACT_SYSTEM,
        "prompt": prompt,
        "images": [_encode_image(image_path)],
        "stream": False,
        "keep_alive": 0,   # unload immediately — free VRAM for math model
        "options": {"num_gpu": 99, "temperature": 0.1, "num_predict": 300},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result = json.loads(resp.read())
            return result.get("response", "").strip()
    except Exception as e:
        return f"[Vision extraction failed: {e}]"


# ---------------------------------------------------------------------------
# Phase 2 — math solving (streaming)
# ---------------------------------------------------------------------------

def _stream_math_solve(
    extracted_question: str,
    on_token: Callable[[str], None],
    user_question: Optional[str] = None,
) -> None:
    """Stream the solution from deepseek-r1 token by token."""
    if user_question:
        prompt = (
            f"User question: {user_question}\n\n"
            f"Exam content:\n{extracted_question}"
        )
    else:
        prompt = (
            f"Solve this exam problem step by step:\n\n{extracted_question}\n\n"
            "Show all working. State the correct answer choice at the end."
        )

    payload = json.dumps({
        "model": MATH_MODEL,
        "system": _SOLVE_SYSTEM,
        "prompt": prompt,
        "stream": True,
        "keep_alive": -1,
        "options": {"num_gpu": 0, "temperature": 0.2, "num_predict": 1200},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        in_think = False
        think_shown = False
        buf = ""
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            for raw_line in resp:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                chunk = json.loads(raw_line)
                token = chunk.get("response", "")
                if token:
                    buf += token
                    # Suppress <think>...</think> chain-of-thought — show one status line
                    while True:
                        if not in_think:
                            start = buf.find("<think>")
                            if start == -1:
                                on_token(buf)
                                buf = ""
                                break
                            # emit text before <think>
                            if start > 0:
                                on_token(buf[:start])
                            buf = buf[start + len("<think>"):]
                            in_think = True
                            if not think_shown:
                                on_token("[Reasoning...]\n")
                                think_shown = True
                        else:
                            end = buf.find("</think>")
                            if end == -1:
                                buf = ""  # discard thinking tokens
                                break
                            buf = buf[end + len("</think>"):]
                            in_think = False
                if chunk.get("done", False):
                    if buf:
                        on_token(buf)
                    break
    except urllib.error.URLError as e:
        on_token(f"\n[Connection error: {e.reason}]")
    except Exception as e:
        on_token(f"\n[Solve error: {e}]")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stream_vision(
    image_path: Path,
    on_token: Callable[[str], None],
    user_question: Optional[str] = None,
) -> None:
    """
    Full two-phase pipeline:
      1. Vision model extracts question text from screenshot
      2. Math model solves and streams answer token by token
    Falls back to vision-only if deepseek-r1 is not available.
    """
    ocr_hint = _ocr_extract(image_path)

    on_token("[Reading screen...]\n\n")
    extracted = _extract_question(image_path, ocr_hint)

    if not _math_model_available():
        # Fallback: vision model does everything (old behaviour)
        on_token(f"[deepseek-r1 not found — vision-only mode]\n\n{extracted}")
        return

    on_token("[Solving...]\n\n")
    _stream_math_solve(extracted, on_token, user_question)


def ask_vision(image_path: Path, user_question: Optional[str] = None) -> str:
    """Non-streaming wrapper — returns the full answer as a single string."""
    parts: list[str] = []
    stream_vision(image_path, parts.append, user_question)
    return "".join(parts).strip()
