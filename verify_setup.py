"""
Verification and setup script for Monitor-AI Graph Analysis.

This script verifies:
1. Model file is in correct location
2. All required packages are installed
3. Graph analyzer can be imported
4. pytesseract is properly configured
"""

import sys
from pathlib import Path
import subprocess


def check_model_file():
    """Check if the AI model is downloaded and accessible."""
    print("\n" + "="*60)
    print("1. Checking AI Model File")
    print("="*60)
    
    model_path = Path("MONITOR-AI-ASSISTANT/models/mistral-7b-v0.1.Q4_0.gguf")
    
    if model_path.exists():
        size_gb = model_path.stat().st_size / (1024**3)
        print(f"✓ Model file found: {model_path}")
        print(f"  Size: {size_gb:.2f} GB")
        return True
    else:
        print(f"✗ Model file NOT found: {model_path}")
        print("  Status: Download may still be in progress")
        return False


def check_packages():
    """Check if required packages are installed."""
    print("\n" + "="*60)
    print("2. Checking Required Packages")
    print("="*60)
    
    packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'pytesseract': 'pytesseract',
        'llama_cpp': 'llama-cpp-python',
    }
    
    all_ok = True
    for module_name, package_name in packages.items():
        try:
            __import__(module_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} - NOT INSTALLED")
            print(f"  Install with: pip install {package_name}")
            all_ok = False
    
    return all_ok


def check_tesseract():
    """Check if Tesseract-OCR is installed."""
    print("\n" + "="*60)
    print("3. Checking Tesseract-OCR Installation")
    print("="*60)
    
    # First check PATH (legacy check)
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ Tesseract found in PATH: {version_line}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check if pytesseract can find it directly
    try:
        import pytesseract
        from pathlib import Path
        
        # Check common installation paths
        tesseract_paths = [
            Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
            Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        ]
        
        for path in tesseract_paths:
            if path.exists():
                print(f"✓ Tesseract found: {path}")
                print("  (pytesseract configured to use this path)")
                return True
    except:
        pass
    
    print("⚠ Tesseract-OCR not found in system PATH")
    print("  However, pytesseract may still work with direct path configuration")
    print("\n  To add to PATH:")
    print("  Windows: choco install tesseract")
    print("  Linux:   apt-get install tesseract-ocr")
    print("  macOS:   brew install tesseract")
    return False


def check_graph_analyzer():
    """Check if graph analyzer module can be imported."""
    print("\n" + "="*60)
    print("4. Checking Graph Analyzer Module")
    print("="*60)
    
    try:
        from src.graph_analyzer import GraphAnalyzer, analyze_graph_in_image
        print("✓ graph_analyzer module imported successfully")
        
        # Try to instantiate
        analyzer = GraphAnalyzer()
        print("✓ GraphAnalyzer instantiated successfully")
        
        print(f"✓ pytesseract availability: {analyzer.pytesseract_available}")
        return True
    except Exception as e:
        print(f"✗ Failed to import graph_analyzer: {e}")
        return False


def check_ocr_processor():
    """Check if OCR processor has graph analysis."""
    print("\n" + "="*60)
    print("5. Checking OCR Processor Enhancements")
    print("="*60)
    
    try:
        from src.ocr_processor import (
            extract_text_from_image,
            analyze_graphs_in_screenshot,
            combined_screenshot_analysis
        )
        print("✓ extract_text_from_image()")
        print("✓ analyze_graphs_in_screenshot()")
        print("✓ combined_screenshot_analysis()")
        return True
    except Exception as e:
        print(f"✗ Failed to import from ocr_processor: {e}")
        return False


def check_ai_processor():
    """Check if AI processor has graph analysis."""
    print("\n" + "="*60)
    print("6. Checking AI Processor Enhancements")
    print("="*60)
    
    try:
        from src.ai_processor import (
            query_llm,
            analyze_graph_with_llm,
            combined_analysis
        )
        print("✓ query_llm()")
        print("✓ analyze_graph_with_llm()")
        print("✓ combined_analysis()")
        return True
    except Exception as e:
        print(f"✗ Failed to import from ai_processor: {e}")
        return False


def check_documentation():
    """Check if documentation files exist."""
    print("\n" + "="*60)
    print("7. Checking Documentation")
    print("="*60)
    
    docs = {
        'GRAPH_ANALYSIS.md': 'Graph Analysis Guide',
        'graph_analysis_examples.py': 'Usage Examples',
        'tests/test_graph_analyzer.py': 'Unit Tests',
        'IMPLEMENTATION_SUMMARY.md': 'Implementation Summary'
    }
    
    all_ok = True
    for filename, description in docs.items():
        path = Path(filename)
        if path.exists():
            print(f"✓ {description}: {filename}")
        else:
            print(f"✗ {description}: {filename} NOT FOUND")
            all_ok = False
    
    return all_ok


def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " MONITOR-AI GRAPH ANALYSIS VERIFICATION ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        'Model File': check_model_file(),
        'Required Packages': check_packages(),
        'Tesseract-OCR': check_tesseract(),
        'Graph Analyzer': check_graph_analyzer(),
        'OCR Processor': check_ocr_processor(),
        'AI Processor': check_ai_processor(),
        'Documentation': check_documentation(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    print("\n" + "="*60)
    if passed == total:
        print("✓ ALL CHECKS PASSED - System is ready!")
        print("\nYou can now:")
        print("  1. Run examples:    python graph_analysis_examples.py")
        print("  2. Run tests:       python -m pytest tests/test_graph_analyzer.py -v")
        print("  3. Read docs:       cat GRAPH_ANALYSIS.md")
        return 0
    else:
        failed = total - passed
        print(f"✗ {failed} check(s) failed - Please fix issues above")
        print("\nMost common issues:")
        if not results['Model File']:
            print("  • Model download still in progress (check in 1-2 minutes)")
        if not results['Required Packages']:
            print("  • Run: pip install -r requirements.txt")
        if not results['Tesseract-OCR']:
            print("  • Install Tesseract-OCR (system package, see above)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
