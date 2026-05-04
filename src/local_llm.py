"""
Local LLM driver using llama-cpp-python.

The model runs in an isolated subprocess so that a C-level crash inside
llama_cpp (OOM, access violation) kills only the worker process — the UI
stays alive and shows an error message instead of disappearing.

The subprocess is spawned once at startup, loads the model, then handles
queries from a queue indefinitely.
"""

import multiprocessing
import platform
from pathlib import Path

from .config import (
    LOCAL_MODEL_PATH,
    LOCAL_N_CTX,
    LOCAL_N_BATCH,
    LOCAL_TEMPERATURE,
)

# ---------------------------------------------------------------------------
# Worker function — runs in the child process.
# Must be at module level so multiprocessing can pickle it on Windows.
# ---------------------------------------------------------------------------

def _llm_worker(model_path: str, n_ctx: int, n_batch: int, temperature: float,
                in_q: multiprocessing.Queue, out_q: multiprocessing.Queue) -> None:
    """
    Loads the GGUF model once, then loops reading prompts from in_q and
    writing completions to out_q.  Sentinel None in in_q signals shutdown.
    """
    try:
        from llama_cpp import Llama
        model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_gpu_layers=0,
            verbose=False,
        )
    except Exception as e:
        out_q.put(f"__ERROR__:{e}")
        return

    out_q.put("__READY__")

    while True:
        item = in_q.get()
        if item is None:
            break
        prompt, max_tokens = item
        try:
            result = model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=1.0,
                repeat_penalty=1.1,
                stop=["[INST]", "</s>"],
            )
            text = result["choices"][0]["text"].strip()
            out_q.put(text)
        except Exception as e:
            out_q.put(f"[LLM error: {e}]")


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------

class LocalLLM:
    """Spawns a worker subprocess that owns the model. Crash-safe for the UI."""

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("LocalLLM is currently Windows-only.")

        if not LOCAL_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {LOCAL_MODEL_PATH}. "
                "Place the GGUF model file in the correct directory."
            )

        self._in_q: multiprocessing.Queue = multiprocessing.Queue()
        self._out_q: multiprocessing.Queue = multiprocessing.Queue()

        self._proc = multiprocessing.Process(
            target=_llm_worker,
            args=(
                str(LOCAL_MODEL_PATH),
                LOCAL_N_CTX,
                LOCAL_N_BATCH,
                LOCAL_TEMPERATURE,
                self._in_q,
                self._out_q,
            ),
            daemon=True,
            name="LLM-Worker",
        )
        self._proc.start()

        # Block until the model signals it is ready (or errors out).
        try:
            msg = self._out_q.get(timeout=120)
        except Exception:
            self._proc.kill()
            raise RuntimeError("LLM worker did not become ready within 2 minutes.")

        if isinstance(msg, str) and msg.startswith("__ERROR__"):
            self._proc.kill()
            raise RuntimeError(f"LLM worker failed to load model: {msg[9:]}")

    # ------------------------------------------------------------------
    def generate(self, prompt: str, max_tokens: int = 350) -> str:
        if not self._proc.is_alive():
            return "[LLM process is no longer running — please restart the application.]"

        self._in_q.put((prompt, max_tokens))

        try:
            return self._out_q.get(timeout=180)
        except Exception:
            return "[LLM timed out — the query took longer than 3 minutes.]"
