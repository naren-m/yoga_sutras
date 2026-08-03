"""Integration tests for the Yoga Sutras SanskritAdapter.

Tests use the real sanskrit_analyzer library to verify the adapter
actually works end-to-end. Tests skip gracefully if engines aren't available.
"""

import pytest

from app.services.sanskrit_adapter import SanskritAdapter, get_sanskrit_adapter


@pytest.fixture
def adapter():
    """Create a real SanskritAdapter instance."""
    try:
        a = SanskritAdapter()
        _ = a.analyzer  # Trigger lazy init
        return a
    except Exception as e:
        pytest.skip(f"sanskrit_analyzer not available: {e}")


class TestSanskritAdapter:
    """Tests for SanskritAdapter with real Analyzer."""

    def test_analyzer_initializes(self, adapter):
        """Test that the real Analyzer initializes successfully."""
        assert adapter.analyzer is not None

    def test_is_available(self, adapter):
        """Test is_available returns True when initialized."""
        assert adapter.is_available() is True

    def test_singleton_instance(self):
        """Test get_sanskrit_adapter returns same instance."""
        import app.services.sanskrit_adapter as mod

        mod._adapter_instance = None
        a1 = get_sanskrit_adapter()
        a2 = get_sanskrit_adapter()
        assert a1 is a2
        mod._adapter_instance = None

    def test_split_returns_backwards_compatible_dict(self, adapter):
        """Test split() returns the old SandhiService response format."""
        result = adapter.split("yogaścittavṛttinirodhaḥ")

        assert "splits" in result
        assert "original" in result
        assert "engine_available" in result
        assert result["engine_available"] is True
        assert isinstance(result["splits"], list)

    def test_split_has_expected_keys(self, adapter):
        """Test split tokens have text and lemma keys."""
        result = adapter.split("rāmaḥ")

        if result["splits"]:
            token = result["splits"][0]
            assert "text" in token
            assert "lemma" in token

    def test_get_morphology_sync(self, adapter):
        """Test morphology analysis for a known word."""
        result = adapter.get_morphology_sync("गच्छति")
        # Returns dict or None
        if result is not None:
            assert isinstance(result, dict)

    def test_get_status(self, adapter):
        """Test get_status returns service info."""
        status = adapter.get_status()
        assert status["service"] == "sanskrit_analyzer"
        assert status["available"] is True

    def test_dictionary_lookup(self, adapter):
        """Test dictionary_lookup returns a list."""
        result = adapter.dictionary_lookup("yoga")
        assert isinstance(result, list)

    def test_analyze_word_sync(self, adapter):
        """Test word analysis returns expected format."""
        result = adapter.analyze_word_sync("रामः")
        assert "word" in result
        assert result["word"] == "रामः"

    def test_split_output_is_display_scripts_not_slp1(self, adapter):
        """Regression: tokens must be IAST/Devanagari, not raw SLP1.

        Sutra 1.2 contains vṛtti/nirodha whose SLP1 forms (vftti, niroDa)
        leaked to the frontend before the adapter transliterated output.
        """
        result = adapter.split("योगश्चित्तवृत्तिनिरोधः")

        texts = [t["text"] for t in result["splits"]]
        assert "vṛtti" in texts
        assert "nirodha" in texts
        assert not any("f" in t or "D" in t for t in texts)

        devanagari = [t["text_devanagari"] for t in result["splits"]]
        assert "वृत्ति" in devanagari

        assert result["original"]["iast"] == "yogaścittavṛttinirodhaḥ"

    def test_morphology_iast_verb_keeps_aspirate(self, adapter):
        """Regression: 'bhavati' was mangled to 'bavati' by double script
        detection (title-case SLP1 'Bavati' misread as IAST in engines)."""
        result = adapter.get_morphology_sync("bhavati")

        assert result is not None
        assert result["lemma"] == "bhū"
        assert result["surface_form"] == "bhavati"
        assert result["is_verb"] is True
        assert result["dhatu"] == "bhū"
        assert result["gana"] == 1

    def test_morphology_returns_lemma_without_dhatu(self, adapter):
        """A parseable word with no morphology/dhatu still yields its lemma."""
        result = adapter.get_morphology_sync("योगः")

        assert result is not None
        assert result["lemma"] == "yoga"
        assert result["lemma_devanagari"] == "योग"

    def test_analyze_block_returns_word_list(self, adapter):
        """analyze_block yields one display-script entry per unsandhied word."""
        result = adapter.analyze_block_sync("योगश्चित्तवृत्तिनिरोधः")

        assert result is not None
        assert result["source"] == "sanskrit_analyzer"
        assert isinstance(result["words"], list)
        assert len(result["words"]) >= 2  # yoga + citta/vṛtti/nirodha splits

        for entry in result["words"]:
            assert "surface_form" in entry
            assert "surface_devanagari" in entry
            assert "lemma" in entry
            assert "lemma_devanagari" in entry
            assert "meanings" in entry
            # Display scripts only — no SLP1 leakage markers
            assert "f" not in entry["surface_form"]
            assert "D" not in entry["surface_form"]

    def test_display_forms_handles_both_engine_scripts(self):
        """Regression: ByT5 emits IAST surfaces, vidyut emits SLP1.

        Blind SLP1 conversion turned IAST 'atha' into अत्ह and left
        'anuśāsanam' half-converted (अनुśāसनम्).
        """
        from app.services.sanskrit_adapter import _display_forms

        # IAST input (ByT5 path) — plain ASCII must be read as IAST
        assert _display_forms("atha") == ("atha", "अथ")
        assert _display_forms("anuśāsanam")[1] == "अनुशासनम्"
        assert _display_forms("nirodhaḥ")[1] == "निरोधः"

        # SLP1 input (vidyut path) — markers force SLP1 reading
        assert _display_forms("vftti") == ("vṛtti", "वृत्ति")
        assert _display_forms("BU") == ("bhū", "भू")
        # Title-case SLP1 (only marker is the initial capital)
        assert _display_forms("Bavati") == ("bhavati", "भवति")

    def test_merge_privative_rejoins_a_prefix(self):
        """Sutra 1.5 regression: 'akliṣṭāḥ' split into 'a' + 'kliṣṭāḥ'
        misleads — the negated stem is one word with its own entry."""
        words = [
            {"surface_form": "kliṣṭa", "surface_devanagari": "क्लिष्ट",
             "lemma": "kliś", "lemma_devanagari": "क्लिश्", "meanings": ["afflicted"]},
            {"surface_form": "a", "surface_devanagari": "अ",
             "lemma": "a", "lemma_devanagari": "अ", "meanings": ["not"]},
            {"surface_form": "kliṣṭāḥ", "surface_devanagari": "क्लिष्टाः",
             "lemma": "kliś", "lemma_devanagari": "क्लिश्", "meanings": ["afflicted"]},
        ]
        merged = SanskritAdapter._merge_privative(words)

        assert len(merged) == 2
        assert merged[0]["surface_form"] == "kliṣṭa"
        assert merged[1]["surface_form"] == "akliṣṭāḥ"
        assert merged[1]["surface_devanagari"] == "अक्लिष्टाः"
        assert merged[1]["lemma"] == "akliṣṭa"  # dictionary headword of the negated stem
        assert merged[1]["meanings"] == []  # forces negated-stem re-lookup

    def test_nominal_resolves_from_its_lemma_not_its_inflection(self, adapter):
        """A declined noun must give the same root wherever it appears.

        Trying the inflected surface first let case endings pick the reading:
        viṣayam matched a vi+√siv 'to sew' krdanta and viṣayā matched √viṣ
        'to sprinkle', so one word carried three etymologies across the text.
        A word the engine gave a case to is a nominal — its lemma is the form
        to ask about. The ByT5 pipeline fills in no morphology at all (case,
        gender and person are empty for the whole corpus), so the signal that
        actually fires is the lemma differing from the surface: that only
        happens when the analyser really did reduce an inflected form."""
        entry = {}
        SanskritAdapter._attach_dhatu(adapter, entry, "vizayam", "vizaya")
        bare = {}
        SanskritAdapter._attach_dhatu(adapter, bare, "vizaya", "vizaya")

        assert entry.get("dhatu") == bare.get("dhatu")
        assert entry.get("dhatu") != "siv"

    def test_finite_verb_still_resolves_from_its_surface(self, adapter):
        """A finite verb has no case, and only its surface carries the root
        (the lemma of gacchati is no help — √gam is in the inflected form)."""
        entry = {}
        SanskritAdapter._attach_dhatu(adapter, entry, "gacCati", "gacCati")
        assert entry.get("dhatu") == "gam"

    def test_merge_suffix_rejoins_abstract_tva(self):
        """Sutra 1.22 regression: 'adhimātratvāt' split into 'adhimātra' +
        'tvāt'. The stranded suffix is not a word — it was being shown to the
        reader as one and glossed 'one, several' (the numeral tva), a gloss
        with nothing to do with the sentence."""
        words = [
            {"surface_form": "adhimātra", "surface_devanagari": "अधिमात्र",
             "lemma": "adhimātra", "lemma_devanagari": "अधिमात्र",
             "meanings": ["above measure, excessive"], "dhatu": "mā"},
            {"surface_form": "tvāt", "surface_devanagari": "त्वात्",
             "lemma": "tva", "lemma_devanagari": "त्व",
             "meanings": ["one, several"]},
        ]
        merged = SanskritAdapter._merge_suffix(words)

        assert len(merged) == 1
        assert merged[0]["surface_form"] == "adhimātratvāt"
        assert merged[0]["surface_devanagari"] == "अधिमात्रत्वात्"
        assert merged[0]["lemma"] == "adhimātratva"  # the abstract noun
        assert merged[0]["meanings"] == []  # forces re-lookup of the whole
        assert merged[0]["dhatu"] == "mā"  # the stem still carries the root

    def test_merge_suffix_rejoins_abstract_ta(self):
        """Sutra 2.6 regression: 'ekātmatā' left a bare 'tā' glossed √tu."""
        words = [
            {"surface_form": "ātma", "surface_devanagari": "आत्म",
             "lemma": "ātman", "lemma_devanagari": "आत्मन्", "meanings": ["the breath"]},
            {"surface_form": "tā", "surface_devanagari": "ता",
             "lemma": "tā", "lemma_devanagari": "ता", "meanings": [], "dhatu": "tu"},
        ]
        merged = SanskritAdapter._merge_suffix(words)

        assert len(merged) == 1
        assert merged[0]["surface_form"] == "ātmatā"
        assert merged[0]["lemma"] == "ātmatā"
        assert merged[0].get("dhatu") != "tu", "√tu belonged to the stray suffix"

    def test_merge_suffix_keeps_a_leading_fragment(self):
        """With no stem in front of it there is nothing to rejoin — a
        sentence-initial fragment is left alone rather than dropped."""
        words = [{"surface_form": "tā", "surface_devanagari": "ता",
                  "lemma": "tā", "lemma_devanagari": "ता", "meanings": []}]
        assert SanskritAdapter._merge_suffix(words) == words

    def test_analyze_block_resolves_dhatu_for_derived_nouns(self, adapter):
        """The headline feature: every content word shows its root, not just
        finite verbs. yoga -> √yuj, nirodha -> ni + √rudh, with the root's
        own Sanskrit gloss."""
        result = adapter.analyze_block_sync("योगश्चित्तवृत्तिनिरोधः")
        assert result is not None
        by_lemma = {w["lemma"]: w for w in result["words"]}

        yoga = by_lemma.get("yoga")
        assert yoga is not None
        assert yoga["dhatu"] == "yuj"
        assert yoga["dhatu_devanagari"] == "युज्"
        assert yoga["dhatu_verified"] is True
        assert yoga["dhatu_meaning"]  # non-empty artha

        nirodha = by_lemma.get("nirodha")
        assert nirodha is not None
        assert nirodha["dhatu"] == "rudh"
        assert nirodha["dhatu_prefixes"] == ["ni"]

    def test_golden_sutra_1_1_roots_and_english_meanings(self):
        """Golden example — sutra 1.1 'atha yogānuśāsanam'.

        Asserts against data/word_analysis.json, the precomputed artifact the
        API actually serves (the live pipeline runs the ByT5-only engine
        config from scripts/enrich_word_analysis.py, not the default adapter).
        Every content word must show its root AND an English gloss for that
        root; the particle must show neither — the whole feature in one line.
        """
        import json
        import os

        cache = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "word_analysis.json",
        )
        if not os.path.exists(cache):
            pytest.skip("word_analysis.json not precomputed")
        with open(cache, encoding="utf-8") as fh:
            result = json.load(fh)["1.1"]
        by_lemma = {w["lemma"]: w for w in result["words"]}

        yoga = by_lemma.get("yoga")
        assert yoga is not None, f"no 'yoga' in {list(by_lemma)}"
        assert yoga["dhatu"] == "yuj"
        # The root's meaning a reader can actually read.
        assert yoga["dhatu_meaning_en"], "root √yuj has no English gloss"
        assert "yoke" in yoga["dhatu_meaning_en"] or "join" in yoga["dhatu_meaning_en"]

        anu = by_lemma.get("anuśāsana")
        assert anu is not None, f"no 'anuśāsana' in {list(by_lemma)}"
        assert anu["dhatu"] == "śās", f"expected √śās, got {anu['dhatu']}"
        assert anu["dhatu_prefixes"] == ["anu"]
        assert anu["dhatu_meaning_en"], "root √śās has no English gloss"

        atha = by_lemma.get("atha")
        assert atha is not None
        assert atha["dhatu"] is None, "particle 'atha' must have no root"

    def test_analyze_block_matches_stored_schema(self, adapter):
        """Output is JSON-serializable, fit for the word_analysis column."""
        import json

        result = adapter.analyze_block_sync("अथ योगानुशासनम्")

        assert result is not None
        json.dumps(result, ensure_ascii=False)  # must not raise
        surfaces = [w["surface_devanagari"] for w in result["words"]]
        assert any("योग" in s or "अनुशासन" in s for s in surfaces)
