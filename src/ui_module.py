# ui_module.py
import tkinter as tk
from datetime import datetime

try:
    from mss import mss
except Exception:
    mss = None

class AnswerWindow:
    def __init__(self, monitor_index: int = 2, width_ratio: float = 0.6, height_ratio: float = 0.8):
        self.root = tk.Tk()
        self.root.title("AI Answers")

        # try to place on specified monitor (requires mss)
        if mss and monitor_index is not None:
            try:
                with mss() as sct:
                    monitors = sct.monitors
                    if 1 <= monitor_index < len(monitors):
                        m = monitors[monitor_index]
                        left, top, w, h = m["left"], m["top"], m["width"], m["height"]
                        win_w = int(w * width_ratio)
                        win_h = int(h * height_ratio)
                        pos_x = left + max(0, (w - win_w) // 2)
                        pos_y = top + max(0, (h - win_h) // 2)
                        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
            except Exception:
                pass

        # layout: left = Answer, right = Logs
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=2)

        # Answer frame
        ans_frame = tk.LabelFrame(self.root, text="Answer", bd=2, relief="groove")
        ans_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        ans_frame.rowconfigure(0, weight=1)
        ans_frame.columnconfigure(0, weight=1)

        self.answer_text = tk.Text(ans_frame, wrap="word", font=("Consolas", 12))
        self.answer_text.grid(row=0, column=0, sticky="nsew")
        ans_scroll = tk.Scrollbar(ans_frame, command=self.answer_text.yview)
        ans_scroll.grid(row=0, column=1, sticky="ns")
        self.answer_text.config(yscrollcommand=ans_scroll.set)
        self._set_readonly(self.answer_text)

        # Logs frame
        log_frame = tk.LabelFrame(self.root, text="Question Logs", bd=2, relief="groove")
        log_frame.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word", font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)
        self.log_text.config(state=tk.DISABLED)

    def _set_readonly(self, widget: tk.Text):
        widget.config(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.config(state=tk.DISABLED)

    def _safe_update(self, fn, *a, **k):
        # schedule GUI updates from other threads
        try:
            self.root.after(0, lambda: fn(*a, **k))
        except Exception:
            pass

    def set_answer(self, answer: str):
        def do():
            self.answer_text.config(state=tk.NORMAL)
            self.answer_text.delete("1.0", tk.END)
            self.answer_text.insert(tk.END, answer)
            self.answer_text.config(state=tk.DISABLED)
        self._safe_update(do)

    def append_log(self, text: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] {text}\n"
        def do():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self._safe_update(do)

    def run(self):
        self.root.mainloop()
