"""Tests for DictionaryService: MW etymology parsing, sense runs, lexicon lookup."""

import pytest

from app.services.dictionary_service import DictionaryService

sense_run = DictionaryService._extract_sense_run


class TestCitedRootParsing:
    """MW names a word's root inline ('fr. √ rañj'), and that citation
    outranks every heuristic in the resolver — so a malformed capture is
    worse than none. The entry bodies put several things after the √ sign
    that are not roots: cross-reference numerals, CDSL id suffixes, and a
    '?' marking an etymology MW is unsure of."""

    parse = staticmethod(DictionaryService._cited_root_from_texts)

    def test_plain_citation(self):
        assert self.parse(["m. (fr. √ rañj; ifc. A, or I) the act of colouring"]) == "raYj"

    def test_skips_cross_reference_numerals(self):
        """'See √ 1. 2. and 4. kṣi' must not yield the numeral '2'."""
        assert self.parse(["See √ 1. 2. and 4. kzi."]) != "2"

    def test_drops_cdsl_id_suffix(self):
        """'√ sañj.228458' — the trailing id is a database key, not the root."""
        assert self.parse(["See below and √ sañj.228458."]) == "saYj"

    def test_prefers_an_unmarked_citation_over_a_doubtful_one(self):
        """kāla: one entry hedges 'fr. √ 3. kal?', a later one states
        '√ 3. kal' outright. The confident reading is the one to use."""
        texts = ["n. (fr. √ 3. kal?), black, of a dark colour",
                 "m. (√ 3. kal, 'to calculate or enumerate'), a fixed point of time"]
        assert self.parse(texts) == "kal"

    def test_doubtful_citation_still_used_when_it_is_all_there_is(self):
        assert self.parse(["n. (fr. √ car?; the wheel"]) == "car"

    def test_no_citation(self):
        assert self.parse(["m. change, alteration, transformation into (instr.)"]) is None


class TestRootSenseRun:
    """Root glosses shown to the reader come from MW's 'to ...' sense run."""

    def test_extracts_sense_run_after_conjugation_block(self):
        text = ("cl. 7. P. Ā. (Dhātup. xxix, 7) yunakti, yuṅkte "
                "to yoke or join or fasten or harness, RV. &c.")
        assert sense_run(text) == "to yoke or join or fasten or harness"

    def test_truncates_long_sense_lists(self):
        text = "cl. 1. P. to turn, turn round, revolve, roll, move, be"
        assert sense_run(text) == "to turn, turn round, revolve, roll"

    def test_skips_grammatical_apparatus(self):
        """'to Dhātup. xxv, 6' is a citation, not a meaning."""
        assert sense_run("cl. 3. P. mimāti (accord. to Dhātup. xxv, 6 Ā.)") is None

    def test_returns_none_when_no_sense_run(self):
        assert sense_run("m. permission, consent, TBr.") is None


_SERVICE = DictionaryService()


@pytest.mark.parametrize(
    "word, fuzzy, expect_key, expect_fuzzy",
    [
        ("rAga", False, "rAga", False),          # SLP1 input
        ("राग", False, "rAga", False),            # Devanagari input
        ("nirodha", False, "niroDa", False),      # IAST input
        ("nirodhaḥ", False, None, False),         # inflected form: not a headword
        ("niroDa", True, "niroDa", False),        # exact hit never reports fuzzy
        ("niroDx", True, "niroDa", True),         # typo, fuzzy on
        ("niroDx", False, None, False),           # typo, fuzzy off
    ],
)
def test_get_definitions(word, fuzzy, expect_key, expect_fuzzy):
    defs = _SERVICE.get_definitions(word, fuzzy=fuzzy)
    if expect_key is None:
        assert defs == []
        return
    hits = [d for d in defs if d["key"] == expect_key]
    assert hits, f"no {expect_key} entry for {word!r}: {[d['key'] for d in defs][:5]}"
    d = hits[0]
    assert d["dictionary_code"] == "mw" and d["licence"] == "CC BY-SA 4.0"
    assert d["key_devanagari"] and d["key_iast"] and d["definition"]
    assert d["is_fuzzy_match"] is expect_fuzzy


@pytest.mark.parametrize(
    "word, root",
    [
        ("rAga", "raYj"),     # 'fr. √ rañj'
        ("karman", "kf"),     # '(√ kf, Uṇ. iv, 144)' keeps raw SLP1
    ],
)
def test_cited_root_from_lexicon(word, root):
    assert _SERVICE.get_cited_root(word) == root
