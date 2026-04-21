from ocr_module import image_to_text
import unittest
import os

class TestOCRModule(unittest.TestCase):

    def test_image_to_text_valid_image(self):
        # Assuming there's a sample image with known text for testing
        test_image_path = 'tests/sample_image.png'
        expected_text = 'Hello, World!'  # Replace with the actual expected text
        result = image_to_text(test_image_path)
        self.assertEqual(result.strip(), expected_text)

    def test_image_to_text_invalid_image(self):
        invalid_image_path = 'tests/invalid_image.png'
        result = image_to_text(invalid_image_path)
        self.assertEqual(result.strip(), '')

    def test_image_to_text_non_existent_image(self):
        non_existent_image_path = 'tests/non_existent_image.png'
        with self.assertRaises(FileNotFoundError):
            image_to_text(non_existent_image_path)

if __name__ == '__main__':
    unittest.main()