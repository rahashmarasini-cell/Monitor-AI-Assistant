"""
Graph Analyzer – Detects and analyzes graphs/charts using pytesseract and OpenCV.

This module provides functionality to:
  1. Detect graph regions in screenshots
  2. Extract axis labels and values using pytesseract
  3. Identify data points and trends
  4. Return structured analysis of graphs/charts
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


@dataclass
class GraphData:
    """Structured representation of extracted graph data."""
    title: str
    x_axis_label: str
    y_axis_label: str
    data_points: List[Tuple[float, float]]
    extracted_values: Dict[str, str]  # Any text labels/values found
    description: str  # Human-readable description of the graph
    confidence: float  # Confidence score (0-1) for the analysis


class GraphAnalyzer:
    """Analyzes graphs and charts in images using OCR and computer vision."""

    def __init__(self):
        """Initialize the graph analyzer."""
        self.pytesseract_available = PYTESSERACT_AVAILABLE
        if not self.pytesseract_available:
            print("[WARNING] pytesseract not available - graph analysis will be limited")

    def detect_graph_regions(self, image: np.ndarray) -> List[np.ndarray]:
        """
        Detect potential graph/chart regions in the image.
        
        Returns:
            List of image regions that likely contain graphs
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection to find borders
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate to connect nearby edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours that are likely graphs (large rectangular areas)
        graph_regions = []
        image_area = image.shape[0] * image.shape[1]
        
        for contour in contours:
            area = cv2.contourArea(contour)
            # Look for contours that are 10-70% of the image area (likely to be graph areas)
            if 0.1 * image_area < area < 0.7 * image_area:
                x, y, w, h = cv2.boundingRect(contour)
                # Prefer roughly rectangular shapes (aspect ratio between 0.5 and 2)
                aspect_ratio = float(w) / h if h > 0 else 0
                if 0.5 < aspect_ratio < 2.0:
                    region = image[y:y+h, x:x+w]
                    graph_regions.append(region)
        
        return graph_regions

    def extract_text_from_region(self, region: np.ndarray) -> Dict[str, str]:
        """
        Extract all text from a graph region using pytesseract.
        
        Returns:
            Dictionary with extracted text organized by region
        """
        if not self.pytesseract_available:
            return {"error": "pytesseract not available"}
        
        try:
            # Enhance contrast for better OCR
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Extract text
            full_text = pytesseract.image_to_string(enhanced)
            
            # Also try to get detailed data
            data = pytesseract.image_to_data(enhanced, output_type=pytesseract.Output.DICT)
            
            return {
                "full_text": full_text,
                "words": data.get('text', []),
                "confidence": np.mean([int(c) for c in data.get('confidence', [0]) if c != '-1'])
            }
        except Exception as e:
            print(f"[ERROR] Failed to extract text from region: {e}")
            return {"error": str(e)}

    def detect_data_points(self, region: np.ndarray) -> List[Tuple[int, int]]:
        """
        Detect data points (markers) in a graph.
        
        Returns:
            List of (x, y) coordinates of detected data points
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # Look for common graph marker colors (red, blue, green dots)
        data_points = []
        
        # Define color ranges for common markers
        color_ranges = {
            'red': (np.array([0, 100, 100]), np.array([10, 255, 255])),
            'blue': (np.array([100, 100, 100]), np.array([130, 255, 255])),
            'green': (np.array([40, 100, 100]), np.array([80, 255, 255])),
        }
        
        for color_name, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, lower, upper)
            
            # Find contours of colored regions
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter by contour size (should be small for data points)
                area = cv2.contourArea(contour)
                if 10 < area < 1000:  # Reasonable size for a data point marker
                    M = cv2.moments(contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        data_points.append((cx, cy))
        
        return data_points

    def analyze_graph(self, image_path: Path) -> Optional[GraphData]:
        """
        Complete analysis of a graph/chart in an image.
        
        Args:
            image_path: Path to the image file containing the graph
            
        Returns:
            GraphData object with extracted information, or None if no graph found
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"[ERROR] Could not read image: {image_path}")
                return None
            
            # Detect graph regions
            graph_regions = self.detect_graph_regions(image)
            if not graph_regions:
                print("[DEBUG] No graph regions detected")
                return None
            
            # Analyze the primary (largest) graph region
            primary_region = max(graph_regions, key=lambda r: r.shape[0] * r.shape[1])
            
            # Extract text
            text_data = self.extract_text_from_region(primary_region)
            
            # Detect data points
            data_points = self.detect_data_points(primary_region)
            
            # Parse extracted text to find axes and values
            full_text = text_data.get('full_text', '')
            lines = full_text.split('\n')
            
            # Simple parsing: first line is title, look for axis labels
            title = lines[0] if lines else "Untitled Graph"
            x_label = ""
            y_label = ""
            
            # Extract axis labels (usually contain "x", "y", or axis names)
            for line in lines[1:]:
                if any(keyword in line.lower() for keyword in ['x-axis', 'x axis', 'time', 'date']):
                    x_label = line
                elif any(keyword in line.lower() for keyword in ['y-axis', 'y axis', 'value', 'amount']):
                    y_label = line
            
            # Create description
            description = f"Graph: {title}. "
            if data_points:
                description += f"Detected {len(data_points)} data points. "
            if x_label:
                description += f"X-axis: {x_label}. "
            if y_label:
                description += f"Y-axis: {y_label}. "
            
            # Calculate confidence based on text extraction
            confidence = text_data.get('confidence', 0) / 100.0 if isinstance(text_data.get('confidence'), (int, float)) else 0.5
            
            return GraphData(
                title=title,
                x_axis_label=x_label,
                y_axis_label=y_label,
                data_points=data_points,
                extracted_values=text_data,
                description=description,
                confidence=confidence
            )
            
        except Exception as e:
            print(f"[ERROR] Graph analysis failed: {e}")
            return None

    def analyze_multiple_graphs(self, image_path: Path) -> List[GraphData]:
        """
        Analyze multiple graphs in a single image.
        
        Returns:
            List of GraphData objects for each detected graph
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return []
            
            graph_regions = self.detect_graph_regions(image)
            results = []
            
            for i, region in enumerate(graph_regions):
                text_data = self.extract_text_from_region(region)
                data_points = self.detect_data_points(region)
                
                full_text = text_data.get('full_text', '')
                lines = full_text.split('\n')
                
                title = f"Graph {i+1}"
                if lines:
                    title = lines[0] if lines[0].strip() else title
                
                description = f"Graph {i+1}: {len(data_points)} data points detected"
                
                graph_data = GraphData(
                    title=title,
                    x_axis_label="",
                    y_axis_label="",
                    data_points=data_points,
                    extracted_values=text_data,
                    description=description,
                    confidence=0.5
                )
                results.append(graph_data)
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Multiple graph analysis failed: {e}")
            return []


# -------------------------------------------------
# Helper functions for easy access
# -------------------------------------------------

_analyzer = None

def get_analyzer() -> GraphAnalyzer:
    """Get or create the global graph analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GraphAnalyzer()
    return _analyzer


def analyze_graph_in_image(image_path: Path) -> Optional[GraphData]:
    """
    Quick function to analyze a graph in an image file.
    
    Args:
        image_path: Path to the image containing the graph
        
    Returns:
        GraphData with extracted information, or None
    """
    analyzer = get_analyzer()
    return analyzer.analyze_graph(image_path)


def get_graph_description(image_path: Path) -> str:
    """
    Get a text description of a graph.
    
    Args:
        image_path: Path to the image containing the graph
        
    Returns:
        Human-readable description of the graph
    """
    graph = analyze_graph_in_image(image_path)
    if graph:
        return graph.description
    return "No graph detected in image"

# -------------------------------------------------
