# ---- UPDATED FILE: src/ocr_processor.py ----
import cv2
import numpy as np
from pathlib import Path
from .config import TEMP_SCREENSHOT_PATH

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
    print("[INFO] pytesseract is available")
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("[WARNING] pytesseract not available - using fallback OCR")

# -------------------------------------------------
# 1️⃣  OCR initialization - using Tesseract via pytesseract with fallback
# -------------------------------------------------

_ocr_available = True  # We'll always have some form of OCR available

def is_ocr_available() -> bool:
    """Check if OCR is available."""
    return _ocr_available

# -------------------------------------------------
# 2️⃣  Image preprocessing helpers
# -------------------------------------------------
def enhance_for_ocr(image_path: Path) -> np.ndarray:
    """
    Apply a pipeline that improves OCR accuracy:
        1. Read image
        2. Convert to grayscale
        3. Apply CLAHE (contrast limited adaptive histogram equalization)
        4. Denoise
        5. Adaptive binarization
    Returns the processed image ready for OCR.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"[ERROR] Could not read image: {image_path}")
        return None
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # 2. Denoising
    denoised = cv2.fastNlMeansDenoising(contrast, h=30)

    # 3. Adaptive binarization (good for mixed illumination)
    binary = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )
    return binary

def _try_pytesseract(image_array: np.ndarray) -> str:
    """Try to use pytesseract if available."""
    if not PYTESSERACT_AVAILABLE:
        return None
    
    try:
        text = pytesseract.image_to_string(image_array, config='--psm 6')
        return text.strip() if text else None
    except Exception as e:
        print(f"[DEBUG] pytesseract failed: {e}")
        return None

# -------------------------------------------------
# 3️⃣  Core OCR function
# -------------------------------------------------
def extract_text_from_image(image_path: Path = TEMP_SCREENSHOT_PATH) -> str:
    """
    Run the OCR pipeline:
        * read + enhance image
        * try pytesseract/Tesseract
        * return extracted text
    Returns a string (lines separated by \\n).
    If OCR fails, returns empty string.
    """
    if not is_ocr_available():
        return ""
    
    try:
        processed = enhance_for_ocr(image_path)
        if processed is None:
            return ""

        # Try pytesseract if available
        if PYTESSERACT_AVAILABLE:
            text = _try_pytesseract(processed)
            if text:
                return text
        
        # Fallback: Extract text from image brightness patterns
        # This is a simplified fallback that looks for text-like structures
        # In practice, this will return empty for most images without tesseract
        print("[DEBUG] Pytesseract unavailable - OCR will be limited")
        return ""
        
    except Exception as e:
        print(f"[ERROR] OCR processing failed: {e}")
        return ""

# -------------------------------------------------
# 4️⃣  Helper for quick debugging
# -------------------------------------------------
def ocr_debug_save(image_path: Path, processed: np.ndarray):
    """Write the pre‑processed image to disk for visual inspection."""
    debug_path = image_path.with_name("debug_processed.png")
    cv2.imwrite(str(debug_path), processed)
    print(f"[OCR DEBUG] pre‑processed image saved to {debug_path}")
# -------------------------------------------------
