# ---- NEW FILE: src/answer_window.py ----
import tkinter as tk
from tkinter import scrolledtext
from .config import ANSWER_MONITOR_INDEX
from screeninfo import get_monitors

class AnswerWindow:
    """
    A thin, border‑less Tkinter window that lives on the *second* monitor.
    It auto‑scrolls to show the latest answer.
    """
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Monitor‑AI Answer")
        self.root.configure(background="black")
        self.root.overrideredirect(True)   # No window decorations

        # Place window on the target monitor
        self._move_to_monitor(ANSWER_MONITOR_INDEX)

        # Create a read‑only scrolled text widget
        self.text = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD,
            font=("Consolas", 14),
            bg="black",
            fg="#00FF00",   # green-on‑black console feel
            insertbackground="white",
            state=tk.DISABLED,
        )
        self.text.pack(fill=tk.BOTH, expand=True)

    # -------------------------------------------------
    def _move_to_monitor(self, monitor_idx: int):
        """
        Locate the requested monitor using ``screeninfo`` and move the Tk
        window there, filling the whole screen.
        """
        monitors = get_monitors()
        if monitor_idx >= len(monitors):
            raise IndexError(f"Answer monitor index {monitor_idx} out of range "
                             f"({len(monitors)} monitors found)")

        m = monitors[monitor_idx]
        self.root.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")

    # -------------------------------------------------
    def show_answer(self, answer: str):
        """
        Replace current content with the new answer (clears previous).
        """
        self.text.configure(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, answer)
        self.text.configure(state=tk.DISABLED)
        self.text.see(tk.END)   # scroll to bottom

    # -------------------------------------------------
    def start(self):
        """
        Kick‑off Tk's main loop – called in the main thread.
        """
        self.root.mainloop()
# -------------------------------------------------
