# Graph Analysis Integration with pytesseract

## Overview

The Monitor-AI Assistant now includes sophisticated graph and chart analysis capabilities using **pytesseract** (OCR) and **OpenCV** (computer vision). This enables the system to:

1. **Detect graphs** in screenshots automatically
2. **Extract text** from graphs using pytesseract (axis labels, titles, values)
3. **Identify data points** and markers
4. **Analyze trends** and patterns
5. **Generate insights** using the local LLM

## Features

### 1. Automatic Graph Detection
- Uses OpenCV edge detection and contour analysis
- Identifies rectangular graph regions in screenshots
- Filters by size and aspect ratio to avoid false positives

### 2. pytesseract Text Extraction
- Extracts all text from graph regions (labels, titles, legends)
- Uses image preprocessing (contrast enhancement, denoising)
- Returns confidence scores for OCR accuracy

### 3. Data Point Detection
- Identifies colored markers (red, blue, green dots)
- Detects graph legend elements
- Estimates data point locations

### 4. LLM Interpretation
- Feeds graph analysis to the local Mistral-7B model
- Generates natural language insights
- Answers user questions about graphs

## Architecture

### Core Modules

#### `graph_analyzer.py`
Main graph analysis engine:
- `GraphAnalyzer` class: Core functionality
- `GraphData` dataclass: Structured output format
- Helper functions: `analyze_graph_in_image()`, `get_graph_description()`

**Key Methods:**
```python
# Detect graph regions in image
regions = analyzer.detect_graph_regions(image)

# Extract text using pytesseract
text_data = analyzer.extract_text_from_region(region)

# Identify data points
points = analyzer.detect_data_points(region)

# Complete analysis
graph_data = analyzer.analyze_graph(image_path)
```

#### `ocr_processor.py` (Enhanced)
OCR processing with graph support:
- `extract_text_from_image()`: Traditional text OCR
- `analyze_graphs_in_screenshot()`: Graph detection + pytesseract
- `combined_screenshot_analysis()`: Text + graphs

#### `ai_processor.py` (Enhanced)
AI-powered analysis:
- `analyze_graph_with_llm()`: Graph analysis → LLM interpretation
- `combined_analysis()`: Text + graphs → LLM insight
- `query_llm()`: Original text-only analysis (still available)

## Usage Examples

### Basic Graph Analysis
```python
from pathlib import Path
from src.graph_analyzer import analyze_graph_in_image

image_path = Path("screenshot.png")
graph_data = analyze_graph_in_image(image_path)

if graph_data:
    print(f"Title: {graph_data.title}")
    print(f"X-Axis: {graph_data.x_axis_label}")
    print(f"Y-Axis: {graph_data.y_axis_label}")
    print(f"Found {len(graph_data.data_points)} data points")
    print(f"Description: {graph_data.description}")
```

### Graph Analysis with LLM
```python
from src.ai_processor import analyze_graph_with_llm

analysis = analyze_graph_with_llm(
    image_path=Path("graph.png"),
    user_question="What are the key trends?"
)
print(analysis)
```

### Combined Text + Graph Analysis
```python
from src.ai_processor import combined_analysis
from src.ocr_processor import extract_text_from_image

text = extract_text_from_image(Path("screenshot.png"))
insight = combined_analysis(
    extracted_text=text,
    image_path=Path("screenshot.png"),
    user_question="Summarize this screenshot"
)
print(insight)
```

### Advanced: Direct Analyzer Usage
```python
import cv2
from src.graph_analyzer import GraphAnalyzer

analyzer = GraphAnalyzer()
image = cv2.imread("screenshot.png")

# Detect regions
regions = analyzer.detect_graph_regions(image)

# Analyze each region
for region in regions:
    text = analyzer.extract_text_from_region(region)
    points = analyzer.detect_data_points(region)
    print(f"Extracted: {text}")
    print(f"Data points: {len(points)}")
```

## Data Structure

### GraphData Dataclass
```python
@dataclass
class GraphData:
    title: str                           # Graph title
    x_axis_label: str                   # X-axis label
    y_axis_label: str                   # Y-axis label
    data_points: List[Tuple[float, float]]  # Detected point coordinates
    extracted_values: Dict[str, str]    # OCR-extracted text
    description: str                    # Human-readable summary
    confidence: float                   # Confidence score (0-1)
```

## Performance Considerations

### Processing Time (CPU Only)
- Graph detection: ~100-200ms
- pytesseract text extraction: ~500-1000ms
- Data point detection: ~200-300ms
- **Total: ~800ms-1.5s per screenshot**

