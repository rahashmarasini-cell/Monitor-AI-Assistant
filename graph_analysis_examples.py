"""
Example usage of the Graph Analyzer integration with pytesseract.

This script demonstrates how to use the graph analysis capabilities
added to the Monitor-AI Assistant.
"""

from pathlib import Path
from src.graph_analyzer import (
    analyze_graph_in_image,
    get_graph_description,
    GraphAnalyzer
)
from src.ocr_processor import (
    extract_text_from_image,
    analyze_graphs_in_screenshot,
    combined_screenshot_analysis
)
from src.ai_processor import (
    analyze_graph_with_llm,
    combined_analysis,
    query_llm
)
from src.config import TEMP_SCREENSHOT_PATH


# ============================================================
# EXAMPLE 1: Direct Graph Analysis (pytesseract + OpenCV)
# ============================================================
def example_graph_detection():
    """
    Demonstrates graph detection and pytesseract text extraction
    from a graph region.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Direct Graph Analysis")
    print("="*60)
    
    image_path = TEMP_SCREENSHOT_PATH
    
    # Analyze graph in image
    graph_data = analyze_graph_in_image(image_path)
    
    if graph_data:
        print(f"Title: {graph_data.title}")
        print(f"X-Axis: {graph_data.x_axis_label}")
        print(f"Y-Axis: {graph_data.y_axis_label}")
        print(f"Data Points Found: {len(graph_data.data_points)}")
        print(f"Description: {graph_data.description}")
        print(f"Confidence: {graph_data.confidence:.2%}")
        print(f"\nExtracted Values:")
        for key, value in graph_data.extracted_values.items():
            print(f"  {key}: {value}")
    else:
        print("No graph detected in image")


# ============================================================
# EXAMPLE 2: Text-Only OCR Analysis
# ============================================================
def example_text_extraction():
    """
    Extract text from screenshot using pytesseract.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Text OCR Extraction")
    print("="*60)
    
    image_path = TEMP_SCREENSHOT_PATH
    
    text = extract_text_from_image(image_path)
    print(f"Extracted Text:\n{text}\n")


# ============================================================
# EXAMPLE 3: Graph Analysis Description
# ============================================================
def example_graph_text_description():
    """
    Get a text description of detected graphs using pytesseract.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Graph Analysis Description")
    print("="*60)
    
    image_path = TEMP_SCREENSHOT_PATH
    
    description = get_graph_description(image_path)
    print(f"Graph Description:\n{description}\n")


# ============================================================
# EXAMPLE 4: Combined Text + Graph Analysis (No LLM)
# ============================================================
def example_combined_ocr():
    """
    Perform both text extraction and graph analysis.
    Returns both separately for comparison.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Combined OCR Analysis (Text + Graphs)")
    print("="*60)
    
    image_path = TEMP_SCREENSHOT_PATH
    
    results = combined_screenshot_analysis(image_path)
    
    print("TEXT EXTRACTION:")
    print(results["text"])
    print("\nGRAPH ANALYSIS:")
    print(results["graphs"])
    print("\nCOMBINED ANALYSIS:")
    print(results["combined"])


# ============================================================
# EXAMPLE 5: LLM Analysis of Graphs
# ============================================================
def example_llm_graph_analysis():
    """
    Use the local LLM to interpret graph analysis from pytesseract.
    The LLM will provide insights about detected graphs.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: LLM Interpretation of Graphs")
    print("="*60)
    
    image_path = TEMP_SCREENSHOT_PATH
    
    # Optional: ask a specific question
    question = "What trends do you see in this graph?"
    
    analysis = analyze_graph_with_llm(image_path, user_question=question)
    print(f"LLM Analysis:\n{analysis}\n")


# ============================================================
# EXAMPLE 6: Combined Text + Graph Analysis with LLM
# ============================================================
def example_llm_combined_analysis():
    """
    Perform OCR text extraction, graph analysis with pytesseract,
    and feed both to the LLM for comprehensive analysis.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Full Analysis (Text + Graphs + LLM)")
    print("="*60)
    
    image_path = TEMP_SCREENSHOT_PATH
    
    # First, extract text
    extracted_text = extract_text_from_image(image_path)
    
    # Then perform combined analysis with LLM
    llm_response = combined_analysis(
        extracted_text=extracted_text,
        image_path=image_path,
        user_question="Summarize what you see in this screenshot"
    )
    
    print(f"LLM Combined Analysis:\n{llm_response}\n")


