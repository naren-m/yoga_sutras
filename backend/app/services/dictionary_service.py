from app.models.dictionary import Dictionary, DictionaryEntry
from app import db
from typing import List, Dict, Any, Optional
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from rapidfuzz import fuzz, process
import re


class DictionaryService:
    """
    Dictionary lookup service supporting multiple input scripts
    (Devanagari, IAST, SLP1) and fuzzy matching for typo tolerance.
    """

    # Cache for dictionary keys to speed up fuzzy matching
    _keys_cache: Optional[List[str]] = None
    _keys_cache_count: int = 0

    def _detect_script(self, word: str) -> str:
        """
        Detect the script of the input word.
        Returns: 'DEVANAGARI', 'IAST', or 'SLP1'
        """
        # Check for Devanagari characters (Unicode range 0900-097F)
        if re.search(r'[\u0900-\u097F]', word):
            return 'DEVANAGARI'

        # Check for IAST diacritics (macrons, dots, tildes on letters)
        # IAST uses: ā ī ū ṛ ṝ ḷ ḹ ṃ ḥ ñ ṅ ṭ ḍ ṇ ś ṣ
        iast_chars = 'āīūṛṝḷḹṃḥñṅṭḍṇśṣĀĪŪṚṜḶḸṂḤÑṄṬḌṆŚṢ'
        if any(c in word for c in iast_chars):
            return 'IAST'

        # Default to SLP1 (ASCII-based transliteration)
        return 'SLP1'

    def _to_slp1(self, word: str) -> str:
        """
        Convert word from any supported script to SLP1.
        """
        script = self._detect_script(word)

        if script == 'DEVANAGARI':
            return transliterate(word, sanscript.DEVANAGARI, sanscript.SLP1)
        elif script == 'IAST':
            return transliterate(word, sanscript.IAST, sanscript.SLP1)
        else:
            # Already SLP1
            return word

    def _to_devanagari(self, slp1_word: str) -> str:
        """Convert SLP1 to Devanagari for display."""
        return transliterate(slp1_word, sanscript.SLP1, sanscript.DEVANAGARI)

    def _to_iast(self, slp1_word: str) -> str:
        """Convert SLP1 to IAST for display."""
        return transliterate(slp1_word, sanscript.SLP1, sanscript.IAST)

    def _get_all_keys(self) -> List[str]:
        """
        Get all dictionary keys for fuzzy matching.
        Uses caching to improve performance.
        """
        # Check if cache needs refresh (count changed)
        current_count = db.session.query(DictionaryEntry).count()

        if self._keys_cache is None or self._keys_cache_count != current_count:
            # Fetch unique keys
            keys_query = db.session.query(DictionaryEntry.key).distinct().all()
            self._keys_cache = [k[0] for k in keys_query]
            self._keys_cache_count = current_count

        return self._keys_cache

    def _fuzzy_match(self, word_slp1: str, threshold: int = 80, limit: int = 5) -> List[str]:
        """
        Find fuzzy matches for a word using rapidfuzz.

        Args:
            word_slp1: Word in SLP1 encoding
            threshold: Minimum similarity score (0-100)
            limit: Maximum number of matches to return

        Returns:
            List of matching keys sorted by similarity
        """
        all_keys = self._get_all_keys()

        if not all_keys:
            return []

        # Use rapidfuzz to find similar keys
        matches = process.extract(
            word_slp1,
            all_keys,
            scorer=fuzz.ratio,
            limit=limit,
            score_cutoff=threshold
        )

        # Return just the keys (matches are tuples of (key, score, index))
        return [match[0] for match in matches]

    def get_definitions(self, word: str, fuzzy: bool = True) -> List[Dict[str, Any]]:
        """
        Lookup a word across all dictionaries.

        Args:
            word: Word in Devanagari, IAST, or SLP1
            fuzzy: Whether to use fuzzy matching if exact match fails

        Returns:
            List of definitions with dictionary info and display formats
        """
        # Convert input to SLP1 for lookup
        word_slp1 = self._to_slp1(word.strip())

        # Try exact match first
        results = db.session.query(DictionaryEntry, Dictionary).\
            join(Dictionary, DictionaryEntry.dictionary_id == Dictionary.id).\
            filter(DictionaryEntry.key == word_slp1).all()

        # If no exact match and fuzzy enabled, try fuzzy matching
        matched_keys = [word_slp1]
        is_fuzzy_match = False

        if not results and fuzzy:
            fuzzy_keys = self._fuzzy_match(word_slp1)
            if fuzzy_keys:
                matched_keys = fuzzy_keys
                is_fuzzy_match = True
                # Query for all fuzzy matches
                results = db.session.query(DictionaryEntry, Dictionary).\
                    join(Dictionary, DictionaryEntry.dictionary_id == Dictionary.id).\
                    filter(DictionaryEntry.key.in_(fuzzy_keys)).all()

        # Format results
        definitions = []
        for entry, dictionary in results:
            definitions.append({
                "dictionary_id": dictionary.id,
                "dictionary_name": dictionary.title,
                "dictionary_code": dictionary.slug,
                "entry_id": entry.id,
                "key": entry.key,
                "key_devanagari": self._to_devanagari(entry.key),
                "key_iast": self._to_iast(entry.key),
                "definition": entry.value,
                "is_fuzzy_match": is_fuzzy_match and entry.key != word_slp1
            })

        return definitions

    def get_dictionaries(self) -> List[Dict[str, Any]]:
        """Get list of all available dictionaries."""
        dictionaries = db.session.query(Dictionary).all()
        return [d.to_dict() for d in dictionaries]
