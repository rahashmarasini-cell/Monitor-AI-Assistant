# ---- UPDATED FILE: src/main.py ----
"""
Entry‑point for the Monitor‑AI Assistant.

The program follows the classic producer‑consumer pattern:
    * a background thread captures the screen, runs OCR, and asks the LLM;
    * the UI thread (Tkinter) displays the answer on the second monitor.
"""

import threading
import time
import traceback
from pathlib import Path

from .screen_capture import capture_screen
from .ocr_processor import extract_text_from_image
from .ai_processor import query_llm
from .answer_window import AnswerWindow
from .config import CAPTURE_INTERVAL

def _worker_loop(stop_event: threading.Event, answer_win: AnswerWindow) -> None:
    """Background loop – capture → OCR → LLM → update UI."""
    while not stop_event.is_set():
        try:
            # 1️⃣ Capture
            img_path: Path = capture_screen()

            # 2️⃣ OCR
            raw_text: str = extract_text_from_image(img_path)

            if not raw_text.strip():
                # No legible text – skip this round.
                print("[INFO] No OCR text detected, trying again...")
                time.sleep(CAPTURE_INTERVAL)
                continue

            # 3️⃣ Ask the local model
            answer: str = query_llm(raw_text)

            # 4️⃣ Push answer to the UI (must happen on the Tk thread)
            answer_win.root.after(0, answer_win.show_answer, answer)

        except Exception as exc:
            print("[ERROR] Exception inside worker loop:")
            traceback.print_exc()

        # Wait before the next capture cycle.
        time.sleep(CAPTURE_INTERVAL)

def main() -> None:
    """
    Initialise the UI, start the background worker, and run the Tkinter
    main‑loop. When the window is closed we signal the thread to exit cleanly.
    """
    # UI lives in the *main* thread.
    answer_win = AnswerWindow()

    # Background worker (daemon → won't block interpreter exit)
    stop_event = threading.Event()
    worker = threading.Thread(
        target=_worker_loop,
        args=(stop_event, answer_win),
        daemon=True,
        name="Capture‑Worker",
    )
    worker.start()
    print("[INFO] Capture worker started – answer window on monitor", answer_win.root.winfo_screen())

    try:
        answer_win.start()               # blocks until the window is closed
    finally:
        # Graceful shutdown
        stop_event.set()
        worker.join(timeout=5)
        print("[INFO] Worker thread stopped. Bye!")

if __name__ == "__main__":
    main()
# -------------------------------------------------
