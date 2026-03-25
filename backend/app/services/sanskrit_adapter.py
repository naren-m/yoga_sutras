"""Unified Sanskrit analysis adapter for Yoga Sutras.

This adapter wraps the sanskrit_analyzer library, providing both async
and sync interfaces for integration with the Yoga Sutras application.
"""

from sanskrit_analyzer import Analyzer, Config, AnalysisMode
from sanskrit_analyzer.models import AnalysisTree, SandhiGroup
import asyncio
import logging

logger = logging.getLogger(__name__)


class SanskritAdapter:
    """Unified Sanskrit analysis for Yoga Sutras.

    Provides lazy initialization and both async/sync interfaces
    for Sanskrit text analysis, sandhi splitting, and dictionary lookup.
    """

    def __init__(self):
        self._analyzer = None

    @property
    def analyzer(self) -> Analyzer:
        """Lazy initialization - expensive to create."""
        if self._analyzer is None:
            try:
                self._analyzer = Analyzer(Config())
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
                    tokens.append({
                        "text": word.form,
                        "lemma": word.lemma or word.form,
                        "text_devanagari": word.form,
                        "lemma_devanagari": word.lemma or word.form,
                    })

            return {
                "splits": tokens,
                "original": {
                    "input": compound,
                    "devanagari": compound,
                    "iast": compound,
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

    async def get_morphology(self, word: str) -> dict | None:
        """Get morphological analysis for a word."""
        result = await self.analyzer.analyze(word, mode=AnalysisMode.EDUCATIONAL)
        if not result.parse_forest or not result.parse_forest[0].sandhi_groups:
            return None

        first_word = result.parse_forest[0].sandhi_groups[0].base_words[0]
        morph = first_word.morphology

        if not morph:
            return None

        return {
            "lemma": first_word.lemma or first_word.form,
            "unsandhied": first_word.form,
            "surface_form": first_word.form,
            "tag": self._build_tag(morph),
            "case": morph.case.value if morph.case else None,
            "gender": morph.gender.value if morph.gender else None,
            "number": morph.number.value if morph.number else None,
            "person": morph.person.value if morph.person else None,
            "tense": morph.tense.value if morph.tense else None,
            "voice": morph.voice.value if morph.voice else None,
            "meanings": [m.definition for m in morph.meanings if m.definition] if morph.meanings else [],
            "is_verb": morph.tense is not None or morph.person is not None,
            "dhatu": first_word.dhatu_info.dhatu if first_word.dhatu_info else None,
            "gana": first_word.dhatu_info.gana.value if first_word.dhatu_info and first_word.dhatu_info.gana else None,
        }

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
