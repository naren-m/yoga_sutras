"""
Sandhi splitting service using Vidyut Cheda.

Provides tokenization and lemma lookup for Sanskrit text.
Accepts input in Devanagari, IAST, or SLP1 encoding.
"""
import os
import re
from typing import List, Dict, Any, Optional

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

try:
    from vidyut.vidyut import cheda
    VIDYUT_AVAILABLE = True
except ImportError:
    cheda = None
    VIDYUT_AVAILABLE = False


class SandhiService:
    """
    Service for splitting Sanskrit compounds and tokenizing text.

    Uses Vidyut Cheda for tokenization and lemma identification.
    Supports input in multiple scripts (Devanagari, IAST, SLP1).
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the sandhi service.

        Args:
            data_path: Path to vidyut-data directory. If None, uses default path.
        """
        self.chedaka = None
        self._init_error: Optional[str] = None

        if not VIDYUT_AVAILABLE:
            self._init_error = "Vidyut library not installed. Install with: pip install vidyut"
            return

        # Determine data path
        if data_path is None:
            # Default: data/vidyut-data from project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            data_path = os.path.join(project_root, 'data', 'vidyut-data')

        if not os.path.exists(data_path):
            self._init_error = f"Vidyut data not found at {data_path}. Run: python -c \"import vidyut; vidyut.download_data('{data_path}')\""
            return

        try:
            self.chedaka = cheda.Chedaka(data_path)
        except Exception as e:
            self._init_error = f"Failed to initialize Vidyut Cheda: {e}"

    def _detect_script(self, text: str) -> str:
        """
        Detect the script of the input text.

        Returns: 'DEVANAGARI', 'IAST', or 'SLP1'
        """
        # Check for Devanagari characters (Unicode range 0900-097F)
        if re.search(r'[\u0900-\u097F]', text):
            return 'DEVANAGARI'

        # Check for IAST diacritics (macrons, dots, tildes on letters)
        iast_chars = 'āīūṛṝḷḹṃḥñṅṭḍṇśṣĀĪŪṚṜḶḸṂḤÑṄṬḌṆŚṢ'
        if any(c in text for c in iast_chars):
            return 'IAST'

        # Default to SLP1 (ASCII-based transliteration)
        return 'SLP1'

    def _to_slp1(self, text: str) -> str:
        """Convert text from any supported script to SLP1."""
        script = self._detect_script(text)

        if script == 'DEVANAGARI':
            return transliterate(text, sanscript.DEVANAGARI, sanscript.SLP1)
        elif script == 'IAST':
            return transliterate(text, sanscript.IAST, sanscript.SLP1)
        else:
            return text

    def _to_devanagari(self, slp1_text: str) -> str:
        """Convert SLP1 to Devanagari for display."""
        return transliterate(slp1_text, sanscript.SLP1, sanscript.DEVANAGARI)

    def _to_iast(self, slp1_text: str) -> str:
        """Convert SLP1 to IAST for display."""
        return transliterate(slp1_text, sanscript.SLP1, sanscript.IAST)

    def split(self, text: str) -> Dict[str, Any]:
        """
        Split/tokenize a Sanskrit text into components.

        Args:
            text: Sanskrit text in Devanagari, IAST, or SLP1 encoding

        Returns:
            Dictionary with:
                - splits: List of token objects with text, lemma, and display forms
                - original: Original input
                - original_slp1: Input converted to SLP1
                - original_devanagari: Input converted to Devanagari
                - original_iast: Input converted to IAST
        """
        if not self.chedaka:
            # Return graceful fallback when engine not available
            slp1_text = self._to_slp1(text.strip())
            return {
                "splits": [{
                    "text": slp1_text,
                    "text_devanagari": self._to_devanagari(slp1_text),
                    "text_iast": self._to_iast(slp1_text),
                    "lemma": None,
                    "lemma_devanagari": None,
                    "lemma_iast": None,
                    "is_original": True
                }],
                "original": text,
                "original_slp1": slp1_text,
                "original_devanagari": self._to_devanagari(slp1_text),
                "original_iast": self._to_iast(slp1_text),
                "engine_available": False,
                "engine_error": self._init_error
            }

        # Convert input to SLP1 (Vidyut expects SLP1)
        slp1_text = self._to_slp1(text.strip())

        try:
            # Run tokenization
            tokens = self.chedaka.run(slp1_text)

            # Format results
            splits = []
            for token in tokens:
                token_text = token.text if token.text else ""
                token_lemma = token.lemma if token.lemma else None

                split_obj = {
                    "text": token_text,
                    "text_devanagari": self._to_devanagari(token_text) if token_text else "",
                    "text_iast": self._to_iast(token_text) if token_text else "",
                    "lemma": token_lemma,
                    "lemma_devanagari": self._to_devanagari(token_lemma) if token_lemma else None,
                    "lemma_iast": self._to_iast(token_lemma) if token_lemma else None,
                }
                splits.append(split_obj)

            return {
                "splits": splits,
                "original": text,
                "original_slp1": slp1_text,
                "original_devanagari": self._to_devanagari(slp1_text),
                "original_iast": self._to_iast(slp1_text),
                "engine_available": True,
                "engine_error": None
            }

        except Exception as e:
            # Graceful fallback on error - return original word
            return {
                "splits": [{
                    "text": slp1_text,
                    "text_devanagari": self._to_devanagari(slp1_text),
                    "text_iast": self._to_iast(slp1_text),
                    "lemma": None,
                    "lemma_devanagari": None,
                    "lemma_iast": None,
                    "is_original": True
                }],
                "original": text,
                "original_slp1": slp1_text,
                "original_devanagari": self._to_devanagari(slp1_text),
                "original_iast": self._to_iast(slp1_text),
                "engine_available": True,
                "engine_error": str(e)
            }

    def is_available(self) -> bool:
        """Check if the sandhi engine is available and initialized."""
        return self.chedaka is not None

    def get_status(self) -> Dict[str, Any]:
        """Get status information about the sandhi service."""
        return {
            "available": self.is_available(),
            "vidyut_installed": VIDYUT_AVAILABLE,
            "error": self._init_error
        }
