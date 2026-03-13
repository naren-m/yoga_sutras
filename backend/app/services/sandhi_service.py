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
    from vidyut.vidyut import sandhi, kosha, cheda
    VIDYUT_AVAILABLE = True
except ImportError:
    sandhi = None
    kosha = None
    cheda = None
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
        self.chedaka = None  # For morphological analysis of inflected forms
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

            # Initialize Chedaka for morphological analysis (handles inflected forms)
            self.chedaka = cheda.Chedaka(data_path)
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

        First tries direct kosha lookup, then falls back to Chedaka for
        morphological analysis of inflected forms (e.g., niroDaH → niruD).

        Returns:
            Tuple of (found, lemma) where lemma is the root/stem if found.
        """
        if not self.kosha:
            return False, None

        # First try direct dictionary lookup
        entries = self.kosha.get(word)
        if entries:
            # Find the best lemma from dictionary entries
            lemmas = set()
            for entry in entries:
                lemma = self._get_lemma_from_entry(entry)
                if lemma:
                    lemmas.add(lemma)

            if lemmas:
                # Prefer shorter lemmas (e.g., 'yuj' over 'yoji')
                best_lemma = min(lemmas, key=len)
                return True, best_lemma
            return True, None

        # If not found in dictionary, try Chedaka for inflected forms
        # Only use Chedaka for words with typical Sanskrit case endings
        # This handles cases like niroDaH (nominative) → niruD (stem)
        inflected_endings = ('H', 'm', 'aH', 'am', 'eH', 'oH', 'ayoH', 'AH', 'In', 'iH')
        if self.chedaka and any(word.endswith(e) for e in inflected_endings):
            try:
                tokens = self.chedaka.run(word)
                if tokens:
                    token = tokens[0]
                    lemma = token.lemma if hasattr(token, 'lemma') else None
                    # Chedaka returns 'None' string for unknown lemmas
                    # Also reject very short lemmas (< 2 chars) as likely false positives
                    if lemma and lemma != 'None' and len(lemma) >= 2:
                        return True, lemma
            except Exception:
                pass

        return False, None

    def _build_fallback_response(self, text: str, slp1_text: str, lemma: Optional[str] = None,
                                  engine_available: bool = False, error: Optional[str] = None) -> Dict[str, Any]:
        """Build a fallback response when splitting fails or is unavailable."""
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
            "engine_available": engine_available,
            "engine_error": error
        }

    def _detect_sandhi_type(self, first: str, second: str, original_junction: str) -> Optional[Dict[str, str]]:
        """
        Detect the type of sandhi that occurred at the junction between two words.

        Args:
            first: First part of the split (in SLP1)
            second: Second part of the split (in SLP1)
            original_junction: The character(s) at the split point in the original text

        Returns:
            Dictionary with sandhi type info, or None if no sandhi detected
        """
        if not first or not second:
            return None

        first_end = first[-1] if first else ''
        second_start = second[0] if second else ''

        # Define vowel groups in SLP1
        all_vowels = 'aAiIuUfFxXeEoO'
        a_vowels = 'aA'
        i_vowels = 'iI'
        u_vowels = 'uU'
        r_vowels = 'fF'

        # Check for savarṇa dīrgha sandhi (similar vowels merge to long)
        savarna_rules = [
            (a_vowels, "ā + a → ā"),
            (i_vowels, "ī + i → ī"),
            (u_vowels, "ū + u → ū"),
        ]
        for vowels, rule in savarna_rules:
            if first_end in vowels and second_start in vowels:
                return {
                    "name": "savarṇa-dīrgha",
                    "name_devanagari": "सवर्ण-दीर्घ",
                    "rule": rule,
                    "description": "Similar vowels combine into long vowel"
                }

        # Check for guṇa sandhi (a/ā + i/ī → e, a/ā + u/ū → o, a/ā + ṛ → ar)
        if first_end in a_vowels:
            guna_rules = [
                (i_vowels, "a + i → e", "a/ā + i/ī combines to e"),
                (u_vowels, "a + u → o", "a/ā + u/ū combines to o"),
                (r_vowels, "a + ṛ → ar", "a/ā + ṛ combines to ar"),
            ]
            for vowels, rule, desc in guna_rules:
                if second_start in vowels:
                    return {
                        "name": "guṇa",
                        "name_devanagari": "गुण",
                        "rule": rule,
                        "description": desc
                    }

        # Check for vṛddhi sandhi (ā + i → ai, ā + u → au)
        if first_end == 'A':  # long_a in SLP1
            if second_start in i_vowels:
                return {
                    "name": "vṛddhi",
                    "name_devanagari": "वृद्धि",
                    "rule": "ā + i → ai",
                    "description": "ā + i/ī combines to ai"
                }
            if second_start in u_vowels:
                return {
                    "name": "vṛddhi",
                    "name_devanagari": "वृद्धि",
                    "rule": "ā + u → au",
                    "description": "ā + u/ū combines to au"
                }

        # Check for yāṇ sandhi (i/ī + vowel → y + vowel)
        if first_end in i_vowels and second_start in all_vowels and second_start not in i_vowels:
            return {
                "name": "yāṇ",
                "name_devanagari": "यण्",
                "rule": "i + V → y + V",
                "description": "i/ī before different vowel becomes y"
            }

        # Check for yāṇ sandhi (u/ū + vowel → v + vowel)
        if first_end in u_vowels and second_start in all_vowels and second_start not in u_vowels:
            return {
                "name": "yāṇ",
                "name_devanagari": "यण्",
                "rule": "u + V → v + V",
                "description": "u/ū before different vowel becomes v"
            }

        # Check for visarga sandhi
        if first_end == 'H':  # visarga in SLP1
            return {
                "name": "visarga",
                "name_devanagari": "विसर्ग",
                "rule": "ḥ + ...",
                "description": "Visarga sandhi"
            }

        return None

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

                # Detect sandhi type if vowel sandhi occurred
                sandhi_type = None
                if vowel_sandhi:
                    sandhi_type = self._detect_sandhi_type(first, second, original_at_split)

                # Check if second part is valid (either directly or recursively)
                second_found, second_lemma = self._lookup_word(second)

                if second_found:
                    seen_splits.add(split_key)
                    second_token = {"text": second, "lemma": second_lemma, "vowel_sandhi": vowel_sandhi}
                    if sandhi_type:
                        second_token["sandhi_type"] = sandhi_type
                    valid_splits.append([
                        {"text": first, "lemma": first_lemma, "vowel_sandhi": False},
                        second_token,
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
                return (1000, 0, 0, 0, 0, 0, 0, 0)

            # Count vowel-sandhi reconstructions - penalize these
            # Prefer direct splits (compound joins) over vowel sandhi reconstructions
            # This handles savarṇa dīrgha ambiguity: mithyā+jñāna vs mithyā+ajñāna
            vowel_sandhi_count = sum(1 for p in split if p.get("vowel_sandhi", False))

            # Penalize splits that have very short FINAL parts (3 chars or less)
            # Short final parts often indicate over-splitting (e.g., "jñā + nam" vs "jñānam")
            # But short prefixes (like "anu", "upa", "pra") are valid and shouldn't be penalized
            last_part_len = len(split[-1]["text"])
            short_final_penalty = 3 if last_part_len <= 3 else 0

            # For educational purposes, prefer splits that show all meaningful components
            # Sanskrit compounds often have 3-4 parts (e.g., yoga+citta+vṛtti+nirodha)
            # We want MORE granular splits when parts are meaningful (min length >= 4)
            if num_parts == 1:
                part_penalty = 10  # No split - only use as fallback
            elif num_parts >= 2 and num_parts <= 4:
                # Prefer more parts when all parts are meaningful (longer)
                # If min_part_len >= 4, prefer more parts; otherwise prefer fewer
                if min_part_len >= 4:
                    part_penalty = 5 - num_parts  # 2 parts=3, 3 parts=2, 4 parts=1
                else:
                    part_penalty = num_parts - 1  # 2 parts=1, 3 parts=2, 4 parts=3
            else:
                part_penalty = 5 * (num_parts - 4)  # Penalize heavily > 4 parts

            # First part should be a meaningful word (prefer longer first parts)
            # This helps select "yoga + anu" over "yas + gAn"
            first_part_len = len(split[0]["text"])

            # Penalize first parts that look like inflected forms rather than stems
            # In compounds, the first member should be in stem form (prātipadika)
            # e.g., "yoga" is stem, "yogAn" is accusative plural - prefer stem
            first_part = split[0]["text"]
            inflected_penalty = 0
            # Common case endings that indicate inflected forms (not stem forms)
            # - Nominative singular: -aH, -As, -iH, -uH (a-stems, i-stems, u-stems)
            # - Accusative plural: -An, -In, -Un
            # - Other plural endings: -AH, -IH, -UH, -Ani, -Ini
            inflected_endings = ('An', 'In', 'Un', 'AH', 'IH', 'UH', 'Ani', 'Ini', 'As', 'is', 'us')
            if any(first_part.endswith(e) for e in inflected_endings):
                inflected_penalty = 2  # Significant penalty for inflected first parts

            # Scoring tuple (lower is better):
            # 1. Vowel sandhi count (prefer 0)
            # 2. Short final part penalty (penalize 3-char or shorter final parts)
            # 3. Inflected form penalty (prefer stem forms as first compound member)
            # 4. Part count penalty
            # 5. Negative first part length (prefer longer first part)
            # 6. Negative min part length (prefer longer)
            # 7. Negative total length (prefer more coverage)
            # 8. Number of parts (tiebreaker - prefer more for education)
            return (vowel_sandhi_count, short_final_penalty, inflected_penalty, part_penalty, -first_part_len, -min_part_len, -total_len, -num_parts)

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
            return self._build_fallback_response(text, slp1_text, error=self._init_error)

        try:
            # Find all valid splits using dictionary lookup
            all_splits = self._find_valid_splits(slp1_text)

            # Select the best split
            best_split = self._select_best_split(all_splits)

            if not best_split:
                # No valid split found - return original word
                _, lemma = self._lookup_word(slp1_text)
                return self._build_fallback_response(text, slp1_text, lemma=lemma, engine_available=True)

            # Format results
            splits = []
            for i, token in enumerate(best_split):
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

                # Detect sandhi at junction with NEXT token (what sandhi applies when joining)
                if i < len(best_split) - 1:
                    next_token = best_split[i + 1]
                    sandhi_type = self._detect_sandhi_type(token_text, next_token["text"], "")
                    if sandhi_type:
                        split_obj["sandhi_type"] = sandhi_type

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
            return self._build_fallback_response(text, slp1_text, engine_available=True, error=str(e))

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
