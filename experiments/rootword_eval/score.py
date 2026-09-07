"""Shared scorer for root-word identification experiments.

All experiments MUST use score_run() so numbers are comparable.

Usage from an experiment script:

    from score import load_gold, score_run

    gold = load_gold()
    predictions = {case_id: {"lemmas": [...], "dhatu": "..." or None}, ...}
    report = score_run(predictions, gold)
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))

Prediction lemmas may be in Devanagari, IAST, or SLP1 — everything is
normalized to SLP1 before comparison.
"""

import json
import re
import unicodedata
from pathlib import Path

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

GOLD_PATH = Path(__file__).parent / "gold.json"

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_IAST_MARKS = re.compile(r"[āīūṛṝḷḹṃṁḥśṣñṭḍṇṅ]")


def to_slp1(word: str) -> str:
    """Normalize any-script word to lowercase SLP1 for comparison."""
    w = unicodedata.normalize("NFC", (word or "").strip())
    if not w:
        return ""
    if _DEVANAGARI.search(w):
        src = sanscript.DEVANAGARI
    elif _IAST_MARKS.search(w.lower()):
        src = sanscript.IAST
    else:
        # ASCII-only: could be SLP1 already or plain IAST without diacritics.
        # SLP1 markers: meaningful capitals OR lowercase chars IAST never uses
        # (f=ṛ, x=ḷ, w=ṭ, q=ḍ, z=ṣ). Without this, lowercase SLP1 like
        # 'vftti' falls into the IAST branch and gets mangled.
        if re.search(r"[AIUFXEOKGNCJYWQRTDPBMSZLVfxwqz]", w):
            return w.strip("-").strip()
        src = sanscript.IAST
    out = transliterate(w, src, sanscript.SLP1)
    return out.strip("-").strip()


def _slot_match(predicted_slp1: set, accept_list: list) -> bool:
    return any(to_slp1(a) in predicted_slp1 for a in accept_list)


def load_gold(path: Path = GOLD_PATH) -> dict:
    return json.loads(path.read_text())


def score_run(predictions: dict, gold: dict) -> dict:
    """Score predictions against gold.

    predictions: {case_id(int or str): {"lemmas": list[str], "dhatu": str|None}}
    Returns dict with per-case rows and summary (mean F1, exact-match rate,
    dhatu accuracy over cases that define a dhatu).
    """
    rows = []
    f1s = []
    exact = 0
    dhatu_total = 0
    dhatu_hit = 0

    for case in gold["cases"]:
        cid = case["id"]
        pred = predictions.get(cid) or predictions.get(str(cid)) or {}
        pred_lemmas = pred.get("lemmas") or []
        pred_set = {to_slp1(x) for x in pred_lemmas if x}
        pred_set.discard("")

        slots = case["expected"]
        hits = sum(1 for accept in slots if _slot_match(pred_set, accept))
        recall = hits / len(slots) if slots else 0.0
        precision = hits / len(pred_set) if pred_set else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        is_exact = hits == len(slots) and len(pred_set) == len(slots)

        f1s.append(f1)
        exact += int(is_exact)

        drow = None
        if case.get("dhatu"):
            dhatu_total += 1
            pd = to_slp1(pred.get("dhatu") or "")
            gd = to_slp1(case["dhatu"])
            ok = pd == gd
            dhatu_hit += int(ok)
            drow = {"gold": case["dhatu"], "pred": pred.get("dhatu"), "ok": ok}

        rows.append({
            "id": cid,
            "input": case["iast"],
            "gold_slots": slots,
            "predicted": sorted(pred_set),
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "f1": round(f1, 3),
            "exact": is_exact,
            "dhatu": drow,
        })

    n = len(gold["cases"])
    return {
        "rows": rows,
        "summary": {
            "n_cases": n,
            "mean_f1": round(sum(f1s) / n, 4) if n else 0.0,
            "exact_match_rate": round(exact / n, 4) if n else 0.0,
            "dhatu_accuracy": round(dhatu_hit / dhatu_total, 4) if dhatu_total else None,
            "dhatu_n": dhatu_total,
        },
    }


if __name__ == "__main__":
    g = load_gold()
    # sanity: gold matches itself perfectly
    perfect = {c["id"]: {"lemmas": [a[0] for a in c["expected"]], "dhatu": c.get("dhatu")} for c in g["cases"]}
    rep = score_run(perfect, g)
    print(json.dumps(rep["summary"], indent=2))
    assert rep["summary"]["mean_f1"] == 1.0, "self-test failed"
    print("self-test OK")
