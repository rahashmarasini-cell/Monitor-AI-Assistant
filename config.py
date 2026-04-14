# ---- NEW FILE: src/config.py ----
import os
from pathlib import Path

# -------------------------------------------------
# USER SETTINGS – adjust to your hardware
# -------------------------------------------------
# Index of the monitor you want to capture from (0‑based)
CAPTURE_MONITOR_INDEX = 1

# Index of the monitor where the answer window will appear
ANSWER_MONITOR_INDEX = 2

# Capture interval in seconds
CAPTURE_INTERVAL = 2.0

# OpenAI (or compatible) model name
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

# Prompt template – you can fine‑tune this later
PROMPT_TEMPLATE = """You are a helpful assistant. 
Given the following extracted text from a screen, answer the user's question (if any) or summarize the content.

--- BEGIN TEXT ---
{extracted_text}
--- END TEXT ---

If there is a clear question in the text, answer it concisely. 
Otherwise, provide a short, bullet‑point summary."""
# -------------------------------------------------
# INTERNAL CONSTANTS (not for user editing)
# -------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Where to store temporary screenshots
TEMP_SCREENSHOT_PATH = DATA_DIR / "last_capture.png"
# -------------------------------------------------
