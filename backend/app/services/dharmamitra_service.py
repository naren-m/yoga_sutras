"""
Dharmamitra ByT5 Sanskrit Morphology Service

Provides Sanskrit morphological analysis using the Dharmamitra ByT5 model:
- Sandhi resolution (compound word segmentation)
- Lemmatization (finding root forms)
- Morphosyntactic analysis (case, gender, number, person)
- Meaning lookup (60K+ Sanskrit-English word mappings)

Reference: ../ramayanam/api/services/dharmamitra_service.py
"""

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# Common Sanskrit dhatus (verb roots) with their gana (verb class 1-10)
# This is a subset - a complete list would have 2000+ roots
DHATU_GANA_MAP: Dict[str, int] = {
    # Gana 1 (Bhvādi) - most common
    "bhū": 1, "gam": 1, "sthā": 1, "dā": 1, "pā": 1, "ji": 1, "nī": 1,
    "kṛ": 1, "hṛ": 1, "vad": 1, "pat": 1, "sad": 1, "jan": 1, "man": 1,
    "yuj": 1, "kram": 1, "ram": 1, "nam": 1, "labh": 1, "vṛt": 1, "śak": 1,
    "vas": 1, "has": 1, "paś": 1, "dṛś": 1, "spṛś": 1, "tyaj": 1, "bhaj": 1,
    # Gana 2 (Adādi)
    "as": 2, "i": 2, "vid": 2, "śī": 2, "han": 2, "vac": 2, "brū": 2,
    "ad": 2, "svap": 2, "śvas": 2, "rudh": 2, "dviṣ": 2, "duḥ": 2,
    # Gana 3 (Juhotyādi)
    "hu": 3, "dā": 3, "dhā": 3, "mā": 3, "hā": 3, "bibh": 3,
    # Gana 4 (Divādi)
    "div": 4, "nṛt": 4, "mad": 4, "kup": 4, "tṛp": 4, "muh": 4, "lubh": 4,
    "kliś": 4, "puṣ": 4, "tuṣ": 4, "kruś": 4, "śam": 4, "dam": 4, "jan": 4,
    # Gana 5 (Svādi)
    "su": 5, "śru": 5, "āp": 5, "ṛ": 5, "śak": 5, "kṣi": 5,
    # Gana 6 (Tudādi)
    "tud": 6, "viś": 6, "muc": 6, "lup": 6, "ric": 6, "sic": 6, "kṛṣ": 6,
    "liś": 6, "pṛc": 6, "spṛś": 6, "kir": 6, "gir": 6, "mil": 6, "pis": 6,
    # Gana 7 (Rudhādi)
    "rudh": 7, "bhid": 7, "chid": 7, "yuj": 7, "bhuj": 7, "añj": 7,
    "hiṃs": 7, "piṣ": 7, "ric": 7, "vic": 7,
    # Gana 8 (Tanādi)
    "tan": 8, "san": 8, "man": 8, "van": 8, "kṛ": 8,
    # Gana 9 (Kryādi)
    "krī": 9, "graha": 9, "jñā": 9, "pū": 9, "lū": 9, "stṛ": 9,
    "prī": 9, "math": 9, "puṣ": 9, "bandh": 9, "aś": 9,
    # Gana 10 (Curādi) - causatives and denominatives
    "cur": 10, "cint": 10, "kath": 10, "pāl": 10, "mantr": 10,
    "gup": 10, "dhūp": 10, "vic": 10, "pan": 10, "spardh": 10,
}


def lookup_gana(lemma: str) -> Optional[int]:
    """Look up the verb class (gana) for a dhatu/lemma."""
    if not lemma:
        return None
    # Normalize: try both as-is and without final 'a' (common lemma form)
    clean_lemma = lemma.strip().lower()
    if clean_lemma in DHATU_GANA_MAP:
        return DHATU_GANA_MAP[clean_lemma]
    # Try removing trailing 'a' (e.g., "gaccha" -> "gacch")
    if clean_lemma.endswith('a') and len(clean_lemma) > 1:
        base = clean_lemma[:-1]
        if base in DHATU_GANA_MAP:
            return DHATU_GANA_MAP[base]
    return None


@dataclass
class MorphologicalAnalysis:
    """Structured morphological analysis result for a single word"""
    lemma: str              # Base/dictionary form
    unsandhied: str         # Form after sandhi splitting
    surface_form: str       # Original inflected form
    tag: str                # Morphological tags (Case=X|Gender=Y|Number=Z)
    meanings: List[str]     # English meanings from Dharmamitra
    confidence: float = 1.0

    # Parsed tag components for easy access
    case: Optional[str] = None
    gender: Optional[str] = None
    number: Optional[str] = None
    person: Optional[str] = None
    tense: Optional[str] = None
    voice: Optional[str] = None

    # Verb-specific fields
    dhatu: Optional[str] = None  # Verb root
    gana: Optional[int] = None   # Verb class (1-10)
    is_verb: bool = False

    def __post_init__(self):
        """Parse morphological tags into individual components"""
        if self.tag:
            self._parse_tag()

    def _parse_tag(self):
        """Parse tag string like 'Case=Nominative|Gender=Masculine|Number=Singular'"""
        for part in self.tag.split('|'):
            if '=' in part:
                key, value = part.split('=', 1)
                key_lower = key.lower()
                if key_lower == 'case':
                    self.case = value
                elif key_lower == 'gender':
                    self.gender = value
                elif key_lower == 'number':
                    self.number = value
                elif key_lower == 'person':
                    self.person = value
                    self.is_verb = True
                elif key_lower == 'tense':
                    self.tense = value
                    self.is_verb = True
                elif key_lower == 'voice':
                    self.voice = value
                    self.is_verb = True

        # For verb forms, set dhatu (root) and look up gana (verb class)
        if self.is_verb and self.lemma:
            self.dhatu = self.lemma
            self.gana = lookup_gana(self.lemma)


