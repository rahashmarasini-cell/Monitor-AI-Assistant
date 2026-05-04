import os
import sys
from pathlib import Path

# Resolve the root directory correctly whether running from source or as a
# PyInstaller exe. In PyInstaller 6.x one-dir mode, sys._MEIPASS points to
# the _internal/ folder; the exe and all user data live one level above it.
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS).parent
else:
    BASE_DIR = Path(__file__).parent.parent

# -------------------------------------------------
# USER SETTINGS
# -------------------------------------------------
CAPTURE_MONITOR_INDEX = 0
ANSWER_MONITOR_INDEX = 1
CAPTURE_INTERVAL = 30.0

# -------------------------------------------------
# PROMPT TEMPLATE FOR LLM
# -------------------------------------------------
PROMPT_TEMPLATE = """<s>[INST] You are an expert exam and homework assistant. The text below was captured from a screen using OCR and may contain browser tabs, URLs, and other noise — ignore those.

Your job:
1. Find the actual question, problem, or exercise in the text.
2. Solve it fully, showing your reasoning step by step.
3. If multiple choice, state which option is correct and explain why.
4. If it is a math or logic problem, show your working.
5. Give a clear, direct final answer.

Screen text:
{extracted_text}

Answer: [/INST]"""

# -------------------------------------------------
# LOCAL LLM SETTINGS
# -------------------------------------------------
DEFAULT_MODEL_PATH = BASE_DIR / "MONITOR-AI-ASSISTANT" / "models" / "mistral-7b-v0.1.Q4_0.gguf"
LOCAL_MODEL_PATH = Path(os.getenv("LOCAL_MODEL_PATH", DEFAULT_MODEL_PATH))

LOCAL_N_CTX = int(os.getenv("LOCAL_N_CTX", 2048))
LOCAL_N_BATCH = int(os.getenv("LOCAL_N_BATCH", 512))
LOCAL_TEMPERATURE = float(os.getenv("LOCAL_TEMPERATURE", 0.2))

# -------------------------------------------------
# TESSERACT CONFIGURATION
# -------------------------------------------------
TESSERACT_CMD_PATH = Path(os.getenv(
    "TESSERACT_CMD",
    "C:/Program Files/Tesseract-OCR/tesseract.exe"
))
TESSERACT_DATA_DIR = Path(os.getenv(
    "TESSDATA_PREFIX",
    str(TESSERACT_CMD_PATH.parent / "tessdata")
))
TESSERACT_LANGUAGES = os.getenv("TESSERACT_LANGUAGES", "eng")

# -------------------------------------------------
# INTERNAL PATHS
# -------------------------------------------------
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

TEMP_SCREENSHOT_PATH = DATA_DIR / "last_capture.png"

OCR_OUTPUT_DIR = DATA_DIR / "ocr_output"
OCR_OUTPUT_DIR.mkdir(exist_ok=True)

TESSERACT_INSTALLED = False
