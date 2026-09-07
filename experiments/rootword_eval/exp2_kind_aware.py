"""EXPERIMENT 2 follow-up: KIND-AWARE lemma selection on hybrid dev config.

Per token:
  1. if a finite-verb analysis exists (kind=='verb' with a lakara/purusha tin
     marker) -> use its lemma (+dhatu)   [fixes finite verbs like bhavati]
  2. else prefer a nominal-kind pratipadika lemma   [keeps the noun wins]
  3. else fall back to headline (analyses[0].lemma)

Re-runs DeepRead on hybrid dev (needs the full analyses, which the stored JSON
does not keep), scores with the PATCHED score.py, appends the run as strategy
"kind_aware" under results["hybrid__dev"]["strategies"] in exp2_results.json,
and prints the numbers + which cases changed vs the "nominal" strategy.
"""
import concurrent.futures
import json
import os
import time

from sanskrit_analyzer.deep_read import DeepRead
from score import load_gold, score_run

EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(EVAL_DIR, "exp2_results.json")
TIMEOUT_S = 45.0
_FINITE_MARKERS = ("lakara", "purusha", "prayoga")


def _is_finite_verb(a):
    return a.kind == "verb" and any(k in (a.morphology or {}) for k in _FINITE_MARKERS)


def _dhatu_headline(tokens):
    for tok in tokens:
        for a in tok.analyses or []:
            if a.dhatu and a.dhatu.root:
                return a.dhatu.root
    return None


def extract_nominal(res):
    lemmas = []
    for tok in res.tokens:
        ans = tok.analyses or []
        if not ans:
            continue
        pick = next((a for a in ans if a.kind == "nominal"), None)
        if pick is None:
            pick = next((a for a in ans if a.kind == "derived"), None)
        if pick is None:
            pick = ans[0]
        if pick.lemma:
            lemmas.append(pick.lemma)
    return {"lemmas": lemmas, "dhatu": _dhatu_headline(res.tokens)}


def extract_kind_aware(res):
    lemmas = []
    dhatu = None
    for tok in res.tokens:
        ans = tok.analyses or []
        if not ans:
            continue
        verb = next((a for a in ans if _is_finite_verb(a)), None)
        if verb is not None:
            pick = verb
            if dhatu is None and verb.dhatu and verb.dhatu.root:
                dhatu = verb.dhatu.root
        else:
            pick = next((a for a in ans if a.kind == "nominal"), None)
            if pick is None:
                pick = next((a for a in ans if a.kind == "derived"), None)
            if pick is None:
                pick = ans[0]
        if pick.lemma:
            lemmas.append(pick.lemma)
    if dhatu is None:
        dhatu = _dhatu_headline(res.tokens)
    return {"lemmas": lemmas, "dhatu": dhatu}


def main():
    gold = load_gold()
    cases = gold["cases"]
    dr = DeepRead()

    per_case = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        for case in cases:
            fut = ex.submit(dr.analyze, case["dev"], prefer_analyzer=False, use_dharmamitra=True)
            try:
                per_case[case["id"]] = fut.result(timeout=TIMEOUT_S)
            except Exception as e:  # noqa: BLE001
                print(f"  id{case['id']} error: {type(e).__name__}: {e}")
                per_case[case["id"]] = None

    preds_ka, preds_nom = {}, {}
    for case in cases:
        res = per_case[case["id"]]
        preds_ka[case["id"]] = extract_kind_aware(res) if res else {"lemmas": [], "dhatu": None}
        preds_nom[case["id"]] = extract_nominal(res) if res else {"lemmas": [], "dhatu": None}

    rep_ka = score_run(preds_ka, gold)
    rep_nom = score_run(preds_nom, gold)
    s = rep_ka["summary"]
    print("kind_aware  f1=%.3f exact=%.3f dhatu_acc=%s (n=%d)"
          % (s["mean_f1"], s["exact_match_rate"], s["dhatu_accuracy"], s["dhatu_n"]))
    sn = rep_nom["summary"]
    print("nominal     f1=%.3f exact=%.3f dhatu_acc=%s (n=%d)"
          % (sn["mean_f1"], sn["exact_match_rate"], sn["dhatu_accuracy"], sn["dhatu_n"]))

    # cases whose lemma prediction changed vs nominal
    print("\nCASES CHANGED vs nominal:")
    ka_rows = {r["id"]: r for r in rep_ka["rows"]}
    nom_rows = {r["id"]: r for r in rep_nom["rows"]}
    changed = []
    for case in cases:
        cid = case["id"]
        if preds_ka[cid]["lemmas"] != preds_nom[cid]["lemmas"]:
            kr, nr = ka_rows[cid], nom_rows[cid]
            changed.append(cid)
            print(f"  id{cid:>2} {case['iast']:<16} gold={nr['gold_slots']}")
            print(f"        nominal   lemmas={preds_nom[cid]['lemmas']} f1={nr['f1']}")
            print(f"        kind_aware lemmas={preds_ka[cid]['lemmas']} f1={kr['f1']}")
    if not changed:
        print("  (none)")

    # append to exp2_results.json
    out = json.load(open(RESULTS))
    out["results"]["hybrid__dev"]["strategies"]["kind_aware"] = {
        "summary": rep_ka["summary"],
        "rows": rep_ka["rows"],
        "predictions": {str(k): v for k, v in preds_ka.items()},
    }
    with open(RESULTS, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nAppended strategy 'kind_aware' to {RESULTS}")
    return rep_ka["summary"], changed


if __name__ == "__main__":
    main()
