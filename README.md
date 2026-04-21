# Monitor AI Assistant

## Overview
The Monitor AI Assistant is a Python application designed to capture information from one monitor, process it using Paddle OCR, and provide answers to questions or problems on a second monitor. This tool leverages advanced AI capabilities to interpret and respond to user queries based on the captured text.

## Features
- Screen capture from a specified monitor.
- Optical Character Recognition (OCR) using Paddle OCR to extract text from images.
- AI-driven responses to user queries based on the extracted text.
- User-friendly interface to display answers on a separate monitor.

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Steps
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/monitor-ai-assistant.git
   cd monitor-ai-assistant
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```
   python src/main.py
   ```

2. The application will start capturing the screen of the specified monitor at defined intervals. It will process the captured images to extract text and query the AI model for answers.

3. The answers will be displayed in the AnswerWindow on the second monitor.

## Testing
To run the tests for the application, navigate to the `tests` directory and execute:
```
pytest
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.