import unittest
import requests
import time
from unittest.mock import patch, MagicMock

class TestVoiceAgent(unittest.TestCase):
    def setUp(self):
        self.nlweb_url = "http://localhost:8000"
        
    def test_nlweb_connection(self):
        """Test NLWeb server connectivity"""
        try:
            response = requests.get(f"{self.nlweb_url}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
        except requests.exceptions.RequestException:
            self.fail("Cannot connect to NLWeb server")
    
    def test_query_processing(self):
        """Test basic query processing"""
        test_query = "What is artificial intelligence?"
        
        payload = {"question": test_query}
        response = requests.post(
            f"{self.nlweb_url}/api/ask",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("answer", result)
        self.assertTrue(len(result["answer"]) > 0)
    
    @patch('speech_recognition.Recognizer')
    def test_speech_recognition_mock(self, mock_recognizer):
        """Test speech recognition with mock"""
        mock_recognizer.return_value.recognize_google.return_value = "test query"
        
        # This would test your voice agent's speech processing
        # Implementation depends on your specific voice agent class
        pass

if __name__ == '__main__':
    unittest.main()
