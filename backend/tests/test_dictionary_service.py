"""Tests for DictionaryService.clean_definition — raw CDSL entry cleanup."""

from app.services.dictionary_service import DictionaryService

clean = DictionaryService.clean_definition


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
