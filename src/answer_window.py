import threading
import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional

from .config import ANSWER_MONITOR_INDEX
from screeninfo import get_monitors


class AnswerWindow:
    def __init__(
        self,
        paused_event: threading.Event,
        on_ask: Callable[[str], None],
        on_capture: Callable[[], None],
        on_exit: Callable[[], None],
    ):
        self._paused_event = paused_event
        self._on_ask = on_ask
        self._on_capture = on_capture
        self._on_exit = on_exit

        self.root = tk.Tk()
        self.root.title("Monitor-AI Answer")
        self.root.configure(background="black")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        self._move_to_monitor(ANSWER_MONITOR_INDEX)
        self._build_ui()

    # ------------------------------------------------------------------
    def _move_to_monitor(self, monitor_idx: int):
        monitors = get_monitors()
        if monitor_idx >= len(monitors):
            raise IndexError(
                f"Answer monitor index {monitor_idx} out of range "
                f"({len(monitors)} monitors found)"
            )
        m = monitors[monitor_idx]
        self.root.geometry(f"{m.width}x{m.height}+{m.x}+{m.y}")

    # ------------------------------------------------------------------
    def _build_ui(self):
        # --- Answer display (fills all available space) ---
        self.text = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=("Consolas", 14),
            bg="black",
            fg="#00FF00",
            insertbackground="white",
            state=tk.DISABLED,
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # --- Bottom control bar ---
        bar = tk.Frame(self.root, bg="#111111", pady=6, padx=8)
        bar.pack(fill=tk.X, side=tk.BOTTOM)

        btn_style = dict(
            bg="#1a1a1a",
            fg="#00FF00",
            activebackground="#003300",
            activeforeground="#00FF00",
            relief=tk.FLAT,
            font=("Consolas", 12),
            padx=12,
            pady=4,
            cursor="hand2",
        )

        # Prompt entry
        self._prompt_var = tk.StringVar()
        entry = tk.Entry(
            bar,
            textvariable=self._prompt_var,
            bg="#0d0d0d",
            fg="#00FF00",
            insertbackground="#00FF00",
            font=("Consolas", 13),
            relief=tk.FLAT,
            bd=4,
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        entry.bind("<Return>", lambda _: self._submit_question())

        # Ask button
        tk.Button(bar, text="Ask", command=self._submit_question, **btn_style).pack(side=tk.LEFT, padx=(0, 8))

        # Capture button
        tk.Button(bar, text="Capture", command=self._on_capture, **btn_style).pack(side=tk.LEFT, padx=(0, 16))

        # Pause / Resume toggle — label reflects actual initial state
        self._pause_btn_text = tk.StringVar(
            value="Resume" if self._paused_event.is_set() else "Pause"
        )
        tk.Button(
            bar,
            textvariable=self._pause_btn_text,
            command=self._toggle_pause,
            **btn_style,
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Exit button
        tk.Button(bar, text="Exit", command=self._exit, fg="#FF4444", bg="#1a1a1a",
                  activebackground="#330000", activeforeground="#FF4444",
                  relief=tk.FLAT, font=("Consolas", 12), padx=12, pady=4,
                  cursor="hand2").pack(side=tk.LEFT)

    # ------------------------------------------------------------------
    def _submit_question(self):
        question = self._prompt_var.get().strip()
        if not question:
            return
        self._prompt_var.set("")
        self.show_answer(f"[Asking] {question}\n\nProcessing...")
        self._on_ask(question)

    def set_paused(self, paused: bool):
        """Sync the pause button label with an externally set paused state."""
        self._pause_btn_text.set("Resume" if paused else "Pause")

    def _toggle_pause(self):
        if self._paused_event.is_set():
            self._paused_event.clear()
            self._pause_btn_text.set("Pause")
        else:
            self._paused_event.set()
            self._pause_btn_text.set("Resume")

    def _exit(self):
        self._on_exit()

    # ------------------------------------------------------------------
    def show_answer(self, answer: str):
        def _update():
            self.text.configure(state=tk.NORMAL)
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, answer)
            self.text.configure(state=tk.DISABLED)
            self.text.see(tk.END)
        self.root.after(0, _update)

    def start_stream(self):
        """Clear display and prepare for incoming stream tokens."""
        self.text.configure(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.configure(state=tk.DISABLED)

    def append_stream(self, token: str):
        """Append a single streamed token to the display."""
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, token)
        self.text.configure(state=tk.DISABLED)
        self.text.see(tk.END)

    def start(self):
        self.show_answer(
            "Monitor-AI ready.\n\n"
            "  Capture  — read current screen and analyse it\n"
            "  Ask      — type a question, then press Ask or Enter\n"
            "  Resume   — start auto-monitoring every 30 seconds\n"
            "  Exit     — close the application"
        )
        self.root.mainloop()