### Optimization Tips
1. **Preprocess images**: Enhance contrast before analysis
2. **Region filtering**: Focus on large rectangular regions
3. **Parallel processing**: Analyze multiple screenshots concurrently
4. **Cache results**: Store graph analyses for repeated queries

### GPU Acceleration
If available, enable GPU support:
```python
# Enable GPU in graph detection
# (Future enhancement: DirectML support)
```

## Dependencies

### Required
- `opencv-python` (>=4.8.0) - Image processing
- `pytesseract` (>=0.3.10) - OCR text extraction
- `numpy` (>=1.20) - Array operations

### Optional
- `Tesseract-OCR` (system package) - pytesseract backend

### Tesseract Installation

**Windows:**
```bash
# Install via chocolatey
choco install tesseract

# Or download from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Configuration

### Environment Variables
```bash
# pytesseract path (if Tesseract not in PATH)
set PYTESSERACT_PATH=C:\Program Files\Tesseract-OCR\pytesseract.py

# Custom Tesseract location
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Parameters in graph_analyzer.py
```python
# Minimum/maximum graph area (percentage of image)
GRAPH_AREA_MIN = 0.1  # 10%
GRAPH_AREA_MAX = 0.7  # 70%

# Aspect ratio filtering (width/height)
ASPECT_RATIO_MIN = 0.5
ASPECT_RATIO_MAX = 2.0

# Data point marker size filtering
MARKER_AREA_MIN = 10
MARKER_AREA_MAX = 1000

# OCR confidence threshold
OCR_CONFIDENCE_MIN = 30  # percentage
```

## Limitations

1. **Handwritten labels**: pytesseract works best with printed text
2. **Small graphs**: Requires minimum resolution (~100x100 pixels)
3. **Rotated graphs**: Not currently handled (could enhance)
4. **Complex layouts**: Multiple overlapping graphs may confuse detection
5. **Non-text data**: Cannot extract pure numerical data without labels

## Troubleshooting

### pytesseract Not Found
```
ERROR: Could not import pytesseract
```
**Solution**: Install pytesseract
```bash
pip install pytesseract
```

### Tesseract Not Found
```
TesseractNotFoundError: tesseract is not installed
```
**Solution**: Install Tesseract-OCR (see Dependencies section)

### Poor OCR Accuracy
- Ensure graph has good contrast
- Try different CLAHE parameters in ocr_processor.py
- Verify Tesseract language packs are installed

### No Graphs Detected
- Check image has clear graph boundaries
- Try adjusting GRAPH_AREA_MIN/MAX in graph_analyzer.py
- Ensure graph has rectangular shape

## Future Enhancements

- [ ] Support for rotated graphs
- [ ] Direct numerical data extraction (pattern matching)
- [ ] GPU-accelerated OCR with CUDA
- [ ] Support for 3D and polar charts
- [ ] Automatic axis scaling detection
- [ ] Legend parsing and color mapping
- [ ] Trend line detection and equations
- [ ] Integration with SymPy for mathematical analysis

## Integration with Assistant

The graph analysis is automatically used when:
1. Screenshot contains visible graphs/charts
2. User asks questions about data or trends
3. Combined analysis is requested

The assistant will:
1. Extract graph data with pytesseract
2. Analyze with OpenCV
3. Feed to LLM for interpretation
4. Provide natural language insights

## Testing

Run the example script to test functionality:
```bash
python graph_analysis_examples.py
```

This will demonstrate all graph analysis capabilities.

## API Reference

### Public Functions

#### `analyze_graph_in_image(image_path: Path) -> Optional[GraphData]`
Complete graph analysis pipeline.

#### `get_graph_description(image_path: Path) -> str`
Get text description of detected graph.

#### `analyze_graphs_in_screenshot(image_path: Path) -> str`
Analyze all graphs in a screenshot.

#### `analyze_graph_with_llm(image_path: Path, user_question: Optional[str]) -> str`
Graph analysis with LLM interpretation.

#### `combined_analysis(extracted_text: str, image_path: Path, user_question: Optional[str]) -> str`
Text + graph analysis with LLM.

## Contributing

To enhance graph analysis:
1. Add new detection methods in `GraphAnalyzer`
2. Improve pytesseract accuracy
3. Support additional graph types
4. Optimize performance

---

**Version**: 1.0  
**Last Updated**: April 2026  
**Status**: Beta
