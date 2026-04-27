# ---- UPDATED FILE: src/config.py ----
import os
from pathlib import Path

# -------------------------------------------------
# USER SETTINGS – adjust to your hardware
# -------------------------------------------------
# Index of the monitor you want to capture from (0‑based)
CAPTURE_MONITOR_INDEX = 0

# Index of the monitor where the answer window will appear
ANSWER_MONITOR_INDEX = 1

# Capture interval in seconds
CAPTURE_INTERVAL = 2.0

# -------------------------------------------------
# PROMPT TEMPLATE FOR LLM
# -------------------------------------------------
# The template is used in ai_processor.py to build the full prompt
# {extracted_text} will be replaced with OCR-extracted text from the screen
PROMPT_TEMPLATE = """You are a helpful assistant. Below is text extracted from a screen capture.
If the text contains a question, answer it clearly and concisely.
If it contains information to analyze or summarize, do that instead.
Keep your response focused and under 500 words.

Screen text:
{extracted_text}

Answer:"""

# -------------------------------------------------
# LOCAL LLM SETTINGS (no OpenAI API)
# -------------------------------------------------
# Path to a GGML‑quantised model (e.g. Mistral‑7B‑Instruct Q4_0)
# You can set the env var LOCAL_MODEL_PATH or edit the default below.
DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "MONITOR-AI-ASSISTANT" / "models" / "mistral-7b-v0.1.Q4_0.gguf"
LOCAL_MODEL_PATH = Path(os.getenv("LOCAL_MODEL_PATH", DEFAULT_MODEL_PATH))

# Inference parameters – feel free to tweak
LOCAL_N_CTX = int(os.getenv("LOCAL_N_CTX", 2048))       # context size
LOCAL_N_BATCH = int(os.getenv("LOCAL_N_BATCH", 512))   # batch size for prompt processing
LOCAL_TEMPERATURE = float(os.getenv("LOCAL_TEMPERATURE", 0.2))

# -------------------------------------------------
# INTERNAL CONSTANTS (not for user editing)
# -------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Where to store temporary screenshots
TEMP_SCREENSHOT_PATH = DATA_DIR / "last_capture.png"
# -------------------------------------------------
