"""Dictionary lookup over ``sanskrit_analyzer.lexicon`` (yoga_sutras #10).

The CDSL data, its parsing and its body cleaning live in the shared library.
This module keeps only what is specific to this app: the response shape the
frontend reads, fuzzy matching for typos, and the MW etymology helpers the
sanskrit adapter uses to pick a word's root.

Sources:
- Monier-Williams (CC BY-SA 4.0) ships with the app at
  ``app/data/lexicon/mw.sqlite``. It sits outside ``/app/data``, which the
  prod PVC mounts over.
- Apte (AP90, GPL-3.0) is never bundled. Set ``SANSKRIT_AP90_DB``, or place
  ``ap90.sqlite`` at ``/app/data/lexicon/`` on the data volume. Without it,
  lookups return MW only.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz, process
from sanskrit_analyzer import lexicon
from sanskrit_analyzer.models.scripts import Script
from sanskrit_analyzer.utils import detect_script
from sanskrit_analyzer.utils.transliterate import to_devanagari, to_iast, to_slp1

logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).resolve().parent.parent
MW_DB_PATH = _APP_DIR / "data" / "lexicon" / "mw.sqlite"
AP90_DB_PATH = Path(os.environ.get("YOGA_DATA_DIR", "/app/data")) / "lexicon" / "ap90.sqlite"
os.environ.setdefault("SANSKRIT_MW_DB", str(MW_DB_PATH))
if AP90_DB_PATH.is_file():
    os.environ.setdefault("SANSKRIT_AP90_DB", str(AP90_DB_PATH))

# lexicon source id -> (API code the frontend filters on, display title)
_SOURCES = {
    "mw": ("mw", "Monier-Williams Sanskrit-English Dictionary (1899)"),
    "ap90": ("apte", "Apte Practical Sanskrit-English Dictionary (1890)"),
}
# Prefix length used to gather fuzzy-match candidates, and how many to rank.
_FUZZY_PREFIX = 2
_FUZZY_POOL = 5000


class DictionaryService:
    """Dictionary lookup for Devanagari, IAST or SLP1 input, with typo tolerance."""

    def _sources(self) -> List[str]:
        return [s for s in _SOURCES if lexicon.is_available(s)]

    @staticmethod
    def _to_slp1(word: str) -> str:
        # Plain ASCII is read as SLP1, the CDSL key encoding.
        script = detect_script(word, plain_ascii_default=Script.SLP1)
        if script in (Script.DEVANAGARI, Script.IAST):
            return to_slp1(word, script)
        return word

    def _fuzzy_match(self, word_slp1: str, threshold: int = 80, limit: int = 5) -> List[str]:
        """Closest headwords sharing the word's first letters."""
        if len(word_slp1) < _FUZZY_PREFIX:
            return []
        pool = lexicon.prefix(word_slp1[:_FUZZY_PREFIX], _FUZZY_POOL, sources=self._sources())
        matches = process.extract(word_slp1, pool, scorer=fuzz.ratio,
                                  limit=limit, score_cutoff=threshold)
        return [m[0] for m in matches]

    def _entries(self, key: str) -> list:
        return lexicon.lookup(key, sources=self._sources())

    def get_definitions(self, word: str, fuzzy: bool = True) -> List[Dict[str, Any]]:
        """Entries for ``word`` across the available dictionaries."""
        word_slp1 = self._to_slp1(word.strip())
        entries = self._entries(word_slp1)
        is_fuzzy = False
        if not entries and fuzzy:
            for key in self._fuzzy_match(word_slp1):
                entries.extend(self._entries(key))
            is_fuzzy = bool(entries)

        definitions = []
        for e in entries:
            code, title = _SOURCES[e.source]
            definitions.append({
                "dictionary_code": code,
                "dictionary_name": title,
                "entry_id": e.lnum,
                "key": e.key,
                "key_devanagari": to_devanagari(e.key, Script.SLP1),
                "key_iast": to_iast(e.key, Script.SLP1),
                "definition": e.text,
                "is_fuzzy_match": is_fuzzy and e.key != word_slp1,
                "licence": e.licence,
                "acknowledgement": e.acknowledgement,
            })
        return definitions

    # MW states a derived word's origin as 'fr. √ 1. viṣ' or '(√ rañj)'. The
    # homograph numerals that may precede the root are skipped, however many
    # of them a cross-reference piles up ('See √ 1. 2. and 4. kṣi').
    _CITED_ROOT = re.compile(r'√\s*(?:(?:\d+\.?|and)\s*)*([^\s,;)\]]+)')
    # CDSL glues its own entry id onto some roots: 'sañj.228458'.
    _CDSL_ID = re.compile(r'\.\d+$')

    @staticmethod
    def _cited_root_from_texts(texts) -> Optional[str]:
        """The root MW names across a word's entries, in SLP1, or None.

        A '?' after the root is MW flagging an etymology it is unsure of. That
        is worth reporting, but a confident citation elsewhere in the same
        word's entries beats it — kāla hedges 'fr. √ 3. kal?' in one entry and
        states '√ 3. kal' outright in the next.
        """
        doubtful = None
        for text in texts:
            for match in DictionaryService._CITED_ROOT.finditer(text or ""):
                cited = match.group(1).strip('.’\'"')
                marked = cited.endswith('?')
                cited = DictionaryService._CDSL_ID.sub('', cited.rstrip('?'))
                # A capture that is not a word is a stray numeral or list
                # punctuation the citation ran into, not a root.
                if not cited or not cited.isalpha():
                    continue
                # Bodies are IAST, but some roots keep the raw SLP1 the CDSL
                # file used ('√ kf'): all-ASCII tokens are taken as SLP1.
                root = (to_slp1(cited, Script.IAST)
                        if any(ord(c) > 127 for c in cited) else cited)
                if not marked:
                    return root
                doubtful = doubtful or root
        return doubtful

    _cited_root_cache: Dict[str, Optional[str]] = {}

    def get_cited_root(self, word: str) -> Optional[str]:
        """The root MW itself names for a word, in SLP1, or None.

        Where several Kośa readings compete (rāga: √rāj? √rag? √rañj?) the
        dictionary's own etymology settles it, and it also reaches words the
        Kośa has no derivational entry for at all (karman -> √kṛ).
        """
        if word in self._cited_root_cache:
            return self._cited_root_cache[word]
        try:
            root = self._cited_root_from_texts(
                e["definition"] for e in self.get_definitions(word, fuzzy=False)
                if e["dictionary_code"] == "mw"
            )
        except Exception:  # best-effort: lexicon data missing
            logger.debug("cited-root lookup failed for %r", word, exc_info=True)
            root = None
        self._cited_root_cache[word] = root
        return root

    # Sense runs open with 'to' and end at the first citation or bracket.
    _SENSE_RUN = re.compile(r'\b(to\s+[a-z][a-z ,\-]{3,150})')
    # Grammatical apparatus that means we matched a citation, not a sense.
    _SENSE_JUNK = re.compile(r'\b(?:Dh[aā]tup|accord|ib|cf)\b', re.IGNORECASE)
    _root_gloss_cache: Dict[Any, Optional[str]] = {}

    def get_root_gloss(self, root_slp1: str, gana: Optional[int] = None) -> Optional[str]:
        """English gloss for a verbal root, e.g. 'yuj' -> 'to yoke or join'.

        The Dhātupāṭha's own artha ('saṃyamane') is Sanskrit, so it tells an
        English reader nothing. MW's root entries open with the conjugation
        class and then the sense run, so we take the first 'to ...' clause.
        Homographic roots are told apart by class: √rudh 1 is 'to sprout' but
        √rudh 7 (behind nirodha) is 'to obstruct'. When ``gana`` is known, the
        entry declaring that class is preferred.
        """
        cache_key = (root_slp1, gana)
        if cache_key in self._root_gloss_cache:
            return self._root_gloss_cache[cache_key]
        try:
            texts = [e["definition"] for e in self.get_definitions(root_slp1, fuzzy=False)]
        except Exception:  # best-effort: lexicon data missing
            logger.debug("root gloss lookup failed for %r", root_slp1, exc_info=True)
            texts = []
        if gana is not None:
            marker = f"cl. {gana}."
            texts.sort(key=lambda t: marker not in t)
        gloss = next((g for g in map(self._extract_sense_run, texts) if g), None)
        self._root_gloss_cache[cache_key] = gloss
        return gloss

    @classmethod
    def _extract_sense_run(cls, text: str) -> Optional[str]:
        """First readable 'to X, Y, Z' sense run in an MW/Apte root entry."""
        for match in cls._SENSE_RUN.finditer(text or ''):
            run = match.group(1).strip().rstrip(' ,')
            if cls._SENSE_JUNK.search(run) or len(run) < 6:
                continue
            senses = [s.strip() for s in run.split(',') if s.strip()]
            return ', '.join(senses[:4])
        return None

    def get_dictionaries(self) -> List[Dict[str, Any]]:
        """The dictionaries available to this process."""
        return [{"code": _SOURCES[s][0], "title": _SOURCES[s][1]} for s in self._sources()]
