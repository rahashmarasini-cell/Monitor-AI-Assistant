#!/usr/bin/env python3
"""
Tesseract-OCR Installer for Monitor AI Assistant
Automatically detects, downloads, and installs Tesseract-OCR on Windows
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path
import time

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(num, text):
    """Print a step indicator."""
    print(f"\n[{num}] {text}")

def check_tesseract():
    """Check if Tesseract is already installed."""
    paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    ]
    
    for path in paths:
        if path.exists():
            print(f"✓ Tesseract found at: {path}")
            # Get version
            try:
                result = subprocess.run(
                    [str(path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    print(f"✓ Version: {version_line}")
                    return True
            except Exception as e:
                print(f"⚠ Could not verify version: {e}")
    
    return False

def check_pytesseract():
    """Check if pytesseract Python package is installed."""
    try:
        import pytesseract
        print(f"✓ pytesseract is installed")
        return True
    except ImportError:
        print(f"✗ pytesseract is not installed")
        return False

def install_pytesseract():
    """Install pytesseract via pip."""
    print_step("A", "Installing pytesseract Python package...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pytesseract", "-q"],
            check=True
        )
        print("✓ pytesseract installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install pytesseract: {e}")
        return False

def download_tesseract_installer():
    """Download Tesseract installer."""
    print_step("B", "Downloading Tesseract-OCR installer...")
    
    installer_path = Path(os.getenv("TEMP")) / "tesseract-ocr-setup.exe"
    url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3/tesseract-ocr-w64-setup-v5.3.3.exe"
    
    if installer_path.exists():
        print(f"✓ Installer already downloaded: {installer_path}")
        return installer_path
    
    try:
        print(f"  Downloading from: {url}")
        print(f"  Size: ~180 MB (this may take 2-5 minutes)")
        
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(downloaded * 100 / total_size, 100)
                mb_downloaded = downloaded / 1024 / 1024
                mb_total = total_size / 1024 / 1024
                print(f"  Progress: {percent:.1f}% ({mb_downloaded:.1f}MB / {mb_total:.1f}MB)", end="\r")
        
        urllib.request.urlretrieve(url, str(installer_path), download_progress)
        print()  # New line after progress
        print(f"✓ Downloaded to: {installer_path}")
        return installer_path
    
    except Exception as e:
        print(f"✗ Download failed: {e}")
        print(f"  Please download manually from: {url}")
        print(f"  Or use: https://github.com/UB-Mannheim/tesseract/releases")
        return None

def install_tesseract(installer_path):
    """Run Tesseract installer."""
    print_step("C", "Installing Tesseract-OCR...")
    print(f"  Installer: {installer_path}")
    print(f"  Installation path: C:\\Program Files\\Tesseract-OCR")
    print(f"  (This will take 2-3 minutes)")
    
    try:
        # Run installer silently
        result = subprocess.run(
            [str(installer_path), "/S", "/D=C:\\Program Files\\Tesseract-OCR"],
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print("✓ Installation command executed")
            return True
        else:
            print(f"✗ Installation failed with code: {result.returncode}")
            return False
    
    except subprocess.TimeoutExpired:
        print("⚠ Installation timeout (may still be running)")
        return None
    except Exception as e:
        print(f"✗ Installation error: {e}")
        return False

def verify_installation():
    """Verify Tesseract installation."""
    print_step("D", "Verifying installation...")
    
    # Wait a bit for installation to complete
    print("  Waiting for installation to complete...")
    for i in range(5):
        time.sleep(2)
        print(f"  {(i+1)*2} seconds...", end="\r")
    print()
    
    # Check Tesseract
    if check_tesseract():
        print("✓ Tesseract-OCR verified")
        return True
    else:
        print("⚠ Tesseract-OCR not found yet (may still be installing)")
        return False

def configure_environment():
    """Configure environment variables for Tesseract."""
    print_step("E", "Configuring environment...")
    
    tesseract_path = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
    tessdata_path = Path("C:/Program Files/Tesseract-OCR/tessdata")
    
    if not tesseract_path.exists():
        print("⚠ Tesseract path not found, skipping environment setup")
        return False
    
    try:
        # Set environment variables for current process
        os.environ['TESSERACT_CMD'] = str(tesseract_path)
        os.environ['TESSDATA_PREFIX'] = str(tessdata_path)
        
        print(f"✓ TESSERACT_CMD: {tesseract_path}")
        print(f"✓ TESSDATA_PREFIX: {tessdata_path}")
        
        # Try to set system environment variables (requires admin)
        try:
            subprocess.run(
                [
                    "setx",
                    "TESSERACT_CMD",
                    str(tesseract_path)
                ],
                check=True,
                capture_output=True
            )
            print("✓ System environment variables updated")
            print("  (You may need to restart your terminal/IDE)")
        except:
            print("⚠ Could not set system environment variables")
            print("  (No admin rights - that's OK, using process-level variables)")
        
        return True
    
    except Exception as e:
        print(f"✗ Environment configuration failed: {e}")
        return False

def test_ocr():
    """Test OCR functionality."""
    print_step("F", "Testing OCR functionality...")
    
    try:
        from src.ocr_processor import (
            verify_tesseract_installation,
            print_ocr_status,
            get_ocr_status
        )
        
        # Run verification
        if verify_tesseract_installation():
            print("\n✓ OCR system verification passed!")
            print_ocr_status()
            return True
        else:
            print("✗ OCR system verification failed")
            status = get_ocr_status()
            print(f"  Available: {status['ocr_available']}")
            return False
    
    except Exception as e:
        print(f"⚠ Could not test OCR: {e}")
        print("  (This is OK - may just mean src module isn't in path)")
        return None

def main():
    """Main installation flow."""
    print_header("TESSERACT-OCR INSTALLATION FOR MONITOR AI ASSISTANT")
    
    # Step 1: Check Python package
    print_step(1, "Checking for pytesseract Python package")
    if not check_pytesseract():
        if not install_pytesseract():
            print("\n✗ Installation failed - please run: pip install pytesseract")
            return False
    
    # Step 2: Check existing Tesseract
    print_step(2, "Checking for existing Tesseract installation")
    if check_tesseract():
        print("✓ Tesseract is already installed!")
        test_ocr()
        return True
    
    print("✗ Tesseract-OCR not found - proceeding with installation")
    
    # Step 3: Download installer
    installer = download_tesseract_installer()
    if not installer:
        print("\n✗ Could not obtain installer")
        print("  Please download manually from: https://github.com/UB-Mannheim/tesseract/releases")
        return False
    
    # Step 4: Run installer
    if not install_tesseract(installer):
        print("\n⚠ Installation may have failed")
        print("  Please check: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        return False
    
    # Step 5: Verify
    if not verify_installation():
        print("\n⚠ Verification incomplete - installation may still be processing")
        print("  Please wait a few moments and try again")
        return None
    
    # Step 6: Configure
    configure_environment()
    
    # Step 7: Test
    test_result = test_ocr()
    
    # Summary
    print_header("INSTALLATION SUMMARY")
    print("\n✓ Installation completed!")
    print("\nNext steps:")
    print("  1. Restart your terminal or IDE (VS Code)")
    print("  2. Run: python verify_setup.py")
    print("  3. Start using OCR in your Monitor AI Assistant")
    print("\nDocumentation: See TESSERACT_SETUP.md for detailed usage")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
