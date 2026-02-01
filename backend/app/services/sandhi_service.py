"""
Sandhi splitting service using Vidyut.

Provides tokenization and lemma lookup for Sanskrit text using dictionary-informed
compound splitting. Uses Vidyut's sandhi rules and Kosha (dictionary) for validation.
Accepts input in Devanagari, IAST, or SLP1 encoding.
"""
import os
import re
from typing import List, Dict, Any, Optional, Tuple

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

try:
    from vidyut.vidyut import sandhi, kosha
    VIDYUT_AVAILABLE = True
except ImportError:
    sandhi = None
    kosha = None
    VIDYUT_AVAILABLE = False


class SandhiService:
    """
    Service for splitting Sanskrit compounds and tokenizing text.

    Uses Vidyut's sandhi rules combined with dictionary (Kosha) lookup for
    accurate compound word splitting. This approach validates splits against
    the lexicon rather than relying solely on statistical models.
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the sandhi service.

        Args:
            data_path: Path to vidyut-data directory. If None, uses default path.
        """
        self.splitter = None
        self.kosha = None
        self._init_error: Optional[str] = None

        if not VIDYUT_AVAILABLE:
            self._init_error = "Vidyut library not installed. Install with: pip install vidyut"
            return

        # Determine data path
        if data_path is None:
            # Check for DATA_DIR environment variable (set in Docker)
            data_dir = os.environ.get('DATA_DIR')
            if data_dir:
                data_path = os.path.join(data_dir, 'vidyut-data')
            else:
                # Default: data/vidyut-data from project root (local development)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                data_path = os.path.join(project_root, 'data', 'vidyut-data')

        if not os.path.exists(data_path):
            self._init_error = f"Vidyut data not found at {data_path}. Run: python -c \"import vidyut; vidyut.download_data('{data_path}')\""
            return

        try:
            # Initialize sandhi splitter from rules
            sandhi_rules_path = os.path.join(data_path, 'sandhi', 'rules.csv')
            self.splitter = sandhi.Splitter.from_csv(sandhi_rules_path)

            # Initialize dictionary (kosha) for validation
            kosha_path = os.path.join(data_path, 'kosha')
            self.kosha = kosha.Kosha(kosha_path)
        except Exception as e:
            self._init_error = f"Failed to initialize Vidyut: {e}"

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

    def _get_lemma_from_entry(self, entry) -> Optional[str]:
        """
        Extract the lemma (root/stem) from a Kosha entry.

        For krdanta (derived) words, returns the dhatu (verb root).
        For basic pratipadikas, returns the stem.
        """
        if not hasattr(entry, 'pratipadika_entry'):
            return None

        pe = entry.pratipadika_entry

        # Check for krdanta (derived from dhatu)
        if hasattr(pe, 'dhatu_entry') and pe.dhatu_entry:
            return pe.dhatu_entry.clean_text

        # Check for basic pratipadika (stem)
        if hasattr(pe, 'pratipadika') and pe.pratipadika:
            return pe.pratipadika.text

        return None

    def _lookup_word(self, word: str) -> Tuple[bool, Optional[str]]:
        """
        Look up a word in the dictionary.

        Returns:
            Tuple of (found, lemma) where lemma is the root/stem if found.
        """
        if not self.kosha:
            return False, None

        entries = self.kosha.get(word)
        if not entries:
            return False, None

        # Find the best lemma - prefer 'yuj' over 'yoji' for yoga-related words
        lemmas = set()
        for entry in entries:
            lemma = self._get_lemma_from_entry(entry)
            if lemma:
                lemmas.add(lemma)

        if not lemmas:
            return True, None

        # Prefer shorter lemmas (e.g., 'yuj' over 'yoji')
        best_lemma = min(lemmas, key=len)
        return True, best_lemma

    def _find_valid_splits(self, text: str, max_depth: int = 4, include_whole: bool = True) -> List[List[Dict[str, Any]]]:
        """
        Find all valid compound splits for the given text using sandhi rules
        and dictionary validation.

        Args:
            text: Text in SLP1 encoding
            max_depth: Maximum recursion depth for nested compounds
            include_whole: Whether to include the whole word as a valid "split"

        Returns:
            List of possible split sequences, each containing token dictionaries
            Each token has: text, lemma, and optionally 'vowel_sandhi' flag
        """
        if not self.splitter or not self.kosha:
            return []

        valid_splits = []
        seen_splits = set()  # Avoid duplicates

        # First pass: Try DIRECT splits (no sandhi reconstruction)
        # This finds compounds where parts were simply joined without vowel changes
        for i in range(3, len(text) - 2):
            first = text[:i]
            second = text[i:]

            first_found, first_lemma = self._lookup_word(first)
            if not first_found:
                continue

            second_found, second_lemma = self._lookup_word(second)
            if second_found:
                split_key = (first, second)
                if split_key not in seen_splits:
                    seen_splits.add(split_key)
                    valid_splits.append([
                        {"text": first, "lemma": first_lemma, "vowel_sandhi": False},
                        {"text": second, "lemma": second_lemma, "vowel_sandhi": False},
                    ])

                    # Recursively split second part
                    if max_depth > 0 and len(second) > 5:
                        recursive_splits = self._find_valid_splits(second, max_depth - 1, include_whole=False)
                        for rsplit in recursive_splits:
                            if len(rsplit) > 1:
                                valid_splits.append([
                                    {"text": first, "lemma": first_lemma, "vowel_sandhi": False},
                                    *rsplit
                                ])

        # Second pass: Try sandhi-rule-based splits
        # This handles cases where vowels merged (savarṇa dīrgha, etc.)
        for i in range(1, len(text)):
            try:
                split_results = self.splitter.split_at(text, i)
            except Exception:
                continue

            for split in split_results:
                if not split.is_valid:
                    continue

                first = split.first
                second = split.second

                if not first or not second:
                    continue

                # Skip short parts - meaningful Sanskrit morphemes are typically 3+ chars
                if len(first) < 3 or len(second) < 3:
                    continue

                split_key = (first, second)
                if split_key in seen_splits:
                    continue  # Already found via direct split

                # Check if first part is a valid word
                first_found, first_lemma = self._lookup_word(first)
                if not first_found:
                    continue

                # Detect if this split involved vowel sandhi reconstruction
                # Compare the sandhi result to what's actually at that position
                original_at_split = text[i:i+1] if i < len(text) else ""
                second_start = second[0] if second else ""
                vowel_sandhi = (original_at_split != second_start) or second_start in 'aAiIuUfFxXeEoO'

                # Check if second part is valid (either directly or recursively)
                second_found, second_lemma = self._lookup_word(second)

                if second_found:
                    seen_splits.add(split_key)
                    valid_splits.append([
                        {"text": first, "lemma": first_lemma, "vowel_sandhi": False},
                        {"text": second, "lemma": second_lemma, "vowel_sandhi": vowel_sandhi},
                    ])

                    # Also try to recursively split the second part for deeper analysis
                    if max_depth > 0 and len(second) > 3:
                        recursive_splits = self._find_valid_splits(second, max_depth - 1, include_whole=False)
                        for rsplit in recursive_splits:
                            if len(rsplit) > 1:  # Only add if we actually split further
                                valid_splits.append([
                                    {"text": first, "lemma": first_lemma, "vowel_sandhi": False},
                                    *rsplit
                                ])

                elif max_depth > 0:
                    # Second part not found - try to recursively split it
                    recursive_splits = self._find_valid_splits(second, max_depth - 1, include_whole=False)
                    for rsplit in recursive_splits:
                        seen_splits.add(split_key)
                        valid_splits.append([
                            {"text": first, "lemma": first_lemma, "vowel_sandhi": False},
                            *rsplit
                        ])

        # Only include whole word as fallback if no compound splits found
        if not valid_splits and include_whole:
            found, lemma = self._lookup_word(text)
            if found:
                valid_splits.append([{
                    "text": text,
                    "lemma": lemma,
                }])

        return valid_splits

    def _select_best_split(self, splits: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Select the best split from multiple candidates.

        Balances educational value with linguistic accuracy:
        1. Minimum part length of 3 chars (avoids trivial/incorrect splits)
        2. Prefers direct splits over vowel-sandhi reconstructions
           (e.g., mithyā+jñāna over mithyā+ajñāna)
        3. Prefers 2-3 part splits (most compounds are binary or ternary)
        4. Prefers longer minimum parts (more meaningful components)
        """
        if not splits:
            return []

        def split_score(split):
            num_parts = len(split)
            min_part_len = min(len(p["text"]) for p in split)
            total_len = sum(len(p["text"]) for p in split)

            # Hard filter: reject splits with very short parts (< 3 chars)
            # These are almost always incorrect sandhi interpretations
            if min_part_len < 3:
                return (1000, 0, 0, 0, 0, 0)

            # Count vowel-sandhi reconstructions - penalize these
            # Prefer direct splits (compound joins) over vowel sandhi reconstructions
            # This handles savarṇa dīrgha ambiguity: mithyā+jñāna vs mithyā+ajñāna
            vowel_sandhi_count = sum(1 for p in split if p.get("vowel_sandhi", False))

            # Ideal number of parts is 2-3 for most compounds
            # Penalize 1 part (no split) and > 3 parts (over-fragmentation)
            if num_parts == 1:
                part_penalty = 10  # No split - only use as fallback
            elif num_parts == 2:
                part_penalty = 0   # Binary compound - ideal
            elif num_parts == 3:
                part_penalty = 1   # Ternary compound - good
            else:
                part_penalty = 5 * (num_parts - 3)  # Penalize heavily

            # Scoring tuple (lower is better):
            # 1. Vowel sandhi count (prefer 0)
            # 2. Part count penalty
            # 3. Negative min part length (prefer longer)
            # 4. Negative total length (prefer more coverage)
            # 5. Number of parts (tiebreaker)
            return (vowel_sandhi_count, part_penalty, -min_part_len, -total_len, num_parts)

        return min(splits, key=split_score)

    def split(self, text: str) -> Dict[str, Any]:
        """
        Split/tokenize a Sanskrit text into components.

        Uses dictionary-informed sandhi splitting for accurate compound analysis.

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
        # Convert input to SLP1
        slp1_text = self._to_slp1(text.strip())

        if not self.splitter or not self.kosha:
            # Return graceful fallback when engine not available
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

        try:
            # Find all valid splits using dictionary lookup
            all_splits = self._find_valid_splits(slp1_text)

            # Select the best split
            best_split = self._select_best_split(all_splits)

            if not best_split:
                # No valid split found - return original word
                found, lemma = self._lookup_word(slp1_text)
                return {
                    "splits": [{
                        "text": slp1_text,
                        "text_devanagari": self._to_devanagari(slp1_text),
                        "text_iast": self._to_iast(slp1_text),
                        "lemma": lemma,
                        "lemma_devanagari": self._to_devanagari(lemma) if lemma else None,
                        "lemma_iast": self._to_iast(lemma) if lemma else None,
                        "is_original": True
                    }],
                    "original": text,
                    "original_slp1": slp1_text,
                    "original_devanagari": self._to_devanagari(slp1_text),
                    "original_iast": self._to_iast(slp1_text),
                    "engine_available": True,
                    "engine_error": None
                }

            # Format results
            splits = []
            for token in best_split:
                token_text = token["text"]
                token_lemma = token.get("lemma")

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
        return self.splitter is not None and self.kosha is not None

    def get_status(self) -> Dict[str, Any]:
        """Get status information about the sandhi service."""
        return {
            "available": self.is_available(),
            "vidyut_installed": VIDYUT_AVAILABLE,
            "error": self._init_error
        }
