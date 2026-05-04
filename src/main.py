"""
Entry-point for the Monitor-AI Assistant.

Pipeline (tried in order):
  1. Vision  — screenshot → llava:7b via Ollama, streamed token-by-token (GPU)
  2. Fallback — screenshot → Tesseract OCR → Mistral local LLM
"""

import threading
import time
import traceback
from pathlib import Path

from .screen_capture import capture_screen
from .ocr_processor import get_ocr_diagnostics
from .ai_processor import query_llm
from .vision_llm import stream_vision, is_ollama_running
from .answer_window import AnswerWindow
from .config import CAPTURE_INTERVAL, DATA_DIR, LOCAL_MODEL_PATH


# ---------------------------------------------------------------------------
# Shared analysis helpers
# ---------------------------------------------------------------------------

def _analyse_fallback(img_path: Path, user_question: str | None = None) -> str:
    """OCR + local LLM path used when Ollama is not reachable."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import pytesseract as _pt
        _img = Image.open(str(img_path)).convert("L")
        _img = ImageEnhance.Contrast(_img).enhance(2.0)
        _img = _img.filter(ImageFilter.SHARPEN)
        raw_text = _pt.image_to_string(_img, config="--psm 6 -l eng").strip()
        if len(raw_text) < 10:
            raw_text = _pt.image_to_string(_img, config="--psm 11 -l eng").strip()
        del _img
    except Exception as ocr_err:
        raw_text = ""
        print(f"[WARN] OCR failed: {ocr_err}")

    if not raw_text or len(raw_text.strip()) < 5:
        diag = get_ocr_diagnostics()
        return (
            "Ollama is not running and OCR found no text.\n\n"
            "Start Ollama to use vision mode, or check Tesseract for OCR fallback.\n\n"
            f"--- OCR Diagnostics ---\n{diag}"
        )

    return query_llm(raw_text, user_question) or "(No answer generated.)"


def _run_with_stream(
    img_path: Path,
    answer_win: AnswerWindow,
    user_question: str | None = None,
) -> None:
    """
    Ollama online  → stream tokens live so the answer appears word-by-word.
    Ollama offline → OCR + local LLM, display when complete.
    """
    if is_ollama_running():
        answer_win.root.after(0, answer_win.start_stream)

        def _on_token(token: str):
            answer_win.root.after(0, answer_win.append_stream, token)

        stream_vision(img_path, _on_token, user_question)
    else:
        answer = _analyse_fallback(img_path, user_question)
        answer_win.root.after(0, answer_win.show_answer, answer)


# ---------------------------------------------------------------------------
# Background worker (auto-monitor mode)
# ---------------------------------------------------------------------------

def _worker_loop(
    stop_event: threading.Event,
    paused_event: threading.Event,
    answer_win: AnswerWindow,
) -> None:
    while not stop_event.is_set():
        if paused_event.is_set():
            time.sleep(0.5)
            continue

        try:
            img_path: Path = capture_screen()
            if paused_event.is_set():
                continue
            _run_with_stream(img_path, answer_win)
        except Exception:
            print("[ERROR] Exception in worker loop:")
            traceback.print_exc()

        time.sleep(CAPTURE_INTERVAL)


# Prevents concurrent Ask/Capture calls from racing each other.
_operation_lock = threading.Lock()


# ---------------------------------------------------------------------------
# User-triggered operations
# ---------------------------------------------------------------------------

def _force_capture(
    answer_win: AnswerWindow,
    paused_event: threading.Event,
) -> None:
    if not _operation_lock.acquire(blocking=False):
        answer_win.show_answer("Still processing — please wait.")
        return

    def _run():
        paused_event.set()
        answer_win.root.after(0, answer_win.set_paused, True)
        mode = "Vision/GPU" if is_ollama_running() else "OCR fallback"
        answer_win.root.after(0, answer_win.show_answer, f"Capturing... [{mode}]")
        try:
            img_path = capture_screen()
            _run_with_stream(img_path, answer_win)
        except Exception as e:
            answer_win.root.after(0, answer_win.show_answer, f"[Capture error: {e}]")
        finally:
            _operation_lock.release()

    threading.Thread(target=_run, daemon=True, name="Force-Capture").start()


def _ask_question(
    question: str,
    answer_win: AnswerWindow,
    paused_event: threading.Event,
) -> None:
    if not _operation_lock.acquire(blocking=False):
        answer_win.show_answer("Still processing — please wait.")
        return

    def _run():
        paused_event.set()
        answer_win.root.after(0, answer_win.set_paused, True)
        try:
            img_path = capture_screen()
            _run_with_stream(img_path, answer_win, user_question=question)
        except Exception as e:
            answer_win.root.after(0, answer_win.show_answer, f"[Error: {e}]")
        finally:
            _operation_lock.release()

    threading.Thread(target=_run, daemon=True, name="Ask-Thread").start()


# ---------------------------------------------------------------------------

def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    LOCAL_MODEL_PATH.parent.mkdir(exist_ok=True)

    stop_event = threading.Event()
    paused_event = threading.Event()
    paused_event.set()  # Start paused — user initiates first capture

    answer_win = AnswerWindow(
        paused_event=paused_event,
        on_ask=lambda q: _ask_question(q, answer_win, paused_event),
        on_capture=lambda: _force_capture(answer_win, paused_event),
        on_exit=lambda: (stop_event.set(), answer_win.root.destroy()),
    )

    worker = threading.Thread(
        target=_worker_loop,
        args=(stop_event, paused_event, answer_win),
        daemon=True,
        name="Capture-Worker",
    )
    worker.start()

    try:
        answer_win.start()
    finally:
        stop_event.set()
        worker.join(timeout=5)