@dataclass
class SentenceAnalysis:
    """Complete morphological analysis for a sentence/verse"""
    sentence: str
    words: List[MorphologicalAnalysis]
    processing_mode: str
    cache_hit: bool = False


class DharmamitraMorphologyService:
    """
    Dharmamitra ByT5 Sanskrit morphological analysis service

    Features:
    - Lazy initialization (processor loaded on first use)
    - LRU caching for repeated lookups
    - Graceful fallback when model unavailable
    """

    _instance = None
    _processor = None
    _initialized = False

    def __new__(cls):
        """Singleton pattern - only one instance of the service"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize service (lazy - processor loaded on first use)"""
        pass

    def _ensure_initialized(self) -> bool:
        """Initialize processor on first use"""
        if self._initialized:
            return self._processor is not None

        self._initialized = True

        try:
            import urllib3
            from dharmamitra_sanskrit_grammar import DharmamitraSanskritProcessor

            # Disable SSL warnings for Dharmamitra API
            urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

            self._processor = DharmamitraSanskritProcessor()
            logger.info("Dharmamitra ByT5 processor initialized successfully")
            return True

        except ImportError as e:
            logger.warning(
                f"Dharmamitra not installed: {e}. "
                "Install with: pip install dharmamitra-sanskrit-grammar"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Dharmamitra processor: {e}")
            return False

    def is_available(self) -> bool:
        """Check if Dharmamitra service is available"""
        return self._ensure_initialized()

    @lru_cache(maxsize=1000)
    def analyze_word(
        self,
        word: str,
        mode: str = "unsandhied-lemma-morphosyntax"
    ) -> Optional[MorphologicalAnalysis]:
        """
        Analyze a single Sanskrit word

        Args:
            word: Sanskrit word (Devanagari or IAST)
            mode: Processing mode
                - "lemma": Basic lemmatization only
                - "unsandhied": Word segmentation
                - "unsandhied-lemma-morphosyntax": Full analysis (default)

        Returns:
            MorphologicalAnalysis or None if unavailable
        """
        if not word or not word.strip():
            return None

        if not self._ensure_initialized():
            return None

        try:
            results = self._processor.process_batch(
                [word.strip()],
                mode=mode,
                human_readable_tags=True
            )

            if not results or len(results) == 0:
                logger.debug(f"No Dharmamitra results for word: {word}")
                return None

            result_data = results[0]
            analyses = result_data.get("grammatical_analysis", [])

            if not analyses:
                return None

            # Get first word analysis
            word_data = analyses[0]

            analysis = MorphologicalAnalysis(
                lemma=word_data.get("lemma", ""),
                unsandhied=word_data.get("unsandhied", word),
                surface_form=word,
                tag=word_data.get("tag", ""),
                meanings=word_data.get("meanings", []),
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing word '{word}' with Dharmamitra: {e}")
            return None

    def analyze_text(
        self,
        text: str,
        mode: str = "unsandhied-lemma-morphosyntax"
    ) -> Optional[SentenceAnalysis]:
        """
        Analyze Sanskrit text (sentence/verse)

        Args:
            text: Sanskrit text
            mode: Processing mode

        Returns:
            SentenceAnalysis with word-by-word analysis
        """
        if not text or not text.strip():
            return None

        if not self._ensure_initialized():
            return None

        try:
            results = self._processor.process_batch(
                [text.strip()],
                mode=mode,
                human_readable_tags=True
            )

            if not results or len(results) == 0:
                return None

            result_data = results[0]
            words = []

            for word_data in result_data.get("grammatical_analysis", []):
                analysis = MorphologicalAnalysis(
                    lemma=word_data.get("lemma", ""),
                    unsandhied=word_data.get("unsandhied", ""),
                    surface_form=word_data.get("unsandhied", ""),
                    tag=word_data.get("tag", ""),
                    meanings=word_data.get("meanings", []),
                )
                words.append(analysis)

            return SentenceAnalysis(
                sentence=text,
                words=words,
                processing_mode=mode,
                cache_hit=False
            )

        except Exception as e:
            logger.error(f"Error analyzing text with Dharmamitra: {e}")
            return None

    def get_word_meanings(self, word: str) -> List[str]:
        """
        Get English meanings for a Sanskrit word

        Args:
            word: Sanskrit word

        Returns:
            List of English meanings
        """
        analysis = self.analyze_word(word)
        if analysis and analysis.meanings:
            return analysis.meanings
        return []

    def clear_cache(self):
        """Clear the LRU cache"""
        self.analyze_word.cache_clear()
        logger.info("Dharmamitra cache cleared")


# Singleton instance
_dharmamitra_service: Optional[DharmamitraMorphologyService] = None


def get_dharmamitra_service() -> DharmamitraMorphologyService:
    """Get or create the Dharmamitra service singleton"""
    global _dharmamitra_service
    if _dharmamitra_service is None:
        _dharmamitra_service = DharmamitraMorphologyService()
    return _dharmamitra_service
