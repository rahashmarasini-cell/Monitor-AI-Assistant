# ---- NEW FILE: src/screen_capture.py ----
import mss
import mss.tools
from pathlib import Path
from .config import CAPTURE_MONITOR_INDEX, TEMP_SCREENSHOT_PATH

def _get_monitor_geometry():
    """Return the geometry dict required by mss for the chosen monitor."""
    with mss.mss() as sct:
        monitors = sct.monitors  # monitors[0] = all monitors, monitors[1] = primary, etc.
        if CAPTURE_MONITOR_INDEX + 1 >= len(monitors):
            raise IndexError(f"Monitor index {CAPTURE_MONITOR_INDEX} out of range. "
                             f"Detected {len(monitors)-1} monitor(s).")
        return monitors[CAPTURE_MONITOR_INDEX + 1]

def capture_screen() -> Path:
    """
    Grab a screenshot from the configured monitor and write it to
    ``TEMP_SCREENSHOT_PATH``. Returns the Path object for downstream use.
    """
    monitor = _get_monitor_geometry()
    with mss.mss() as sct:
        img = sct.grab(monitor)               # raw pixel data
        # Save as PNG (lossless, easy for OCR)
        mss.tools.to_png(img.rgb, img.size, output=str(TEMP_SCREENSHOT_PATH))
    return TEMP_SCREENSHOT_PATH
# -------------------------------------------------
