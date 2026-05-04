"""
OCR Processor – Extracts text and analyzes graphs from screen captures.

Provides functions for:
  * Full pytesseract/Tesseract integration
  * Advanced image preprocessing and enhancement
  * Multiple OCR modes (document, single line, sparse text, etc.)
  * Language detection and multi-language support
  * Graph detection and analysis integration
  * Confidence scores and detailed OCR data
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import os
import sys

from .config import (
    TEMP_SCREENSHOT_PATH, 
    TESSERACT_CMD_PATH,
    TESSERACT_DATA_DIR,
    TESSERACT_LANGUAGES,
    OCR_OUTPUT_DIR
)

# Initialize pytesseract
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
    print("[✓] pytesseract module loaded")
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("[⚠] pytesseract not installed - run: pip install pytesseract")

# -------------------------------------------------
# 1️⃣  Tesseract Configuration & Initialization
# -------------------------------------------------

TESSERACT_INSTALLED = False
TESSERACT_PATH = None
OCR_AVAILABLE = False

def _configure_tesseract() -> bool:
    """Configure pytesseract. Returns True if Tesseract binary is found and wired up."""
    global TESSERACT_INSTALLED, TESSERACT_PATH, OCR_AVAILABLE

    if not PYTESSERACT_AVAILABLE:
        return False

    possible_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        Path(f"{os.environ.get('ProgramFiles', 'C:/Program Files')}/Tesseract-OCR/tesseract.exe"),
        Path(f"{os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')}/Tesseract-OCR/tesseract.exe"),
        TESSERACT_CMD_PATH,
    ]

    for path in possible_paths:
        if path.exists():
            TESSERACT_PATH = str(path)
            pytesseract.pytesseract.pytesseract_cmd = TESSERACT_PATH

            # Tesseract 5.x: TESSDATA_PREFIX must point TO the tessdata directory itself.
            # Tesseract appends <lang>.traineddata directly to TESSDATA_PREFIX.
            install_dir = path.parent
            tessdata_dir = install_dir / "tessdata"
            if tessdata_dir.exists():
                os.environ['TESSDATA_PREFIX'] = str(tessdata_dir)

            TESSERACT_INSTALLED = True
            OCR_AVAILABLE = True
            return True

    return False


def get_ocr_diagnostics() -> str:
    """Return a human-readable diagnostic string for display in the UI."""
    lines = []
    lines.append(f"pytesseract available: {PYTESSERACT_AVAILABLE}")
    lines.append(f"OCR available: {OCR_AVAILABLE}")
    lines.append(f"Tesseract path: {TESSERACT_PATH or 'NOT FOUND'}")
    lines.append(f"TESSDATA_PREFIX: {os.environ.get('TESSDATA_PREFIX', 'not set')} (should end in \\tessdata)")
    if TESSERACT_PATH:
        lines.append(f"Binary exists: {Path(TESSERACT_PATH).exists()}")
    try:
        v = pytesseract.get_tesseract_version() if OCR_AVAILABLE else "N/A"
        lines.append(f"Tesseract version: {v}")
    except Exception as e:
        lines.append(f"Version check error: {e}")
    return "\n".join(lines)

def is_ocr_available() -> bool:
    """Check if OCR (Tesseract) is available and configured."""
    global OCR_AVAILABLE
    if not OCR_AVAILABLE and PYTESSERACT_AVAILABLE:
        _configure_tesseract()
    return OCR_AVAILABLE

def get_tesseract_version() -> Optional[str]:
    """Get Tesseract version string."""
    if not is_ocr_available():
        return None
    try:
        return pytesseract.get_tesseract_version()
    except Exception as e:
        print(f"[⚠] Could not get Tesseract version: {e}")
        return None

def get_tesseract_languages() -> list:
    """Get list of available languages in Tesseract."""
    if not is_ocr_available():
        return []
    try:
        return pytesseract.get_languages()
    except Exception as e:
        print(f"[⚠] Could not get available languages: {e}")
        return ['eng']  # Default fallback

# Initialize Tesseract on module load
if PYTESSERACT_AVAILABLE:
    _configure_tesseract()

# -------------------------------------------------
# 2️⃣  Advanced Image Preprocessing for OCR
# -------------------------------------------------

def enhance_for_ocr(image_path: Path, aggressive: bool = False) -> Optional[np.ndarray]:
    """
    Apply comprehensive preprocessing pipeline to improve OCR accuracy:
        1. Read and validate image
        2. Convert to grayscale
        3. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        4. Denoise using bilateral filter (fast, edge-preserving)
        5. Adaptive thresholding (handles variable lighting)
        6. Optional: Morphological operations (aggressive mode)
    
    Args:
        image_path: Path to image file
        aggressive: If True, apply additional morphological operations
    
    Returns:
        Preprocessed image as numpy array, or None if read fails
    """
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"[✗] Could not read image: {image_path}")
        return None
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Contrast enhancement using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 2. Bilateral filtering (edge-preserving denoising) — lighter for screen captures
    denoised = cv2.bilateralFilter(enhanced, 5, 50, 50)

    # 3. Adaptive thresholding — smaller blockSize works better for clean screen text
    binary = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=15,
        C=8,
    )
    
    # 4. Optional: Morphological operations for aggressive preprocessing
    if aggressive:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary


def enhance_for_ocr_preserve_color(image_path: Path) -> Optional[np.ndarray]:
    """
    Enhanced preprocessing that preserves some color information for better OCR.
    Useful for colored text or mixed-color documents.
    """
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"[✗] Could not read image: {image_path}")
        return None
    
    # Convert BGR to HSV for better color handling
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Enhance saturation for text clarity
    hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.2)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    
    # Convert back to BGR, then to grayscale
    enhanced_bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    gray = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )
    
    return binary


# -------------------------------------------------
# 3️⃣  Pytesseract Integration with Multiple Modes
# -------------------------------------------------

# PSM (Page Segmentation Mode) constants for Tesseract
PSM_MODES = {
    "auto": 3,              # Automatic page segmentation with OSD
    "single_block": 6,      # Single uniform block of text
    "single_column": 4,     # Single column of text of variable sizes
    "single_line": 7,       # Single text line
    "single_word": 8,       # Treat the image as a single word
    "circle_word": 9,       # Treat the image as a single word in a circle
    "line": 11,             # Sparse text with layout preservation
    "sparse_text": 11,      # Find as much text as possible
    "raw_line": 13,         # Treat image as raw line
}


def extract_text_basic(
    image_path: Path = TEMP_SCREENSHOT_PATH,
    lang: str = "eng",
    psm: int = 3
) -> str:
    """Basic text extraction using pytesseract with PIL (no cv2 dependency)."""
    if not is_ocr_available():
        return ""
    try:
        from PIL import Image
        img = Image.open(str(image_path))
        config = f'--psm {psm} -l {lang}'
        text = pytesseract.image_to_string(img, config=config)
        return text.strip() if text else ""
    except Exception as e:
        print(f"[✗] Basic OCR failed: {e}")
        return ""


def extract_text_enhanced(
    image_path: Path = TEMP_SCREENSHOT_PATH,
    lang: str = "eng",
    psm: int = 3,
    aggressive: bool = False
) -> str:
    """Enhanced text extraction with cv2 preprocessing. Falls back to PIL on failure."""
    if not is_ocr_available():
        return ""
    try:
        processed = enhance_for_ocr(image_path, aggressive=aggressive)
        if processed is None:
            # cv2 couldn't read the image — fall back to PIL directly
            return extract_text_basic(image_path, lang=lang, psm=psm)
        config = f'--psm {psm} -l {lang}'
        text = pytesseract.image_to_string(processed, config=config)
        return text.strip() if text else ""
    except Exception as e:
        print(f"[✗] Enhanced OCR failed: {e}")
        return ""


def extract_text_with_confidence(
    image_path: Path = TEMP_SCREENSHOT_PATH,
    lang: str = "eng",
    psm: int = 3
) -> Dict:
    """
    Extract text with confidence scores and detailed data.
    
    Returns dict with:
        - text: Extracted text
        - confidence: Overall confidence (0-100)
        - boxes: Bounding boxes for each word
        - languages: Languages detected
    """
    if not is_ocr_available():
        return {"text": "", "confidence": 0, "boxes": [], "languages": []}
    
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return {"text": "", "confidence": 0, "boxes": [], "languages": []}
        
        config = f'--psm {psm} -l {lang}'
        
        # Get text
        text = pytesseract.image_to_string(img, config=config)
        
        # Get detailed data (boxes, confidence, etc.)
        data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence
        confidences = [int(c) for c in data['confidence'] if int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            "text": text.strip() if text else "",
            "confidence": round(avg_confidence),
            "boxes": len(data['text']),
            "languages": TESSERACT_LANGUAGES.split('+'),
            "words": [w for w in data['text'] if w.strip()]
        }
    
    except Exception as e:
        print(f"[✗] Confidence extraction failed: {e}")
        return {"text": "", "confidence": 0, "boxes": [], "languages": []}


def extract_text_multi_mode(
    image_path: Path = TEMP_SCREENSHOT_PATH,
    lang: str = "eng"
) -> Dict[str, str]:
    """
    Try multiple PSM modes and return results with best confidence.
    Useful for unknown document types.
    """
    if not is_ocr_available():
        return {}
    
    results = {}
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return {}
        
        for mode_name, psm_num in PSM_MODES.items():
            try:
                config = f'--psm {psm_num} -l {lang}'
                text = pytesseract.image_to_string(img, config=config)
                if text.strip():
                    results[mode_name] = text.strip()
            except:
                pass
        
        return results
    
    except Exception as e:
        print(f"[✗] Multi-mode OCR failed: {e}")
        return {}


# -------------------------------------------------
# 4️⃣  Convenience Functions
# -------------------------------------------------

def extract_text_from_image(
    image_path: Path = TEMP_SCREENSHOT_PATH,
    use_enhancement: bool = True,
    aggressive: bool = False
) -> str:
    """
    Main OCR function. Screen captures are already clean, so basic OCR is tried
    first. Enhanced preprocessing is only applied as a fallback when basic OCR
    returns very little text (< 20 chars), since it can hurt clean images.
    """
    # Basic OCR first — best for clean screen captures (PDFs, browsers, etc.)
    basic = extract_text_basic(
        image_path,
        lang=TESSERACT_LANGUAGES,
        psm=PSM_MODES["auto"]
    )
    if basic and len(basic.strip()) >= 20:
        return basic

    # Fallback: try enhanced preprocessing for low-contrast or faint text
    if use_enhancement:
        enhanced = extract_text_enhanced(
            image_path,
            lang=TESSERACT_LANGUAGES,
            psm=PSM_MODES["auto"],
            aggressive=aggressive
        )
        if enhanced and len(enhanced.strip()) > len(basic.strip()):
            return enhanced

    return basic


def ocr_debug_save(image_path: Path, processed: np.ndarray = None):
    """
    Save preprocessed image for visual inspection and debugging.
    
    Args:
        image_path: Original image path
        processed: Preprocessed image array (if None, creates one)
    """
    if processed is None:
        processed = enhance_for_ocr(image_path)
    
    if processed is not None:
        debug_path = OCR_OUTPUT_DIR / f"debug_{image_path.stem}.png"
        cv2.imwrite(str(debug_path), processed)
        print(f"[✓] Debug image saved: {debug_path}")
    else:
        print("[✗] Could not create debug image")


def ocr_batch_process(image_dir: Path, lang: str = "eng", pattern: str = "*.png") -> Dict[str, str]:
    """
    Process multiple images in a directory.
    
    Args:
        image_dir: Directory containing images
        lang: Language for OCR
        pattern: File pattern (e.g., '*.png', '*.jpg')
    
    Returns:
        Dictionary mapping filenames to extracted text
    """
    if not is_ocr_available():
        print("[⚠] OCR not available")
        return {}
    
    results = {}
    image_dir = Path(image_dir)
    
    if not image_dir.exists():
        print(f"[✗] Directory not found: {image_dir}")
        return results
    
    for image_file in image_dir.glob(pattern):
        try:
            text = extract_text_enhanced(image_file, lang=lang)
            results[image_file.name] = text
            print(f"[✓] {image_file.name}: {len(text)} chars extracted")
        except Exception as e:
            print(f"[✗] Failed to process {image_file.name}: {e}")
            results[image_file.name] = ""
    
    return results

# -------------------------------------------------
# 5️⃣  Graph Analysis Integration
# -------------------------------------------------

def analyze_graphs_in_screenshot(image_path: Path = TEMP_SCREENSHOT_PATH) -> str:
    """
    Detect and analyze graphs/charts in a screenshot.
    Returns a text description of detected graphs and their data.
    """
    try:
        from .graph_analyzer import analyze_graph_in_image
        
        graph_data = analyze_graph_in_image(image_path)
        if graph_data:
            return graph_data.description
        return "No graphs detected in screenshot"
    except Exception as e:
        print(f"[✗] Graph analysis failed: {e}")
        return ""


def combined_screenshot_analysis(
    image_path: Path = TEMP_SCREENSHOT_PATH,
    include_graphs: bool = True
) -> Dict[str, str]:
    """
    Perform both text OCR and graph analysis on a screenshot.
    
    Args:
        image_path: Path to screenshot
        include_graphs: Whether to analyze graphs
    
    Returns:
        Dictionary with 'text' and 'graphs' keys
    """
    result = {
        "text": extract_text_from_image(image_path),
        "status": "✓ OCR" if is_ocr_available() else "⚠ OCR unavailable"
    }
    
    if include_graphs:
        result["graphs"] = analyze_graphs_in_screenshot(image_path)
    
    return result

# -------------------------------------------------
# 6️⃣  Diagnostic & Status Functions
# -------------------------------------------------

def get_ocr_status() -> Dict[str, any]:
    """Get comprehensive OCR system status."""
    return {
        "pytesseract_available": PYTESSERACT_AVAILABLE,
        "tesseract_installed": TESSERACT_INSTALLED,
        "tesseract_path": TESSERACT_PATH,
        "ocr_available": is_ocr_available(),
        "tesseract_version": get_tesseract_version(),
        "available_languages": get_tesseract_languages(),
        "configured_languages": TESSERACT_LANGUAGES,
        "tessdata_prefix": os.environ.get('TESSDATA_PREFIX', 'Not set'),
    }


def print_ocr_status():
    """Print formatted OCR status information."""
    status = get_ocr_status()
    print("\n" + "="*60)
    print("OCR SYSTEM STATUS")
    print("="*60)
    for key, value in status.items():
        print(f"  {key:.<45} {value}")
    print("="*60 + "\n")


def verify_tesseract_installation() -> bool:
    """
    Verify Tesseract is properly installed and accessible.
    Provides helpful error messages if not found.
    """
    print("\n[INFO] Verifying Tesseract installation...")
    
    if not PYTESSERACT_AVAILABLE:
        print("[✗] pytesseract module not installed")
        print("    Fix: pip install pytesseract")
        return False
    
    if not is_ocr_available():
        print("[✗] Tesseract-OCR not found")
        print("    Download: https://github.com/UB-Mannheim/tesseract/releases")
        print("    Or install: pip install pytesseract-ocr (includes bundled Tesseract)")
        return False
    
    version = get_tesseract_version()
    languages = get_tesseract_languages()
    
    print(f"[✓] Tesseract version: {version}")
    print(f"[✓] Available languages: {', '.join(languages)}")
    return True

