# ---- NEW FILE: src/ocr_processor.py ----
import cv2
import numpy as np
from pathlib import Path
from paddleocr import PaddleOCR
from .config import TEMP_SCREENSHOT_PATH

# -------------------------------------------------
# 1️⃣  OCR initialization (once, reuse for speed)
# -------------------------------------------------
# ``lang="en"`` – you can add more languages later, e.g. "en+fr"
ocr_engine = PaddleOCR(lang="en", 
                       use_angle_cls=True, 
                       rec=True,
                       det=True,
                       # Enable GPU if available (remove `cpu` flag)
                       enable_mkldnn=True,
                       # Smaller model for speed; change to "ch" for Chinese, etc.
                       # See PaddleOCR docs for more options.
                       )

# -------------------------------------------------
# 2️⃣  Image preprocessing helpers
# -------------------------------------------------
def enhance_for_ocr(image_path: Path) -> np.ndarray:
    """
    Apply a small pipeline that improves OCR accuracy:
        1. Convert to grayscale
        2. Apply CLAHE (contrast limited adaptive histogram equalization)
        3. Denoise with fastNlMeansD
        4. Optional binary threshold (helps for very dark backgrounds)
    Returns the processed ``numpy`` image ready for PaddleOCR.
    """
    img = cv2.imread(str(image_path))
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

# -------------------------------------------------
# 3️⃣  Core OCR function
# -------------------------------------------------
def extract_text_from_image(image_path: Path = TEMP_SCREENSHOT_PATH) -> str:
    """
    Run the full OCR pipeline:
        * read + enhance image
        * feed to PaddleOCR
        * post‑process raw results
    Returns a *single* string (lines separated by ``\\n``).
    """
    processed = enhance_for_ocr(image_path)

    # PaddleOCR expects a file path or a numpy array (BGR)
    # result is a list of pages, each page is a list of regions
    # each region is [[bbox_coords...], (text, confidence)]
    result = ocr_engine.ocr(processed, cls=True)

    lines = []
    # result is a list of pages
    if result:
        for page in result:
            # Each page is a list of regions
            for region in page:
                # Each region is [bbox, (text, confidence)]
                if len(region) >= 2:
                    text_confidence = region[1]  # (text, confidence)
                    txt = text_confidence[0].strip() if isinstance(text_confidence, (tuple, list)) else str(text_confidence).strip()
                    if txt:  # ignore empty strings
                        lines.append(txt)

    # Clean up whitespace, collapse multiple spaces
    cleaned = "\n".join(lines)
    return cleaned

# -------------------------------------------------
# 4️⃣  Helper for quick debugging
# -------------------------------------------------
def ocr_debug_save(image_path: Path, processed: np.ndarray):
    """Write the pre‑processed image to disk for visual inspection."""
    debug_path = image_path.with_name("debug_processed.png")
    cv2.imwrite(str(debug_path), processed)
    print(f"[OCR DEBUG] pre‑processed image saved to {debug_path}")
# -------------------------------------------------
