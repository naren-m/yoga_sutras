from app.models.dictionary import Dictionary, DictionaryEntry
from app import db
from typing import List, Dict, Any, Optional
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from rapidfuzz import fuzz, process
import re


# CDSL entry bodies interleave English prose with SLP1 Sanskrit tokens and
# end with scan-page references, e.g.:
#   'niroDaHniroDaH niroDanaM 1 Confinement; yogaScittavfttiniroDaH Yoga S.168960631-c'
_DEF_WORD = re.compile(r'[A-Za-z/]+')
_DEF_TRAIL_REF = re.compile(r'[\d,\-]{4,}[a-z]?\s*$')
_DEF_DOUBLED = re.compile(r'(\w{4,})\1+')
_DEF_ACCENT = re.compile(r'(?<=[A-Za-z])/(?=[A-Za-z])')
# A token that starts the definition body proper: part-of-speech marker,
# numbered sense, parenthesis, abbreviation, or capitalized English word.
_DEF_BODY_START = re.compile(r'^(?:(?:mfn|mf|m|f|n|ind|cl|p{1,2})\.?$|[0-9(&A-Z])')


class DictionaryService:
    """
    Dictionary lookup service supporting multiple input scripts
    (Devanagari, IAST, SLP1) and fuzzy matching for typo tolerance.
    """

    # Cache for dictionary keys to speed up fuzzy matching
    _keys_cache: Optional[List[str]] = None
    _keys_cache_count: int = 0

    @staticmethod
    def clean_definition(value: str) -> str:
        """Make a raw CDSL entry body readable.

        - Transliterates embedded SLP1 tokens to IAST. An SLP1 token starts
          lowercase but has interior capitals (aspirates/long vowels:
          'niroDaH', 'yogaScittavfttiniroDaH'); English words and citation
          abbreviations ('Ms.', 'MBh.') never match that shape.
        - Collapses doubled headword echoes ('cittacitta' -> 'citta').
        - Drops the trailing scan-page reference ('168960631-c').
        """
        def _xlit_token(m: re.Match) -> str:
            token = m.group(0)
            core = token.replace('/', '')  # '/' marks vedic accent in MW
            if core and core[0].islower() and any(c.isupper() for c in core[1:]):
                try:
                    return transliterate(core, sanscript.SLP1, sanscript.IAST)
                except Exception:
                    return token
            return token

        text = _DEF_WORD.sub(_xlit_token, value)
        text = _DEF_ACCENT.sub('', text)   # MW vedic accent marks: yo/ga -> yoga
        text = _DEF_DOUBLED.sub(r'\1', text)
        text = _DEF_TRAIL_REF.sub('', text)
        # Apte bodies open with a run of headword variants ("nirodhaḥ
        # nirodhanaṃ ...") before the first numbered sense. After
        # transliteration those echoes carry IAST diacritics while English
        # prose is pure ASCII — strip the leading non-ASCII token run.
        stripped = re.sub(r'^(?:\S*[^\x00-\x7F]\S*\s+)+', '', text)
        if len(stripped) >= 3:
            text = stripped
        # All-lowercase SLP1 echoes ('vftti f. rolling...') carry no capitals
        # for the transliterator to spot; drop leading tokens up to the first
        # recognizable body-start token instead.
        tokens = text.split(' ')
        for i, token in enumerate(tokens[:6]):
            if _DEF_BODY_START.match(token):
                if i > 0:
                    text = ' '.join(tokens[i:])
                break
        return text.rstrip(' ;,')

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
                "definition": self.clean_definition(entry.value),
                "is_fuzzy_match": is_fuzzy_match and entry.key != word_slp1
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
                # Entry bodies are half-transliterated: tokens carrying
                # diacritics came through as IAST, all-ASCII ones are still
                # the raw SLP1 the CDSL file used ('√ kf').
                root = (transliterate(cited, sanscript.IAST, sanscript.SLP1)
                        if any(ord(c) > 127 for c in cited) else cited)
                if not marked:
                    return root
                doubtful = doubtful or root
        return doubtful

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
                e.get("definition") or "" for e in self.get_definitions(word, fuzzy=False)
            )
        except Exception:
            root = None
        self._cited_root_cache[word] = root
        return root

    _cited_root_cache: Dict[str, Optional[str]] = {}

    def get_root_gloss(self, root_slp1: str, gana: Optional[int] = None) -> Optional[str]:
        """English gloss for a verbal root, e.g. 'yuj' -> 'to yoke or join'.

        The Dhātupāṭha's own artha ('saṃyamane') is Sanskrit, so it tells an
        English reader nothing. MW's root entries open with the conjugation
        class and then the sense run — 'cl. 7. P. Ā. ... ruṇaddhi ... to
        obstruct, check, arrest' — so we take the first 'to ...' clause.

        Homographic roots are distinguished by class: √rudh 1 is 'to sprout'
        but √rudh 7 (the one behind nirodha) is 'to obstruct'. When ``gana``
        is known we prefer the MW entry declaring that class.
        """
        cache_key = (root_slp1, gana)
        if cache_key in self._root_gloss_cache:
            return self._root_gloss_cache[cache_key]

        gloss = None
        try:
            entries = self.get_definitions(root_slp1, fuzzy=False)
        except Exception:
            entries = []

        texts = [e.get("definition") or "" for e in entries]
        if gana is not None:
            marker = f"cl. {gana}."
            texts.sort(key=lambda t: marker not in t)

        for text in texts:
            gloss = self._extract_sense_run(text)
            if gloss:
                break

        self._root_gloss_cache[cache_key] = gloss
        return gloss

    # Sense runs open with 'to' and end at the first citation or bracket.
    _SENSE_RUN = re.compile(r'\b(to\s+[a-z][a-z ,\-]{3,150})')
    # Grammatical apparatus that means we matched a citation, not a sense.
    _SENSE_JUNK = re.compile(r'\b(?:Dh[aā]tup|accord|ib|cf)\b', re.IGNORECASE)
    _root_gloss_cache: Dict[Any, Optional[str]] = {}

    @classmethod
    def _extract_sense_run(cls, text: str) -> Optional[str]:
        """First readable 'to X, Y, Z' sense run in an MW/Apte root entry."""
        for match in cls._SENSE_RUN.finditer(text or ''):
            run = match.group(1).strip().rstrip(' ,')
            if cls._SENSE_JUNK.search(run) or len(run) < 6:
                continue
            # Keep it short enough for a gloss line: first few senses only.
            senses = [s.strip() for s in run.split(',') if s.strip()]
            return ', '.join(senses[:4])
        return None

    def get_dictionaries(self) -> List[Dict[str, Any]]:
        """Get list of all available dictionaries."""
        dictionaries = db.session.query(Dictionary).all()
        return [d.to_dict() for d in dictionaries]
