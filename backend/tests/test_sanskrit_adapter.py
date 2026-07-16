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
