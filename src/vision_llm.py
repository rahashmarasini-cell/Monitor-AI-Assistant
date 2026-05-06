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
MATH_MODEL    = "qwen2.5:7b"     # solves the extracted problem (strong math, no CoT)
_FALLBACK_VISION = "llava:7b"
TIMEOUT = 180  # GPU inference; covers model swap + reasoning + answer

_OLLAMA_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"

_EXTRACT_SYSTEM = (
    "You are a precise text extractor for exam screenshots. "
    "Your ONLY job is to read the screen and output the question and answer choices verbatim. "
    "Do NOT solve anything. Do NOT explain. Output the text exactly as it appears."
)

_SOLVE_SYSTEM = (
    "You are a precise math tutor. Solve the multiple-choice problem in as few steps as possible.\n"
    "Be DIRECT — do not wander. Pick the right method on the first try.\n"
    "\n"
    "QUADRATIC VERTEX (y = ax² + bx + c):\n"
    "  Use ONLY the formula h = -b/(2a), k = a·h² + b·h + c.\n"
    "  Read a, b, c straight from the original equation. Do not divide or factor first.\n"
    "  Direction: a > 0 opens upward, a < 0 opens downward.\n"
    "  Example: y = 3x² - 18x - 10  →  a=3, b=-18, c=-10\n"
    "    h = -(-18)/(2·3) = 18/6 = 3\n"
    "    k = 3(3²) + (-18)(3) + (-10) = 27 - 54 - 10 = -37\n"
    "    Vertex (3,-37), opens upward.\n"
    "\n"
    "COMPLEX NUMBER PRODUCT (a+bi)(c+di):\n"
    "  Expand all four FOIL terms, then substitute i² = -1.\n"
    "  Result: (ac - bd) + (ad + bc)i\n"
    "\n"
    "COMPLEX NUMBER SUM/DIFFERENCE:\n"
    "  Add real parts and imaginary parts separately. Keep all signs.\n"
    "\n"
    "POWERS OF i:\n"
    "  i² = -1, i³ = -i, i⁴ = 1, then cycle. For i^n, compute n mod 4.\n"
    "\n"
    "End every response with a final line: Answer: X.) [value]\n"
    "Your final answer MUST exactly match one of the listed choices a/b/c/d."
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
    # BUT only when the line is a math expression — NOT a coordinate tuple
    # like "(3,-37)". Coordinate tuples contain commas; math expressions don't.
    def _fix_trailing(line: str) -> str:
        if ',' in line:
            return line
        return re.sub(r'(\d)[)/](\s*)$', r'\1i\2', line)
    text = '\n'.join(_fix_trailing(l) for l in text.splitlines())
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
        "Transcribe this exam screenshot exactly. Output:\n"
        "- The question text (verbatim, including ALL math symbols)\n"
        "- Each answer choice labeled a/b/c/d (verbatim)\n"
        "\n"
        "Critical: preserve every character precisely:\n"
        "  • superscripts (²,³): write as x^2, x^3 (NEVER as x?, x2 alone, or drop them)\n"
        "  • signs: every + and - must match the image exactly\n"
        "  • the symbol i in complex numbers (NOT capital I, NOT 1)\n"
        "  • parentheses and their contents word-for-word\n"
        "\n"
        "Do NOT solve. Do NOT explain. Output only the transcription."
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
    ocr_text: str = "",
) -> None:
    """Stream the solution from the math model token by token."""
    sources_block = (
        f"--- VISION READING ---\n{extracted_question}\n"
        f"--- OCR READING ---\n{ocr_text}\n--- END ---"
        if ocr_text else extracted_question
    )

    if user_question:
        prompt = (
            f"User question: {user_question}\n\n"
            f"Exam content (two sources of the same screenshot — cross-check them):\n"
            f"{sources_block}"
        )
    else:
        prompt = (
            f"Solve this exam problem.\n\n"
            f"Two sources transcribe the same screenshot — cross-check character-by-character "
            f"when they disagree (especially superscripts ², signs +/-, the symbol i, "
            f"and stacked fractions which OCR may flatten into two adjacent numbers):\n\n"
            f"{sources_block}\n\n"
            f"Process:\n"
            f"  1. Solve the problem and write your computed answer in canonical form.\n"
            f"  2. Compare your answer to EACH choice. Watch for: ² vs ?, +k vs -k, "
            f"(x-h) vs (x+h), and stacked fractions like a/b rendered as 'a b' in OCR.\n"
            f"  3. Pick the choice whose meaning matches your computed answer.\n"
            f"  4. Final line MUST be: 'Answer: X.) <your own canonical form>' "
            f"— write YOUR computed value, not a copy from the (possibly garbled) choice text.\n"
            f"\n"
            f"Use plain ASCII math (e.g. 6/13, x^2, -17/13 i). Do NOT use LaTeX \\(...\\) or \\[...\\]."
        )

    payload = json.dumps({
        "model": MATH_MODEL,
        "system": _SOLVE_SYSTEM,
        "prompt": prompt,
        "stream": True,
        "keep_alive": -1,
        # 8GB VRAM constraint: full GPU offload spills to shared memory (10x slower).
        # 28 layers + 4096 ctx fits comfortably under 7GB total.
        "options": {
            "num_gpu": 28,
            "num_ctx": 4096,
            "temperature": 0.2,
            "num_predict": 800,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # Ollama splits deepseek-r1 output into two streams:
        #   chunk["thinking"] — chain-of-thought (long, internal)
        #   chunk["response"] — the final answer (what the user wants)
        # We show a single "[Reasoning...]" line + dots while thinking arrives,
        # then stream the real response token-by-token.
        thinking_announced = False
        thinking_chars = 0
        response_started = False
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            for raw_line in resp:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                chunk = json.loads(raw_line)
                think_tok = chunk.get("thinking", "") or ""
                resp_tok  = chunk.get("response", "") or ""

                if think_tok and not response_started:
                    if not thinking_announced:
                        on_token("[Reasoning")
                        thinking_announced = True
                    thinking_chars += len(think_tok)
                    # one dot every ~80 thinking chars as a heartbeat
                    while thinking_chars >= 80:
                        on_token(".")
                        thinking_chars -= 80

                if resp_tok:
                    if thinking_announced and not response_started:
                        on_token("]\n\n")
                    response_started = True
                    on_token(resp_tok)

                if chunk.get("done", False):
                    if thinking_announced and not response_started:
                        on_token("]\n\n[No answer produced — model exhausted token budget on reasoning. Try again.]")
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

    # Brief pause to let Ollama finish unloading the vision model (frees VRAM)
    time.sleep(1.5)
    on_token("[Solving on GPU...]\n\n")
    _stream_math_solve(extracted, on_token, user_question, ocr_hint)


def ask_vision(image_path: Path, user_question: Optional[str] = None) -> str:
    """Non-streaming wrapper — returns the full answer as a single string."""
    parts: list[str] = []
    stream_vision(image_path, parts.append, user_question)
    return "".join(parts).strip()
