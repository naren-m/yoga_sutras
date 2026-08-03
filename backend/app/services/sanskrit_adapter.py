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

from app.services.dhatu_resolver import get_dhatu_resolver

logger = logging.getLogger(__name__)


def _ascii_default(text: str) -> Script:
    """Disambiguate plain-ASCII script the same way _display_forms does:
    any uppercase marks SLP1 (aspirates/long vowels), else IAST."""
    return (
        Script.SLP1 if text.isascii() and any(c.isupper() for c in text)
        else Script.IAST
    )


def _to_slp1(text: str) -> str:
    """Convert an engine-produced word to SLP1 for Kośa/dhātu lookup."""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        script = detect_script(text, plain_ascii_default=_ascii_default(text))
        if script == Script.SLP1:
            return text
        src = sanscript.IAST if script == Script.IAST else sanscript.DEVANAGARI
        return transliterate(text, src, sanscript.SLP1)
    except Exception:
        return text


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
        script = detect_script(text, plain_ascii_default=_ascii_default(text))
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

        morph_meanings = getattr(morph, "meanings", None) if morph else None

        lemma_iast, lemma_dev = _display_forms(lemma)
        surface_iast, surface_dev = _display_forms(word.surface_form)

        entry = {
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
            "meanings": [m.definition for m in morph_meanings if m.definition] if morph_meanings else [],
            "is_verb": (morph.tense is not None or morph.person is not None) if morph else False,
        }
        self._attach_dhatu(entry, word.surface_form, lemma)
        return entry

    def _attach_dhatu(self, entry: dict, surface: str, lemma: str) -> None:
        """Populate root fields via the vidyut-Kośa dhātu resolver.

        Recovers the root even for derived nominals (yoga -> √yuj), with the
        root's own Sanskrit gloss and any prefixes (nirodha -> ni + √rudh).
        Leaves everything null for particles/pronouns that have no root.
        """
        entry.setdefault("dhatu", None)
        entry.setdefault("dhatu_slp1", None)
        entry.setdefault("dhatu_devanagari", None)
        entry.setdefault("dhatu_meaning", None)
        entry.setdefault("dhatu_meaning_en", None)
        entry.setdefault("dhatu_prefixes", [])
        entry.setdefault("dhatu_verified", False)
        entry.setdefault("gana", None)

        # A word the engine gave a case to is a nominal, and its lemma is the
        # form to ask about: asking with the inflection first let case endings
        # choose the reading, so viṣayam matched a vi+√siv 'to sew' krdanta
        # and viṣayā matched √viṣ 'to sprinkle' — one word, three etymologies
        # across the text. A finite verb has no case and keeps surface-first,
        # since only the inflected form carries its root (gacchati -> √gam).
        # Either way the resolver falls back to peeling a canonical prefix
        # when the Kośa has no dhātu link for the prefixed stem itself
        # (anuśāsana -> anu + √śās).
        resolver = get_dhatu_resolver()
        if resolver.is_rootless(_to_slp1(surface), _to_slp1(lemma)):
            return  # particle or pronoun — no root, and no fallback either
        cited = self._cited_root(lemma) or self._cited_root(surface)
        info = resolver.resolve(
            _to_slp1(surface), _to_slp1(lemma), preferred_root=cited,
        )
        if not info and cited:
            # The Kośa has no derivation for this stem, but the dictionary
            # names its root outright (karman -> √kṛ, and taddhita forms the
            # Kośa does not analyse at all).
            info = resolver.describe_root(cited)
        if not info:
            return
        root = info["root_slp1"]
        # The Kośa sometimes derives a stem from something that is not in the
        # Dhātupāṭha at all (artha, guṇa, kāla). Those are stems, not roots —
        # showing them as √artha teaches the reader something false, so a root
        # must be attested somewhere: the Dhātupāṭha index, or MW naming it
        # for this very word (√vic is a real root the index happens to lack).
        if not info["verified"] and root != cited:
            return
        entry["dhatu_slp1"] = root
        entry["dhatu"] = _slp1_to_iast(root)
        entry["dhatu_devanagari"] = _slp1_to_devanagari(root)
        entry["dhatu_prefixes"] = [_slp1_to_iast(p) for p in info["prefixes_slp1"]]
        entry["dhatu_verified"] = info["verified"]
        entry["gana"] = info["gana"]
        # Trust the resolver's verb flag only when the engine didn't already
        # give the word nominal morphology (a case) — otherwise a noun that
        # happens to share a surface with a finite verb gets mislabeled.
        if info.get("is_verb") and not entry.get("case"):
            entry["is_verb"] = True
        if info.get("artha_slp1"):
            entry["dhatu_meaning"] = _slp1_to_iast(info["artha_slp1"])
        entry["dhatu_meaning_en"] = self._root_gloss_en(root, info["gana"])

    @staticmethod
    def _cited_root(word: str) -> str | None:
        """Root MW names for this word, if the dictionary is reachable."""
        try:
            from app.services.dictionary_service import DictionaryService

            return DictionaryService().get_cited_root(_to_slp1(word))
        except Exception:  # no app context / dictionaries not seeded
            return None

    @staticmethod
    def _root_gloss_en(root_slp1: str, gana: int | None) -> str | None:
        """English sense of the root from MW, e.g. √yuj -> 'to yoke or join'.

        The Dhātupāṭha artha carried by the Kośa is Sanskrit ('saṃyamane'),
        which is opaque to the reader this gloss is for. Best-effort: needs a
        Flask app context and a seeded dictionary, and returns None without
        them so analysis still works in bare unit tests.
        """
        try:
            from app.services.dictionary_service import DictionaryService

            return DictionaryService().get_root_gloss(root_slp1, gana)
        except Exception:  # no app context / dictionaries not seeded
            return None

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

    # Abstract-noun (bhāva) taddhita suffixes the segmenter strands as words.
    # Keyed by the lemma the analyser gives the fragment; the value is the
    # suffix in its stem form, which is what the joined lemma ends in
    # (adhimātra + tvāt -> lemma adhimātratva, surface adhimātratvāt).
    _ABSTRACT_SUFFIXES = {"tva": "tva", "tā": "tā"}

    @staticmethod
    def _merge_suffix(words: list[dict]) -> list[dict]:
        """Rejoin a stranded abstract-noun suffix with the stem before it.

        The mirror of ``_merge_privative``, on the other end of the word.
        Segmenters cut adhimātratvāt into 'adhimātra' + 'tvāt' and ekātmatā
        into 'ātma' + 'tā'. The tail is a suffix, not a word: shown on its own
        it was glossed from the homographic numeral tva ('one, several') and
        the root √tu, telling the reader something the sentence never said.
        The stem keeps its own root — adhiṣṭhātṛtvam is still from √sthā —
        so the merged entry is built from the stem and only its meanings are
        cleared, so the enricher looks the whole abstract noun up afresh.
        """
        merged: list[dict] = []
        for word in words:
            suffix = SanskritAdapter._ABSTRACT_SUFFIXES.get(word.get("lemma"))
            if suffix and merged:
                stem = merged[-1]
                surface = stem["surface_form"] + word["surface_form"]
                # The stem's *surface* is the compounding form (ātman -> ātma),
                # so the abstract noun is built on it, not on the stem's lemma.
                lemma = stem["surface_form"] + suffix
                combined = dict(stem)
                combined["surface_form"], combined["surface_devanagari"] = _display_forms(surface)
                combined["lemma"], combined["lemma_devanagari"] = _display_forms(lemma)
                combined["meanings"] = []
                merged[-1] = combined
                continue
            merged.append(word)
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
        words = self._merge_suffix(words)
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
