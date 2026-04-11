"""
TransDocs - Document Translation and Proofreading Tool

A Python tool for translating Microsoft Word documents using the Ollama API.
Supports automatic language detection, professional translation quality,
and proofreading capabilities.
"""

__version__ = "1.2.0"
__author__ = "Wes Moskal-Fitzpatrick (adapted)"

from .transdoc import (
    detect_source_language,
    call_ollama_api,
    translate_or_proofread,
    process_document,
)

__all__ = [
    "detect_source_language",
    "call_ollama_api",
    "translate_or_proofread",
    "process_document",
]
