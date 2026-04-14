# ---- NEW FILE: src/local_llm.py ----
"""
Local LLM driver using llama-cpp-python.

The driver loads the GGML model once (on first use) and exposes a simple
``generate(prompt: str) -> str`` method that returns the model’s completion.

It is deliberately lightweight – only the parameters we need for
the Monitor‑AI assistant are exposed via ``src/config.py``.
"""

import os
import platform
from pathlib import Path
from typing import Optional

from .config import (
    LOCAL_MODEL_PATH,
    LOCAL_N_CTX,
    LOCAL_N_BATCH,
    LOCAL_TEMPERATURE,
)

class LocalLLM:
    """Thin wrapper around llama_cpp.Llama that hides the library specifics."""
    def __init__(self) -> None:
        # -----------------------------------------------------------------
        # Basic sanity checks – we only support Windows in this repo (as requested)
        # -----------------------------------------------------------------
        if platform.system() != "Windows":
            raise RuntimeError("Local LLM wrapper is currently targeted at Windows only.")

        model_path = Path(LOCAL_MODEL_PATH).expanduser().resolve()
        if not model_path.is_file():
            raise FileNotFoundError(
                f"GGML model not found at {model_path!s}. "
                "Download a quantised model and set LOCAL_MODEL_PATH accordingly."
            )

        try:
            # Import is inside the try so that the error message is clearer for users.
            from llama_cpp import Llama
        except Exception as exc:
            raise ImportError(
                "Failed to import llama_cpp. Make sure 'llama-cpp-python' is installed. "
                "On Windows you need the compiled wheel (pip install llama-cpp-python)."
            ) from exc

        # -------------------------------------------------------------
        # Model initialisation – we keep it simple: CPU‑only for maximum compatibility.
        # You can experiment with n_gpu_layers>0 if you built a DirectML wheel.
        # -------------------------------------------------------------
        self._model = Llama(
            model_path=str(model_path),
            n_ctx=LOCAL_N_CTX,
            n_batch=LOCAL_N_BATCH,
            n_gpu_layers=0,               # 0 = CPU only; change if you have a GPU build.
            verbose=False,
        )

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Run the model on *prompt* and return the generated text.

        Parameters
        ----------
        prompt: str
            Full prompt (including any system instructions) – already formatted.
        max_tokens: int, optional
            Upper bound on the number of tokens the model may emit.

        Returns
        -------
        str
            The model’s completion with leading/trailing whitespace stripped.
        """
        # ``self._model`` returns a dict with a ``choices`` list.
        # Example: {"choices": [{"text": " answer"}], "usage": {...}}
        output = self._model(
            prompt,
            max_tokens=max_tokens,
            temperature=LOCAL_TEMPERATURE,
            # The following arguments are optional but keep defaults for simplicity.
            top_p=1.0,
            repeat_penalty=1.0,
            stop=None,
        )
        # Guard against unexpected shape – raise a clear error if needed.
        try:
            text = output["choices"][0]["text"]
        except Exception as exc:
            raise RuntimeError(f"Unexpected LLM output format: {output}") from exc

        return text.strip()
# -------------------------------------------------
