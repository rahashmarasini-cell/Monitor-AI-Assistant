# PyInstaller hook for PaddleOCR
# Ensures all necessary data files and models are included in the frozen package.

from PyInstaller.utils.hooks import collect_data_files

# Collect all data files from paddleocr package
datas = collect_data_files('paddleocr')
