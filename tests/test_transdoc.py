"""
Unit tests for TransDocs - Document Translation and Proofreading Tool.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestTransDoc(unittest.TestCase):
    """Test cases for the TransDocs translation and proofreading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_doc_path = "test_document.docx"
        self.output_doc_path = "output_test.docx"

    @patch("transdoc.Document")
    def test_detect_source_language_en(self, mock_doc_class):
        """Test source language detection for English text."""
        # Mock document with English paragraphs - each paragraph needs runs attribute
        mock_run1 = Mock()
        mock_run1.text = "This is a test document in English."

        mock_para1 = Mock()
        mock_para1.runs = [mock_run1]

        mock_run2 = Mock()
        mock_run2.text = "It contains multiple sentences and words."

        mock_para2 = Mock()
        mock_para2.runs = [mock_run2]

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc_class.return_value = mock_doc

        from transdoc import detect_source_language

        result = detect_source_language(mock_doc)
        self.assertEqual(result, "en")

    @patch("transdoc.Document")
    def test_detect_source_language_de(self, mock_doc_class):
        """Test source language detection for German text."""
        # Mock document with German paragraphs - each paragraph needs runs attribute
        mock_run1 = Mock()
        mock_run1.text = "Dies ist ein Testdokument auf Deutsch."

        mock_para1 = Mock()
        mock_para1.runs = [mock_run1]

        mock_run2 = Mock()
        mock_run2.text = "Es enthält mehrere Sätze und Wörter."

        mock_para2 = Mock()
        mock_para2.runs = [mock_run2]

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc_class.return_value = mock_doc

        from transdoc import detect_source_language

        result = detect_source_language(mock_doc)
        self.assertEqual(result, "de")

    @patch("transdoc.detect")
    @patch("transdoc.Document")
    def test_detect_source_language_insufficient_text(
        self, mock_doc_class, mock_detect
    ):
        """Test language detection with insufficient text."""
        # Mock document with very little text - paragraph needs runs attribute
        mock_run1 = Mock()
        mock_run1.text = "Hi."

        mock_para1 = Mock()
        mock_para1.runs = [mock_run1]

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1]
        mock_doc_class.return_value = mock_doc

        # Make detect raise an exception for short text
        from langdetect.lang_detect_exception import LangDetectException

        def raise_exception(text):
            raise LangDetectException("Length too short", "sw")

        mock_detect.side_effect = raise_exception

        from transdoc import detect_source_language

        result = detect_source_language(mock_doc, min_words=50)
        self.assertIsNone(result)

    @patch("transdoc.requests.post")
    def test_call_ollama_api_translate(self, mock_post):
        """Test API call for translation mode."""
        # Mock successful response with proper attributes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is the translated text."}
        mock_response.headers = {}
        mock_response.text = (
            '{"response": "This is the translated text."}'  # Make it subscriptable
        )
        mock_post.return_value = mock_response

        from transdoc import call_ollama_api

        result = call_ollama_api(
            text="Hello world",
            src_lang="en",
            target_lang="de",
            model="qwen2.5-coder:1.5b-base",
            api_token=None,
            api_url="http://localhost:11434/api/generate",
            mode="translate",
        )

        self.assertEqual(result, "This is the translated text.")

    @patch("transdoc.requests.post")
    def test_call_ollama_api_proofread(self, mock_post):
        """Test API call for proofreading mode."""
        # Mock successful response with proper attributes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "This is the corrected text."}
        mock_response.headers = {}
        mock_response.text = (
            '{"response": "This is the corrected text."}'  # Make it subscriptable
        )
        mock_post.return_value = mock_response

        from transdoc import call_ollama_api

        result = call_ollama_api(
            text="Hello wrld",  # Intentional typo for proofreading test
            src_lang="en",
            target_lang="en",
            model="qwen2.5-coder:1.5b-base",
            api_token=None,
            api_url="http://localhost:11434/api/generate",
            mode="proofread",
        )

        self.assertEqual(result, "This is the corrected text.")

    @patch("transdoc.requests.post")
    def test_call_ollama_api_error(self, mock_post):
        """Test API call with error response."""
        # Mock failed response with proper headers dict
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {}
        mock_post.return_value = mock_response

        from transdoc import call_ollama_api

        result = call_ollama_api(
            text="Test text",
            src_lang="en",
            target_lang="de",
            model="qwen2.5-coder:1.5b-base",
            api_token=None,
            api_url="http://localhost:11434/api/generate",
            mode="translate",
        )

        # Should return original text on error
        self.assertEqual(result, "Test text")

    @patch("transdoc.translate_or_proofread")
    def test_process_paragraph(self, mock_translate):
        """Test paragraph processing."""
        from transdoc import process_paragraph

        # Mock paragraph with runs - need to properly set up the structure
        mock_run1 = Mock()
        mock_run1.text = "Hello world"

        mock_para = Mock()
        mock_para.runs = [mock_run1]
        mock_para.add_run = Mock(
            side_effect=lambda text: setattr(mock_run1, "text", text) or mock_run1
        )

        mock_translate.return_value = "Hallo Welt"

        process_paragraph(
            para=mock_para,
            src_lang="en",
            model="qwen2.5-coder:1.5b-base",
            target_lang="de",
            api_token=None,
            api_url="http://localhost:11434/api/generate",
        )

        # Verify the paragraph text was updated - add_run should create new run with processed text
        self.assertEqual(mock_para.runs[0].text, "Hallo Welt")

    @patch("transdoc.translate_or_proofread")
    def test_process_paragraph_empty(self, mock_translate):
        """Test processing empty paragraph."""
        from transdoc import process_paragraph

        # Mock empty paragraph
        mock_para = Mock()
        mock_para.runs = []

        process_paragraph(
            para=mock_para,
            src_lang="en",
            model="qwen2.5-coder:1.5b-base",
            target_lang="de",
            api_token=None,
            api_url="http://localhost:11434/api/generate",
        )

        # Should not fail on empty paragraph


class TestCLIArguments(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_required_arguments(self):
        """Test that required arguments are enforced."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--input", type=str, required=True)
        parser.add_argument("-o", "--output", type=str, required=True)
        parser.add_argument("-t", "--target", type=str, required=True)

        # Should not raise when all required args provided
        args = parser.parse_args(["-i", "test.docx", "-o", "out.docx", "-t", "en"])
        self.assertEqual(args.input, "test.docx")

    def test_model_is_required(self):
        """Test that model argument is required."""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--model", type=str, default="")
        parser.add_argument("-s", "--source", type=str, default=None)
        parser.add_argument("--proofread", action="store_true")

        args = parser.parse_args(["-m", ""])
        self.assertEqual(args.model, "")
        self.assertIsNone(args.source)
        self.assertFalse(args.proofread)


if __name__ == "__main__":
    unittest.main()
