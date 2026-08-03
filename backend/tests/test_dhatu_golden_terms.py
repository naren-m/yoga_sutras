"""Ground truth: roots of the Yoga Sutras' core technical vocabulary.

Every entry is a term whose derivation the grammatical tradition agrees on
(Vyāsa's bhāṣya, MW's etymologies, the Dhātupāṭha). This is the regression
guard for DhatuResolver: root identification is a ranking problem over
homographic Kośa readings, and a change that helps one word easily breaks
another, so the whole set runs together.

Roots are SLP1. ``None`` means the word must show NO root — a pronoun,
particle, or a stem with no accepted verbal derivation.
"""

import pytest

from app.services.dhatu_resolver import get_dhatu_resolver

# (stem in SLP1, expected root in SLP1 or None)
GOLDEN_TERMS = [
    # --- headline derivations, sutra 1.1-1.2 ---
    ("yoga", "yuj"),          # yoking, union
    ("citta", "cit"),         # mind-stuff <- to perceive
    ("vftti", "vft"),         # turning, modification
    ("niroDa", "ruD"),        # ni + to obstruct
    ("anuSAsana", "SAs"),     # anu + to instruct
    # --- the kleśas and their kin (2.3ff) ---
    ("avidyA", "vid"),        # not-knowing; NOT vi + √dā
    ("rAga", "raYj"),         # attachment <- to be coloured
    ("dveza", "dviz"),        # aversion
    ("kleSa", "kliS"),        # affliction
    ("aBiniveSa", "viS"),     # abhi + ni + to enter
    # --- practice vocabulary ---
    ("aByAsa", "as"),         # abhi + to be: repeated practice
    pytest.param("vErAgya", "raYj", marks=pytest.mark.xfail(
        reason="taddhita vrddhi stem: no Kosa derivation, MW cites no root",
        strict=False)),
    ("smfti", "smf"),         # memory
    ("samADi", "DA"),         # sam + ā + to place
    ("DAraRA", "Df"),         # to hold
    pytest.param("prARa", "an", marks=pytest.mark.xfail(
        reason="prefix-free root pra also attested; no signal separates them",
        strict=False)),
    ("saMyama", "yam"),       # sam + to restrain
    ("tapas", "tap"),         # to burn, austerity
    ("karman", "kf"),         # to do
    ("jAti", "jan"),          # birth <- to be born
    pytest.param("BOga", "Buj", marks=pytest.mark.xfail(
        reason="no Kosa derivation for bhoga, MW cites no root",
        strict=False)),
    ("jYAna", "jYA"),         # knowledge
    ("viveka", "vic"),        # vi + to separate: discernment
    ("KyAti", "KyA"),         # to declare, discernment
    pytest.param("Ananda", "nand", marks=pytest.mark.xfail(
        reason="Kosa cites this root as tunadi~; restoring the idit nasal "
               "infix (P. 7.1.58) is not implemented",
        strict=False)),
    ("saMskAra", "kf"),       # sam + to do: latent impression
    ("Agama", "gam"),         # ā + to go: received testimony
    ("anumAna", "mA"),        # anu + to measure: inference
    ("vyAKyA", "KyA"),        # vi + ā + to declare
    pytest.param("Apatti", "pad", marks=pytest.mark.xfail(
        reason="Kosa offers curated pat over uncurated pad",
        strict=False)),
    # --- Dhātupāṭha citation spellings that must be undone (P. 8.4.41) ---
    ("sTiti", "sTA"),         # cited as ṣṭhā, not sṭhā
    ("avasTA", "sTA"),        # ava + √sthā
    ("vyutTAna", "sTA"),      # vi + ud + √sthā
    ("svapna", "svap"),       # cited as ñiṣvap
    ("prasAda", "sad"),       # pra + √sad, cited as ṣad
    ("naSa", "naS"),       # cited as ṇaś
    # --- words that must stay root-less ---
    ("tad", None),            # pronoun
    ("aTa", None),            # particle
    ("ca", None),             # particle
    ("tatra", None),          # indeclinable
    ("iti", None),            # particle
]


def _ids(terms):
    """Readable test ids for plain tuples and xfail-marked params alike."""
    return [t.values[0] if hasattr(t, "values") else t[0] for t in terms]


@pytest.fixture(scope="module")
def resolve_root():
    """Resolve exactly as the adapter does — Kośa plus MW's own etymology."""
    r = get_dhatu_resolver()
    if not r._ensure():
        pytest.skip("vidyut Kośa / sanskrit_model unavailable")

    from app import create_app
    from app.services.sanskrit_adapter import SanskritAdapter

    app = create_app()

    def _resolve(stem):
        entry = {}
        with app.app_context():
            SanskritAdapter._attach_dhatu(SanskritAdapter, entry, stem, stem)
        return entry.get("dhatu_slp1")

    return _resolve


@pytest.mark.parametrize("stem,expected", GOLDEN_TERMS, ids=_ids(GOLDEN_TERMS))
def test_golden_root(resolve_root, stem, expected):
    got = resolve_root(stem)
    assert got == expected, f"{stem}: expected {expected}, got {got}"
