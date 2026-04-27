"""
Unit tests for graph analyzer functionality using pytesseract.

Tests the graph detection, OCR, and analysis capabilities.
"""

import unittest
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

try:
    from src.graph_analyzer import (
        GraphAnalyzer, GraphData, analyze_graph_in_image, get_graph_description
    )
    GRAPH_ANALYZER_AVAILABLE = True
except ImportError:
    GRAPH_ANALYZER_AVAILABLE = False


class TestGraphAnalyzer(unittest.TestCase):
    """Test cases for GraphAnalyzer class."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not GRAPH_ANALYZER_AVAILABLE:
            raise ImportError("graph_analyzer module not available")
        cls.analyzer = GraphAnalyzer()

    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer)
        self.assertTrue(hasattr(self.analyzer, 'detect_graph_regions'))
        self.assertTrue(hasattr(self.analyzer, 'extract_text_from_region'))

    def test_detect_graph_regions_empty_image(self):
        """Test graph detection on empty/blank image."""
        # Create a blank white image
        blank_image = np.ones((500, 500, 3), dtype=np.uint8) * 255
        
        regions = self.analyzer.detect_graph_regions(blank_image)
        
        # Should detect no regions in blank image
        self.assertEqual(len(regions), 0, "Blank image should have no graph regions")

    def test_detect_graph_regions_with_rectangle(self):
        """Test graph detection with a simple rectangular region."""
        # Create image with a rectangle
        image = np.ones((500, 500, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (50, 50), (450, 450), (0, 0, 0), 3)
        
        regions = self.analyzer.detect_graph_regions(image)
        
        # Should detect at least one region
        self.assertGreater(len(regions), 0, "Should detect rectangular region")

    def test_graph_data_dataclass(self):
        """Test GraphData dataclass creation."""
        graph = GraphData(
            title="Test Graph",
            x_axis_label="Time",
            y_axis_label="Value",
            data_points=[(0, 0), (1, 1)],
            extracted_values={"test": "value"},
            description="A test graph",
            confidence=0.95
        )
        
        self.assertEqual(graph.title, "Test Graph")
        self.assertEqual(graph.x_axis_label, "Time")
        self.assertEqual(len(graph.data_points), 2)
        self.assertEqual(graph.confidence, 0.95)

    def test_data_point_detection_no_markers(self):
        """Test data point detection on image without markers."""
        image = np.ones((200, 200, 3), dtype=np.uint8) * 255
        
        points = self.analyzer.detect_data_points(image)
        
        # Should find no colored markers
        self.assertEqual(len(points), 0, "Blank image should have no data points")

    @patch('cv2.imread')
    def test_analyze_graph_file_not_found(self, mock_imread):
        """Test graph analysis when image file not found."""
        mock_imread.return_value = None
        
        result = self.analyzer.analyze_graph(Path("nonexistent.png"))
        
        self.assertIsNone(result, "Should return None for missing file")

    def test_pytesseract_availability(self):
        """Test pytesseract availability check."""
        has_pytesseract = self.analyzer.pytesseract_available
        
        # Should be boolean
        self.assertIsInstance(has_pytesseract, bool)

    @patch('src.graph_analyzer.pytesseract')
    def test_extract_text_with_pytesseract(self, mock_pytesseract):
        """Test text extraction with mocked pytesseract."""
        # Mock pytesseract response
        mock_pytesseract.image_to_string.return_value = "Sample Graph Text"
        mock_pytesseract.image_to_data.return_value = {
            'text': ['Sample', 'Graph', 'Text'],
            'confidence': ['95', '90', '85']
        }
        
        image = np.ones((200, 200, 3), dtype=np.uint8)
        
        if self.analyzer.pytesseract_available:
            result = self.analyzer.extract_text_from_region(image)
            self.assertIn('full_text', result)


class TestGraphAnalyzerIntegration(unittest.TestCase):
    """Integration tests for graph analyzer with actual images."""

    def setUp(self):
        """Set up test fixtures."""
        if not GRAPH_ANALYZER_AVAILABLE:
            self.skipTest("graph_analyzer not available")

    def test_analyze_graph_in_image_with_mock(self):
        """Test analyze_graph_in_image function."""
        # Create a test image with a rectangle (simulating a graph)
        test_image = np.ones((300, 300, 3), dtype=np.uint8) * 255
        cv2.rectangle(test_image, (25, 25), (275, 275), (0, 0, 0), 2)
        
        # Save test image temporarily
        test_path = Path("test_graph.png")
        cv2.imwrite(str(test_path), test_image)
        
        try:
            result = analyze_graph_in_image(test_path)
            
            # Result should either be None or a GraphData object
            self.assertTrue(result is None or isinstance(result, GraphData))
        finally:
            # Clean up
            if test_path.exists():
                test_path.unlink()

    def test_get_graph_description(self):
        """Test get_graph_description helper function."""
        # Create a test image
        test_image = np.ones((300, 300, 3), dtype=np.uint8) * 255
        test_path = Path("test_desc.png")
        cv2.imwrite(str(test_path), test_image)
        
        try:
            description = get_graph_description(test_path)
            
            # Should return a string
            self.assertIsInstance(description, str)
            # Should not be empty
            self.assertGreater(len(description), 0)
        finally:
            if test_path.exists():
                test_path.unlink()


class TestGraphAnalyzerPerformance(unittest.TestCase):
    """Performance tests for graph analyzer."""

    def setUp(self):
        """Set up test fixtures."""
        if not GRAPH_ANALYZER_AVAILABLE:
            self.skipTest("graph_analyzer not available")
        self.analyzer = GraphAnalyzer()

    def test_detection_performance(self):
        """Test graph detection performance."""
        import time
        
        # Create test image
        image = np.ones((500, 500, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (50, 50), (450, 450), (0, 0, 0), 3)
        
        # Time the detection
        start = time.time()
        regions = self.analyzer.detect_graph_regions(image)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<1 second)
        self.assertLess(elapsed, 1.0, f"Detection took {elapsed:.2f}s (should be <1s)")

    def test_data_point_detection_performance(self):
        """Test data point detection performance."""
        import time
        
        # Create test image with colored regions
        image = np.ones((500, 500, 3), dtype=np.uint8) * 255
        # Add some red markers
        cv2.circle(image, (100, 100), 5, (0, 0, 255), -1)
        cv2.circle(image, (200, 200), 5, (0, 0, 255), -1)
        
        # Time the detection
        start = time.time()
        points = self.analyzer.detect_data_points(image)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (<1 second)
        self.assertLess(elapsed, 1.0, f"Data detection took {elapsed:.2f}s (should be <1s)")


# ============================================================
# Test Runner
# ============================================================
if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
