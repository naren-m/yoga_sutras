"""Unified Sanskrit analysis adapter for Yoga Sutras.

This adapter wraps the sanskrit_analyzer library, providing both async
and sync interfaces for integration with the Yoga Sutras application.
"""

import asyncio
import logging

from sanskrit_analyzer import Analyzer, Config, AnalysisMode
from sanskrit_analyzer.models import AnalysisTree, SandhiGroup
from sanskrit_analyzer.models.scripts import Script
from sanskrit_analyzer.utils import detect_script, to_devanagari, to_iast

logger = logging.getLogger(__name__)


def _slp1_to_devanagari(text: str) -> str:
    """Convert analyzer-internal SLP1 to Devanagari for display."""
    try:
        return to_devanagari(text, Script.SLP1)
    except Exception:
        return text


def _slp1_to_iast(text: str) -> str:
    """Convert analyzer-internal SLP1 to IAST for display."""
    try:
        return to_iast(text, Script.SLP1)
    except Exception:
        return text


def _display_forms(text: str) -> tuple[str, str]:
    """Convert an engine-produced word to (IAST, Devanagari) display forms.

    Engine output script varies by pipeline: vidyut yields internal SLP1
    ("vftti", "Bavati", "BU") while ByT5 yields IAST ("vṛtti", "anuśāsanam").
    Detect per word; for ambiguous plain ASCII, any uppercase letter marks
    SLP1 (aspirates/long vowels: B, T, A) since engine IAST is always
    lowercase, while all-lowercase reads as IAST — treating "atha" as SLP1
    would produce अत्ह instead of अथ.
    """
    try:
        ascii_default = (
            Script.SLP1 if text.isascii() and any(c.isupper() for c in text)
            else Script.IAST
        )
        script = detect_script(text, plain_ascii_default=ascii_default)
        return to_iast(text, script), to_devanagari(text, script)
    except Exception:
        return text, text


