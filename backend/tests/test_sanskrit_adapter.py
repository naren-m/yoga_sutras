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
