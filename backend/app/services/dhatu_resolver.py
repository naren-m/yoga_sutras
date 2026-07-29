"""Resolve the verbal root (dhātu) behind any Sanskrit word.

The ensemble engines give a *lemma* — for a verb that is already the root
(gacchati -> gam), but for a derived nominal it is only the stem (yoga, not
yuj). This module recovers the root for derived nominals too, which is the
educationally interesting fact ("yoga comes from √yuj, 'to yoke'").

Source of truth is vidyut's Kośa: its entries for derived stems are
``Kṛdanta`` pratipādikas that carry the originating ``DhatuEntry`` — the
root's aupadeśika form, its prefixes, gaṇa, and Sanskrit gloss (artha).
The raw aupadeśika still carries Pāṇinian it-markers (yu\\ja~ , ru\\Di~^r),
so we clean it via sanskrit_model's ``strip_anubandhas`` and prefer the
294-entry hand-curated ``core_root`` table when the root is in it
("neural/statistical proposes, Pāṇini disposes").

Everything is best-effort: if the vidyut data bundle or sanskrit_model
checkout is absent, resolve() simply returns None and the caller keeps its
prior behaviour.
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)


class DhatuResolver:
    """Lazy, process-wide resolver of stem/word -> root via vidyut Kośa."""

    def __init__(self, slm_path: str | None = None):
        self._kosha = None
        self._strip = None
        self._dhatu_kosha = None
        self._ready: bool | None = None
        self._slm_path = slm_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))),
            "sanskrit_model",
        )

    def _ensure(self) -> bool:
        """Load vidyut Kośa + sanskrit_model helpers once; cache success."""
        if self._ready is not None:
            return self._ready
        try:
            import sys
            from vidyut.kosha import Kosha
            from sanskrit_analyzer.prakriya.analyzer import resolve_data_dir

            data_dir = resolve_data_dir()
            if data_dir is None:
                raise RuntimeError("vidyut data bundle not found")
            self._kosha = Kosha(os.path.join(str(data_dir), "kosha"))

            if self._slm_path not in sys.path:
                sys.path.insert(0, self._slm_path)
            from slm.rules import strip_anubandhas, DhatuKosha

            self._strip = strip_anubandhas
            self._dhatu_kosha = DhatuKosha()
            self._ready = True
        except Exception as e:  # missing data bundle / model checkout
            logger.info("DhatuResolver unavailable: %s", e)
            self._ready = False
        return self._ready

    # Vidyut gaṇa str() form -> traditional dhātu class number (1..10).
    _GANA_NUM = {
        "BvAdi": 1, "adAdi": 2, "juhotyAdi": 3, "divAdi": 4, "svAdi": 5,
        "tudAdi": 6, "ruDAdi": 7, "tanAdi": 8, "kryAdi": 9, "curAdi": 10,
    }

    # Pronoun (sarvanāman) stems in SLP1 — closed class, no verbal root.
    # Backs up the is_avyaya check for stems the Kośa doesn't flag.
    _PRONOUN_STEMS = frozenset({
        "tad", "etad", "idam", "adas", "yad", "kim", "asmad", "yuzmad",
        "enad", "tyad", "eka", "sarva", "sva",
    })

    _RESIDUAL = re.compile(r"[iIuU]?~[\^a-zA-Z]*$")

    def _clean_root(self, aupadeshika: str) -> tuple[str, bool]:
        """(clean SLP1 root, verified-against-curated-dhatupatha)."""
        root = self._strip(aupadeshika)
        # strip_anubandhas leaves nasal-infix / retroflex residues like
        # 'rudhi~' or 'dfSi~r'; drop the linking vowel + nasal marker tail.
        root = self._RESIDUAL.sub("", root).rstrip("~^\\")
        entries = self._dhatu_kosha.lookup(root)
        if entries:
            curated = next((e for e in entries if e.get("curated")), entries[0])
            return (curated.get("core_root") or root), True
        return root, False

    def resolve(self, *candidates_slp1: str) -> dict | None:
        """Return root info for the first candidate that maps to a dhātu.

        Pass SLP1 forms most-specific-first (surface, then lemma). Returns a
        dict with SLP1 root fields the adapter transliterates for display, or
        None when nothing resolves (particles, pronouns, unknown stems).
        """
        if not self._ensure():
            return None
        cands = [(c or "").strip().lstrip("'") for c in candidates_slp1]
        cands = [c for c in cands if c]

        # Indeclinables and pronouns have no verbal root, yet the Kośa lists
        # obscure verb/nominal homographs for them (ca -> √ci) and for their
        # inflected forms (tasya -> √tas). Skip the whole word if *any*
        # candidate — surface OR lemma — is an avyaya or a pronoun stem, so an
        # inflected pronoun can't slip a spurious root past its flagged lemma.
        if any(c in self._PRONOUN_STEMS for c in cands):
            return None
        for cand in cands:
            if any(getattr(e, "is_avyaya", False) for e in self._kosha.get(cand)):
                return None

        for cand in cands:
            entries = list(self._kosha.get(cand))
            # A finite-verb (Tiṅanta) reading, when present, gives the root
            # most directly and is the intended reading of a finite form
            # (gacchati -> gam); prefer it over a homographic krdanta.
            entries.sort(key=lambda e: not type(e).__name__.endswith("Tinanta"))
            for entry in entries:
                is_verb = type(entry).__name__.endswith("Tinanta")
                # Both Tiṅanta (direct) and krdanta Subanta (via pratipadika)
                # carry the originating DhatuEntry.
                de = getattr(entry, "dhatu_entry", None)
                if de is None:
                    pe = getattr(entry, "pratipadika_entry", None)
                    de = getattr(pe, "dhatu_entry", None) if pe else None
                if de is None:
                    continue
                dhatu = de.dhatu
                root, verified = self._clean_root(dhatu.aupadeshika)
                if not root:
                    continue
                gana = self._GANA_NUM.get(str(dhatu.gana)) if dhatu.gana else None
                return self._pack(
                    root, list(dhatu.prefixes or []), gana, de.artha_sa, verified,
                    is_verb=is_verb,
                )
        return None

    @staticmethod
    def _pack(root_slp1, prefixes_slp1, gana, artha_slp1, verified, is_verb=False) -> dict:
        return {
            "root_slp1": root_slp1,
            "prefixes_slp1": prefixes_slp1,
            "gana": gana,
            "artha_slp1": artha_slp1,
            "verified": verified,
            "is_verb": is_verb,
        }


_resolver: DhatuResolver | None = None


def get_dhatu_resolver() -> DhatuResolver:
    global _resolver
    if _resolver is None:
        _resolver = DhatuResolver()
    return _resolver