class SanskritAdapter:
    """Unified Sanskrit analysis for Yoga Sutras.

    Provides lazy initialization and both async/sync interfaces
    for Sanskrit text analysis, sandhi splitting, and dictionary lookup.
    """

    def __init__(self, config: Config | None = None):
        self._analyzer = None
        self._config = config

    @property
    def analyzer(self) -> Analyzer:
        """Lazy initialization - expensive to create."""
        if self._analyzer is None:
            try:
                self._analyzer = Analyzer(self._config or Config())
            except Exception as e:
                logger.error(f"Failed to initialize Analyzer: {e}")
                raise
        return self._analyzer

    def is_available(self) -> bool:
        """Check if the analyzer is available."""
        try:
            return self.analyzer is not None
        except Exception:
            return False

    async def split_sandhi(self, compound: str) -> list[SandhiGroup]:
        """Split compound word with sandhi analysis."""
        result = await self.analyzer.analyze(compound, mode=AnalysisMode.EDUCATIONAL)
        return result.parse_forest[0].sandhi_groups if result.parse_forest else []

    def split_sandhi_sync(self, compound: str) -> list[SandhiGroup]:
        """Sync wrapper for Flask routes without async support."""
        return asyncio.run(self.split_sandhi(compound))

    def split(self, compound: str) -> dict:
        """Split compound word and return backwards-compatible dict format.

        Returns dict matching the old SandhiService.split() response format.
        """
        try:
            groups = self.split_sandhi_sync(compound)

            tokens = []
            for sg in groups:
                for word in sg.base_words:
                    surface_iast, surface_dev = _display_forms(word.surface_form)
                    lemma_iast, lemma_dev = _display_forms(word.lemma or word.surface_form)
                    tokens.append({
                        "text": surface_iast,
                        "lemma": lemma_iast,
                        "text_devanagari": surface_dev,
                        "lemma_devanagari": lemma_dev,
                    })

            try:
                input_script = detect_script(compound)
                original_dev = to_devanagari(compound, input_script)
                original_iast = to_iast(compound, input_script)
            except Exception:
                original_dev = original_iast = compound

            return {
                "splits": tokens,
                "original": {
                    "input": compound,
                    "devanagari": original_dev,
                    "iast": original_iast,
                },
                "engine_available": True,
            }
        except Exception as e:
            logger.error(f"Error splitting compound: {e}")
            return {
                "splits": [],
                "original": {"input": compound},
                "engine_available": False,
                "error": str(e),
            }

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "available": self.is_available(),
            "service": "sanskrit_analyzer",
            "error": None,
        }

    async def analyze_word(self, word: str) -> dict:
        """Full word analysis for ClickableWord component."""
        result = await self.analyzer.analyze(word, mode=AnalysisMode.EDUCATIONAL)
        if not result.parse_forest:
            return {'word': word, 'analysis': None}

        first_parse = result.parse_forest[0]
        return {
            'word': word,
            'confidence': result.confidence.overall if result.confidence else 0.0,
            'sandhi_groups': [
                sg.to_dict() if hasattr(sg, 'to_dict') else {'words': [w.lemma for w in sg.base_words]}
                for sg in first_parse.sandhi_groups
            ]
        }

    def analyze_word_sync(self, word: str) -> dict:
        """Sync wrapper for Flask routes without async support."""
        return asyncio.run(self.analyze_word(word))

    def _word_entry(self, word) -> dict:
        """Build the display-script analysis dict for one BaseWord."""
        morph = word.morphology
        lemma = word.lemma or word.surface_form

        # Pipeline never populates BaseWord.dhatu; fall back to the
        # analyzer's dhatu DB keyed by the lemma.
        dhatu_info = word.dhatu or self.analyzer.lookup_dhatu(lemma)
        dhatu_slp1 = dhatu_info.dhatu if dhatu_info else None
        dhatu = dhatu_slp1
        if dhatu and dhatu.isascii():
            dhatu = _slp1_to_iast(dhatu)
        morph_meanings = getattr(morph, "meanings", None) if morph else None
        gana = None
        if dhatu_info and dhatu_info.gana is not None:
            gana = getattr(dhatu_info.gana, "value", dhatu_info.gana)

        lemma_iast, lemma_dev = _display_forms(lemma)
        surface_iast, surface_dev = _display_forms(word.surface_form)

        # Even without morphology or a dhatu hit, a successful parse still
        # yields a useful lemma for the frontend to display.
        return {
            "lemma": lemma_iast,
            "lemma_devanagari": lemma_dev,
            "surface_form": surface_iast,
            "surface_devanagari": surface_dev,
            "tag": self._build_tag(morph) if morph else "",
            "case": morph.case.value if morph and morph.case else None,
            "gender": morph.gender.value if morph and morph.gender else None,
            "number": morph.number.value if morph and morph.number else None,
            "person": morph.person.value if morph and morph.person else None,
            "tense": morph.tense.value if morph and morph.tense else None,
            "voice": morph.voice.value if morph and morph.voice else None,
            "meanings": (
                [m.definition for m in morph_meanings if m.definition]
                if morph_meanings
                else (list(dhatu_info.meanings) if dhatu_info and dhatu_info.meanings else [])
            ),
            "is_verb": (morph.tense is not None or morph.person is not None) if morph else dhatu_info is not None,
            "dhatu": dhatu,
            "dhatu_slp1": dhatu_slp1 if dhatu_slp1 and dhatu_slp1.isascii() else None,
            "gana": gana,
        }

    @staticmethod
    def _merge_privative(words: list[dict]) -> list[dict]:
        """Rejoin a split privative prefix (a-/an-) with the following word.

        Segmenters decompose e.g. akliṣṭāḥ into 'a' + 'kliṣṭāḥ'. That is
        morphologically defensible but pedagogically misleading — the
        negated stem is one lexical unit with its own dictionary entry
        ('akliṣṭa' = non-afflicted, opposite of kliṣṭa). Merge them and
        clear meanings so the enricher looks up the negated stem itself.
        """
        merged: list[dict] = []
        i = 0
        while i < len(words):
            word = words[i]
            if word.get("surface_form") in ("a", "an") and i + 1 < len(words):
                nxt = words[i + 1]
                combined = dict(nxt)
                surface = word["surface_form"] + nxt["surface_form"]
                # Negated compounds are a-stem nominals; the joined verb-root
                # lemma ('a'+'kliś') is not a word — stem the surface instead
                # (akliṣṭāḥ -> akliṣṭa), which is the dictionary headword.
                lemma = surface.rstrip("ḥṃ")
                if lemma.endswith("ā"):
                    lemma = lemma[:-1] + "a"
                combined["surface_form"], combined["surface_devanagari"] = _display_forms(surface)
                combined["lemma"], combined["lemma_devanagari"] = _display_forms(lemma)
                combined["meanings"] = []
                merged.append(combined)
                i += 2
                continue
            merged.append(word)
            i += 1
        return merged

    async def get_morphology(self, word: str) -> dict | None:
        """Get morphological analysis for a word."""
        result = await self.analyzer.analyze(word, mode=AnalysisMode.EDUCATIONAL)
        if not result.parse_forest or not result.parse_forest[0].sandhi_groups:
            return None

        first_word = result.parse_forest[0].sandhi_groups[0].base_words[0]
        entry = self._word_entry(first_word)
        entry["unsandhied"] = entry["surface_form"]
        return entry

    async def analyze_block(self, text: str) -> dict | None:
        """Word-by-word analysis of a whole block (sutra line).

        Produces the word_analysis JSON stored on TextBlock: one entry per
        unsandhied word, in display scripts, ready to render as an inline
        gloss without any per-word API calls.
        """
        result = await self.analyzer.analyze(text, mode=AnalysisMode.EDUCATIONAL)
        if not result.parse_forest:
            return None

        parse = result.parse_forest[0]
        words = []
        for sg in parse.sandhi_groups:
            for word in sg.base_words:
                words.append(self._word_entry(word))
        words = self._merge_privative(words)
        if not words:
            return None

        return {
            "source": "sanskrit_analyzer",
            "confidence": result.confidence.overall if result.confidence else None,
            "words": words,
        }

    def analyze_block_sync(self, text: str) -> dict | None:
        """Sync wrapper for scripts and Flask routes."""
        return asyncio.run(self.analyze_block(text))

    def get_morphology_sync(self, word: str) -> dict | None:
        """Sync wrapper for morphology lookup."""
        return asyncio.run(self.get_morphology(word))

    def _build_tag(self, morph) -> str:
        """Build morphological tag string from MorphologicalTag."""
        parts = []
        if morph.case:
            parts.append(f"Case={morph.case.value}")
        if morph.gender:
            parts.append(f"Gender={morph.gender.value}")
        if morph.number:
            parts.append(f"Number={morph.number.value}")
        if morph.person:
            parts.append(f"Person={morph.person.value}")
        if morph.tense:
            parts.append(f"Tense={morph.tense.value}")
        if morph.voice:
            parts.append(f"Voice={morph.voice.value}")
        return "|".join(parts) if parts else ""

    def dictionary_lookup(self, word: str) -> list[dict]:
        """Multi-source dictionary lookup."""
        return self.analyzer.dictionary_lookup(word)


# Global singleton instance for easy import
_adapter_instance = None


def get_sanskrit_adapter() -> SanskritAdapter:
    """Get or create the global SanskritAdapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = SanskritAdapter()
    return _adapter_instance
