# ---- NEW FILE: src/main.py ----
import threading
import time
import traceback
from pathlib import Path

from .screen_capture import capture_screen
from .ocr_processor import extract_text_from_image
from .ai_processor import query_llm
from .answer_window import AnswerWindow
from .config import CAPTURE_INTERVAL

# -------------------------------------------------
# Helper to run the capture‑process‑display loop in a background thread
# -------------------------------------------------
def worker_loop(stop_event: threading.Event, answer_win: AnswerWindow):
    """
    Runs forever (or until ``stop_event`` is set):
        1. Capture screenshot
        2. OCR → raw text
        3. Ask LLM
        4. Update the Tk GUI
    """
    while not stop_event.is_set():
        try:
            # 1️⃣ Capture screen
            img_path: Path = capture_screen()

            # 2️⃣ OCR
            raw_text: str = extract_text_from_image(img_path)

            if not raw_text.strip():
                # No text detected – skip to next iteration
                print("[INFO] OCR yielded no text, retrying...")
                time.sleep(CAPTURE_INTERVAL)
                continue

            # 3️⃣ LLM query (no explicit user question right now)
            answer: str = query_llm(raw_text)

            # 4️⃣ Push answer to UI (must be done from Tk's thread via ``after``)
            answer_win.root.after(0, answer_win.show_answer, answer)

        except Exception as e:
            # Log the traceback but keep the loop alive
            print("[ERROR] Exception in worker loop:")
            traceback.print_exc()

        # Wait before the next capture
        time.sleep(CAPTURE_INTERVAL)

# -------------------------------------------------
def main():
    # 1️⃣ Create the UI (runs in the *main* thread)
    answer_win = AnswerWindow()

    # 2️⃣ Background thread for heavy work
    stop_event = threading.Event()
    worker = threading.Thread(
        target=worker_loop,
        args=(stop_event, answer_win),
        daemon=True,
        name="Capture-Worker",
    )
    worker.start()
    print("[INFO] Capture worker started. UI is now visible on monitor 2.")

    # 3️⃣ Start the Tkinter mainloop (blocks until window is closed)
    try:
        answer_win.start()
    finally:
        # When the UI closes, signal the worker to exit cleanly
        stop_event.set()
        worker.join(timeout=5)
        print("[INFO] Worker thread terminated. Bye!")

if __name__ == "__main__":
    main()
# -------------------------------------------------
