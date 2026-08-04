"""Tests for DictionaryService.clean_definition — raw CDSL entry cleanup."""

from app.services.dictionary_service import DictionaryService

clean = DictionaryService.clean_definition
sense_run = DictionaryService._extract_sense_run


class TestCleanDefinition:
    def test_transliterates_embedded_slp1_tokens(self):
        raw = ('niroDaH niroDanaM 1 Confinement, locking up; '
               'yogaScittavfttiniroDaH Yoga S.')
        out = clean(raw)
        # leading headword echoes stripped, quoted Sanskrit transliterated
        assert out.startswith('1 Confinement, locking up')
        assert 'yogaścittavṛttinirodhaḥ' in out
        assert 'niroDaH' not in out

    def test_collapses_doubled_headword_echo(self):
        assert clean('cittacitta mfn. observed').startswith('mfn. observed')

    def test_collapses_triple_echo_and_accent_marks(self):
        # 'yogayogayoga' (triple) and accent-marked 'yo/ga' variants collapse,
        # then the leading echo is dropped at the POS-marker boundary
        out = clean('yogayo/gayo/ga m. the act of yoking')
        assert out.startswith('m. the act of yoking')

    def test_strips_lowercase_slp1_echo(self):
        # 'vftti' has no capitals for the transliterator to spot; the leading
        # echo run must still be dropped at the 'f.' POS marker
        out = clean('vfttivf/ttivf/tti f. rolling, rolling down (of tears), MBh.')
        assert out.startswith('f. rolling, rolling down')
        assert 'vftti' not in out

    def test_strips_trailing_scan_reference(self):
        out = clean('instruction, direction, command168960631-c')
        assert out == 'instruction, direction, command'

    def test_leaves_english_and_citations_alone(self):
        raw = 'Restraint, check; Ms. 8. 310, 375; MBh.; the Buddhists'
        out = clean(raw)
        assert 'Ms.' in out
        assert 'MBh.' in out
        assert 'Buddhists' in out

    def test_real_apte_nirodha_row(self):
        raw = ('niroDaHniroDaH niroDanaMniroDaH niroDanaM 1 Confinement, '
               'locking up, imprisonment; Ms. 8. 310, 375. 2 Enclosing, '
               'covering up; Amaru. 87.168960631-c')
        out = clean(raw)
        assert out.startswith('1 Confinement')
        assert 'niroDa' not in out
        assert '168960631' not in out


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