# ============================================================
# EXAMPLE 7: Graph Analyzer Class Direct Usage
# ============================================================
def example_analyzer_class():
    """
    Advanced usage: Direct use of the GraphAnalyzer class
    for fine-grained control.
    """
    print("\n" + "="*60)
    print("EXAMPLE 7: Advanced GraphAnalyzer Usage")
    print("="*60)
    
    import cv2
    
    analyzer = GraphAnalyzer()
    image_path = TEMP_SCREENSHOT_PATH
    
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"Could not load image: {image_path}")
        return
    
    # Detect graph regions
    graph_regions = analyzer.detect_graph_regions(image)
    print(f"Detected {len(graph_regions)} graph region(s)")
    
    # For each region, analyze it
    for i, region in enumerate(graph_regions):
        print(f"\nRegion {i+1}:")
        
        # Extract text from region using pytesseract
        text_data = analyzer.extract_text_from_region(region)
        print(f"  Extracted Text: {text_data.get('full_text', '')[:100]}...")
        
        # Detect data points
        points = analyzer.detect_data_points(region)
        print(f"  Data Points Detected: {len(points)}")


# ============================================================
# WORKFLOW EXAMPLE: Real-world usage
# ============================================================
def example_real_world_workflow():
    """
    Real-world example: Monitor screenshot, analyze contents,
    and get AI insights.
    """
    print("\n" + "="*60)
    print("REAL-WORLD WORKFLOW: Complete Screenshot Analysis")
    print("="*60)
    
    print("1. Capturing screenshot...")
    # (In actual usage, screen_capture.py would capture)
    # capture_screen(CAPTURE_MONITOR_INDEX, TEMP_SCREENSHOT_PATH)
    
    print("2. Extracting text with pytesseract...")
    text = extract_text_from_image(TEMP_SCREENSHOT_PATH)
    print(f"   Found {len(text.split())} words")
    
    print("3. Analyzing graphs with pytesseract + OpenCV...")
    graph_desc = analyze_graphs_in_screenshot(TEMP_SCREENSHOT_PATH)
    print(f"   Graph analysis: {graph_desc[:100]}...")
    
    print("4. Getting AI interpretation...")
    insight = combined_analysis(
        extracted_text=text,
        image_path=TEMP_SCREENSHOT_PATH,
        user_question="What's the key takeaway from this?"
    )
    print(f"   AI Response: {insight[:200]}...")
    
    print("\nWorkflow complete!")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("Monitor-AI Graph Analysis Examples")
    print("="*60)
    print("\nThese examples show how to use pytesseract for graph analysis")
    print("integrated with the Monitor-AI Assistant.\n")
    
    # Run all examples
    try:
        example_text_extraction()
    except Exception as e:
        print(f"Text extraction example failed: {e}")
    
    try:
        example_graph_detection()
    except Exception as e:
        print(f"Graph detection example failed: {e}")
    
    try:
        example_graph_text_description()
    except Exception as e:
        print(f"Graph description example failed: {e}")
    
    try:
        example_combined_ocr()
    except Exception as e:
        print(f"Combined OCR example failed: {e}")
    
    try:
        example_analyzer_class()
    except Exception as e:
        print(f"Advanced analyzer example failed: {e}")
    
    print("\n" + "="*60)
    print("✓ Graph Analysis Examples Complete")
    print("="*60)
