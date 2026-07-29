"""Tests for DhatuResolver — vidyut-Kośa root recovery.

Skips gracefully when the vidyut data bundle or sanskrit_model checkout is
absent (e.g. minimal CI without the model repo).
"""
import pytest

from app.services.dhatu_resolver import DhatuResolver


@pytest.fixture(scope="module")
def resolver():
    r = DhatuResolver()
    if not r._ensure():
        pytest.skip("vidyut data / sanskrit_model not available")
    return r


class TestDhatuResolver:
    def test_derived_noun_maps_to_root(self, resolver):
        """yoga (a nominal stem, not a verb) -> √yuj with its gaṇa + gloss."""
        info = resolver.resolve("yogaH", "yoga")
        assert info is not None
        assert info["root_slp1"] == "yuj"
        assert info["verified"] is True
        assert info["gana"] == 10  # curādi
        assert info["artha_slp1"]  # saMyamane
        assert info["is_verb"] is False

    def test_prefixed_derivative_keeps_prefix(self, resolver):
        """nirodha -> ni + √rudh (prefix surfaced separately)."""
        info = resolver.resolve("niroDaH", "niroDa")
        assert info is not None
        assert info["root_slp1"] == "ruD"
        assert info["prefixes_slp1"] == ["ni"]

    def test_finite_verb_flagged(self, resolver):
        """A finite form resolves to its root and is flagged a verb."""
        info = resolver.resolve("Bavati", "BU")
        assert info is not None
        assert info["root_slp1"] == "BU"
        assert info["is_verb"] is True
        assert info["gana"] == 1  # bhvādi

    def test_retroflex_root_cleaned(self, resolver):
        """draṣṭṛ -> √dṛś (residual it-marker stripped, curated-verified)."""
        info = resolver.resolve("drazwf", "drazwf")
        assert info is not None
        assert info["root_slp1"] == "dfS"

    def test_particle_has_no_root(self, resolver):
        """Indeclinables/particles legitimately return None."""
        assert resolver.resolve("aTa", "aTa") is None
